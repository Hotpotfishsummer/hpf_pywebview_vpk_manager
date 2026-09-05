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
