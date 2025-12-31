"""
测试 PPTProject 模型
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from app.models.ppt.project import PPTProject
from app.models.database import Base


class TestPPTProject:
    """测试 PPTProject 模型"""

    def test_project_creation_with_minimum_fields(self):
        """测试使用最少字段创建项目"""
        project = PPTProject()
        assert project is not None
        assert project.id is not None
        assert len(project.id) == 36  # UUID 长度
        assert project.status == 'DRAFT'
        assert project.creation_type == 'idea'
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_project_creation_with_all_fields(self):
        """测试使用所有字段创建项目"""
        project = PPTProject(
            idea_prompt="制作一个关于人工智能的PPT",
            outline_text="第一章：AI概述\n第二章：机器学习\n第三章：深度学习",
            description_text="详细介绍人工智能的发展历程",
            extra_requirements="使用现代风格，配色简洁",
            creation_type="idea",
            template_image_path="/uploads/template.png",
            status="REVIEW"
        )

        assert project.idea_prompt == "制作一个关于人工智能的PPT"
        assert project.outline_text == "第一章：AI概述\n第二章：机器学习\n第三章：深度学习"
        assert project.description_text == "详细介绍人工智能的发展历程"
        assert project.extra_requirements == "使用现代风格，配色简洁"
        assert project.creation_type == "idea"
        assert project.template_image_path == "/uploads/template.png"
        assert project.status == "REVIEW"

    def test_project_default_status(self):
        """测试项目默认状态"""
        project = PPTProject()
        assert project.status == 'DRAFT'

    def test_project_default_creation_type(self):
        """测试项目默认创建类型"""
        project = PPTProject()
        assert project.creation_type == 'idea'

    def test_project_valid_statuses(self):
        """测试有效的项目状态"""
        valid_statuses = ['DRAFT', 'REVIEW', 'APPROVED', 'REJECTED']
        for status in valid_statuses:
            project = PPTProject(status=status)
            assert project.status == status

    def test_project_valid_creation_types(self):
        """测试有效的创建类型"""
        valid_types = ['idea', 'outline', 'descriptions']
        for creation_type in valid_types:
            project = PPTProject(creation_type=creation_type)
            assert project.creation_type == creation_type

    def test_project_timestamps_on_creation(self):
        """测试创建时的时间戳"""
        before_creation = datetime.utcnow()
        project = PPTProject()
        after_creation = datetime.utcnow()

        assert project.created_at >= before_creation
        assert project.created_at <= after_creation
        assert project.updated_at >= before_creation
        assert project.updated_at <= after_creation

    def test_project_to_dict_basic(self):
        """测试基本的 to_dict 方法"""
        project = PPTProject(
            idea_prompt="测试项目",
            creation_type="idea",
            status="DRAFT"
        )

        result = project.to_dict()

        assert isinstance(result, dict)
        assert 'project_id' in result
        assert result['project_id'] == project.id
        assert result['idea_prompt'] == "测试项目"
        assert result['creation_type'] == "idea"
        assert result['status'] == "DRAFT"
        assert result['outline_text'] is None
        assert result['description_text'] is None
        assert result['extra_requirements'] is None

    def test_project_to_dict_with_template_image(self):
        """测试包含模板图片的 to_dict 方法"""
        project = PPTProject(
            id="test-project-id",
            template_image_path="uploads/template.png"
        )

        result = project.to_dict()
        assert 'template_image_url' in result
        assert result['template_image_url'] == '/files/test-project-id/template/template.png'

    def test_project_to_dict_without_template_image(self):
        """测试没有模板图片的 to_dict 方法"""
        project = PPTProject(template_image_path=None)
        result = project.to_dict()
        assert result['template_image_url'] is None

    def test_project_to_dict_include_pages_false(self):
        """测试 to_dict 不包含页面"""
        project = PPTProject()
        result = project.to_dict(include_pages=False)
        assert 'pages' not in result

    def test_project_to_dict_timestamps_format(self):
        """测试 to_dict 时间戳格式"""
        project = PPTProject()
        result = project.to_dict()

        assert 'created_at' in result
        assert 'updated_at' in result
        # 检查是 ISO 格式字符串
        assert isinstance(result['created_at'], str)
        assert isinstance(result['updated_at'], str)

    def test_project_repr(self):
        """测试项目的字符串表示"""
        project = PPTProject(id="test-id", status="DRAFT")
        repr_str = repr(project)
        assert "test-id" in repr_str
        assert "DRAFT" in repr_str

    def test_project_id_is_unique(self):
        """测试项目ID是唯一的"""
        project1 = PPTProject()
        project2 = PPTProject()
        assert project1.id != project2.id

    def test_project_id_format(self):
        """测试项目ID格式（UUID）"""
        project = PPTProject()
        # UUID 格式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, project.id.lower())

    def test_project_nullable_text_fields(self):
        """测试可空的文本字段"""
        project = PPTProject()
        assert project.idea_prompt is None
        assert project.outline_text is None
        assert project.description_text is None
        assert project.extra_requirements is None
        assert project.template_image_path is None

    def test_project_update_field(self):
        """测试更新项目字段"""
        project = PPTProject(status="DRAFT")
        project.status = "REVIEW"
        assert project.status == "REVIEW"

    def test_project_idea_prompt_can_be_long_text(self):
        """测试项目想法可以是长文本"""
        long_prompt = """
        这是一个非常长的项目想法，包含多个段落和详细描述。

        第一段：介绍项目的背景和目标
        第二段：详细说明技术方案
        第三段：描述预期效果和成果

        这里可以包含更多的内容...
        """
        project = PPTProject(idea_prompt=long_prompt)
        assert project.idea_prompt == long_prompt
        assert len(project.idea_prompt) > 100

    def test_project_extra_requirements_can_be_long_text(self):
        """测试额外要求可以是长文本"""
        long_requirements = """
        1. 风格要求：现代简约风格
        2. 配色方案：蓝色系为主
        3. 字体要求：使用无衬线字体
        4. 排版要求：留白充足
        """
        project = PPTProject(extra_requirements=long_requirements)
        assert project.extra_requirements == long_requirements

    def test_project_relationships_exist(self):
        """测试项目关系存在"""
        project = PPTProject()
        # 检查关系属性存在
        assert hasattr(project, 'pages')
        assert hasattr(project, 'tasks')
        assert hasattr(project, 'materials')


class TestPPTProjectCreationTypes:
    """测试项目创建类型"""

    def test_idea_creation_type(self):
        """测试 idea 创建类型"""
        project = PPTProject(
            creation_type="idea",
            idea_prompt="制作一个关于AI的PPT"
        )
        assert project.creation_type == "idea"

    def test_outline_creation_type(self):
        """测试 outline 创建类型"""
        project = PPTProject(
            creation_type="outline",
            outline_text="第一章：AI概述\n第二章：机器学习"
        )
        assert project.creation_type == "outline"

    def test_descriptions_creation_type(self):
        """测试 descriptions 创建类型"""
        project = PPTProject(
            creation_type="descriptions",
            description_text="详细介绍人工智能的各个方面"
        )
        assert project.creation_type == "descriptions"


class TestPPTProjectStatusWorkflow:
    """测试项目状态工作流"""

    def test_draft_to_review_transition(self):
        """测试从草稿到审核的状态转换"""
        project = PPTProject(status="DRAFT")
        project.status = "REVIEW"
        assert project.status == "REVIEW"

    def test_review_to_approved_transition(self):
        """测试从审核到批准的状态转换"""
        project = PPTProject(status="REVIEW")
        project.status = "APPROVED"
        assert project.status == "APPROVED"

    def test_review_to_rejected_transition(self):
        """测试从审核到拒绝的状态转换"""
        project = PPTProject(status="REVIEW")
        project.status = "REJECTED"
        assert project.status == "REJECTED"

    def test_all_status_transitions(self):
        """测试所有可能的状态转换"""
        statuses = ["DRAFT", "REVIEW", "APPROVED", "REJECTED"]
        for status in statuses:
            project = PPTProject(status=status)
            assert project.status == status
