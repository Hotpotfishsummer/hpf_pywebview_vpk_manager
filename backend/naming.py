"""共享的 VPK 命名/清洗逻辑

"addontitle 清洗 + 工坊 ID 追加"原本在上传、本地化、导出三处各写一份,
统一收敛到本模块,保证命名行为一致。
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

# Windows 文件名非法字符 + 控制字符
_ILLEGAL_CHARS_PATTERN = r'[<>:"/\\|?*\x00-\x1f]'
# 文件名中 8 位以上的连续数字视为 Steam 创意工坊 ID
_WORKSHOP_ID_PATTERN = r'(\d{8,})'
# 清洗后基名上限:Windows 默认路径上限 260,留出目录层级与扩展名余量
_MAX_BASE_NAME_LEN = 120
# VPK 关联的图片文件扩展名
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.tga', '.bmp', '.gif')


def extract_workshop_id(filename: str) -> str:
    """从文件名中提取 8 位以上的数字 ID(创意工坊文件命名约定),无则返回空串"""
    match = re.search(_WORKSHOP_ID_PATTERN, filename)
    return match.group(1) if match else ""


def vpk_stem_for_association(filename: str) -> str:
    """计算与 VPK 关联图片/文档使用的基名。

    约定与缩略图扫描一致:x.vpk → x;x.vpk.disabled → x.vpk
    (即先剥 .disabled 再取 splitext,禁用文件的图片名为 x.vpk.jpg)。
    """
    name = filename
    if name.lower().endswith('.disabled'):
        # mod.vpk.disabled → mod.vpk(图片为 x.vpk.jpg,与缩略图扫描一致)
        return name[: -len('.disabled')]
    return os.path.splitext(name)[0]


def sanitize_addon_title(title: str) -> str:
    """把 addontitle 清洗为安全的文件名:空格转下划线、非法字符替换、合并连续下划线

    另去除尾部点号——Windows 文件名不允许以点结尾(创建时会失败或被静默改动)。
    """
    custom_title = title.replace(" ", "_").strip()
    base_name = re.sub(_ILLEGAL_CHARS_PATTERN, '_', custom_title)
    return re.sub(r'_{2,}', '_', base_name).rstrip('.')


def build_export_base_name(addontitle: Optional[str], filename: str, fallback_stem: str) -> str:
    """根据 addontitle 生成上传/本地化/导出共用的基础文件名。

    无标题或清洗后为空(纯非法字符)时回退到原文件 stem;若原文件名
    带有工坊 ID 且清洗后的名称尚不包含它,则把 ID 追加到末尾。
    """
    if not addontitle:
        return fallback_stem

    base_name = sanitize_addon_title(addontitle)[:_MAX_BASE_NAME_LEN]
    if not base_name.strip('_'):
        base_name = fallback_stem

    workshop_id = extract_workshop_id(filename)
    if workshop_id and workshop_id not in base_name:
        base_name = f"{base_name}-{workshop_id}"
    return base_name


def find_associated_images(
    directory: str,
    vpk_filename: str,
    exts: Tuple[str, ...] = IMAGE_EXTS,
    strip_vpk_suffix: bool = False,
) -> List[Tuple[str, str]]:
    """在目录中扫描与 VPK 同名(大小写不敏感)的关联图片文件。

    用于 Windows 大小写不敏感文件系统下的重复匹配问题;每种扩展名
    只返回第一个匹配。strip_vpk_suffix 用于上传场景:对 x.vpk.disabled
    匹配 x.jpg 而不是 x.vpk.jpg(与导出/本地化的既有约定不同,保持原行为)。
    返回 [(文件完整路径, 小写扩展名)] 列表。
    """
    stem = Path(vpk_filename).stem.lower()
    if strip_vpk_suffix and stem.endswith('.vpk'):
        stem = stem[:-4]
    exts_lower = {e.lower() for e in exts}

    results: List[Tuple[str, str]] = []
    seen_exts = set()
    try:
        entries = os.listdir(directory)
    except OSError:
        # 目录不可读时视为无关联文件(与原实现一致)
        return results

    for name in entries:
        f_path = os.path.join(directory, name)
        if not os.path.isfile(f_path):
            continue
        f_ext = Path(name).suffix.lower()
        f_stem = Path(name).stem.lower()
        if f_stem == stem and f_ext in exts_lower and f_ext not in seen_exts:
            results.append((f_path, f_ext))
            seen_exts.add(f_ext)
    return results
