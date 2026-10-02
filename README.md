# 扫码出入库管理（Flet + SQLite，安卓 APK）

一个纯 Python 实现的安卓扫码出入库管理应用：摄像头扫描条码/二维码识别物料，支持入库/出库、流水查询、库存自动增减与低库存预警，数据本地 SQLite 持久化，无后端依赖。

## 功能

- 📷 **扫码识别**：安卓/iOS 使用 `mobile_scanner` 原生控件实时扫码；桌面退化为相机拍照识别 + 手动输入。
- 🔼🔽 **入库 / 出库**：记录商品名称、编码、数量、操作时间、操作人、仓库/库位、备注。
- 📦 **库存联动**：入库加、出库减；出库时库存不足会拦截并提示。
- ⚠️ **低库存预警**：库存低于安全库存时，首页横幅 + 库存页红色高亮提示。
- 🔎 **流水查询**：按编码、时间范围、出入库类型筛选。
- 📤 **导出 xlsx 备份**：一键将库存与流水导出为 Excel（`openpyxl` + `FilePicker`）。
- 💾 **本地持久化**：SQLite 文件随应用存储，卸载即清。

## 目录结构

```
inventory_app/
├── main.py                 # 入口：导航 + 四个页面
├── pyproject.toml          # Flet 打包配置（含安卓相机权限 + 自定义控件）
├── requirements.txt        # 桌面开发依赖（含 pyzbar / Pillow）
├── requirements-android.txt# 安卓构建依赖（已排除无安卓 wheel 的 pyzbar / Pillow）
├── .github/workflows/build-apk.yml  # GitHub Actions 自动出包
├── app/
│   ├── config.py           # 配色与触控尺寸常量
│   ├── db.py               # SQLite 持久化与业务逻辑
│   ├── scanner/            # mobile_scanner 自定义控件
│   │   ├── barcode_scanner.py     # Python 侧 BarcodeScanner 控件
│   │   └── dart/                  # Dart 侧 Flutter 包（封装 mobile_scanner）
│   └── pages/
│       ├── home.py         # 工作台（含导出 xlsx 按钮）
│       ├── scan.py         # 扫码页（原生控件优先，相机退化）
│       ├── operation.py    # 出入库登记（BottomSheet）
│       ├── inventory.py    # 库存页
│       ├── records.py      # 流水查询页
│       └── export_xlsx.py  # 导出 Excel 备份
└── app/inventory.db        # 运行时自动生成
```

## 依赖

```
flet>=0.27.0          # UI 框架
flet-camera>=0.1.0    # 相机预览/取流（桌面退化路径用）
flet-permission-handler>=0.1.0  # 运行时申请相机权限
pyzbar>=0.1.10        # 桌面端条码/二维码解码（需系统 zbar）
Pillow>=10.0.0        # 图像字节转 PIL，供 pyzbar 解码
openpyxl>=3.1.0       # 导出 xlsx 备份
```

桌面开发还需系统安装 zbar：

