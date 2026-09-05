"""VpkDownloadService 的单元测试(mock SFTP)"""

from unittest.mock import MagicMock

from backend.services.vpk_download_service import VpkDownloadService


def _make_service(existing=()):
    sftp = MagicMock()
    sftp.download_file.return_value = True
    sftp.file_exists.side_effect = lambda cfg, p: p in set(existing)
    return VpkDownloadService(sftp), sftp


class TestDownload:
    def test_downloads_vpk_to_local_addons(self, tmp_path):
        svc, sftp = _make_service()

        result = svc.download(["/remote/mod.vpk"], str(tmp_path), {})

        assert result == {"success": True, "downloaded_count": 1}
        assert sftp.download_file.call_args_list[0].args[1:] == ("/remote/mod.vpk", str(tmp_path / "mod.vpk"))

    def test_downloads_associated_image(self, tmp_path):
        svc, sftp = _make_service(existing=["/remote/mod.jpg"])

        svc.download(["/remote/mod.vpk"], str(tmp_path), {})

        targets = [c.args[1] for c in sftp.download_file.call_args_list]
        assert "/remote/mod.jpg" in targets

    def test_disabled_vpk_uses_vpk_stem_for_image(self, tmp_path):
        svc, sftp = _make_service(existing=["/remote/mod.vpk.jpg"])

        svc.download(["/remote/mod.vpk.disabled"], str(tmp_path), {})

        targets = [c.args[1] for c in sftp.download_file.call_args_list]
        assert "/remote/mod.vpk.jpg" in targets
        assert "/remote/mod.jpg" not in targets

    def test_vpk_failure_skips_images(self, tmp_path):
        svc, sftp = _make_service(existing=["/remote/mod.jpg"])
        sftp.download_file.return_value = False

        result = svc.download(["/remote/mod.vpk"], str(tmp_path), {})

        assert result["downloaded_count"] == 0
        # VPK 下载失败后不再尝试图片
        assert sftp.download_file.call_count == 1

    def test_multiple_files_counted(self, tmp_path):
        svc, sftp = _make_service()

        result = svc.download(["/remote/a.vpk", "/remote/b.vpk"], str(tmp_path), {})

        assert result["downloaded_count"] == 2
