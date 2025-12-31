"""
AI 任务管理器 - 管理异步AI生成任务
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Callable, Optional
from app.models.database import SessionLocal
from app.models.ppt.task import Task

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器 - 使用线程池执行异步任务"""

    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks: Dict[str, threading.Thread] = {}

    def submit_task(
        self,
        task_id: str,
        task_func: Callable,
        *args,
        **kwargs
    ):
        """
        提交任务到线程池执行

        Args:
            task_id: 任务ID
            task_func: 任务函数
            *args: 位置参数
            **kwargs: 关键字参数
        """

        def task_wrapper():
            db = SessionLocal()
            try:
                # 获取任务
                task = db.query(Task).get(task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return

                # 更新任务状态为执行中
                task.status = 'IN_PROGRESS'
                db.commit()

                # 执行任务函数
                logger.info(f"Executing task {task_id}...")
                result = task_func(*args, **kwargs)

                # 更新任务状态为完成
                task.status = 'COMPLETED'
                task.result = result if isinstance(result, dict) else {'result': result}
                db.commit()
                logger.info(f"Task {task_id} completed successfully")

            except Exception as e:
                logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
                try:
                    task = db.query(Task).get(task_id)
                    if task:
                        task.status = 'FAILED'
                        task.error_message = str(e)
                        db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update task status: {str(db_error)}")

            finally:
                db.close()
                # 从运行中任务移除
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

        # 提交任务到线程池
        future = self.executor.submit(task_wrapper)
        self.running_tasks[task_id] = future

        logger.info(f"Task {task_id} submitted to executor")

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典
        """
        db = SessionLocal()
        try:
            task = db.query(Task).get(task_id)
            if task:
                return task.to_dict()
            return None
        finally:
            db.close()

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务（仅支持未开始或正在执行的任务）

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id in self.running_tasks:
            # 注意：ThreadPoolExecutor的Future不支持直接取消
            # 这里仅从字典中移除引用
            del self.running_tasks[task_id]

            # 更新数据库状态
            db = SessionLocal()
            try:
                task = db.query(Task).get(task_id)
                if task and task.status in ['PENDING', 'IN_PROGRESS']:
                    task.status = 'FAILED'
                    task.error_message = 'Task cancelled by user'
                    db.commit()
                    return True
            finally:
                db.close()

        return False

    def shutdown(self, wait: bool = True):
        """
        关闭任务管理器

        Args:
            wait: 是否等待所有任务完成
        """
        self.executor.shutdown(wait=wait)
        logger.info("TaskManager shutdown completed")


# 全局单例
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(max_workers=3)
    return _task_manager


# 便捷导入
task_manager = get_task_manager()
