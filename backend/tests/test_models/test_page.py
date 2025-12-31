"""
测试 Page 模型
"""
import pytest
import json
from datetime import datetime

from app.models.ppt.page import Page


class TestPage:
    """测试 Page 模型"""

    def test_page_creation_with_minimum_fields(self):
        """测试使用最少字段创建页面"""
        page = Page(
            project_id="test-project-id",
            order_index=0
        )

        assert page is not None
        assert page.id is not None
        assert len(page.id) == 36  # UUID 长度
        assert page.project_id == "test-project-id"
        assert page.order_index == 0
        assert page.status == 'DRAFT'
        assert page.created_at is not None
        assert page.updated_at is not None

    def test_page_creation_with_all_fields(self):
        """测试使用所有字段创建页面"""
        page = Page(
            project_id="test-project-id",
            order_index=1,
            part="第一部分",
            content="页面内容",
            status="DESCRIPTION_GENERATED"
        )

        assert page.project_id == "test-project-id"
        assert page.order_index == 1
        assert page.part == "第一部分"
        assert page.content == "页面内容"
        assert page.status == "DESCRIPTION_GENERATED"

    def test_page_default_status(self):
        """测试页面默认状态"""
        page = Page(project_id="test-project-id", order_index=0)
        assert page.status == 'DRAFT'

    def test_page_valid_statuses(self):
        """测试有效的页面状态"""
        valid_statuses = ['DRAFT', 'OUTLINE_GENERATED', 'DESCRIPTION_GENERATED', 'IMAGE_GENERATED']
        for status in valid_statuses:
            page = Page(project_id="test-project-id", order_index=0, status=status)
            assert page.status == status

    def test_page_timestamps_on_creation(self):
        """测试创建时的时间戳"""
        before_creation = datetime.utcnow()
        page = Page(project_id="test-project-id", order_index=0)
        after_creation = datetime.utcnow()

        assert page.created_at >= before_creation
        assert page.created_at <= after_creation
        assert page.updated_at >= before_creation
        assert page.updated_at <= after_creation

    def test_page_id_is_unique(self):
        """测试页面ID是唯一的"""
        page1 = Page(project_id="test-project-id", order_index=0)
        page2 = Page(project_id="test-project-id", order_index=1)
        assert page1.id != page2.id

    def test_page_id_format(self):
        """测试页面ID格式（UUID）"""
        page = Page(project_id="test-project-id", order_index=0)
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, page.id.lower())

    def test_page_nullable_fields(self):
        """测试可空字段"""
        page = Page(project_id="test-project-id", order_index=0)
        assert page.part is None
        assert page.content is None
        assert page.outline_content is None
        assert page.description_content is None
        assert page.generated_image_path is None

    def test_page_repr(self):
        """测试页面的字符串表示"""
        page = Page(id="test-page-id", order_index=1, status="DRAFT")
        repr_str = repr(page)
        assert "test-page-id" in repr_str
        assert "1" in repr_str
        assert "DRAFT" in repr_str


