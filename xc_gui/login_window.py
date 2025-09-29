"""
Copyright (c) 2013-present Matic Kukovec.
Released under the GNU GPL3 license.

For more information check the 'LICENSE.txt' file.
For complete license information of the dependencies, check the 'additional_licenses' directory.
"""

import os
import qt
import data
import settings
from xc_service.account_service import AccountService
from xc_service.sqlite_service import SQLiteService, sqlite_service
from settings.constants import version_type
from xc_common.logger import get_logger
# 获取模块专属logger
logger = get_logger("login_window")

class LoginWindow(qt.QDialog):
    """
    Login dialog window that appears before the main application window
    """
    # Signals
    login_successful = qt.pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialization routine for the login window
        """
        super().__init__(parent)

        # Set window properties
        self.setWindowTitle("Editor Desktop. - 登录")
        self.setWindowIcon(qt.QIcon(data.application_icon) if os.path.isfile(data.application_icon) else qt.QIcon())
        self.setMinimumSize(700, 500)
        self.setWindowFlag(qt.Qt.WindowType.WindowCloseButtonHint, True)
        self.setWindowFlag(qt.Qt.WindowType.WindowSystemMenuHint, True)

        # Set font - 这里不修改全局字体，而是在各个组件中单独设置
        self.setFont(settings.get_current_font())

        # Initialize UI components
        self.init_ui()
        self.init_loading_mask()

        # Connect signals
        self.login_button.clicked.connect(self.check_credentials)
        self.cancel_button.clicked.connect(self.reject)
        self.password_edit.returnPressed.connect(self.check_credentials)
        self.username_edit.returnPressed.connect(self.check_credentials)

        # Center the window on screen
        self.center_on_screen()
        # 尝试从设置中加载记住的账号密码
        self.load_saved_credentials()

    def init_ui(self):
        """
        Initialize the UI components of the login window
        """
        # Main layout
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)  # 增大主布局边距，使所有元素远离边框
        main_layout.setSpacing(25)  # 增大组件间距

        # Logo and title
        title_layout = qt.QVBoxLayout()
        title_layout.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        # Create a simple logo since we don't have an actual logo
        logo_label = qt.QLabel()
        logo_label.setText("Editor Desktop.")
        logo_font = qt.QFont(logo_label.font())
        logo_font.setPointSize(42)  # 增大标题字体
        logo_font.setBold(True)
        logo_label.setFont(logo_font)
        logo_label.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)
        if version_type == "dev":
            title_label = qt.QLabel("开发版 - 版本 {:s}".format(data.application_version))
        else:
            title_label = qt.QLabel("发布版 - 版本 {:s}".format(data.application_version))

        title_font = qt.QFont(title_label.font())
        title_font.setPointSize(18)  # 增大版本号字体
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)

        # Login form layout
        form_layout = qt.QFormLayout()
        form_layout.setFieldGrowthPolicy(qt.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setFormAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        # 创建标签字体
        label_font = qt.QFont()
        label_font.setPointSize(16)  # 设置表单标签字体大小

        # Username field
        self.username_edit = qt.QLineEdit()
        self.username_edit.setPlaceholderText("请输入编辑平台登录账号")

        settings_control_font = settings.get("settings_control_font")
        self.username_edit.setStyleSheet(settings_control_font.get("QLineEdit"))

        self.username_edit.setMinimumWidth(350)  # 增大输入框最小宽度
        # 设置输入框高度
        self.username_edit.setMinimumHeight(40)

        # Password field
        self.password_edit = qt.QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setStyleSheet(settings_control_font.get("QLineEdit"))
        self.password_edit.setEchoMode(qt.QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumWidth(350)  # 增大输入框最小宽度
        self.password_edit.setMinimumHeight(40)

        # 添加带字体的标签和输入框到表单布局
        username_label = qt.QLabel("账号:")
        username_label.setFont(label_font)
        password_label = qt.QLabel("密码:")
        password_label.setFont(label_font)

        form_layout.addRow(username_label, self.username_edit)
        form_layout.addRow(password_label, self.password_edit)

        # 添加"记住账号密码"复选框
        remember_layout = qt.QHBoxLayout()
        self.remember_checkbox = qt.QCheckBox("记住账号密码")
        checkbox_font = qt.QFont(self.remember_checkbox.font())
        checkbox_font.setPointSize(14)
        self.remember_checkbox.setFont(checkbox_font)  # 设置复选框字体
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        form_layout.addRow(remember_layout)

        # Message label for showing errors
        self.message_label = qt.QLabel()
        self.message_label.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: red;")
        self.message_label.setVisible(False)

        # Button layout
        button_layout = qt.QHBoxLayout()
        button_layout.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)  # 增大按钮间距

        # Login button
        self.login_button = qt.QPushButton("登录")
        button_font = qt.QFont(self.login_button.font())
        button_font.setPointSize(14)
        self.login_button.setFont(button_font)  # 设置按钮字体
        self.login_button.setDefault(True)
        self.login_button.setMinimumWidth(150)  # 增大按钮最小宽度
        self.login_button.setMinimumHeight(45)  # 设置按钮高度

        # Cancel button
        self.cancel_button = qt.QPushButton("取消")
        self.cancel_button.setFont(button_font)  # 应用相同的字体设置
        self.cancel_button.setMinimumWidth(150)  # 增大按钮最小宽度
        self.cancel_button.setMinimumHeight(45)  # 设置按钮高度

        # Add buttons to button layout
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)

        # Add all layouts to main layout
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.message_label)
        main_layout.addLayout(button_layout)

        # Set main layout
        self.setLayout(main_layout)

    def init_loading_mask(self):
        """
        初始化登录遮罩层和进度指示
        """
        # 创建半透明遮罩层
        self.loading_mask = qt.QWidget(self)
        self.loading_mask.setGeometry(self.rect())
        self.loading_mask.setStyleSheet("background-color: rgba(255, 255, 255, 150);")  # 半透明白色背景
        self.loading_mask.setWindowFlag(qt.Qt.WindowType.SubWindow)
        self.loading_mask.hide()

        # 创建遮罩层布局
        mask_layout = qt.QVBoxLayout(self.loading_mask)
        mask_layout.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        # 创建加载文本
        loading_label = qt.QLabel("正在登录中...")
        loading_font = qt.QFont(loading_label.font())
        loading_font.setPointSize(16)
        loading_font.setBold(True)
        loading_label.setFont(loading_font)
        loading_label.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        # 创建进度条 - 修复样式表设置
        self.progress_bar = qt.QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为不确定模式
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setMinimumHeight(25)
        # 修复样式表语法，确保字符串格式正确
        self.progress_bar.setStyleSheet(
            "QProgressBar {"
            "    border: 2px solid #2c3e50;"
            "    border-radius: 5px;"
            "    background-color: #ecf0f1;"
            "    text-align: center;"
            "    height: 25px;"
            "}"
            "QProgressBar::chunk {"
            "    background-color: #3498db;"
            "    border-radius: 3px;"
            "}"
        )

        # 添加文本和进度条到遮罩层布局
        mask_layout.addWidget(loading_label)
        mask_layout.addSpacing(20)
        mask_layout.addWidget(self.progress_bar)

    def show_loading_mask(self):
        """
        显示加载遮罩层
        """
        # 调整遮罩层大小以适应窗口
        self.loading_mask.setGeometry(self.rect())
        # 显示遮罩层
        self.loading_mask.raise_()
        self.loading_mask.show()
        # 强制刷新UI
        qt.QApplication.processEvents()

    def hide_loading_mask(self):
        """
        隐藏加载遮罩层
        """
        self.loading_mask.hide()
        # 强制刷新UI
        qt.QApplication.processEvents()

    def check_credentials(self):
        """
        Check if the entered credentials are valid
        For demonstration purposes, we'll just check if the username and password are not empty
        """
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            self.show_error("请输入账号密码......")
            return

        try:
            # 禁用所有交互控件，防止重复提交
            self.login_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.username_edit.setEnabled(False)
            self.password_edit.setEnabled(False)
            self.remember_checkbox.setEnabled(False)

            # 更改登录按钮文本
            original_button_text = self.login_button.text()
            self.login_button.setText("登录中...")

            # 强制刷新UI，确保用户看到状态变化
            qt.QApplication.processEvents()

            # 显示遮罩层和进度条
            self.show_loading_mask()

            # 使用AccountService进行登录
            success, message = AccountService().login(username, password)
            if success:
                # 清除数据库进行中的数据
                sqlite_service.clear_downloading_books()
                logger.info("清楚历史进行中数据完毕。。。")
                # 如果勾选了记住账号密码，则保存；否则清除已保存的凭据
                if self.remember_checkbox.isChecked():
                    self.save_credentials(username, password)
                else:
                    self.clear_saved_credentials()

                # 获取当前环境 是dev 还是prod
                from xc_service.book_service import book_service
                from utilities.aws_s3 import aws_oss_singleton
                # 调用get_aws_configs方法获取AWS配置
                aws_configs = book_service.get_aws_configs()
                if aws_configs:
                    # 根据version_type选择对应的配置
                    target_config = None
                    for config in aws_configs:
                        # 检查配置的environment字段是否匹配当前version_type
                        if config.get("environment") == version_type:
                            target_config = config
                            break

                    # 如果没有找到匹配的配置，使用第一个配置
                    if not target_config and aws_configs:
                        target_config = aws_configs[0]
                        logger.warning(f"未找到匹配{version_type}环境的AWS配置，使用第一个配置")

                    # 更新aws_oss_singleton实例的配置
                    if target_config:
                        # 使用update_config方法更新配置
                        aws_oss_singleton.update_config(
                            aws_id=target_config.get("aws_access_key_id"),
                            aws_key=target_config.get("aws_secret_key"),
                            aws_region_name=target_config.get("aws_region"),
                            aws_endpoint=target_config.get("aws_endpoint"),
                            aws_bucket=target_config.get("aws_s3_bucket_name"),
                            is_fast=target_config.get("is_active", False),
                            fast_url=target_config.get("aws_fast_url", "")
                        )
                        logger.info(f"成功更新AWS配置，当前环境: {version_type} ，bucket_name: {target_config.get('aws_s3_bucket_name')}")
                    else:
                        logger.error("获取AWS配置失败，无法初始化S3客户端")
                else:
                    logger.error("调用get_aws_configs方法返回空配置")


                # 登录成功，发射信号并接受对话框
                self.login_successful.emit()
                self.accept()
            else:
                # 登录失败，显示错误信息
                self.show_error("登录失败，请重试")
        except Exception as e:
            # 处理异常
            self.show_error(f"登录过程中发生错误: {str(e)}")
        finally:
            # 恢复控件状态
            self.login_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.username_edit.setEnabled(True)
            self.password_edit.setEnabled(True)
            self.remember_checkbox.setEnabled(True)
            self.login_button.setText(original_button_text)

            # 隐藏遮罩层
            self.hide_loading_mask()

    def clear_saved_credentials(self):
        """
        清除已保存的账号密码
        """
        try:
            settings.set("remember_credentials", False)
            settings.set("saved_username", "")
            settings.set("saved_password", "")
        except Exception as e:
            logger.error(f"清除账号密码失败: {str(e)}")

    def save_credentials(self, username, password):
        """
        保存账号密码到设置中
        """
        try:
            settings.set("remember_credentials", True)
            settings.set("saved_username", username)
            settings.set("saved_password", password)  # 注意：实际应用中应考虑加密存储
        except Exception as e:
            logger.error(f"保存账号密码失败: {str(e)}")

    def load_saved_credentials(self):
        """
        从设置中加载保存的账号密码
        """
        try:
            # 检查是否有保存的凭据
            if settings.get("remember_credentials"):
                username = settings.get("saved_username")
                password = settings.get("saved_password")
                if username:
                    self.username_edit.setText(username)
                    if password:
                        self.password_edit.setText(password)
                    self.remember_checkbox.setChecked(True)
        except Exception as e:
            logger.error(f"加载账号密码失败: {str(e)}")

    def show_error(self, message):
        """
        Show an error message
        """
        self.message_label.setText(message)
        self.message_label.setVisible(True)
        # 设置错误消息的字体大小
        font = self.message_label.font()
        font.setPointSize(14)  # 增大错误消息字体
        self.message_label.setFont(font)

    def center_on_screen(self):
        """
        Center the window on the screen
        """
        screen_geometry = qt.QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()

        # Center the window
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

#
# # Example usage
# if __name__ == "__main__":
#     import sys
#
#     app = qt.QApplication(sys.argv)
#     login_window = LoginWindow()
#
#
#     def on_login_success():
#         print("Login successful!")
#
#
#     login_window.login_successful.connect(on_login_success)
#
#     if login_window.exec() == qt.QDialog.DialogCode.Accepted:
#         print("Proceeding to main application...")
#         # Here you would initialize and show the main window
#
#     sys.exit(app.exec())