- Windows：下载 [zbar](https://zbar.sourceforge.net/) 安装，并把 `zbar.dll` 所在目录加入 PATH。
- macOS：`brew install zbar`
- Linux（Debian/Ubuntu）：`sudo apt-get install libzbar0`

> ⚠️ **关键认知：`flet build apk` 解析的依赖来自 `pyproject.toml` 的 `[project.dependencies]`，不是 `requirements.txt` / `requirements-android.txt`**。
> 因此安卓不需要、且**没有安卓 wheel** 的包（例如 `pyzbar`：源上最高仅 `0.1.9`，且依赖系统 libzbar）必须**从 `pyproject.toml` 的依赖里移除**，否则打包直接报 `No matching distribution found` 失败。
> `Pillow` 在 Flet 预编译源有安卓 wheel，可保留。`pyzbar` 仅桌面端扫码使用（桌面开发由 `requirements.txt` 安装）；扫码页中它是「懒加载 + 失败兜底」，安卓端走 `mobile_scanner` 原生控件或手动输入，移除 `pyproject.toml` 中的 `pyzbar` 不影响功能。

## 本地运行（桌面开发调试）

```bash
cd inventory_app
pip install -r requirements.txt
python main.py
```

> 注：桌面端 `flet-camera` 无相机、`mobile_scanner` 未接入，扫码页会提示“未检测到相机”，
> 用「手动输入」即可正常调试入库/出库/库存/流水/导出等全部逻辑。

### 开发期自检（强烈建议在打包前跑）

Flet 1.0 是破坏性升级，很多 API 被改名/移除；这类问题**构建时不会报错，只有手机上运行才崩**。
仓库内置了两个自检脚本，可在打包前提前发现：

```bash
# 1) 静态 API 校验：ft.X 名称 / 构造参数 / page.* 成员
python tests/check_flet_api.py

# 2) 冒烟构建：在真实 ft.Page 上构建全部页面 + 出入库弹窗 + xlsx 导出
python tests/smoke_build_views.py
```

两个脚本都需要装了 `flet==1.0.3` 的解释器（见 `requirements.txt`）。
在 CI 里也可以把它们加进 workflow 的 build 步骤之前，避免“构建成功但一打开就崩”。

## 安卓相机权限配置

权限在 `pyproject.toml` 中声明，打包时自动注入 `AndroidManifest.xml`：

```toml
[tool.flet]
permissions = ["camera"]   # 跨平台权限包，自动注入 CAMERA

[tool.flet.android.permission]
"android.permission.CAMERA" = true
"android.permission.INTERNET" = true   # Flet 默认已加，列出以明确

[tool.flet.android.feature]
"android.hardware.camera" = true
"android.hardware.camera.autofocus" = true
```

运行时权限在 `app/pages/scan.py` 的 `init_camera()` 中用 `flet-permission-handler` 申请（已做异常兜底）。

等效命令行写法：

```bash
flet build apk \
  --android-permissions "android.permission.CAMERA=true" \
  --android-features "android.hardware.camera=true"
```

## 打包安卓 APK（`flet build apk`）

前置条件（仅打包机需要，开发调试不需要）：

1. 安装 **Android SDK Command-line Tools**，并配置环境变量：
   ```bash
   export ANDROID_HOME=$HOME/Android/Sdk
   export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
   sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
   ```
2. 安装 **Java 17（JDK）**，并设置 `JAVA_HOME`。
3. 安装 Flet 命令行（建议用虚拟环境）：`pip install flet`

打包步骤：

```bash
cd inventory_app
pip install -r requirements.txt
flet build apk            # 输出 build/apk/app-release.apk
# 按 CPU 架构拆分：flet build apk --split-per-abi
# 正式签名：在 pyproject.toml 填好 [tool.flet.android.signing] 后 flet build apk --build-number 1
```

> 发布 Google Play 用 `flet build aab`。

## 安卓端原生实时扫码（mobile_scanner 自定义控件）

已在 `app/scanner/` 完整实现，安卓/iOS 上做到毫秒级实时扫码：

- **Python 侧** `app/scanner/barcode_scanner.py`：`BarcodeScanner(ft.Control)`，暴露 `on_scan`
  事件，回调参数为 `BarcodeScanEvent.code`。
- **Dart 侧** `app/scanner/dart/`：Flutter 包封装 `mobile_scanner` 插件，
  `barcode_scanner_control.dart` 在 `onDetect` 中 `sendEvent("scan", {"code": ...})` 回传；
  `barcode_scanner.dart` 用 `FletAppServices.registerControl` 注册类型 `barcode_scanner`。
- **接入**：在 `pyproject.toml` 的 `[tool.flet]` 下登记 `controls = ["app/scanner/dart"]`
  （或 `flet build apk --controls app/scanner/dart`），并在 Flet 生成的 Flutter
  `main.dart` 的 `main()` 里调用 `initialize()` 后再 `FletApp(...).run()`。
- **自动切换**：`app/pages/scan.py` 的 `ScanView` 在安卓/iOS 且控件可用时自动启用原生扫码；
  否则退化为相机拍照 + 手动输入，功能不受影响。

详细接入步骤见 `app/scanner/dart/README.md`。Dart 代码需在 Flutter 工具链下编译，无法在纯 Python 环境验证。

## 导出 xlsx 备份

首页「导出 xlsx 备份」按钮（`app/pages/export_xlsx.py`）将数据导出为 Excel：

- **字段范围**（两个 Sheet）：
  - `商品库存`：编码、商品名称、当前库存、安全库存、单位、仓库/库位、更新时间。
  - `出入库流水`：序号、编码、商品名称、操作类型（入库/出库）、数量、操作人、仓库/库位、备注、操作时间。
- **文件命名**：`库存备份_YYYYMMDD_HHMMSS.xlsx`（例如 `库存备份_20261002_205000.xlsx`）。
- **交互逻辑**：点击 → 弹出系统保存对话框（预填文件名）→ 用户选择路径后写入并提示成功（含路径）；
  取消则不导出；异常弹错误提示。导出按钮在 `page.overlay` 上挂载单例 `FilePicker`，多次进入首页复用。

## GitHub Actions 自动构建 APK

已内置 `.github/workflows/build-apk.yml`，推送代码即可在云端自动出包，无需本地配 Android SDK。

**触发方式**
- 推送到 `main`/`master`：自动构建 APK，并作为 **Artifact** 提供下载（保留 14 天）。
- 手动在仓库 `Actions → Build Android APK → Run workflow` 触发。
- 发布 **GitHub Release**：额外构建 **AAB**，并把 APK/AAB 作为资产挂到 Release 页面，可直接下载安装。

**工作流做的事**
1. 装 Java 17（Temurin）、Python 3.12、Flutter stable。
2. `android-actions/setup-android` 装 Android SDK 并自动接受 license、设置 `ANDROID_HOME`。
3. （可选）`pip install -r requirements-android.txt` 仅为 CI 的 Python 环境安装包；**`flet build apk` 真正打包的依赖来自 `pyproject.toml`**，已从中排除无安卓 wheel 的 `pyzbar`。
4. `flet build apk --verbose` → 产物 `build/apk/`。
5. 上传 Artifact；Release 时再 `flet build aab` 并附加到 Release。

**使用注意**
- 首次构建约 10~20 分钟（需下载 Flutter / SDK / Gradle 依赖）。
- 本工作流假设 Flet 项目在仓库根目录（`pyproject.toml` 在根）。若项目在子目录，请在 build 步骤加 `working-directory`。
- **自动签名（可选）**：在仓库 `Settings → Secrets` 配置 `KEYSTORE_BASE64` / `KEYSTORE_PASSWORD` / `KEY_ALIAS` / `KEY_PASSWORD`，在 `pyproject.toml` 的 `[tool.flet.android.signing]` 引用，并在「Build APK」前加一步 `echo "$KEYSTORE_BASE64" | base64 -d > release-key.jks`。未签名也能构建成功（输出未签名 APK，可用于自测安装）。

## 国际化 / 扩展建议

- 多仓多员：表已含 `location`/`operator` 字段，可在首页加筛选维度。
- 主题：当前为浅色；如需深色，调整 `app/config.py` 中常量并切换 `page.theme_mode`。
