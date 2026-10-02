"""扫码页：优先使用 mobile_scanner 原生控件（安卓/iOS），否则退化为 flet-camera + 手动输入。

- 安卓/iOS 且已接入 app/scanner Dart 包：实时原生扫码，识别到码即弹出登记。
- 桌面/Web 或未接入原生控件：flet-camera 拍照识别 + 手动输入兜底。
"""
import io

import flet as ft

from app.config import *
from app.pages.operation import open_operation

# 尝试导入原生扫码自定义控件（仅安卓/iOS 构建并包含 Dart 包时可用）
try:
    from app.scanner.barcode_scanner import BarcodeScanner, BarcodeScanEvent
    _HAS_NATIVE = True
except Exception:  # noqa: BLE001
    _HAS_NATIVE = False


def decode_bytes(data: bytes):
    """用 pyzbar 解码图像字节；不可用（如安卓无 libzbar）返回 None。"""
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image
        results = decode(Image.open(io.BytesIO(data)))
        return [d.data.decode("utf-8", "ignore") for d in results]
    except Exception:  # noqa: BLE001
        return None


class ScanView(ft.Column):
    def __init__(self, app):
        super().__init__(expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)
        self.app = app
        self._decoding = False
        self._found = False
        self.native = None
        self.camera = None

        self.status = ft.Text("正在初始化…", color=SUBTEXT)
        self.manual = ft.TextField(label="手动输入编码", height=INPUT_HEIGHT, border_radius=10)
        self.scan_slot = ft.Container(
            height=360, border_radius=14, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor="#000000", alignment=ft.Alignment.CENTER,
            content=ft.ProgressRing(),
        )
        self.shoot_btn = ft.FilledButton(
            "拍照识别", icon=ft.Icons.CAMERA_ALT, height=BTN_HEIGHT,
            on_click=self.on_shoot, visible=False,
        )
        self.controls = [
            self.scan_slot,
            self.status,
            ft.Row(
                [
                    self.shoot_btn,
                    ft.FilledButton(
                        "手动确认", icon=ft.Icons.KEYBOARD, height=BTN_HEIGHT,
                        on_click=self.on_manual,
                    ),
                ],
                spacing=10, expand=True, alignment=ft.MainAxisAlignment.CENTER,
            ),
            self.manual,
            ft.Text(
                "说明：安卓/iOS 使用 mobile_scanner 原生实时扫码；桌面端退化为相机拍照识别"
                " + 手动输入（pyzbar 需在桌面系统安装 zbar）。",
                size=12, color=SUBTEXT,
            ),
        ]

    # ---- 生命周期 ----
    def did_mount(self):
        self.app.page.run_task(self.init_scanner)

    def will_unmount(self):
        self.app.page.run_task(self._teardown)

    # ---- 初始化：优先原生，退化相机 ----
    async def init_scanner(self):
        page = self.app.page
        platform = (getattr(page, "platform", "") or "").lower()
        if _HAS_NATIVE and platform in ("android", "ios"):
            try:
                self.native = BarcodeScanner(on_scan=self.on_native_scan)
                self.scan_slot.content = self.native
                self.status.value = "将条码 / 二维码对准取景框"
                page.update()
                return
            except Exception as e:  # noqa: BLE001
                self.status.value = f"原生扫码不可用，退化为相机：{e}"
        await self.init_camera()

    async def init_camera(self):
        page = self.app.page
        self.shoot_btn.visible = True
        import flet_camera as fc
        self.camera = fc.Camera(preview_enabled=True, on_stream_image=self.on_frame)
        self.scan_slot.content = self.camera
        page.update()

        # 申请相机权限（best-effort）
        # Flet 1.0 的 flet-permission-handler：
        #   - 枚举名是 Permission（不是旧版的 PermissionType）
        #   - 查询用 get_status（不是 check），申请用 request
        #   - PermissionHandler 是 Service，必须挂到 page.services 才会生效
        try:
            from flet_permission_handler import Permission, PermissionHandler, PermissionStatus

            ph = PermissionHandler()
            if ph not in page.services:
                page.services.append(ph)
            st = await ph.get_status(Permission.CAMERA)
            if st != PermissionStatus.GRANTED:
                await ph.request(Permission.CAMERA)
        except Exception:  # noqa: BLE001
            pass

        try:
            cams = await self.camera.get_available_cameras()
            if not cams:
                self.status.value = "未检测到相机（桌面正常，扫码请用手动输入）"
                page.update()
                return
            back = next(
                (c for c in cams if c.lens_direction == fc.CameraLensDirection.BACK),
                cams[0],
            )
            await self.camera.initialize(
                description=back, resolution_preset=fc.ResolutionPreset.MEDIUM,
                enable_audio=False,
            )
            try:
                await self.camera.start_image_stream()
            except Exception:  # noqa: BLE001
                pass
            self.status.value = "将条码 / 二维码对准取景框（或点拍照识别）"
        except Exception as e:  # noqa: BLE001
            self.status.value = f"相机初始化失败：{e}\n请确认已授予相机权限"
        page.update()

    async def _teardown(self):
        try:
            if self.camera:
                await self.camera.stop_image_stream()
        except Exception:  # noqa: BLE001
            pass

    # ---- 原生扫码回调 ----
    def on_native_scan(self, e: "BarcodeScanEvent"):
        if self._found:
            return
        self._found = True
        open_operation(self.app, code=e.code, default_type="IN")

    # ---- 相机帧解码 ----
    def on_frame(self, e):
        if self._found or self._decoding:
            return
        self._decoding = True
        codes = decode_bytes(e.bytes)
        self._decoding = False
        if codes:
            self._found = True
            self.app.page.run_task(self.stop_and_open(codes[0]))

    async def stop_and_open(self, code):
        try:
            await self.camera.stop_image_stream()
        except Exception:  # noqa: BLE001
            pass
        open_operation(self.app, code=code, default_type="IN")

    async def on_shoot(self, e):
        try:
            data = await self.camera.take_picture()
            codes = decode_bytes(data)
            if codes:
                open_operation(self.app, code=codes[0], default_type="IN")
            else:
                self.status.value = "未识别到条码，请重试或手动输入"
                self.app.page.update()
        except Exception as ex:  # noqa: BLE001
            self.status.value = f"拍照失败：{ex}"
            self.app.page.update()

    def on_manual(self, e):
        code = self.manual.value.strip()
        if not code:
            self.app.snack("请输入编码")
            return
        open_operation(self.app, code=code, default_type="IN")
