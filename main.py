"""应用入口：顶部 AppBar + 底部导航 + 内容区，四个标签页（首页/扫码/库存/流水）。"""
import flet as ft

from app.db import init_db
from app.pages.home import home_view
from app.pages.scan import ScanView
from app.pages.inventory import inventory_view
from app.pages.records import records_view
from app.config import BG, PRIMARY, PRIMARY_LIGHT, TEXT


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current = 0
        self.content = ft.Container(expand=True, padding=12, content=ft.Column())

        self.nav = ft.NavigationBar(
            selected_index=0,
            on_change=self.on_nav,
            bgcolor=ft.Colors.WHITE,
            destinations=[
                # Flet 1.0：0.x 的 ft.NavigationDestination 已更名为 ft.NavigationBarDestination
                ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="首页"),
                ft.NavigationBarDestination(icon=ft.Icons.QR_CODE_2, selected_icon=ft.Icons.QR_CODE_2, label="扫码"),
                ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label="库存"),
                ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, selected_icon=ft.Icons.HISTORY, label="流水"),
            ],
        )

        page.title = "扫码出入库管理"
        page.bgcolor = BG
        page.appbar = ft.AppBar(
            title=ft.Text("扫码出入库管理", color=TEXT),
            bgcolor=PRIMARY_LIGHT, center_title=True, elevation=1,
        )
        page.navigation_bar = self.nav
        page.add(ft.Column([self.content], expand=True, spacing=0))
        self.select(0)

    def on_nav(self, e):
        self.select(e.control.selected_index)

    def select(self, idx):
        self.current = idx
        self.nav.selected_index = idx
        if idx == 0:
            view = home_view(self)
        elif idx == 1:
            view = ScanView(self)
        elif idx == 2:
            view = inventory_view(self)
        else:
            view = records_view(self)
        self.content.content = view
        self.page.update()

    def refresh(self):
        # 出入库保存后刷新当前页（例如库存数量、低库存预警）
        self.select(self.current)

    def snack(self, message, color=None):
        # Flet 1.0：SnackBar 通过 page.show_dialog 显示（不再用 page.snack_bar + open）
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=color or PRIMARY,
            )
        )


def main(page: ft.Page):
    init_db()
    App(page)


if __name__ == "__main__":
    # Flet 1.0：ft.app(target=...) 已移除，改为 ft.run(main)
    ft.run(main)
