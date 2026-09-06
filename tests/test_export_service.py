"""vpk_export_service 纯函数的单元测试"""

import pytest

from backend.services.vpk_export_service import VpkExportService


class TestGenerateArchiveName:
    def test_uses_titles_when_given(self):
        name = VpkExportService._generate_archive_name(
            ["a.vpk", "b.vpk"], titles=["Mod One", "Mod Two"]
        )
        assert name == "Mod One-Mod Two"

    def test_pads_missing_titles_with_filename_stems(self):
        name = VpkExportService._generate_archive_name(
            ["a.vpk", "b.vpk", "c.vpk"], titles=["Only One"]
        )
        assert name == "Only One-b-c"

    def test_no_titles_uses_stems(self):
        name = VpkExportService._generate_archive_name(["a.vpk", "b.vpk"])
        assert name == "a-b"

    def test_more_than_three_files_appends_count(self):
        paths = ["1.vpk", "2.vpk", "3.vpk", "4.vpk", "5.vpk"]
        name = VpkExportService._generate_archive_name(paths, titles=None)
        assert name == "1-2-3-and-2-more"

    def test_illegal_chars_replaced_with_underscore(self):
        name = VpkExportService._generate_archive_name(
            ['x.vpk'], titles=['bad:name?*']
        )
        assert ":" not in name and "?" not in name and "*" not in name
        assert name == "bad_name__"

    def test_long_name_truncated(self):
        name = VpkExportService._generate_archive_name(
            ["x.vpk"], titles=["t" * 300]
        )
        assert len(name) <= 100
        assert name.endswith("...")

    def test_blank_title_falls_back_to_timestamped_name(self):
        name = VpkExportService._generate_archive_name(["x.vpk"], titles=["   "])
        assert name.startswith("vpk_export_")

    def test_result_is_windows_safe_filename(self):
        name = VpkExportService._generate_archive_name(
            ["x.vpk"], titles=['a<b>c:d"e/f\\g|h?i*j']
        )
        assert not any(c in name for c in '<>:"/\\|?*')


class TestMissingDependency:
    def test_export_without_zstd_raises_clear_error(self, tmp_path, monkeypatch):
        """环境缺 zstandard 时导出应抛清晰错误"""
        import backend.services.vpk_export_service as mod
        monkeypatch.setattr(mod, "HAS_ZSTD", False)

        with pytest.raises(Exception, match="zstandard"):
            VpkExportService.export_vpks(["/a.vpk"], str(tmp_path))


class TestEmptyInputGuard:
    def test_empty_file_list_raises(self, tmp_path):
        with pytest.raises(Exception, match="No files selected"):
            VpkExportService.export_vpks([], str(tmp_path))
