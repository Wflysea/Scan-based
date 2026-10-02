"""数据层单元测试：无需相机/安卓，可在 PyCharm 中直接 Run/Debug。

运行方式（PyCharm）：
  - 右键本文件 → Run 'pytest for test_db.py'  （需 Settings → Tools →
    Python Integrated Tools → Testing → Default test runner = pytest）
  - 或在 Terminal 执行：pytest tests/test_db.py -v

测试使用一个临时 SQLite 文件，不会污染项目里的 app/inventory.db。
"""
import os
import tempfile

import app.db as db


def setup_module(module):
    # 用临时库覆盖模块内的 DB_PATH，避免改动真实数据库
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db.DB_PATH = tmp.name


def teardown_module(module):
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)


def test_init_and_first_inbound():
    db.init_db()
    new_qty, sf, name = db.record_operation(
        "P001", "螺丝", "IN", 100, "张三", "A区", "", safety_stock=20
    )
    assert new_qty == 100
    assert sf == 20
    assert name == "螺丝"
    assert db.get_product("P001")["quantity"] == 100


def test_outbound_reduces_stock():
    db.record_operation("P001", "螺丝", "OUT", 30, "李四", "A区", "领用")
    assert db.get_product("P001")["quantity"] == 70


def test_low_stock_warning():
    # 再出库 65 → 库存 5，低于安全库存 20
    db.record_operation("P001", "螺丝", "OUT", 65, "王五", "A区", "")
    assert db.get_product("P001")["quantity"] == 5
    lows = db.low_stock()
    assert any(p["code"] == "P001" for p in lows)


def test_transaction_filters():
    txs_by_code = db.list_transactions(code="P001")
    assert len(txs_by_code) == 3

    from datetime import date
    txs_range = db.list_transactions(
        start=date(2000, 1, 1), end=date(2100, 1, 1)
    )
    assert len(txs_range) == 3

    txs_in = db.list_transactions(op_type="IN")
    assert len(txs_in) == 1


def test_stats_counts():
    s = db.get_stats()
    assert s["total_sku"] == 1
    assert s["total_qty"] == 5
    assert s["today_in"] == 100
    assert s["today_out"] == 95
    assert s["low"]  # 存在低库存项
