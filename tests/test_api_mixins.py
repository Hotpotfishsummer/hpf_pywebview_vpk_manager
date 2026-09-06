"""API mixin 层(SftpApiMixin/AppApiMixin/VpkOpsApiMixin)的单元测试。

VpkManagerApi.__init__ 有真实副作用不可实例化,但三个 mixin 的方法只依赖
少量宿主属性——用最小宿主(stub 服务)直接测 mixin,覆盖此前无法触达的
API 错误处理与聚合逻辑。
"""

from unittest.mock import MagicMock

import pytest

from backend.api_app import AppApiMixin
from backend.api_ops import VpkOpsApiMixin
from backend.api_sftp import SftpApiMixin
from backend.services.storage_service import DEFAULT_SFTP_SETTINGS


class _Host:
    """mixin 需要的最小宿主:全部服务以 MagicMock 注入"""

    def __init__(self):
        self.storage_service = MagicMock()
        self.sftp_service = MagicMock()
        self.upload_service = MagicMock()
        self.download_service = MagicMock()
        self.scan_service = MagicMock()
        self.export_service = MagicMock()
        self.import_service = MagicMock()
        self.localize_service = MagicMock()
        self.metadata_service = MagicMock()
        self.config_service = MagicMock()
        self._window = None
        self._is_scanning = False
        self._is_exporting = False


class SftpHost(SftpApiMixin, _Host):
    pass


class AppHost(AppApiMixin, _Host):
    pass


class OpsHost(VpkOpsApiMixin, _Host):
    pass


class TestSftpApiMixin:
    def test_get_sftp_settings_error_returns_defaults(self):
        host = SftpHost()
        host.storage_service.get_sftp_settings.side_effect = IOError("disk")

        result = host.get_sftp_settings()

        assert result == DEFAULT_SFTP_SETTINGS
        assert result is not DEFAULT_SFTP_SETTINGS  # 不得共享可变默认

    def test_save_sftp_settings_success_and_failure(self):
        host = SftpHost()
        assert host.save_sftp_settings({"address": "h"}) == {"success": True}

        host.storage_service.save_sftp_settings.side_effect = IOError("ro")
        result = host.save_sftp_settings({})
        assert result["success"] is False and "ro" in result["error"]

    def test_list_remote_vpks(self):
        host = SftpHost()
        host.sftp_service.list_vpk_files.return_value = [{"name": "a.vpk"}]
        assert host.list_remote_vpks() == {"success": True, "files": [{"name": "a.vpk"}]}

        host.sftp_service.list_vpk_files.side_effect = ValueError("no path")
        result = host.list_remote_vpks()
        assert result["success"] is False and "no path" in result["error"]

    def test_delete_remote_vpk(self):
        host = SftpHost()
        host.sftp_service.delete_file_with_images.return_value = True
        assert host.delete_remote_vpk("/a.vpk") == {"success": True}

        host.sftp_service.delete_file_with_images.return_value = False
        assert host.delete_remote_vpk("/a.vpk")["success"] is False

    def test_delete_multiple_remote_vpks_aggregates(self):
        host = SftpHost()
        host.sftp_service.delete_file_with_images.side_effect = [True, False, True]

        result = host.delete_multiple_remote_vpks(["/a", "/b", "/c"])

        assert result == {
            "success": False,
            "success_count": 2,
            "error_count": 1,
            "errors": ["/b"],
        }

    def test_rename_remote_vpk(self):
        host = SftpHost()
        host.sftp_service.rename_file_with_images.return_value = True
        assert host.rename_remote_vpk("/a", "/b") == {"success": True}

    def test_download_requires_l4d2_directory(self):
        host = SftpHost()
        host.storage_service.get_l4d2_directory.return_value = None

        result = host.download_remote_vpks(["/a.vpk"])

        assert result["success"] is False
        host.download_service.download.assert_not_called()

    def test_download_delegates_to_service(self, tmp_path):
        host = SftpHost()
        host.storage_service.get_l4d2_directory.return_value = str(tmp_path)
        host.download_service.download.return_value = {"success": True, "downloaded_count": 1}

        result = host.download_remote_vpks(["/a.vpk"])

        assert result["downloaded_count"] == 1
        args = host.download_service.download.call_args.args
        assert args[0] == ["/a.vpk"]
        assert args[1] == str(tmp_path / "left4dead2" / "addons")

    def test_upload_requires_remote_addons_path(self):
        host = SftpHost()
        host.storage_service.get_sftp_settings.return_value = {"addons_path": ""}

        result = host.upload_local_vpks(["/a.vpk"])

        assert result["success"] is False
        host.upload_service.upload.assert_not_called()

    def test_upload_delegates_to_service(self):
        host = SftpHost()
        host.storage_service.get_sftp_settings.return_value = {"addons_path": "/srv/addons"}
        host.upload_service.upload.return_value = {"success": True, "uploaded_count": 2}

        result = host.upload_local_vpks(["/a.vpk", "/b.vpk"], better_naming=True)

        assert result["uploaded_count"] == 2
        args = host.upload_service.upload.call_args.args
        assert args[0] == ["/a.vpk", "/b.vpk"]
        assert args[1] == "/srv/addons"
        assert args[3] is True


