"""
Copyright (c) 2025

"""

from qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QAbstractItemView
)

import constants
import components.internals
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

    def __init__(self, editor, parent, main_form):
        # Initialize the superclass
        super().__init__()
        # Initialize components
        self.internals = components.internals.Internals(self, parent)
        # Store the main form and parent widget references
        self._parent = parent
        self._editor = editor
        self.main_form = main_form
        self.init_ui()

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
        self.find_input.setPlaceholderText("请输入查找内容")
        self.find_input.setMinimumHeight(30)

        self.settings_button = QPushButton("⚙️")  # 使用齿轮符号
        self.settings_button.setFixedWidth(40)
        self.settings_button.setMinimumHeight(30)

        self.search_button = QPushButton("查找")
        self.search_button.setMinimumHeight(30)

        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.settings_button)
        find_layout.addWidget(self.search_button)

        # 2. 替换行
        replace_layout = QHBoxLayout()
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("请输入替换内容")
        self.replace_input.setMinimumHeight(30)

        self.replace_all_button = QPushButton("全部替换")
        self.replace_all_button.setMinimumHeight(30)

        self.replace_button = QPushButton("替换")
        self.replace_button.setMinimumHeight(30)

        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.replace_all_button)
        replace_layout.addWidget(self.replace_button)

        # 3. 结果列表
        self.result_list = QListWidget()
        self.result_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.result_list.setMinimumHeight(300)

        # 4. 添加组件到主布局
        main_layout.addLayout(find_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addWidget(self.result_list)

        # 示例数据
        self.result_list.addItem("Dsa")
        self.result_list.addItem("Safd")

        self.setLayout(main_layout)

        # 连接点击事件
        self.result_list.itemClicked.connect(self.on_item_clicked)

    def change_editor(self, search_text, editor):
        """change
        """
        if isinstance(editor, CustomEditor):
            self._editor = editor
        self._search_text = search_text

    def enterEvent(self, event):
        """
        """
        if self._change:
            focused_tab = self.main_form.get_used_tab()
            if isinstance(focused_tab, CustomEditor):
                self._editor = focused_tab

        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        """
        if not self._change:
            self._change = True

        super().leaveEvent(event)

    def on_item_clicked(self, item):
        """
        当 QListWidget 中的一个项目被点击时调用的槽函数。

        参数:
        item (QListWidgetItem): 被点击的项目对象。
        """
        # 获取被点击项目的文本
        clicked_text = item.text()

        # 2. 将点击的文本设置到查找输入框
        # self.find_input.setText(clicked_text)

        print(f"你点击了项目: {clicked_text}")
