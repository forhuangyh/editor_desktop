"""
图书类: 属性，方法
"""
import re
from qt import QMessageBox
from xc_common.word_count import word_count_func


from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from xc_entity.question import Question
from xc_common.file_utils import get_chapter_title_reg


class Book(QObject):
    """书籍类，包含书籍基本信息和章节管理功能"""

    chapter_list_updated = pyqtSignal(list)

    def __init__(self, book_name, language=None, is_online=False, parent=None):
        """
        初始化书籍实例
        :param name: 书籍名称
        :param book_name: 书籍唯一ID
        """
        super().__init__(parent)
        self.book_name = book_name
        self.chapter_list = []
        self.chapter_pattern = b""
        self.language = language
        self.is_online = is_online
        self.question = Question(self.book_name)

    def refresh_chapter_list(self, text):
        if not text:
            return

        self.confirm_chapter_title_reg(text)

        if not self.chapter_pattern:
            return
        self.split_chapter_list(text)

    def confirm_chapter_title_reg(self, text):
        if not text:
            return
        if not self.is_online:
            return
        chapter_title = text.split('\n', 1)[0]
        if not chapter_title:
            return
        chapter_title = f"{chapter_title}\n"
        collect_patt, patt = get_chapter_title_reg(self.language)
        match = re.search(collect_patt, chapter_title)
        if match:
            self.chapter_pattern = bytes(collect_patt, "utf-8")
            return
        match = re.search(patt, text)
        if match:
            self.chapter_pattern = bytes(patt, "utf-8")
            return

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

    def upload_check(self, editor):
        """上传前检查"""

        if not self.is_online or not editor.save_path:
            return False, "非线上图书，无法上传"
        if not self.language:
            return False, "缺少语种，无法上传"
        editor.save_document(saveas=False)
        # 检查一下标题
        collect_patt, patt = get_chapter_title_reg(self.language)
        for chapter in self.chapter_list:
            match = re.search(collect_patt, chapter["title"])
            if match:
                continue
            match = re.search(patt, chapter["title"])
            if match:
                continue
            else:
                return False, f'标题：\"{chapter["title"]}\"，不符合规范，无法上线'

        return True, ""

    def count_words(self, text):
        """计算字数
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
