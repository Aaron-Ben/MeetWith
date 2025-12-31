"""
AI 服务 - 处理PPT生成相关的AI调用
"""
import logging
import re
from typing import List, Dict, Any, Optional
from app.utils.llm_client import LLMClient
from app.config import Config

logger = logging.getLogger(__name__)


class ProjectContext:
    """项目上下文，包含参考文件等信息"""

    def __init__(self, project, reference_files_content: List[str] = None):
        self.project = project
        self.reference_files_content = reference_files_content or []

    def get_context_prompt(self) -> str:
        """生成上下文提示词"""
        context_parts = []

        # 添加项目基本信息
        if self.project.idea_prompt:
            context_parts.append(f"项目主题：{self.project.idea_prompt}")

        if self.project.extra_requirements:
            context_parts.append(f"额外要求：{self.project.extra_requirements}")

        # 添加参考文件内容
        if self.reference_files_content:
            context_parts.append("参考文件内容：")
            for idx, content in enumerate(self.reference_files_content, 1):
                if content:
                    context_parts.append(f"\n--- 参考文件 {idx} ---\n{content[:2000]}...\n")

        return "\n\n".join(context_parts) if context_parts else "无特定上下文"


class AIService:
    """AI PPT生成服务"""

    def __init__(self):
        self.client = LLMClient()
        self.model = Config.QWEN_MODEL

    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """调用LLM"""
        try:
            response = self.client.chat(messages, temperature=temperature)
            return response
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise

    def generate_outline_from_idea(
        self,
        project_context: ProjectContext,
        idea_prompt: str,
        language: str = "zh"
    ) -> List[Dict[str, Any]]:
        """
        从想法生成大纲

        Args:
            project_context: 项目上下文
            idea_prompt: 想法提示
            language: 语言

        Returns:
            大纲列表
        """
        system_prompt = f"""你是一个专业的PPT大纲设计助手。根据用户的想法生成一个结构清晰的PPT大纲。

请按照以下JSON格式返回大纲：
[
  {{
    "title": "第一部分标题",
    "pages": [
      {{"title": "页面1标题", "description": "简要描述"}},
      {{"title": "页面2标题", "description": "简要描述"}}
    ]
  }}
]

要求：
1. 大纲应该包含3-5个部分
2. 每个部分包含2-4个页面
3. 页面标题简洁明了
4. 描述要详细，为后续生成图片提供指导
5. 使用{language}语言
"""

        user_prompt = f"""请根据以下想法生成PPT大纲：

{idea_prompt}

{project_context.get_context_prompt()}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self._call_llm(messages, temperature=0.7)

        # 解析JSON响应
        try:
            # 提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                outline = eval(json_match.group())
            else:
                outline = eval(response)
            return outline
        except Exception as e:
            logger.error(f"解析大纲JSON失败: {str(e)}")
            raise ValueError(f"生成的大纲格式错误: {response}")

    def generate_page_description(
        self,
        project_context: ProjectContext,
        outline: List[Dict[str, Any]],
        page_data: Dict[str, Any],
        page_number: int,
        language: str = "zh"
    ) -> str:
        """
        生成页面描述

        Args:
            project_context: 项目上下文
            outline: 完整大纲
            page_data: 当前页面数据
            page_number: 页面编号
            language: 语言

        Returns:
            页面描述文本
        """
        system_prompt = f"""你是一个专业的PPT内容创作助手。为指定页面生成详细的内容描述。

描述应该包含：
1. 页面主要内容（3-5个要点）
2. 每个要点的详细说明
3. 适合视觉呈现的关键信息
4. 建议的图表或图示类型（如果适用）

使用{language}语言，内容要专业、清晰、有逻辑性。
"""

        # 构建大纲摘要
        outline_summary = "\n".join([
            f"- {part.get('title', '未命名部分')}" if 'title' in part else f"- {part.get('title', '页面')}"
            for part in outline[:5]
        ])

        user_prompt = f"""请为以下页面生成详细内容描述：

【页面信息】
页面编号：{page_number}
标题：{page_data.get('title', '未命名')}
简述：{page_data.get('description', '')}

【完整大纲】
{outline_summary}

【项目上下文】
{project_context.get_context_prompt()}

请生成详细的页面内容描述：
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._call_llm(messages, temperature=0.7)

    def generate_image_prompt(
        self,
        project_context: ProjectContext,
        page_description: str,
        page_title: str,
        template_style: str = None,
        language: str = "zh"
    ) -> str:
        """
        生成图片生成提示词

        Args:
            project_context: 项目上下文
            page_description: 页面描述
            page_title: 页面标题
            template_style: 模板样式描述
            language: 语言

        Returns:
            图片生成提示词
        """
        system_prompt = f"""你是一个专业的PPT视觉设计助手。根据页面内容生成适合AI图片生成的提示词。

提示词应该包含：
1. 画面构图和布局
2. 主要视觉元素
3. 配色建议
4. 文字排版建议
5. 图标或插图建议

提示词要具体、详细，能够指导AI生成高质量的PPT页面图片。
使用{language}语言。
"""

        user_prompt = f"""请为以下PPT页面生成图片设计提示词：

【页面标题】
{page_title}

【页面内容】
{page_description}

【模板样式】
{template_style or "现代简约风格"}

【项目要求】
{project_context.project.extra_requirements or "无"}

请生成详细的图片设计提示词：
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._call_llm(messages, temperature=0.8)

    def extract_image_urls_from_markdown(self, text: str) -> List[str]:
        """
        从markdown文本中提取图片URL

        Args:
            text: markdown文本

        Returns:
            图片URL列表
        """
        # 匹配 markdown 图片格式 ![alt](url)
        pattern = r'!\[.*?\]\((.*?)\)'
        urls = re.findall(pattern, text)
        return urls

    def generate_edit_prompt(
        self,
        current_image_path: str,
        edit_instruction: str,
        original_description: str = None
    ) -> str:
        """
        生成图片编辑提示词

        Args:
            current_image_path: 当前图片路径
            edit_instruction: 编辑指令
            original_description: 原始描述

        Returns:
            编辑提示词
        """
        system_prompt = """你是一个专业的PPT图片编辑助手。根据用户的编辑指令生成具体的编辑指导。

编辑指导应该：
1. 具体明确需要修改的内容
2. 保持与原图片风格一致
3. 提供可执行的修改建议
"""

        user_prompt = f"""请生成图片编辑指导：

【编辑指令】
{edit_instruction}

【原始描述】
{original_description or "无"}

请生成详细的编辑指导：
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._call_llm(messages, temperature=0.7)
