"""
Copyright (c) 2015

存放固定的部件，如搜索部件，特殊替换部件，搜索结果部件等


"""
import qt
from xc_gui.search_replace_dialog import SearchReplaceDialog
from xc_gui.chapter_list import ChapterList
from xc_gui.special_replace import SpecialReplace
from xc_gui.question_list import QuestionList
from gui.customeditor import CustomEditor


class FixedWidget(qt.QObject):
    """
    存放固定的部件，如搜索部件，特殊替换部件，搜索结果部件等
    """
    chapter_list = None
    search_dialog = None
    special_replace = None
    question_list = None
    editor = None
    editor_changed = qt.pyqtSignal(qt.QObject)
    editor_closed = qt.pyqtSignal(qt.QObject)

    def __init__(self, main_form):
        """init
        """
        super().__init__(main_form)
        self.main_form = main_form
        self.editor = None

    def change_editor(self, widget):
        """change
        """
        if isinstance(widget, CustomEditor):
            self.editor = widget
            self.editor_changed.emit(self.editor)  # 当编辑器变化时发出信号

    def close_editor(self, widget):
        """close_editor
        """
        if isinstance(widget, CustomEditor):
            if self.editor != widget:
                return
            self.editor_closed.emit(self.editor)  # 当编辑器关闭时发出信号
            self.editor = None

    def open_find_replace_dialog(self):
        """open_find_replace_dialog
        """
        focused_editor = self.editor
        search_text = focused_editor.selectedText()
        if self.search_dialog:
            self.search_dialog.change_editor(search_text, focused_editor)
            if not self.search_dialog.isVisible():
                self.search_dialog.show()
        else:
            self.search_dialog = SearchReplaceDialog(search_text, self.main_form, self)
            self.search_dialog.show()

        self.search_dialog.activateWindow()
        self.search_dialog.setFocus()
        self.search_dialog._search_input.setFocus()

    def open_chapter_list(self, tab_widget, document_name=""):
        """open_chapter_list"""

        focused_editor = self.editor
        if self.chapter_list:
            self.chapter_list.update_editor_reference(focused_editor)
            return self.chapter_list

        new_chapter_list = ChapterList(self, tab_widget, self.main_form)
        new_chapter_list_tab_index = tab_widget.addTab(new_chapter_list, document_name)
        # 禁止关闭
        tab_widget.tabBar().setTabButton(new_chapter_list_tab_index, qt.QTabBar.ButtonPosition.RightSide, None)
        # Make new tab visible
        tab_widget.setCurrentIndex(new_chapter_list_tab_index)
        self.chapter_list = tab_widget.widget(new_chapter_list_tab_index)
        return self.chapter_list

    def open_special_replace(self, tab_widget, document_name=""):
        """open_special_replace"""
        search_text = ""
        focused_editor = self.editor
        if self.special_replace:
            self.special_replace.update_editor_reference(focused_editor)
            return self.special_replace

        if focused_editor:
            search_text = focused_editor.selectedText()

        new_special_replace = SpecialReplace(search_text, self, tab_widget, self.main_form)
        new_tab_index = tab_widget.addTab(new_special_replace, document_name)
        # 禁止关闭
        tab_widget.tabBar().setTabButton(new_tab_index, qt.QTabBar.ButtonPosition.RightSide, None)
        # Make new tab visible
        tab_widget.setCurrentIndex(new_tab_index)
        self.special_replace = tab_widget.widget(new_tab_index)

        return self.special_replace

    def open_question_list(self, tab_widget, document_name=""):
        """question_list"""

        focused_editor = self.editor
        if self.question_list:
            self.question_list.update_editor_reference(focused_editor)
            return self.question_list

        new_question_list = QuestionList(self, tab_widget, self.main_form)
        new_question_list_tab_index = tab_widget.addTab(new_question_list, document_name)
        # 禁止关闭
        tab_widget.tabBar().setTabButton(new_question_list_tab_index, qt.QTabBar.ButtonPosition.RightSide, None)
        # Make new tab visible
        tab_widget.setCurrentIndex(new_question_list_tab_index)
        self.question_list = tab_widget.widget(new_question_list_tab_index)
        return self.question_list
