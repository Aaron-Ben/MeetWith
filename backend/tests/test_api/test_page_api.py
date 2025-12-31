"""
测试页面 API 端点
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.page import page_router


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(page_router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    with patch('app.api.page.get_db') as mock:
        db = MagicMock()
        mock.return_value = db
        yield db


class TestCreatePage:
    """测试创建页面端点"""

    def test_create_page_success(self, client, mock_db):
        """测试成功创建页面"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_project

        mock_page = Mock()
        mock_page.id = "new-page-id"
        mock_page.to_dict.return_value = {"page_id": "new-page-id", "order_index": 0}
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()

        with patch('app.api.page.Page') as mock_page_class:
            mock_page_class.return_value = mock_page

            response = client.post(
                "/api/projects/test-project-id/pages",
                json={
                    "order_index": 0,
                    "part": "第一部分",
                    "outline_content": {"title": "测试页面"}
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert "data" in data

    def test_create_page_project_not_found(self, client, mock_db):
        """测试为不存在的项目创建页面"""
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/projects/non-existing-id/pages",
            json={"order_index": 0}
        )

        assert response.status_code == 404

    def test_create_page_minimum_fields(self, client, mock_db):
        """测试使用最少字段创建页面"""
        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_project

        mock_page = Mock()
        mock_page.id = "new-page-id"
        mock_page.to_dict.return_value = {"page_id": "new-page-id"}
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()

        with patch('app.api.page.Page') as mock_page_class:
            mock_page_class.return_value = mock_page

            response = client.post(
                "/api/projects/test-project-id/pages",
                json={"order_index": 0}
            )

            assert response.status_code == 201


class TestDeletePage:
    """测试删除页面端点"""

    @patch('app.api.page.FileService')
    def test_delete_page_success(self, mock_file_service_class, client, mock_db):
        """测试成功删除页面"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_page

        mock_project = Mock()
        mock_db.query().filter.return_value.first.return_value = mock_project

        mock_file_service = Mock()
        mock_file_service.delete_page_image = MagicMock()
        mock_file_service_class.return_value = mock_file_service

        response = client.delete("/api/projects/test-project-id/pages/page-1")

        assert response.status_code == 200

    def test_delete_page_not_found(self, client, mock_db):
        """测试删除不存在的页面"""
        mock_db.query().filter().first.return_value = None

        response = client.delete("/api/projects/test-project-id/pages/non-existing-page")

        assert response.status_code == 404

    @patch('app.api.page.FileService')
    def test_delete_page_wrong_project(self, mock_file_service_class, client, mock_db):
        """测试删除不属于该项目的页面"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "other-project-id"
        mock_db.query().filter().first.return_value = mock_page

        response = client.delete("/api/projects/test-project-id/pages/page-1")

        assert response.status_code == 404


class TestUpdatePageOutline:
    """测试更新页面大纲端点"""

    def test_update_page_outline_success(self, client, mock_db):
        """测试成功更新页面大纲"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.to_dict.return_value = {"page_id": "page-1"}
        mock_db.query().filter().first.return_value = mock_page

        mock_project = Mock()
        mock_db.query().filter.return_value.first.return_value = mock_project

        outline_data = {
            "title": "新标题",
            "description": "新描述"
        }

        response = client.put(
            "/api/projects/test-project-id/pages/page-1/outline",
            json={"outline_content": outline_data}
        )

        assert response.status_code == 200

    def test_update_page_outline_not_found(self, client, mock_db):
        """测试更新不存在的页面大纲"""
        mock_db.query().filter().first.return_value = None

        response = client.put(
            "/api/projects/test-project-id/pages/non-existing-page/outline",
            json={"outline_content": {"title": "新标题"}}
        )

        assert response.status_code == 404


class TestUpdatePageDescription:
    """测试更新页面描述端点"""

    def test_update_page_description_success(self, client, mock_db):
        """测试成功更新页面描述"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.to_dict.return_value = {"page_id": "page-1"}
        mock_db.query().filter().first.return_value = mock_page

        mock_project = Mock()
        mock_db.query().filter.return_value.first.return_value = mock_project

        desc_data = {
            "text": "新的描述文本",
            "text_content": ["要点1", "要点2"]
        }

        response = client.put(
            "/api/projects/test-project-id/pages/page-1/description",
            json={"description_content": desc_data}
        )

        assert response.status_code == 200

    def test_update_page_description_not_found(self, client, mock_db):
        """测试更新不存在的页面描述"""
        mock_db.query().filter().first.return_value = None

        response = client.put(
            "/api/projects/test-project-id/pages/non-existing-page/description",
            json={"description_content": {"text": "描述"}}
        )

        assert response.status_code == 404


class TestGeneratePageDescription:
    """测试生成页面描述端点"""

    @patch('app.api.page.AIService')
    @patch('app.api.page._get_project_reference_files_content')
    @patch('app.api.page.ProjectContext')
    def test_generate_page_description_success(
        self, mock_context_class, mock_get_ref, mock_ai_class, client, mock_db
    ):
        """测试成功生成页面描述"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.part = None
        mock_page.get_outline_content.return_value = {
            "title": "测试标题",
            "description": "测试描述"
        }
        mock_page.get_description_content.return_value = None
        mock_page.to_dict.return_value = {"page_id": "page-1"}
        mock_db.query().filter().first.return_value = mock_page
        mock_db.query().order_by.return_value.all.return_value = [mock_page]

        mock_project = Mock()
        mock_project.idea_prompt = "测试项目"
        mock_project.extra_requirements = None
        mock_db.query().filter.return_value.first.return_value = mock_project

        mock_get_ref.return_value = []

        mock_context = Mock()
        mock_context_class.return_value = mock_context

        mock_ai_service = Mock()
        mock_ai_service.generate_page_description.return_value = "生成的描述内容"
        mock_ai_class.return_value = mock_ai_service

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/generate/description",
            json={"language": "zh"}
        )

        assert response.status_code == 200

    def test_generate_page_description_page_not_found(self, client, mock_db):
        """测试为不存在的页面生成描述"""
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/projects/test-project-id/pages/non-existing-page/generate/description",
            json={"language": "zh"}
        )

        assert response.status_code == 404

    @patch('app.api.page.AIService')
    @patch('app.api.page._get_project_reference_files_content')
    def test_generate_page_description_already_exists(
        self, mock_get_ref, mock_ai_class, client, mock_db
    ):
        """测试生成已存在的描述（不强制重新生成）"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.get_outline_content.return_value = {"title": "标题"}
        mock_page.get_description_content.return_value = {"text": "已有描述"}
        mock_db.query().filter().first.return_value = mock_page

        mock_project = Mock()
        mock_db.query().filter.return_value.first.return_value = mock_project

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/generate/description",
            json={"force_regenerate": False}
        )

        assert response.status_code == 400

    @patch('app.api.page.AIService')
    def test_generate_page_description_no_outline(
        self, mock_ai_class, client, mock_db
    ):
        """测试没有大纲时生成描述"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.get_outline_content.return_value = None
        mock_page.get_description_content.return_value = None
        mock_db.query().filter().first.return_value = mock_page

        mock_project = Mock()
        mock_db.query().filter.return_value.first.return_value = mock_project

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/generate/description",
            json={"force_regenerate": True}
        )

        assert response.status_code == 400


class TestGeneratePageImage:
    """测试生成页面图片端点"""

    @patch('app.api.page.task_manager')
    @patch('app.api.page.FileService')
    @patch('app.api.page.AIService')
    def test_generate_page_image_success(
        self, mock_ai_class, mock_file_service_class, mock_tm, client, mock_db
    ):
        """测试成功生成页面图片"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.part = None
        mock_page.generated_image_path = None
        mock_page.get_outline_content.return_value = {"title": "标题"}
        mock_page.get_description_content.return_value = {
            "text": "这是描述文本，包含 ![图片](https://example.com/img.png) 的markdown"
        }
        mock_db.query().filter().first.return_value = mock_page
        mock_db.query().order_by.return_value.all.return_value = [mock_page]

        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_project.extra_requirements = None
        mock_db.query().filter.return_value.first.return_value = mock_project

        mock_file_service = Mock()
        mock_file_service.get_template_path = MagicMock(return_value="/path/to/template.png")
        mock_file_service_class.return_value = mock_file_service

        mock_ai_service = Mock()
        mock_ai_service.extract_image_urls_from_markdown.return_value = []
        mock_ai_class.return_value = mock_ai_service

        mock_task = Mock()
        mock_task.id = "task-1"
        mock_task.set_progress = Mock()
        mock_tm.submit_task = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()

        with patch('app.api.page.Task') as mock_task_class:
            mock_task_class.return_value = mock_task

            response = client.post(
                "/api/projects/test-project-id/pages/page-1/generate/image",
                json={"use_template": True}
            )

            assert response.status_code == 202

    def test_generate_page_image_page_not_found(self, client, mock_db):
        """测试为不存在的页面生成图片"""
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/projects/test-project-id/pages/non-existing-page/generate/image",
            json={"use_template": True}
        )

        assert response.status_code == 404

    @patch('app.api.page.FileService')
    @patch('app.api.page.AIService')
    def test_generate_page_image_already_exists(
        self, mock_ai_class, mock_file_service_class, client, mock_db
    ):
        """测试生成已存在的图片（不强制重新生成）"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.generated_image_path = "/existing/image.png"
        mock_db.query().filter().first.return_value = mock_page

        mock_project = Mock()
        mock_db.query().filter.return_value.first.return_value = mock_project

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/generate/image",
            json={"force_regenerate": False}
        )

        assert response.status_code == 400


class TestEditPageImage:
    """测试编辑页面图片端点"""

    @patch('app.api.page.task_manager')
    @patch('app.api.page.FileService')
    def test_edit_page_image_success(
        self, mock_file_service_class, mock_tm, client, mock_db
    ):
        """测试成功编辑页面图片"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.generated_image_path = "/existing/image.png"
        mock_page.get_description_content.return_value = {"text": "描述"}
        mock_db.query().filter().first.return_value = mock_page

        mock_project = Mock()
        mock_project.id = "test-project-id"
        mock_db.query().filter.return_value.first.return_value = mock_project

        mock_file_service = Mock()
        mock_file_service.get_absolute_path.return_value = "/absolute/path/image.png"
        mock_file_service.get_template_path = MagicMock(return_value=None)
        mock_file_service_class.return_value = mock_file_service

        mock_task = Mock()
        mock_task.id = "task-1"
        mock_task.set_progress = Mock()
        mock_tm.submit_task = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()

        with patch('app.api.page.Task') as mock_task_class:
            mock_task_class.return_value = mock_task

            response = client.post(
                "/api/projects/test-project-id/pages/page-1/edit/image",
                data={
                    "edit_instruction": "把背景改成蓝色",
                    "use_template": "false",
                    "desc_image_urls": "[]"
                }
            )

            assert response.status_code == 202

    def test_edit_page_image_page_not_found(self, client, mock_db):
        """测试编辑不存在的页面图片"""
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/projects/test-project-id/pages/non-existing-page/edit/image",
            data={"edit_instruction": "修改图片"}
        )

        assert response.status_code == 404

    def test_edit_page_image_no_generated_image(self, client, mock_db):
        """测试编辑没有生成图片的页面"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.generated_image_path = None
        mock_db.query().filter().first.return_value = mock_page

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/edit/image",
            data={"edit_instruction": "修改图片"}
        )

        assert response.status_code == 400


class TestGetPageImageVersions:
    """测试获取页面图片版本列表端点"""

    def test_get_page_image_versions_success(self, client, mock_db):
        """测试成功获取页面图片版本"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_page

        mock_version1 = Mock()
        mock_version1.to_dict.return_value = {
            "version_id": "v1",
            "version_number": 1
        }
        mock_version2 = Mock()
        mock_version2.to_dict.return_value = {
            "version_id": "v2",
            "version_number": 2
        }

        mock_db.query().order_by.return_value.all.return_value = [
            mock_version2, mock_version1
        ]

        response = client.get(
            "/api/projects/test-project-id/pages/page-1/image-versions"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["versions"]) == 2

    def test_get_page_image_versions_page_not_found(self, client, mock_db):
        """测试获取不存在页面的图片版本"""
        mock_db.query().filter().first.return_value = None

        response = client.get(
            "/api/projects/test-project-id/pages/non-existing-page/image-versions"
        )

        assert response.status_code == 404


