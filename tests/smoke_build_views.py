"""开发期冒烟测试：在真实 ft.Page 上构建各页面视图，捕获运行时构造错误。

覆盖：
  - App 初始化 + 首页
  - 扫码页 / 库存页 / 流水页
  - 出入库登记弹窗（入库、出库两种）
  - xlsx 备份字节生成

不启动 Flet 会话（把 update/add/show_dialog/run_task 打桩），仅验证控件树能否顺利构建。
用法：python tests/smoke_build_views.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import flet as ft  # noqa: E402

from app import db  # noqa: E402
from app.pages.export_xlsx import _build_xlsx_bytes, build_export_button  # noqa: E402
from app.pages.operation import open_operation  # noqa: E402
from main import App  # noqa: E402

db.init_db()

# 造一点测试数据，保证导出时有内容
try:
    db.record_operation("SMOKE-001", "冒烟测试物料", "IN", 100, "tester", "A区", "",
                        safety_stock=20)
    db.record_operation("SMOKE-001", "冒烟测试物料", "OUT", 30, "tester", "A区", "")
except Exception:
    pass


class _DummySession:
    """Page 需要一个可被弱引用的会话对象，这里只需占位。"""


page = ft.Page(sess=_DummySession())
page.update = lambda *a, **k: None
page.add = lambda *a, **k: None
page.show_dialog = lambda *a, **k: None
page.run_task = lambda *a, **k: None

failed = 0


def check(label, fn):
    global failed
    try:
        fn()
        print("[OK] " + label)
    except Exception as e:
        failed += 1
        print("[FAIL] {} -> {}: {}".format(label, type(e).__name__, e))


app = App(page)
print("[OK] App 初始化 + 首页构建")

for idx, name in ((1, "扫码页"), (2, "库存页"), (3, "流水页")):
    check("{} 构建".format(name), lambda i=idx: app.select(i))

check("入库登记弹窗构建", lambda: open_operation(app, code="SMOKE-001", default_type="IN"))
check("出库登记弹窗构建", lambda: open_operation(app, code="SMOKE-001", default_type="OUT"))
check("导出按钮构建", lambda: build_export_button(app))


def _export_bytes():
    data = _build_xlsx_bytes()
    assert data and len(data) > 1000, "xlsx 内容过小：{}".format(len(data))
    print("      (xlsx 大小 {} 字节)".format(len(data)))


check("xlsx 备份字节生成", _export_bytes)

print("")
print("冒烟测试：" + ("发现 {} 处失败".format(failed) if failed else "全部通过"))
sys.exit(1 if failed else 0)
