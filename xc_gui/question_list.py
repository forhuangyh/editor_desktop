"""
Copyright (c) 2015
"""

from qt import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSize, Qt,
    QStyledItemDelegate, QApplication,
    QListView, QStyle, QColor, QFontMetrics,
    QAbstractListModel, QModelIndex, QVariant, Qt,
    QLabel, pyqtSlot, QToolButton
)

import constants
import components.internals
import settings
from xc_entity.book import book_manager
from gui.customeditor import CustomEditor
from xc_entity.work import TaskWorker
from qt import QThread


class QuestionList(QWidget):
    # Class variables
    name = "查重列表"
    _parent = None
    main_form = None
    current_icon = None
    internals = None
    savable = constants.CanSave.NO
    # Reference to the custom context menu
    context_menu = None
    # Namespace references for grouping functionality
    hotspots = None

    def __del__(self):
        self._parent = None
        self.main_form = None
        self._fixed_widget = None
        self._editor = None
        if self._current_book:
            try:
                self._current_book.chapter_list_updated.disconnect(self.handle_chapter_list_update)
                self._fixed_widget.editor_changed.disconnect(self.update_editor_reference)
                self._fixed_widget.editor_closed.disconnect(self.close_editor_reference)
                self._current_book = None
                self._chapter_list = None
            except:
                pass
        try:
            if hasattr(self, 'worker'):
                self.worker.stop()
                self.worker_thread.quit()
                self.worker_thread.wait()
        except:
            pass

    def __init__(self, fixed_widget, parent, main_form):
        # Initialize the superclass
        super().__init__()
        # Initialize components
        self.internals = components.internals.Internals(self, parent)
        # Store the main form and parent widget references
        self._parent = parent
        self.main_form = main_form
        self._fixed_widget = fixed_widget
        self._editor = self._fixed_widget.editor
        self._current_book = book_manager.get_book(self._editor)
        self._chapter_list = None
        self.settings_control_font = settings.get("settings_control_font")
        # text_change的耗时操作线程，比如split_chapter_list
        # 初始化工作线程和 Worker 对象
        self.worker_thread = QThread()
        self.worker = TaskWorker()
        # 将 Worker 对象移动到工作线程中，确保了耗时任务在后台运行，而不会冻结主线程的 UI
        self.worker.moveToThread(self.worker_thread)
        # 连接信号：当线程启动时，开始工作
        self.worker_thread.started.connect(self.worker.run)
        # 启动工作线程
        self.worker_thread.start()
        self.init_ui()
        self._fixed_widget.editor_changed.connect(self.update_editor_reference)
        self._fixed_widget.editor_closed.connect(self.close_editor_reference)
        self.set_theme(settings.get_theme())

    def update_editor_reference(self, new_editor):
        """当fixed_widget的编辑器引用发生更新，联动更新"""
        if self._editor == new_editor:
            return
        if not isinstance(new_editor, CustomEditor):
            return
        self._editor = new_editor
        new_book = book_manager.get_book(self._editor)
        if not new_book:
            return
        if self._current_book == new_book:
            return

        # 1. 如果存在旧的书籍对象，先断开它与槽函数的连接
        if self._current_book:
            self._current_book.chapter_list_updated.disconnect(self.handle_chapter_list_update)
            self._current_book.question.question_list_updated.disconnect(self.handle_question_list_update)

        # 2. 建立新的绑定
        if new_book:
            self._chapter_list = new_book.get_chapter_list()
            self._current_book = new_book
            # 连接新书的 chapterListUpdated 信号到槽函数
            self._current_book.chapter_list_updated.connect(self.handle_chapter_list_update)
            self._current_book.question.question_list_updated.connect(self.handle_question_list_update)
            match_list, highlight_matches = self._current_book.question.get_question_list(
                # self._editor.line_list, self._chapter_list, self._editor, self._current_book
            )
            self.fill_match_list(match_list, highlight_matches)
        else:
            self._current_book = None
            self.fill_match_list([], [])

    def close_editor_reference(self, new_editor):
        """当fixed_widget的编辑器变化时，更新我们的_editor引用"""
        if self._editor != new_editor:
            return
        if not isinstance(new_editor, CustomEditor):
            return

        new_book = book_manager.get_book(new_editor)
        if not new_book:
            return
        if self._current_book != new_book:
            return

        # 1. 如果存在旧的书籍对象，先断开它与槽函数的连接
        if self._current_book:
            try:
                self._current_book.chapter_list_updated.disconnect(self.handle_chapter_list_update)
            except TypeError:
                pass

        self._editor.clear_question_highlights()
        self.model.setMatches([])
        self.info_label.setText("重复总数：0")
        self._current_book = None
        self._editor = None

    @pyqtSlot(list)
    def handle_chapter_list_update(self, chapter_list):
        """当书籍的章节列表更新时，联动更新"""
        self._chapter_list = chapter_list
        question = self._current_book.question
        task = {
            'name': 'refresh_question_list',
            'function': question.split_question_list,
            'args': (self._editor.line_list, self._chapter_list, self._editor, self._current_book)
        }
        # 将任务提交给 Worker 对象，由 Worker 自己处理
        self.worker.add_task(task)

    @pyqtSlot(list, list)
    def handle_question_list_update(self, match_list, highlight_matches):
        """当书籍的章节列表更新时，联动更新"""
        self.fill_match_list(match_list, highlight_matches)

    def init_ui(self):
        # 直接设置自身属性
        self.setWindowTitle("章节列表")
        self.resize(400, 600)  # 设置窗口初始大小

        # 主垂直布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # 设置布局间距

        # 替换 QListWidget 为 QListView
        self.result_view = QListView()
        self.result_view.setUniformItemSizes(True)
        self.result_view.setWordWrap(False)
        self.result_view.setTextElideMode(Qt.TextElideMode.ElideNone)

        # 创建并设置自定义模型和代理
        self.model = SearchMatchModel()
        self.result_view.setModel(self.model)
        self.delegate = HighlightDelegate(self.result_view)
        self.result_view.setItemDelegate(self.delegate)

        self.info_label = QLabel("章节总数：")
        self.info_label.setWordWrap(True)  # 允许自动换行
        self.info_label.setMinimumHeight(10)  # 设置最小高度
        self.info_label.setStyleSheet("color: gray;")  # 可以设置样式

        # 2. info_label 和上下箭头按钮布局
        info_button_layout = QHBoxLayout()
        self.info_label = QLabel("章节总数：")
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(10)
        self.info_label.setStyleSheet("color: gray;")

        # 增加弹性伸缩空间，将标签推到左侧
        info_button_layout.addWidget(self.info_label)
        info_button_layout.addStretch()

        # 创建上箭头按钮
        self.up_button = QToolButton()
        self.up_button.setArrowType(Qt.ArrowType.UpArrow)
        self.up_button.setFixedSize(QSize(20, 20))  # 固定按钮大小

        # 创建下箭头按钮
        self.down_button = QToolButton()
        self.down_button.setArrowType(Qt.ArrowType.DownArrow)
        self.down_button.setFixedSize(QSize(20, 20))  # 固定按钮大小

        info_button_layout.addWidget(self.up_button)
        info_button_layout.addWidget(self.down_button)

        self.search_button = QPushButton("查重")
        self.search_button.setMinimumHeight(30)
        self.search_button.setMinimumWidth(40)
        self.search_button.setMaximumWidth(50)
        info_button_layout.addWidget(self.search_button)

        self.clear_button = QPushButton("清除")
        self.clear_button.setMinimumHeight(30)
        self.clear_button.setMinimumWidth(40)
        self.clear_button.setMaximumWidth(50)
        info_button_layout.addWidget(self.clear_button)

        # 4. 添加组件到主布局
        main_layout.addLayout(info_button_layout)
        main_layout.addWidget(self.result_view)
        self.setLayout(main_layout)

        # # 连接信号槽
        self.search_button.clicked.connect(self._find_all)
        self.clear_button.clicked.connect(self._clear_highlight)
        self.result_view.clicked.connect(self.on_item_clicked)
        self.up_button.clicked.connect(self.on_up_clicked)
        self.down_button.clicked.connect(self.on_down_clicked)

    def on_up_clicked(self):
        current_index = self.result_view.currentIndex()
        # 确保有选中的项，并且不是第一项
        if not current_index.isValid():
            new_row = 0
        else:
            new_row = current_index.row() - 1 if current_index.row() >= 1 else 0

        new_index = self.model.index(new_row, 0)
        # 将焦点设置到新的项上
        self.result_view.setCurrentIndex(new_index)
        # 滚动到新的项，确保可见
        self.result_view.scrollTo(new_index)
        # 模拟点击事件，触发 on_item_clicked
        self.on_item_clicked(new_index)

    def on_down_clicked(self):
        current_index = self.result_view.currentIndex()
        if not current_index.isValid():
            new_row = 0
        else:
            new_row = current_index.row()

        if new_row < self.model.rowCount() - 1:
            new_row = current_index.row() + 1
            new_index = self.model.index(new_row, 0)
            # 将焦点设置到新的项上
            self.result_view.setCurrentIndex(new_index)
            # 滚动到新的项，确保可见
            self.result_view.scrollTo(new_index)
            # 模拟点击事件，触发 on_item_clicked
            self.on_item_clicked(new_index)

    def _find_all(self):
        """查找下一个匹配项并高亮"""
        self._current_book.question.set_is_work(True)
        match_list, highlight_matches = self._current_book.question.split_question_list(
            self._editor.line_list, self._chapter_list, self._editor, self._current_book
        )
        self.fill_match_list(match_list, highlight_matches)

    def _clear_highlight(self):
        """清除所有高亮"""
        self._editor.clear_question_highlights()
        self._current_book.question.set_is_work(False)
        self.model.setMatches([])
        self.info_label.setText("重复总数：0")

    def fill_match_list(self, match_list, highlight_matches):
        """填充列表
        """
        max_line_text = ""
        line_text_len = 0
        new_match_list = []
        for match in match_list:
            line_text = match["line_text"]
            index = match["index"]
            new_line_text = f"{index}：{line_text}"
            match["line_text"] = new_line_text
            new_match_list.append(match)
            cur_len = len(new_line_text)
            if cur_len > line_text_len:
                max_line_text = line_text
                line_text_len = cur_len

            for i, child in enumerate(match["children"]):
                new_line_text = f'    {child["title"]}' if child["title"] else f"    序号：{i + 1}"
                child["line_text"] = new_line_text
                new_match_list.append(child)

        if match_list:
            self.model.setMatches(new_match_list)
            self.delegate.setMaxLenText(max_line_text)
            self.info_label.setText(f"重复总数：{len(new_match_list)}")
            self._editor.clear_question_highlights()
            self._editor.set_indicator("question")
            self._editor.highlight_raw(highlight_matches)
        else:
            self.model.setMatches([])
            self._editor.clear_question_highlights()
            self.info_label.setText("重复总数：0")

    def on_item_clicked(self, index):
        """
        当 QListWidget 中的一个项目被点击时调用的槽函数。
        """
        line_number = self.model.data(index, Qt.ItemDataRole.UserRole)
        self._editor.goto_line(line_number + 1)
        self._editor.setFocus()

    def set_theme(self, theme):
        """
        根据提供的字典主题设置UI的样式。
        """

        # 设置主窗口背景色
        main_bg = theme['indication']['passivebackground']
        self.setStyleSheet(f"QWidget {{ background-color: {main_bg}; }}")

        # 更新 QPushButton 的样式
        button_style = (
            f"QPushButton {{ "
            f"background-color: {theme['indication']['passivebackground']}; "
            f"color: {theme['fonts']['default']['color']}; "
            f"border: 1px solid {theme['indication']['passiveborder']}; "
            f"padding: 4px; "
            f"}}"
            f"QPushButton:hover {{ "
            f"background-color: {theme['indication']['hover']}; "
            f"}}"
        )
        self.search_button.setStyleSheet(button_style)

        # 更新 QListView 的样式
        list_style = (
            f"QListView {{ "
            f"background-color: {main_bg}; "
            f"color: {theme['fonts']['default']['color']}; "
            f"border: 1px solid {theme['indication']['passiveborder']}; "
            f"}}"
            f"QListView::item:selected {{ "
            f"background-color: {theme['indication']['selection']}; "
            f"color: {theme['fonts']['default']['color']}; "
            f"}}"
        )
        # self.result_view.setStyleSheet(list_style)

        # 更新滚动条样式
        scrollbar_style = (
            f"QScrollBar:vertical {{ "
            f"background: {theme['scrollbar']['background']}; "
            f"width: 12px; "
            f"margin: 0px; "
            f"}}"
            f"QScrollBar::handle:vertical {{ "
            f"background: {theme['scrollbar']['handle']}; "
            f"min-height: 20px; "
            f"}}"
            f"QScrollBar::handle:vertical:hover {{ "
            f"background: {theme['scrollbar']['handle-hover']}; "
            f"}}"
        )
        self.result_view.verticalScrollBar().setStyleSheet(scrollbar_style)

        # 刷新列表视图以应用新的高亮颜色
        self.result_view.viewport().update()

        # 设置工具提示样式
        tooltip_style = (
            f"QToolTip {{ "
            f"background-color: {theme['indication']['passivebackground']}; "
            f"color: {theme['fonts']['default']['color']}; "
            f"border: 1px solid {theme['indication']['passiveborder']}; "
            f"padding: 2px; "
            f"}}"
        )
        self.setStyleSheet(self.styleSheet() + tooltip_style)


