"""pytest 共享配置:确保项目根在 sys.path 中,使 `backend` 可导入。

测试纪律(全项目约定):
- 所有测试通过 tmp_path / monkeypatch 隔离,不触碰用户真实数据
  (preferences.json 位于 Documents/L4D2-VPK-Manager);
- 不实例化 VpkManagerApi(__init__ 有真实副作用),只测服务层与纯函数;
- 构造真实 VPK 用 vpk.NewVPK(参考 test_localize_service 的 _make_vpk)。
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
