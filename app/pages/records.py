"""流水页：按编码、时间范围、出入库类型筛选并查看历史记录。

Flet 1.0 适配说明：
- 下拉选项改用 ft.DropdownOption（1.0 新类名，取代 ft.dropdown.Option）
- 日期范围改为文本框输入 YYYY-MM-DD（1.0 中 DatePicker 已服务化/API 变更，
  用文本输入可稳定跨版本工作）
- 按钮不再有 text 属性，更新标题统一用 content
"""
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
            ft.DropdownOption(key="", text="全部"),
            ft.DropdownOption(key="IN", text="入库"),
            ft.DropdownOption(key="OUT", text="出库"),
        ],
        value="",
    )

    start_f = ft.TextField(
        label="开始日期", hint_text="YYYY-MM-DD，留空不限",
        height=INPUT_HEIGHT, border_radius=10,
    )
    end_f = ft.TextField(
        label="结束日期", hint_text="YYYY-MM-DD，留空不限",
        height=INPUT_HEIGHT, border_radius=10,
    )

    list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def _parse_date(text_value, field_name):
        """把文本框内容解析为 date；空值返回 None，格式错误返回提示信息。"""
        s = (text_value or "").strip()
        if not s:
            return None, None
        try:
            return date.fromisoformat(s), None
        except ValueError:
            return None, f"{field_name}格式应为 YYYY-MM-DD（当前：{s}）"

    def query(e=None):
        start_date, err1 = _parse_date(start_f.value, "开始日期")
        if err1:
            app.snack(err1, OUT_COLOR)
            return
        end_date, err2 = _parse_date(end_f.value, "结束日期")
        if err2:
            app.snack(err2, OUT_COLOR)
            return

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
                    alignment=ft.Alignment.CENTER, padding=30,
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
            start_f,
            end_f,
            query_btn,
            list_col,
        ],
        spacing=10,
        expand=True,
    )
    query()
    return view