class SearchMatchModel(QAbstractListModel):
    def __init__(self, matches=None, parent=None):
        super().__init__(parent)
        self.matches = matches if matches is not None else []
        self._highlight_line = -1
        self.max_width_text = None

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.matches)

    def setMaxWidthText(self, text):
        self.max_width_text = text

    def getMaxWidthItem(self):
        return self.max_width_text

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.matches)):
            return QVariant()

        match_data = self.matches[index.row()]
        line_text = match_data['line_text']
        line_number = match_data['line_number']

        if role == Qt.ItemDataRole.DisplayRole:
            return line_text
        # elif role == Qt.ItemDataRole.CheckStateRole:
        #     return match_data.get('check_state', Qt.CheckState.Checked)
        elif role == Qt.ItemDataRole.UserRole:
            return line_number

        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        # if role == Qt.ItemDataRole.CheckStateRole:
        #     if index.isValid() and (0 <= index.row() < len(self.matches)):
        #         self.matches[index.row()]['check_state'] = Qt.CheckState(value)
        #         self.dataChanged.emit(index, index, [role])
        #         return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable
            #   |
            # Qt.ItemFlag.ItemIsUserCheckable
        )

    def setMatches(self, new_matches):
        self.beginResetModel()
        self.matches = new_matches
        self.endResetModel()

    def getCheckedMatches(self):
        return [
            (i, self.matches[i]) for i in range(len(self.matches))
            if self.matches[i].get('check_state', Qt.CheckState.Checked) != Qt.CheckState.Checked
        ]

    def getNotCheckedMatches(self):
        return [
            (i, self.matches[i]) for i in range(len(self.matches))
            if self.matches[i].get('check_state', Qt.CheckState.Unchecked) != Qt.CheckState.Checked
        ]


