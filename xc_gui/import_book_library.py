import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QDateTime, QThread, pyqtSignal  # 新增：QThread, pyqtSignal

# 导入样式表类
# 添加路径以便导入book_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xc_service.book_service import BookService

# 数据库文件路径
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.exco', 'editor_desktop.db')

# 在文件顶部导入CustomMessageBox
from .q_message_box import CustomMessageBox
from .extended_table_widget import ExtendedTableWidget
from .form_components import SimpleInputForm
from xc_service.sqlite_service import sqlite_service


# ================= 工具函数 =================
def now_timestamp():
    """返回当前时间戳（秒）"""
    return int(QDateTime.currentSecsSinceEpoch())


def now_datetime_str():
    """返回当前时间字符串（ISO格式）"""
    return QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)


# ================= 历史对话框 =================
class BookLibraryHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("下载书库书籍")
        self.setMinimumSize(1200, 800)
        self.book_history = []
        self.selected_book = None
        self.book_service = BookService()
        self.init_ui()
        # 初始化时调用 load_history 方法加载历史记录
        self.load_history()

        # 新增：连接调度器信号以自动刷新列表
        from xc_timer.book_download_scheduler import book_download_scheduler
        self.scheduler = book_download_scheduler
        # 连接任务开始、完成、失败信号到表格刷新方法
        self.scheduler.task_started.connect(self.load_downs_book_to_table)
        self.scheduler.task_completed.connect(self.load_downs_book_to_table)
        self.scheduler.task_failed.connect(self.load_downs_book_to_table)


    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.book_id_form = SimpleInputForm(
            label_text="书籍ID：",
            placeholder_text="请输入书籍ID",
            button_text="确认",
            on_confirm_callback=self.on_confirm_id
        )
        main_layout.addWidget(self.book_id_form)

        # 表格
        self.book_table = ExtendedTableWidget(0, 6, ["书籍ID", "标题", "语言", "总章节数", "提交时间","下载状态"])
        self.book_table.applyBookTableStyle()
        main_layout.addWidget(self.book_table, 1)

        # 按钮区
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新列表")
        refresh_button.clicked.connect(self.load_history)
        button_layout.addWidget(refresh_button)

        button_layout.addStretch(1)
        self.confirm_button = QPushButton("打开编辑")
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.accept)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)
        self.book_table.itemSelectionChanged.connect(self.on_item_selected)

    # 新增：网络请求 worker 线程（独立于GUI线程）
    class BookInfoWorker(QThread):
        # 定义信号：请求完成后返回结果
        result_ready = pyqtSignal(dict)  # 成功时返回book_info
        error_occurred = pyqtSignal(str)  # 失败时返回错误信息

        def __init__(self, book_service, cp_book_id):
            super().__init__()
            self.book_service = book_service
            self.cp_book_id = cp_book_id

        def run(self):
            """在线程中执行网络请求"""
            try:
                book_info = self.book_service.book_info(self.cp_book_id)
                if book_info:
                    self.result_ready.emit(book_info)
                else:
                    self.error_occurred.emit(f"无法获取书籍ID为 '{self.cp_book_id}' 的信息")
            except Exception as e:
                self.error_occurred.emit(f"获取书籍信息时发生错误：{str(e)}")

    def on_confirm_id(self):
        cp_book_id = self.book_id_form.get_value()
        if not cp_book_id:
            CustomMessageBox.warning(self, "输入错误", "请输入书籍ID")
            return

        # 获取按钮并立即更新状态（点击即变）
        confirm_button = self.book_id_form.confirm_button
        original_text = confirm_button.text()
        confirm_button.setEnabled(False)
        confirm_button.setText("加载中...")  # 立即显示加载状态

        # 创建并启动网络请求线程（不阻塞GUI）
        self.worker = self.BookInfoWorker(self.book_service, cp_book_id)

        # 连接线程信号：成功/失败后处理
        self.worker.result_ready.connect(self.on_book_info_success)
        self.worker.error_occurred.connect(self.on_book_info_error)

        # 线程结束后清理并恢复按钮状态
        self.worker.finished.connect(lambda: self.restore_button_state(confirm_button, original_text))
        self.worker.finished.connect(self.worker.deleteLater)  # 释放线程资源

        # 启动线程（网络请求在后台执行）
        self.worker.start()

    # 新增：请求成功处理
    def on_book_info_success(self, book_info):
        flag = sqlite_service.add_book(book_data=book_info)
        if not flag:
            CustomMessageBox.warning(self, text="书籍下载记录保存失败")
            return
        self.load_downs_book_to_table()

    # 新增：请求失败处理
    def on_book_info_error(self, error_msg):
        CustomMessageBox.warning(self, "错误", error_msg)

    # 新增：恢复按钮状态
    def restore_button_state(self, button, original_text):
        button.setEnabled(True)
        button.setText(original_text)
    def load_downs_book_to_table(self):
        """从数据库加载最近100条下载记录并渲染到表格中"""
        try:
            # 清空表格
            self.book_table.setRowCount(0)

            # 从数据库获取最近100条记录
            # 使用LIMIT 100限制数量，ORDER BY updated_at DESC按更新时间倒序排列
            self.book_history = sqlite_service.get_recent_books()

            # 遍历数据并添加到表格
            for book_info in self.book_history:
                # 打印每一条记录信息，打印id 和 时间
                print(f"书籍ID: {book_info.get('cp_book_id', '未知')}, 提交时间: {book_info.get('created_at', '未知时间')},记录id: {book_info.get('id', '未知')}，更新时间:{book_info.get('updated_at', '未知时间')}")
                self.add_book_to_table(book_info)
        except Exception as e:
            print(f"加载下载记录失败: {str(e)}")
            CustomMessageBox.warning(self, "加载失败", f"无法加载书籍下载记录：{str(e)}")

    def add_book_to_table(self, book_info):
        """将单条书籍信息添加到表格中"""
        row = self.book_table.rowCount()
        self.book_table.insertRow(row)

        # 设置表格内容
        # 书籍ID
        book_id_item = QTableWidgetItem(book_info.get('cp_book_id', '未知'))
        book_id_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.book_table.setItem(row, 0, book_id_item)

        # 标题
        title_item = QTableWidgetItem(book_info.get('title', '未知标题'))
        title_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.book_table.setItem(row, 1, title_item)

        # 语言
        language_item = QTableWidgetItem(book_info.get('language', '未知语言'))
        language_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.book_table.setItem(row, 2, language_item)

        # 总章节数
        chapters_item = QTableWidgetItem(str(book_info.get('total_chapters', 0)))
        chapters_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.book_table.setItem(row, 3, chapters_item)

        # 完成状态
        status_item = QTableWidgetItem()
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # 提交时间
        submit_time_item = QTableWidgetItem(book_info.get('created_at', '未知时间'))
        submit_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.book_table.setItem(row, 4, submit_time_item)

        download_state = book_info.get('download_state', 0)
        if download_state == 2:
            status_item.setText("已完成")
            status_item.setForeground(Qt.GlobalColor.green)
        elif download_state == 3:
            status_item.setText("失败")
            status_item.setForeground(Qt.GlobalColor.red)
        elif download_state == 1:
            status_item.setText("进行中")
            status_item.setForeground(Qt.GlobalColor.blue)
        else:
            status_item.setText("未开始")
            status_item.setForeground(Qt.GlobalColor.gray)

        self.book_table.setItem(row, 5, status_item)

        # 存储完整数据到行
        self.book_table.setRowData(row, book_info)

    def load_history(self):
        """加载书籍历史记录（供刷新按钮调用）"""
        self.load_downs_book_to_table()

    def on_item_selected(self):
        selected_rows = self.book_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.selected_book = self.book_table.rowData(row)
            self.confirm_button.setEnabled(True)
        else:
            self.selected_book = None
            self.confirm_button.setEnabled(False)

    def get_selected_book(self):
        return self.selected_book

    def accept(self):
        if self.selected_book:
            self.selected_book['updated_at'] = QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
            sqlite_service.add_or_update_book(self.selected_book)
            # 调用打开sheet的页面

        super().accept()

    def reject(self):
        super().reject()

    def closeEvent(self, event):
        # 新增：断开信号连接，避免内存泄漏
        try:
            self.scheduler.task_started.disconnect(self.load_downs_book_to_table)
            self.scheduler.task_completed.disconnect(self.load_downs_book_to_table)
            self.scheduler.task_failed.disconnect(self.load_downs_book_to_table)
        except Exception as e:
            print(f"断开信号连接失败: {str(e)}")
        event.accept()


# ================= 管理器 =================
class BookLibraryManager:
    @staticmethod
    def import_book_from_library(parent=None):
        dialog = BookLibraryHistoryDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_book = dialog.get_selected_book()
            if selected_book:
                try:
                    return selected_book
                except Exception as e:
                    CustomMessageBox.warning(parent, "下载失败", f"下载书籍时发生错误：{str(e)}")
        return None

    @staticmethod
    def add_book_to_history(book_name, author, file_path):
        try:
            book_info = {
                'book_name': book_name,
                'author': author,
                'file_path': file_path,
                'updated_at': QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
                'created_at': QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
            }
            sqlite_service.add_or_update_book(book_info)
        except Exception as e:
            print(f"无法添加书籍到历史记录：{str(e)}")


# ================= 便捷函数 =================
def show_book_library_history(parent=None):
    return BookLibraryManager.import_book_from_library(parent)


def add_book_to_library_history(book_name, author, file_path):
    BookLibraryManager.add_book_to_history(book_name, author, file_path)
