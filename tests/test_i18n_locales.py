"""前端 i18n locale 文件的键一致性守卫

en/zh 键集合必须完全一致,避免切换语言时出现缺键回落。
"""

import json
from pathlib import Path

FRONTEND_I18N = Path(__file__).resolve().parent.parent / "frontend" / "src" / "i18n" / "locales"


def _load(name: str) -> dict:
    with open(FRONTEND_I18N / name, encoding="utf-8") as f:
        return json.load(f)


def test_en_zh_key_sets_match():
    en = set(_load("en.json"))
    zh = set(_load("zh.json"))
    assert en - zh == set(), f"en 独有键: {sorted(en - zh)}"
    assert zh - en == set(), f"zh 独有键: {sorted(zh - en)}"


def test_notification_keys_present_in_both():
    required = {
        "needDirectoryFirst", "importSuccessPacks", "importFailed", "importError",
        "localizePartial", "localizePartialFailed", "localizeFailed", "localizeError",
        "scanFailed", "remoteScanFailed", "remoteScanError", "remoteDeleted",
        "remoteDeleteFailed", "remoteDeleteError", "remoteDeletedSelected",
        "remoteDeletePartial", "deleteActionFailed", "deleteActionError",
        "remoteDisabled", "remoteDisableError", "remoteEnabled", "remoteEnableError",
        "downloadingRemote", "downloadSuccess", "downloadFailed", "downloadError",
        "uploadingLocal", "uploadSuccess", "uploadFailed", "uploadError",
        "exportDone", "exportErrorMsg", "deletePartialFailed", "statusUpdated",
        "confirmHardDelete",
    }
    for name in ("en.json", "zh.json"):
        keys = set(_load(name))
        missing = required - keys
        assert not missing, f"{name} 缺键: {sorted(missing)}"


def test_no_untranslated_placeholder_mismatch():
    """同键名的插值占位符在 en/zh 中应一致(防止漏译参数)。"""
    import re
    en, zh = _load("en.json"), _load("zh.json")
    for key in en.keys() & zh.keys():
        en_ph = set(re.findall(r"\{(\w+)\}", str(en[key])))
        zh_ph = set(re.findall(r"\{(\w+)\}", str(zh[key])))
        assert en_ph == zh_ph, f"键 {key} 的占位符不一致: en={en_ph} zh={zh_ph}"
