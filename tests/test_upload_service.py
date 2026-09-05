"""VpkUploadService 的单元测试(mock SFTP,tmp 隔离)"""

from unittest.mock import MagicMock

from backend.services.vpk_metadata_service import VpkMetadataService
from backend.services.vpk_upload_service import VpkUploadService


def _make_service(tmp_path, upload_ok=True):
    meta = VpkMetadataService(config_dir=str(tmp_path / "cfg"))
    sftp = MagicMock()
    sftp.upload_file.return_value = upload_ok
    return VpkUploadService(meta, sftp), sftp


def _make_files(tmp_path, name="mod.vpk", images=("mod.jpg",)):
    for img in images:
        (tmp_path / img).write_bytes(b"img")
    (tmp_path / name).write_bytes(b"vpk")
    return str(tmp_path / name)


class TestUpload:
    def test_uploads_vpk_with_original_name(self, tmp_path):
        svc, sftp = _make_service(tmp_path)
        vpk_path = _make_files(tmp_path)

        result = svc.upload([vpk_path], "/remote/addons", {"addons_path": "/remote/addons"})

        assert result == {"success": True, "uploaded_count": 1}
        targets = [c.args[2] for c in sftp.upload_file.call_args_list]
        assert "/remote/addons/mod.vpk" in targets

    def test_uploads_associated_image(self, tmp_path):
        svc, sftp = _make_service(tmp_path)
        vpk_path = _make_files(tmp_path)

        svc.upload([vpk_path], "/remote/addons", {})

        targets = [c.args[2] for c in sftp.upload_file.call_args_list]
        assert "/remote/addons/mod.jpg" in targets

    def test_disabled_file_keeps_suffix(self, tmp_path):
        svc, sftp = _make_service(tmp_path)
        vpk_path = _make_files(tmp_path, name="off.vpk.disabled", images=("off.jpg",))

        svc.upload([vpk_path], "/remote/addons", {})

        targets = [c.args[2] for c in sftp.upload_file.call_args_list]
        assert "/remote/addons/off.vpk.disabled" in targets
        # 上传侧约定:禁用文件匹配 x.jpg
        assert "/remote/addons/off.jpg" in targets

    def test_better_naming_with_workshop_id(self, tmp_path, monkeypatch):
        svc, sftp = _make_service(tmp_path)
        (tmp_path / "12345678.vpk").write_bytes(b"vpk")
        monkeypatch.setattr(
            svc.metadata_service, "get_addontitle", lambda p: "My Mod"
        )

        svc.upload([str(tmp_path / "12345678.vpk")], "/remote/addons", {}, better_naming=True)

        targets = [c.args[2] for c in sftp.upload_file.call_args_list]
        assert "/remote/addons/My_Mod-12345678.vpk" in targets

    def test_multiple_files_counted(self, tmp_path):
        svc, sftp = _make_service(tmp_path)
        a = _make_files(tmp_path / "a" if False else tmp_path, name="a.vpk", images=())
        b = _make_files(tmp_path, name="b.vpk", images=())

        result = svc.upload([a, b], "/remote/addons", {})

        assert result["uploaded_count"] == 2

    def test_upload_failure_not_counted(self, tmp_path):
        svc, sftp = _make_service(tmp_path, upload_ok=False)
        vpk_path = _make_files(tmp_path)

        result = svc.upload([vpk_path], "/remote/addons", {})

        assert result["uploaded_count"] == 0
