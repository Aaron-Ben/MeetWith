"""
测试 AIService 服务
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.ppt.ai_service import AIService, ProjectContext


class TestProjectContext:
    """测试 ProjectContext 类"""

    def test_project_context_creation_without_reference_files(self):
        """测试不带参考文件的项目上下文创建"""
        mock_project = Mock()
        mock_project.idea_prompt = "测试想法"
        mock_project.extra_requirements = "额外要求"

        context = ProjectContext(mock_project)

        assert context.project == mock_project
        assert context.reference_files_content == []

    def test_project_context_creation_with_reference_files(self):
        """测试带参考文件的项目上下文创建"""
        mock_project = Mock()
        mock_project.idea_prompt = "测试想法"
        mock_project.extra_requirements = None

        reference_files = ["参考内容1", "参考内容2"]
        context = ProjectContext(mock_project, reference_files)

        assert context.project == mock_project
        assert context.reference_files_content == reference_files

    def test_get_context_prompt_with_idea_prompt(self):
        """测试获取包含想法的上下文提示"""
        mock_project = Mock()
        mock_project.idea_prompt = "制作一个关于AI的PPT"
        mock_project.extra_requirements = None

        context = ProjectContext(mock_project)
        prompt = context.get_context_prompt()

        assert "制作一个关于AI的PPT" in prompt
        assert "项目主题" in prompt

    def test_get_context_prompt_with_extra_requirements(self):
        """测试获取包含额外要求的上下文提示"""
        mock_project = Mock()
        mock_project.idea_prompt = None
        mock_project.extra_requirements = "使用现代风格"

        context = ProjectContext(mock_project)
        prompt = context.get_context_prompt()

        assert "使用现代风格" in prompt
        assert "额外要求" in prompt

    def test_get_context_prompt_with_reference_files(self):
        """测试获取包含参考文件的上下文提示"""
        mock_project = Mock()
        mock_project.idea_prompt = "测试"
        mock_project.extra_requirements = None

        reference_files = ["这是参考内容1", "这是参考内容2"]
        context = ProjectContext(mock_project, reference_files)
        prompt = context.get_context_prompt()

        assert "参考文件内容" in prompt
        assert "参考文件 1" in prompt
        assert "参考文件 2" in prompt

    def test_get_context_prompt_truncates_long_reference_content(self):
        """测试上下文提示截断过长的参考内容"""
        mock_project = Mock()
        mock_project.idea_prompt = None
        mock_project.extra_requirements = None

        # 创建一个超过2000字符的参考内容
        long_content = "A" * 3000
        context = ProjectContext(mock_project, [long_content])
        prompt = context.get_context_prompt()

        # 检查内容被截断（带省略号）
        assert "..." in prompt
        # 实际内容应该少于原始长度
        assert len(prompt) < len(long_content)

    def test_get_context_prompt_with_no_context(self):
        """测试没有上下文时的提示"""
        mock_project = Mock()
        mock_project.idea_prompt = None
        mock_project.extra_requirements = None

        context = ProjectContext(mock_project, [])
        prompt = context.get_context_prompt()

        assert prompt == "无特定上下文"

    def test_get_context_prompt_with_all_fields(self):
        """测试包含所有字段的上下文提示"""
        mock_project = Mock()
        mock_project.idea_prompt = "AI技术介绍"
        mock_project.extra_requirements = "使用蓝色主题"

        reference_files = ["参考文档内容"]
        context = ProjectContext(mock_project, reference_files)
        prompt = context.get_context_prompt()

        assert "AI技术介绍" in prompt
        assert "使用蓝色主题" in prompt
        assert "参考文档内容" in prompt


class TestAIService:
    """测试 AIService 类"""

    def test_ai_service_creation(self):
        """测试 AI 服务创建"""
        with patch('app.services.ppt.ai_service.LLMClient'):
            service = AIService()
            assert service is not None
            assert hasattr(service, 'client')
            assert hasattr(service, 'model')

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_call_llm_success(self, mock_llm_client):
        """测试成功的 LLM 调用"""
        mock_client_instance = Mock()
        mock_client_instance.chat.return_value = "AI 返回的结果"
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        messages = [{"role": "user", "content": "测试消息"}]
        result = service._call_llm(messages)

        assert result == "AI 返回的结果"
        mock_client_instance.chat.assert_called_once()

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_call_llm_failure(self, mock_llm_client):
        """测试失败的 LLM 调用"""
        mock_client_instance = Mock()
        mock_client_instance.chat.side_effect = Exception("API 错误")
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        messages = [{"role": "user", "content": "测试消息"}]

        with pytest.raises(Exception) as exc_info:
            service._call_llm(messages)

        assert "API 错误" in str(exc_info.value)

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_outline_from_idea_success(self, mock_llm_client):
        """测试从想法成功生成大纲"""
        mock_client_instance = Mock()
        mock_response = '''
        [
          {
            "title": "第一部分：AI概述",
            "pages": [
              {"title": "什么是AI", "description": "人工智能的定义和发展历程"},
              {"title": "AI的应用领域", "description": "介绍AI在各行业的应用"}
            ]
          },
          {
            "title": "第二部分：技术原理",
            "pages": [
              {"title": "机器学习基础", "description": "机器学习的基本概念和算法"}
            ]
          }
        ]
        '''
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        mock_project = Mock()
        mock_project.idea_prompt = "制作一个关于AI的PPT"
        mock_project.extra_requirements = None

        context = ProjectContext(mock_project)
        result = service.generate_outline_from_idea(context, "制作一个关于AI的PPT", language="zh")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "第一部分：AI概述"
        assert len(result[0]["pages"]) == 2

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_outline_with_json_in_text(self, mock_llm_client):
        """测试从包含额外文本的响应中提取JSON"""
        mock_client_instance = Mock()
        mock_response = '''
        这是生成的大纲内容：

        [
          {
            "title": "第一部分",
            "pages": [
              {"title": "页面1", "description": "描述1"}
            ]
          }
        ]

        希望这个大纲对您有帮助！
        '''
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        mock_project = Mock()
        mock_project.idea_prompt = "测试"
        mock_project.extra_requirements = None

        context = ProjectContext(mock_project)
        result = service.generate_outline_from_idea(context, "测试", language="zh")

        assert isinstance(result, list)
        assert len(result) == 1

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_page_description_success(self, mock_llm_client):
        """测试成功生成页面描述"""
        mock_client_instance = Mock()
        mock_response = '''
        # 页面标题

        本页面主要介绍以下内容：

        - 要点一：详细的说明和解释
        - 要点二：相关的技术细节
        - 要点三：实际应用案例

        建议使用图表展示数据分布情况。
        '''
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        mock_project = Mock()
        mock_project.idea_prompt = "测试项目"
        mock_project.extra_requirements = None

        context = ProjectContext(mock_project)
        outline = [{"title": "第一部分", "pages": [{"title": "页面1", "description": "描述"}]}]
        page_data = {"title": "页面1", "description": "描述"}

        result = service.generate_page_description(
            context, outline, page_data, 1, language="zh"
        )

        assert isinstance(result, str)
        assert "要点一" in result

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_image_prompt_success(self, mock_llm_client):
        """测试成功生成图片提示词"""
        mock_client_instance = Mock()
        mock_response = '''
        画面采用现代简约风格，以蓝色为主色调。

        布局建议：
        - 左侧放置标题和核心要点
        - 右侧使用图标和插图展示

        视觉元素：
        - 使用扁平化图标
        - 添加渐变背景
        '''
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        mock_project = Mock()
        mock_project.idea_prompt = "测试"
        mock_project.extra_requirements = None

        context = ProjectContext(mock_project)
        result = service.generate_image_prompt(
            context,
            "这是页面描述",
            "页面标题",
            "现代风格",
            language="zh"
        )

        assert isinstance(result, str)
        assert "蓝色" in result

    def test_extract_image_urls_from_markdown_with_urls(self):
        """测试从 Markdown 中提取图片URL"""
        with patch('app.services.ppt.ai_service.LLMClient'):
            service = AIService()

        text = """
        这是页面内容。

        ![图片1](https://example.com/image1.png)

        更多文字说明。

        ![图片2](https://example.com/image2.jpg)

        结尾。
        """

        urls = service.extract_image_urls_from_markdown(text)

        assert len(urls) == 2
        assert "https://example.com/image1.png" in urls
        assert "https://example.com/image2.jpg" in urls

    def test_extract_image_urls_from_markdown_without_urls(self):
        """测试从没有图片的 Markdown 中提取URL"""
        with patch('app.services.ppt.ai_service.LLMClient'):
            service = AIService()

        text = """
        这是普通文字内容，没有图片。

        - 列表项1
        - 列表项2

        **加粗文字**
        """

        urls = service.extract_image_urls_from_markdown(text)

        assert len(urls) == 0

    def test_extract_image_urls_from_empty_markdown(self):
        """测试从空 Markdown 中提取URL"""
        with patch('app.services.ppt.ai_service.LLMClient'):
            service = AIService()

        urls = service.extract_image_urls_from_markdown("")

        assert len(urls) == 0

    def test_extract_image_urls_with_special_characters(self):
        """测试提取包含特殊字符的图片URL"""
        with patch('app.services.ppt.ai_service.LLMClient'):
            service = AIService()

        text = "![图片](https://example.com/image-with-dashes_and_underscores.png?v=1&size=large)"

        urls = service.extract_image_urls_from_markdown(text)

        assert len(urls) == 1
        assert "image-with-dashes_and_underscores.png" in urls[0]

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_edit_prompt_success(self, mock_llm_client):
        """测试成功生成编辑提示词"""
        mock_client_instance = Mock()
        mock_response = '''
        编辑指导：
        1. 将背景颜色从白色改为浅蓝色
        2. 调整标题字体大小
        3. 保持原有的图标风格不变

        具体操作步骤：
        - 使用取色器选择浅蓝色
        - 调整字体大小到24pt
        '''
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        result = service.generate_edit_prompt(
            "/path/to/image.png",
            "把背景改成蓝色",
            "原始描述内容"
        )

        assert isinstance(result, str)
        assert "蓝色" in result

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_edit_prompt_without_original_description(self, mock_llm_client):
        """测试没有原始描述时生成编辑提示词"""
        mock_client_instance = Mock()
        mock_response = "根据您的编辑要求，建议修改以下内容..."
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        result = service.generate_edit_prompt(
            "/path/to/image.png",
            "简化设计"
        )

        assert isinstance(result, str)
        # 验证调用了 LLM
        mock_client_instance.chat.assert_called_once()


class TestAIServiceLanguageSupport:
    """测试 AIService 的多语言支持"""

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_outline_with_chinese_language(self, mock_llm_client):
        """测试生成中文大纲"""
        mock_client_instance = Mock()
        mock_response = '[{"title": "中文标题", "pages": []}]'
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        mock_project = Mock()
        context = ProjectContext(mock_project)

        result = service.generate_outline_from_idea(context, "测试", language="zh")

        # 验证返回结果
        assert isinstance(result, list)
        # 验证调用了 LLM
        mock_client_instance.chat.assert_called_once()

    @patch('app.services.ppt.ai_service.LLMClient')
    def test_generate_outline_with_english_language(self, mock_llm_client):
        """测试生成英文大纲"""
        mock_client_instance = Mock()
        mock_response = '[{"title": "English Title", "pages": []}]'
        mock_client_instance.chat.return_value = mock_response
        mock_llm_client.return_value = mock_client_instance

        service = AIService()
        mock_project = Mock()
        context = ProjectContext(mock_project)

        result = service.generate_outline_from_idea(context, "test", language="en")

        # 检查系统提示词包含英文说明
        call_args = mock_client_instance.chat.call_args
        messages = call_args[0][0]
        assert any("en" in str(msg) for msg in messages)
