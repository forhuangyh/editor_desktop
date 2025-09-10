
from qt import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
from qt import QColor
import constants
import qt
import components.internals


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

    def __init__(self, search_text, editor, main_form):
        # Initialize the superclass
        super().__init__(main_form)
        # Initialize components
        # self.internals = components.internals.Internals(self, parent)
        # Store the main form and parent widget references
        current_flags = self.windowFlags()
        self.setWindowFlags(current_flags | qt.Qt.WindowType.WindowStaysOnTopHint)
        self._editor = editor
        self._parent = main_form
        self.main_form = main_form
        # Set font family and size
        self._search_text = search_text

        self.init_ui()

    def change_editor(self, search_text, editor):
        self._editor = editor
        self._search_text = search_text

    def init_ui(self):
        self.setWindowTitle("搜索和替换")
        self.setFixedSize(400, 200)

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

        self._regex.checkStateChanged

        # # 初始化高亮指示器
        # self._init_indicator()

    def _find_next(self):
        """查找下一个匹配项并高亮"""
        search_text = self._search_input.text()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        self._editor.find_text(
            search_text, case_sensitive=self._case_sensitive.isChecked(),
            regular_expression=self._regex.isChecked(),
            whole_words=self._whole_word.isChecked()
        )

    def _find_all(self):
        """查找下一个匹配项并高亮"""
        search_text = self._search_input.text()
        if not search_text:
            QMessageBox.warning(self, "警告", "请输入搜索内容！")
            return
        self._editor.highlight_text(
            search_text, case_sensitive=self._case_sensitive.isChecked(),
            regular_expression=self._regex.isChecked(),
            whole_words=self._whole_word.isChecked()
        )

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

    def _clear_highlight(self):
        """清除所有高亮"""
        self._editor.clear_highlights()

    # def showEvent(self, event):
    #     # self.center()
    #     # super().showEvent(event)

    #     event.accept()

    # def center(self):
    #     import functions
    #     if self.parent() is not None:
    #         qr = self.frameGeometry()
    #         geo = self.parent().frameGeometry()
    #         cp = functions.create_point(
    #             int((geo.width() / 2) - (qr.width() / 2)),
    #             int((geo.height() / 2) - (qr.height() / 2)),
    #         )
    #         self.move(cp)
    #     else:
    #         qr = self.frameGeometry()
    #         cp = self.screen().geometry().center()
    #         qr.moveCenter(cp)
    #         self.move(qr.topLeft())

    # def _init_indicator(self):
    #     """初始化高亮指示器"""
    #     # 使用 INDIC_ROUNDBOX（圆角框）或 INDIC_PLAIN（普通下划线）
    #     self._editor.indicatorDefine(QsciScintilla.IndicatorStyle.RoundBoxIndicator, 0)  # 修正：使用枚举类型
    #     self._editor.setIndicatorForegroundColor(QColor("#FFD700"), 0)  # 金色高亮
    #     self._editor.setIndicatorHoverForegroundColor(QColor("#FFA500"), 0)  # 悬停颜色

    # def _get_search_flags(self):
    #     """获取搜索标志"""
    #     flags = 0
    #     if self._case_sensitive.isChecked():
    #         flags |= QsciScintilla.SCFIND_MATCHCASE
    #     if self._whole_word.isChecked():
    #         flags |= QsciScintilla.SCFIND_WHOLEWORD
    #     if self._regex.isChecked():
    #         flags |= QsciScintilla.SCFIND_REGEXP
    #     return flags

    # def _highlight_all_matches(self, search_text):
    #     """高亮所有匹配项"""
    #     if not search_text:
    #         return

    #     flags = self._get_search_flags()
    #     self._editor.clearIndicatorRange(0, 0, self._editor.lines(), 0, 0)  # 清除旧高亮

    #     # 从头开始搜索
    #     self._editor.setCursorPosition(0, 0)
    #     found = True
    #     while found:
    #         found = self._editor.findFirst(search_text, False, False, False, True, flags)
    #         if found:
    #             start_pos = self._editor.getSelectionStart()
    #             end_pos = self._editor.getSelectionEnd()
    #             self._editor.fillIndicatorRange(0, start_pos, end_pos, 0)  # 高亮当前匹配项
    #             self._editor.findNext()  # 继续搜索下一个
