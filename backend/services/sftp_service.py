"""SFTP 远程文件管理服务"""

import os
import logging
import paramiko
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class SftpService:
    """处理与远端服务器的 SFTP 通信和文件管理"""

    def __init__(self, connect_timeout: float = 10.0):
        self._ssh_client = None
        self._sftp = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        # 连接超时秒数;构造时可覆盖(慢速网络/代理场景)
        self.connect_timeout = connect_timeout

    def _get_client(self, config: Dict[str, str]) -> paramiko.SFTPClient:
        """获取或创建 SFTP 客户端"""
        address = config.get('address', '')
        username = config.get('username', '')
        password = config.get('password', '')

        if not address or not username:
            raise ValueError("SFTP 地址或用户名未配置")

        # 解析地址和端口
        if ':' in address:
            host, port = address.rsplit(':', 1)
            if not port.isdigit():
                raise ValueError(f"无效的 SFTP 端口: '{port}'(地址格式应为 host:port)")
            port = int(port)
            if not 1 <= port <= 65535:
                raise ValueError(f"SFTP 端口超出范围: {port}")
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
            self._ssh_client.connect(host, port, username, password, timeout=self.connect_timeout)
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

        sftp = self._get_client(config)
        files = []
        try:
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
            # 目录不可读时视为空列表(调用方展示"无文件")
            logger.error(f"无法访问远程路径 {remote_path}: {e}")
            return []

        return sorted(files, key=lambda x: x['name'].lower())

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

    # 远端启用/禁用/删除时同步处理的关联文件扩展名。
    # 与 naming.IMAGE_EXTS(本地缩略图扫描,含 tga/bmp/gif)语义不同:
    # 此处对齐"本地批量禁用/删除"的行为(图片 + txt 描述文件),不随意扩集。
    ASSOCIATED_EXTS = ('.jpg', '.png', '.jpeg', '.txt')

    def rename_file_with_images(self, config: Dict[str, str], old_path: str, new_path: str) -> bool:
        """重命名远程 VPK,并同步重命名同名关联图片(对齐本地禁用/启用行为)"""
        if not self.rename_file(config, old_path, new_path):
            return False

        old_base = os.path.splitext(old_path)[0]
        new_base = os.path.splitext(new_path)[0]
        for ext in self.ASSOCIATED_EXTS:
            old_img = old_base + ext
            new_img = new_base + ext
            if self.file_exists(config, old_img):
                if not self.rename_file(config, old_img, new_img):
                    logger.warning(f"关联文件重命名失败(忽略): {old_img} -> {new_img}")
        return True

    def delete_file_with_images(self, config: Dict[str, str], file_path: str) -> bool:
        """删除远程 VPK,并同步删除同名关联图片(对齐本地删除行为)"""
        if not self.delete_file(config, file_path):
            return False

        base = os.path.splitext(file_path)[0]
        for ext in self.ASSOCIATED_EXTS:
            img = base + ext
            if self.file_exists(config, img):
                if not self.delete_file(config, img):
                    logger.warning(f"关联文件删除失败(忽略): {img}")
        return True

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
        """关闭连接并释放线程池(应用退出或主动断开时调用)"""
        if self._sftp:
            self._sftp.close()
        if self._ssh_client:
            self._ssh_client.close()
        self._sftp = None
        self._ssh_client = None
        self._executor.shutdown(wait=False)
