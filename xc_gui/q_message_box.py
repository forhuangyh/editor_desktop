import qt


class CustomMessageBox(qt.QDialog):
    """
    自定义消息框类，实现文本和图标在同一行，按钮在右下角的布局
    """

    def __init__(self, parent=None, width=450, height=100):
        super().__init__(parent)

        # 设置窗口属性
        self.setWindowTitle("消息")
        self.setFixedSize(width, height)
        self.setWindowFlags(
            qt.Qt.WindowType.Window |
            qt.Qt.WindowType.WindowTitleHint |
            qt.Qt.WindowType.CustomizeWindowHint |
            qt.Qt.WindowType.WindowCloseButtonHint
        )

        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 3px;
                padding: 5px 15px;
                font-size: 13px;
                border: none;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2968a0;
            }
        """)

        # 创建主要布局
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 创建内容布局（图标+文本）- 同一行
        content_layout = qt.QHBoxLayout()
        content_layout.setSpacing(10)

        # 图标标签
        self.icon_label = qt.QLabel()
        content_layout.addWidget(self.icon_label)

        # 文本标签
        self.text_label = qt.QLabel()
        self.text_label.setWordWrap(True)
        content_layout.addWidget(self.text_label, 1)  # 文本占据剩余空间

        # 添加内容布局到主布局
        main_layout.addLayout(content_layout)

        # 创建按钮布局
        button_layout = qt.QHBoxLayout()
        button_layout.addStretch(1)  # 左侧留白，将按钮推到右侧

        # 确定按钮
        self.ok_button = qt.QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        # 取消按钮（默认隐藏）
        self.cancel_button = qt.QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.hide()
        button_layout.addWidget(self.cancel_button)

        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)

        # 设置默认图标
        self.set_icon(qt.QMessageBox.Icon.Information)

    def set_icon(self, icon_type):
        """设置消息框图标"""
        # 创建标准图标
        icon = qt.QApplication.style().standardIcon(
            qt.QStyle.StandardPixmap.SP_MessageBoxInformation
        )

        if icon_type == qt.QMessageBox.Icon.Warning:
            icon = qt.QApplication.style().standardIcon(
                qt.QStyle.StandardPixmap.SP_MessageBoxWarning
            )
        elif icon_type == qt.QMessageBox.Icon.Critical:
            icon = qt.QApplication.style().standardIcon(
                qt.QStyle.StandardPixmap.SP_MessageBoxCritical
            )
        elif icon_type == qt.QMessageBox.Icon.Question:
            icon = qt.QApplication.style().standardIcon(
                qt.QStyle.StandardPixmap.SP_MessageBoxQuestion
            )

        # 设置图标大小
        self.icon_label.setPixmap(icon.pixmap(32, 32))

    def set_text(self, text):
        """设置消息框文本"""
        self.text_label.setText(text)

    def show_buttons(self, buttons):
        """显示指定的按钮"""
        if buttons & qt.QMessageBox.StandardButton.No:
            self.cancel_button.show()
            self.cancel_button.setText("取消")
        else:
            self.cancel_button.hide()

    @staticmethod
    def warning(parent, title='警告', text='', width=450, height=100):
        """
        显示警告消息框，文本和图标在同一行，按钮在右下角
        """
        msg_box = CustomMessageBox(parent, width, height)
        msg_box.setWindowTitle(title)
        msg_box.set_icon(qt.QMessageBox.Icon.Warning)
        msg_box.set_text(text)
        msg_box.show_buttons(qt.QMessageBox.StandardButton.Ok)
        return msg_box.exec()

    @staticmethod
    def information(parent, title='信息', text='', width=450, height=100):
        """
        显示信息消息框，文本和图标在同一行，按钮在右下角
        """
        msg_box = CustomMessageBox(parent, width, height)
        msg_box.setWindowTitle(title)
        msg_box.set_icon(qt.QMessageBox.Icon.Information)
        msg_box.set_text(text)
        msg_box.show_buttons(qt.QMessageBox.StandardButton.Ok)
        return msg_box.exec()

    @staticmethod
    def critical(parent, title='错误', text='', width=450, height=100):
        """
        显示错误消息框，文本和图标在同一行，按钮在右下角
        """
        msg_box = CustomMessageBox(parent, width, height)
        msg_box.setWindowTitle(title)
        msg_box.set_icon(qt.QMessageBox.Icon.Critical)
        msg_box.set_text(text)
        msg_box.show_buttons(qt.QMessageBox.StandardButton.Ok)
        return msg_box.exec()

    @staticmethod
    def question(parent, title='询问', text='', width=450, height=100):
        """
        显示询问消息框，文本和图标在同一行，按钮在右下角
        """
        msg_box = CustomMessageBox(parent, width, height)
        msg_box.setWindowTitle(title)
        msg_box.set_icon(qt.QMessageBox.Icon.Question)
        msg_box.set_text(text)
        msg_box.show_buttons(qt.QMessageBox.StandardButton.Yes | qt.QMessageBox.StandardButton.No)
        return msg_box.exec()