class TestSetCurrentImageVersion:
    """测试设置当前图片版本端点"""

    def test_set_current_image_version_success(self, client, mock_db):
        """测试成功设置当前图片版本"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_page.to_dict.return_value = {"page_id": "page-1"}
        mock_db.query().filter().first.return_value = mock_page

        mock_version = Mock()
        mock_version.id = "version-1"
        mock_version.page_id = "page-1"
        mock_db.query().filter.return_value.first.return_value = mock_version

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/image-versions/version-1/set-current"
        )

        assert response.status_code == 200

    def test_set_current_image_version_page_not_found(self, client, mock_db):
        """测试为不存在的页面设置当前版本"""
        mock_page = Mock()
        mock_page.project_id = "other-project"
        mock_db.query().filter().first.return_value = mock_page

        mock_version = Mock()
        mock_version.id = "version-1"
        mock_db.query().filter.return_value.first.return_value = mock_version

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/image-versions/version-1/set-current"
        )

        assert response.status_code == 404

    def test_set_current_image_version_not_found(self, client, mock_db):
        """测试设置不存在的版本为当前"""
        mock_page = Mock()
        mock_page.id = "page-1"
        mock_page.project_id = "test-project-id"
        mock_db.query().filter().first.return_value = mock_page

        mock_db.query().filter.return_value.first.return_value = None

        response = client.post(
            "/api/projects/test-project-id/pages/page-1/image-versions/non-existing-version/set-current"
        )

        assert response.status_code == 404
