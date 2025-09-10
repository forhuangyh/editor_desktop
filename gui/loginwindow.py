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
from service.account_service import AccountService


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
        self.setMinimumSize(400, 300)
        self.setWindowFlag(qt.Qt.WindowType.WindowCloseButtonHint, True)
        self.setWindowFlag(qt.Qt.WindowType.WindowSystemMenuHint, True)

        # Set font
        self.setFont(settings.get_current_font())

        # Initialize UI components
        self.init_ui()

        # Connect signals
        self.login_button.clicked.connect(self.check_credentials)
        self.cancel_button.clicked.connect(self.reject)
        self.password_edit.returnPressed.connect(self.check_credentials)
        self.username_edit.returnPressed.connect(self.check_credentials)

        # Center the window on screen
        self.center_on_screen()

    def init_ui(self):
        """
        Initialize the UI components of the login window
        """
        # Main layout
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Logo and title
        title_layout = qt.QVBoxLayout()
        title_layout.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        # Create a simple logo since we don't have an actual logo
        logo_label = qt.QLabel()
        logo_label.setText("Editor Desktop.")
        logo_font = qt.QFont(logo_label.font())
        logo_font.setPointSize(36)
        logo_font.setBold(True)
        logo_label.setFont(logo_font)
        logo_label.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)
        title_label = qt.QLabel("version {:s}".format(data.application_version))
        title_label.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)

        # Login form layout
        form_layout = qt.QFormLayout()
        form_layout.setFieldGrowthPolicy(qt.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setFormAlignment(qt.Qt.AlignmentFlag.AlignCenter)

        # Username field
        self.username_edit = qt.QLineEdit()
        self.username_edit.setPlaceholderText("请输入编辑平台登录账号")
        self.username_edit.setText("lhc")
        self.username_edit.setMinimumWidth(250)

        # Password field
        self.password_edit = qt.QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setText("lhc123")
        self.password_edit.setEchoMode(qt.QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumWidth(250)

        # Add fields to form layout
        form_layout.addRow("账号:", self.username_edit)
        form_layout.addRow("密码:", self.password_edit)

        # Message label for showing errors
        self.message_label = qt.QLabel()
        self.message_label.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: red;")
        self.message_label.setVisible(False)

        # Button layout
        button_layout = qt.QHBoxLayout()
        button_layout.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(10)

        # Login button
        self.login_button = qt.QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.setMinimumWidth(100)

        # Cancel button
        self.cancel_button = qt.QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)

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
            # 使用AccountService进行登录
            success, message = AccountService.login(username, password)
            if success:
                # 登录成功，发射信号并接受对话框
                self.login_successful.emit()
                self.accept()
            else:
                # 登录失败，显示错误信息
                self.show_error(message or "登录失败，请重试")
        except Exception as e:
            # 处理异常
            self.show_error(f"登录过程中发生错误: {str(e)}")

    def show_error(self, message):
        """
        Show an error message
        """
        self.message_label.setText(message)
        self.message_label.setVisible(True)
        # 设置错误消息的字体大小
        font = self.message_label.font()
        font.setPointSize(12)  # 设置为12号字体，可以根据需要调整大小
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