class TestAppApiMixin:
    def test_get_last_directory(self):
        host = AppHost()
        host.storage_service.get_l4d2_directory.return_value = "/games/l4d2"
        assert host.get_last_directory() == "/games/l4d2"

        host.storage_service.get_l4d2_directory.side_effect = IOError("x")
        assert host.get_last_directory() == ""

    def test_get_downloads_directory_fallback_to_home(self, monkeypatch):
        host = AppHost()
        import backend.api_app as mod
        monkeypatch.setattr(mod.os.path, "exists", lambda p: False)

        result = host.get_downloads_directory()

        assert result.endswith("home") or result == str(mod.Path.home())

    def test_open_directory_rejects_missing_path(self):
        host = AppHost()
        assert host.open_directory("") is False
        assert host.open_directory("/definitely/not/exist") is False


class TestOpsApiMixin:
    def test_scan_reentry_guard(self):
        host = OpsHost()
        host._is_scanning = True

        result = host.scan_vpk_files("/some/dir")

        assert result["success"] is False
        assert "已在进行中" in result["error"]

    def test_scan_missing_directory(self, tmp_path):
        host = OpsHost()
        result = host.scan_vpk_files(str(tmp_path / "nope"))
        assert result["success"] is False
        assert "目录不存在" in result["error"]

    def test_scan_success_saves_directory_and_applies_config(self, tmp_path):
        host = OpsHost()
        host.scan_service.scan.return_value = {"local_vpks": [], "workshop_vpks": []}
        directory = tmp_path  # 真实存在的目录

        result = host.scan_vpk_files(str(directory))

        assert result == {"success": True, "local_vpks": [], "workshop_vpks": []}
        host.storage_service.save_l4d2_directory.assert_called_once_with(str(directory))
        host.config_service.apply_autoexec_template.assert_called_once_with(str(directory))
        assert host._is_scanning is False  # finally 复位

    def test_export_reentry_guard(self):
        host = OpsHost()
        host._is_exporting = True

        result = host.export_vpks([], "/out")

        assert result["success"] is False
        assert "已在进行中" in result["error"]

    def test_export_success_passes_titles(self, tmp_path):
        host = OpsHost()
        host.metadata_service.get_addontitle.return_value = "Title"
        host.export_service.export_vpks.return_value = str(tmp_path / "a.tar.zst")

        result = host.export_vpks(["/a.vpk"], str(tmp_path))

        assert result["success"] is True
        assert result["file_path"].endswith("a.tar.zst")
        assert host.export_service.export_vpks.call_args.kwargs["titles"] == ["Title"]

    def test_delete_multiple_aggregates(self, monkeypatch):
        host = OpsHost()
        # _disable_or_delete_single 是真删真改的静态方法,mock 掉
        monkeypatch.setattr(
            OpsHost, "_disable_or_delete_single",
            staticmethod(lambda file_path, disable: (_ for _ in ()).throw(IOError("boom")))
            if False else staticmethod(lambda file_path, disable: None),
        )

        result = host.delete_multiple_vpk_files(["/a", "/b"], disable=True)

        assert result["success"] is True
        assert result["success_count"] == 2
        assert result["error_count"] == 0

    def test_import_no_directory_selected(self, tmp_path):
        host = OpsHost()
        # 满足"addons 目录存在"前置,再让 webview 弹窗返回空 → 用户取消
        l4d2 = tmp_path / "l4d2"
        (l4d2 / "left4dead2" / "addons").mkdir(parents=True)
        host.storage_service.get_l4d2_directory.return_value = str(l4d2)
        host._window = MagicMock()
        host._window.create_file_dialog.return_value = ()

        result = host.import_compressed_vpks()

        # 契约:用户取消不算错误
        assert result["success"] is True
        assert result["imported_count"] == 0
        assert "取消" in result["message"]


