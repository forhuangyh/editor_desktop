"""
问题类: 属性，方法
"""
import re
import bisect
from xc_common.word_count import word_count_func


from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class Question(object):
    """问题列表管理功能"""

    is_work = False

    def __init__(self, book_name):
        """初始化书籍实例
        """
        self.book_name = book_name
        self.question_list = []

    def set_is_work(self, is_work):
        """是否检查问题列表
        """
        self.is_work = is_work

    def split_question_list(self, line_list, chapter_list, editor, book):
        """获取问题列表
        编辑器是用byte定位，这里转化成byte处理
        """
        if not all([line_list, editor, book]):
            return [], []
        if not self.is_work:
            return [], []

        line_dict, repeat_dict = {}, {}
        highlight_matches, match_list = [], []
        chapter_list = book.get_chapter_list()
        order_list = [chapter["start"] for chapter in chapter_list] if chapter_list else []
        try:
            for index, line in enumerate(line_list):
                line = line.strip()
                if not line:
                    continue
                if line in line_dict:
                    line_dict[line].append({"line_num": index})
                else:
                    line_dict[line] = [{"line_num": index}]
            for line, items in line_dict.items():
                if len(items) > 1:
                    repeat_dict[line] = items

            line_index = 0
            for line_text, repeat_list in repeat_dict.items():
                line_index += 1
                for i, item in enumerate(repeat_list):
                    byte_index = editor.positionFromLineIndex(item["line_num"], 0)
                    new_match = {
                        "index": line_index if i == 0 else 0,
                        'line_number': item["line_num"],
                        'line_text': line_text,
                        "byte_index": byte_index,
                        "title": self.find_title(byte_index, order_list, chapter_list)
                    }
                    if i == 0:
                        match_list.append(new_match)
                        match_list[-1]["children"] = [new_match.copy()]
                    else:
                        match_list[-1]["children"].append(new_match)

                    highlight_matches.append(
                        (
                            0,
                            byte_index,
                            0,
                            byte_index + len(line_text.encode("utf-8")),
                        )
                    )
        except Exception as ex:
            raise Exception(f"split_question_list error:book_name={self.book_name}, msg={str(ex)}")

        return match_list, highlight_matches

    def find_title(self, byte_index, order_list, chapter_list):
        """
        查找章节标题
        """
        if not order_list:
            return ""
        # 使用 bisect_left 查找位置
        insertion_point = bisect.bisect_left(order_list, byte_index)
        return chapter_list[insertion_point - 1]["title"]

    def get_question_list(self):
        """获取问题列表
        编辑器是用byte定位，这里转化成byte处理

        """
        return self.question_list

    def __repr__(self) -> str:
        """对象表示方法，便于打印调试"""
        return f"<Question (ID:{self.book_name}) 包含{len(self.question_list)}章>"

    # def refresh_question_list(self, text):
    #     if not text:
    #         return
    #     if not self.chapter_pattern:
    #         return
    #     self.split_question_list(text)

    # def get_line_byte_positions(self, line_list, encoding='utf-8'):
    #     """
    #     计算每行在整个字节流中的起始和结束位置。
    #     Args:
    #         text (str): 输入的原始文本。
    #         encoding (str): 文本编码，默认为 'utf-8'。

    #     Returns:
    #         list: 一个列表，每个元素是一个字典，包含 'paragraph' (str), 'start' (int), 'end' (int)。
    #     """
    #     if not line_list:
    #         return []
    #     results = []
    #     current_byte_pos = 0
    #     for paragraph in line_list:
    #         # 将当前段落（行）编码为字节串
    #         paragraph_bytes = paragraph.encode(encoding)
    #         # 计算结束位置
    #         end_byte_pos = current_byte_pos + len(paragraph_bytes)
    #         # 存储结果
    #         results.append({
    #             'text': paragraph,
    #             'start': current_byte_pos,
    #             'end': end_byte_pos
    #         })
    #         # 移动到下一段落的起始位置
    #         # 需要考虑行分隔符 \n 的字节长度，通常是 1
    #         current_byte_pos = end_byte_pos + 1
    #     return results

    # def find_all(self, source_bytes, pattern_bytes):
    #     """
    #     在二进制数据中查找一个模式出现的所有位置。
    #     Args:
    #         source_bytes: 要搜索的原始 bytes 对象。
    #         pattern_bytes: 要查找的模式 bytes 对象。

    #     Returns:
    #         一个包含所有匹配起始位置的列表。
    #     """
    #     positions = []
    #     start_index = 0
    #     # 只要还能找到模式，就继续循环
    #     while True:
    #         # 从上一次找到的位置+1开始查找
    #         index = source_bytes.find(pattern_bytes, start_index)
    #         if index == -1:
    #             # 如果没有找到，就退出循环
    #             break
    #         positions.append(index)
    #         # 将下一次查找的起始位置更新为当前找到位置的下一个字节
    #         start_index = index + 1

    #     return positions
