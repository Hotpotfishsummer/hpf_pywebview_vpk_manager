"""requirements.txt 与 environment.yml 的依赖一致性守卫测试。

environment.yml 的 pip 段是项目环境的完整事实来源;
requirements.txt 用于 CI(ubuntu)安装,两者必须声明相同的包集合。
不引入 PyYAML,按该文件的固定缩进结构做轻量解析。
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _parse_requirements_txt() -> dict:
    """解析 requirements.txt,返回 {规范化包名: 版本约束}"""
    deps = {}
    for line in (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z0-9._-]+)\s*(.*)$", line)
        deps[m.group(1).lower().replace("_", "-")] = m.group(2).strip()
    return deps


def _parse_environment_yml_pip_section() -> dict:
    """解析 environment.yml 的 pip: 段,返回 {规范化包名: 版本约束}"""
    deps = {}
    lines = (PROJECT_ROOT / "environment.yml").read_text(encoding="utf-8").splitlines()
    in_pip = False
    for line in lines:
        stripped = line.strip()
        if stripped == "- pip:":
            in_pip = True
            continue
        if in_pip:
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                m = re.match(r"^([A-Za-z0-9._-]+)\s*(.*)$", item)
                deps[m.group(1).lower().replace("_", "-")] = m.group(2).strip()
            elif stripped and not stripped.startswith("#"):
                # pip 段结束(回到顶层键)
                in_pip = False
    return deps


def test_requirements_txt_matches_environment_yml():
    req = _parse_requirements_txt()
    env = _parse_environment_yml_pip_section()
    assert req, "requirements.txt 不应为空"
    assert env, "environment.yml 的 pip 段不应为空"

    missing_in_req = sorted(set(env) - set(req))
    missing_in_env = sorted(set(req) - set(env))
    assert not missing_in_req, f"requirements.txt 缺少: {missing_in_req}"
    assert not missing_in_env, f"environment.yml pip 段缺少: {missing_in_env}"

    # 同名包版本约束也必须一致,避免两边环境漂移
    drifted = {k: (req[k], env[k]) for k in req if req[k] != env[k]}
    assert not drifted, f"版本约束不一致(requirements, environment): {drifted}"


def test_key_runtime_packages_present():
    req = _parse_requirements_txt()
    for pkg in ["pywebview", "vpk", "zstandard", "py7zr", "paramiko", "pytest"]:
        assert pkg in req, f"关键依赖 {pkg} 应在 requirements.txt 中声明"