class TestAppApiMixinDeep:
    def test_open_directory_uses_startfile_on_windows(self, monkeypatch):
        host = AppHost()
        import backend.api_app as mod
        real_exists = mod.os.path.exists
        monkeypatch.setattr(mod.os.path, "exists", lambda p: True)
        monkeypatch.setattr(mod.os.path, "isdir", lambda p: True)
        called = {}
        monkeypatch.setattr(mod.os, "startfile", lambda p: called.setdefault("dir", p))
        monkeypatch.setattr(mod.sys, "platform", "win32")

        assert host.open_directory("/some/dir") is True
        assert called["dir"] == "/some/dir"

    def test_open_directory_file_opens_parent(self, monkeypatch):
        host = AppHost()
        import backend.api_app as mod
        monkeypatch.setattr(mod.os.path, "exists", lambda p: True)
        monkeypatch.setattr(mod.os.path, "isdir", lambda p: False)
        monkeypatch.setattr(mod.os.path, "dirname", lambda p: "/parent")
        called = {}
        monkeypatch.setattr(mod.os, "startfile", lambda p: called.setdefault("dir", p))
        monkeypatch.setattr(mod.sys, "platform", "win32")

        assert host.open_directory("/parent/file.vpk") is True
        assert called["dir"] == "/parent"

    def test_browse_directory_with_dialog_result_list(self, monkeypatch):
        host = AppHost()
        import backend.api_app as mod
        host._window = MagicMock()
        host._window.create_file_dialog.return_value = ("/picked/dir",)
        host.storage_service.get_l4d2_directory.return_value = None
        monkeypatch.setattr(mod.Path, "home", lambda: mod.Path("/home"))

        assert host.browse_directory() == "/picked/dir"

    def test_browse_directory_user_cancel(self):
        host = AppHost()
        host._window = MagicMock()
        host._window.create_file_dialog.return_value = ()

        assert host.browse_directory() is None

    def test_open_external_url_opens_browser(self, monkeypatch):
        host = AppHost()
        import backend.api_app as mod
        called = {}
        monkeypatch.setattr(mod.webbrowser, "open", lambda url: called.setdefault("url", url))

        host.open_external_url("https://example.com")

        assert called["url"] == "https://example.com"

    def test_reset_app_data_keeps_preferences_and_exits(self, tmp_path, monkeypatch):
        """重置:删除除 preferences.json 外的所有内容,随后 os._exit(不真退)"""
        host = AppHost()
        import backend.api_app as mod

        storage_dir = tmp_path / "Documents" / "L4D2-VPK-Manager"
        storage_dir.mkdir(parents=True)
        (storage_dir / "preferences.json").write_text("{}", encoding="utf-8")
        (storage_dir / "vpk_manager.log").write_text("log", encoding="utf-8")
        (storage_dir / ".vpk_config").mkdir()
        (storage_dir / ".vpk_config" / "c.json").write_text("{}", encoding="utf-8")

        monkeypatch.setattr(mod.Path, "home", lambda: tmp_path)
        exited = {}
        def fake_exit(code=0):
            exited["code"] = code
            raise SystemExit
        monkeypatch.setattr(mod.os, "_exit", fake_exit)

        with pytest.raises(SystemExit):
            host.reset_app_data()

        assert exited["code"] == 0
        assert (storage_dir / "preferences.json").exists()
        assert not (storage_dir / "vpk_manager.log").exists()
        assert not (storage_dir / ".vpk_config").exists()

    def test_reset_app_data_missing_dir_returns_true(self, tmp_path, monkeypatch):
        host = AppHost()
        import backend.api_app as mod
        monkeypatch.setattr(mod.Path, "home", lambda: tmp_path)
        assert host.reset_app_data() is True
