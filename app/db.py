"""本地持久化层：使用 SQLite，数据库文件随应用打包，无需后端。

注意：数据库文件位于本模块同目录，在安卓 APK 中即应用私有数据目录，
可随应用持久化保存，卸载时一并清除（如需备份可导出 CSV，此处未实现）。
"""
import os
import sqlite3
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS products (
            code         TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            quantity     INTEGER NOT NULL DEFAULT 0,
            safety_stock INTEGER NOT NULL DEFAULT 0,
            unit         TEXT DEFAULT '个',
            location     TEXT DEFAULT '',
            updated_at   TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS transactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            code       TEXT NOT NULL,
            name       TEXT NOT NULL,
            op_type    TEXT NOT NULL,          -- 'IN' 入库 / 'OUT' 出库
            quantity   INTEGER NOT NULL,
            operator   TEXT,
            location   TEXT,
            note       TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_tx_code ON transactions(code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tx_time ON transactions(created_at)")
    conn.commit()
    conn.close()


# ---------------- 商品 / 库存 ----------------

def get_product(code: str):
    conn = get_conn()
    c = conn.cursor()
    r = c.execute("SELECT * FROM products WHERE code=?", (code,)).fetchone()
    conn.close()
    return dict(r) if r else None


def list_products(search: str = None):
    conn = get_conn()
    c = conn.cursor()
    if search:
        like = f"%{search}%"
        rows = c.execute(
            "SELECT * FROM products WHERE name LIKE ? OR code LIKE ? ORDER BY name",
            (like, like),
        ).fetchall()
    else:
        rows = c.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def low_stock():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute(
        "SELECT * FROM products WHERE quantity < safety_stock ORDER BY quantity ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- 出入库流水 ----------------

def list_transactions(code=None, start=None, end=None, op_type=None, limit=500):
    """按编码 / 时间范围 / 类型筛选流水。

    start/end 为 datetime.date；created_at 以 ISO 字符串存储，可直接按字典序比较。
    """
    conn = get_conn()
    c = conn.cursor()
    sql = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if code:
        sql += " AND code LIKE ?"
        params.append(f"%{code}%")
    if op_type:
        sql += " AND op_type=?"
        params.append(op_type)
    if start:
        sql += " AND created_at >= ?"
        params.append(start.isoformat())
    if end:
        sql += " AND created_at <= ?"
        params.append(end.isoformat() + "T23:59:59")
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = c.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def record_operation(code, name, op_type, quantity, operator, location, note,
                     safety_stock=None, unit="个"):
    """记录一次出入库：写入流水并自动调整库存数量。

    返回 (new_qty, safety_stock, name)，供调用方判断是否需要低库存预警。
    """
    delta = quantity if op_type == "IN" else -quantity
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    r = c.execute("SELECT * FROM products WHERE code=?", (code,)).fetchone()
    if r is None:
        c.execute(
            "INSERT INTO products(code,name,quantity,safety_stock,unit,location,updated_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (code, name, delta, safety_stock or 0, unit, location or "", now),
        )
        new_qty = delta
        sf = safety_stock or 0
    else:
        new_qty = r["quantity"] + delta
        c.execute(
            "UPDATE products SET quantity=?, name=?, updated_at=? WHERE code=?",
            (new_qty, name, now, code),
        )
        sf = r["safety_stock"]
    c.execute(
        "INSERT INTO transactions(code,name,op_type,quantity,operator,location,note,created_at) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (code, name, op_type, quantity, operator, location, note, now),
    )
    conn.commit()
    conn.close()
    return new_qty, sf, name


# ---------------- 统计 ----------------

def get_stats():
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    total_sku = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_qty = c.execute("SELECT COALESCE(SUM(quantity),0) FROM products").fetchone()[0]
    today_in = c.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM transactions WHERE op_type='IN' AND created_at LIKE ?",
        (today + "%",),
    ).fetchone()[0]
    today_out = c.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM transactions WHERE op_type='OUT' AND created_at LIKE ?",
        (today + "%",),
    ).fetchone()[0]
    low = low_stock()
    conn.close()
    return dict(
        total_sku=total_sku,
        total_qty=total_qty,
        today_in=today_in,
        today_out=today_out,
        low=low,
    )


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成：", DB_PATH)