class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, highlight_color=QColor(Qt.GlobalColor.yellow)):
        super().__init__(parent)
        self.highlight_color = highlight_color
        self._parent = parent
        self._max_len_text = ""

    def setMaxLenText(self, text):
        self._max_len_text = text

    def paint(self, painter, option, index):
        painter.save()

        # Draw the background
        if option.state & QStyle.StateFlag.State_Selected:
            light_blue = QColor("#E0FFFF")
            painter.fillRect(option.rect, light_blue)
            # painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(QColor(Qt.GlobalColor.black))
        else:
            painter.fillRect(option.rect, option.palette.base())
            painter.setPen(option.palette.text().color())

        # Get the item data
        text = index.data(Qt.ItemDataRole.DisplayRole)
        # Draw the text
        # 使用 QStyleOptionViewItem 的 rect 属性来绘制文本
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        # 当self.result_view.setUniformItemSizes(True)，只计算一次，后续使用缓存的sizeHint，会导致listItem的width不够
        # 这里计算最大长度的text的sizeHint
        # text = index.data(Qt.ItemDataRole.DisplayRole)
        text = self._max_len_text

        # Get the font metrics from the application's default font
        # This is the correct approach in PyQt6
        metrics = QFontMetrics(QApplication.font())

        # Calculate size based on font metrics
        text_size = metrics.boundingRect(text).size()

        # Add a little padding and space for the checkbox
        width = text_size.width() + 20 + 25  # Checkbox width + padding
        height = metrics.height() + 5  # Some vertical padding

        return QSize(width, height)
