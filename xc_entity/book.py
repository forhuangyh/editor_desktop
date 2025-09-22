"""
图书类: 属性，方法
"""
import qt


class Book(object):
    """书籍类，包含书籍基本信息和章节管理功能"""

    def __init__(self):
        """
        初始化书籍实例
        :param name: 书籍名称
        :param book_id: 书籍唯一ID
        :param chapters: 初始章节列表，默认为空列表
        """
        pass
        # self.name = name
        # self.book_id = book_id
        # self.chapter_list = chapters if chapters is not None else []

    def get_chapter_list(self):
        chapter_list = [
            {
                "title": "第一行标题",
                "txt": "",
            },
            {
                "title": "第二行标题",
                "txt": "",
            },
            {
                "title": "第三行标题",
                "txt": "",
            },
        ]
        return chapter_list

    def add_chapter(self, chapter_name: str):
        """添加新章节到书籍"""
        self.chapter_list.append(chapter_name)
        return f"已添加章节：{chapter_name}"

    def remove_chapter(self, index: int):
        """根据索引移除章节"""
        if 0 <= index < len(self.chapter_list):
            removed = self.chapter_list.pop(index)
            return f"已移除章节：{removed}"
        return "无效的章节索引"

    def get_chapters(self) -> list:
        """获取当前所有章节"""
        return self.chapter_list.copy()  # 返回副本防止外部修改

    def __repr__(self) -> str:
        """对象表示方法，便于打印调试"""
        return f"<Book {self.name} (ID:{self.book_id}) 包含{len(self.chapter_list)}章>"


# 示例用法
if __name__ == "__main__":
    # 创建书籍实例
    novel = Book("三体Ⅰ：地球往事", "BK2025001", ["科学边界", "台球桌边的聚会"])

    # 添加新章节
    print(novel.add_chapter("宇宙闪烁"))  # 输出：已添加章节：宇宙闪烁

    # 移除章节
    print(novel.remove_chapter(1))  # 输出：已移除章节：台球桌边的聚会

    # 获取章节列表
    print(novel.get_chapters())  # 输出：['科学边界', '宇宙闪烁']

    # 打印书籍信息
    print(novel)  # 输出：<Book 三体Ⅰ：地球往事 (ID:BK2025001) 包含2章>
