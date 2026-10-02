"""导出 xlsx 备份：将库存与出入库流水导出为 Excel（openpyxl + FilePicker）。

Flet 1.0 适配：FilePicker 已是**异步服务**——直接实例化并 `await` 调用，
不再挂 page.overlay、也不再用 on_result 回调。
安卓 / iOS / Web 必须传 `src_bytes` 才会真正写入文件内容；
桌面端 save_file 仅返回路径，因此拿到路径后补写一次。

字段范围：
- Sheet「商品库存」：编码, 商品名称, 当前库存, 安全库存, 单位, 仓库/库位, 更新时间
- Sheet「出入库流水」：序号, 编码, 商品名称, 操作类型, 数量, 操作人, 仓库/库位, 备注, 操作时间

文件命名：库存备份_YYYYMMDD_HHMMSS.xlsx（例如 库存备份_20261002_205000.xlsx）

交互逻辑：点击按钮 → 生成 xlsx 字节 → 弹出系统保存对话框（已预填文件名）→
  用户选择路径或取消；选择后写入并弹成功提示（含完整路径）；取消则不导出；异常弹错误提示。
"""
import datetime as _dt
from io import BytesIO

import flet as ft

from app import db
from app.config import PRIMARY, OUT_COLOR, BTN_HEIGHT


def build_export_button(app):
    async def on_click(e):
        await _export(app)

    return ft.FilledTonalButton(
        "导出 xlsx 备份", icon=ft.Icons.DOWNLOAD, height=BTN_HEIGHT,
        on_click=on_click,
    )


async def _export(app):
    name = f"库存备份_{_dt.datetime.now():%Y%m%d_%H%M%S}.xlsx"

    # 1) 先在内存生成 xlsx 内容
    try:
        data = _build_xlsx_bytes()
    except Exception as ex:  # noqa: BLE001
        app.snack(f"生成备份失败：{ex}", OUT_COLOR)
        return

    # 2) 弹出保存对话框（安卓必需 src_bytes）
    try:
        file_picker = ft.FilePicker()
        path = await file_picker.save_file(
            dialog_title="导出库存备份",
            file_name=name,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
            src_bytes=data,
        )
    except Exception as ex:  # noqa: BLE001
        app.snack(f"导出失败：{ex}", OUT_COLOR)
        return

    if not path:
        return  # 用户取消

    # 3) 桌面端 save_file 只返回路径不写内容 → 补写；移动端已由 src_bytes 写入，写入失败忽略
    try:
        with open(path, "wb") as f:
            f.write(data)
    except Exception:  # noqa: BLE001
        pass

    app.snack(f"已导出备份：{path}", PRIMARY)


def _build_xlsx_bytes() -> bytes:
    """生成 xlsx 并返回字节内容（不落盘，便于安卓通过 src_bytes 写出）。"""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()

    # ---- Sheet 1：商品库存 ----
    ws1 = wb.active
    ws1.title = "商品库存"
    ws1.append(["编码", "商品名称", "当前库存", "安全库存", "单位", "仓库/库位", "更新时间"])
    for p in db.list_products():
        ws1.append([
            p["code"], p["name"], p["quantity"], p["safety_stock"],
            p["unit"], p["location"], p["updated_at"],
        ])

    # ---- Sheet 2：出入库流水 ----
    ws2 = wb.create_sheet("出入库流水")
    ws2.append(["序号", "编码", "商品名称", "操作类型", "数量", "操作人", "仓库/库位", "备注", "操作时间"])
    for t in db.list_transactions():
        ws2.append([
            t["id"], t["code"], t["name"],
            "入库" if t["op_type"] == "IN" else "出库",
            t["quantity"], t["operator"], t["location"], t["note"], t["created_at"],
        ])

    # ---- 表头样式 + 列宽 ----
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1565C0")
    for ws in (ws1, ws2):
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for col in ws.columns:
            letter = col[0].column_letter
            ws.column_dimensions[letter].width = 18
        ws.freeze_panes = "A2"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
