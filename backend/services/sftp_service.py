"""SFTP 远程文件管理服务"""

import os
import stat
import logging
import paramiko
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class SftpService:
    """处理与远端服务器的 SFTP 通信和文件管理"""
    
    def __init__(self):
        self._ssh_client = None
        self._sftp = None
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _get_client(self, config: Dict[str, str]) -> paramiko.SFTPClient:
        """获取或创建 SFTP 客户端"""
        address = config.get('address', '')
        username = config.get('username', '')
        password = config.get('password', '')

        if not address or not username:
            raise ValueError("SFTP 地址或用户名未配置")

        # 解析地址和端口
        if ':' in address:
            host, port = address.split(':')
            port = int(port)
        else:
            host, port = address, 22

        # 检查现有连接是否有效
        if self._ssh_client and self._ssh_client.get_transport() and self._ssh_client.get_transport().is_active():
            if self._sftp:
                return self._sftp

        # 创建新连接
        try:
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh_client.connect(host, port, username, password, timeout=10)
            self._sftp = self._ssh_client.open_sftp()
            return self._sftp
        except Exception as e:
            logger.error(f"连接 SFTP 失败: {e}")
            self._ssh_client = None
            self._sftp = None
            raise

    def list_vpk_files(self, config: Dict[str, str]) -> List[Dict[str, Any]]:
        """列出远端 addons 目录下的 VPK 文件"""
        remote_path = config.get('addons_path', '')
        if not remote_path:
            raise ValueError("未配置远程 addons 路径")

        try:
            sftp = self._get_client(config)
            files = []
            
            try:
                # 尝试列出目录内容
                for attr in sftp.listdir_attr(remote_path):
                    filename_lower = attr.filename.lower()
                    if filename_lower.endswith('.vpk') or filename_lower.endswith('.vpk.disabled'):
                        files.append({
                            'name': attr.filename,
                            'path': os.path.join(remote_path, attr.filename).replace('\\', '/'),
                            'size': round(attr.st_size / (1024 * 1024), 2),  # MB
                            'modified_time': attr.st_mtime,
                            'is_disabled': filename_lower.endswith('.disabled')
                        })
            except IOError as e:
                logger.error(f"无法访问远程路径 {remote_path}: {e}")
                return []
                
            return sorted(files, key=lambda x: x['name'].lower())
        except Exception as e:
            logger.error(f"获取远程文件列表失败: {e}")
            raise

    def delete_file(self, config: Dict[str, str], file_path: str) -> bool:
        """删除远程文件"""
        try:
            sftp = self._get_client(config)
            sftp.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"删除远程文件失败 {file_path}: {e}")
            return False

    def rename_file(self, config: Dict[str, str], old_path: str, new_path: str) -> bool:
        """重命名远程文件（用于启用/禁用）"""
        try:
            sftp = self._get_client(config)
            sftp.rename(old_path, new_path)
            return True
        except Exception as e:
            logger.error(f"重命名远程文件失败 {old_path} -> {new_path}: {e}")
            return False

    def download_file(self, config: Dict[str, str], remote_path: str, local_path: str) -> bool:
        """从远端下载文件到本地"""
        try:
            sftp = self._get_client(config)
            # 确保本地目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            logger.error(f"下载文件失败 {remote_path} -> {local_path}: {e}")
            return False

    def upload_file(self, config: Dict[str, str], local_path: str, remote_path: str) -> bool:
        """从本地上传文件到远端"""
        try:
            sftp = self._get_client(config)
            sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            logger.error(f"上传文件失败 {local_path} -> {remote_path}: {e}")
            return False

    def file_exists(self, config: Dict[str, str], remote_path: str) -> bool:
        """检查远程文件是否存在"""
        try:
            sftp = self._get_client(config)
            sftp.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def close(self):
        """关闭连接"""
        if self._sftp:
            self._sftp.close()
        if self._ssh_client:
            self._ssh_client.close()
        self._sftp = None
        self._ssh_client = None
