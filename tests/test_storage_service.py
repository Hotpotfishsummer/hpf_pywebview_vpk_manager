"""StorageService 的单元测试(monkeypatch Path.home 隔离 + 单例重置)"""

import json

import pytest

from backend.services import storage_service as ss_mod
from backend.services.storage_service import StorageService


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    """把 Path.home 指向 tmp_path 并重置单例,结束后还原"""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(ss_mod.Path, "home", lambda: fake_home)
    original = StorageService._instance
    StorageService._instance = None
    yield fake_home, StorageService()
    StorageService._instance = original


class TestPreferences:
    def test_set_get(self, isolated_storage):
        _, svc = isolated_storage
        svc.set("key", "value")
        assert svc.get("key") == "value"

    def test_get_default(self, isolated_storage):
        _, svc = isolated_storage
        assert svc.get("missing") is None
        assert svc.get("missing", "dft") == "dft"

    def test_remove_and_clear(self, isolated_storage):
        _, svc = isolated_storage
        svc.set("a", 1)
        svc.set("b", 2)
        svc.remove("a")
        assert svc.get("a") is None
        svc.clear()
        assert svc.get("b") is None

    def test_persists_to_preferences_json(self, isolated_storage):
        home, svc = isolated_storage
        svc.set("l4d2_directory", "C:/Games/L4D2")

        pref_file = home / "Documents" / "L4D2-VPK-Manager" / "preferences.json"
        assert json.loads(pref_file.read_text(encoding="utf-8"))["l4d2_directory"] == "C:/Games/L4D2"

        # 新实例(重置单例后)能从磁盘恢复
        StorageService._instance = None
        svc2 = StorageService()
        assert svc2.get("l4d2_directory") == "C:/Games/L4D2"


class TestSftpSettings:
    def test_defaults_when_missing(self, isolated_storage):
        _, svc = isolated_storage
        settings = svc.get_sftp_settings()
        assert settings == {"address": "", "username": "", "password": "", "addons_path": ""}

    def test_save_and_reload(self, isolated_storage):
        home, svc = isolated_storage
        cfg = {"address": "host:22", "username": "u", "password": "p", "addons_path": "/addons"}
        svc.save_sftp_settings(cfg)

        StorageService._instance = None
        assert StorageService().get_sftp_settings() == cfg


class TestL4d2Directory:
    def test_save_get_roundtrip(self, isolated_storage):
        _, svc = isolated_storage
        assert svc.get_l4d2_directory() is None
        svc.save_l4d2_directory("/games/l4d2")
        assert svc.get_l4d2_directory() == "/games/l4d2"


class TestAtomicWrite:
    def test_no_tmp_file_left_after_save(self, isolated_storage):
        home, svc = isolated_storage
        svc.set("key", "value")

        storage_dir = home / "Documents" / "L4D2-VPK-Manager"
        assert not (storage_dir / "preferences.json.tmp").exists()
        assert json.loads((storage_dir / "preferences.json").read_text(encoding="utf-8")) == {"key": "value"}

    def test_save_overwrites_existing_file(self, isolated_storage):
        home, svc = isolated_storage
        svc.set("key", "v1")
        svc.set("key", "v2")

        storage_dir = home / "Documents" / "L4D2-VPK-Manager"
        assert json.loads((storage_dir / "preferences.json").read_text(encoding="utf-8"))["key"] == "v2"

    def test_corrupt_file_renamed_and_reset(self, isolated_storage):
        home, _ = isolated_storage
        storage_dir = home / "Documents" / "L4D2-VPK-Manager"
        (storage_dir / "preferences.json").write_text("{not valid json", encoding="utf-8")

        # 原单例已加载过,重置后重新加载才会读盘
        StorageService._instance = None
        svc = StorageService()

        assert svc.get("anything") is None
        assert (storage_dir / "preferences.json.corrupt").exists()
        assert (storage_dir / "preferences.json.corrupt").read_text(encoding="utf-8") == "{not valid json"


class TestStaleTmpCleanup:
    def test_stale_tmp_file_cleaned_on_init(self, isolated_storage):
        home, svc = isolated_storage
        storage_dir = home / "Documents" / "L4D2-VPK-Manager"
        stale = storage_dir / "preferences.json.tmp"
        stale.write_text("{}", encoding="utf-8")

        # 重置单例触发重新初始化
        StorageService._instance = None
        StorageService()

        assert not stale.exists()
