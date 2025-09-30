#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新程序 - 负责下载和解压更新包，然后重新启动主程序
"""
import os
import sys

# 在导入其他模块前，确保在Windows下以窗口模式运行（无控制台窗口）
if os.name == 'nt':  # 仅在Windows系统上执行
    try:
        # 设置Windows应用程序类型，防止显示控制台窗口
        import ctypes

        ctypes.windll.kernel32.SetConsoleTitleW("程序更新")
        # 以下代码可以隐藏已有的控制台窗口
        # ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

import logging
import tempfile
import time
import zipfile
import shutil
import subprocess
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QLabel, QProgressBar, QTextEdit, QWidget, QPushButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


# 设置日志配置 - 确保在任何环境下都能正确记录日志
def setup_logging():
    # 获取当前执行文件的目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的程序，使用可执行文件所在目录
        current_dir = os.path.dirname(sys.executable)
    else:
        # 否则使用脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))

    # 定义日志目录优先级，添加当前执行文件目录下的.exco/logs
    log_dirs = [
        os.path.join(current_dir, "updatelogs", "log"),  # 当前执行文件目录下的.exco/logs
        os.path.join(os.path.expanduser("~"), ".exco_editor", "logs"),  # 用户目录
        os.path.join(os.getenv("TEMP", "."), ".exco_editor", "logs"),  # 临时目录
        os.path.join(os.getcwd(), "logs")  # 当前目录
    ]

    log_file = None
    for log_dir in log_dirs:
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "update.log")
            # 不再打印日志文件路径到控制台，因为我们要隐藏控制台
            break
        except Exception as e:
            # 不再打印错误信息到控制台
            pass

    # 如果所有目录都失败，使用当前目录下的简单文件名
    if log_file is None:
        log_file = "update.log"

    # 配置日志只输出到文件（不输出到控制台）
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file)
            # 移除StreamHandler，避免输出到控制台
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成")
    logger.debug(f"当前工作目录: {os.getcwd()}")
    logger.debug(f"Python解释器: {sys.executable}")
    logger.debug(f"命令行参数: {sys.argv}")
    logger.debug(f"当前执行文件目录: {current_dir}")

    # 检查是否在PyInstaller打包环境中
    if getattr(sys, 'frozen', False):
        logger.debug(f"正在运行打包后的程序，临时目录: {sys._MEIPASS}")

    return logger


# 初始化日志系统
logger = setup_logging()


# 下载更新包
def download_update(download_url, save_path, progress_callback=None, status_callback=None):
    """
    下载更新包
    :param download_url: 更新包下载链接
    :param save_path: 保存路径
    :param progress_callback: 进度回调函数
    :param status_callback: 状态回调函数
    """
    try:
        logger.info(f"开始下载更新包: {download_url}")
        if status_callback:
            status_callback(f"开始下载更新包")

        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(save_path, 'wb') as file:
            for data_chunk in response.iter_content(chunk_size=8192):
                if data_chunk:
                    file.write(data_chunk)
                    downloaded_size += len(data_chunk)

                    # 显示下载进度
                    if total_size > 0 and progress_callback:
                        progress = int((downloaded_size / total_size) * 100)
                        progress_callback(progress)

        logger.info(f"更新包下载完成，保存路径: {save_path}")
        if status_callback:
            status_callback("更新包下载完成")
        return True
    except Exception as e:
        logger.error(f"下载更新包失败: {str(e)}")
        if status_callback:
            status_callback(f"下载失败: {str(e)}")
        return False


# 解压更新包
def unzip_update(zip_path, extract_dir, progress_callback=None, status_callback=None, file_callback=None):
    """
    解压更新包，智能处理ZIP内部目录结构
    特别处理：.dll库文件发现重名时不覆盖，其他文件正常覆盖
    增加：打印覆盖文件名称及覆盖状态
    :param zip_path: 压缩包路径
    :param extract_dir: 解压目录
    :param progress_callback: 进度回调函数
    :param status_callback: 状态回调函数
    :param file_callback: 文件处理回调函数
    """
    try:
        logger.info(f"开始解压更新包: {zip_path}")
        logger.info(f"解压到: {extract_dir}")
        if status_callback:
            status_callback("开始解压更新包")

        # 确保解压目录存在
        os.makedirs(extract_dir, exist_ok=True)

        # 用于记录成功覆盖和失败覆盖的文件
        successfully_overwritten = []
        failed_overwritten = []
        skipped_dll_files = []

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取zip中的所有文件和目录
            zip_contents = zip_ref.namelist()
            total_files = len([f for f in zip_contents if not (f.endswith('/') or f.endswith('\\'))])
            processed_files = 0

            # 检查ZIP文件是否只有一个顶层目录
            top_level_dirs = set()
            for item in zip_contents:
                # 获取顶级目录名称（去掉文件名和路径分隔符）
                if '/' in item or '\\' in item:
                    first_part = item.split('/')[0] if '/' in item else item.split('\\')[0]
                    if first_part:
                        top_level_dirs.add(first_part)

            # 判断是否需要扁平化目录结构
            flatten_structure = len(top_level_dirs) == 1 and any(item.startswith(next(iter(top_level_dirs)) + '/') or \
                                                                 item.startswith(next(iter(top_level_dirs)) + '\\') \
                                                                 for item in zip_contents)

            if flatten_structure:
                logger.info(f"检测到ZIP文件包含单一顶层目录，将直接解压内容到目标目录")
                main_dir = next(iter(top_level_dirs))
                # 只解压主目录下的内容
                for item in zip_contents:
                    if item.startswith(main_dir + '/') or item.startswith(main_dir + '\\'):
                        # 去掉主目录前缀
                        target_name = item[len(main_dir) + 1:]
                        if target_name:  # 确保不是空字符串
                            target_path = os.path.join(extract_dir, target_name)

                            # 检查是否是目录
                            if item.endswith('/') or item.endswith('\\'):
                                os.makedirs(target_path, exist_ok=True)
                            else:
                                # 检查文件是否为.dll，且已存在
                                is_dll_file = target_path.lower().endswith('.dll')
                                if is_dll_file and os.path.exists(target_path):
                                    logger.info(f"跳过覆盖已存在的.dll文件: {target_path}")
                                    skipped_dll_files.append(target_path)
                                    if file_callback:
                                        file_callback(f"跳过.dll文件: {os.path.basename(target_path)}")
                                    continue

                                # 检查文件是否存在（用于记录覆盖信息）
                                file_exists = os.path.exists(target_path)
                                if file_exists:
                                    logger.info(f"准备覆盖文件: {target_path}")
                                    if file_callback:
                                        file_callback(f"准备覆盖: {os.path.basename(target_path)}")
                                else:
                                    if file_callback:
                                        file_callback(f"创建文件: {os.path.basename(target_path)}")

                                # 确保目标文件的目录存在
                                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                                # 解压文件（带重试机制）- 非.dll文件或.dll文件不存在
                                max_retries = 3
                                retry_count = 0
                                success = False

                                while retry_count < max_retries and not success:
                                    try:
                                        with zip_ref.open(item) as source, open(target_path, 'wb') as target:
                                            shutil.copyfileobj(source, target)
                                        success = True
                                        processed_files += 1
                                        if progress_callback:
                                            progress_callback(int((processed_files / total_files) * 100))
                                        if file_exists:
                                            logger.info(f"文件覆盖成功: {target_path}")
                                            successfully_overwritten.append(target_path)
                                            if file_callback:
                                                file_callback(f"覆盖成功: {os.path.basename(target_path)}")
                                        else:
                                            logger.info(f"文件创建成功: {target_path}")
                                            if file_callback:
                                                file_callback(f"创建成功: {os.path.basename(target_path)}")
                                    except PermissionError as e:
                                        retry_count += 1
                                        if retry_count >= max_retries:
                                            logger.error(f"无法解压文件: {target_path}，权限被拒绝")
                                            failed_overwritten.append((target_path, "权限被拒绝"))
                                            if file_callback:
                                                file_callback(f"覆盖失败: {os.path.basename(target_path)} - 权限被拒绝")
                                            # 遇到权限错误直接抛出异常，导致解压失败
                                            raise
                                        else:
                                            logger.warning(
                                                f"解压文件失败，正在重试 ({retry_count}/{max_retries}): {target_path}")
                                            if file_callback:
                                                file_callback(
                                                    f"重试解压: {os.path.basename(target_path)} ({retry_count}/{max_retries})")
                                            time.sleep(1)  # 等待1秒后重试
                                    except Exception as e:
                                        logger.error(f"解压文件时出错: {target_path} - {str(e)}")
                                        failed_overwritten.append((target_path, str(e)))
                                        if file_callback:
                                            file_callback(f"解压失败: {os.path.basename(target_path)} - {str(e)}")
                                        # 遇到其他异常直接失败
                                        raise
                logger.info(f"成功解压ZIP文件内容（跳过单一顶层目录）")
            else:
                # 使用原始逻辑，直接解压所有文件
                # 解压前检查冲突文件
                for file_name in zip_contents:
                    # 跳过目录
                    if file_name.endswith('/') or file_name.endswith('\\'):
                        continue

                    target_path = os.path.join(extract_dir, file_name)
                    # 检查是否为.dll文件且已存在
                    is_dll_file = target_path.lower().endswith('.dll')
                    if is_dll_file and os.path.exists(target_path):
                        logger.info(f"跳过覆盖已存在的.dll文件: {target_path}")
                        skipped_dll_files.append(target_path)
                        if file_callback:
                            file_callback(f"跳过.dll文件: {os.path.basename(target_path)}")

                # 解压所有文件（不覆盖.dll文件）
                try:
                    # 先收集所有不是.dll或.dll不存在的文件
                    files_to_extract = []
                    for file_name in zip_contents:
                        if file_name.endswith('/') or file_name.endswith('\\'):  # 总是解压目录
                            files_to_extract.append(file_name)
                        else:
                            target_path = os.path.join(extract_dir, file_name)
                            is_dll_file = target_path.lower().endswith('.dll')
                            if not is_dll_file or not os.path.exists(target_path):
                                files_to_extract.append(file_name)

                    # 逐个解压文件
                    for file_name in files_to_extract:
                        if not file_name.endswith('/') and not file_name.endswith('\\'):  # 不是目录
                            target_path = os.path.join(extract_dir, file_name)
                            # 检查文件是否存在（用于记录覆盖信息）
                            file_exists = os.path.exists(target_path)
                            if file_exists:
                                logger.info(f"准备覆盖文件: {target_path}")
                                if file_callback:
                                    file_callback(f"准备覆盖: {os.path.basename(target_path)}")
                            else:
                                if file_callback:
                                    file_callback(f"创建文件: {os.path.basename(target_path)}")

                            max_retries = 3
                            retry_count = 0
                            success = False
                            while retry_count < max_retries and not success:
                                try:
                                    zip_ref.extract(file_name, extract_dir)
                                    success = True
                                    processed_files += 1
                                    if progress_callback:
                                        progress_callback(int((processed_files / total_files) * 100))
                                    if file_exists:
                                        logger.info(f"文件覆盖成功: {target_path}")
                                        successfully_overwritten.append(target_path)
                                        if file_callback:
                                            file_callback(f"覆盖成功: {os.path.basename(target_path)}")
                                    else:
                                        logger.info(f"文件创建成功: {target_path}")
                                        if file_callback:
                                            file_callback(f"创建成功: {os.path.basename(target_path)}")
                                except PermissionError:
                                    retry_count += 1
                                    if retry_count >= max_retries:
                                        logger.error(f"无法解压文件: {target_path}")
                                        failed_overwritten.append((target_path, "权限被拒绝"))
                                        if file_callback:
                                            file_callback(f"覆盖失败: {os.path.basename(target_path)} - 权限被拒绝")
                                        # 遇到权限错误直接抛出异常，导致解压失败
                                        raise
                                    else:
                                        if file_callback:
                                            file_callback(
                                                f"重试解压: {os.path.basename(target_path)} ({retry_count}/{max_retries})")
                                        time.sleep(1)
                    logger.info(f"成功解压 {len(files_to_extract)} 个文件")
                except PermissionError as e:
                    logger.error(f"解压文件时权限被拒绝: {str(e)}")
                    failed_overwritten.append((target_path, str(e)))
                    if file_callback:
                        file_callback(f"解压失败: {os.path.basename(target_path)} - {str(e)}")
                    # 直接抛出异常导致解压失败
                    raise
                except Exception as e:
                    logger.error(f"解压文件时出错: {str(e)}")
                    failed_overwritten.append((target_path, str(e)))
                    if file_callback:
                        file_callback(f"解压失败: {os.path.basename(target_path)} - {str(e)}")
                    raise

        # 打印覆盖结果统计
        logger.info("===== 解压更新结果统计 ====")
        logger.info(f"成功覆盖的文件数量: {len(successfully_overwritten)}")
        for file_path in successfully_overwritten:
            logger.info(f"✓ {file_path}")

        if skipped_dll_files:
            logger.info(f"跳过覆盖的.dll文件数量: {len(skipped_dll_files)}")
            for file_path in skipped_dll_files:
                logger.info(f"↗ {file_path}")

        if failed_overwritten:
            logger.error(f"覆盖失败的文件数量: {len(failed_overwritten)}")
            for file_path, error in failed_overwritten:
                logger.error(f"✗ {file_path} - {error}")

        logger.info("========================")
        logger.info("更新包解压完成")

        if status_callback:
            status_text = f"解压完成！成功: {len(successfully_overwritten)}, 跳过: {len(skipped_dll_files)}, 失败: {len(failed_overwritten)}"
            status_callback(status_text)

        return True
    except Exception as e:
        logger.error(f"解压更新包失败: {str(e)}")
        if status_callback:
            status_callback(f"解压失败: {str(e)}")
        return False


# 获取主程序路径
def get_main_program_path():
    """\获取主程序路径"""
    # 假设主程序与更新程序在同一目录下
    main_program = "EditorDesktop.exe"
    main_program_path = os.path.join(os.getcwd(), main_program)

    # 检查主程序是否存在
    if os.path.exists(main_program_path):
        return main_program_path

    logger.warning(f"未找到主程序: {main_program_path}")
    return None


# 重启主程序
def restart_main_program():
    """重启主程序"""
    main_program_path = get_main_program_path()
    if main_program_path:
        try:
            logger.info(f"重启主程序: {main_program_path}")
            subprocess.Popen([main_program_path])
            return True
        except Exception as e:
            logger.error(f"重启主程序失败: {str(e)}")
    return False


# 更新线程类
class UpdateThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    file_processed = pyqtSignal(str)
    update_completed = pyqtSignal(bool, str)
    phase_changed = pyqtSignal(str)  # 用于区分下载和解压阶段

    def __init__(self, download_url, program_dir, temp_dir):
        super().__init__()
        self.download_url = download_url
        self.program_dir = program_dir
        self.temp_dir = temp_dir
        self.update_zip_path = os.path.join(temp_dir, "update.zip")

    def run(self):
        try:
            # 第一阶段：下载更新包
            self.phase_changed.emit("下载更新包")
            self.status_updated.emit("准备下载更新包...")
            download_success = download_update(
                self.download_url,
                self.update_zip_path,
                progress_callback=lambda p: self.progress_updated.emit(p),
                status_callback=lambda s: self.status_updated.emit(s)
            )

            if not download_success:
                self.update_completed.emit(False, "下载更新包失败")
                return

            # 第二阶段：解压更新包
            self.phase_changed.emit("解压更新包")
            self.status_updated.emit("准备解压更新包...")
            unzip_success = unzip_update(
                self.update_zip_path,
                self.program_dir,
                progress_callback=lambda p: self.progress_updated.emit(p),
                status_callback=lambda s: self.status_updated.emit(s),
                file_callback=lambda f: self.file_processed.emit(f)
            )

            if not unzip_success:
                self.update_completed.emit(False, "解压更新包失败")
                return

            # 清理临时目录
            try:
                if os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                    logger.info(f"已清理临时目录: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {str(e)}")

            # 更新完成
            self.update_completed.emit(True, "更新完成")
        except Exception as e:
            logger.error(f"更新过程中发生错误: {str(e)}")
            self.update_completed.emit(False, str(e))


# 更新窗口类
class UpdateWindow(QMainWindow):
    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

        # 获取程序目录
        if getattr(sys, 'frozen', False):
            self.program_dir = os.path.dirname(sys.executable)
        else:
            self.program_dir = os.path.dirname(os.path.abspath(__file__))

        # 创建临时目录
        self.temp_dir = os.path.join(self.program_dir, "update_temp")
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            logger.info(f"创建临时目录: {self.temp_dir}")
        except Exception as e:
            logger.error(f"创建临时目录失败: {str(e)}")

        self.init_ui()
        self.start_update()

    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle("程序更新")
        self.setGeometry(300, 300, 600, 400)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint)

        # 创建主布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        self.setCentralWidget(central_widget)

        # 创建标题标签
        self.title_label = QLabel("程序更新")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        # 创建阶段标签
        self.phase_label = QLabel("")
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.phase_label)

        # 创建状态标签
        self.status_label = QLabel("准备更新...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        # 创建进度百分比标签
        self.percentage_label = QLabel("0%")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.percentage_label)

        # 创建文件处理日志文本框
        self.file_log_text = QTextEdit()
        self.file_log_text.setReadOnly(True)
        self.file_log_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.file_log_text.setPlaceholderText("更新过程日志将显示在这里...")
        main_layout.addWidget(self.file_log_text)

    def start_update(self):
        # 创建更新线程
        self.update_thread = UpdateThread(
            self.download_url,
            self.program_dir,
            self.temp_dir
        )

        # 连接信号和槽
        self.update_thread.progress_updated.connect(self.update_progress)
        self.update_thread.status_updated.connect(self.update_status)
        self.update_thread.file_processed.connect(self.add_file_log)
        self.update_thread.update_completed.connect(self.update_finished)
        self.update_thread.phase_changed.connect(self.update_phase)

        # 启动线程
        self.update_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.percentage_label.setText(f"{value}%")

    def update_status(self, status):
        self.status_label.setText(status)

    def update_phase(self, phase):
        self.phase_label.setText(phase)
        # 重置进度条用于新阶段
        self.progress_bar.setValue(0)
        self.percentage_label.setText("0%")

    def add_file_log(self, log_text):
        # 在文本框中添加日志，并自动滚动到底部
        self.file_log_text.append(log_text)
        self.file_log_text.verticalScrollBar().setValue(
            self.file_log_text.verticalScrollBar().maximum()
        )

    def update_finished(self, success, message):
        if success:
            self.status_label.setText("更新完成，准备重启程序...")
            logger.info("更新完成，准备重启主程序")

            # 重启主程序
            if not restart_main_program():
                logger.error("重启主程序失败，请手动启动")
                self.status_label.setText("更新完成，但重启主程序失败，请手动启动")
            else:
                # 延迟关闭更新窗口
                QApplication.processEvents()
                time.sleep(2)
                self.close()
        else:
            self.status_label.setText(f"更新失败: {message}")
            logger.error(f"更新失败: {message}")

    def closeEvent(self, event):
        # 确保线程已经结束
        if hasattr(self, 'update_thread') and self.update_thread.isRunning():
            # 这里可以添加确认对话框，询问用户是否真的要取消更新
            logger.warning("用户取消了更新")
            # 等待线程结束（可选）
            # self.update_thread.wait()
        event.accept()


# 修改主程序入口部分，替换临时目录的使用
if __name__ == '__main__':
    # 如果有测试参数，执行简单测试
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 在测试模式下也不显示控制台输出
        logger.info("执行测试模式...")
        # 创建Qt应用程序进行测试
        app = QApplication(sys.argv)
        update_window = UpdateWindow("https://example.com/test_update.zip")
        update_window.show()
        sys.exit(app.exec())
    else:
        # 完整的更新逻辑
        logger.info("更新程序启动")

        # 检查命令行参数
        if len(sys.argv) < 2:
            logger.error("缺少更新包下载链接参数")
            # 创建一个简单的错误提示窗口
            app = QApplication(sys.argv)
            error_window = QWidget()
            error_window.setWindowTitle("错误")
            error_window.setGeometry(300, 300, 300, 100)
            layout = QVBoxLayout(error_window)
            error_label = QLabel("缺少更新包下载链接参数\n用法: update_program.exe <更新包下载链接>")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)
            error_window.show()
            sys.exit(app.exec())

        download_url = sys.argv[1]
        logger.info(f"获取到更新包下载链接: {download_url}")

        # 创建Qt应用程序
        app = QApplication(sys.argv)

        # 设置应用程序样式（如果需要）
        # app.setStyle("Fusion")  # 可以根据需要设置样式

        # 创建更新窗口
        update_window = UpdateWindow(download_url)
        update_window.show()

        # 运行应用程序
        sys.exit(app.exec())