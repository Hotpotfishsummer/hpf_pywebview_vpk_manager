"""VpkScanService 的功能级测试(真实 VPK 构造,tmp 隔离)"""

import vpk as vpk_lib

from backend.services.vpk_metadata_service import VpkMetadataService
from backend.services.vpk_scan_service import VpkScanService


def _build_vpk(directory, name, title):
    src = directory / f"_{name}_src"
    src.mkdir(exist_ok=True)
    (src / "addoninfo.txt").write_bytes(f'addontitle "{title}"\n'.encode("utf-8"))
    out = directory / name
    vpk_lib.NewVPK(str(src)).save(str(out))
    return out


def _make_env(tmp_path):
    l4d2 = tmp_path / "l4d2"
    addons = l4d2 / "left4dead2" / "addons"
    workshop = addons / "workshop"
    workshop.mkdir(parents=True)
    meta = VpkMetadataService(config_dir=str(tmp_path / "cfg"))
    return VpkScanService(meta), l4d2, addons, workshop


class TestScan:
    def test_scans_local_and_workshop(self, tmp_path):
        svc, l4d2, addons, workshop = _make_env(tmp_path)
        _build_vpk(addons, "local.vpk", "Local Mod")
        _build_vpk(workshop, "987654321.vpk", "Workshop Mod")

        result = svc.scan(str(l4d2))

        assert [f["name"] for f in result["local_vpks"]] == ["local.vpk"]
        assert [f["name"] for f in result["workshop_vpks"]] == ["987654321.vpk"]
        assert result["workshop_vpks"][0]["addontitle"] == "Workshop Mod"
        assert result["workshop_vpks"][0]["display_name"] == "Workshop Mod"

    def test_disabled_flag_detected(self, tmp_path):
        import os
        svc, l4d2, addons, workshop = _make_env(tmp_path)
        enabled = _build_vpk(addons, "mod.vpk", "M")
        disabled = _build_vpk(addons, "off.vpk", "M2")
        os.rename(disabled, addons / "off.vpk.disabled")
        os.remove(enabled)

        result = svc.scan(str(l4d2))

        flags = {f["name"]: f["is_disabled"] for f in result["local_vpks"]}
        assert flags == {"off.vpk.disabled": True}

    def test_ignores_non_vpk_files(self, tmp_path):
        svc, l4d2, addons, workshop = _make_env(tmp_path)
        (addons / "readme.txt").write_text("hi")
        (addons / "not_vpk.jpg").write_bytes(b"x")

        result = svc.scan(str(l4d2))

        assert result["local_vpks"] == []

    def test_thumbnail_becomes_data_uri(self, tmp_path):
        svc, l4d2, addons, workshop = _make_env(tmp_path)
        _build_vpk(addons, "pic.vpk", "P")
        (addons / "pic.jpg").write_bytes(b"\xff\xd8fake")

        result = svc.scan(str(l4d2))

        assert result["local_vpks"][0]["thumbnail_path"].startswith("data:image/jpeg;base64,")

    def test_missing_directories_return_empty(self, tmp_path):
        svc, l4d2, addons, workshop = _make_env(tmp_path)
        import shutil
        shutil.rmtree(addons)

        result = svc.scan(str(l4d2))

        assert result == {"local_vpks": [], "workshop_vpks": []}

    def test_size_and_mtime_populated(self, tmp_path):
        svc, l4d2, addons, workshop = _make_env(tmp_path)
        out = _build_vpk(addons, "mod.vpk", "M")

        result = svc.scan(str(l4d2))

        entry = result["local_vpks"][0]
        assert entry["size"] == out.stat().st_size
        assert entry["modified_time"] == out.stat().st_mtime
        assert entry["is_valid"] is True


class TestScanEdgeCases:
    def test_skips_directory_named_like_vpk(self, tmp_path):
        """名字像 VPK 的目录不应进入扫描结果,也不应抛错"""
        l4d2 = tmp_path / "l4d2"
        addons = l4d2 / "left4dead2" / "addons"
        workshop = addons / "workshop"
        workshop.mkdir(parents=True)
        (addons / "folder.vpk").mkdir()          # 目录,不是文件
        (addons / "real.vpk").write_bytes(b"x")  # 哑文件即可走通元数据路径

        svc = VpkScanService(VpkMetadataService(config_dir=str(tmp_path / "cfg")))
        result = svc.scan(str(l4d2))

        names = [f["name"] for f in result["local_vpks"]]
        assert names == ["real.vpk"]
