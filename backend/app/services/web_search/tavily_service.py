"""
Tavily API 客户端服务
"""
import os
import logging
from typing import List, Dict, Optional
from tavily import TavilyClient
from app.config import Config

logger = logging.getLogger(__name__)


class TavilyService:
    """Tavily 搜索服务"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Tavily 客户端

        Args:
            api_key: Tavily API Key，如果为 None 则从配置读取
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not configured")

        try:
            self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            self.client = None

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        执行网络搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数 (1-10)
            search_depth: 搜索深度 ("basic" 或 "advanced")
            include_domains: 包含的域名列表
            exclude_domains: 排除的域名列表

        Returns:
            搜索结果列表
        """
        if not self.client:
            logger.error("Tavily client not initialized")
            return []

        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []

        try:
            # 限制 max_results 范围
            max_results = max(1, min(10, max_results))

            logger.info(f"Searching: query='{query}', max_results={max_results}, depth={search_depth}")

            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains
            )

            results = response.get("results", [])
            logger.info(f"Search completed: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return []

    def format_results_for_ai(self, results: List[Dict], query: str) -> str:
        """
        格式化搜索结果为 AI 可读格式

        Args:
            results: 搜索结果列表
            query: 原始查询

        Returns:
            格式化的文本
        """
        if not results:
            return f"No search results found for query: {query}"

        formatted = f"Search Query: {query}\n\n"
        formatted += f"Found {len(results)} results:\n\n"

        for i, result in enumerate(results, 1):
            title = result.get('title', 'N/A')
            url = result.get('url', 'N/A')
            content = result.get('content', '')
            score = result.get('score', 0)

            formatted += f"[{i}] {title}\n"
            formatted += f"URL: {url}\n"
            if score:
                formatted += f"Relevance Score: {score:.2f}\n"
            if content:
                # 限制内容长度
                content_preview = content[:500] + "..." if len(content) > 500 else content
                formatted += f"Content: {content_preview}\n"
            formatted += "\n"

        return formatted

    def format_results_for_user(self, results: List[Dict]) -> str:
        """
        格式化搜索结果为用户显示格式（带引用）

        Args:
            results: 搜索结果列表

        Returns:
            格式化的 HTML 文本
        """
        if not results:
            return "<p>未找到相关结果</p>"

        html = "<div class='search-results'>\n"

        for i, result in enumerate(results, 1):
            title = result.get('title', 'N/A')
            url = result.get('url', 'N/A')
            content = result.get('content', '')

            html += f"<div class='search-result-item'>\n"
            html += f"  <h3><a href='{url}' target='_blank' rel='noopener noreferrer'>{title}</a></h3>\n"

            if content:
                content_preview = content[:300] + "..." if len(content) > 300 else content
                html += f"  <p class='result-content'>{content_preview}</p>\n"

            html += f"  <p class='result-url'><a href='{url}' target='_blank' rel='noopener noreferrer'>{url}</a></p>\n"
            html += f"</div>\n"

        html += "</div>"
        return html

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.client is not None

    def get_answer(self, query: str, search_depth: str = "basic") -> Optional[str]:
        """
        使用 Tavily 的生成式搜索功能获取直接答案

        Args:
            query: 搜索查询
            search_depth: 搜索深度

        Returns:
            生成的答案
        """
        if not self.client:
            return None

        try:
            # Tavily SDK 使用 qna_search 方法进行问答搜索
            response = self.client.qna_search(
                query=query,
                search_depth=search_depth,
                max_results=5
            )
            return response  # qna_search 直接返回答案字符串
        except Exception as e:
            logger.error(f"Get answer failed: {e}", exc_info=True)
            return None
