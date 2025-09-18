
from qt import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
from qt import QColor
import constants
import qt
import components.internals
from gui.customeditor import CustomEditor


class SearchReplaceDialog(QDialog):
    # Class variables
    name = "search and replace"
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
        pass

    def __init__(self, search_text, main_form, fixed_widget):
        # Initialize the superclass
        super().__init__(main_form)
        # Initialize components
        # self.internals = components.internals.Internals(self, parent)
        # Store the main form and parent widget references
        current_flags = self.windowFlags()
        self.setWindowFlags(current_flags | qt.Qt.WindowType.WindowStaysOnTopHint)
        self._fixed_widget = fixed_widget
        self._editor = self._fixed_widget.editor
        self._parent = main_form
        self.main_form = main_form
        self._search_text = search_text
        self._fixed_widget.editor_changed.connect(self.update_editor_reference)
        self.init_ui()

    def update_editor_reference(self, new_editor):
        """当fixed_widget的编辑器变化时，更新我们的_editor引用"""
        self._editor = new_editor

    def change_editor(self, search_text, editor):
        """change
        """
        if isinstance(editor, CustomEditor):
            self._editor = editor
            self._search_text = search_text
            self._search_input.setText(self._search_text)

    def init_ui(self):
        self.setWindowTitle("搜索和替换")
        self.setFixedSize(460, 200)

        # 搜索部分
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self._search_input = QLineEdit()
        search_layout.addWidget(self._search_input)
        self._search_input.setText(self._search_text)

        # 替换部分
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("替换:"))
        self._replace_input = QLineEdit()
        replace_layout.addWidget(self._replace_input)

        # 选项
        options_layout = QHBoxLayout()
        self._case_sensitive = QCheckBox("区分大小写")
        self._whole_word = QCheckBox("全词匹配")
        self._regex = QCheckBox("正则表达式")
        options_layout.addWidget(self._case_sensitive)
        options_layout.addWidget(self._whole_word)
        options_layout.addWidget(self._regex)

        # 按钮
        button_layout = QHBoxLayout()
        find_next_btn = QPushButton("查找下一个")
        find_all_btn = QPushButton("查找全部")
        replace_btn = QPushButton("替换")
        replace_all_btn = QPushButton("全部替换")
        clear_highlight_btn = QPushButton("清除高亮")

        button_layout.addWidget(find_next_btn)
        button_layout.addWidget(find_all_btn)
        button_layout.addWidget(replace_btn)
        button_layout.addWidget(replace_all_btn)
        button_layout.addWidget(clear_highlight_btn)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(search_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # # 连接信号槽
        find_next_btn.clicked.connect(self._find_next)
        find_all_btn.clicked.connect(self._find_all)
        replace_btn.clicked.connect(self._replace)
        replace_all_btn.clicked.connect(self._replace_all)
        clear_highlight_btn.clicked.connect(self._clear_highlight)
        self._case_sensitive.stateChanged.connect(self.on_case_sensitive_changed)
        self._whole_word.stateChanged.connect(self.on_whole_word_changed)
        self._regex.stateChanged.connect(self.on_regex_changed)

        # # 初始化高亮指示器
        # self._init_indicator()
    def on_case_sensitive_changed(self, state):
        if state == qt.Qt.CheckState.Checked.value:
            self._regex.setChecked(False)

    def on_whole_word_changed(self, state):
        if state == qt.Qt.CheckState.Checked.value:
            self._regex.setChecked(False)

    def on_regex_changed(self, state):
        if state == qt.Qt.CheckState.Checked.value:
            self._case_sensitive.setChecked(False)
            self._whole_word.setChecked(False)

    def _find_next(self):
        """查找下一个匹配项并高亮"""
        search_text = self._search_input.text()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        result = self._editor.find_text(
            search_text, case_sensitive=self._case_sensitive.isChecked(),
            regular_expression=self._regex.isChecked(),
            whole_words=self._whole_word.isChecked()
        )
        if result == constants.SearchResult.NOT_FOUND:
            self._editor.clear_highlights()
            QMessageBox.warning(self, "警告", "查询不到匹配项")

    def _find_all(self):
        """查找下一个匹配项并高亮"""
        search_text = self._search_input.text()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        result = self._editor.highlight_text(
            search_text, case_sensitive=self._case_sensitive.isChecked(),
            regular_expression=self._regex.isChecked(),
            whole_words=self._whole_word.isChecked()
        )
        if not result:
            self._editor.clear_highlights()
            QMessageBox.warning(self, "警告", "查询不到匹配项")

    def _replace(self):
        """替换当前匹配项"""
        search_text = self._search_input.text()
        replace_text = self._replace_input.text()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        self._editor.find_and_replace(
            search_text, replace_text,
            case_sensitive=self._case_sensitive.isChecked(),
            regular_expression=self._regex.isChecked(),
            whole_words=self._whole_word.isChecked()
        )

    def _replace_all(self):
        """替换所有匹配项"""
        search_text = self._search_input.text()
        replace_text = self._replace_input.text()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        self._editor.replace_all(
            search_text, replace_text,
            case_sensitive=self._case_sensitive.isChecked(),
            regular_expression=self._regex.isChecked(),
            whole_words=self._whole_word.isChecked()
        )
        QMessageBox.information(self, "信息", "替换完成")

    def _clear_highlight(self):
        """清除所有高亮"""
        self._editor.clear_highlights()
