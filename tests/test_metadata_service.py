"""vpk_metadata_service 的单元测试(使用 tmp_path,不触碰真实用户数据)"""

import os
import pathlib

from unittest.mock import MagicMock

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

    def test_save_is_atomic_no_tmp_left_and_overwrites(self, tmp_path):
        svc = _make_service(tmp_path)
        vpk_path = str(tmp_path / "mymod.vpk")
        assert svc.save_metadata(vpk_path, {"addontitle": "v1"}) is True
        assert svc.save_metadata(vpk_path, {"addontitle": "v2"}) is True

        assert not (tmp_path / "vpk_config" / "mymod.json.tmp").exists()
        assert svc.load_metadata(vpk_path) == {"addontitle": "v2"}

    def test_corrupt_cache_returns_none(self, tmp_path):
        svc = _make_service(tmp_path)
        (tmp_path / "vpk_config").mkdir(exist_ok=True)
        (tmp_path / "vpk_config" / "broken.json").write_text("{corrupt", encoding="utf-8")
        assert svc.load_metadata(str(tmp_path / "broken.vpk")) is None

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


class TestCacheInvalidation:
    """缓存带 mtime/size 失效校验(backlog #3)"""

    def _make_vpk(self, tmp_path, name="mod.vpk", content=b""):
        vpk_file = tmp_path / name
        vpk_file.write_bytes(content)
        return str(vpk_file)

    def test_fresh_cache_hit_does_not_reextract(self, tmp_path, monkeypatch):
        svc = _make_service(tmp_path)
        vpk_path = self._make_vpk(tmp_path)

        # 首次提取建立缓存
        monkeypatch.setattr(svc, "extract_addontitle", lambda p: "Title V1")
        assert svc.get_or_extract_metadata(vpk_path)["addontitle"] == "Title V1"

        # 文件未变 → 命中缓存,不再调用 extract
        monkeypatch.setattr(
            svc, "extract_addontitle",
            lambda p: (_ for _ in ()).throw(AssertionError("不应重新提取")),
        )
        assert svc.get_or_extract_metadata(vpk_path)["addontitle"] == "Title V1"

    def test_stale_cache_reextracts_on_mtime_change(self, tmp_path, monkeypatch):
        svc = _make_service(tmp_path)
        vpk_path = self._make_vpk(tmp_path, content=b"v1")

        monkeypatch.setattr(svc, "extract_addontitle", lambda p: "Title V1")
        svc.get_or_extract_metadata(vpk_path)

        # 文件被替换(mtime 变化) → 缓存失效,重新提取并回写
        import os
        future = svc.load_metadata(vpk_path)["source_mtime"] + 100
        os.utime(vpk_path, (future, future))
        monkeypatch.setattr(svc, "extract_addontitle", lambda p: "Title V2")
        assert svc.get_or_extract_metadata(vpk_path)["addontitle"] == "Title V2"
        assert svc.load_metadata(vpk_path)["addontitle"] == "Title V2"

    def test_stale_cache_reextracts_on_size_change(self, tmp_path, monkeypatch):
        svc = _make_service(tmp_path)
        vpk_path = self._make_vpk(tmp_path, content=b"12345678")

        monkeypatch.setattr(svc, "extract_addontitle", lambda p: "Old")
        svc.get_or_extract_metadata(vpk_path)

        # 只改大小不改名的场景:内容变化导致 size 不同
        vpk_path_obj = tmp_path / "mod.vpk"
        vpk_path_obj.write_bytes(b"123456789")
        monkeypatch.setattr(svc, "extract_addontitle", lambda p: "New")
        assert svc.get_or_extract_metadata(vpk_path)["addontitle"] == "New"

    def test_legacy_cache_without_stat_keys_is_invalidated(self, tmp_path, monkeypatch):
        svc = _make_service(tmp_path)
        vpk_path = self._make_vpk(tmp_path)

        # 旧格式缓存(无 source_mtime/source_size) → 视为失效
        svc.save_metadata(vpk_path, {"addontitle": "Legacy"})
        monkeypatch.setattr(svc, "extract_addontitle", lambda p: "Fresh")
        assert svc.get_or_extract_metadata(vpk_path)["addontitle"] == "Fresh"
        # 新缓存带上了 stat 键
        refreshed = svc.load_metadata(vpk_path)
        assert "source_mtime" in refreshed and "source_size" in refreshed

    def test_missing_file_keeps_old_cache_behavior(self, tmp_path):
        svc = _make_service(tmp_path)
        ghost = str(tmp_path / "ghost.vpk")

        # 文件不存在 → 提取失败落空缓存 → 再查仍命中缓存且返回 None
        assert svc.get_or_extract_metadata(ghost) is None
        assert svc.get_or_extract_metadata(ghost) is None

    def test_get_addontitle_unaffected_by_extra_keys(self, tmp_path, monkeypatch):
        svc = _make_service(tmp_path)
        vpk_path = self._make_vpk(tmp_path)
        monkeypatch.setattr(svc, "extract_addontitle", lambda p: "T")
        assert svc.get_addontitle(vpk_path) == "T"


