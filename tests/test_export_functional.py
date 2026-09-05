"""vpk_export_service.export_vpks 的功能级测试

使用哑文件(普通字节,不需要真实 VPK 结构)走完整导出流程,
验证归档生成、better_naming 重命名、关联图片复制与临时目录清理。
"""

import io
import tarfile

import pytest

from backend.services.vpk_export_service import VpkExportService


pytest.importorskip("zstandard", reason="需要 zstandard")

# Python 3.12 的 tarfile 不支持 zstd,先解压一层再读 tar
import zstandard as zstd


def _archive_names(archive_path: str) -> list:
    with open(archive_path, "rb") as f:
        raw = zstd.ZstdDecompressor().stream_reader(f).read()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r|") as tar:
        return sorted(m.name for m in tar if m.isfile())


class TestExportVpks:
    def test_exports_single_file_to_tar_zst(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.vpk").write_bytes(b"fake vpk content")

        out_dir = tmp_path / "out"
        archive = VpkExportService.export_vpks([str(src / "mod.vpk")], str(out_dir))

        assert archive.endswith(".tar.zst")
        assert out_dir.joinpath("mod.tar.zst").exists() or out_dir.joinpath(archive).exists()
        # 无临时目录残留
        leftovers = [p.name for p in out_dir.iterdir() if p.name.startswith(".vpk_temp")]
        assert leftovers == []

    def test_archive_contains_vpk_and_image(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "12345678.vpk").write_bytes(b"vpk-bytes")
        (src / "12345678.jpg").write_bytes(b"jpg-bytes")

        out_dir = tmp_path / "out"
        archive = VpkExportService.export_vpks([str(src / "12345678.vpk")], str(out_dir))

        assert _archive_names(archive) == ["12345678.jpg", "12345678.vpk"]

    def test_better_naming_renames_files_in_archive(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "12345678.vpk").write_bytes(b"vpk-bytes")
        (src / "12345678.jpg").write_bytes(b"jpg-bytes")

        out_dir = tmp_path / "out"
        archive = VpkExportService.export_vpks(
            [str(src / "12345678.vpk")],
            str(out_dir),
            titles=["My Cool Mod"],
            better_naming=True,
        )

        assert _archive_names(archive) == ["My_Cool_Mod-12345678.jpg", "My_Cool_Mod-12345678.vpk"]

    def test_no_titles_keeps_original_names(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "plain.vpk").write_bytes(b"x")

        out_dir = tmp_path / "out"
        archive = VpkExportService.export_vpks([str(src / "plain.vpk")], str(out_dir), titles=[None])

        assert _archive_names(archive) == ["plain.vpk"]

    def test_empty_selection_raises(self, tmp_path):
        with pytest.raises(Exception):
            VpkExportService.export_vpks([], str(tmp_path / "out"))
