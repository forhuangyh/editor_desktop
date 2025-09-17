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
    QListWidget,
    QMessageBox,
    QTextDocument, QSize, Qt,
    QStyledItemDelegate,
    QListWidgetItem, QStyleOptionButton, QApplication,
    QListView, QEvent, QStyle, QColor
)

import constants
import components.internals
import settings
from gui.stylesheets import StyleSheetScrollbar


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
        # constants.constants.settings_control_font.get("QLineEdit", "")

        self.find_input.setStyleSheet(self.settings_control_font.get("QLineEdit"))
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
        self.replace_input.setStyleSheet(self.settings_control_font.get("QLineEdit"))
        self.replace_input.setMinimumHeight(30)

        # self.replace_all_button = QPushButton("全部替换")
        # self.replace_all_button.setMinimumHeight(30)
        # self.replace_all_button.setMinimumWidth(50)

        self.replace_button = QPushButton("替换")
        self.replace_button.setMinimumHeight(30)
        self.replace_button.setMinimumWidth(40)

        replace_layout.addWidget(self.replace_input)
        # replace_layout.addWidget(self.replace_all_button)
        replace_layout.addWidget(self.replace_button)

        self.result_list = QListWidget()
        self.result_list.setUniformItemSizes(True)  # 允许不同大小的项
        self.result_list.setWordWrap(True)  # 允许换行
        self.result_list.setTextElideMode(Qt.TextElideMode.ElideNone)  # 不省略文本

        # 使用自定义delegate 展示部分高亮
        self.result_list.setItemDelegate(HighlightDelegate(self.result_list))
        # 优化性能的设置
        self.result_list.setBatchSize(100)  # 批量处理数量
        self.result_list.setLayoutMode(QListView.LayoutMode.Batched)
        font_obj = self.settings_control_font.get("QListWidget")
        font_style = f"font-family: '{font_obj.split(";")[0]}'; font-size: {font_obj.split(";")[1]};"
        self.result_list.setStyleSheet(font_style)

        # 4. 添加组件到主布局
        main_layout.addLayout(find_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addWidget(self.result_list)
        self.setLayout(main_layout)

        # # 连接信号槽
        self.search_button.clicked.connect(self._find_all)
        self.find_input.returnPressed.connect(self._find_all)
        self.replace_button.clicked.connect(self._replace_all)
        self.result_list.itemDoubleClicked.connect(self.on_item_clicked)

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
        self.matches = matches
        self.add_rich_text_items(search_text, matches)

    def add_rich_text_items(self, search_text, matches):
        """添加到list
        """
        self.result_list.clear()
        if not matches:
            list_item = QListWidgetItem("无匹配项")
            list_item.setData(Qt.ItemDataRole.UserRole, 0)  # 例如存储行号
            self.result_list.addItem(list_item)
            return

        self.result_list.setUpdatesEnabled(False)  # 禁用更新以提高性能
        delegate = self.result_list.itemDelegate()
        if isinstance(delegate, HighlightDelegate):
            delegate.setSearchText(search_text)

        for index, item in enumerate(matches[:1000]):
            #  item=(0, match.start(), 0, match.end(), match.group())
            # select_text = item[4].decode('utf-8')
            line, _ = self._editor.lineIndexFromPosition(item[1])
            line_text = self._editor.line_list[line + 1]
            list_item = QListWidgetItem(line_text)
            # 设置项目标志，使其包含复选框并可选中
            list_item.setFlags(
                list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable
            )
            # 设置初始的复选框状态
            list_item.setCheckState(Qt.CheckState.Checked)
            # 可以存储额外数据到item中
            list_item.setData(Qt.ItemDataRole.UserRole, line)  # 例如存储行号
            self.result_list.addItem(list_item)

        self.result_list.setUpdatesEnabled(True)  # 重新启用更新
        # 滚动到顶部
        self.result_list.scrollToTop()

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
        for index in range(0, self.result_list.count()):
            if self.result_list.item(index).checkState() == Qt.CheckState.Checked:
                continue
            not_repalce_match_dict[index] = self.matches[index]

        matches = self._editor.replace_part(
            search_text,
            replace_text,
            not_repalce_match_dict,
            case_sensitive=False,
        )
        if not matches:
            self.result_list.clear()
            list_item = QListWidgetItem("文本内容有更新，无匹配项被替换")
            list_item.setData(Qt.ItemDataRole.UserRole, 0)  # 例如存储行号
            self.result_list.addItem(list_item)

    def _clear_highlight(self):
        """清除所有高亮"""
        editor = self._fixed_widget.editor
        editor.clear_highlights()

    def on_item_clicked(self, item):
        """
        当 QListWidget 中的一个项目被点击时调用的槽函数。
        """
        # 获取被点击项目的文本
        # clicked_text = item.text()
        line_number = item.data(Qt.ItemDataRole.UserRole)
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

        # 更新 QListWidget 的样式
        list_style = (
            f"QListWidget {{ "
            f"background-color: {main_bg}; "
            f"color: {theme['fonts']['default']['color']}; "
            f"border: 1px solid {theme['indication']['passiveborder']}; "
            f"}}"
            f"QListWidget::item:selected {{ "
            f"background-color: {theme['indication']['selection']}; "
            f"color: {theme['fonts']['default']['color']}; "
            f"}}"
        )
        self.result_list.setStyleSheet(list_style)

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
        self.result_list.verticalScrollBar().setStyleSheet(scrollbar_style)

        # # 更新 HighlightDelegate 的高亮颜色
        # delegate = self.result_list.itemDelegate()
        # if isinstance(delegate, HighlightDelegate):
        #     # 使用find指示器的高亮颜色
        #     highlight_color = QColor(theme['indication']['find'].replace('64', 'ff'))  # 移除透明度
        #     delegate.highlight_color = highlight_color

        # 刷新列表视图以应用新的高亮颜色
        self.result_list.viewport().update()

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


class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, highlight_color=Qt.GlobalColor.yellow):
        super().__init__(parent)
        self.highlight_color = highlight_color
        self.search_text = ""

    def setSearchText(self, text):
        self.search_text = text.lower()

    # def editorEvent(self, event, model, option, index):
    #     # Ensure the index is valid and the item has a checkable flag
    #     if not index.isValid() or not (index.flags() & Qt.ItemFlag.ItemIsUserCheckable):
    #         return super().editorEvent(event, model, option, index)

    #     # Process checkbox clicks
    #     if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
    #         # Calculate the checkbox rectangle
    #         style = QApplication.style()
    #         checkbox_rect = style.subElementRect(
    #             QStyle.SubElement.SE_ItemViewItemCheckIndicator, option, self.parent()
    #         )

    #         # Check if the click was inside the checkbox rectangle
    #         if checkbox_rect.contains(event.pos()):
    #             # Get the current check state
    #             current_state = index.data(Qt.ItemDataRole.CheckStateRole)

    #             # Toggle the check state
    #             new_state = Qt.CheckState.Checked if current_state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked

    #             # Set the new data in the model
    #             model.setData(index, new_state.value, Qt.ItemDataRole.CheckStateRole)

    #             # Explicitly trigger an update for only the edited item's area.
    #             # This is more efficient than updating the entire widget.
    #             self.parent().viewport().update(option.rect)

    #             # Return True to indicate that we have handled the event
    #             return True

    #     return super().editorEvent(event, model, option, index)

    def editorEvent(self, event, model, option, index):
        # 处理鼠标事件
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在复选框区域
            check_state = index.data(Qt.ItemDataRole.CheckStateRole)
            if check_state is not None:
                # 获取复选框的矩形区域
                checkbox_rect = QStyle.alignedRect(
                    Qt.LayoutDirection.LeftToRight,
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                    QSize(20, 20),
                    option.rect
                )

                # 如果点击在复选框区域
                if checkbox_rect.contains(event.pos()):
                    # 切换复选框状态
                    new_state = Qt.CheckState.Unchecked.value if check_state == Qt.CheckState.Checked.value else Qt.CheckState.Checked.value

                    # 更新模型数据
                    model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)

                    # 只重绘当前项，而不是整个视图
                    # self.parent().update(index)
                    self.parent().viewport().update(checkbox_rect)
                    # self.parent().update(option.rect)
                    # index = index.data(Qt.ItemDataRole.UserRole)
                    # 阻止事件继续传播
                    return True

        # 其他情况调用父类实现
        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        # 获取原始文本
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return

        print(index.data(Qt.ItemDataRole.UserRole))

        # 获取 QListWidgetItem 的复选框状态
        check_state = index.data(Qt.ItemDataRole.CheckStateRole)

        # 保存原始画笔和刷子
        painter.save()

        # 绘制背景（包括选中状态）
        if option.state & QStyle.StateFlag.State_Selected:
            # light_blue = QColor("#ADD8E6")  # Light blue color
            light_blue = QColor("#E0FFFF")
            painter.fillRect(option.rect, light_blue)
        else:
            painter.fillRect(option.rect, option.palette.base())

        # 设置文本颜色
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        # 初始化text_rect为option.rect
        text_rect = option.rect

        # 如果有复选框，绘制复选框
        if check_state is not None:
            # 创建一个QStyleOptionButton来绘制复选框
            checkbox_option = QStyleOptionButton()
            checkbox_option.rect = QStyle.alignedRect(
                Qt.LayoutDirection.LeftToRight,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                QSize(20, 20),  # 复选框的大小
                option.rect
            )
            checkbox_option.state = option.state
            # checkbox_option.state |= QStyle.StateFlag.State_On
            # # 设置复选框状态 - 确保使用正确的状态值
            if check_state == Qt.CheckState.Checked.value:
                checkbox_option.state |= QStyle.StateFlag.State_On
            else:
                checkbox_option.state |= QStyle.StateFlag.State_Off
            # elif check_state == Qt.CheckState.PartiallyChecked:
            #     checkbox_option.state |= QStyle.StateFlag.State_NoChange

            # 绘制复选框
            QApplication.style().drawControl(
                QStyle.ControlElement.CE_CheckBox,
                checkbox_option,
                painter
            )
            # 调整文本绘制区域，为复选框留出空间
            text_rect = option.rect
            text_rect.setLeft(checkbox_option.rect.right() + 3)  # 5是复选框和文本之间的间距

            # 处理文本高亮
        doc = QTextDocument()
        doc.setHtml(self.highlightText(text))
        doc.setDefaultFont(option.font)

        doc.setTextWidth(int(option.rect.width()))
        # 绘制文本
        painter.translate(option.rect.topLeft())
        doc.drawContents(painter)
        painter.restore()

    def highlightText(self, text):
        if not self.search_text:
            return text

        lower_text = text.lower()
        result = []
        last_pos = 0
        search_len = len(self.search_text)

        while True:
            pos = lower_text.find(self.search_text, last_pos)
            if pos == -1:
                result.append(text[last_pos:])
                break
            # 添加前面的普通文本
            result.append(text[last_pos:pos])
            # 添加高亮文本
            result.append(f'<span style="background-color:{self.highlight_color.name};">'
                          f'{text[pos:pos + search_len]}</span>')
            last_pos = pos + search_len

        return ''.join(result)

    def sizeHint(self, option, index):
        # 使用QTextDocument计算文本大小
        doc = QTextDocument()
        doc.setHtml(self.highlightText(index.data(Qt.ItemDataRole.DisplayRole)))
        doc.setDefaultFont(option.font)
        doc.setTextWidth(int(option.rect.width()))
        return QSize(int(doc.idealWidth()), int(doc.size().height()))
