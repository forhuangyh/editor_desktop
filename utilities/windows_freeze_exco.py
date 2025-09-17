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
import zipfile
import paramiko
from cx_Freeze import Executable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import application_version


def compress_directory(directory_path):
    """将指定目录压缩成zip文件"""
    zip_filename = f"{directory_path}.zip"
    print(f"正在创建压缩文件: {zip_filename}")

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(directory_path)))

    print(f"压缩文件创建成功: {zip_filename}")
    return zip_filename


# 修改upload_to_remote_server方法中的路径构造部分
def upload_to_remote_server(local_file_path, ssh_host, ssh_port, ssh_username, ssh_password, remote_directory):
    """通过SSH将本地文件上传到远程服务器"""
    try:
        # 建立SSH连接
        print(f"正在连接到远程服务器: {ssh_host}")
        transport = paramiko.Transport((ssh_host, ssh_port))
        transport.connect(username=ssh_username, password=ssh_password)
        # 如果使用密钥文件，请使用以下代码
        # transport.connect(username=ssh_username, pkey=paramiko.RSAKey.from_private_key_file(ssh_key_file))

        # 创建SFTP客户端
        sftp = paramiko.SFTPClient.from_transport(transport)

        # 上传文件 - 修复路径分隔符问题
        file_name = os.path.basename(local_file_path)
        # 确保远程目录以正斜杠结尾
        if not remote_directory.endswith('/'):
            remote_directory += '/'
        # 使用字符串连接而不是os.path.join，确保使用正斜杠
        remote_file_path = f"{remote_directory}{file_name}"
        print(f"正在上传文件到: {remote_file_path}")
        sftp.put(local_file_path, remote_file_path)

        # 关闭连接
        sftp.close()
        transport.close()

        print("文件上传成功！")
        return True

    except Exception as e:
        print(f"上传文件时出错: {str(e)}")
        return False

def main():
    # 工程根目录
    file_directory = os.path.join(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
        "..",
    )
    # 修改输出目录定义
    output_directory = "editor_desktop_v{}_{}_{}".format(
        application_version,
        platform.system().lower(),
        platform.architecture()[0],
    )
    # 添加删除旧编译文件的功能
    print(f"检查是否存在旧的编译文件和文件夹...")

    # 检查并删除文件夹
    if os.path.exists(output_directory):
        print(f"删除旧的文件夹: {output_directory}")
        shutil.rmtree(output_directory)

    # 检查并删除zip文件
    zip_filename = f"{output_directory}.zip"
    if os.path.exists(zip_filename):
        print(f"删除旧的zip文件: {zip_filename}")
        os.remove(zip_filename)

    print(f"旧文件清理完成")
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

    # 调用压缩和上传功能
    # 1. 压缩目录
    zip_file = compress_directory(output_directory)

    # 2. 上传到远程服务器
    # 请根据实际情况修改以下配置
    ssh_host = '192.168.3.7'
    ssh_port = 22
    ssh_username = 'root'
    ssh_password = '123,abc'  # 或者使用密钥文件
    # ssh_key_file = '/path/to/your/private_key'
    remote_directory = '/home/www/editor_desktop_downloads/downloads'

    upload_to_remote_server(zip_file, ssh_host, ssh_port, ssh_username, ssh_password, remote_directory)


if __name__ == "__main__":
    main()
