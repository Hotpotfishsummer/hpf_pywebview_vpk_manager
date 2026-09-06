"""应用/系统交互相关的 API 方法(mixin)。

由 backend/api.py 的 VpkManagerApi 继承使用;依赖宿主提供的
self.storage_service 与 self._window(webview 窗口引用)。
"""

import logging
import os
import shutil
import sys
import webbrowser
from pathlib import Path

import webview

logger = logging.getLogger(__name__)


class AppApiMixin:
    """向 PyWebView 前端暴露的目录/系统交互方法"""

    def get_last_directory(self) -> str:
        """从存储中获取上次选择的 L4D2 目录"""
        try:
            return self.storage_service.get_l4d2_directory() or ""
        except Exception as e:
            logger.error(f"获取上次目录出错: {e}")
            return ""

    def open_external_url(self, url: str) -> None:
        """在系统默认浏览器中打开外部链接。"""
        try:
            logger.info(f"正在打开外部链接: {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"打开外部链接出错: {e}")

    def browse_directory(self) -> "str | None":
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

    def open_directory(self, path: str) -> bool:
        """在系统文件管理器中打开指定目录。"""
        try:
            if not path or not os.path.exists(path):
                logger.error(f"无法打开不存在的目录: {path}")
                return False

            # 确保是目录，如果是文件则打开其父目录
            dir_path = path if os.path.isdir(path) else os.path.dirname(path)

            logger.info(f"正在打开文件夹: {dir_path}")
            if sys.platform == 'win32':
                os.startfile(dir_path)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.run(['open', dir_path])
            else:
                import subprocess
                subprocess.run(['xdg-open', dir_path])
            return True
        except Exception as e:
            logger.error(f"打开文件夹出错: {e}")
            return False

    def reset_app_data(self) -> bool:
        """重置应用数据，仅保留 preferences.json，删除其他所有内容并退出。"""
        try:
            logger.info("正在重置应用数据...")

            # 定义 STORAGE_BASE_DIR（与类外部定义的保持一致）
            storage_dir = Path.home() / 'Documents' / 'L4D2-VPK-Manager'

            if not storage_dir.exists():
                return True

            # 遍历存储目录
            for item in storage_dir.iterdir():
                try:
                    # 如果不是 preferences.json，则删除
                    if item.name != 'preferences.json':
                        if item.is_file():
                            # 关闭日志文件句柄以免无法删除日志
                            if item.name == 'vpk_manager.log':
                                for handler in logging.root.handlers[:]:
                                    handler.close()
                                    logging.root.removeHandler(handler)
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                except Exception as e:
                    logger.error(f"删除条目 {item} 失败: {e}")

            logger.info("数据清理完成，准备退出程序。")

            # 手动触发关闭窗口
            if self._window:
                self._window.destroy()

            # 强制退出
            os._exit(0)
        except Exception as e:
            # 此处可能因为日志句柄已关而无法记录
            logger.error(f"重置应用数据出错: {e}")
            return False

    def get_downloads_directory(self) -> str:
        """获取用户下载目录。

        返回:
            下载目录的路径
        """
        try:
            downloads_dir = str(Path.home() / "Downloads")
            if os.path.exists(downloads_dir):
                return downloads_dir

            # 如果下载目录不存在则返回家目录
            return str(Path.home())
        except Exception as e:
            logger.warning(f"获取下载目录出错: {e}")
            return "."
