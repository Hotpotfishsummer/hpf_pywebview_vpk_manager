"""Configuration service for handling autoexec.cfg and other game settings."""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class ConfigService:
    """Service to manage L4D2 configuration files."""

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize ConfigService.
        
        Args:
            base_path: The root path of the application where assets are located.
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Fallback for development
            self.base_path = Path(__file__).parent.parent.parent

    def apply_autoexec_template(self, l4d2_directory: str) -> bool:
        """
        Finds the cfg directory, backups autoexec.cfg and overwrites it with the template.
        
        Args:
            l4d2_directory: L4D2 root directory (containing 'left4dead2' folder)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not l4d2_directory or not os.path.isdir(l4d2_directory):
            logger.warning(f"L4D2 目录无效: {l4d2_directory}")
            return False

        # Path to cfg directory: l4d2_root/left4dead2/cfg
        # Also check for direct sibling of addons if l4d2_directory is already left4dead2
        if os.path.basename(l4d2_directory).lower() == "left4dead2":
            cfg_dir = os.path.join(l4d2_directory, "cfg")
        else:
            cfg_dir = os.path.join(l4d2_directory, "left4dead2", "cfg")

        if not os.path.isdir(cfg_dir):
            logger.warning(f"cfg 目录不存在: {cfg_dir}")
            return False

        autoexec_path = os.path.join(cfg_dir, "autoexec.cfg")
        bak_path = autoexec_path + ".bak"

        # Find the template file
        template_path = self.base_path / "assets" / "autoexec.cfg.example"

        if not template_path.exists():
            logger.error(f"资源文件不存在: {template_path}")
            return False

        try:
            # 读取模板内容以进行对比
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # 1. If autoexec.cfg exists, check if needs update
            if os.path.exists(autoexec_path):
                try:
                    with open(autoexec_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    
                    if current_content == template_content:
                        logger.info("autoexec.cfg 内容已是最新，无需更新")
                        return True
                except Exception as e:
                    logger.warning(f"读取现有 autoexec.cfg 失败 (可能是编码问题)，将强制备份并覆盖: {e}")
                
                logger.info(f"正在备份 {autoexec_path} 到 {bak_path}")
                shutil.copy2(autoexec_path, bak_path)
            
            # 2. Overwrite autoexec.cfg with template
            logger.info(f"正在应用 autoexec 模板: {template_path} -> {autoexec_path}")
            shutil.copy2(template_path, autoexec_path)
            return True
        except Exception as e:
            logger.error(f"应用 autoexec 模板出错: {e}")
            return False
