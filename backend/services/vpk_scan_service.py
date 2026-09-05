"""VPK 扫描服务 - 遍历 addons 与 workshop 目录,收集 VPK 元数据"""

import logging
import os
from typing import Any, Dict, List

from ..models import VpkFile

logger = logging.getLogger(__name__)


class VpkScanService:
    """扫描 L4D2 目录下的本地与创意工坊 VPK 文件"""

    def __init__(self, metadata_service):
        self.metadata_service = metadata_service

    def scan(self, directory: str) -> Dict[str, List[Dict[str, Any]]]:
        """返回 {local_vpks, workshop_vpks},元素为 VpkFile 序列化后的 dict"""
        addons_dir = os.path.join(directory, "left4dead2", "addons")
        workshop_dir = os.path.join(addons_dir, "workshop")

        return {
            "local_vpks": self._scan_dir(addons_dir),
            "workshop_vpks": self._scan_dir(workshop_dir),
        }

    def _scan_dir(self, scan_dir: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not os.path.isdir(scan_dir):
            return results

        for filename in os.listdir(scan_dir):
            filename_lower = filename.lower()
            if not (filename_lower.endswith(".vpk") or filename_lower.endswith(".vpk.disabled")):
                continue
            vpk_path = os.path.join(scan_dir, filename)
            try:
                vpk_file = self.metadata_service.get_vpk_metadata(vpk_path)
                if vpk_file:
                    results.append(self._vpk_to_dict(vpk_file))
            except Exception as e:
                logger.warning(f"处理文件 {filename} 出错: {e}")

        return results

    @staticmethod
    def _vpk_to_dict(vpk_file: VpkFile) -> dict:
        """Convert VpkFile object to dictionary for JSON serialization."""
        return {
            "name": vpk_file.name,
            "path": vpk_file.path,
            "size": vpk_file.size,
            "modified_time": vpk_file.modified_time,
            "is_valid": vpk_file.is_valid,
            "is_disabled": vpk_file.is_disabled,
            "thumbnail_path": vpk_file.thumbnail_path,
            "addontitle": vpk_file.addontitle,
            "display_name": vpk_file.display_name,
        }
