"""L4D2 VPK 管理器 - PyWebView 主入口"""

import sys
import logging
import os
from pathlib import Path

# Configure logging FIRST before any other imports
STORAGE_BASE_DIR = Path.home() / 'Documents' / 'L4D2-VPK-Manager'
STORAGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
log_file = STORAGE_BASE_DIR / 'vpk_manager.log'

# 安全地初始化日志处理器，避免在 GUI 模式下（sys.stdout 为 None）崩溃
handlers = [logging.FileHandler(log_file, encoding='utf-8')]
if sys.stdout is not None:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

# 为 Windows 控制台设置 UTF-8 编码
if sys.platform == 'win32' and sys.stdout is not None:
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("启动 L4D2 VPK 管理器")
logger.info(f"Python 版本: {sys.version}")
logger.info(f"工作目录: {os.getcwd()}")
logger.info(f"日志文件: {os.path.abspath(log_file)}")
logger.info("=" * 80)

# 解决 debugpy + pywebview 兼容性问题
logger.info("初始化线程...")
try:
    if hasattr(sys, '_getframe'):
        import threading
        # 预初始化线程以避免与 debugpy 的递归问题
        current = threading.current_thread()
        logger.info(f"当前线程: {current.name}")
except Exception as e:
    logger.error(f"初始化线程出错: {e}", exc_info=True)

# 添加后端到 Python 路径
logger.info("添加后端到 Python 路径...")
sys.path.insert(0, str(Path(__file__).parent))
logger.info(f"Python 路径: {sys.path[:3]}")

logger.info("导入 VpkManagerApi...")
try:
    from backend.api import VpkManagerApi
    logger.info("VpkManagerApi 导入成功")
except Exception as e:
    logger.error(f"导入 VpkManagerApi 失败: {e}", exc_info=True)
    raise


def main():
    """应用程序主入口点"""
    logger.info("调用 main() 函数")
    
    try:
        import webview
        logger.info(f"PyWebView 导入成功, 版本: {webview.__version__ if hasattr(webview, '__version__') else '未知'}")
    except Exception as e:
        logger.error(f"导入 PyWebView 失败: {e}", exc_info=True)
        raise

    logger.info("创建 API 实例...")
    try:
        api = VpkManagerApi()
        logger.info("API 实例创建成功")
        
        # 检查是否为开发模式
        is_dev = os.environ.get('PYWEBVIEW_DEV') == 'true'
        
        if is_dev:
            url = 'http://localhost:5173'
            logger.info("检测到开发模式，将加载 Vite 开发服务器")
        else:
            # 生产模式
            # Nuitka onefile 下资源会被解压到 __file__ 所在的临时目录中
            # 兼容 Nuitka (使用 __file__) 和 PyInstaller (使用 sys._MEIPASS)
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            url = os.path.join(base_path, 'frontend', 'dist', 'index.html')
            
            logger.info(f"正在定位前端资源: {url}")
            if not os.path.exists(url):
                logger.error(f"严重错误: 找不到前端资源! 路径: {url}")
                # 尝试回退到相对于 EXE 的路径
                exe_dir = os.path.dirname(sys.executable)
                exe_url = os.path.join(exe_dir, 'frontend', 'dist', 'index.html')
                if os.path.exists(exe_url):
                    url = exe_url
                    logger.info(f"在可执行文件同级找到资源: {url}")
                else:
                    # 最后一个尝试：相对路径
                    url = 'frontend/dist/index.html'
                    logger.warning("所有绝对路径均失败，回退到相对路径")

    except Exception as e:
        logger.error(f"创建 API 实例失败: {e}", exc_info=True)
        raise

    logger.info("创建 WebView 窗口...")
    try:
        window = webview.create_window(
            title='L4D2 VPK 管理器',
            url=url,
            width=1200,
            height=800,
            resizable=True,
            js_api=api,
        )
        # 设置窗口引用到 API 实例
        api.set_window(window)
        
        logger.info("WebView 窗口创建成功")
        logger.info(f"窗口标题: {window.title}")
        logger.info(f"加载 URL: {url}")
    except Exception as e:
        logger.error(f"创建 WebView 窗口失败: {e}", exc_info=True)
        raise

    logger.info("启动 WebView...")
    try:
        # 在开发模式下启用调试工具 (F12)
        is_dev = os.environ.get('PYWEBVIEW_DEV') == 'true'
        
        logger.info(f"PyWebView 已启动，调试模式: {is_dev}")
        logger.info("前端日志现在会同步输出到本控制台")
        logger.info("=" * 80)
        
        # 让 pywebview 使用默认随机端口，避免 Windows 上固定端口被保留或拒绝绑定
        webview.start(debug=is_dev)
        
        logger.info("=" * 80)
        logger.info("WebView 已停止")
    except Exception as e:
        logger.error(f"运行 WebView 出错: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"致命错误: {e}", exc_info=True)
        sys.exit(1)
    logger.info("应用程序正常退出")
