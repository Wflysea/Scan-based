import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

/// Flet 自定义控件：封装 mobile_scanner，渲染实时扫码预览，
/// 并把识别到的码通过 Flet 事件通道回传给 Python 侧的 on_scan 回调。
class BarcodeScannerControl extends Control {
  late final MobileScannerController _controller;

  BarcodeScannerControl({
    required super.camera,
    required super.id,
    required super.parentControl,
    required super.children,
    required super.disposeCallback,
  }) {
    _controller = MobileScannerController();
  }

  @override
  Widget build(BuildContext context, Control? parent, List<Control>? children) {
    return MobileScanner(
      controller: _controller,
      onDetect: (capture) {
        for (final barcode in capture.barcodes) {
          final code = barcode.rawValue;
          if (code != null && code.isNotEmpty) {
            // 回传给 Python 侧 on_scan 回调：{"code": "..."}
            sendEvent("scan", {"code": code});
          }
        }
      },
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
