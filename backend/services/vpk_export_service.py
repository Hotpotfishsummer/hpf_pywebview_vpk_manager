"""VPK 导出服务 - 处理 VPK 文件导出和 zstandard 压缩"""

from pathlib import Path
from typing import List, Optional
import shutil
import os
import time
import tarfile
import multiprocessing
import re

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False


class VpkExportService:
    """VPK 文件导出和删除的服务类"""

    @staticmethod
    def export_vpks(vpk_file_paths: List[str], output_dir: str, titles: Optional[List[str]] = None, better_naming: bool = False) -> str:
        """
        将选定的 VPK 文件导出到 zstandard 压缩的 tar 归档。

        参数:
            vpk_file_paths: 要导出的 VPK 文件路径列表
            output_dir: 输出目录（通常是下载文件夹）
            titles: VPK 文件的显示名称或标题列表（可选）
            better_naming: 是否在压缩包内使用 addontitle 命名文件

        返回:
            Path to the created archive file

        Raises:
            Exception: If export fails
        """
        start_time = time.time()

        if not HAS_ZSTD:
            raise Exception('zstandard library not installed. Install with: pip install zstandard')

        if not vpk_file_paths:
            raise Exception('No files selected for export')

        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate archive name
            archive_name = VpkExportService._generate_archive_name(vpk_file_paths, titles)
            archive_path = output_path / f"{archive_name}.tar.zst"

            print(f"export_vpks: creating archive {archive_path}")

            # Create temporary directory for collecting files
            temp_dir = output_path / '.vpk_temp'
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)

            try:
                # Copy VPK files to temp directory
                for i, vpk_path_str in enumerate(vpk_file_paths):
                    vpk_path = Path(vpk_path_str)
                    
                    # 确定导出后的基础文件名
                    base_name = vpk_path.stem
                    if better_naming and titles and i < len(titles) and titles[i]:
                        # 使用 addontitle 并去除空格和非法字符
                        custom_title = titles[i]
                        # 移除空格，替换为下划线，并处理其他非法字符
                        custom_title = custom_title.replace(" ", "_")
                        # 复用 _generate_archive_name 中的清洗逻辑逻辑（其实可以抽出来的，这里简单处理下）
                        illegal_pattern = r'[<>:"/\\|?*\x00-\x1f]'
                        base_name = re.sub(illegal_pattern, '_', custom_title)
                        # 确保不为空
                        if not base_name.strip():
                            base_name = vpk_path.stem

                    # Copy VPK file
                    if vpk_path.exists():
                        dest = temp_dir / f"{base_name}.vpk"
                        print(f"export_vpks: copying {vpk_path} to {dest}")
                        shutil.copy2(vpk_path, dest)

                        # 同时检查并复制同名的图片文件 (缩略图)
                        # 常见的图片扩展名
                        image_exts = ['.jpg', '.jpeg', '.png', '.tga', '.bmp', '.gif']
                        vpk_stem = vpk_path.stem
                        vpk_parent = vpk_path.parent
                        
                        for ext in image_exts:
                            # 尝试匹配各种大小写的扩展名
                            for img_path in [vpk_parent / f"{vpk_stem}{ext}", vpk_parent / f"{vpk_stem}{ext.upper()}"]:
                                if img_path.exists() and img_path.is_file():
                                    # 保持与 VPK 新名字一致的标题，但保留图片原本的后缀名
                                    img_ext = img_path.suffix
                                    img_dest = temp_dir / f"{base_name}{img_ext}"
                                    print(f"export_vpks: copying associated image {img_path} to {img_dest}")
                                    shutil.copy2(img_path, img_dest)
                                    # 找到一个即可，通常同名图片只有一个
                                    break

                # Create tar.zst archive with zstandard compression
                print(f"export_vpks: creating zstandard compressed archive with high compression")

                # Get system CPU count for multi-threaded compression
                num_threads = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free
                print(f"export_vpks: using {num_threads} threads for compression")

                # Create zstandard context with maximum compression level and multi-threading
                cctx = zstd.ZstdCompressor(
                    level=3,  # Maximum compression level (1-22, default 3)
                    threads=num_threads,  # Multi-threaded compression
                    write_checksum=True,  # Include checksum for integrity verification
                )

                # Create tar archive and compress with zstandard
                print(f"export_vpks: compressing files into {archive_path}")
                with open(archive_path, 'wb') as f_out:
                    with cctx.stream_writer(f_out, closefd=False) as writer:
                        with tarfile.open(fileobj=writer, mode='w|') as tar:
                            # Add all files from temp directory to tar
                            for file_path in sorted(temp_dir.iterdir()):
                                if file_path.is_file():
                                    print(f"export_vpks: adding {file_path.name} to archive")
                                    tar.add(file_path, arcname=file_path.name)

                elapsed_time = time.time() - start_time
                archive_size = archive_path.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"export_vpks: successfully created {archive_path} ({archive_size:.2f} MB) in {elapsed_time:.2f} seconds")
                return str(archive_path)

            finally:
                # Clean up temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    print(f"export_vpks: cleaned up temp directory")

        except Exception as e:
            error_msg = f'Error exporting VPK files: {str(e)}'
            print(f"export_vpks: {error_msg}")
            raise

    @staticmethod
    def _generate_archive_name(vpk_file_paths: List[str], titles: Optional[List[str]] = None) -> str:
        """Generate archive filename from file names or titles"""
        names = []
        if titles:
            # 使用提供的标题
            names = [str(t) for t in titles if t]
        
        # 如果标题不足，使用文件名填充
        if len(names) < len(vpk_file_paths):
            for i in range(len(names), len(vpk_file_paths)):
                names.append(Path(vpk_file_paths[i]).stem)

        # 仅取前三个名字进行拼接
        count = len(names)
        display_names = names[:3]
        archive_name = '-'.join(display_names)

        if count > 3:
            archive_name += f"-and-{count - 3}-more"

        # 处理非法字符 (Windows/Linux/Mac 系统安全)
        # Windows 不允许: < > : " / \ | ? *
        # 还要由于这是压缩包名，我们把空格也换成下划线更稳妥
        # 移除控制字符
        archive_name = "".join(c for c in archive_name if c.isprintable())
        
        # 正则替换非法字符为下划线
        # 包括常见的非法字符以及换行符等
        illegal_pattern = r'[<>:"/\\|?*\x00-\x1f]'
        archive_name = re.sub(illegal_pattern, '_', archive_name)
        
        # 限制长度 (文件名过长也会报错，Windows 路径总长限制 260)
        if len(archive_name) > 100:
            archive_name = archive_name[:97] + "..."

        # 确保不为空
        if not archive_name.strip() or archive_name == "...":
            archive_name = f"vpk_export_{int(time.time())}"

        print(f"_generate_archive_name: generated archive name: {archive_name}")
        return archive_name

    @staticmethod
    def get_downloads_directory() -> str:
        """Get user's Downloads directory path"""
        if os.name == 'nt':  # Windows
            # Try using environment variable first
            downloads = os.environ.get('USERPROFILE')
            if downloads:
                downloads = str(Path(downloads) / 'Downloads')
                if Path(downloads).exists():
                    return downloads
        else:  # macOS and Linux
            downloads = os.path.expanduser('~/Downloads')
            if Path(downloads).exists():
                return downloads

        # Fallback to home directory
        return os.path.expanduser('~')
