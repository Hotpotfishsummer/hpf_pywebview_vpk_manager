"""SftpService 的单元测试(mock paramiko 客户端,不发起真实网络连接)"""

from unittest.mock import MagicMock

import pytest

from backend.services.sftp_service import SftpService


def _make_service_with_mock_sftp(monkeypatch):
    svc = SftpService()
    sftp = MagicMock()
    monkeypatch.setattr(svc, "_get_client", lambda config: sftp)
    return svc, sftp


class TestListVpkFiles:
    def test_filters_and_sorts(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)

        def make_attr(name, size):
            attr = MagicMock()
            attr.filename = name
            attr.st_size = size
            attr.st_mtime = 0
            return attr

        sftp.listdir_attr.return_value = [
            make_attr("b.vpk", 2 * 1024 * 1024),
            make_attr("a.vpk.disabled", 1024),
            make_attr("notes.txt", 10),
            make_attr("A.vpk", 1024),
        ]

        files = svc.list_vpk_files({"addons_path": "/srv/addons"})

        # .txt 被过滤;排序按 name.lower():'a.vpk' 是 'a.vpk.disabled' 的前缀
        assert [f["name"] for f in files] == ["A.vpk", "a.vpk.disabled", "b.vpk"]
        assert files[2]["size"] == 2.0  # MB
        assert files[1]["is_disabled"] is True  # a.vpk.disabled
        assert files[2]["path"] == "/srv/addons/b.vpk"

    def test_missing_addons_path_raises(self, monkeypatch):
        svc, _ = _make_service_with_mock_sftp(monkeypatch)
        with pytest.raises(ValueError):
            svc.list_vpk_files({})


class TestRenameWithImages:
    def test_renames_associated_images(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        # .jpg 存在,.txt 不存在
        sftp.stat.side_effect = lambda p: MagicMock() if p.endswith(".jpg") else (_ for _ in ()).throw(IOError("nf"))

        config = {}
        ok = svc.rename_file_with_images(config, "/a/mod.vpk", "/a/mod.vpk.disabled")

        assert ok is True
        renamed = [c.args for c in sftp.rename.call_args_list]
        assert ("/a/mod.vpk", "/a/mod.vpk.disabled") in renamed
        assert ("/a/mod.jpg", "/a/mod.vpk.jpg") in renamed

    def test_no_images_only_renames_vpk(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        sftp.stat.side_effect = IOError("not found")

        ok = svc.rename_file_with_images({}, "/a/mod.vpk.disabled", "/a/mod.vpk")

        assert ok is True
        assert sftp.rename.call_args_list == [((("/a/mod.vpk.disabled", "/a/mod.vpk")),)]
        # 启用方向: x.vpk.disabled 的图片基名 x.vpk → x
        renamed = [c.args for c in sftp.rename.call_args_list]
        assert ("/a/mod.vpk.disabled", "/a/mod.vpk") in renamed

    def test_vpk_rename_failure_returns_false(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        sftp.rename.side_effect = IOError("perm")
        assert svc.rename_file_with_images({}, "/a/x.vpk", "/a/x.vpk.disabled") is False
        assert sftp.rename.call_count == 1


class TestDeleteWithImages:
    def test_deletes_associated_images(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        sftp.stat.side_effect = lambda p: MagicMock() if p.endswith((".jpg", ".txt")) else (_ for _ in ()).throw(IOError("nf"))

        ok = svc.delete_file_with_images({}, "/a/mod.vpk")

        assert ok is True
        removed = [c.args[0] for c in sftp.remove.call_args_list]
        assert removed == ["/a/mod.vpk", "/a/mod.jpg", "/a/mod.txt"]

    def test_vpk_delete_failure_returns_false(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        sftp.remove.side_effect = IOError("perm")
        assert svc.delete_file_with_images({}, "/a/x.vpk") is False
        assert sftp.remove.call_count == 1


class TestConnection:
    def _patch_paramiko(self, monkeypatch):
        ssh = MagicMock()
        monkeypatch.setattr("backend.services.sftp_service.paramiko.SSHClient", MagicMock(return_value=ssh))
        return ssh

    def test_connect_uses_default_timeout(self, monkeypatch):
        svc = SftpService()
        ssh = self._patch_paramiko(monkeypatch)

        svc._get_client({"address": "host:22", "username": "u", "password": "p"})

        args, kwargs = ssh.connect.call_args
        assert args[:4] == ("host", 22, "u", "p")
        assert kwargs["timeout"] == 10.0

    def test_connect_uses_custom_timeout(self, monkeypatch):
        svc = SftpService(connect_timeout=3.5)
        ssh = self._patch_paramiko(monkeypatch)

        svc._get_client({"address": "host", "username": "u", "password": "p"})

        args, kwargs = ssh.connect.call_args
        assert args[0] == "host"
        assert args[1] == 22  # 无端口时默认 22
        assert kwargs["timeout"] == 3.5

    def test_connect_failure_resets_state_and_raises(self, monkeypatch):
        svc = SftpService()
        ssh = self._patch_paramiko(monkeypatch)
        ssh.connect.side_effect = IOError("unreachable")

        with pytest.raises(IOError):
            svc._get_client({"address": "host:2222", "username": "u", "password": "p"})

        assert svc._ssh_client is None
        assert svc._sftp is None

    def test_missing_credentials_raises_before_connect(self, monkeypatch):
        svc = SftpService()
        ssh = self._patch_paramiko(monkeypatch)

        with pytest.raises(ValueError):
            svc._get_client({"address": "host"})
        ssh.connect.assert_not_called()


class TestCloseLifecycle:
    def test_close_shuts_down_executor_and_clears_state(self):
        svc = SftpService()
        executor = svc._executor
        svc.close()

        assert svc._sftp is None
        assert svc._ssh_client is None
        assert executor._shutdown is True

    def test_close_is_idempotent(self):
        svc = SftpService()
        svc.close()
        svc.close()  # 二次调用不应抛错


class TestTransferErrorPaths:
    def test_download_failure_returns_false(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        sftp.get.side_effect = IOError("net down")
        assert svc.download_file({}, "/r/a.vpk", "/l/a.vpk") is False

    def test_download_creates_local_dirs(self, tmp_path, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        local = tmp_path / "deep" / "dir" / "a.vpk"
        ok = svc.download_file({}, "/r/a.vpk", str(local))
        assert ok is True
        assert local.parent.exists()

    def test_upload_failure_returns_false(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        sftp.put.side_effect = IOError("quota")
        assert svc.upload_file({}, "/l/a.vpk", "/r/a.vpk") is False

    def test_file_exists_variants(self, monkeypatch):
        svc, sftp = _make_service_with_mock_sftp(monkeypatch)
        sftp.stat.return_value = MagicMock()
        assert svc.file_exists({}, "/r/a.vpk") is True
        sftp.stat.side_effect = FileNotFoundError()
        assert svc.file_exists({}, "/r/a.vpk") is False
        sftp.stat.side_effect = IOError("perm")
        assert svc.file_exists({}, "/r/a.vpk") is False

    def test_close_without_connection_is_safe(self):
        SftpService().close()
