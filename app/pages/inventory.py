"""库存页：展示当前库存，支持按名称/编码搜索；点击条目可发起出入库。"""
import flet as ft

from app import db
from app.config import *
from app.pages.operation import open_operation


def inventory_view(app):
    page = app.page
    search = ft.TextField(
        label="搜索名称 / 编码", height=INPUT_HEIGHT, border_radius=10,
        on_submit=lambda e: reload(),
    )
    list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def reload():
        rows = []
        for p in db.list_products(search.value.strip()):
            low = p["quantity"] < p["safety_stock"]
            rows.append(
                ft.Card(
                    elevation=1,
                    content=ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.INVENTORY_2,
                            color=OUT_COLOR if low else PRIMARY,
                        ),
                        title=ft.Text(
                            p["name"],
                            weight=ft.FontWeight.BOLD if low else ft.FontWeight.NORMAL,
                        ),
                        subtitle=ft.Text(
                            f"编码 {p['code']}  |  库位 {p['location'] or '—'}  |  安全 {p['safety_stock']}{p['unit']}"
                        ),
                        trailing=ft.Container(
                            content=ft.Text(
                                f"{p['quantity']} {p['unit']}",
                                weight=ft.FontWeight.BOLD,
                                color=OUT_COLOR if low else TEXT,
                                size=16,
                            ),
                            padding=8,
                        ),
                        on_click=lambda e, code=p["code"]: open_operation(
                            app, code=code, default_type="IN"
                        ),
                    ),
                )
            )
        if not rows:
            rows.append(
                ft.Container(
                    ft.Text("暂无数据，去扫码或手动登记吧", color=SUBTEXT),
                    alignment=ft.alignment.center, padding=30,
                )
            )
        list_col.controls = rows
        page.update()

    view = ft.Column([search, list_col], spacing=10, expand=True)
    reload()
    return view
