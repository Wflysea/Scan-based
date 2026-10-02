"""Flet 1.0 API 静态校验工具（开发期用，不参与打包）。

在 CI/打包之前运行，可提前发现「本地能装、手机上一打开就崩」的那类问题：
  1. ft.X 名称是否存在（Flet 1.0 大量重命名，如 NavigationDestination -> NavigationBarDestination）
  2. ft.X(...) 的构造参数是否为该控件 dataclass 的合法字段
  3. page.xxx 成员是否存在（Flet 1.0 移除/改名，如 page.update_async 已删除）

用法（需已安装 flet==1.0.3 及扩展包）：
    python tests/check_flet_api.py
"""
import ast
import dataclasses
import inspect
import pathlib
import sys

try:
    import flet as ft
except ImportError:
    print("未安装 flet，请先：pip install flet==1.0.3")
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parent.parent  # 项目根目录


def resolve(node):
    """把 ast 节点 ft.X / ft.X.Y 解析成真实对象。"""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if not (isinstance(cur, ast.Name) and cur.id == "ft"):
        return None
    parts.reverse()
    obj = ft
    for p in parts:
        try:
            obj = getattr(obj, p)
        except Exception:
            return None
    return obj


def iter_app_files():
    for p in sorted(ROOT.rglob("*.py")):
        s = p.as_posix()
        rel = s[len(ROOT.as_posix()) + 1:]
        if rel.startswith(("build/", "tests/", "_")) or ".git" in rel:
            continue
        yield p, rel


# ── 1. ft.X 名称存在性 ───────────────────────────────────────────
name_problems = []
# ── 2. 构造参数合法性 ────────────────────────────────────────────
kwarg_problems = []
# ── 3. page.* 成员 ───────────────────────────────────────────────
page_problems = []

PAGE_MEMBERS = set(dir(ft.Page))

for path, rel in iter_app_files():
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)

    for node in ast.walk(tree):
        # 1) ft.X 名称
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "ft" and node.attr not in (
                "Icons", "Colors", "app", "run",
            ):
                try:
                    getattr(ft, node.attr)
                except AttributeError:
                    name_problems.append(
                        "{}:{}  ft.{}  <-- Flet 1.0 中不存在".format(
                            rel, node.lineno, node.attr
                        )
                    )

        # 2) ft.X(...) 构造参数
        if isinstance(node, ast.Call):
            obj = resolve(node.func)
            if obj is not None and inspect.isclass(obj):
                try:
                    fields = {f.name for f in dataclasses.fields(obj)}
                except Exception:
                    fields = None
                if fields:
                    for kw in node.keywords:
                        if kw.arg and kw.arg not in fields:
                            kwarg_problems.append(
                                "{}:{}  ft.{}({}=...)  <-- 未知参数".format(
                                    rel, node.lineno, obj.__name__, kw.arg
                                )
                            )

        # 3) page.xxx / self.page.xxx / self.app.page.xxx
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in ("page",) or node.attr and isinstance(
                node.value, ast.Attribute
            ) and node.value.attr == "page":
                if node.attr not in PAGE_MEMBERS:
                    page_problems.append(
                        "{}:{}  page.{}  <-- Page 无此成员".format(
                            rel, node.lineno, node.attr
                        )
                    )


def report(title, items):
    print("=== " + title + " ===")
    if items:
        for x in items:
            print("  [BAD]", x)
    else:
        print("  [OK]")
    print("")


report("1. ft.X 名称检查", name_problems)
report("2. 控件构造参数检查", kwarg_problems)
report("3. page.* 成员检查", page_problems)

print("=== 4. 关键控件实例化 ===")
cases = {
    "NavigationBarDestination": dict(icon=ft.Icons.HOME, label="home"),
    "NavigationBar": dict(selected_index=0),
    "AppBar": dict(title=ft.Text("t")),
    "SnackBar": dict(content=ft.Text("m")),
    "DropdownOption": dict(key="a", text="b"),
    "FilledButton": dict(content=ft.Text("x"), height=50),
    "TextField": dict(label="code", height=50, border_radius=10),
    "ProgressRing": dict(),
}
failed = 0
for name, kw in cases.items():
    try:
        getattr(ft, name)(**kw)
        print("  [OK] ft." + name)
    except Exception as e:
        failed += 1
        print("  [FAIL] ft.{}: {}: {}".format(name, type(e).__name__, e))

total = len(name_problems) + len(kwarg_problems) + len(page_problems) + failed
print("")
print("结论：" + ("发现 {} 个问题".format(total) if total else "全部通过"))
sys.exit(1 if total else 0)
