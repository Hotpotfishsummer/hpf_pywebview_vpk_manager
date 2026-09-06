"""PyWebView API - 前后端通信接口"""

import logging
import os
import sys
from pathlib import Path

from .services.vpk_metadata_service import VpkMetadataService
from .services.vpk_export_service import VpkExportService
from .services.vpk_import_service import VpkImportService
from .services.storage_service import StorageService
from .services.sftp_service import SftpService
from .services.config_service import ConfigService
from .services.vpk_localize_service import VpkLocalizeService
from .services.vpk_scan_service import VpkScanService
from .services.vpk_upload_service import VpkUploadService
from .services.vpk_download_service import VpkDownloadService
from .api_sftp import SftpApiMixin
from .api_app import AppApiMixin
from .api_ops import VpkOpsApiMixin

# 确保存储目录存在
STORAGE_BASE_DIR = Path.home() / 'Documents' / 'L4D2-VPK-Manager'
STORAGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = STORAGE_BASE_DIR / 'vpk_manager.log'

# 安全地初始化日志处理器，通常 main.py 已经配置过了，但这里也做一层保护
handlers = [logging.FileHandler(LOG_FILE, encoding='utf-8')]
if sys.stdout is not None:
    handlers.append(logging.StreamHandler(sys.stdout))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)


class VpkManagerApi(SftpApiMixin, AppApiMixin, VpkOpsApiMixin):
    """VPK 管理器 API 类 - 向 PyWebView 前端暴露的方法

    SFTP 相关方法(get_sftp_settings 等 8 个)由 SftpApiMixin 提供;
    目录/系统交互方法(get_last_directory 等 6 个)由 AppApiMixin 提供;
    VPK 核心操作(scan/export/delete/import/localize 等 7 方法)由 VpkOpsApiMixin 提供。
    """

    # PyWebView 应该反射的公开方法列表
    _PUBLIC_METHODS = {
        'get_last_directory',
        'browse_directory',
        'get_downloads_directory',
        'scan_vpk_files',
        'export_vpks',
        'import_compressed_vpks',
        'localize_workshop_vpks',
        'open_directory',
        'delete_vpk_file',
        'delete_multiple_vpk_files',
        'enable_vpk_file',
        'reset_app_data',
        'log_from_js',
        'get_sftp_settings',
        'save_sftp_settings',
        'list_remote_vpks',
        'delete_remote_vpk',
        'delete_multiple_remote_vpks',
        'rename_remote_vpk',
        'download_remote_vpks',
        'upload_local_vpks',
        'open_external_url',
    }

    def __init__(self):
        """用服务初始化 API"""
        logger.info("正在初始化 VpkManagerApi...")
        self.metadata_service = VpkMetadataService()
        logger.info("  - VpkMetadataService 初始化完成")
        self.export_service = VpkExportService()
        logger.info("  - VpkExportService 初始化完成")
        self.import_service = VpkImportService()
        logger.info("  - VpkImportService 初始化完成")
        self.storage_service = StorageService()
        logger.info("  - StorageService 初始化完成")
        self.sftp_service = SftpService()
        logger.info("  - SftpService 初始化完成")
        self.localize_service = VpkLocalizeService(self.metadata_service)
        logger.info("  - VpkLocalizeService 初始化完成")
        self.scan_service = VpkScanService(self.metadata_service)
        logger.info("  - VpkScanService 初始化完成")
        self.upload_service = VpkUploadService(self.metadata_service, self.sftp_service)
        logger.info("  - VpkUploadService 初始化完成")
        self.download_service = VpkDownloadService(self.sftp_service)
        logger.info("  - VpkDownloadService 初始化完成")
        
        # 获取应用根目录
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_service = ConfigService(base_path)
        logger.info(f"  - ConfigService 初始化完成 (base_path: {base_path})")
        
        # 启动时自动运行: 检查并更新 autoexec.cfg
        self._auto_apply_config()
        
        self._is_scanning = False
        self._is_exporting = False
        self._window = None  # 存储 webview 窗口引用
        logger.info("VpkManagerApi 初始化完成")

    def _auto_apply_config(self):
        """启动时自动应用配置"""
        try:
            l4d2_dir = self.storage_service.get_l4d2_directory()
            if l4d2_dir:
                logger.info(f"正在启动自动配置更新: {l4d2_dir}")
                self.config_service.apply_autoexec_template(l4d2_dir)
            else:
                logger.info("未找到保存的 L4D2 目录，略过启动自动配置")
        except Exception as e:
            logger.error(f"启动自动配置出错: {e}")

    def set_window(self, window):
        """设置 webview 窗口引用"""
        self._window = window

    def log_from_js(self, level: str, message: str):
        """接收来自前端的日志并记录到 Python 日志中。"""
        log_map = {
            'debug': logger.debug,
            'info': logger.info,
            'warn': logger.warning,
            'error': logger.error
        }
        log_func = log_map.get(level.lower(), logger.info)
        log_func(f"[前端 {level.upper()}] {message}")

    def __dir__(self):
        """返回仅公开方法用于 PyWebView API 反射。
        
        这防止了当 PyWebView 尝试自省对象时发生的无限递归。
        我们仅暴露公开方法，不暴露内部服务对象。
        """
        return list(self._PUBLIC_METHODS)

    def __getattr__(self, name: str):
        """防止 PyWebView 反射中的无限递归，通过过滤属性。
        
        这对 debugpy 兼容性至关重要。没有这个，PyWebView 的 API 反射
        可能会在 debugpy 监控时触发无限递归。
        """
        # 仅允许访问公开方法和公开属性
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return object.__getattribute__(self, name)