class TestPageOutlineContent:
    """测试页面大纲内容"""

    def test_set_outline_content_with_dict(self):
        """测试设置大纲内容（字典）"""
        page = Page(project_id="test-project-id", order_index=0)
        outline_data = {
            "title": "测试标题",
            "description": "测试描述"
        }
        page.set_outline_content(outline_data)

        assert page.outline_content is not None

    def test_get_outline_content_with_valid_json(self):
        """测试获取有效的大纲内容"""
        page = Page(project_id="test-project-id", order_index=0)
        outline_data = {
            "title": "测试标题",
            "description": "测试描述"
        }
        page.set_outline_content(outline_data)

        result = page.get_outline_content()
        assert result is not None
        assert result["title"] == "测试标题"
        assert result["description"] == "测试描述"

    def test_get_outline_content_with_invalid_json(self):
        """测试获取无效 JSON 的大纲内容"""
        page = Page(project_id="test-project-id", order_index=0)
        page.outline_content = "invalid json"

        result = page.get_outline_content()
        assert result is None

    def test_get_outline_content_when_empty(self):
        """测试获取空的大纲内容"""
        page = Page(project_id="test-project-id", order_index=0)
        result = page.get_outline_content()
        assert result is None

    def test_set_outline_content_with_none(self):
        """测试设置 None 大纲内容"""
        page = Page(project_id="test-project-id", order_index=0)
        page.set_outline_content(None)
        assert page.outline_content is None

    def test_set_outline_content_with_empty_dict(self):
        """测试设置空字典大纲内容"""
        page = Page(project_id="test-project-id", order_index=0)
        page.set_outline_content({})
        result = page.get_outline_content()
        assert result == {}

    def test_outline_content_with_nested_structure(self):
        """测试嵌套结构的大纲内容"""
        page = Page(project_id="test-project-id", order_index=0)
        outline_data = {
            "title": "第一部分",
            "pages": [
                {"title": "页面1", "description": "描述1"},
                {"title": "页面2", "description": "描述2"}
            ],
            "metadata": {
                "level": 1,
                "order": 0
            }
        }
        page.set_outline_content(outline_data)

        result = page.get_outline_content()
        assert result["title"] == "第一部分"
        assert len(result["pages"]) == 2
        assert result["metadata"]["level"] == 1


class TestPageDescriptionContent:
    """测试页面描述内容"""

    def test_set_description_content_with_dict(self):
        """测试设置描述内容（字典）"""
        page = Page(project_id="test-project-id", order_index=0)
        desc_data = {
            "text": "这是测试描述",
            "generated_at": "2024-01-01T00:00:00"
        }
        page.set_description_content(desc_data)

        assert page.description_content is not None

    def test_get_description_content_with_valid_json(self):
        """测试获取有效的描述内容"""
        page = Page(project_id="test-project-id", order_index=0)
        desc_data = {
            "text": "这是测试描述",
            "text_content": ["要点1", "要点2", "要点3"],
            "generated_at": "2024-01-01T00:00:00"
        }
        page.set_description_content(desc_data)

        result = page.get_description_content()
        assert result is not None
        assert result["text"] == "这是测试描述"
        assert len(result["text_content"]) == 3

    def test_get_description_content_with_invalid_json(self):
        """测试获取无效 JSON 的描述内容"""
        page = Page(project_id="test-project-id", order_index=0)
        page.description_content = "invalid json"

        result = page.get_description_content()
        assert result is None

    def test_get_description_content_when_empty(self):
        """测试获取空的描述内容"""
        page = Page(project_id="test-project-id", order_index=0)
        result = page.get_description_content()
        assert result is None

    def test_set_description_content_with_none(self):
        """测试设置 None 描述内容"""
        page = Page(project_id="test-project-id", order_index=0)
        page.set_description_content(None)
        assert page.description_content is None

    def test_description_content_with_text_content_list(self):
        """测试包含文本内容列表的描述"""
        page = Page(project_id="test-project-id", order_index=0)
        desc_data = {
            "text": "主要描述",
            "text_content": [
                "第一点内容",
                "第二点内容",
                "第三点内容"
            ]
        }
        page.set_description_content(desc_data)

        result = page.get_description_content()
        assert result["text"] == "主要描述"
        assert len(result["text_content"]) == 3


