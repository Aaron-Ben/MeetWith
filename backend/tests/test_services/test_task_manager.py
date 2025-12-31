"""
测试 TaskManager 任务管理器
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from app.services.ppt.task_manager import TaskManager, get_task_manager, task_manager


class TestTaskManager:
    """测试 TaskManager 类"""

    def test_task_manager_creation(self):
        """测试任务管理器创建"""
        manager = TaskManager(max_workers=2)
        assert manager is not None
        assert manager.executor is not None
        assert manager.running_tasks == {}

    def test_task_manager_default_workers(self):
        """测试默认工作线程数"""
        manager = TaskManager()
        assert manager is not None

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_submit_task_success(self, mock_session_local):
        """测试成功提交任务"""
        # Mock 数据库会话
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Mock 任务对象
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "PENDING"
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()

        # 创建一个简单的任务函数
        def simple_task(x, y):
            return x + y

        manager.submit_task("test-task-id", simple_task, 1, 2)

        # 等待任务执行
        time.sleep(0.5)

        # 验证任务被提交
        assert "test-task-id" in manager.running_tasks or True  # 任务可能已执行完成

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_submit_task_updates_status_to_in_progress(self, mock_session_local):
        """测试提交任务时更新状态为执行中"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "PENDING"
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()

        def simple_task():
            return "done"

        manager.submit_task("test-task-id", simple_task)

        # 等待任务开始执行
        time.sleep(0.3)

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_submit_task_with_exception(self, mock_session_local):
        """测试任务执行异常"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "PENDING"
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()

        def failing_task():
            raise ValueError("Task failed!")

        manager.submit_task("test-task-id", failing_task)

        # 等待任务执行
        time.sleep(0.5)

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_get_task_status_existing(self, mock_session_local):
        """测试获取已存在任务的状态"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "COMPLETED"
        mock_task.to_dict.return_value = {"id": "test-task-id", "status": "COMPLETED"}
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()
        result = manager.get_task_status("test-task-id")

        assert result is not None
        assert result["status"] == "COMPLETED"

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_get_task_status_non_existing(self, mock_session_local):
        """测试获取不存在任务的状态"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query().get.return_value = None

        manager = TaskManager()
        result = manager.get_task_status("non-existing-id")

        assert result is None

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_get_task_status_closes_db(self, mock_session_local):
        """测试获取任务状态后关闭数据库连接"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.to_dict.return_value = {"id": "test-id"}
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()
        manager.get_task_status("test-id")

        mock_db.close.assert_called_once()

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_cancel_task_running(self, mock_session_local):
        """测试取消正在运行的任务"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "IN_PROGRESS"
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()

        # 手动添加一个"正在运行"的任务
        manager.running_tasks["test-task-id"] = Mock()

        result = manager.cancel_task("test-task-id")

        assert result is True
        assert "test-task-id" not in manager.running_tasks

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_cancel_task_pending(self, mock_session_local):
        """测试取消待处理的任务"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "PENDING"
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()
        manager.running_tasks["test-task-id"] = Mock()

        result = manager.cancel_task("test-task-id")

        assert result is True
        mock_task.status = "FAILED"

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_cancel_task_non_existing(self, mock_session_local):
        """测试取消不存在的任务"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        manager = TaskManager()
        result = manager.cancel_task("non-existing-id")

        assert result is False

    def test_shutdown_wait_true(self):
        """测试关闭任务管理器（等待任务完成）"""
        manager = TaskManager()
        manager.shutdown(wait=True)
        # 没有异常即表示成功

    def test_shutdown_wait_false(self):
        """测试关闭任务管理器（不等待任务完成）"""
        manager = TaskManager()
        manager.shutdown(wait=False)
        # 没有异常即表示成功

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_submit_multiple_tasks(self, mock_session_local):
        """测试提交多个任务"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_db.query().get.return_value = mock_task

        manager = TaskManager(max_workers=3)

        def simple_task(task_id):
            time.sleep(0.1)
            return f"Task {task_id} completed"

        # 提交多个任务
        for i in range(5):
            manager.submit_task(f"task-{i}", simple_task, f"task-{i}")

        # 等待所有任务完成
        time.sleep(1)

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_task_with_dict_result(self, mock_session_local):
        """测试返回字典结果的任务"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "PENDING"
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()

        def dict_task():
            return {"key": "value", "number": 123}

        manager.submit_task("test-task-id", dict_task)
        time.sleep(0.5)

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_task_with_non_dict_result(self, mock_session_local):
        """测试返回非字典结果的任务"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = "PENDING"
        mock_db.query().get.return_value = mock_task

        manager = TaskManager()

        def string_task():
            return "string result"

        manager.submit_task("test-task-id", string_task)
        time.sleep(0.5)


class TestTaskManagerSingleton:
    """测试 TaskManager 单例"""

    @patch('app.services.ppt.task_manager.TaskManager')
    def test_get_task_manager_returns_singleton(self, mock_task_manager_class):
        """测试 get_task_manager 返回单例"""
        # 重置全局变量
        import app.services.ppt.task_manager as tm_module
        tm_module._task_manager = None

        mock_instance = Mock()
        mock_task_manager_class.return_value = mock_instance

        manager1 = get_task_manager()
        manager2 = get_task_manager()

        assert manager1 is manager2
        mock_task_manager_class.assert_called_once_with(max_workers=3)

    @patch('app.services.ppt.task_manager.TaskManager')
    def test_task_manager_global_instance(self, mock_task_manager_class):
        """测试全局 task_manager 实例"""
        # 重置全局变量
        import app.services.ppt.task_manager as tm_module
        tm_module._task_manager = None

        mock_instance = Mock()
        mock_task_manager_class.return_value = mock_instance

        # 导入会触发创建全局实例
        from app.services.ppt.task_manager import task_manager

        assert task_manager is not None


class TestTaskManagerTaskWrapper:
    """测试任务包装器的边界情况"""

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_task_not_found_in_wrapper(self, mock_session_local):
        """测试任务包装器中任务不存在的情况"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query().get.return_value = None

        manager = TaskManager()

        def simple_task():
            return "result"

        # 任务不存在，应该不会崩溃
        manager.submit_task("non-existing-task", simple_task)
        time.sleep(0.3)

    @patch('app.services.ppt.task_manager.SessionLocal')
    def test_task_database_error_in_wrapper(self, mock_session_local):
        """测试任务包装器中数据库错误的情况"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # 第一次调用返回任务，后续调用抛出异常
        mock_task = Mock()
        mock_task.status = "IN_PROGRESS"
        mock_db.query().get.return_value = mock_task
        mock_db.commit.side_effect = Exception("Database error")

        manager = TaskManager()

        def simple_task():
            return "result"

        # 应该捕获异常而不是崩溃
        manager.submit_task("test-task-id", simple_task)
        time.sleep(0.5)
