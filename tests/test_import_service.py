"""vpk_import_service 纯函数的单元测试"""

from backend.services.vpk_import_service import VpkImportService


class TestIsVpkOrImage:
    def test_vpk(self):
        assert VpkImportService._is_vpk_or_image("addon.vpk") is True

    def test_vpk_case_insensitive(self):
        assert VpkImportService._is_vpk_or_image("ADDON.VPK") is True

    def test_nested_path_with_basename_vpk(self):
        assert VpkImportService._is_vpk_or_image("folder/sub/addon.vpk") is True

    def test_common_images(self):
        for name in ["a.jpg", "a.jpeg", "a.png", "a.tga", "a.bmp", "a.gif"]:
            assert VpkImportService._is_vpk_or_image(name) is True, name

    def test_rejects_other_extensions(self):
        for name in ["a.txt", "a.zip", "a.7z", "a.tar.zst", "a.vpk.disabled"]:
            assert VpkImportService._is_vpk_or_image(name) is False, name

    def test_rejects_empty_and_directory_names(self):
        assert VpkImportService._is_vpk_or_image("") is False
        assert VpkImportService._is_vpk_or_image("folder/") is False
