"""首页 / 工作台：关键指标、低库存预警、快捷入口、数据备份。"""
import flet as ft

from app import db
from app.config import *
from app.pages.operation import open_operation
from app.pages.export_xlsx import build_export_button


def _stat_card(label, value, color):
    return ft.Container(
        width=158,
        padding=14,
        border_radius=12,
        bgcolor=CARD,
        border=ft.Border.all(1, BORDER),
        content=ft.Column(
            [
                ft.Text(label, size=13, color=SUBTEXT),
                ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=4,
        ),
    )


def home_view(app):
    page = app.page
    s = db.get_stats()
    low = s["low"]

    if low:
        items = [
            ft.Text(
                f"• {p['name']}（{p['code']}）剩余 {p['quantity']} / 安全 {p['safety_stock']}{p['unit']}",
                size=13,
                color=OUT_COLOR,
            )
            for p in low[:6]
        ]
        low_card = ft.Container(
            padding=14,
            border_radius=12,
            bgcolor="#FFF3E0",
            border=ft.Border.all(1, "#FFCC80"),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.WARNING_AMBER, color=WARN),
                            ft.Text("低于安全库存提醒", weight=ft.FontWeight.BOLD, color=WARN),
                        ]
                    ),
                    *items,
                ],
                spacing=6,
            ),
        )
    else:
        low_card = ft.Container(
            ft.Text("✓ 库存充足，无预警", color=IN_COLOR, size=13),
            padding=12,
            border_radius=12,
            bgcolor="#E8F5E9",
            border=ft.Border.all(1, "#A5D6A7"),
        )

    quick = ft.Row(
        [
            ft.FilledButton(
                "去扫码", icon=ft.Icons.QR_CODE_2, height=BTN_HEIGHT,
                on_click=lambda e: app.select(1), expand=True,
            ),
            ft.FilledButton(
                "手动登记", icon=ft.Icons.EDIT_NOTE, height=BTN_HEIGHT,
                on_click=lambda e: open_operation(app, default_type="IN"), expand=True,
            ),
        ],
        spacing=10,
    )
    nav_row = ft.Row(
        [
            ft.FilledTonalButton(
                "查看库存", icon=ft.Icons.INVENTORY_2, height=BTN_HEIGHT,
                on_click=lambda e: app.select(2), expand=True,
            ),
            ft.FilledTonalButton(
                "出入库流水", icon=ft.Icons.HISTORY, height=BTN_HEIGHT,
                on_click=lambda e: app.select(3), expand=True,
            ),
        ],
        spacing=10,
    )
    export_row = ft.Row([build_export_button(app)], spacing=10)

    return ft.Column(
        [
            ft.Text("工作台", size=22, weight=ft.FontWeight.BOLD, color=TEXT),
            ft.Row(
                [_stat_card("商品种类", s["total_sku"], PRIMARY),
                 _stat_card("库存总量", s["total_qty"], TEXT)],
                spacing=10, wrap=True,
            ),
            ft.Row(
                [_stat_card("今日入库", s["today_in"], IN_COLOR),
                 _stat_card("今日出库", s["today_out"], OUT_COLOR)],
                spacing=10, wrap=True,
            ),
            low_card,
            quick,
            nav_row,
            export_row,
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
