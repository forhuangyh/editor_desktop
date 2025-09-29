import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QDateTime, QThread, pyqtSignal  # 新增：QThread, pyqtSignal

# 导入样式表类
# 添加路径以便导入book_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xc_service.book_service import book_service

# 数据库文件路径
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.exco', 'editor_desktop.db')

# 在文件顶部导入CustomMessageBox
from .q_message_box import CustomMessageBox
from .extended_table_widget import ExtendedTableWidget
from .form_components import SimpleInputForm
from xc_service.sqlite_service import sqlite_service
from xc_gui.progress_dialog import UploadProgressDialog  # 导入公共遮罩组件
from xc_common.logger import get_logger
# 获取模块专属logger
logger = get_logger("import_book_library")

# ================= 历史对话框 =================
class BookLibraryHistoryDialog(QDialog):
    def __init__(self, main_form, parent=None):
        super().__init__(parent)
        self.setWindowTitle("下载书库书籍")
        self.setMinimumSize(1200, 800)
        self.book_history = []
        self.selected_book = None
        self.book_service = book_service
        self.main_form = main_form
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
            button_text="确认下载",
            on_confirm_callback=self.on_confirm_id
        )
        main_layout.addWidget(self.book_id_form)

        # 表格
        self.book_table = ExtendedTableWidget(0, 6, ["书籍ID", "书名", "语言", "章节数", "下载时间", "下载状态"])
        self.book_table.applyBookTableStyle()
        main_layout.addWidget(self.book_table, 1)

        # # 按钮区
        # button_layout = QHBoxLayout()
        # refresh_button = QPushButton("刷新列表")
        # refresh_button.clicked.connect(self.load_history)
        # button_layout.addWidget(refresh_button)
        #
        # button_layout.addStretch(1)
        # self.confirm_button = QPushButton("打开编辑")
        # self.confirm_button.setEnabled(False)
        # self.confirm_button.clicked.connect(self.accept)
        #
        # cancel_button = QPushButton("取消")
        # cancel_button.clicked.connect(self.reject)
        # button_layout.addWidget(self.confirm_button)
        # button_layout.addWidget(cancel_button)

        # main_layout.addLayout(button_layout)
        # self.book_table.itemSelectionChanged.connect(self.on_item_selected)
        # 【新增】连接表格双击事件到accept函数
        # 当用户双击表格行时，直接调用accept函数打开编辑
        self.book_table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # 【新增】双击事件处理函数

    def on_cell_double_clicked(self, row, column):
        # 获取双击行的数据
        self.selected_book = self.book_table.rowData(row)
        if self.selected_book:
            # 检查下载状态，仅"已完成"状态可打开（download_state=2）
            download_state = self.selected_book.get('download_state', 0)
            if download_state == 2:
                # 打印整条数据
                logger.info(f"双击书籍数据：{self.selected_book}")
                # 删除数据库记录，获取文件路径
                record_id = self.selected_book.get('id')
                if record_id:
                    self.accept()
            else:
                # 可以添加提示信息，但不阻止其他操作
                pass

    def on_confirm_id(self):
        cp_book_id = self.book_id_form.get_value().strip()
        if not cp_book_id:
            CustomMessageBox.warning(self, "输入错误", "请输入书籍ID")
            return

        # 获取按钮并立即更新状态（点击即变）
        confirm_button = self.book_id_form.confirm_button
        original_text = confirm_button.text()
        confirm_button.setEnabled(False)
        confirm_button.setText("加载中...")  # 立即显示加载状态

        # 显示查询书籍信息遮罩框
        self.info_mask = UploadProgressDialog(self, "书籍信息查询")
        self.info_mask.update_status("查询书籍信息中", "正在请求网络数据...")
        self.info_mask.setModal(True)
        self.info_mask.show()

        # 强制刷新UI，确保遮罩框显示
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            # 同步调用书籍信息接口（无线程）
            book_info = self.book_service.book_info(cp_book_id)

            if book_info:
                # 处理成功逻辑
                flag = sqlite_service.add_book(book_data=book_info)
                if not flag:
                    self.info_mask.close()
                    CustomMessageBox.warning(self, text="书籍下载记录保存失败")
                else:
                    self.load_downs_book_to_table()
            else:
                self.info_mask.close()
                CustomMessageBox.warning(self, "获取失败", f"无法查到此书，书籍ID为 '{cp_book_id}'")

        except Exception as e:
            self.info_mask.close()
            # 处理异常
            CustomMessageBox.warning(self, "错误", f"获取书籍信息时发生错误：{str(e)}")

        finally:
            # 无论成功失败，关闭遮罩并恢复按钮状态
            self.info_mask.close()
            confirm_button.setEnabled(True)
            confirm_button.setText(original_text)

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
                logger.info(f"书籍ID: {book_info.get('cp_book_id', '未知')}, 提交时间: {book_info.get('created_at', '未知时间')},记录id: {book_info.get('id', '未知')}，更新时间:{book_info.get('updated_at', '未知时间')}")
                self.add_book_to_table(book_info)
        except Exception as e:
            logger.error(f"加载下载记录失败: {str(e)}")
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

    def get_selected_book(self):
        return self.selected_book

    def accept(self):
        if not self.selected_book:
            return
        cp_book_id = self.selected_book.get('cp_book_id')
        id = self.selected_book.get('id')
        book_id = self.selected_book.get('book_id')
        language = self.selected_book.get('language')
        exco_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.exco')
        download_dir = os.path.join(exco_dir, 'down_load_books')
        file_path = download_dir + "/" + f"{cp_book_id}_{id}_{book_id}.txt"
        # 调用打开
        is_open = self.main_form.open_file_from_online(f"{cp_book_id}.txt", language, file_path)
        if is_open:
            # 【新增】从选中数据中获取record_id并执行删除
            record_id = self.selected_book.get('id')
            if record_id:
                sqlite_service.delete_book(record_id)  # 在accept()中执行删除
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
            logger.info(f"断开信号连接失败: {str(e)}")
        event.accept()


# ================= 管理器 =================
class BookLibraryManager:
    @staticmethod
    def import_book_from_library(main_form, parent=None):
        dialog = BookLibraryHistoryDialog(main_form, parent)
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
            logger.error(f"无法添加书籍到历史记录：{str(e)}")


# ================= 便捷函数 =================
def show_book_library_history(main_form, parent=None):
    return BookLibraryManager.import_book_from_library(main_form, parent)


def add_book_to_library_history(book_name, author, file_path):
    BookLibraryManager.add_book_to_history(book_name, author, file_path)
