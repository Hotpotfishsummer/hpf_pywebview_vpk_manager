"""未使用 i18n 键守卫测试。

扫描 frontend/src 全部源码,把"键名以字符串字面量形式出现"视为已使用
(保守策略:宁可漏报,不误报)。新增翻译键后忘记使用、或删除功能后
残留的死键会被本测试暴露。
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "frontend" / "src"
LOCALES_DIR = SRC_DIR / "i18n" / "locales"


def _load_locale_keys(name: str) -> set:
    data = json.loads((LOCALES_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return set(data.keys())


def _collect_source_text() -> str:
    chunks = []
    for pattern in ("*.vue", "*.ts"):
        for f in SRC_DIR.rglob(pattern):
            chunks.append(f.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _used_keys(source: str, keys: set) -> set:
    used = set()
    for key in keys:
        # 键名作为单引号/双引号/反引号字符串字面量出现在源码中即视为使用
        if re.search(rf"""['"`]{re.escape(key)}['"`]""", source):
            used.add(key)
    return used


def test_no_unused_locale_keys():
    source = _collect_source_text()
    for locale in ("en", "zh"):
        keys = _load_locale_keys(locale)
        unused = keys - _used_keys(source, keys)
        assert unused == set(), f"{locale}.json 存在未使用的翻译键: {sorted(unused)}"


def test_key_count_stays_reasonable():
    # 防御性下限:若键数骤降说明误删了整批翻译
    for locale in ("en", "zh"):
        assert len(_load_locale_keys(locale)) >= 100
