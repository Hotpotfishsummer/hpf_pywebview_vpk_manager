"""VPK 下载服务 - 从 SFTP 服务器下载 VPK 及关联图片到本地 addons 目录"""

import logging
import os
from typing import Any, Dict, List

from ..naming import IMAGE_EXTS, vpk_stem_for_association

logger = logging.getLogger(__name__)


class VpkDownloadService:
    """把远端 addons 目录中的 VPK 下载到本地 addons 目录"""

    def __init__(self, sftp_service):
        self.sftp_service = sftp_service

    def download(
        self,
        remote_file_paths: List[str],
        local_addons_dir: str,
        config: Dict[str, str],
    ) -> Dict[str, Any]:
        """下载选中的远端 VPK(含关联图片),返回 {success, downloaded_count}"""
        success_count = 0

        for r_path in remote_file_paths:
            file_name = os.path.basename(r_path)
            l_path = os.path.join(local_addons_dir, file_name)

            if not self.sftp_service.download_file(config, r_path, l_path):
                logger.warning(f"下载 VPK 失败(跳过关联图片): {r_path}")
                continue
            success_count += 1

            # 关联图片基名与缩略图约定一致:x.vpk.disabled → x.vpk
            base_name = vpk_stem_for_association(file_name)
            remote_dir = os.path.dirname(r_path)
            for ext in IMAGE_EXTS:
                r_img_path = os.path.join(remote_dir, base_name + ext).replace('\\', '/')
                if self.sftp_service.file_exists(config, r_img_path):
                    l_img_path = os.path.join(local_addons_dir, base_name + ext)
                    self.sftp_service.download_file(config, r_img_path, l_img_path)

        return {"success": True, "downloaded_count": success_count}
