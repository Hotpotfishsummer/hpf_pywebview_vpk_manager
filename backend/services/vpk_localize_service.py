"""VPK 本地化服务 - 将创意工坊 VPK 复制到 addons 并把原文件归档到 .trash"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..naming import find_associated_images

logger = logging.getLogger(__name__)


class VpkLocalizeService:
    """把创意工坊(或任意目录)的 VPK 复制到本地 addons 目录"""

    def __init__(self, metadata_service):
        """metadata_service: 用于 better_naming 时读取 addontitle"""
        self.metadata_service = metadata_service

    def localize(self, file_paths: List[str], l4d2_dir: str, better_naming: bool = False) -> Dict[str, Any]:
        """本地化选中的 VPK 文件,返回 {success, success_count, errors}"""
        addons_dir = os.path.join(l4d2_dir, "left4dead2", "addons")
        os.makedirs(addons_dir, exist_ok=True)

        trash_dir = os.path.join(l4d2_dir, "left4dead2", "addons", "workshop", ".trash")
        os.makedirs(trash_dir, exist_ok=True)

        success_count = 0
        errors: List[str] = []

        for src_path_str in file_paths:
            try:
                src_path = Path(src_path_str).absolute()
                if not src_path.exists():
                    errors.append(f"文件不存在: {src_path.name}")
                    continue

                is_in_workshop = "workshop" in [p.name.lower() for p in src_path.parents]
                base_name = self._resolve_base_name(src_path, better_naming)

                # 复制 VPK 到 addons(禁用状态的文件统一恢复为 .vpk)
                dest_vpk = Path(addons_dir) / f"{base_name}.vpk"
                shutil.copy2(src_path, dest_vpk)

                # 复制并重命名同名图片到 addons(大小写不敏感扫描)
                associated_files: List[Path] = []
                for img_src, _ext in find_associated_images(str(src_path.parent), src_path.name):
                    dest_img = Path(addons_dir) / f"{base_name}{Path(img_src).suffix}"
                    shutil.copy2(img_src, dest_img)
                    associated_files.append(Path(img_src))

                # 本地化成功后,把创意工坊下的原文件移入 .trash
                if is_in_workshop:
                    self._move_to_trash(src_path, trash_dir)
                    for img_path in associated_files:
                        if img_path.exists():
                            self._move_to_trash(img_path, trash_dir)

                success_count += 1
            except Exception as e:
                errors.append(f"本地化 {os.path.basename(src_path_str)} 失败: {str(e)}")

        return {
            "success": len(errors) == 0,
            "success_count": success_count,
            "errors": errors if errors else None,
        }

    def _resolve_base_name(self, src_path: Path, better_naming: bool) -> str:
        """确定本地化后的文件名;better_naming 时用 addontitle 清洗命名。

        禁用文件(x.vpk.disabled)统一恢复为 x.vpk——即以剥离 .disabled
        后的 stem 为基础(修复旧实现产生 x.vpk.vpk 双后缀的问题)。
        """
        name = src_path.name
        if name.lower().endswith('.disabled'):
            fallback = Path(name[: -len('.disabled')]).stem
        else:
            fallback = src_path.stem

        if not better_naming:
            return fallback

        vpk_meta = self.metadata_service.get_vpk_metadata(str(src_path))
        if vpk_meta and vpk_meta.addontitle:
            from ..naming import build_export_base_name
            return build_export_base_name(vpk_meta.addontitle, name, fallback)
        return fallback

    @staticmethod
    def _move_to_trash(path: Path, trash_dir: str) -> None:
        trash_path = os.path.join(trash_dir, path.name)
        if os.path.exists(trash_path):
            try:
                os.remove(trash_path)
            except OSError:
                pass
        shutil.move(str(path), trash_path)
