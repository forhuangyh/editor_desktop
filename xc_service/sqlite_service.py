import os
import json
from PyQt6.QtCore import QDateTime, Qt
from xc_common.sqlite_utils import SQLiteUtils

# 数据库文件路径
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.exco', 'editor_desktop.db')
from xc_common.logger import get_logger
# 获取模块专属logger
logger = get_logger("sqlite_service")

class SQLiteService:
    """SQLite数据库服务类，提供书籍相关的数据库操作"""

    def __init__(self, db_file=db_path):
        """初始化数据库连接"""
        self.db = SQLiteUtils(db_file)
        self.init_book_tables()

    def init_book_tables(self):
        """初始化书籍相关表结构"""
        # 创建书籍下载记录表，使用您提供的表结构 download_state 0-未开始 1-下载中 2-已完成 3-下载失败 4-暂停
        columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'cp_book_id': 'TEXT NOT NULL',
            'book_id': 'TEXT NOT NULL',
            'title': 'TEXT',
            'chapter_list': 'TEXT',
            'cover_url': 'TEXT',
            'language': 'TEXT',
            'intro': 'TEXT',
            'total_chapters': 'INTEGER DEFAULT 0',
            'updated_at': 'TEXT',
            'created_at': 'TEXT',
            'file_path': 'TEXT',
            'download_chapters': 'INTEGER',
            'download_state': 'INTEGER',
            'UNIQUE': '(book_id, file_path)'
        }
        self.db.create_table('book_download_records', columns)

    def add_book(self, book_data):
        """添加新书籍记录
        Args:
            book_data: 包含书籍信息的字典
        Returns:
            bool: 操作是否成功
        """
        try:
            # 过滤只保留表结构中定义的字段
            allowed_fields = ['cp_book_id', 'book_id', 'title', 'cover_url', 'language',
                              'intro', 'total_chapters', 'updated_at', 'created_at',
                              'file_path', 'download_chapters', 'download_state','chapter_list']

            # 创建一个只包含允许字段的新字典
            filtered_data = {k: v for k, v in book_data.items() if k in allowed_fields}

            filtered_data['intro'] = ''
            # 添加必要的默认字段
            if 'created_at' not in filtered_data:
                filtered_data['created_at'] = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            if 'updated_at' not in filtered_data:
                filtered_data['updated_at'] = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            if 'download_state' not in filtered_data:
                filtered_data['download_state'] = 0  # 0-未开始
            if 'download_chapters' not in filtered_data:
                filtered_data['download_chapters'] = 0
            # 将chapter_list转换为JSON字符串
            if 'chapter_list' in filtered_data and isinstance(filtered_data['chapter_list'], list):
                filtered_data['chapter_list'] = json.dumps(filtered_data['chapter_list'])
            self.db.insert('book_download_records', filtered_data)
            return True
        except Exception as e:
            logger.error(f"添加书籍记录失败: {str(e)}")
            return False

    def update_book(self, book_data):
        """更新现有书籍记录

        Args:
            book_data: 包含书籍信息的字典，必须包含book_id和file_path

        Returns:
            bool: 操作是否成功
        """
        try:
            # 确保包含必要的标识字段
            book_id = book_data.get('book_id', '')
            file_path = book_data.get('file_path', '')

            if not book_id or not file_path:
                logger.error("更新书籍记录失败: 缺少必要的book_id或file_path字段")
                return False

            # 检查记录是否存在
            existing_book = self.db.fetch_one(
                "SELECT id FROM book_download_records WHERE book_id = ? AND file_path = ?",
                (book_id, file_path)
            )

            if not existing_book:
                logger.error(f"更新书籍记录失败: 未找到书籍ID为'{book_id}'且文件路径为'{file_path}'的记录")
                return False

            # 过滤只保留表结构中定义的字段（排除id）
            allowed_fields = ['cp_book_id', 'book_id', 'title', 'cover_url', 'language',
                              'intro', 'total_chapters', 'updated_at', 'created_at',
                              'file_path', 'download_chapters', 'download_state','chapter_list']

            # 创建一个只包含允许字段的新字典
            filtered_data = {k: v for k, v in book_data.items() if k in allowed_fields}

            # 更新时间戳
            filtered_data['updated_at'] = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:ss:mm")
            # 将chapter_list转换为JSON字符串
            if 'chapter_list' in filtered_data and isinstance(filtered_data['chapter_list'], list):
                filtered_data['chapter_list'] = json.dumps(filtered_data['chapter_list'])
            self.db.update(
                'book_download_records',
                filtered_data,
                f"id = {existing_book[0]}"
            )
            return True
        except Exception as e:
            logger.error(f"更新书籍记录失败: {str(e)}")
            return False

    def add_or_update_book(self, book_data):
        """添加或更新书籍记录（保持向后兼容）"""
        try:
            # 检查是否存在相同的书籍ID和文件路径组合
            existing_book = self.db.fetch_one(
                "SELECT id FROM book_download_records WHERE book_id = ? AND file_path = ?",
                (book_data.get('book_id', ''), book_data.get('file_path', ''))
            )

            if existing_book:
                # 调用更新方法
                return self.update_book(book_data)
            else:
                # 调用添加方法
                return self.add_book(book_data)
        except Exception as e:
            logger.error(f"添加或更新书籍记录失败: {str(e)}")
            return False

    def get_all_books(self):
        """获取所有书籍记录"""
        try:
            return self.db.fetch_all(
                "SELECT * FROM book_download_records ORDER BY created_at DESC"
            )
        except Exception as e:
            logger.error(f"获取书籍记录失败: {str(e)}")
            return []

    def get_recent_books(self, limit=100):
        """获取最近的书籍记录
        Args:
            limit: 限制返回记录的数量，默认为100
        Returns:
            list: 最近的书籍记录列表
        """
        try:
            return self.db.fetch_all(
                "SELECT * FROM book_download_records ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        except Exception as e:
            logger.error(f"获取最近书籍记录失败: {str(e)}")
            return []

    def get_book_by_id(self, id):
        """根据书籍ID获取书籍记录"""
        try:
            # 2. 查询书籍记录
            result = self.db.fetch_one(
                "SELECT * FROM book_download_records WHERE id = ?",
                (id,)
            )

            if result:
                # 3. 使用动态字段列表构建字典
                return result
            return None
        except Exception as e:
            logger.error(f"获取书籍记录失败: {str(e)}")
            return None

    def update_download_state(self, id, state, chapters=None):
        """更新书籍下载状态
        state: 下载状态 (0-未开始 1-进行中 2-结束 3-失败)"""
        try:
            data = {'download_state': state, 'updated_at': QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)}
            if chapters is not None:
                data['download_chapters'] = chapters

            self.db.update(
                'book_download_records',
                data,
                "id = ?",
                (id)
            )
            return True
        except Exception as e:
            logger.error(f"更新下载状态失败: {str(e)}")
            return False

    def delete_book(self, id):
        """删除书籍记录"""
        try:
            self.db.execute(
                "DELETE FROM book_download_records WHERE id=?",
                (id,)  # 【修复】添加逗号，确保参数为元组类型
            )
            return True
        except Exception as e:
            logger.error(f"删除书籍记录失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        try:
            if hasattr(self.db, 'close'):
                self.db.close()
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}")

    # 清除数据库中进行中的数据
    def clear_downloading_books(self):
        """清除数据库中所有下载状态为1（进行中）的书籍记录"""
        try:
            self.db.execute(
                "DELETE FROM book_download_records WHERE download_state = 1 or download_state = 0"
            )
            return True
        except Exception as e:
            logger.error(f"清除下载中书籍记录失败: {str(e)}")
            return False

    """--------------------------------下载相关--------------------------------"""
    def get_books_by_download_state(self, states):
        """根据下载状态获取书籍记录
        Args:
            states: 下载状态列表 (0-未开始 1-进行中 2-已完成 3-失败 4-关闭应用状态)
        Returns:
            list: 符合条件的书籍记录列表
        """
        try:
            # 构建参数化查询
            placeholders = ', '.join(['?' for _ in states])
            # 为了支持按特定顺序排序，这里我们需要使用CASE语句
            case_when = "CASE download_state"
            for i, state in enumerate(states):
                case_when += f" WHEN {state} THEN {i}"
            case_when += " END"

            query = f"SELECT * FROM book_download_records WHERE download_state IN ({placeholders}) ORDER BY {case_when} ASC"
            return self.db.fetch_all(query, states)
        except Exception as e:
            logger.error(f"获取特定状态的书籍记录失败: {str(e)}")
            return []

    def get_pending_books(self, limit=10):
        """获取待处理的书籍记录（状态为4-关闭应用状态、3-失败和0-未开始）
        Args:
            limit: 限制返回记录的数量，默认为10
        Returns:
            list: 待处理的书籍记录列表（按4、3、0的顺序排列，且不包含重复项）
        """
        try:
            # 查询状态为4、3、0的记录，并按照这个顺序排序
            # 使用book_id和file_path组合确保不返回重复项
            query = """
                    SELECT *
                    FROM book_download_records
                    WHERE download_state = 0 LIMIT ? \
                    """
            return self.db.fetch_all(query, (limit,))
        except Exception as e:
            logger.error(f"获取待处理书籍记录失败: {str(e)}")
            return []

    def pause_all_downloads(self):
        """将所有下载中的书籍（状态为1）暂停（改为状态4）
        用于应用关闭时的处理
        Returns:
            bool: 操作是否成功
        """
        try:
            # 更新所有状态为1的记录为状态4
            self.db.execute(
                "UPDATE book_download_records SET download_state = 4, updated_at = ? WHERE download_state = 1",
                (QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),)
            )
            return True
        except Exception as e:
            logger.error(f"暂停所有下载失败: {str(e)}")
            return False
# 创建全局实例供其他模块使用
sqlite_service = SQLiteService()
