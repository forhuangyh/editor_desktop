"""
Copyright (c) 2015

存放固定的部件，如搜索部件，特殊替换部件，搜索结果部件等


"""

from xc_gui.search_replace_dialog import SearchReplaceDialog
from xc_gui.chapter_list import ChapterList
from xc_gui.special_replace import SpecialReplace


class FixedWidget(object):
    """
    存放固定的部件，如搜索部件，特殊替换部件，搜索结果部件等
    """
    chapter_list = None
    search_dialog = None
    special_replace = None

    def __init__(self, main_form):
        """init
        """
        self.main_form = main_form

    def open_find_replace_dialog(self):
        """初始化常规查找替换窗口
        """
        # 创建新的树形tab
        # Create the new scintilla document in the selected basic widget
        focused_tab = self.main_form.get_used_tab()
        search_text = focused_tab.selectedText()
        if self.search_dialog is None:
            self.search_dialog = SearchReplaceDialog(search_text, focused_tab, self)
        else:
            self.search_dialog.change_editor(search_text, focused_tab)
        # search_dialog.center()
        self.search_dialog.show()

    def get_used_tab(self):
        """
        Get the tab that was last used (if none return the main tab)
        """
        focused_tab = self.get_tab_by_focus()
        # Check if any tab is focused
        if focused_tab is None:
            focused_tab = self.get_largest_window()
        return focused_tab
