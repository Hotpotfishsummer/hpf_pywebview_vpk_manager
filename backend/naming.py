"""共享的 VPK 命名/清洗逻辑

"addontitle 清洗 + 工坊 ID 追加"原本在上传、本地化、导出三处各写一份,
统一收敛到本模块,保证命名行为一致。
"""

import re
from typing import Optional

# Windows 文件名非法字符 + 控制字符
_ILLEGAL_CHARS_PATTERN = r'[<>:"/\\|?*\x00-\x1f]'
# 文件名中 8 位以上的连续数字视为 Steam 创意工坊 ID
_WORKSHOP_ID_PATTERN = r'(\d{8,})'


def extract_workshop_id(filename: str) -> str:
    """从文件名中提取 8 位以上的数字 ID(创意工坊文件命名约定),无则返回空串"""
    match = re.search(_WORKSHOP_ID_PATTERN, filename)
    return match.group(1) if match else ""


def sanitize_addon_title(title: str) -> str:
    """把 addontitle 清洗为安全的文件名:空格转下划线、非法字符替换、合并连续下划线"""
    custom_title = title.replace(" ", "_").strip()
    base_name = re.sub(_ILLEGAL_CHARS_PATTERN, '_', custom_title)
    return re.sub(r'_{2,}', '_', base_name)


def build_export_base_name(addontitle: Optional[str], filename: str, fallback_stem: str) -> str:
    """根据 addontitle 生成上传/本地化/导出共用的基础文件名。

    无标题或清洗后为空(纯非法字符)时回退到原文件 stem;若原文件名
    带有工坊 ID 且清洗后的名称尚不包含它,则把 ID 追加到末尾。
    """
    if not addontitle:
        return fallback_stem

    base_name = sanitize_addon_title(addontitle)
    if not base_name.strip('_'):
        base_name = fallback_stem

    workshop_id = extract_workshop_id(filename)
    if workshop_id and workshop_id not in base_name:
        base_name = f"{base_name}-{workshop_id}"
    return base_name