class TestStaleTmpCleanup:
    def test_stale_tmp_files_cleaned_on_init(self, tmp_path):
        cfg = tmp_path / "vpk_config"
        cfg.mkdir()
        (cfg / "mod.json.tmp").write_text("{}", encoding="utf-8")

        VpkMetadataService(config_dir=str(cfg))

        assert list(cfg.glob("*.json.tmp")) == []


class TestCacheInvalidationBySize:
    def test_same_mtime_different_size_invalidates(self, tmp_path):
        """mtime 相同而 size 变化(罕见但可能)也必须失效重提取"""
        svc = _make_service(tmp_path)
        vpk_path = tmp_path / "mod.vpk"
        vpk_path.write_bytes(b"v1")
        svc.get_or_extract_metadata(str(vpk_path))  # 建立缓存

        # 强制 size 变化但保持 mtime 不变
        st = vpk_path.stat()
        vpk_path.write_bytes(b"v1 with different length")
        os.utime(vpk_path, (st.st_atime, st.st_mtime))

        fresh = svc.get_or_extract_metadata(str(vpk_path))
        # 重新提取后缓存里的 stat 与文件一致
        assert fresh["source_size"] == vpk_path.stat().st_size


class TestErrorPaths:
    def test_save_metadata_failure_returns_false_and_cleans_tmp(self, tmp_path):
        # 把 config 目录变成文件,使写入必然失败
        cfg_file = tmp_path / "not_a_dir"
        cfg_file.write_text("", encoding="utf-8")
        broken = VpkMetadataService.__new__(VpkMetadataService)
        broken.config_dir = cfg_file

        assert broken.save_metadata(str(tmp_path / "m.vpk"), {"a": 1}) is False
        assert list(tmp_path.glob("*.tmp")) == []

    def test_unreadable_thumbnail_is_skipped(self, tmp_path):
        # 缩略图位置放一个目录,读取必然失败但不影响元数据返回
        vpk_file = tmp_path / "mod.vpk"
        vpk_file.write_bytes(b"x")
        (tmp_path / "mod.jpg").mkdir()

        svc = _make_service(tmp_path)
        meta = svc.get_vpk_metadata(str(vpk_file))

        assert meta is not None
        assert meta.thumbnail_path is None


class TestDefensiveBranches:
    def test_stale_tmp_cleanup_failure_is_silent(self, tmp_path, monkeypatch):
        cfg = tmp_path / "vpk_config"
        cfg.mkdir()
        stale = cfg / "old.json.tmp"
        stale.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(
            pathlib.Path, "unlink",
            lambda self, missing_ok=False: (_ for _ in ()).throw(OSError("locked")),
        )
        VpkMetadataService(config_dir=str(cfg))
        assert stale.exists()  # 清理失败但初始化不崩

    def test_save_failure_cleans_tmp_file(self, tmp_path):
        # 目标 json 路径是目录 → open 失败,tmp 清理路径走 unlink(missing_ok=True)
        svc = _make_service(tmp_path)
        cfg = tmp_path / "vpk_config"
        cfg.mkdir(exist_ok=True)
        (cfg / "blocker.json").mkdir()  # 同名目录使 os.replace 失败

        result = svc.save_metadata(str(tmp_path / "blocker.vpk"), {"a": 1})

        assert result is False

    def test_addoninfo_read_failure_returns_none(self, tmp_path, monkeypatch):
        """addoninfo.txt 字节流读取失败时返回 None 而非崩溃"""
        import vpk as vpk_lib
        svc = _make_service(tmp_path)

        fake_entry = MagicMock()
        fake_entry.read.side_effect = IOError("read boom")
        fake_vpk = MagicMock()
        fake_vpk.__contains__ = lambda self, k: k == "addoninfo.txt"
        fake_vpk.__getitem__ = lambda self, k: fake_entry
        monkeypatch.setattr(vpk_lib, "VPK", lambda path: fake_vpk)

        assert svc.extract_addontitle(str(tmp_path / "whatever.vpk")) is None

    def test_parse_addontitle_non_string_content_returns_none(self):
        svc = VpkMetadataService.__new__(VpkMetadataService)
        assert svc._parse_addontitle(12345) is None  # 非 str 触发异常分支


class TestThumbnailPriority:
    def test_jpg_preferred_over_png(self, tmp_path):
        """同名多格式缩略图按 jpg > png > jpeg 优先"""
        vpk_file = tmp_path / "mod.vpk"
        vpk_file.write_bytes(b"x")
        (tmp_path / "mod.png").write_bytes(b"png")
        (tmp_path / "mod.jpg").write_bytes(b"jpg")

        svc = _make_service(tmp_path)
        meta = svc.get_vpk_metadata(str(vpk_file))

        assert meta is not None
        assert meta.thumbnail_path.startswith("data:image/jpeg")

    def test_png_used_when_no_jpg(self, tmp_path):
        vpk_file = tmp_path / "mod.vpk"
        vpk_file.write_bytes(b"x")
        (tmp_path / "mod.png").write_bytes(b"png")

        svc = _make_service(tmp_path)
        meta = svc.get_vpk_metadata(str(vpk_file))

        assert meta is not None
        assert meta.thumbnail_path.startswith("data:image/png")
