"""backend.naming 共享命名逻辑的单元测试"""

from backend.naming import (
    build_export_base_name,
    extract_workshop_id,
    find_associated_images,
    sanitize_addon_title,
    vpk_stem_for_association,
)


class TestExtractWorkshopId:
    def test_extracts_long_number(self):
        assert extract_workshop_id("123456789.vpk") == "123456789"

    def test_ignores_short_numbers(self):
        assert extract_workshop_id("1234567.vpk") == ""

    def test_extracts_from_mixed_name(self):
        assert extract_workshop_id("some_mod_2233445566_v2.vpk") == "2233445566"

    def test_empty_filename(self):
        assert extract_workshop_id("") == ""


class TestSanitizeAddonTitle:
    def test_spaces_to_underscores(self):
        assert sanitize_addon_title("My Cool Mod") == "My_Cool_Mod"

    def test_illegal_chars_replaced(self):
        result = sanitize_addon_title('a<b>c:d"e/f\\g|h?i*j')
        assert not any(c in result for c in '<>:"/\\|?*')

    def test_consecutive_underscores_merged(self):
        assert sanitize_addon_title("a  b??c") == "a_b_c"

    def test_strips_whitespace(self):
        # 注意:空格先被替换为下划线,str.strip() 只剥空白字符,
        # 因此首尾空格会保留为下划线(与原三处实现的怪癖保持一致)
        assert sanitize_addon_title("  x  ") == "_x_"
        # 制表符属于控制字符,按非法字符规则替换为下划线
        assert sanitize_addon_title("x\ty") == "x_y"


class TestBuildExportBaseName:
    def test_uses_cleaned_title(self):
        assert build_export_base_name("My Mod", "nomods.vpk", "nomods") == "My_Mod"

    def test_id_extracted_from_numeric_filename(self):
        assert build_export_base_name("My Mod", "12345678.vpk", "12345678") == "My_Mod-12345678"

    def test_appends_workshop_id(self):
        result = build_export_base_name("My Mod", "99887766554433.vpk", "99887766554433")
        assert result == "My_Mod-99887766554433"

    def test_no_id_in_filename(self):
        assert build_export_base_name("My Mod", "nomods.vpk", "nomods") == "My_Mod"

    def test_id_not_duplicated_if_already_in_title(self):
        result = build_export_base_name("Mod 99887766554433", "99887766554433.vpk", "99887766554433")
        assert result == "Mod_99887766554433"

    def test_falsy_title_falls_back_to_stem(self):
        assert build_export_base_name(None, "12345678.vpk", "12345678") == "12345678"
        assert build_export_base_name("", "12345678.vpk", "12345678") == "12345678"

    def test_title_of_only_illegal_chars_falls_back_to_stem(self):
        # 全部字符都是非法字符 → 清洗后只剩空/下划线 → 回退 stem
        assert build_export_base_name("???*", "backup.vpk", "backup") == "backup"

    def test_fallback_stem_has_no_id_appended(self):
        # 回退分支不追加工坊 ID(与原三处实现一致)
        assert build_export_base_name(None, "999888777666.vpk", "orig") == "orig"


class TestVpkStemForAssociation:
    def test_enabled_vpk(self):
        assert vpk_stem_for_association("mod.vpk") == "mod"

    def test_disabled_vpk_keeps_vpk_in_stem(self):
        # 与缩略图扫描约定一致:禁用文件的图片是 x.vpk.jpg
        assert vpk_stem_for_association("mod.vpk.disabled") == "mod.vpk"

    def test_case_insensitive_disabled_suffix(self):
        assert vpk_stem_for_association("mod.VPK.DISABLED") == "mod.VPK"


