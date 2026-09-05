"""VpkManagerApi._disable_or_delete_single 的单元测试

直接调用静态方法,不实例化 VpkManagerApi——其实例化会读取用户真实
preferences 并可能对 L4D2 目录应用 autoexec 模板,测试不可触碰。
"""

import pytest

from backend.api import VpkManagerApi


def _make_files(tmp_path, name="mod.vpk", images=("mod.jpg",), extra=()):
    for img in images:
        (tmp_path / img).write_bytes(b"img")
    for f in extra:
        (tmp_path / f).write_bytes(b"x")
    vpk = tmp_path / name
    vpk.write_bytes(b"vpk")
    return str(vpk)


class TestDisableSingle:
    def test_disable_renames_vpk_and_images(self, tmp_path):
        vpk_path = _make_files(tmp_path)
        VpkManagerApi._disable_or_delete_single(vpk_path, disable=True)

        assert not (tmp_path / "mod.vpk").exists()
        assert (tmp_path / "mod.vpk.disabled").exists()
        assert (tmp_path / "mod.vpk.jpg").exists()

    def test_disable_toggles_enabled_file(self, tmp_path):
        # 已 .disabled 的文件再 disable = 恢复启用(与批量版语义一致)
        vpk_path = _make_files(tmp_path, name="mod.vpk.disabled", images=("mod.vpk.jpg",))
        VpkManagerApi._disable_or_delete_single(vpk_path, disable=True)

        assert (tmp_path / "mod.vpk").exists()
        assert (tmp_path / "mod.jpg").exists()

    def test_disable_renames_txt_and_jpeg_too(self, tmp_path):
        vpk_path = _make_files(
            tmp_path,
            name="mod.vpk",
            images=(),
            extra=("mod.txt", "mod.jpeg", "mod.png"),
        )
        VpkManagerApi._disable_or_delete_single(vpk_path, disable=True)

        assert (tmp_path / "mod.vpk.txt").exists()
        assert (tmp_path / "mod.vpk.jpeg").exists()
        assert (tmp_path / "mod.vpk.png").exists()

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VpkManagerApi._disable_or_delete_single(str(tmp_path / "ghost.vpk"), True)


class TestDeleteSingle:
    def test_delete_removes_vpk_and_images(self, tmp_path):
        vpk_path = _make_files(
            tmp_path, name="mod.vpk", images=("mod.jpg",), extra=("mod.txt",)
        )
        VpkManagerApi._disable_or_delete_single(vpk_path, disable=False)

        assert not (tmp_path / "mod.vpk").exists()
        assert not (tmp_path / "mod.jpg").exists()
        assert not (tmp_path / "mod.txt").exists()

    def test_delete_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VpkManagerApi._disable_or_delete_single(str(tmp_path / "ghost.vpk"), False)


class TestPublicMethodsConsistency:
    def test_enable_vpk_file_is_exposed(self):
        assert "enable_vpk_file" in VpkManagerApi._PUBLIC_METHODS

    def test_all_public_methods_exist(self):
        for name in VpkManagerApi._PUBLIC_METHODS:
            assert callable(getattr(VpkManagerApi, name, None)), name


class TestPublicMethodsComplete:
    """防止新增公开方法忘记登记 _PUBLIC_METHODS(该表决定前端可见性)"""

    def test_every_public_method_is_registered(self):
        import inspect

        public_methods = {
            name
            for name, _ in inspect.getmembers(VpkManagerApi, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        # set_window 由 main.py 内部调用,不暴露给前端
        unregistered = public_methods - VpkManagerApi._PUBLIC_METHODS - {"set_window"}
        assert unregistered == set(), f"未登记到 _PUBLIC_METHODS: {sorted(unregistered)}"

    def test_registry_has_no_phantom_entries(self):
        import inspect

        public_methods = {
            name
            for name, _ in inspect.getmembers(VpkManagerApi, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        phantom = VpkManagerApi._PUBLIC_METHODS - public_methods
        assert phantom == set(), f"_PUBLIC_METHODS 中存在不存在的方法: {sorted(phantom)}"
