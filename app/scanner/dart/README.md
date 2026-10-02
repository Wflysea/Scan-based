# mobile_scanner 自定义控件（Dart / Flutter 侧）

Python 侧：`../barcode_scanner.py`（`BarcodeScanner` 控件，事件 `on_scan`）。

本目录是配套的 Flutter 包，封装 [`mobile_scanner`](https://pub.dev/packages/mobile_scanner)
插件，把识别到的码通过 Flet 事件通道回传给 Python，实现安卓/iOS 原生级实时扫码。

## 文件

- `lib/barcode_scanner_control.dart`：`BarcodeScannerControl`，渲染 `MobileScanner` 并
  `sendEvent("scan", {"code": ...})`。
- `lib/barcode_scanner.dart`：`initialize()` 用 `FletAppServices.registerControl` 注册
  控件类型 `barcode_scanner`。
- `pubspec.yaml`：依赖 `flet` 与 `mobile_scanner`。

## 接入到 flet build apk

1. 依赖：本包已声明 `mobile_scanner`；`flet` 由 Flet 构建注入（见第 3 步）。
2. 在项目 `pyproject.toml` 的 `[tool.flet]` 下登记自定义控件包路径，例如：
   ```toml
   [tool.flet]
   controls = ["app/scanner/dart"]
   ```
   若你的 Flet 版本使用 `--controls` 参数，则改为：
   `flet build apk --controls app/scanner/dart`
3. 让 Flet 在启动 Flutter 时调用 `initialize()`：在 Flet 生成的 Flutter 工程
   `lib/main.dart` 的 `main()` 中，于 `FletApp(...).run()` 之前加入：
   ```dart
   import 'package:barcode_scanner_control/barcode_scanner.dart';
   void main() {
     initialize();          // 注册 barcode_scanner 控件
     FletApp(...).run();
   }
   ```
   （Flet 构建允许通过自定义 `main.dart` / `--flutter-app-dir` 覆盖默认入口；
   具体以你所用的 Flet 版本官方文档「Custom controls」为准。）
4. 构建：
   ```bash
   flet build apk
   ```
   构建成功后 APK 内含 `mobile_scanner`，`ScanView` 在安卓/iOS 上会自动启用原生扫码。

> 注：本 Dart 代码需在 Flutter 工具链下编译，无法在纯 Python 环境验证；
> 桌面/Web 未接入本包时，应用会退化为相机拍照 + 手动输入，功能不受影响。
