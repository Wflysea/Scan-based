"""流水页：按编码、时间范围、出入库类型筛选并查看历史记录。"""
import flet as ft
from datetime import date

from app import db
from app.config import *


def records_view(app):
    page = app.page
    code_f = ft.TextField(label="按编码筛选", height=INPUT_HEIGHT, border_radius=10)
    type_dd = ft.Dropdown(
        label="类型", height=INPUT_HEIGHT, border_radius=10,
        options=[
            ft.dropdown.Option("", "全部"),
            ft.dropdown.Option("IN", "入库"),
            ft.dropdown.Option("OUT", "出库"),
        ],
        value="",
    )

    start_date = None
    end_date = None
    start_btn = ft.OutlinedButton(
        "开始日期", icon=ft.Icons.CALENDAR_TODAY,
        on_click=lambda e: page.open(dp_start),
    )
    end_btn = ft.OutlinedButton(
        "结束日期", icon=ft.Icons.CALENDAR_TODAY,
        on_click=lambda e: page.open(dp_end),
    )
    dp_start = ft.DatePicker(
        first_date=date(2020, 1, 1), last_date=date.today(),
        on_change=lambda e: set_date(e, "start"),
    )
    dp_end = ft.DatePicker(
        first_date=date(2020, 1, 1), last_date=date.today(),
        on_change=lambda e: set_date(e, "end"),
    )

    list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def set_date(e, which):
        nonlocal start_date, end_date
        d = e.control.value
        if which == "start":
            start_date = d
            start_btn.text = f"开始 {d}"
        else:
            end_date = d
            end_btn.text = f"结束 {d}"
        page.update()

    def query(e=None):
        rows = []
        for t in db.list_transactions(
            code=code_f.value.strip(), start=start_date, end=end_date,
            op_type=type_dd.value or None,
        ):
            is_in = t["op_type"] == "IN"
            rows.append(
                ft.Card(
                    elevation=1,
                    content=ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.ARROW_DOWNWARD if is_in else ft.Icons.ARROW_UPWARD,
                            color=IN_COLOR if is_in else OUT_COLOR,
                        ),
                        title=ft.Text(
                            f"{'入库' if is_in else '出库'}  {t['quantity']}  ·  {t['name']}"
                        ),
                        subtitle=ft.Text(
                            f"编码 {t['code']} | {t['operator'] or '—'} | {t['location'] or '—'}\n{t['created_at']}"
                        ),
                    ),
                )
            )
        if not rows:
            rows.append(
                ft.Container(
                    ft.Text("暂无记录", color=SUBTEXT),
                    alignment=ft.alignment.center, padding=30,
                )
            )
        list_col.controls = rows
        page.update()

    query_btn = ft.FilledButton(
        "查询", icon=ft.Icons.SEARCH, height=BTN_HEIGHT,
        on_click=query, expand=True,
    )

    view = ft.Column(
        [
            code_f,
            type_dd,
            ft.Row([start_btn, end_btn], spacing=10, expand=True),
            query_btn,
            list_col,
        ],
        spacing=10,
        expand=True,
    )
    query()
    return view
