"""vpk_metadata_service 的单元测试(使用 tmp_path,不触碰真实用户数据)"""

from backend.services.vpk_metadata_service import VpkMetadataService


def _make_service(tmp_path):
    return VpkMetadataService(config_dir=str(tmp_path / "vpk_config"))


class TestParseAddontitle:
    def setup_method(self):
        self.svc = VpkMetadataService.__new__(VpkMetadataService)

    def test_unquoted_key_format(self):
        assert self.svc._parse_addontitle('addontitle "My Mod"') == "My Mod"

    def test_quoted_key_format(self):
        assert self.svc._parse_addontitle('"addontitle" "My Mod"') == "My Mod"

    def test_case_insensitive_key(self):
        assert self.svc._parse_addontitle('ADDONTITLE "x"') == "x"

    def test_finds_title_among_lines(self):
        content = 'addonversion "1.0"\naddontitle "The Title"\naddonauthor "me"\n'
        assert self.svc._parse_addontitle(content) == "The Title"

    def test_no_title_returns_none(self):
        assert self.svc._parse_addontitle('addonauthor "me"') is None
        assert self.svc._parse_addontitle("") is None

    def test_indented_line(self):
        assert self.svc._parse_addontitle('  addontitle "Spaced"') == "Spaced"


class TestMetadataCache:
    def test_load_missing_returns_none(self, tmp_path):
        svc = _make_service(tmp_path)
        assert svc.load_metadata(str(tmp_path / "nope.vpk")) is None

    def test_save_load_roundtrip(self, tmp_path):
        svc = _make_service(tmp_path)
        vpk_path = str(tmp_path / "mymod.vpk")
        assert svc.save_metadata(vpk_path, {"addontitle": "T"}) is True
        assert svc.load_metadata(vpk_path) == {"addontitle": "T"}

    def test_json_file_lives_in_config_dir(self, tmp_path):
        svc = _make_service(tmp_path)
        vpk_path = str(tmp_path / "mymod.vpk")
        svc.save_metadata(vpk_path, {})
        assert (tmp_path / "vpk_config" / "mymod.json").exists()

    def test_save_none_saves_empty_object(self, tmp_path):
        svc = _make_service(tmp_path)
        vpk_path = str(tmp_path / "mymod.vpk")
        assert svc.save_metadata(vpk_path, None) is True
        assert svc.load_metadata(vpk_path) == {}

    def test_extract_addontitle_on_missing_file_returns_none(self, tmp_path):
        svc = _make_service(tmp_path)
        assert svc.extract_addontitle(str(tmp_path / "ghost.vpk")) is None

    def test_get_or_extract_metadata_missing_file_returns_none(self, tmp_path):
        svc = _make_service(tmp_path)
        missing = str(tmp_path / "ghost.vpk")
        assert svc.get_or_extract_metadata(missing) is None
        # 失败也会落一个空缓存文件,后续直接命中缓存
        assert svc.load_metadata(missing) == {}


class TestGetVpkMetadata:
    def test_basic_fields_for_existing_file(self, tmp_path):
        svc = _make_service(tmp_path)
        vpk_file = tmp_path / "mod.vpk"
        vpk_file.write_bytes(b"")

        result = svc.get_vpk_metadata(str(vpk_file))

        assert result is not None
        assert result.name == "mod.vpk"
        assert result.size == 0
        assert result.is_valid is True
        assert result.is_disabled is False
        assert result.addontitle is None
        assert result.display_name == "mod.vpk"
        assert result.thumbnail_path is None

    def test_disabled_suffix_detected(self, tmp_path):
        svc = _make_service(tmp_path)
        vpk_file = tmp_path / "mod.vpk.disabled"
        vpk_file.write_bytes(b"")

        result = svc.get_vpk_metadata(str(vpk_file))

        assert result is not None
        assert result.is_disabled is True

    def test_missing_file_returns_none(self, tmp_path):
        svc = _make_service(tmp_path)
        assert svc.get_vpk_metadata(str(tmp_path / "ghost.vpk")) is None
