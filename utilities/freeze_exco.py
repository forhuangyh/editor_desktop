"""
Copyright (c) 2013-present Matic Kukovec.
Released under the GNU GPL3 license.

For more information check the 'LICENSE.txt' file.
For complete license information of the dependencies, check the 'additional_licenses' directory.
"""

import os
import sys
import pprint
import shutil
import inspect
import platform
import glob
import black
import cx_Freeze
from cx_Freeze import Executable


def main():
    # 工程根目录
    file_directory = os.path.join(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
        "..",
    )
    output_directory = "frozen_exco_{}_{}".format(
        platform.system().lower(),
        platform.architecture()[0],
    )

    # 内置模块
    builtin_modules = [
        "PyQt6",
        "PyQt6.Qsci",
        "PyQt6.QtTest",
        "pyte",
        "hy",
        "hy.core",
        "hy.core.result_macros",
        "black",
        "autopep8",
        "yapf",
        "fpdf",
    ]

    # 本地模块收集
    local_modules = []
    exclude_dirs = ["cython", "nim", "utilities", "git_clone"]
    excluded_modules = ["freeze_exco", "git_clone"]

    for root, dirs, files in os.walk(file_directory):
        base_path = os.path.relpath(root, file_directory)  # 相对路径
        if base_path == ".":
            base_path = ""  # 根目录特殊处理

        if any(x in base_path for x in exclude_dirs):
            continue

        for f in files:
            if f.endswith(".py"):
                raw_module = f.replace(".py", "")
                if base_path:
                    new_module = f"{base_path}.{raw_module}"
                else:
                    new_module = raw_module

                new_module = new_module.replace("\\", ".").replace("/", ".")
                if new_module in excluded_modules:
                    continue
                local_modules.append(new_module)

    pprint.pprint(local_modules)
    modules = local_modules + builtin_modules

    # --- 强制包含 black 的 mypyc 扩展 ---
    black_path = os.path.dirname(black.__file__)
    mypyc_files = glob.glob(os.path.join(black_path, "*.pyd"))

    # 构造 include_files
    extra_include_files = [
        (os.path.abspath(p), os.path.join("lib", "black", os.path.basename(p)))
        for p in mypyc_files
    ]
    include_files = [(os.path.abspath(black_path), os.path.join("lib", "black"))] + extra_include_files

    # 检查缺失文件
    missing = [src for src, _ in include_files if not os.path.exists(src)]
    if missing:
        raise FileNotFoundError(f"这些源路径不存在，无法复制: {missing}")

    # 搜索路径
    search_path = sys.path + [file_directory]

    base = None
    excludes = ["tkinter"]
    executable_name = "ExCo"

    if platform.system().lower() == "windows":
        base = "Win32GUI"
        builtin_modules.extend(
            ["win32api", "win32con", "win32gui", "win32file", "winpty"]
        )
        excludes += [
            "PyQt5",
            "PyQt5.QtCore",
            "PyQt5.QtWidgets",
            "PyQt5.QtGui",
            "PyQt5.Qsci",
            "PyQt5.QtTest",
        ]
        executable_name = "ExCo.exe"

    elif platform.system().lower() == "linux":
        builtin_modules.extend(["ptyprocess"])

    # 要冻结的可执行文件
    executables = [
        Executable(
            os.path.join(file_directory, "exco.py"),
            base=base,
            icon="resources/exco-icon-win.ico",
            target_name=executable_name,
        )
    ]

    freezer = cx_Freeze.Freezer(
        executables,
        includes=modules,
        excludes=excludes,
        replace_paths=[],
        compress=True,
        optimize=True,
        include_msvcr=True,
        path=search_path,
        target_dir=output_directory,
        include_files=include_files,
        zip_includes=[],
        silent=False,
    )
    freezer.freeze()

    # 拷贝资源
    resources_dir = os.path.join(file_directory, "resources")
    if os.path.exists(resources_dir):
        shutil.copytree(resources_dir, os.path.join(output_directory, "resources"))
    else:
        print(f"[警告] 未找到资源目录: {resources_dir}")


if __name__ == "__main__":
    main()
