"""出入库登记：以底部抽屉（BottomSheet）形式打开，可从扫码/库存/首页任意入口唤起。

记录字段：商品名称、编码、数量、操作类型(入库/出库)、操作人、仓库/库位、备注。
保存时自动增减库存，并在低于安全库存时给出预警。

Flet 1.0 适配：弹层用 page.show_dialog / page.pop_dialog（替代 0.86 的 page.open/close）。
"""
import flet as ft

from app import db
from app.config import *


def open_operation(app, code=None, default_type="IN"):
    page = app.page
    product = db.get_product(code) if code else None

    code_f = ft.TextField(
        label="编码（条码 / 二维码）", value=code or "",
        height=INPUT_HEIGHT, border_radius=10, disabled=bool(code),
    )
    name = ft.TextField(
        label="商品 / 物料名称", value=product["name"] if product else "",
        height=INPUT_HEIGHT, border_radius=10,
    )
    qty = ft.TextField(
        label="数量", value="1", keyboard_type=ft.KeyboardType.NUMBER,
        height=INPUT_HEIGHT, border_radius=10,
    )
    op_group = ft.RadioGroup(
        content=ft.Row([ft.Radio(label="入库", value="IN"),
                        ft.Radio(label="出库", value="OUT")]),
        value=default_type,
    )
    operator = ft.TextField(label="操作人", height=INPUT_HEIGHT, border_radius=10)
    location = ft.TextField(
        label="仓库 / 库位", value=product["location"] if product else "",
        height=INPUT_HEIGHT, border_radius=10,
    )
    note = ft.TextField(label="备注", height=INPUT_HEIGHT, border_radius=10)
    safety = ft.TextField(
        label="安全库存（仅首次登记生效）",
        value=str(product["safety_stock"]) if product else "0",
        keyboard_type=ft.KeyboardType.NUMBER, height=INPUT_HEIGHT, border_radius=10,
        disabled=bool(product),
    )

    def submit(e):
        t = op_group.value or default_type
        try:
            q = int(qty.value)
        except ValueError:
            app.snack("数量必须为整数")
            return
        if q <= 0:
            app.snack("数量必须大于 0")
            return
        c = code_f.value.strip()
        if not c:
            app.snack("编码不能为空")
            return
        n = name.value.strip() or c

        if t == "OUT":
            cur = db.get_product(c)
            if cur and cur["quantity"] < q:
                app.snack(f"库存不足：当前仅 {cur['quantity']} {cur['unit']}", OUT_COLOR)
                return

        try:
            sf_val = int(safety.value) if safety.value else 0
        except ValueError:
            sf_val = 0

        new_qty, sf, pname = db.record_operation(
            c, n, t, q, operator.value.strip(), location.value.strip(),
            note.value.strip(), safety_stock=None if product else sf_val, unit="个",
        )
        page.pop_dialog()
        app.refresh()
        msg = f"{'入库' if t == 'IN' else '出库'}成功：{pname} 当前库存 {new_qty}"
        color = IN_COLOR if t == "IN" else OUT_COLOR
        if new_qty < sf:
            msg += f"  ⚠ 低于安全库存({sf})"
            color = WARN
        app.snack(msg, color)

    sheet = ft.BottomSheet(
        content=ft.Container(
            padding=ft.padding.all(20),
            content=ft.Column(
                [
                    ft.Text("出入库登记", size=20, weight=ft.FontWeight.BOLD, color=TEXT),
                    code_f, name, qty, op_group, operator, location, note, safety,
                    ft.Row(
                        [
                            ft.FilledButton(
                                "保存", height=BTN_HEIGHT, icon=ft.Icons.SAVE,
                                on_click=submit, expand=True,
                            ),
                            ft.OutlinedButton(
                                "取消", height=BTN_HEIGHT,
                                on_click=lambda e: page.pop_dialog(), expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
    )
    page.show_dialog(sheet)