class TestPageToDict:
    """测试页面 to_dict 方法"""

    def test_to_dict_basic_fields(self):
        """测试基本字段的 to_dict"""
        page = Page(
            id="test-page-id",
            project_id="test-project-id",
            order_index=1,
            part="第一部分",
            status="DRAFT"
        )

        result = page.to_dict()

        assert isinstance(result, dict)
        assert result['page_id'] == "test-page-id"
        assert result['order_index'] == 1
        assert result['part'] == "第一部分"
        assert result['status'] == "DRAFT"

    def test_to_dict_with_outline_content(self):
        """测试包含大纲内容的 to_dict"""
        page = Page(project_id="test-project-id", order_index=0)
        outline_data = {"title": "标题", "description": "描述"}
        page.set_outline_content(outline_data)

        result = page.to_dict()
        assert result['outline_content']['title'] == "标题"
        assert result['outline_content']['description'] == "描述"

    def test_to_dict_with_description_content(self):
        """测试包含描述内容的 to_dict"""
        page = Page(project_id="test-project-id", order_index=0)
        desc_data = {"text": "描述文本", "text_content": ["要点1"]}
        page.set_description_content(desc_data)

        result = page.to_dict()
        assert result['description_content']['text'] == "描述文本"

    def test_to_dict_with_generated_image(self):
        """测试包含生成图片的 to_dict"""
        page = Page(
            project_id="test-project-id",
            order_index=0,
            generated_image_path="uploads/pages/page_1.png"
        )

        result = page.to_dict()
        assert 'generated_image_url' in result
        assert 'page_1.png' in result['generated_image_url']

    def test_to_dict_without_generated_image(self):
        """测试没有生成图片的 to_dict"""
        page = Page(project_id="test-project-id", order_index=0)
        result = page.to_dict()
        assert result['generated_image_url'] is None

    def test_to_dict_timestamps_format(self):
        """测试 to_dict 时间戳格式"""
        page = Page(project_id="test-project-id", order_index=0)
        result = page.to_dict()

        assert 'created_at' in result
        assert 'updated_at' in result
        assert isinstance(result['created_at'], str)
        assert isinstance(result['updated_at'], str)

    def test_to_dict_none_outline_content(self):
        """测试空大纲内容的 to_dict"""
        page = Page(project_id="test-project-id", order_index=0)
        result = page.to_dict()
        assert result['outline_content'] is None

    def test_to_dict_none_description_content(self):
        """测试空描述内容的 to_dict"""
        page = Page(project_id="test-project-id", order_index=0)
        result = page.to_dict()
        assert result['description_content'] is None


class TestPageOrderIndex:
    """测试页面排序索引"""

    def test_order_index_sequence(self):
        """测试排序索引序列"""
        pages = [
            Page(project_id="test-project-id", order_index=i)
            for i in range(5)
        ]
        for i, page in enumerate(pages):
            assert page.order_index == i

    def test_order_index_can_be_large(self):
        """测试排序索引可以是大数值"""
        page = Page(project_id="test-project-id", order_index=9999)
        assert page.order_index == 9999

    def test_order_index_zero(self):
        """测试排序索引为零"""
        page = Page(project_id="test-project-id", order_index=0)
        assert page.order_index == 0


class TestPagePartField:
    """测试页面部分字段"""

    def test_part_with_chinese_characters(self):
        """测试中文字符的部分名称"""
        page = Page(project_id="test-project-id", order_index=0, part="第一部分：介绍")
        assert page.part == "第一部分：介绍"

    def test_part_with_english_characters(self):
        """测试英文字符的部分名称"""
        page = Page(project_id="test-project-id", order_index=0, part="Part 1: Introduction")
        assert page.part == "Part 1: Introduction"

    def test_part_can_be_none(self):
        """测试部分可以为 None"""
        page = Page(project_id="test-project-id", order_index=0, part=None)
        assert page.part is None

    def test_part_with_special_characters(self):
        """测试包含特殊字符的部分名称"""
        page = Page(project_id="test-project-id", order_index=0, part="第一章 - AI技术")
        assert page.part == "第一章 - AI技术"


class TestPageStatusWorkflow:
    """测试页面状态工作流"""

    def test_draft_to_outline_generated(self):
        """测试从草稿到大纲已生成"""
        page = Page(project_id="test-project-id", order_index=0, status="DRAFT")
        page.status = "OUTLINE_GENERATED"
        assert page.status == "OUTLINE_GENERATED"

    def test_outline_to_description_generated(self):
        """测试从大纲到描述已生成"""
        page = Page(project_id="test-project-id", order_index=0, status="OUTLINE_GENERATED")
        page.status = "DESCRIPTION_GENERATED"
        assert page.status == "DESCRIPTION_GENERATED"

    def test_description_to_image_generated(self):
        """测试从描述到图片已生成"""
        page = Page(project_id="test-project-id", order_index=0, status="DESCRIPTION_GENERATED")
        page.status = "IMAGE_GENERATED"
        assert page.status == "IMAGE_GENERATED"
