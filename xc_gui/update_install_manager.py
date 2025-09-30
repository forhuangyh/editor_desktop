import os
import sys
import subprocess
import logging
from PyQt6 import QtWidgets as qt
from PyQt6 import QtCore
from xc_service.update_software_service import UpdateSoftwareService

logger = logging.getLogger(__name__)

class UpdateInstallManager:
    """更新安装管理器 - 负责版本检查和更新程序启动"""

    def __init__(self, parent_window=None):
        """初始化更新安装管理器

        Args:
            parent_window: 父窗口，用于模态对话框显示
        """
        self.parent_window = parent_window
        self.update_service = UpdateSoftwareService()

    def check_for_updates_and_prompt(self):
        """检查是否有新版本并提示用户

        Returns:
            bool: 是否执行了更新操作
        """
        try:
            # 调用更新服务检查更新
            download_url, latest_version = self.update_service.check_update()

            # 有新版本时的处理
            if download_url:
                logger.info(f"发现新版本，下载地址: {download_url}")
                return self._prompt_user_and_update(download_url, latest_version)
            else:
                logger.info("当前版本是最新的")
                return False
        except Exception as e:
            logger.error(f"检查更新时发生错误: {str(e)}")
            self._show_error_dialog("检查更新失败", f"无法连接到更新服务器: {str(e)}")
            return False

    def _prompt_user_and_update(self, download_url, latest_version):
        """显示更新提示对话框并根据用户选择执行更新

        Args:
            download_url: 新版本下载地址

        Returns:
            bool: 是否执行了更新操作
        """
        # 创建消息框实例
        msg_box = qt.QMessageBox(self.parent_window)
        msg_box.setWindowTitle("版本更新提示")
        # 使用HTML设置下载地址字体变小
        msg_box.setTextFormat(QtCore.Qt.TextFormat.RichText)  # 修复这里，使用QtCore.Qt
        msg_box.setText(f"发现新版本，最新版本号:  {latest_version} <br> 下载地址: <br>  <span style='font-size:14px;'>{download_url}</span>")
        msg_box.setIcon(qt.QMessageBox.Icon.Information)
        # 添加自定义文本的"确定"按钮
        confirm_button = msg_box.addButton("确认更新", qt.QMessageBox.ButtonRole.AcceptRole)

        # 显示消息框
        msg_box.exec()

        # 用户点击了确定按钮，执行更新
        try:
            logger.info(f"用户选择安装新版本，下载地址: {download_url}")
            return self._launch_update_program(download_url)
        except Exception as e:
            logger.error(f"执行更新时发生错误: {str(e)}")
            return False

    def _launch_update_program(self, download_url):
        """启动更新程序

        Args:
            download_url: 新版本下载地址

        Returns:
            bool: 更新程序是否成功启动
        """
        try:
            # 获取应用程序目录
            app_dir = self._get_app_directory()
            logger.info(f"获取到的应用程序目录: {app_dir}")

            # 搜索更新程序
            update_program_exe = self._find_update_program(app_dir)

            if not update_program_exe:
                raise FileNotFoundError("无法找到更新程序")

            # 启动更新程序并传递下载链接
            logger.info(f"启动更新程序: {update_program_exe}，参数: {download_url}")
            subprocess.Popen([update_program_exe, download_url])

            # 退出主程序
            sys.exit(0)

            # 返回True表示成功启动更新程序
            return True

        except Exception as e:
            logger.error(f"启动更新程序失败: {str(e)}")
            self._show_error_dialog("更新失败", f"更新程序启动失败，请检查日志文件。\n错误: {str(e)}")
            return False

    def _get_app_directory(self):
        """获取应用程序目录

        Returns:
            str: 应用程序目录路径
        """
        if hasattr(sys, 'frozen'):
            # 打包后的环境
            return os.path.dirname(sys.executable)
        else:
            # 开发环境
            return os.path.dirname(os.path.abspath(__file__))

    def _find_update_program(self, app_dir):
        """搜索更新程序

        Args:
            app_dir: 应用程序目录

        Returns:
            str: 更新程序路径，如果未找到则返回None
        """
        # 扩展可能的更新程序路径，增加多个搜索位置
        possible_paths = [
            os.path.join(app_dir, 'update_program.exe'),  # 主程序同级目录（打包后位置）
            os.path.join(app_dir, 'utilities', 'update_program.exe'),  # 开发环境位置
            os.path.join(os.getcwd(), 'update_program.exe'),  # 当前工作目录
            # 检查打包输出目录
            os.path.join(os.path.dirname(app_dir), 'update_program.exe'),
        ]

        # 遍历搜索路径
        update_program_exe = None
        for path in possible_paths:
            if os.path.exists(path):
                update_program_exe = path
                logger.info(f"找到更新程序: {update_program_exe}")
                break

        logger.info(f"搜索更新程序路径: {possible_paths}")

        # 尝试使用系统路径查找
        if not update_program_exe:
            try:
                # 检查是否在PATH环境变量中
                import shutil
                update_program_exe = shutil.which('update_program.exe')
                if update_program_exe:
                    logger.info(f"从系统路径找到更新程序: {update_program_exe}")
            except:
                pass

        return update_program_exe

    def _show_error_dialog(self, title, message):
        """显示错误对话框

        Args:
            title: 对话框标题
            message: 错误消息内容
        """
        qt.QMessageBox.critical(
            self.parent_window,
            title, message
        )
