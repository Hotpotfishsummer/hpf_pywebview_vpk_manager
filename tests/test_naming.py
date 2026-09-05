"""backend.naming 共享命名逻辑的单元测试"""

from backend.naming import (
    build_export_base_name,
    extract_workshop_id,
    sanitize_addon_title,
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
