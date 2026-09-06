"""SFTP 相关的 API 方法(mixin)。

由 backend/api.py 的 VpkManagerApi 继承使用;依赖宿主提供的
self.storage_service / self.sftp_service / self.upload_service / self.download_service。
"""

import logging
import os
from typing import List

from .services.storage_service import DEFAULT_SFTP_SETTINGS

logger = logging.getLogger(__name__)


class SftpApiMixin:
    """向 PyWebView 前端暴露的 SFTP 相关方法"""

    def get_sftp_settings(self) -> dict:
        """获取 SFTP 设置。"""
        try:
            return self.storage_service.get_sftp_settings()
        except Exception as e:
            logger.error(f"获取 SFTP 设置出错: {e}")
            return dict(DEFAULT_SFTP_SETTINGS)

    def save_sftp_settings(self, settings: dict) -> dict:
        """保存 SFTP 设置。"""
        try:
            self.storage_service.save_sftp_settings(settings)
            return {"success": True}
        except Exception as e:
            logger.error(f"保存 SFTP 设置出错: {e}")
            return {"success": False, "error": str(e)}

    def list_remote_vpks(self) -> dict:
        """列出远程 SFTP 服务器上的 VPK 文件"""
        try:
            config = self.storage_service.get_sftp_settings()
            files = self.sftp_service.list_vpk_files(config)
            return {"success": True, "files": files}
        except Exception as e:
            logger.error(f"获取远程文件列表出错: {e}")
            return {"success": False, "error": str(e)}

    def delete_remote_vpk(self, file_path: str) -> dict:
        """删除远程 SFTP 服务器上的 VPK 文件"""
        try:
            config = self.storage_service.get_sftp_settings()
            success = self.sftp_service.delete_file_with_images(config, file_path)
            if success:
                return {"success": True}
            else:
                return {"success": False, "error": "删除失败"}
        except Exception as e:
            logger.error(f"删除远程文件出错: {e}")
            return {"success": False, "error": str(e)}

    def delete_multiple_remote_vpks(self, file_paths: List[str]) -> dict:
        """批量删除远程 SFTP 服务器上的 VPK 文件"""
        try:
            config = self.storage_service.get_sftp_settings()
            success_count = 0
            errors = []
            for path in file_paths:
                if self.sftp_service.delete_file_with_images(config, path):
                    success_count += 1
                else:
                    errors.append(path)

            return {
                "success": len(errors) == 0,
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors
            }
        except Exception as e:
            logger.error(f"批量删除远程文件出错: {e}")
            return {"success": False, "error": str(e)}

    def rename_remote_vpk(self, old_path: str, new_path: str) -> dict:
        """重命名远程 SFTP 服务器上的 VPK 文件 (用于禁用/启用)"""
        try:
            config = self.storage_service.get_sftp_settings()
            success = self.sftp_service.rename_file_with_images(config, old_path, new_path)
            if success:
                return {"success": True}
            else:
                return {"success": False, "error": "重命名失败"}
        except Exception as e:
            logger.error(f"重命名远程文件出错: {e}")
            return {"success": False, "error": str(e)}

    def download_remote_vpks(self, remote_file_paths: List[str]) -> dict:
        """将远程 VPK 文件及关联图片下载到本地 addons 目录"""
        try:
            l4d2_dir = self.storage_service.get_l4d2_directory()
            if not l4d2_dir:
                return {"success": False, "error": "未配置本地 L4D2 目录"}

            local_addons_dir = os.path.join(l4d2_dir, "left4dead2", "addons")
            config = self.storage_service.get_sftp_settings()

            return self.download_service.download(remote_file_paths, local_addons_dir, config)
        except Exception as e:
            logger.error(f"下载远程文件出错: {e}")
            return {"success": False, "error": str(e)}

    def upload_local_vpks(self, local_file_paths: List[str], better_naming: bool = False) -> dict:
        """将本地 VPK 文件及关联图片上传到远程 SFTP 服务器"""
        try:
            config = self.storage_service.get_sftp_settings()
            remote_addons_path = config.get('addons_path', '')
            if not remote_addons_path:
                return {"success": False, "error": "未配置远程 addons 路径"}

            return self.upload_service.upload(local_file_paths, remote_addons_path, config, better_naming)
        except Exception as e:
            logger.error(f"上传本地文件出错: {e}")
            return {"success": False, "error": str(e)}
