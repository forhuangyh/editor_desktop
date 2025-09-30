"""
Copyright (c) 2015
"""

from qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QSize, Qt,
    QStyledItemDelegate,
    QApplication,
    QListView, QStyle, QColor, QFontMetrics,
    QAbstractListModel, QModelIndex, QVariant, Qt,
    QLabel, QComboBox, pyqtSlot, QToolButton, QTimer
)

import constants
import components.internals
import settings
from xc_entity.book import book_manager
from gui.customeditor import CustomEditor


class ChapterList(QWidget):
    # Class variables
    name = "章节列表"
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
        # self.matches = None
        if self._current_book:
            try:
                self._current_book.chapter_list_updated.disconnect(self.handle_chapter_list_update)
                self._fixed_widget.editor_changed.disconnect(self.update_editor_reference)
                self._fixed_widget.editor_closed.disconnect(self.close_editor_reference)
                self._current_book = None
                self._chapter_list = None
            except (TypeError, RuntimeError):
                pass  # 忽略已断开的连接错误

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
        self.reg_list = {
            "章节匹配正则(Book Chapter 1)": r'^(.*?Chapter.*?)\r?\n?$',
            "章节匹配正则(第一章)": r'^(.*?第.*?章.*?)\r?\n?$',
        }
        self.last_index = 0
        self.init_ui()
        self._fixed_widget.editor_changed.connect(self.update_editor_reference)
        self._fixed_widget.editor_closed.connect(self.close_editor_reference)
        self.set_theme(settings.get_theme())

    def update_editor_reference(self, new_editor):
        """当fixed_widget的编辑器变化时，更新我们的_editor引用"""
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
            try:
                self._current_book.chapter_list_updated.disconnect(self.handle_chapter_list_update)
            except TypeError:
                pass

        self.find_input.setEditText(new_book.chapter_pattern.decode("utf-8"))
        # 2. 建立新的绑定
        if new_book:
            self.chapter_list = new_book.get_chapter_list()
            self._current_book = new_book
            # 连接新书的 chapterListUpdated 信号到槽函数
            self._current_book.chapter_list_updated.connect(self.handle_chapter_list_update)
            self.last_index = 0
            self.fill_match_list(new_book.chapter_list)
        else:
            self._current_book = None
            self.fill_match_list(new_book.chapter_list)

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

        self._editor = None

        # 1. 如果存在旧的书籍对象，先断开它与槽函数的连接
        if self._current_book:
            try:
                self._current_book.chapter_list_updated.disconnect(self.handle_chapter_list_update)
            except TypeError:
                pass

        self.find_input.setEditText("")
        self._current_book = None
        self.model.setMatches([])
        self.info_label.setText("章节总数：0")

    @pyqtSlot(list)
    def handle_chapter_list_update(self, chapter_list):
        """当书籍的章节列表更新时，此槽函数会被调用"""
        self.chapter_list = chapter_list
        self.find_input.setEditText(self._current_book.chapter_pattern.decode("utf-8"))
        self.fill_match_list(chapter_list)

    def init_ui(self):
        # 直接设置自身属性
        self.setWindowTitle("章节列表")
        self.resize(400, 600)  # 设置窗口初始大小

        # 主垂直布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # 设置布局间距

        # 1. 顶部查找行
        find_layout = QHBoxLayout()
        self.find_input = QComboBox()
        self.find_input.setEditable(True)  # 设置为可编辑
        # 可选：添加一些历史搜索项
        for lable, val in self.reg_list.items():
            self.find_input.addItem(lable, val)
        # self.find_input.setStyleSheet(self.settings_control_font.get("QLineEdit"))
        self.find_input.setPlaceholderText("请输入")
        self.find_input.setMinimumHeight(30)
        self.find_input.setMinimumWidth(100)

        self.search_button = QPushButton("提取")
        self.search_button.setMinimumHeight(30)
        self.search_button.setMinimumWidth(40)
        self.search_button.setMaximumWidth(50)

        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.search_button)

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

        # 4. 添加组件到主布局
        main_layout.addLayout(find_layout)
        main_layout.addLayout(info_button_layout)
        main_layout.addWidget(self.result_view)
        self.setLayout(main_layout)

        # # 连接信号槽
        self.search_button.clicked.connect(self._find_all)
        self.find_input.lineEdit().returnPressed.connect(self._find_all)
        self.find_input.activated.connect(self._on_change)
        self.result_view.clicked.connect(self.on_item_clicked)

        self.up_button.clicked.connect(self.on_up_clicked)
        self.down_button.clicked.connect(self.on_down_clicked)

        # 定时器，用于长按连续触发
        # self.up_repeat_timer = QTimer()
        # self.up_repeat_timer.setInterval(200)  # 100ms 触发一次
        # self.up_button.pressed.connect(self.on_up_button_pressed)
        # self.up_button.released.connect(self.on_up_button_released)
        # self.up_repeat_timer.timeout.connect(self.on_up_timer_timeout)

    # def on_up_timer_timeout(self):
    #     self.on_up_clicked()

    # def on_up_button_pressed(self):
    #     self.on_up_clicked()  # 第一次点击
    #     self.up_repeat_timer.start()  # 启动定时器，模拟长按

    # def on_up_button_released(self):
    #     self.up_repeat_timer.stop()  # 松开按钮，停止定时器

    def _on_change(self, index):
        search_text = self.find_input.currentData()
        # if search_text in self.reg_list:
        #     search_text = self.reg_list[search_text]
        self.find_input.setCurrentText(search_text)

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
        search_text = self.find_input.currentText()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入章节提取规则！")
            return

        book = self._current_book
        self.chapter_list = book.split_chapter_list(self._editor.text(), search_text)
        self.fill_match_list(self.chapter_list)

    def fill_match_list(self, chapter_list):
        """填充列表
        """
        match_list = []
        max_len_index = 0
        line_text_len = 0
        for index, chapter in enumerate(chapter_list):
            line_number, _ = self._editor.lineIndexFromPosition(chapter["start"])
            line_text = chapter["title"]
            match_list.append(
                {
                    'line_number': line_number,
                    'line_text': f"{index + 1}：{line_text}({chapter['word_count']})",
                    'match_data': chapter,
                    "text_count": 0,
                }
            )
            cur_len = len(line_text)
            if cur_len > line_text_len:
                max_len_index = index
                line_text_len = cur_len

        if match_list:
            self.model.setMatches(match_list)
            self.delegate.setMaxLenText(match_list[max_len_index]["line_text"])
            match_len = len(match_list)
            self.info_label.setText(f"章节总数：{match_len}")
            # 内容修改，定位回原来章节位置
            if self.last_index >= 0:
                if self.last_index >= match_len:
                    self.last_index = match_len - 1
                new_index = self.model.index(self.last_index, 0)
                self.result_view.setCurrentIndex(new_index)
                self.result_view.scrollTo(new_index)
        else:
            self.model.setMatches([])
            self.info_label.setText("章节总数：0")

    def on_item_clicked(self, index):
        """
        当 QListWidget 中的一个项目被点击时调用的槽函数。
        """
        self.last_index = index.row()
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

        # 更新 QLineEdit 的样式
        line_edit_style = (
            f"QLineEdit {{ "
            f"background-color: {main_bg}; "
            f"color: {theme['fonts']['default']['color']}; "
            f"border: 1px solid {theme['indication']['passiveborder']}; "
            f"selection-background-color: {theme['indication']['selection']}; "
            f"selection-color: {theme['fonts']['default']['color']}; "
            f"}}"
        )
        self.find_input.setStyleSheet(line_edit_style)
        # 设置固定字体
        self.find_input.setStyleSheet(self.settings_control_font.get("QLineEdit"))

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
