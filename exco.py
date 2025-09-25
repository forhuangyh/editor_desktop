"""
Copyright (c) 2013-present Matic Kukovec.
Released under the GNU GPL3 license.

For more information check the 'LICENSE.txt' file.
For complete license information of the dependencies, check the 'additional_licenses' directory.
"""

# FILE DESCRIPTION:
# Execute this file to start Ex.Co.


import sys
import argparse
import traceback
import qt
import data
import settings
import functions
import components.fonts
import components.signaldispatcher
import components.processcontroller
import components.communicator
import components.thesquid
import gui.mainwindow
import xc_gui.login_window
from xc_entity import account


def parse_arguments():
    """
    Parse Ex.Co. command line arguments
    """

    # Nested function for input file parsing
    def parse_file_list(files_string):
        return files_string.split(";")

    # Initialize the argument parser
    arg_parser = argparse.ArgumentParser()
    # Version number
    arg_parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="Editor Version: {:s}".format(data.application_version),
    )
    # Debug mode
    arg_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        dest="debug_mode",
        help="Enable debug mode. Not used anymore.",
    )
    # Logging mode
    arg_parser.add_argument(
        "-l",
        "--logging",
        action="store_true",
        default=False,
        dest="logging_mode",
        help="Show the logging window on startup.",
    )
    # Logging mode
    arg_parser.add_argument(
        "-n",
        "--new",
        action="store_true",
        default=False,
        dest="new_document",
        help="""
                  Create a new document in the main window on startup.
                  This flag can be overriden with the --files flag.
                  """,
    )
    # Add a file group to the argument parser
    file_group = arg_parser.add_argument_group("input file options")
    # Input files
    file_group.add_argument(
        "-f",
        "--files",
        type=parse_file_list,
        help="""
                    List of files to open on startup, separated
                    by semicolons (';'). This flag overrides the --new flag.
                    """,
    )
    # Single file argument
    help_string = "Single file passed as an argument, "
    help_string += (
        'Used for openning files with a desktops "Open with..." functionality'
    )
    file_group.add_argument(
        "single_file", action="store", nargs="?", default=None, help=help_string
    )
    parsed_options = arg_parser.parse_args()
    return parsed_options


def main():
    """
    Main function of Ex.Co.
    """
    # 【新增】跨平台单实例控制：Windows 互斥锁 / macOS 锁文件
    import sys
    import os
    import tempfile
    import ctypes
    from ctypes import wintypes

    # 全局唯一标识（避免与其他应用冲突）
    APP_ID = "ExCo_Editor_Single_Instance"
    instance_exists = False
    lock_file = None

    # === Windows 平台：使用命名互斥锁 ===
    if sys.platform == "win32":
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.CreateMutexW.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE

        mutex_name = f"Global\\{APP_ID}_Mutex"  # Global 前缀确保系统级唯一性
        h_mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.get_last_error()
        if h_mutex == 0 or last_error == 183:  # 183 = ERROR_ALREADY_EXISTS
            instance_exists = True

    # === macOS 平台：使用临时目录锁文件 ===
    elif sys.platform == "darwin":
        lock_dir = tempfile.gettempdir()
        lock_file_path = os.path.join(lock_dir, f"{APP_ID}.lock")
        try:
            import fcntl
            # 尝试创建独占锁文件（不存在则创建，存在则抛异常）
            lock_file = open(lock_file_path, 'w')
            # 获取文件独占锁（防止其他进程删除）
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (FileExistsError, BlockingIOError):
            instance_exists = True
        except Exception as e:
            print(f"macOS 锁文件创建失败: {str(e)}")

    # === 检测到已有实例：发送唤起指令并退出 ===
    if instance_exists:
        try:
            # 发送 "显示窗口" 指令给已有实例
            _data = {"command": "show", "arguments": None}
            fc = components.communicator.FileCommunicator("SHOW-OPEN-INSTANCE")
            fc.send_data(_data)
            import time
            time.sleep(0.5)  # 确保指令发送完成
        except Exception as e:
            print(f"唤起已有实例失败: {str(e)}")
        finally:
            if lock_file:
                lock_file.close()  # 关闭 macOS 锁文件
            sys.exit(0)  # 退出当前实例

    # Check arguments
    options = parse_arguments()
    data.command_line_options = options
    if options.debug_mode == True:
        data.debug_mode = True
    else:
        # Redirect output to a file
        try:
            functions.output_redirect()
        except:
            traceback.print_exc()
    if options.logging_mode == True:
        data.logging_mode = True
    file_arguments = options.files
    if options.single_file is not None:
        if file_arguments is not None:
            file_list = file_arguments.split(";")
            file_list.append(options.single_file)
            file_arguments = ";".join(file_list)
        else:
            file_arguments = [options.single_file]
    if file_arguments == [""]:
        file_arguments = None

    # Create QT application, needed to use QT forms
    app = qt.QApplication(sys.argv)
    # Save the Qt application to the global reference
    data.application = app
    # Create a proxy style
    data.application.setStyle("Fusion")

    # Process control
    number_of_instances = components.processcontroller.check_opened_excos()
    if settings.get("open-new-files-in-open-instance"):
        if number_of_instances > 1 and file_arguments is not None:
            try:
                _data = {"command": "open", "arguments": file_arguments}
                #                components.processcontroller.send_raw_command(_data)
                fc = components.communicator.FileCommunicator(
                    "OPEN-IN-EXISTING-INSTANCE"
                )
                fc.send_data(_data)
                return
            except:
                pass
        elif number_of_instances > 1:
            try:
                _data = {"command": "show", "arguments": None}
                fc = components.communicator.FileCommunicator("SHOW-OPEN-INSTANCE")
                fc.send_data(_data)
                return
            except:
                pass

    # Set default application font
    components.fonts.set_application_font(
        settings.get("current_font_name"),
        settings.get("current_font_size"),
    )
    # Global signal dispatcher
    data.signal_dispatcher = components.signaldispatcher.GlobalSignalDispatcher()

    # 在创建MainWindow之前显示登录窗口
    login_window = xc_gui.login_window.LoginWindow()
    if login_window.exec() != qt.QDialog.DialogCode.Accepted:
        # 如果用户取消登录或关闭窗口，直接退出应用程序
        sys.exit(0)

    # 登录成功后，确保用户信息已正确加载
    if not account.user_info.token:
        print("登录验证失败，退出应用程序")
        sys.exit(0)

    # Create the main window, pass the filename that may have been passed as an argument
    main_window = gui.mainwindow.MainWindow(
        new_document=options.new_document,
        logging=data.logging_mode,
        file_arguments=file_arguments,
        user_info=account.user_info,  # 传递用户信息
    )
    components.thesquid.TheSquid.init_objects(main_window)
    main_window.import_user_functions()
    main_window.show()
    result = app.exec()
    functions.output_backup()
    sys.exit(result)


# Check if this is the main executing script
if __name__ == "__main__":
    main()
elif "__main__" in __name__:
    # cx_freeze mangles the __name__ variable,
    # but it still contains '__main__'
    main()
