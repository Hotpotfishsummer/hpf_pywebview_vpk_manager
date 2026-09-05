"""ConfigService(autoexec.cfg 管理)的单元测试,全部使用 tmp_path 隔离"""

from backend.services.config_service import ConfigService


def _make_env(tmp_path, template_content='bind "x" "say hi"\n', l4d2_dir=True):
    """搭建 base_path(含模板)与 L4D2 目录(含 cfg)"""
    base = tmp_path / "base"
    assets = base / "assets"
    assets.mkdir(parents=True)
    (assets / "autoexec.cfg.example").write_text(template_content, encoding="utf-8")

    root = tmp_path / "l4d2"
    cfg = root / "left4dead2" / "cfg"
    cfg.mkdir(parents=True)
    if not l4d2_dir:
        root.rmdir()

    return ConfigService(str(base)), root, cfg


class TestApplyAutoexecTemplate:
    def test_invalid_directory_returns_false(self, tmp_path):
        svc, _, _ = _make_env(tmp_path)
        assert svc.apply_autoexec_template("") is False
        assert svc.apply_autoexec_template(str(tmp_path / "nope")) is False

    def test_missing_cfg_dir_returns_false(self, tmp_path):
        svc, root, _ = _make_env(tmp_path)
        (root / "left4dead2" / "cfg").rmdir()
        assert svc.apply_autoexec_template(str(root)) is False

    def test_missing_template_returns_false(self, tmp_path):
        svc, root, cfg = _make_env(tmp_path)
        (svc.base_path / "assets" / "autoexec.cfg.example").unlink()
        assert svc.apply_autoexec_template(str(root)) is False

    def test_applies_template_to_fresh_cfg_dir(self, tmp_path):
        svc, root, cfg = _make_env(tmp_path)
        assert svc.apply_autoexec_template(str(root)) is True
        assert (cfg / "autoexec.cfg").read_text(encoding="utf-8") == 'bind "x" "say hi"\n'
        assert not (cfg / "autoexec.cfg.bak").exists()

    def test_overwrites_and_backs_up_existing(self, tmp_path):
        svc, root, cfg = _make_env(tmp_path)
        autoexec = cfg / "autoexec.cfg"
        autoexec.write_text("old user config", encoding="utf-8")

        assert svc.apply_autoexec_template(str(root)) is True
        assert autoexec.read_text(encoding="utf-8") == 'bind "x" "say hi"\n'
        assert (cfg / "autoexec.cfg.bak").read_text(encoding="utf-8") == "old user config"

    def test_identical_content_is_noop(self, tmp_path):
        svc, root, cfg = _make_env(tmp_path)
        autoexec = cfg / "autoexec.cfg"
        autoexec.write_text('bind "x" "say hi"\n', encoding="utf-8")

        assert svc.apply_autoexec_template(str(root)) is True
        assert not (cfg / "autoexec.cfg.bak").exists()

    def test_accepts_left4dead2_dir_directly(self, tmp_path):
        # 传入的就是 left4dead2 目录时,cfg 是其直接子目录
        svc, root, _ = _make_env(tmp_path)
        l4d2 = root / "left4dead2"
        assert svc.apply_autoexec_template(str(l4d2)) is True
        assert (l4d2 / "cfg" / "autoexec.cfg").exists()
