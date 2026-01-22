"""VPK 导入服务 - 处理压缩包的解压和 VPK 文件的提取"""

import os
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import List, Dict, Any

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

class VpkImportService:
    """处理压缩包解压并将 VPK 及其同名图片导入到 addons 目录的服务"""

    @staticmethod
    def import_compressed_files(file_paths: List[str], target_addons_dir: str) -> Dict[str, Any]:
        """
        解压选定的压缩包并提取 VPK 和图片文件。

        参数:
            file_paths: 压缩包路径列表
            target_addons_dir: L4D2 的 addons 文件夹路径

        返回:
            包含成功状态和统计信息的字典
        """
        imported_count = 0
        errors = []
        target_path = Path(target_addons_dir)

        if not target_path.exists():
            return {"success": False, "error": f"目标目录不存在: {target_addons_dir}"}

        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            if not file_path.exists():
                errors.append(f"文件不存在: {file_path_str}")
                continue

            try:
                suffix = file_path.suffix.lower()
                # 处理 .tar.zst 这种双后缀
                if file_path_str.lower().endswith('.tar.zst'):
                    VpkImportService._extract_tar_zst(file_path, target_path)
                elif suffix == '.zip':
                    VpkImportService._extract_zip(file_path, target_path)
                elif suffix == '.7z':
                    if not HAS_PY7ZR:
                        raise Exception("系统未安装 py7zr，无法处理 .7z 文件")
                    VpkImportService._extract_7z(file_path, target_path)
                else:
                    errors.append(f"不支持的文件格式: {file_path.name}")
                    continue
                
                imported_count += 1
            except Exception as e:
                errors.append(f"解压 {file_path.name} 失败: {str(e)}")

        return {
            "success": len(errors) == 0,
            "imported_count": imported_count,
            "errors": errors if errors else None
        }

    @staticmethod
    def _extract_zip(file_path: Path, target_path: Path):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if VpkImportService._is_vpk_or_image(member):
                    # 假定无嵌套，获取文件名
                    filename = os.path.basename(member)
                    if not filename: continue
                    
                    extract_path = target_path / filename
                    with zip_ref.open(member) as source, open(extract_path, "wb") as target:
                        shutil.copyfileobj(source, target)

    @staticmethod
    def _extract_7z(file_path: Path, target_path: Path):
        with py7zr.SevenZipFile(file_path, mode='r') as z:
            # py7zr getnames 返回所有文件
            for name in z.getnames():
                if VpkImportService._is_vpk_or_image(name):
                    filename = os.path.basename(name)
                    if not filename: continue
                    
                    # 7z 的解压通常比较直接
                    # 我们过滤并解压特定文件
                    z.extract(targets=[name], path=str(target_path))
                    # 如果有路径嵌套，我们需要移动它（虽然题目规定假定无嵌套，但这里做个简单的扁平化处理以防万一）
                    temp_extracted = target_path / name
                    if temp_extracted != target_path / filename:
                        if (target_path / filename).exists():
                            (target_path / filename).unlink()
                        shutil.move(str(temp_extracted), str(target_path / filename))
                        # 检查并删除空的中间目录
                        parent = temp_extracted.parent
                        while parent != target_path:
                            if not os.listdir(parent):
                                os.rmdir(parent)
                                parent = parent.parent
                            else:
                                break

    @staticmethod
    def _extract_tar_zst(file_path: Path, target_path: Path):
        if not HAS_ZSTD:
            raise Exception("系统未安装 zstandard，无法处理 .tar.zst 文件")
        
        dctx = zstd.ZstdDecompressor()
        with open(file_path, 'rb') as ifh:
            with dctx.stream_reader(ifh) as reader:
                with tarfile.open(fileobj=reader, mode='r|') as tar:
                    for member in tar:
                        if member.isfile() and VpkImportService._is_vpk_or_image(member.name):
                            filename = os.path.basename(member.name)
                            if not filename: continue
                            
                            dest_path = target_path / filename
                            # 提取文件
                            fileobj = tar.extractfile(member)
                            if fileobj:
                                with open(dest_path, "wb") as target:
                                    shutil.copyfileobj(fileobj, target)

    @staticmethod
    def _is_vpk_or_image(name: str) -> bool:
        lower_name = name.lower()
        if lower_name.endswith('.vpk'):
            return True
        image_exts = ['.jpg', '.jpeg', '.png', '.tga', '.bmp', '.gif']
        return any(lower_name.endswith(ext) for ext in image_exts)
