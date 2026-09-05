"""用 vpk 库构造真实 VPK 文件,覆盖 extract_addontitle 的完整编码链路"""

import base64

import pytest

import vpk as vpk_lib

from backend.services.vpk_metadata_service import VpkMetadataService


def _build_vpk(tmp_path, addoninfo_bytes=None, name="mod.vpk"):
    """用 NewVPK 从源目录构造真实 VPK,返回 vpk 文件路径"""
    src = tmp_path / f"{name}_src"
    src.mkdir(exist_ok=True)
    if addoninfo_bytes is not None:
        (src / "addoninfo.txt").write_bytes(addoninfo_bytes)
    out = tmp_path / name
    vpk_lib.NewVPK(str(src)).save(str(out))
    return str(out)


@pytest.fixture()
def svc(tmp_path):
    return VpkMetadataService(config_dir=str(tmp_path / "cfg"))


class TestExtractAddontitleRealVpk:
    def test_utf8_title(self, tmp_path, svc):
        content = '"addonversion"\t"1.0"\n"addontitle"\t"Real Test Mod"\n'.encode("utf-8")
        vpk_path = _build_vpk(tmp_path, content)
        assert svc.extract_addontitle(vpk_path) == "Real Test Mod"

    def test_chinese_title_utf8(self, tmp_path, svc):
        content = 'addontitle "中文模组标题"\n'.encode("utf-8")
        vpk_path = _build_vpk(tmp_path, content)
        assert svc.extract_addontitle(vpk_path) == "中文模组标题"

    def test_gbk_encoded_title(self, tmp_path, svc):
        # gbk 字节流无法用 utf-8 解码,验证编码回退链
        content = 'addontitle "GBK模组"\n'.encode("gbk")
        try:
            content.decode("utf-8")
            pytest.skip("该 gbk 字节流恰好是合法 utf-8,无法测试回退链")
        except UnicodeDecodeError:
            pass
        vpk_path = _build_vpk(tmp_path, content)
        assert svc.extract_addontitle(vpk_path) == "GBK模组"

    def test_quoted_key_variant(self, tmp_path, svc):
        content = b'"addontitle"\t"Quoted Key"\n'
        vpk_path = _build_vpk(tmp_path, content)
        assert svc.extract_addontitle(vpk_path) == "Quoted Key"

    def test_no_addoninfo_returns_none(self, tmp_path, svc):
        vpk_path = _build_vpk(tmp_path, None)
        assert svc.extract_addontitle(vpk_path) is None

    def test_cache_after_real_extraction(self, tmp_path, svc):
        content = 'addontitle "Cached"\n'.encode("utf-8")
        vpk_path = _build_vpk(tmp_path, content)
        assert svc.get_addontitle(vpk_path) == "Cached"
        # 第二次走缓存
        assert svc.get_addontitle(vpk_path) == "Cached"
        cached = svc.load_metadata(vpk_path)
        assert cached["addontitle"] == "Cached"
        assert "source_mtime" in cached


class TestThumbnail:
    def test_jpeg_thumbnail_to_base64_data_uri(self, tmp_path, svc):
        vpk_path = _build_vpk(tmp_path, 'addontitle "T"\n'.encode("utf-8"), name="pic.vpk")
        # 注意:构造 VPK 的源目录 src 与 vpk 同级,缩略图需放在 vpk 旁边
        jpg = tmp_path / "pic.jpg"
        jpg.write_bytes(b"\xff\xd8\xff\xe0fakejpeg")

        meta = svc.get_vpk_metadata(vpk_path)

        assert meta is not None
        assert meta.thumbnail_path is not None
        assert meta.thumbnail_path.startswith("data:image/jpeg;base64,")
        assert base64.b64decode(meta.thumbnail_path.split(",", 1)[1]) == b"\xff\xd8\xff\xe0fakejpeg"

    def test_png_thumbnail_mime(self, tmp_path, svc):
        vpk_path = _build_vpk(tmp_path, 'addontitle "T"\n'.encode("utf-8"), name="pic2.vpk")
        (tmp_path / "pic2.png").write_bytes(b"\x89PNGfake")

        meta = svc.get_vpk_metadata(vpk_path)
        assert meta.thumbnail_path.startswith("data:image/png;base64,")
