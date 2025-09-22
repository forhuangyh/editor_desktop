import sqlite3
import os
from typing import Dict, List, Tuple, Any, Optional, Union

class SQLiteUtils:
    """通用SQLite数据库工具类"""

    def __init__(self, db_path: str):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self._ensure_db_directory()

    def _ensure_db_directory(self):
        """确保数据库文件所在目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def connect(self):
        """建立数据库连接

        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        if not self.conn:
            try:
                self.conn = sqlite3.connect(self.db_path)
                # 启用外键约束
                self.conn.execute("PRAGMA foreign_keys = ON")
                # 返回字典类型的结果
                self.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                print(f"数据库连接失败: {str(e)}")
                self.conn = None
                raise
        return self.conn

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, sql: str, params: Union[Tuple, Dict] = None) -> Optional[sqlite3.Cursor]:
        """执行SQL语句

        Args:
            sql: SQL语句
            params: SQL参数，元组或字典

        Returns:
            sqlite3.Cursor: 游标对象，如果执行失败则返回None
        """
        if not self.connect():
            return None

        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            print(f"执行SQL失败: {str(e)}")
            print(f"SQL: {sql}")
            print(f"Params: {params}")
            self.conn.rollback()
            raise

    def executemany(self, sql: str, params_list: List[Union[Tuple, Dict]]) -> bool:
        """批量执行SQL语句

        Args:
            sql: SQL语句
            params_list: 参数列表

        Returns:
            bool: 执行是否成功
        """
        if not self.connect():
            return False

        try:
            cursor = self.conn.cursor()
            cursor.executemany(sql, params_list)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"批量执行SQL失败: {str(e)}")
            print(f"SQL: {sql}")
            self.conn.rollback()
            raise

    def fetch_one(self, sql: str, params: Union[Tuple, Dict] = None) -> Optional[Dict]:
        """获取单条记录

        Args:
            sql: SQL查询语句
            params: SQL参数

        Returns:
            Dict: 记录字典，如果没有记录则返回None
        """
        cursor = self.execute(sql, params)
        if cursor:
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def fetch_all(self, sql: str, params: Union[Tuple, Dict] = None) -> List[Dict]:
        """获取所有记录

        Args:
            sql: SQL查询语句
            params: SQL参数

        Returns:
            List[Dict]: 记录字典列表
        """
        cursor = self.execute(sql, params)
        if cursor:
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        return []

    def fetch_scalar(self, sql: str, params: Union[Tuple, Dict] = None) -> Any:
        """获取单个值

        Args:
            sql: SQL查询语句
            params: SQL参数

        Returns:
            Any: 查询结果的第一个值，如果没有结果则返回None
        """
        cursor = self.execute(sql, params)
        if cursor:
            row = cursor.fetchone()
            if row:
                return row[0]
        return None

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在

        Args:
            table_name: 表名

        Returns:
            bool: 表是否存在
        """
        sql = """
        SELECT name FROM sqlite_master WHERE type='table' AND name=?
        """
        result = self.fetch_one(sql, (table_name,))
        return result is not None

    def create_table(self, table_name: str, columns: Dict[str, str], primary_key: str = None) -> bool:
        """创建表

        Args:
            table_name: 表名
            columns: 列名和类型的字典，例如 {'id': 'INTEGER', 'name': 'TEXT'}
            primary_key: 主键列名

        Returns:
            bool: 创建是否成功
        """
        if self.table_exists(table_name):
            return True

        columns_sql = []
        for col_name, col_type in columns.items():
            col_def = f"{col_name} {col_type}"
            if col_name == primary_key:
                col_def += " PRIMARY KEY"
            columns_sql.append(col_def)

        columns_str = ", ".join(columns_sql)
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"

        return self.execute(sql) is not None

    def insert(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """插入记录

        Args:
            table_name: 表名
            data: 字段名和值的字典

        Returns:
            int: 插入记录的ID，如果插入失败则返回None
        """
        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.keys()])
        sql = f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})"

        cursor = self.execute(sql, tuple(data.values()))
        if cursor:
            return cursor.lastrowid
        return None

    def update(self, table_name: str, data: Dict[str, Any], condition: str, condition_params: Union[Tuple, Dict] = None) -> int:
        """更新记录

        Args:
            table_name: 表名
            data: 要更新的字段名和值的字典
            condition: WHERE条件
            condition_params: 条件参数

        Returns:
            int: 受影响的行数
        """
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"

        # 合并数据参数和条件参数
        params = list(data.values())
        if condition_params:
            if isinstance(condition_params, tuple):
                params.extend(condition_params)
            elif isinstance(condition_params, dict):
                params.extend(condition_params.values())
            else:
                params.append(condition_params)

        cursor = self.execute(sql, tuple(params))
        if cursor:
            return cursor.rowcount
        return 0

    def delete(self, table_name: str, condition: str = None, condition_params: Union[Tuple, Dict] = None) -> int:
        """删除记录

        Args:
            table_name: 表名
            condition: WHERE条件，如果为None则删除所有记录
            condition_params: 条件参数

        Returns:
            int: 受影响的行数
        """
        if condition:
            sql = f"DELETE FROM {table_name} WHERE {condition}"
            params = condition_params
        else:
            sql = f"DELETE FROM {table_name}"
            params = None

        cursor = self.execute(sql, params)
        if cursor:
            return cursor.rowcount
        return 0

    def begin_transaction(self):
        """开始事务"""
        if self.connect():
            self.execute("BEGIN TRANSACTION")

    def commit_transaction(self):
        """提交事务"""
        if self.conn:
            try:
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"事务提交失败: {str(e)}")
                self.conn.rollback()
                raise

    def rollback_transaction(self):
        """回滚事务"""
        if self.conn:
            try:
                self.conn.rollback()
            except sqlite3.Error as e:
                print(f"事务回滚失败: {str(e)}")
                raise

    def __enter__(self):
        """支持上下文管理器"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器，自动关闭连接"""
        self.close()


"""
# 创建数据库连接并执行操作
with SQLiteUtils('example.db') as db:
    # 创建表
    db.create_table('users', {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'name': 'TEXT NOT NULL',
        'age': 'INTEGER',
        'email': 'TEXT'
    })
    
    # 插入记录
    user_id = db.insert('users', {
        'name': '张三',
        'age': 25,
        'email': 'zhangsan@example.com'
    })
    
    # 查询记录
    user = db.fetch_one('SELECT * FROM users WHERE id = ?', (user_id,))
    print(f"查询结果: {user}")
    
    # 更新记录
    updated_rows = db.update('users', {'age': 26}, 'id = ?', (user_id,))
    print(f"更新了 {updated_rows} 行")
    
    # 查询所有记录
    all_users = db.fetch_all('SELECT * FROM users')
    print(f"所有用户: {all_users}")


"""