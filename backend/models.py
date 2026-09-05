"""L4D2 VPK 管理器的数据模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VpkFile:
    """代表 VPK 文件的模型"""

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
