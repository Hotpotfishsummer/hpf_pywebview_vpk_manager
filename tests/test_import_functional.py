"""vpk_import_service.import_compressed_files 的功能级测试(真实压缩包,tmp 隔离)"""

import io
import tarfile
import zipfile

import pytest

from backend.services.vpk_import_service import VpkImportService

py7zr = pytest.importorskip("py7zr", reason="需要 py7zr")
zstd = pytest.importorskip("zstandard", reason="需要 zstandard")


def _make_zip(tmp_path):
    archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("nested/dir/addon.vpk", b"vpk-bytes")
        zf.writestr("nested/dir/addon.jpg", b"jpg-bytes")
        zf.writestr("nested/dir/readme.txt", b"txt-bytes")  # 应被过滤
    return str(archive)


def _make_tar_zst(tmp_path):
    archive = tmp_path / "pack.tar.zst"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, data in [("sub/addon.vpk", b"vpk"), ("sub/addon.png", b"png")]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    raw = zstd.ZstdCompressor().compress(buf.getvalue())
    archive.write_bytes(raw)
    return str(archive)


def _make_7z(tmp_path):
    archive = tmp_path / "pack.7z"
    src = tmp_path / "payload"
    src.mkdir()
    (src / "deep.vpk").write_bytes(b"vpk")
    with py7zr.SevenZipFile(archive, "w") as z:
        z.write(src / "deep.vpk", arcname="deep.vpk")
    return str(archive)


class TestImportCompressedFiles:
    def test_zip_flattens_and_filters(self, tmp_path):
        addons = tmp_path / "addons"
        addons.mkdir()
        result = VpkImportService.import_compressed_files([_make_zip(tmp_path)], str(addons))

        assert result["success"] is True
        assert result["imported_count"] == 1
        names = sorted(p.name for p in addons.iterdir())
        assert names == ["addon.jpg", "addon.vpk"]  # txt 被过滤,无嵌套目录

    def test_tar_zst_extracts_vpk_and_image(self, tmp_path):
        addons = tmp_path / "addons"
        addons.mkdir()
        result = VpkImportService.import_compressed_files([_make_tar_zst(tmp_path)], str(addons))

        assert result["success"] is True
        assert sorted(p.name for p in addons.iterdir()) == ["addon.png", "addon.vpk"]

    def test_7z_extracts(self, tmp_path):
        addons = tmp_path / "addons"
        addons.mkdir()
        result = VpkImportService.import_compressed_files([_make_7z(tmp_path)], str(addons))

        assert result["success"] is True
        assert (addons / "deep.vpk").read_bytes() == b"vpk"

    def test_multiple_archives_counted(self, tmp_path):
        addons = tmp_path / "addons"
        addons.mkdir()
        result = VpkImportService.import_compressed_files(
            [_make_zip(tmp_path), _make_tar_zst(tmp_path)], str(addons)
        )
        assert result["imported_count"] == 2

    def test_unsupported_format_reports_error(self, tmp_path):
        addons = tmp_path / "addons"
        addons.mkdir()
        rar = tmp_path / "pack.rar"
        rar.write_bytes(b"not really")
        result = VpkImportService.import_compressed_files([str(rar)], str(addons))

        assert result["success"] is False
        assert result["imported_count"] == 0
        assert any("不支持的文件格式" in e for e in (result["errors"] or []))

    def test_missing_target_dir_fails(self, tmp_path):
        result = VpkImportService.import_compressed_files(
            [_make_zip(tmp_path)], str(tmp_path / "nope")
        )
        assert result["success"] is False
        assert "目标目录不存在" in result["error"]

    def test_missing_archive_reported(self, tmp_path):
        addons = tmp_path / "addons"
        addons.mkdir()
        result = VpkImportService.import_compressed_files(
            [str(tmp_path / "ghost.zip")], str(addons)
        )
        assert result["success"] is False
        assert any("文件不存在" in e for e in (result["errors"] or []))


class TestPathTraversalGuard:
    def test_7z_rejects_traversal_entry(self, tmp_path):
        """恶意 7z(条目名含 ..)不得写出目标目录,也不得逃逸到目录外"""
        archive = tmp_path / "evil.7z"
        payload = tmp_path / "payload.vpk"
        payload.write_bytes(b"vpk")
        with py7zr.SevenZipFile(archive, "w") as z:
            z.write(payload, arcname="sub/../../evil.vpk")

        addons = tmp_path / "addons"
        addons.mkdir()
        outside = tmp_path / "evil.vpk"

        result = VpkImportService.import_compressed_files([str(archive)], str(addons))

        assert result["success"] is False
        assert result["imported_count"] == 0
        assert not addons.exists() or list(addons.iterdir()) == []
        assert not outside.exists(), "条目逃逸了目标目录!"


class TestDuplicateBasenameOverwrite:
    def test_zip_duplicate_basenames_last_write_wins(self, tmp_path):
        """两个嵌套条目扁平化后同名 → 后写覆盖前写(固化当前行为)"""
        archive = tmp_path / "dup.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("a/mod.vpk", b"content A")
            z.writestr("b/mod.vpk", b"content B")

        addons = tmp_path / "addons"
        addons.mkdir()

        result = VpkImportService.import_compressed_files([str(archive)], str(addons))

        assert result["success"] is True
        # 只有一个 mod.vpk,内容为后写的 B
        assert (addons / "mod.vpk").read_bytes() == b"content B"
