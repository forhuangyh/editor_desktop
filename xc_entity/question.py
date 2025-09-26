"""
问题类: 属性，方法
"""

import bisect


class Question(object):
    """查重列表管理功能"""

    is_work = False

    def __init__(self, book_name):
        """初始化书籍实例
        """
        self.book_name = book_name
        self.question_list = []

    def set_is_work(self, is_work):
        """是否查重
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
        if not order_list or not chapter_list:
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
