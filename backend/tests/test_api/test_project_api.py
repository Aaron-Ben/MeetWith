"""
测试项目 API 端点
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.project import project_router, CreateProjectRequest
from app.models.ppt.project import PPTProject
from app.models.ppt.page import Page


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(project_router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    with patch('app.api.project.get_db') as mock:
        db = MagicMock()
        mock.return_value = db
        yield db


class TestCreateProject:
    """测试创建项目端点"""

    def test_create_project_with_idea_type(self, client, mock_db):
        """测试使用 idea 类型创建项目"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.to_dict.return_value = {"project_id": "test-project-id"}
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(return_value=mock_project)

        with patch('app.api.project.PPTProject') as mock_project_class:
            mock_project_class.return_value = mock_project

            response = client.post(
                "/api/projects",
                json={
                    "idea_prompt": "制作一个关于AI的PPT",
                    "creation_type": "idea"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True

    def test_create_project_with_outline_type(self, client, mock_db):
        """测试使用 outline 类型创建项目"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.to_dict.return_value = {"project_id": "test-project-id"}
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(return_value=mock_project)

        with patch('app.api.project.PPTProject') as mock_project_class:
            mock_project_class.return_value = mock_project

            response = client.post(
                "/api/projects",
                json={
                    "outline_text": "第一章：AI概述\n第二章：机器学习",
                    "creation_type": "outline"
                }
            )

            assert response.status_code == 201

    def test_create_project_missing_idea_prompt(self, client, mock_db):
        """测试创建项目缺少 idea_prompt"""
        response = client.post(
            "/api/projects",
            json={
                "creation_type": "idea"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "idea_prompt is required" in data["detail"]

    def test_create_project_invalid_creation_type(self, client, mock_db):
        """测试无效的创建类型"""
        response = client.post(
            "/api/projects",
            json={
                "idea_prompt": "测试",
                "creation_type": "invalid_type"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid creation_type" in data["detail"]

    def test_create_project_missing_outline_text(self, client, mock_db):
        """测试创建项目缺少 outline_text"""
        response = client.post(
            "/api/projects",
            json={
                "creation_type": "outline"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "outline_text is required" in data["detail"]


class TestListProjects:
    """测试获取项目列表端点"""

    def test_list_projects_all(self, client, mock_db):
        """测试获取所有项目"""
        mock_project1 = Mock()
        mock_project1.to_dict.return_value = {"project_id": "1", "status": "DRAFT"}
        mock_project2 = Mock()
        mock_project2.to_dict.return_value = {"project_id": "2", "status": "DRAFT"}

        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = [mock_project1, mock_project2]
        mock_db.query.return_value = mock_query

        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["count"] == 2

    def test_list_projects_with_status_filter(self, client, mock_db):
        """测试按状态过滤项目"""
        mock_project = Mock()
        mock_project.to_dict.return_value = {"project_id": "1", "status": "DRAFT"}

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_project]
        mock_db.query.return_value = mock_query

        response = client.get("/api/projects?status=DRAFT")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["count"] == 1

    def test_list_projects_empty(self, client, mock_db):
        """测试获取空项目列表"""
        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["count"] == 0


class TestGetProject:
    """测试获取项目详情端点"""

    def test_get_project_success(self, client, mock_db):
        """测试成功获取项目"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.to_dict.return_value = {
            "project_id": "test-project-id",
            "status": "DRAFT"
        }
        mock_db.query().filter().first.return_value = mock_project

        response = client.get("/api/projects/test-project-id")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["project_id"] == "test-project-id"

    def test_get_project_not_found(self, client, mock_db):
        """测试获取不存在的项目"""
        mock_db.query().filter().first.return_value = None

        response = client.get("/api/projects/non-existing-id")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_project_with_pages(self, client, mock_db):
        """测试获取项目包含页面"""
        mock_page = Mock()
        mock_page.to_dict.return_value = {"page_id": "1", "order_index": 0}

        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.to_dict.return_value = {
            "project_id": "test-project-id",
            "pages": [mock_page.to_dict()]
        }
        mock_project.pages.order_by.return_value.all.return_value = [mock_page]
        mock_db.query().filter().first.return_value = mock_project

        response = client.get("/api/projects/test-project-id")

        assert response.status_code == 200


class TestUpdateProject:
    """测试更新项目端点"""

    def test_update_project_idea_prompt(self, client, mock_db):
        """测试更新项目想法"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.idea_prompt = "旧想法"
        mock_project.to_dict.return_value = {"project_id": "test-project-id"}
        mock_db.query().filter().first.return_value = mock_project

        response = client.put(
            "/api/projects/test-project-id",
            json={"idea_prompt": "新想法"}
        )

        assert response.status_code == 200
        assert mock_project.idea_prompt == "新想法"

    def test_update_project_status(self, client, mock_db):
        """测试更新项目状态"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.status = "DRAFT"
        mock_project.to_dict.return_value = {"project_id": "test-project-id"}
        mock_db.query().filter().first.return_value = mock_project

        response = client.put(
            "/api/projects/test-project-id",
            json={"status": "REVIEW"}
        )

        assert response.status_code == 200
        assert mock_project.status == "REVIEW"

    def test_update_project_not_found(self, client, mock_db):
        """测试更新不存在的项目"""
        mock_db.query().filter().first.return_value = None

        response = client.put(
            "/api/projects/non-existing-id",
            json={"status": "REVIEW"}
        )

        assert response.status_code == 404


class TestDeleteProject:
    """测试删除项目端点"""

    @patch('app.api.project.FileService')
    def test_delete_project_success(self, mock_file_service_class, client, mock_db):
        """测试成功删除项目"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_project

        mock_file_service = Mock()
        mock_file_service_class.return_value = mock_file_service

        response = client.delete("/api/projects/test-project-id")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch('app.api.project.FileService')
    def test_delete_project_not_found(self, mock_file_service_class, client, mock_db):
        """测试删除不存在的项目"""
        mock_db.query().filter().first.return_value = None

        response = client.delete("/api/projects/non-existing-id")

        assert response.status_code == 404


class TestGenerateOutline:
    """测试生成大纲端点"""

    @patch('app.api.project.AIService')
    @patch('app.api.project._get_reference_files_content')
    def test_generate_outline_success(self, mock_get_ref, mock_ai_class, client, mock_db):
        """测试成功生成大纲"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.idea_prompt = "测试想法"
        mock_project.extra_requirements = None
        mock_project.to_dict.return_value = {"project_id": "test-project-id"}
        mock_db.query().filter().first.return_value = mock_project

        mock_db.query().filter().all.return_value = []  # 没有现有页面

        mock_get_ref.return_value = []

        mock_ai_service = Mock()
        mock_ai_service.generate_outline_from_idea.return_value = [
            {
                "title": "第一部分",
                "pages": [
                    {"title": "页面1", "description": "描述1"}
                ]
            }
        ]
        mock_ai_class.return_value = mock_ai_service

        response = client.post(
            "/api/projects/test-project-id/generate/outline",
            json={"language": "zh"}
        )

        assert response.status_code == 200

    @patch('app.api.project.AIService')
    def test_generate_outline_project_not_found(self, mock_ai_class, client, mock_db):
        """测试为不存在的项目生成大纲"""
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/projects/non-existing-id/generate/outline",
            json={"language": "zh"}
        )

        assert response.status_code == 404

    @patch('app.api.project.AIService')
    def test_generate_outline_with_existing_pages(self, mock_ai_class, client, mock_db):
        """测试在有页面时生成大纲（不强制重新生成）"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_project

        mock_page = Mock()
        mock_db.query().filter().all.return_value = [mock_page]

        response = client.post(
            "/api/projects/test-project-id/generate/outline",
            json={"force_regenerate": False}
        )

        assert response.status_code == 400


class TestGenerateDescriptions:
    """测试生成描述端点"""

    @patch('app.api.project.AIService')
    @patch('app.api.project._get_reference_files_content')
    def test_generate_all_descriptions_success(self, mock_get_ref, mock_ai_class, client, mock_db):
        """测试成功生成所有描述"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.order_index = 0
        mock_page.part = None
        mock_page.get_outline_content.return_value = {
            "title": "页面1",
            "description": "描述1"
        }
        mock_page.set_description_content = Mock()
        mock_page.status = "OUTLINE_GENERATED"

        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.extra_requirements = None
        mock_db.query().filter().first.return_value = mock_project
        mock_db.query().order_by.return_value.all.return_value = [mock_page]

        mock_get_ref.return_value = []

        mock_ai_service = Mock()
        mock_ai_service.generate_page_description.return_value = "生成的描述文本"
        mock_ai_class.return_value = mock_ai_service

        response = client.post(
            "/api/projects/test-project-id/generate/all-descriptions",
            json={"language": "zh"}
        )

        assert response.status_code == 200

    @patch('app.api.project.AIService')
    def test_generate_all_descriptions_no_pages(self, mock_ai_class, client, mock_db):
        """测试没有页面时生成描述"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_project
        mock_db.query().order_by.return_value.all.return_value = []

        response = client.post(
            "/api/projects/test-project-id/generate/all-descriptions",
            json={"language": "zh"}
        )

        assert response.status_code == 400


class TestGenerateImages:
    """测试生成图片端点"""

    @patch('app.api.project.Task')
    def test_generate_all_images_success(self, mock_task_class, client, mock_db):
        """测试成功生成所有图片任务"""
        mock_page = Mock()
        mock_page.get_description_content.return_value = {"text": "描述内容"}

        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_project
        mock_db.query().order_by.return_value.all.return_value = [mock_page]

        mock_task = Mock()
        mock_task.id = "task-1"
        mock_task.set_progress = Mock()
        mock_task_class.return_value = mock_task

        response = client.post(
            "/api/projects/test-project-id/generate/all-images",
            json={"use_template": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data["data"]

    def test_generate_all_images_project_not_found(self, client, mock_db):
        """测试为不存在的项目生成图片"""
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/projects/non-existing-id/generate/all-images",
            json={"use_template": True}
        )

        assert response.status_code == 404

    @patch('app.api.project.Task')
    def test_generate_all_images_no_pages(self, mock_task_class, client, mock_db):
        """测试没有页面时生成图片"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_project
        mock_db.query().order_by.return_value.all.return_value = []

        response = client.post(
            "/api/projects/test-project-id/generate/all-images",
            json={"use_template": True}
        )

        assert response.status_code == 400


class TestGetTaskStatus:
    """测试获取任务状态端点"""

    @patch('app.api.project.get_task_manager')
    def test_get_task_status_success(self, mock_get_tm, client, mock_db):
        """测试成功获取任务状态"""
        mock_task_manager = Mock()
        mock_task_manager.get_task_status.return_value = {
            "task_id": "task-1",
            "status": "COMPLETED"
        }
        mock_get_tm.return_value = mock_task_manager

        response = client.get("/api/projects/test-project-id/tasks/task-1")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "COMPLETED"

    @patch('app.api.project.get_task_manager')
    def test_get_task_status_not_found(self, mock_get_tm, client, mock_db):
        """测试获取不存在的任务状态"""
        mock_task_manager = Mock()
        mock_task_manager.get_task_status.return_value = None
        mock_get_tm.return_value = mock_task_manager

        response = client.get("/api/projects/test-project-id/tasks/non-existing-task")

        assert response.status_code == 404
