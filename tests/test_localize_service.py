"""VpkLocalizeService 的功能级测试(真实 VPK 构造,tmp 隔离)"""

import vpk as vpk_lib

from backend.services.vpk_localize_service import VpkLocalizeService
from backend.services.vpk_metadata_service import VpkMetadataService


def _make_l4d2(tmp_path):
    """搭建 L4D2 目录结构与 workshop 源目录"""
    l4d2 = tmp_path / "l4d2"
    addons = l4d2 / "left4dead2" / "addons"
    workshop = addons / "workshop"
    workshop.mkdir(parents=True)
    return l4d2, addons, workshop


def _make_vpk(directory, name="12345678.vpk", title="Real Test Mod"):
    src = directory / f"_{name}_src"
    src.mkdir(exist_ok=True)
    if title:
        (src / "addoninfo.txt").write_bytes(f'addontitle "{title}"\n'.encode("utf-8"))
    out = directory / name
    vpk_lib.NewVPK(str(src)).save(str(out))
    return str(out)


def _make_service(tmp_path):
    meta = VpkMetadataService(config_dir=str(tmp_path / "cfg"))
    return VpkLocalizeService(meta)


class TestLocalize:
    def test_copies_to_addons_and_trashes_original(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop)

        result = svc.localize([vpk_path], str(l4d2))

        assert result["success"] is True
        assert result["success_count"] == 1
        assert result["errors"] is None
        assert (addons / "12345678.vpk").exists()
        assert not (workshop / "12345678.vpk").exists()
        assert (workshop / ".trash" / "12345678.vpk").exists()

    def test_copies_and_trashes_associated_image(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop)
        (workshop / "12345678.jpg").write_bytes(b"img")

        result = svc.localize([vpk_path], str(l4d2))

        assert result["success"] is True
        assert (addons / "12345678.jpg").exists()
        assert not (workshop / "12345678.jpg").exists()
        assert (workshop / ".trash" / "12345678.jpg").exists()

    def test_better_naming_uses_addontitle_with_id(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop, title="My Cool Mod")  # 文件名含 8 位 ID

        result = svc.localize([vpk_path], str(l4d2), better_naming=True)

        assert result["success"] is True
        assert (addons / "My_Cool_Mod-12345678.vpk").exists()

    def test_better_naming_false_keeps_stem(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop, title="My Cool Mod")

        result = svc.localize([vpk_path], str(l4d2), better_naming=False)

        assert result["success"] is True
        assert (addons / "12345678.vpk").exists()

    def test_non_workshop_file_not_trashed(self, tmp_path):
        import os
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        elsewhere = tmp_path / "downloads"
        elsewhere.mkdir()
        vpk_path = _make_vpk(elsewhere)

        result = svc.localize([vpk_path], str(l4d2))

        assert result["success"] is True
        assert (addons / "12345678.vpk").exists()
        assert os.path.exists(vpk_path)  # 原文件保留

    def test_missing_file_reported(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)

        result = svc.localize([str(workshop / "ghost.vpk")], str(l4d2))

        assert result["success"] is False
        assert result["success_count"] == 0
        assert any("文件不存在" in e for e in result["errors"])

    def test_disabled_file_restored_to_vpk(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop)
        import os
        disabled = workshop / "mod.vpk.disabled"
        os.rename(vpk_path, disabled)

        result = svc.localize([str(disabled)], str(l4d2))

        assert result["success"] is True
        assert (addons / "mod.vpk").exists()

    def test_case_insensitive_image_match(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop, name="mod.vpk", title=None)
        (workshop / "MOD.jpg").write_bytes(b"img")  # stem 大小写不匹配,扫描应能找到

        result = svc.localize([vpk_path], str(l4d2))

        assert result["success"] is True
        assert (addons / "mod.jpg").exists()


class TestBetterNamingEdgeCases:
    def test_better_naming_without_addontitle_falls_back_to_stem(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop, name="87654321.vpk", title=None)

        result = svc.localize([vpk_path], str(l4d2), better_naming=True)

        assert result["success"] is True
        assert (addons / "87654321.vpk").exists()

    def test_better_naming_disabled_file_restores_and_renames(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        vpk_path = _make_vpk(workshop, name="12345678.vpk.disabled", title="My Cool Mod")

        result = svc.localize([vpk_path], str(l4d2), better_naming=True)

        assert result["success"] is True
        assert (addons / "My_Cool_Mod-12345678.vpk").exists()
        assert not any(p.name.endswith(".disabled") for p in addons.iterdir())

    def test_better_naming_title_of_only_illegal_chars_falls_back(self, tmp_path):
        l4d2, addons, workshop = _make_l4d2(tmp_path)
        svc = _make_service(tmp_path)
        # 纯非法字符标题清洗后为空 → 回退原 stem
        vpk_path = _make_vpk(workshop, name="87654321.vpk", title='???')

        result = svc.localize([vpk_path], str(l4d2), better_naming=True)

        assert result["success"] is True
        assert (addons / "87654321.vpk").exists()
