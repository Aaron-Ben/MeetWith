"""
AI 内容提取器
使用 LLM 从网页内容中智能提取关键信息
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import json
import re

from app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContent:
    """提取的内容"""
    title: str
    summary: str  # 2-3段摘要
    key_points: List[str]  # 要点列表
    relevance_score: float  # 相关性评分 (0-1)
    confidence: float  # 置信度 (0-1)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedContent":
        """从字典创建"""
        return cls(**data)


class ContentExtractor:
    """
    AI 驱动的内容提取器

    使用 LLM 从网页内容中提取:
    - 标题
    - 摘要
    - 关键要点
    - 相关性评分
    """

    def __init__(self):
        """初始化提取器"""
        self.client = LLMClient()
        self.max_input_length = 10000  # 最大输入字符数
        self.temperature = 0.2  # 低温度保证稳定性

        logger.info("ContentExtractor initialized")

    async def extract_content(
        self,
        page_content: str,
        query: str,
        url: Optional[str] = None
    ) -> Optional[ExtractedContent]:
        """
        从网页内容中提取关键信息

        Args:
            page_content: 网页原始内容
            query: 用户查询
            url: 网页 URL (可选)

        Returns:
            提取的内容，失败返回 None
        """
        if not page_content or not query:
            logger.warning("Empty content or query provided")
            return None

        try:
            # 截断内容以避免超出模型限制
            content = self._truncate_content(page_content)

            logger.info(
                f"Extracting content from: {url or 'unknown'} "
                f"(content length: {len(content)})"
            )

            system_prompt = """你是一个专业的内容分析助手。你的任务是从网页内容中提取关键信息，并根据用户的查询判断相关性。

请严格按照以下 JSON 格式返回结果：
{
  "title": "页面标题",
  "summary": "2-3段摘要，每段不超过100字",
  "key_points": ["要点1", "要点2", "要点3", "要点4"],
  "relevance_score": 0.85,
  "confidence": 0.9
}

要求：
1. title: 提取或总结一个简洁的标题
2. summary: 提供内容的核心摘要，包含最重要的信息
3. key_points: 提取4-6个关键要点，每个要点不超过30字
4. relevance_score: 根据用户查询评估内容相关性 (0.0-1.0)
5. confidence: 你对提取结果的置信度 (0.0-1.0)

只返回 JSON，不要包含其他文字。"""

            user_prompt = f"""请从以下网页内容中提取关键信息：

【网页 URL】
{url or "未知"}

【用户查询】
{query}

【网页内容】
{content}

请提取并返回 JSON 格式的结果。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self.client.chat(
                messages=messages,
                temperature=self.temperature,
                max_tokens=1000
            )

            # 解析 JSON 响应
            result = self._parse_json_response(response)

            if result:
                # 验证必需字段
                if not all(k in result for k in ["title", "summary", "key_points", "relevance_score", "confidence"]):
                    logger.warning(f"Missing required fields in extraction result")
                    # 补充缺失字段
                    result.setdefault("title", "未知标题")
                    result.setdefault("summary", content[:200] + "...")
                    result.setdefault("key_points", [content[:100] + "..."])
                    result.setdefault("relevance_score", 0.5)
                    result.setdefault("confidence", 0.5)

                return ExtractedContent(
                    title=result["title"],
                    summary=result["summary"],
                    key_points=result["key_points"],
                    relevance_score=float(result["relevance_score"]),
                    confidence=float(result["confidence"])
                )

            logger.error("Failed to parse extraction result as JSON")
            return None

        except Exception as e:
            logger.error(f"Content extraction failed: {e}", exc_info=True)
            return None

    async def batch_extract(
        self,
        contents_and_queries: List[tuple[str, str]],
        urls: Optional[List[Optional[str]]] = None
    ) -> List[Optional[ExtractedContent]]:
        """
        批量提取内容

        Args:
            contents_and_queries: (content, query) 元组列表
            urls: 对应的 URL 列表

        Returns:
            提取结果列表
        """
        results = []

        for i, (content, query) in enumerate(contents_and_queries):
            url = urls[i] if urls and i < len(urls) else None
            result = await self.extract_content(content, query, url)
            results.append(result)

        return results

    def _truncate_content(self, content: str) -> str:
        """截断内容到最大长度"""
        if len(content) <= self.max_input_length:
            return content

        # 截断并添加省略标记
        return content[:self.max_input_length - 100] + "\n\n...(内容已截断)"

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析 JSON 响应

        Args:
            response: LLM 返回的文本

        Returns:
            解析后的字典，失败返回 None
        """
        if not response:
            return None

        # 清理响应文本
        response = response.strip()

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取花括号内容
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        logger.error(f"Failed to parse JSON from response: {response[:200]}")
        return None

    def format_for_ai(self, extracted: ExtractedContent, url: Optional[str] = None) -> str:
        """
        格式化提取结果为 AI 可读格式

        Args:
            extracted: 提取的内容
            url: 原始 URL

        Returns:
            格式化的文本
        """
        formatted = f"Title: {extracted.title}\n"

        if url:
            formatted += f"URL: {url}\n"

        formatted += f"Relevance: {extracted.relevance_score:.2f}\n"
        formatted += f"Confidence: {extracted.confidence:.2f}\n\n"
        formatted += f"Summary:\n{extracted.summary}\n\n"
        formatted += "Key Points:\n"

        for i, point in enumerate(extracted.key_points, 1):
            formatted += f"{i}. {point}\n"

        return formatted

    def format_for_user(self, extracted: ExtractedContent, url: Optional[str] = None) -> str:
        """
        格式化提取结果为用户显示格式

        Args:
            extracted: 提取的内容
            url: 原始 URL

        Returns:
            格式化的 HTML
        """
        html = '<div class="extracted-content">\n'

        # 标题
        html += f'<h3 class="extracted-title">{extracted.title}</h3>\n'

        if url:
            html += f'<p class="extracted-url"><a href="{url}" target="_blank" rel="noopener">{url}</a></p>\n'

        # 摘要
        html += '<div class="extracted-summary">\n'
        for paragraph in extracted.summary.split('\n'):
            if paragraph.strip():
                html += f'<p>{paragraph}</p>\n'
        html += '</div>\n'

        # 关键要点
        html += '<ul class="extracted-points">\n'
        for point in extracted.key_points:
            html += f'<li>{point}</li>\n'
        html += '</ul>\n'

        html += '</div>'
        return html

    # ========== 同步包装器方法 ==========
    # 这些方法用于在同步上下文中调用异步方法

    def extract_content_sync(
        self,
        page_content: str,
        query: str,
        url: Optional[str] = None
    ) -> Optional[ExtractedContent]:
        """
        同步版本的 extract_content
        在新的事件循环中运行异步代码，避免与 uvloop 冲突
        """
        import asyncio
        import threading

        def run_in_new_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.extract_content(page_content, query, url))
            finally:
                loop.close()

        if threading.current_thread() is not threading.main_thread():
            return run_in_new_loop()
        else:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()
