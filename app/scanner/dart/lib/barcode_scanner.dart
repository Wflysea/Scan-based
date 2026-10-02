import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';
import 'barcode_scanner_control.dart';

/// 注册自定义控件，使 Python 侧的 BarcodeScanner 能映射到本 Dart 实现。
///
/// 在 Flet Flutter 工程入口 main() 中调用一次 initialize() 即可：
///   import 'package:barcode_scanner_control/barcode_scanner.dart';
///   void main() {
///     initialize();
///     FletApp(...).run();
///   }
void initialize() {
  FletAppServices.registerControl(
    "barcode_scanner",
    (camera, id, parent, children, dispose) => BarcodeScannerControl(
      camera: camera,
      id: id,
      parentControl: parent,
      children: children,
      disposeCallback: dispose,
    ),
  );
}
