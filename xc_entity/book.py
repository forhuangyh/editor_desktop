"""
图书类: 属性，方法
"""
import re
from qt import QMessageBox
from xc_common.word_count import word_count_func


from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from xc_entity.question import Question


class Book(QObject):
    """书籍类，包含书籍基本信息和章节管理功能"""

    chapter_list_updated = pyqtSignal(list)

    def __init__(self, book_name, parent=None):
        """
        初始化书籍实例
        :param name: 书籍名称
        :param book_name: 书籍唯一ID
        """
        super().__init__(parent)
        self.book_name = book_name
        self.chapter_list = []
        self.chapter_pattern = b""
        self.language = ""
        self.question = Question(self.book_name)

    def refresh_chapter_list(self, text):
        if not text:
            return
        if not self.chapter_pattern:
            return
        self.split_chapter_list(text)

    def split_chapter_list(self, text, chapter_pattern=None):
        """获取章节列表
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
            raise Exception(f"split_chapter_list error:book_name={self.book_name}, msg={str(ex)}")

        self.chapter_list = merged_chapters
        self.chapter_list_updated.emit(self.chapter_list)

        return self.chapter_list

    # def split_chapter_list_and_line(self, text):
    #     """获取章节列表, 并将内容拆解成line，用在问题段落中
    #     编辑器是用byte定位，这里转化成byte处理

    #     """
    #     if not text:
    #         return []
    #     if not self.chapter_pattern:
    #         return []

    #     text = bytes(text, "utf-8")
    #     merged_chapters = []
    #     pre_txt_begin = 0
    #     current_chapter = {}
    #     try:
    #         for match in re.finditer(self.chapter_pattern, text, re.MULTILINE):
    #             if pre_txt_begin != 0:
    #                 pre_txt = text[pre_txt_begin:match.start()]
    #                 current_chapter["word_count"] = self.count_words(pre_txt.decode("utf-8"))
    #                 if current_chapter:
    #                     merged_chapters.append(current_chapter)

    #             pre_txt_begin = match.end()
    #             if len(match.groups()) == 1:
    #                 current_chapter = {
    #                     "start": match.start(),
    #                     "end": match.end(),
    #                     "title": match.group(1).decode("utf-8").strip()
    #                 }
    #             elif len(match.groups()) >= 2:
    #                 current_chapter = {
    #                     "start": match.start(),
    #                     "end": match.end(),
    #                     "cid": match.group(1).decode("utf-8").strip(),
    #                     "title": match.group(2).decode("utf-8").strip()
    #                 }
    #             else:
    #                 current_chapter = {
    #                     "start": match.start(),
    #                     "end": match.end(),
    #                     "title": match.group().decode("utf-8").strip()
    #                 }
    #             last_txt_begin = match.end()

    #         if current_chapter:
    #             pre_txt = text[last_txt_begin:]
    #             # current_chapter["txt"] = pre_txt.strip()
    #             current_chapter["word_count"] = self.count_words(pre_txt.decode("utf-8"))
    #             merged_chapters.append(current_chapter)

    #     except Exception as ex:
    #         raise Exception(f"split_chapter_list error:book_name={self.book_name}, msg={str(ex)}")

    #     return merged_chapters

    def count_words(self, text):
        """
        计算单词数，可以处理连字符和撇号。
        todo 根据语种计算词量
        """

        return word_count_func(text)

    def get_chapter_list(self):
        """获取章节列表
        编辑器是用byte定位，这里转化成byte处理

        """
        return self.chapter_list

    def __repr__(self) -> str:
        """对象表示方法，便于打印调试"""
        return f"<Book (ID:{self.book_name}) 包含{len(self.chapter_list)}章>"


class BookManager(object):
    """书籍类，包含书籍基本信息和章节管理功能"""

    def __init__(self):
        """
        初始化书籍实例
        :param name: 书籍名称
        :param book_name: 书籍唯一ID
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


book_manager = BookManager()
