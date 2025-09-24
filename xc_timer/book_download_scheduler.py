import os
import sys
from PyQt6.QtCore import QObject, QTimer, QThreadPool, QRunnable, pyqtSignal

# 确保可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xc_service.book_service import BookService


class DownloadState:
    """书籍下载状态常量"""
    PENDING = 0
    DOWNLOADING = 1
    COMPLETED = 2
    FAILED = 3
    PAUSED = 4


class BookDownloadTask(QRunnable):
    """单个书籍下载任务，只负责执行下载逻辑，不处理数据库和信号"""

    def __init__(self, book_record, scheduler):
        super().__init__()
        self.book_record = book_record
        self.scheduler = scheduler
        self.book_service = BookService()

    def run(self):
        """执行下载任务"""
        book_id = self.book_record.get("book_id", "")
        id = self.book_record.get("id", "")
        file_path = self.book_record.get("file_path", "")
        title = self.book_record.get("title", "未知")

        try:
            # 下载书籍
            success = self.book_service.download_book(id)
            if success:
                self.scheduler.on_task_completed(self.book_record)
            else:
                self.scheduler.on_task_failed(self.book_record, reason="下载失败")
        except Exception as e:
            self.scheduler.on_task_failed(self.book_record, reason=str(e))
        finally:
            self.scheduler.task_finished(self)


class BookDownloadScheduler(QObject):
    """书籍下载调度器，负责管理下载队列和任务状态"""
    # 信号
    task_started = pyqtSignal(dict)    # 任务开始
    task_completed = pyqtSignal(dict)  # 任务完成
    task_failed = pyqtSignal(dict)     # 任务失败
    queue_updated = pyqtSignal(list)   # 队列更新

    def __init__(self, interval=15000, max_concurrent_tasks=1):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self._process_pending_tasks)

        self.thread_pool = QThreadPool.globalInstance()
        # 强制设置为单任务，确保每次只有一个线程执行
        self.max_concurrent_tasks = 1

        self.active_tasks = []  # 当前运行中的任务
        self.task_queue = []  # 等待中的任务
        self.processed_book_ids = set()

    # ---------------------- 调度控制 ----------------------
    def start(self):
        # 增强：添加调度器参数信息
        print(f"【调度器】启动书籍下载调度器 | 检查间隔={self.timer.interval()}ms | 最大并发任务数={self.max_concurrent_tasks}")
        self._initialize_queue()
        self.timer.start()

    def stop(self):
        # 增强：显示当前活跃任务数量
        print(f"【调度器】停止书籍下载调度器 | 正在终止 {len(self.active_tasks)} 个活跃任务...")
        self.timer.stop()
        self.thread_pool.waitForDone()
        print(f"【调度器】所有任务已终止")

    def pause_all_downloads(self):
        # 增强：明确暂停操作范围
        print(f"【调度器】暂停所有下载任务 | 正在更新数据库中'下载中'状态的任务...")
        from xc_service.sqlite_service import SQLiteService
        db_service = SQLiteService()
        db_service.pause_all_downloads()
        db_service.close()
        print(f"【调度器】所有下载任务已暂停")

    # ---------------------- 队列处理 ----------------------

    def _initialize_queue(self):
        print("【队列】初始化任务队列...")
        self.task_queue.clear()
        self.processed_book_ids.clear()

        from xc_service.sqlite_service import SQLiteService
        db_service = SQLiteService()
        pending_books = db_service.get_pending_books(100)
        db_service.close()

        # 增强：显示数据库查询结果
        print(f"【队列】从数据库获取到 {len(pending_books)} 个待处理书籍记录")
        for book in pending_books:
            book_id = book.get('id', '未知ID')
            book_title = book.get('title', '未知标题')
            book_key = f"{book_id}"
            if book_key not in self.processed_book_ids:
                self.task_queue.append(book)
                self.processed_book_ids.add(book_key)
                print(f"【队列】添加待下载书籍: ID={book_id}, 标题='{book_title}'")

        self.queue_updated.emit(self.task_queue.copy())
        print(f"【队列】初始化完成 | 待处理任务总数={len(self.task_queue)}")

    def _process_pending_tasks(self):
        # 增强：显示当前任务状态
        print(
            f"\n【任务处理】处理待处理任务 | 活跃任务数={len(self.active_tasks)}/{self.max_concurrent_tasks} | 队列剩余任务数={len(self.task_queue)}")

        if len(self.active_tasks) >= self.max_concurrent_tasks:
            print(f"【任务处理】活跃任务数已达上限，跳过本次处理")
            return

        # 新增：每次定时器触发时均重新初始化队列（加载最新待处理任务）
        print(f"【任务处理】刷新队列，从数据库加载最新待处理任务...")
        self._initialize_queue()

        if not self.task_queue:
            print(f"【任务处理】队列为空，等待下次定时器触发后重新加载...")
            return

        # 处理队列中的任务
        book_record = self.task_queue.pop(0)
        book_id = book_record.get('id', '未知ID')
        book_title = book_record.get('title', '未知标题')
        cp_book_id = book_record.get('cp_book_id', '未知来源ID')

        print(
            f"【任务处理】启动新任务 | 书籍ID={book_id} | 来源ID={cp_book_id} | 标题='{book_title}' | 剩余队列任务数={len(self.task_queue)}")
        self.on_task_started(book_record)

        task = BookDownloadTask(book_record, self)
        self.active_tasks.append(task)
        self.thread_pool.start(task)
        self.queue_updated.emit(self.task_queue.copy())

    def task_finished(self, task):
        if task in self.active_tasks:
            book_record = task.book_record
            book_id = book_record.get('id', '未知ID')
            self.active_tasks.remove(task)
            # 增强：显示任务结束信息
            print(f"【任务结束】任务完成 | 书籍ID={book_id} | 剩余活跃任务数={len(self.active_tasks)}")
        self._process_pending_tasks()

    # ---------------------- 状态处理 ----------------------

    def on_task_started(self, book_record):
        book_id = book_record.get('id', '未知ID')
        book_title = book_record.get('title', '未知标题')
        from xc_service.sqlite_service import SQLiteService
        db_service = SQLiteService()
        db_service.update_download_state(book_record["id"], DownloadState.DOWNLOADING)
        db_service.close()
        # 增强：明确书籍开始下载
        print(f"【书籍状态】开始下载 | ID={book_id} | 标题='{book_title}' | 状态=下载中")
        self.task_started.emit(book_record)

    def on_task_completed(self, book_record):
        book_id = book_record.get('id', '未知ID')
        book_title = book_record.get('title', '未知标题')
        from xc_service.sqlite_service import SQLiteService
        db_service = SQLiteService()
        db_service.update_download_state(book_record["id"], DownloadState.COMPLETED)
        db_service.close()
        # 增强：包含书籍完整信息
        print(f"【书籍状态】下载完成 ✅ | ID={book_id} | 标题='{book_title}' | 状态=已完成")
        self.task_completed.emit(book_record)

    def on_task_failed(self, book_record, reason=None):
        book_id = book_record.get('id', '未知ID')
        book_title = book_record.get('title', '未知标题')
        from xc_service.sqlite_service import SQLiteService
        db_service = SQLiteService()
        db_service.update_download_state(book_record["id"], DownloadState.FAILED)
        db_service.close()
        # 增强：包含失败原因和书籍信息
        print(f"【书籍状态】下载失败 ❌ | ID={book_id} | 标题='{book_title}' | 原因={reason or '未知错误'} | 状态=下载失败")
        self.task_failed.emit(book_record)


# 全局调度器实例
book_download_scheduler = BookDownloadScheduler()
