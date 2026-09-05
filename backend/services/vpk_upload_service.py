"""VPK 上传服务 - 将本地 VPK 及关联图片上传到 SFTP 服务器"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from ..naming import build_export_base_name, find_associated_images

logger = logging.getLogger(__name__)


class VpkUploadService:
    """把本地 addons 目录中的 VPK 上传到远端 addons 目录"""

    def __init__(self, metadata_service, sftp_service):
        self.metadata_service = metadata_service
        self.sftp_service = sftp_service

    def upload(
        self,
        local_file_paths: List[str],
        remote_addons_path: str,
        config: Dict[str, str],
        better_naming: bool = False,
    ) -> Dict[str, Any]:
        """上传选中的本地 VPK(含关联图片),返回 {success, uploaded_count}"""
        success_count = 0

        for l_path in local_file_paths:
            src_path = Path(l_path)
            is_disabled = l_path.lower().endswith('.vpk.disabled')
            base_name = self._resolve_base_name(src_path, better_naming)

            suffix = ".vpk.disabled" if is_disabled else ".vpk"
            r_path = os.path.join(remote_addons_path, f"{base_name}{suffix}").replace('\\', '/')

            if self.sftp_service.upload_file(config, l_path, r_path):
                success_count += 1
                self._upload_associated_images(src_path, base_name, remote_addons_path, config)

        return {"success": True, "uploaded_count": success_count}

    def _resolve_base_name(self, src_path: Path, better_naming: bool) -> str:
        """确定远端文件名;better_naming 时用 addontitle 清洗命名并追加工坊 ID。

        禁用文件(x.vpk.disabled)以剥离 .vpk.disabled 后的名字为基础,
        避免拼出 x.vpk.vpk.disabled 双后缀(修复旧实现的问题)。
        """
        name = src_path.name
        if name.lower().endswith('.vpk.disabled'):
            fallback = name[: -len('.vpk.disabled')]
        else:
            fallback = src_path.stem

        if not better_naming:
            return fallback
        title = self.metadata_service.get_addontitle(str(src_path))
        return build_export_base_name(title, name, fallback)

    def _upload_associated_images(
        self, src_path: Path, base_name: str, remote_addons_path: str, config: Dict[str, str]
    ) -> None:
        """上传同名关联图片(对 .vpk.disabled 匹配 x.jpg,保持上传侧既有约定)"""
        uploaded_exts_lower = set()
        for f_path, f_ext in find_associated_images(
            str(src_path.parent), src_path.name, strip_vpk_suffix=True
        ):
            if f_ext not in uploaded_exts_lower:
                remote_img_name = f"{base_name}{f_ext}"
                r_img_path = os.path.join(remote_addons_path, remote_img_name).replace('\\', '/')
                if self.sftp_service.upload_file(config, f_path, r_img_path):
                    uploaded_exts_lower.add(f_ext)
