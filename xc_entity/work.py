from qt import QObject, QThread, pyqtSignal
from collections import deque


class TaskWorker(QObject):
    """负责管理自己的任务队列并执行任务
    """
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.task_queue = deque()
        self._running = True

    def run(self):
        """从队列中取出任务并执行
        """
        while self._running:
            # 检查队列中是否有任务
            if self.task_queue:
                try:
                    task = self.task_queue.popleft()
                    # 执行任务
                    print(f"Executing task: {task['name']}")
                    task['function'](*task['args'])
                except Exception as e:
                    print(f"Task execution failed: {e}")
            else:
                # 队列为空时，短暂休眠，防止CPU占用过高
                QThread.msleep(100)

    def add_task(self, task):
        """
        添加新任务到队列
        """
        self.task_queue.append(task)

    def stop(self):
        """
        停止工作线程
        """
        self._running = False
