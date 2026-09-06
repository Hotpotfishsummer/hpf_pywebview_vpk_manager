"""L4D2 VPK 管理器的数据模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VpkFile:
    """代表 VPK 文件的模型

    字段说明:
        name: 文件名(含 .vpk / .vpk.disabled 后缀)
        path: 完整路径
        size: 字节数
        modified_time: mtime(Unix 秒)
        is_valid: 文件可读且为合法 VPK
        is_disabled: 禁用态(文件名以 .disabled 结尾)
        thumbnail_path: 缩略图 base64 data URL(jpg/png),无则 None
        addontitle: 从 addoninfo.txt 提取的标题,提取失败为 None
    """

    name: str
    path: str
    size: int
    modified_time: float
    is_valid: bool
    is_disabled: bool = False
    thumbnail_path: Optional[str] = None
    addontitle: Optional[str] = None

    @property
    def display_name(self) -> str:
        """返回显示名称（标题或文件名）"""
        return self.addontitle or self.name
