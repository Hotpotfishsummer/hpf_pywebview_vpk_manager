"""VPK 元数据提取和缓存服务"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
import vpk
import base64

logger = logging.getLogger(__name__)


class VpkMetadataService:
    """VPK 元数据提取和缓存的服务类"""

    def __init__(self, config_dir: str = None):
        """用配置目录初始化元数据服务"""
        if config_dir is None:
            # 统一存储在文稿目录下的应用文件夹中
            config_dir = str(Path.home() / 'Documents' / 'L4D2-VPK-Manager' / '.vpk_config')
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # 清理上次写入中断遗留的临时文件
        for stale in self.config_dir.glob("*.json.tmp"):
            try:
                stale.unlink()
            except OSError:
                pass

    def get_json_path(self, vpk_file_path: str) -> Path:
        """获取 VPK 文件的 JSON 文件路径"""
        vpk_name = Path(vpk_file_path).stem  # 获取没有扩展名的文件名
        return self.config_dir / f"{vpk_name}.json"

    def load_metadata(self, vpk_file_path: str) -> Optional[Dict[str, Any]]:
        """如果存在，从 JSON 文件加载元数据"""
        json_path = self.get_json_path(vpk_file_path)
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.info(f"load_metadata: 加载 JSON {json_path} 失败: {e}")
        return None

    def save_metadata(self, vpk_file_path: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """将元数据保存到 JSON 文件（先写临时文件再原子替换，避免中断损坏缓存）"""
        json_path = self.get_json_path(vpk_file_path)
        tmp_path = json_path.with_suffix('.json.tmp')
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(metadata or {}, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, json_path)
            logger.info(f"save_metadata: 已保存元数据到 {json_path}")
            return True
        except Exception as e:
            logger.info(f"save_metadata: 保存 JSON {json_path} 失败: {e}")
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    def extract_addontitle(self, vpk_file_path: str) -> Optional[str]:
        """从 VPK 文件提取 addontitle"""
        try:
            # 尝试打开 VPK 文件
            vpk_file = vpk.VPK(vpk_file_path)

            # 在 VPK 中查找 addoninfo.txt
            if 'addoninfo.txt' in vpk_file:
                # 尝试多种编码以处理各种字符集
                addoninfo_data = None
                # 增加编解码的容错性，首先读取字节流
                try:
                    raw_data = vpk_file['addoninfo.txt'].read()
                except Exception as e:
                    logger.info(f"extract_addontitle: 读取 addoninfo.txt 字节流失败: {e}")
                    return None

                for encoding in ['utf-8', 'gbk', 'utf-16', 'big5', 'latin-1']:
                    try:
                        addoninfo_data = raw_data.decode(encoding)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue

                # 如果所有编码都失败，使用 utf-8 并替换错误字符（万能兜底）
                if addoninfo_data is None:
                    try:
                        addoninfo_data = raw_data.decode('utf-8', errors='replace')
                    except Exception:
                        addoninfo_data = ""

                addontitle = self._parse_addontitle(addoninfo_data)
                return addontitle
            else:
                logger.info(f"extract_addontitle: {vpk_file_path} 中未找到 addoninfo.txt")
                return None
        except Exception as e:
            logger.info(f"extract_addontitle: 从 {vpk_file_path} 提取失败: {e}")
            return None

    def _parse_addontitle(self, addoninfo_content: str) -> Optional[str]:
        """从 addoninfo.txt 内容解析 addontitle"""
        try:
            for line in addoninfo_content.split('\n'):
                line = line.strip()
                if line.lower().startswith('"addontitle"') or line.lower().startswith('addontitle'):
                    # 提取引号之间的值
                    # 格式: addontitle "value" 或 "addontitle" "value"
                    parts = line.split('"')
                    # 如果格式是 addontitle "value"，parts[1] 就是 value
                    # 如果格式是 "addontitle" "value"，parts[3] 就是 value
                    if len(parts) >= 4:
                        return parts[3]
                    elif len(parts) >= 2:
                        return parts[1]
            return None
        except Exception as e:
            logger.info(f"_parse_addontitle: 解析 addoninfo 内容失败: {e}")
            return None

    def get_or_extract_metadata(self, vpk_file_path: str) -> Optional[Dict[str, Any]]:
        """从缓存或从 VPK 获取元数据(缓存带 mtime/size 失效校验)"""
        path = Path(vpk_file_path)
        cached_metadata = self.load_metadata(vpk_file_path)
        if cached_metadata is not None and self._cache_is_fresh(cached_metadata, path):
            logger.info(f"get_or_extract_metadata: 使用缓存的元数据 {vpk_file_path}")
            return cached_metadata or None

        # 缓存缺失或已失效，从 VPK 提取
        logger.info(f"get_or_extract_metadata: 从 {vpk_file_path} 提取元数据")
        addontitle = self.extract_addontitle(vpk_file_path)

        # 创建元数据字典（即使在错误情况下也为空）
        metadata: Dict[str, Any] = {'addontitle': addontitle} if addontitle else {}

        # 记录源文件的 mtime/size，供下次缓存失效校验
        try:
            stat = path.stat()
            metadata['source_mtime'] = stat.st_mtime
            metadata['source_size'] = stat.st_size
        except OSError:
            pass

        # 保存到缓存
        self.save_metadata(vpk_file_path, metadata)

        return metadata if metadata else None

    @staticmethod
    def _cache_is_fresh(cached_metadata: Dict[str, Any], path: Path) -> bool:
        """判断缓存是否仍与源文件一致。

        文件已不存在时无法对比，沿用缓存（对齐旧行为）；
        缓存缺少 mtime/size（旧格式）视为失效，触发一次重提取。
        """
        try:
            stat = path.stat()
        except OSError:
            return True
        if 'source_mtime' not in cached_metadata or 'source_size' not in cached_metadata:
            return False
        return (
            cached_metadata['source_mtime'] == stat.st_mtime
            and cached_metadata['source_size'] == stat.st_size
        )

    def get_addontitle(self, vpk_file_path: str) -> Optional[str]:
        """获取 VPK 文件的 addontitle（从缓存或提取）"""
        metadata = self.get_or_extract_metadata(vpk_file_path)
        if metadata and 'addontitle' in metadata:
            return metadata['addontitle']
        return None

    def get_vpk_metadata(self, vpk_file_path: str) -> Optional['VpkFile']:
        """获取完整的 VPK 文件元数据作为 VpkFile 对象"""
        from ..models import VpkFile
        import os

        try:
            path = Path(vpk_file_path)
            stat = path.stat()

            # 判断文件是否被禁用
            is_disabled = vpk_file_path.endswith('.disabled')

            # 获取 addontitle
            addontitle = self.get_addontitle(vpk_file_path)

            # 查找同名的缩略图 (jpg 或 png)
            thumbnail_url = None
            parent_dir = path.parent
            base_name = path.stem
            
            # 优先尝试 jpg，因为 L4D2 插件图片多为 jpg
            for ext in ['.jpg', '.png', '.jpeg']:
                thumb_path = parent_dir / f"{base_name}{ext}"
                if thumb_path.exists():
                    try:
                        # 对于 PyWebView，将图片转换为 base64 是最稳定的显示方式
                        with open(thumb_path, "rb") as img_file:
                            img_data = img_file.read()
                            encoded_string = base64.b64encode(img_data).decode('utf-8')
                            mime_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"
                            thumbnail_url = f"data:{mime_type};base64,{encoded_string}"
                        break
                    except Exception as e:
                        logger.info(f"读取图片失败 {thumb_path}: {e}")

            return VpkFile(
                name=path.name,
                path=vpk_file_path,
                size=stat.st_size,
                modified_time=stat.st_mtime,
                is_valid=True,
                is_disabled=is_disabled,
                addontitle=addontitle,
                thumbnail_path=thumbnail_url,  # 存储 base64 数据
            )
        except Exception as e:
            logger.info(f"get_vpk_metadata: 获取 {vpk_file_path} 的元数据失败: {e}")
            return None
