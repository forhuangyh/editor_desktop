"""
Copyright (c) 2015
"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
import qt
import data
import constants
import components.actionfilter
import components.hotspots
import components.internals
import settings
import lexers

import gui.contextmenu
import gui.baseeditor


class ChapterList(QTreeWidget):
    # Class variables
    name = "chapter_list"
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

    def __init__(self, parent, main_form):
        # Initialize the superclass
        super().__init__()
        # Initialize components
        self.internals = components.internals.Internals(self, parent)
        # Store the main form and parent widget references
        self._parent = parent
        self.main_form = main_form
        # Set font family and size
        self.init_ui()

    def init_ui(self):
        # 直接设置自身属性
        self.setHeaderLabels(["项目"])
        self.setIndentation(20)
        # 添加默认项目到自身
        self.add_default_items()
        # 连接双击信号到自身
        self.itemDoubleClicked.connect(self.handle_item_double_click)
        # 展开所有项目
        self.expandAll()

    # def mousePressEvent(self, event):
    #     """Function connected to the clicked signal of the tree display"""
    #     super().mousePressEvent(event)
    #     # Set the focus
    #     self.setFocus()
    #     QMessageBox.information(self, "项目信息", "test")

    def add_default_items(self):
        """添加三个默认项目"""
        # 创建父项目
        projects = [
            {
                "name": "定位",
                "children": [
                    {"name": "第一行"},
                    {"name": "第二行"},
                    {"name": "第三行"}
                ]
            }
        ]
        # 添加项目到树中
        for project in projects:
            parent_item = QTreeWidgetItem()
            parent_item.setText(0, project["name"])
            # parent_item.setText(1, project["description"])

            # 添加子项目
            for child in project["children"]:
                child_item = QTreeWidgetItem()
                child_item.setText(0, child["name"])
                # child_item.setText(1, child["description"])
                parent_item.addChild(child_item)

            self.addTopLevelItem(parent_item)

    def handle_item_double_click(self, item, column):
        """处理项目双击事件"""
        # 创建消息内容
        from gui.customeditor import CustomEditor
        cur_editor = None
        cur_tab = None
        cur_index = 0
        for w in self.main_form.get_all_windows():
            for i in range(w.count()):
                widget = w.widget(i)
                if isinstance(widget, CustomEditor):
                    cur_editor = widget
                    cur_index = i
                    cur_tab = w
                    break
        cur_tab.setCurrentIndex(cur_index)

        index_item = self.currentIndex()
        cur_editor.goto_line(index_item.row() + 1)
        cur_editor.setFocus()
        current_line = cur_editor.getCursorPosition()[0]
        line_length = len(cur_editor.text(current_line))
        # 设置行选择范围
        start = cur_editor.positionFromLineIndex(current_line, 0)
        end = start + line_length - 1
        cur_editor.clear_highlights()
        cur_editor.set_indicator("highlight")
        cur_editor.highlight_raw([(0, start, 0, end)])
