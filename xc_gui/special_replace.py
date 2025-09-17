"""
Copyright (c) 2025

"""
import qt
from qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QSize, Qt,
    QStyledItemDelegate,
    QStyleOptionButton, QApplication,
    QListView, QEvent, QStyle, QColor, QFontMetrics,
    QAbstractListModel, QModelIndex, QVariant, QRect, Qt
)

import constants
import components.internals
import settings
from gui.stylesheets import StyleSheetScrollbar
from gui.customeditor import CustomEditor


class SpecialReplace(QWidget):

    name = "特殊替换"
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
        self.matches = None

    def __init__(self, search_text, fixed_widget, parent, main_form):
        # Initialize the superclass
        super().__init__()
        # Initialize components
        self.internals = components.internals.Internals(self, parent)
        # Store the main form and parent widget references
        self._parent = parent
        self._fixed_widget = fixed_widget
        self._editor = self._fixed_widget.editor
        self.main_form = main_form
        self._search_text = search_text
        self.settings_control_font = settings.get("settings_control_font")
        self.init_ui()
        self._fixed_widget.editor_changed.connect(self.update_editor_reference)
        self.set_theme(settings.get_theme())

    def update_editor_reference(self, new_editor):
        """当fixed_widget的编辑器变化时，更新我们的_editor引用"""
        self._editor = new_editor

    def init_ui(self):
        # 直接设置自身属性
        self.setWindowTitle("查找和替换")
        self.resize(400, 600)  # 设置窗口初始大小

        # 主垂直布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # 设置布局间距

        # 1. 顶部查找行
        find_layout = QHBoxLayout()
        self.find_input = QLineEdit()

        # self.find_input.setStyleSheet(self.settings_control_font.get("QLineEdit"))
        self.find_input.setPlaceholderText("请输入查找内容")
        self.find_input.setMinimumHeight(30)

        self.search_button = QPushButton("查找")
        self.search_button.setMinimumHeight(30)
        self.search_button.setMinimumWidth(40)

        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.search_button)

        # 2. 替换行
        replace_layout = QHBoxLayout()
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("请输入替换内容")

        self.replace_input.setMinimumHeight(30)

        self.replace_button = QPushButton("替换")
        self.replace_button.setMinimumHeight(30)
        self.replace_button.setMinimumWidth(40)

        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.replace_button)

        # 替换 QListWidget 为 QListView
        self.result_view = QListView()
        self.result_view.setUniformItemSizes(True)
        self.result_view.setWordWrap(False)
        self.result_view.setTextElideMode(Qt.TextElideMode.ElideRight)

        # 创建并设置自定义模型和代理
        self.model = SearchMatchModel()
        self.result_view.setModel(self.model)
        self.delegate = HighlightDelegate(self.result_view)
        self.result_view.setItemDelegate(self.delegate)

        # 4. 添加组件到主布局
        main_layout.addLayout(find_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addWidget(self.result_view)
        self.setLayout(main_layout)

        # # 连接信号槽
        self.search_button.clicked.connect(self._find_all)
        self.find_input.returnPressed.connect(self._find_all)
        self.replace_button.clicked.connect(self._replace_all)
        self.result_view.doubleClicked.connect(self.on_item_clicked)

    def _find_all(self):
        """查找下一个匹配项并高亮"""
        search_text = self.find_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        if search_text.find("\n") > -1:
            QMessageBox.warning(self, "警告", "搜索内容中有换行符号")
            return

        self._editor.clear_highlights()
        matches = self._editor.highlight_text(
            search_text, case_sensitive=False,
            regular_expression=False,
            whole_words=False
        )
        match_list = []
        for match in matches:
            line_number, _ = self._editor.lineIndexFromPosition(match[1])
            line_text = self._editor.line_list[line_number + 1]
            match_list.append(
                {
                    'line_number': line_number,
                    'line_text': line_text,
                    'match_data': match,
                    'check_state': Qt.CheckState.Checked
                }
            )
        self.model.setMatches(match_list)
        self.delegate.setSearchText(search_text)

    def _replace_all(self):
        """替换所有匹配项"""
        search_text = self.find_input.text().strip()
        replace_text = self.replace_input.text().strip()

        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        if search_text.find("\n") > -1:
            QMessageBox.warning(self, "警告", "搜索内容中有换行符号")
            return
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入替换内容！")
            return
        if search_text.find("\n") > -1:
            QMessageBox.warning(self, "警告", "替换内容中有换行符号")
            return

        not_repalce_match_dict = {}
        for index, match in self.model.getNotCheckedMatches():
            not_repalce_match_dict[index] = match['match_data']

        matches = self._editor.replace_part(
            search_text,
            replace_text,
            not_repalce_match_dict,
            case_sensitive=False,
        )
        if not matches:
            self.result_view.clear()
            # list_item = QListWidgetItem("文本内容有更新，无匹配项被替换")
            # list_item.setData(Qt.ItemDataRole.UserRole, 0)  # 例如存储行号
            # self.result_list.addItem(list_item)

    def _clear_highlight(self):
        """清除所有高亮"""
        editor = self._fixed_widget.editor
        editor.clear_highlights()

    def on_item_clicked(self, index):
        """
        当 QListWidget 中的一个项目被点击时调用的槽函数。
        """
        # 获取被点击项目的文本
        # clicked_text = item.text()
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
        self.replace_input.setStyleSheet(line_edit_style)
        # 设置固定字体
        self.find_input.setStyleSheet(self.settings_control_font.get("QLineEdit"))
        self.replace_input.setStyleSheet(self.settings_control_font.get("QLineEdit"))

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
        self.replace_button.setStyleSheet(button_style)

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

        # # 更新 HighlightDelegate 的高亮颜色
        # delegate = self.result_list.itemDelegate()
        # if isinstance(delegate, HighlightDelegate):
        #     # 使用find指示器的高亮颜色
        #     highlight_color = QColor(theme['indication']['find'].replace('64', 'ff'))  # 移除透明度
        #     delegate.highlight_color = highlight_color

        # 刷新列表视图以应用新的高亮颜色
        self.result_view.viewport().update()

        # 更新 delegate 的高亮颜色
        # find_color = QColor(theme['indication']['find'])
        # self.delegate.highlight_color = find_color
        # # 强制视图重新绘制以应用新颜色
        # self.result_view.viewport().update()

        # # 设置上下文菜单样式（如果有）
        # if hasattr(self, 'context_menu'):
        #     context_menu_style = (
        #         f"QMenu {{ "
        #         f"background-color: {theme['context-menu-background']}; "
        #         f"border: 1px solid {theme['context-menu-hex-edge']}; "
        #         f"}}"
        #         f"QMenu::item:selected {{ "
        #         f"background-color: {theme['indication']['selection']}; "
        #         f"}}"
        #     )
        #     self.context_menu.setStyleSheet(context_menu_style)

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

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.matches)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.matches)):
            return QVariant()

        match_data = self.matches[index.row()]
        line_text = match_data['line_text']
        line_number = match_data['line_number']

        if role == Qt.ItemDataRole.DisplayRole:
            return line_text
        elif role == Qt.ItemDataRole.CheckStateRole:
            return match_data.get('check_state', Qt.CheckState.Checked)
        elif role == Qt.ItemDataRole.UserRole:
            return line_number

        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.CheckStateRole:
            if index.isValid() and (0 <= index.row() < len(self.matches)):
                self.matches[index.row()]['check_state'] = Qt.CheckState(value)
                self.dataChanged.emit(index, index, [role])
                return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsUserCheckable
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
        self.search_text = ""
        self._parent = parent

    def setSearchText(self, text):
        self.search_text = text.lower()

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
        check_state = index.data(Qt.ItemDataRole.CheckStateRole)
        line_number = index.data(Qt.ItemDataRole.UserRole)

        # --- Draw Checkbox ---
        checkbox_rect = QStyle.alignedRect(
            Qt.LayoutDirection.LeftToRight,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            QSize(20, 20),
            option.rect
        )

        style_option = QStyleOptionButton()
        style_option.rect = checkbox_rect
        style_option.state = option.state | QStyle.StateFlag.State_Enabled

        if check_state == Qt.CheckState.Checked:
            style_option.state |= QStyle.StateFlag.State_On
        else:
            style_option.state |= QStyle.StateFlag.State_Off

        QApplication.style().drawControl(QStyle.ControlElement.CE_CheckBox, style_option, painter)

        # --- Draw Text with Highlighting ---
        text_rect = option.rect.adjusted(checkbox_rect.width() + 5, 0, 0, 0)
        line_number = line_number + 1
        lower_text = f"{line_number}: {text.lower()}"
        text = f"{line_number}: {text}"
        last_pos = 0
        search_len = len(self.search_text)
        line_number_len = len(f"{line_number}:") + 1

        while True:
            if last_pos == 0:
                pos = lower_text.find(self.search_text, last_pos + line_number_len)
            else:
                pos = lower_text.find(self.search_text, last_pos)

            if pos == -1:
                painter.drawText(text_rect, Qt.TextFlag.TextSingleLine, text[last_pos:])
                break

            # Draw preceding text
            pre_text = text[last_pos:pos]
            pre_text_width = painter.fontMetrics().horizontalAdvance(pre_text)
            painter.drawText(text_rect, Qt.TextFlag.TextSingleLine, pre_text)

            # Draw highlighted text
            highlight_text = text[pos: pos + search_len]
            highlight_text_width = painter.fontMetrics().horizontalAdvance(highlight_text)

            highlight_rect = QRect(
                text_rect.x() + pre_text_width,
                text_rect.y(),
                highlight_text_width,
                text_rect.height()
            )

            # Draw highlight background
            painter.fillRect(highlight_rect, self.highlight_color)

            # Draw highlighted text (on top of the highlight background)
            painter.drawText(highlight_rect, Qt.TextFlag.TextSingleLine, highlight_text)

            # Advance the text rectangle for the next part
            text_rect.setLeft(text_rect.left() + pre_text_width + highlight_text_width)
            last_pos = pos + search_len

        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole)

        # Get the font metrics from the application's default font
        # This is the correct approach in PyQt6
        metrics = QFontMetrics(QApplication.font())

        # Calculate size based on font metrics
        text_size = metrics.boundingRect(text).size()

        # Add a little padding and space for the checkbox
        width = text_size.width() + 20 + 5  # Checkbox width + padding
        height = metrics.height() + 5  # Some vertical padding

        return QSize(width, height)
