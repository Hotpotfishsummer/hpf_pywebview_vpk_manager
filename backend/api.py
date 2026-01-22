"""PyWebView API - 前后端通信接口"""

import asyncio
import logging
import os
import sys
import webview
from typing import List, Optional
from pathlib import Path

from .models import ApiResponse, VpkFile
from .services.vpk_metadata_service import VpkMetadataService
from .services.vpk_export_service import VpkExportService
from .services.vpk_import_service import VpkImportService
from .services.storage_service import StorageService

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


class VpkManagerApi:
    """VPK 管理器 API 类 - 向 PyWebView 前端暴露的方法"""

    # PyWebView 应该反射的公开方法列表
    _PUBLIC_METHODS = {
        'get_last_directory',
        'browse_directory',
        'get_downloads_directory',
        'scan_vpk_files',
        'export_vpks',
        'import_compressed_vpks',
        'delete_vpk_file',
        'delete_multiple_vpk_files',
        'log_from_js',
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
        self._is_scanning = False
        self._is_exporting = False
        self._window = None  # 存储 webview 窗口引用
        logger.info("VpkManagerApi 初始化完成")

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

    def get_last_directory(self) -> str:
        """从存储中获取上次选择的 L4D2 目录"""
        try:
            return self.storage_service.get_l4d2_directory() or ""
        except Exception as e:
            logger.error(f"获取上次目录出错: {e}")
            return ""

    def browse_directory(self) -> Optional[str]:
        """打开系统文件对话框选择目录。
        
        返回:
            选中的目录路径或如果用户取消则返回 None
        """
        logger.info("browse_directory() 被调用")
        try:
            if not self._window:
                logger.error("WebView 窗口引用未设置，尝试使用 tkinter 备选方案")
                import tkinter as tk
                from tkinter.filedialog import askdirectory
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                directory = askdirectory(title="选择 L4D2 安装目录")
                root.destroy()
                return directory if directory else None

            # 使用 pywebview 原生对话框 (推荐)
            initial_dir = self.storage_service.get_l4d2_directory() or str(Path.home())
            logger.info(f"打开原生目录选择器，初始目录: {initial_dir}")
            
            result = self._window.create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=initial_dir
            )
            
            if result and len(result) > 0:
                # webview.FOLDER_DIALOG 返回的是元组或列表
                directory = result[0] if isinstance(result, (list, tuple)) else result
                logger.info(f"选择的目录: {directory}")
                return directory
            else:
                logger.info("用户取消了目录选择")
                return None
                
        except Exception as e:
            logger.error(f"打开目录选择器出错: {e}", exc_info=True)
            return None

    def get_downloads_directory(self) -> str:
        """获取用户下载目录。
        
        返回:
            下载目录的路径
        """
        try:
            from pathlib import Path
            downloads_dir = str(Path.home() / "Downloads")
            if os.path.exists(downloads_dir):
                return downloads_dir
            
            # 如果下载目录不存在则返回家目录
            return str(Path.home())
        except Exception as e:
            logger.warning(f"获取下载目录出错: {e}")
            return "."

    def scan_vpk_files(self, directory: str) -> dict:
        """扫描目录以查找 VPK 文件。

        参数:
            directory: L4D2 根目录路径

        返回:
            包含成功状态和本地/创意工坊 VPK 文件列表的字典
        """
        if self._is_scanning:
            return {
                "success": False,
                "error": "扫描已在进行中",
                "local_vpks": [],
                "workshop_vpks": [],
            }

        try:
            self._is_scanning = True
            logger.info(f"扫描 VPK 文件: {directory}")

            # 验证目录
            if not os.path.isdir(directory):
                return {
                    "success": False,
                    "error": f"目录不存在: {directory}",
                    "local_vpks": [],
                    "workshop_vpks": [],
                }

            # 保存目录供以后使用
            self.storage_service.save_l4d2_directory(directory)

            addons_dir = os.path.join(directory, "left4dead2", "addons")
            workshop_dir = os.path.join(directory, "left4dead2", "addons", "workshop")

            local_vpks = []
            workshop_vpks = []

            # 扫描本地 VPK 文件
            if os.path.exists(addons_dir):
                for filename in os.listdir(addons_dir):
                    if filename.endswith(".vpk"):
                        vpk_path = os.path.join(addons_dir, filename)
                        try:
                            vpk_file = self.metadata_service.get_vpk_metadata(vpk_path)
                            if vpk_file:
                                local_vpks.append(self._vpk_to_dict(vpk_file))
                        except Exception as e:
                            logger.warning(f"处理文件 {filename} 出错: {e}")

            # 扫描创意工坊文件
            if os.path.exists(workshop_dir):
                for filename in os.listdir(workshop_dir):
                    if filename.endswith(".vpk"):
                        vpk_path = os.path.join(workshop_dir, filename)
                        try:
                            vpk_file = self.metadata_service.get_vpk_metadata(vpk_path)
                            if vpk_file:
                                workshop_vpks.append(self._vpk_to_dict(vpk_file))
                        except Exception as e:
                            logger.warning(f"处理文件 {filename} 出错: {e}")

            return {
                "success": True,
                "local_vpks": local_vpks,
                "workshop_vpks": workshop_vpks,
            }

        except Exception as e:
            logger.error(f"扫描 VPK 文件出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "local_vpks": [],
                "workshop_vpks": [],
            }
        finally:
            self._is_scanning = False

    def export_vpks(self, file_paths: List[str], output_dir: str, better_naming: bool = False) -> dict:
        """将选定的 VPK 文件导出到压缩归档。

        参数:
            file_paths: 要导出的 VPK 文件路径列表
            output_dir: 保存导出归档的目录
            better_naming: 是否在压缩包内重命名文件

        返回:
            包含成功状态和导出详情的字典
        """
        if self._is_exporting:
            return {
                "success": False,
                "error": "导出已在进行中",
            }

        try:
            self._is_exporting = True
            logger.info(f"开始导出 {len(file_paths)} 个 VPK 文件")

            # 提取文件标题用于压缩包命名
            titles = []
            for path in file_paths:
                title = self.metadata_service.get_addontitle(path)
                titles.append(title)

            # 直接运行，pywebview 会在单独的线程中调用此方法
            result = self.export_service.export_vpks(
                file_paths,
                output_dir,
                titles=titles,
                better_naming=better_naming
            )

            return {
                "success": True,
                "message": f"导出完成: {result}",
                "file_path": result,
            }

        except Exception as e:
            logger.error(f"导出 VPK 文件出错: {e}")
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            self._is_exporting = False

    def delete_vpk_file(self, file_path: str, disable: bool = True) -> dict:
        """删除或禁用 VPK 文件。

        参数:
            file_path: VPK 文件路径
            disable: 如果为 True，重命名为 .vpk.disabled；如果为 False，删除

        返回:
            包含成功状态的字典
        """
        try:
            logger.info(
                f"{'禁用' if disable else '删除'} VPK 文件: {file_path}"
            )

            if not os.path.exists(file_path):
                return {"success": False, "error": f"文件不存在: {file_path}"}

            if disable:
                # 重命名为 .vpk.disabled
                new_path = f"{file_path}.disabled"
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(file_path, new_path)
            else:
                # 删除文件
                os.remove(file_path)

            return {"success": True, "message": f"文件{'禁用' if disable else '删除'}成功"}

        except Exception as e:
            logger.error(f"处理 VPK 文件出错: {e}")
            return {"success": False, "error": str(e)}

    def enable_vpk_file(self, file_path: str) -> dict:
        """通过移除 .disabled 后缀启用禁用的 VPK 文件。

        参数:
            file_path: 禁用的 VPK 文件路径 (.vpk.disabled)

        返回:
            包含成功状态的字典
        """
        try:
            logger.info(f"启用 VPK 文件: {file_path}")

            if not os.path.exists(file_path):
                return {"success": False, "error": f"文件不存在: {file_path}"}

            if not file_path.endswith(".disabled"):
                return {"success": False, "error": "文件未被禁用"}

            # 移除 .disabled 后缀
            new_path = file_path[:-9]  # 移除 ".disabled" (9 个字符)
            if os.path.exists(new_path):
                return {"success": False, "error": f"文件已存在: {new_path}"}

            os.rename(file_path, new_path)
            logger.info(f"成功启用 VPK 文件: {new_path}")
            return {"success": True, "message": "文件启用成功"}

        except Exception as e:
            logger.error(f"启用 VPK 文件出错: {e}")
            return {"success": False, "error": str(e)}

    def delete_multiple_vpk_files(self, file_paths: List[str], disable: bool = True) -> dict:
        """删除或禁用多个 VPK 文件。

        参数:
            file_paths: VPK 文件路径列表
            disable: 如果为 True，重命名为 .vpk.disabled；如果为 False，删除

        返回:
            包含成功状态和计数的字典
        """
        try:
            logger.info(
                f"{'禁用' if disable else '删除'} {len(file_paths)} 个 VPK 文件"
            )

            success_count = 0
            error_count = 0
            errors = []

            for file_path in file_paths:
                try:
                    if not os.path.exists(file_path):
                        error_count += 1
                        errors.append(f"File not found: {file_path}")
                        continue

                    if disable:
                        new_path = f"{file_path}.disabled"
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(file_path, new_path)
                    else:
                        os.remove(file_path)

                    success_count += 1
                    logger.info(f"Successfully {'disabled' if disable else 'deleted'} {file_path}")

                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing {file_path}: {str(e)}")
                    logger.error(f"Error processing {file_path}: {e}")

            return {
                "success": error_count == 0,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
                "message": f"Processed {success_count} files successfully, {error_count} errors",
            }

        except Exception as e:
            logger.error(f"Error deleting multiple VPK files: {e}")
            return {"success": False, "error": str(e)}

    def import_compressed_vpks(self) -> dict:
        """打开文件对话框选择压缩包，并导入其中的 VPK。"""
        try:
            if not self._window:
                return {"success": False, "error": "WebView 窗口未就绪"}

            # 获取当前 L4D2 目录以确定 addons 文件夹
            l4d2_dir = self.storage_service.get_l4d2_directory()
            if not l4d2_dir:
                return {"success": False, "error": "请先选择 L4D2 安装目录"}

            addons_dir = os.path.join(l4d2_dir, "left4dead2", "addons")
            if not os.path.exists(addons_dir):
                return {"success": False, "error": f"addons 目录不存在: {addons_dir}"}

            # 1. 选择文件
            file_types = ('Addon Archives (*.zip;*.7z;*.zst)', 'All files (*.*)')
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=file_types
            )

            if not result:
                return {"success": True, "message": "用户取消了选择", "imported_count": 0}

            # 2. 调用导入服务
            import_result = self.import_service.import_compressed_files(result, addons_dir)
            
            # 如果成功，自动重新扫描一下
            if import_result.get("success") or import_result.get("imported_count", 0) > 0:
                logger.info(f"导入完成，成功导入了 {import_result.get('imported_count')} 个压缩包中的文件")

            return import_result

        except Exception as e:
            logger.error(f"导入压缩包出错: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

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
