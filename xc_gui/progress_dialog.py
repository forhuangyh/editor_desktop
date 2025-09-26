from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

class UploadProgressDialog(QDialog):
    """通用上传进度遮罩框组件（可复用）"""

    def __init__(self, parent, file_name):
        super().__init__(parent)
        self.setWindowTitle("处理中")
        self.setFixedSize(400, 160)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet("QDialog {background-color: rgba(255, 255, 255, 240); border: 1px solid black;}")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 进度文本（可动态修改）
        self.status_label = QLabel(f"正在处理: {file_name}")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 状态提示文本（可动态修改）
        self.progress_label = QLabel("处理中...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        self.setLayout(layout)

    def update_status(self, status_text, progress_text):
        """更新进度框文本内容"""
        self.status_label.setText(status_text)
        self.progress_label.setText(progress_text)
