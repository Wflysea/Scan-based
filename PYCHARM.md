# 在 PyCharm 中开发本 Flet 扫码出入库应用

本指南基于 PyCharm（Professional / Community 均可），针对本项目 `inventory_app` 给出
**打开项目、配置解释器、编写代码、调试运行、查看数据库、单元测试、打包 APK** 的具体操作。

> 菜单英文以 PyCharm 默认英文界面为准；若已安装官方中文语言包
> （Settings → Plugins 搜 *Chinese (Simplified) Language Pack*），中英文对照：
> `File`=文件，`Settings`=设置（`Ctrl+Alt+S`），`Run`=运行，`Debug`=调试，
> `Terminal`=终端，`Database`=数据库。

---

## 1. 打开项目

1. `File` → `Open`，选择目录 `E:/WorkBuddy/闲聊/inventory_app`。
2. 弹出 *Trust and Open* 时勾选 **Trust Project**（允许执行项目内脚本/构建）。
3. PyCharm 会自动识别 `app/`（含 `__init__.py`）为 Python 包；若 `from app...` 报红，
   右键 `app` → `Mark Directory as` → `Sources Root`。

---

## 2. 配置 Python 解释器（虚拟环境）

推荐为项目单独建一个 venv，避免污染系统 Python：

1. `Settings` (`Ctrl+Alt+S`) → `Project: inventory_app` → `Python Interpreter`。
2. 右上角齿轮 ⚙ → `Add Interpreter` → `Add Local Interpreter`。
3. 选 `Virtualenv Environment` → `New`，Base interpreter 选 **Python 3.10+**
   （本机 3.13 可用）→ `OK`。PyCharm 会在项目下生成 `.venv/`。
4. 安装依赖（两种方式任选）：
   - **图形界面**：仍在 Python Interpreter 页点 ＋ ，分别搜索并安装
     `flet`、`flet-camera`、`flet-permission-handler`、`pyzbar`、`Pillow`。
   - **Terminal**：底部打开 `Terminal`，执行
     ```bash
     pip install -r requirements.txt
     ```
