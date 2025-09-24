"""
问题类: 属性，方法
"""
import re
from xc_common.word_count import word_count_func


from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class Question(QObject):
    """问题列表管理功能"""

    question_list_updated = pyqtSignal(list)

    def __init__(self, cp_book_id, parent=None):
        """初始化书籍实例
        """
        super().__init__(parent)
        self.cp_book_id = cp_book_id
        self.question_list = []

    def refresh_question_list(self, text):
        if not text:
            return
        if not self.chapter_pattern:
            return
        self.split_question_list(text)

    def split_question_list(self, text, chapter_pattern=None):
        """获取问题列表
        编辑器是用byte定位，这里转化成byte处理
        """
        if not text:
            return []
        if chapter_pattern:
            self.chapter_pattern = bytes(chapter_pattern, "utf-8")
        if not self.chapter_pattern:
            return []

        text = bytes(text, "utf-8")
        merged_chapters = []
        pre_txt_begin = 0
        current_chapter = {}
        try:
            for match in re.finditer(self.chapter_pattern, text, re.MULTILINE):
                if pre_txt_begin != 0:
                    pre_txt = text[pre_txt_begin:match.start()]
                    current_chapter["word_count"] = self.count_words(pre_txt.decode("utf-8"))
                    if current_chapter:
                        merged_chapters.append(current_chapter)

                pre_txt_begin = match.end()
                if len(match.groups()) == 1:
                    current_chapter = {
                        "start": match.start(),
                        "end": match.end(),
                        "title": match.group(1).decode("utf-8").strip()
                    }
                elif len(match.groups()) >= 2:
                    current_chapter = {
                        "start": match.start(),
                        "end": match.end(),
                        "cid": match.group(1).decode("utf-8").strip(),
                        "title": match.group(2).decode("utf-8").strip()
                    }
                else:
                    current_chapter = {
                        "start": match.start(),
                        "end": match.end(),
                        "title": match.group().decode("utf-8").strip()
                    }
                last_txt_begin = match.end()

            if current_chapter:
                pre_txt = text[last_txt_begin:]
                # current_chapter["txt"] = pre_txt.strip()
                current_chapter["word_count"] = self.count_words(pre_txt.decode("utf-8"))
                merged_chapters.append(current_chapter)

        except Exception as ex:
            raise Exception(f"split_question_list error:cp_book_id={self.cp_book_id}, msg={str(ex)}")

        self.question_list = merged_chapters
        self.question_list_updated.emit(self.question_list)

        return self.question_list

    def count_words(self, text):
        """
        计算单词数，可以处理连字符和撇号。
        todo 根据语种计算词量
        """

        return word_count_func(text)

    def get_question_list(self):
        """获取问题列表
        编辑器是用byte定位，这里转化成byte处理

        """
        return self.question_list

    def __repr__(self) -> str:
        """对象表示方法，便于打印调试"""
        return f"<Question (ID:{self.cp_book_id}) 包含{len(self.question_list)}章>"


class QuestionManager(object):
    """书籍类，包含书籍基本信息和问题管理功能"""

    def __init__(self):
        """
        初始化书籍实例
        :param name: 书籍名称
        :param cp_book_id: 书籍唯一ID
        """
        self.book_map = {}

    def get_book(self, editor):
        """返回当前编辑器对应的书籍"""
        if editor in self.book_map:
            return self.book_map[editor]
        return None

    def add_book(self, editor, book):
        """添加编辑器-图书关系
        """
        self.book_map[editor] = book

    def remove_book(self, editor):
        """添加编辑器-图书关系
        """
        self.book_map.pop(editor, None)


question_manager = QuestionManager()