class TestFindAssociatedImages:
    def test_matches_case_insensitively(self, tmp_path):
        (tmp_path / "Mod.jpg").write_bytes(b"x")
        (tmp_path / "mod.PNG").write_bytes(b"x")
        results = find_associated_images(str(tmp_path), "mod.vpk")
        assert sorted(ext for _, ext in results) == [".jpg", ".png"]

    def test_dedups_same_ext_different_case(self, tmp_path):
        (tmp_path / "mod.jpg").write_bytes(b"x")
        (tmp_path / "mod.JPG").write_bytes(b"x")
        results = find_associated_images(str(tmp_path), "mod.vpk")
        assert [ext for _, ext in results] == [".jpg"]

    def test_filters_non_image_and_other_stems(self, tmp_path):
        (tmp_path / "mod.txt").write_bytes(b"x")
        (tmp_path / "other.jpg").write_bytes(b"x")
        assert find_associated_images(str(tmp_path), "mod.vpk") == []

    def test_disabled_default_keeps_vpk_in_stem(self, tmp_path):
        # 默认(导出/本地化约定):x.vpk.disabled 的图片是 x.vpk.jpg
        (tmp_path / "mod.vpk.jpg").write_bytes(b"x")
        (tmp_path / "mod.jpg").write_bytes(b"x")
        results = find_associated_images(str(tmp_path), "mod.vpk.disabled")
        assert [ext for _, ext in results] == [".jpg"]
        assert results[0][0].endswith("mod.vpk.jpg")

    def test_strip_vpk_suffix_for_upload_convention(self, tmp_path):
        # 上传约定:x.vpk.disabled 的图片是 x.jpg
        (tmp_path / "mod.jpg").write_bytes(b"x")
        (tmp_path / "mod.vpk.jpg").write_bytes(b"x")
        results = find_associated_images(str(tmp_path), "mod.vpk.disabled", strip_vpk_suffix=True)
        assert [ext for _, ext in results] == [".jpg"]
        assert results[0][0].endswith("mod.jpg")

    def test_custom_exts(self, tmp_path):
        (tmp_path / "mod.tga").write_bytes(b"x")
        results = find_associated_images(str(tmp_path), "mod.vpk", exts=(".tga",))
        assert len(results) == 1

    def test_missing_directory_returns_empty(self, tmp_path):
        assert find_associated_images(str(tmp_path / "nope"), "mod.vpk") == []


class TestBuildExportBaseNameEdgeCases:
    def test_empty_string_title_falls_back(self):
        assert build_export_base_name("", "mod.vpk", "fallback") == "fallback"

    def test_whitespace_only_title_falls_back(self):
        assert build_export_base_name("   ", "mod.vpk", "fallback") == "fallback"

    def test_underscore_only_title_falls_back(self):
        assert build_export_base_name("___", "mod.vpk", "fallback") == "fallback"

    def test_overlong_title_truncated_to_limit(self):
        # 超长标题截断到 120 字符,避免突破 Windows 路径上限
        title = "很长的标题" * 50
        name = build_export_base_name(title, "mod.vpk", "fallback")
        assert len(name) == 120

    def test_truncated_title_still_appends_workshop_id(self):
        title = "a" * 200
        name = build_export_base_name(title, "123456789.vpk", "fallback")
        assert name.endswith("-123456789")
        assert len(name) == 120 + len("-123456789")

    def test_quotes_and_brackets_sanitized(self):
        assert build_export_base_name('a"b:c<d>', "mod.vpk", "fb") == "a_b_c_d_"


class TestExtractWorkshopIdEdgeCases:
    def test_exactly_eight_digits(self):
        assert extract_workshop_id("x12345678.vpk") == "12345678"

    def test_long_digit_run_taken_whole(self):
        # 贪婪匹配:整个连续数字段视为 ID
        assert extract_workshop_id("x12345678901.vpk") == "12345678901"


class TestVpkStemForAssociationEdgeCases:
    def test_plain_disabled_file_without_vpk(self):
        assert vpk_stem_for_association("readme.disabled") == "readme"

    def test_disabled_suffix_must_be_tail(self):
        # 'disabled' 出现在中间不算禁用后缀
        assert vpk_stem_for_association("mod.disabled.vpk") == "mod.disabled"
