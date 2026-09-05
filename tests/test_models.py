"""models.VpkFile 的单元测试"""

from backend.models import VpkFile


def _make_vpk(**overrides) -> VpkFile:
    defaults = dict(
        name="12345678.vpk",
        path="C:/addons/12345678.vpk",
        size=1024,
        modified_time=0.0,
        is_valid=True,
    )
    defaults.update(overrides)
    return VpkFile(**defaults)


def test_display_name_prefers_addontitle():
    vpk = _make_vpk(addontitle="My Cool Mod")
    assert vpk.display_name == "My Cool Mod"


def test_display_name_falls_back_to_filename():
    vpk = _make_vpk(addontitle=None)
    assert vpk.display_name == "12345678.vpk"


def test_is_disabled_default_false():
    assert _make_vpk().is_disabled is False
