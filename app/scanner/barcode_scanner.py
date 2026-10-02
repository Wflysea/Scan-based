"""mobile_scanner 自定义控件 —— Python 侧。

该控件仅在「安卓/iOS 构建且 Dart 侧包已编译进 APK」时真正生效；
其余平台（桌面/Web）由 ScanView 退化为 flet-camera + 手动输入。

Dart 侧实现见同目录 dart/ 包：Dart 监听到条码后调用
`sendEvent("scan", {"code": "..."})`，这里封装成 BarcodeScanEvent 回传。
"""
import json

import flet as ft


class BarcodeScanEvent(ft.Event):
    """扫码事件，携带识别到的码字符串。"""

    def __init__(self, data):
        super().__init__(data)
        payload = json.loads(data) if isinstance(data, str) else (data or {})
        self.code = payload.get("code", "") if isinstance(payload, dict) else ""


class BarcodeScanner(ft.Control):
    """原生条码/二维码扫码控件（封装 Flutter mobile_scanner 插件）。

    属性:
        on_scan:  回调 (BarcodeScanEvent) -> None，识别到码时触发。
        on_error: 回调 (str) -> None，出错时触发。
    """

    def __init__(self, on_scan=None, on_error=None, **kwargs):
        super().__init__(**kwargs)
        self.on_scan = on_scan
        self.on_error = on_error

    def _get_control_name(self):
        return "barcode_scanner"

    def _get_children(self):
        return []