5. ⚠️ 桌面开发注意：
   - `flet-camera` 在 Windows/macOS/Linux **装得上但相机不可用**（仅安卓/iOS/Web 支持），
     扫码页会提示“未检测到相机”，其余页面正常。
   - `pyzbar` 需要系统 `libzbar`：Windows 装 [zbar](https://zbar.sourceforge.net/) 并把
     其 `bin` 目录加入 PATH；macOS `brew install zbar`；Ubuntu `sudo apt install libzbar0`。

---

## 3. 代码编写（PyCharm 提效）

- **智能补全**：输入 `ft.` 或 `fc.` 会有 Flet 控件/属性提示；`db.` 可补全数据库函数。
- **跳转到定义**：`Ctrl`+点击 `home_view` / `db.record_operation` 直达实现。
- **结构化参数提示**：在 `ft.TextField(` 处 PyCharm 会列出 `label`/`height`/`border_radius` 等。
- **TODO**：在代码里写 `# TODO 接入 mobile_scanner` ，`Alt+6` 打开 TODO 工具窗集中管理。
- **改配色即时生效**：调 `app/config.py` 里的 `PRIMARY`/`IN_COLOR` 等常量后直接 Run 即可。
- **本地历史**：右键任意文件 → `Local History` → `Show History`，可回滚误改。

---

## 4. 运行

### 4.1 直接运行（最常用）
打开 `main.py` → 右上角绿色 ▶（`Run 'main'`），或右键 `main.py` → `Run 'main'`。
PyCharm 自动生成 Run/Debug Configuration（类型 Python，Script path=`main.py`，
Working directory=项目根）。也可使用本项目已附的 `.run/main.run.xml`：
`Run` → `Edit Configurations` → 左上 ＋ → `Python` → 在 `Store as project file` 指向
`.run/main.run.xml`（若该解释器提示未找到，重新选择本项目的 venv 即可）。

### 4.2 带热重载开发
Terminal 执行：
```bash
flet run main.py
```
Flet CLI 支持保存即刷新。可在 PyCharm 建一个 Shell Script 配置封装这条命令。

> 运行后 `ft.app()` 会用浏览器/Flutter 窗口渲染 UI；桌面端扫码页不可用属正常。

---

## 5. 调试（Debug）

### 5.1 调试业务逻辑（推荐，无需相机）
数据层与页面逻辑是纯 Python，最适合用 Debug 单步：
1. 在 `app/db.py` 的 `record_operation` 行号左侧点红点设断点。
2. 打开 `tests/test_db.py` → 右键 → `Debug 'pytest for test_db.py'`。
3. Debug 工具窗中查看 `Variables` / `Watches`：监测 `delta`、`new_qty`、`sf` 是否正确。
4. 用 `Step Over`(`F8`) / `Step Into`(`F7`) 跟踪一次入库→出库→低库存的完整流程。

### 5.2 调试界面回调
- 在 `app/pages/operation.py` 的 `submit()` 设断点，Debug 运行 `main.py`，
  在弹出的界面点“保存”即可命中，检查 `code`、`qty`、`t`（IN/OUT）。
- 调试 `app/pages/scan.py` 的 `async def init_camera`：PyCharm 支持异步断点，
  Debug 窗勾选 **Async stack trace** 可查看协程调用栈。

### 5.3 测试运行器配置
`Settings` → `Tools` → `Python Integrated Tools` → `Testing` →
`Default test runner` 选 **pytest**。之后右键 `tests/` 可一键 Run/Debug。

---

## 6. 用 Database 工具窗查看 SQLite（强烈推荐）

无需写 SQL 即可核对库存联动是否正确：
1. 右侧 `Database` 工具窗（或 `View` → `Tool Windows` → `Database`）。
2. ＋ → `Data Source` → `SQLite`。
3. `File` 选择 `app/inventory.db`（首次 `Run 'main'` 后才会生成；若没有，先 Run 一次）。
4. 展开 `products`、`transactions` 表，双击即可看到数据；
   点表上方 SQL 控制台，输入并运行：
   ```sql
   SELECT * FROM products WHERE quantity < safety_stock;  -- 查看低库存
   SELECT op_type, SUM(quantity) FROM transactions GROUP BY op_type; -- 出入库汇总
   ```
5. 改完代码 Run 后，在表上 `Refresh`（或 `Ctrl+F5`）即可看到最新数据。

---

## 7. 打包 APK（在 PyCharm 内完成）

前置（仅打包机需要，开发调试不需要）：
- 安装 **Android SDK Command-line Tools**，配置：
  ```bash
  export ANDROID_HOME=$HOME/Android/Sdk
  export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
  sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
  ```
- 安装 **JDK 17** 并设 `JAVA_HOME`。
- `pip install flet`（命令行可用 `flet`）。

在 PyCharm 中执行（任选）：
- **Terminal**：`flet build apk`（产物 `build/apk/app-release.apk`）；
  按架构拆分：`flet build apk --split-per-abi`；发布商店用 `flet build aab`。
- **Run Configuration**：用本项目附的 `.run/build_apk.run.xml`
  （Python 配置，Module=`flet`，Parameters=`build apk`，`Emulate terminal`=开）。

> 相机权限已在 `pyproject.toml` 的 `[tool.flet]` 与 `[tool.flet.android.permission]` 配置，
> 构建时自动写入 `AndroidManifest.xml`。

---

## 8. 常见问题速查

| 现象 | 处理 |
|------|------|
| `from app...` 报红 | 右键 `app` → `Mark Directory as` → `Sources Root` |
| Run 报错 `No module named flet` | Python Interpreter 里确认已装 flet（用项目 venv） |
| 扫码页提示“未检测到相机” | 桌面正常，相机仅安卓/iOS/Web 支持 |
| `pyzbar` 解码报 `zbar` 缺失 | 安装系统 zbar 并加入 PATH（见第 2 步） |
| `app/inventory.db` 找不到 | 先 Run 一次 `main.py` 生成数据库 |
| Debug 不命中异步函数 | 勾选 Debug 窗 `Async stack trace`，对 `async def` 设断点 |
