"""
Web Search Agent 工具
"""
import logging
from typing import Optional, List
from app.services.agent.base_tool import BaseTool
from app.services.web_search import SearchService, ContentFetcher, ContentExtractor

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    网络搜索工具 - 用于获取实时信息
    """

    def get_description(self) -> str:
        return """WebSearch(query: str) -> str
执行网络搜索获取实时信息。

适用场景：
- 用户询问最新新闻、时事
- 用户询问实时数据（股票、天气等）
- 用户询问模型训练日期之后发生的事件
- 需要验证或补充信息时

参数：
- query: 搜索查询字符串

返回：搜索结果摘要
"""

    def __init__(self, user_id: str = "anonymous"):
        super().__init__()
        self.user_id = user_id
        self.search_service = SearchService()

    def run(self, query: str, max_results: int = 5) -> str:
        """
        执行搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            搜索结果摘要
        """
        if not query or not query.strip():
            return "错误：搜索查询不能为空"

        logger.info(f"WebSearchTool called with query: {query}")

        try:
            # 执行搜索
            result = self.search_service.search(
                user_id=self.user_id,
                query=query,
                max_results=max_results
            )

            if not result.get("success"):
                error = result.get("error", "")
                if error == "daily_limit_exceeded":
                    return "抱歉，今日搜索次数已达上限"
                else:
                    return f"搜索失败：{result.get('message', '未知错误')}"

            results = result.get("results", [])
            if not results:
                return f"未找到与'{query}'相关的结果"

            # 格式化为 AI 可读格式
            formatted = self.search_service.format_for_ai(results, query)

            logger.info(f"WebSearchTool returned {len(results)} results")
            return formatted

        except Exception as e:
            logger.error(f"WebSearchTool error: {e}", exc_info=True)
            return f"搜索出错：{str(e)}"


class WebSearchAnswerTool(BaseTool):
    """
    增强的网络搜索工具 - 使用多级回退获取网页内容 + AI 提取
    """

    def get_description(self) -> str:
        return """WebSearchAnswer(query: str) -> str
使用网络搜索获取相关信息，并智能提取关键内容。

适用场景：
- 需要最新信息的问题
- 事实性问题
- 需要验证或补充信息

参数：
- query: 问题或搜索查询

返回：搜索结果的详细摘要（AI 提取）
"""

    def __init__(self):
        super().__init__()
        self.search_service = SearchService()
        self.content_fetcher = ContentFetcher()
        self.content_extractor = ContentExtractor()
        self.user_id = "anonymous"

    def run(self, query: str) -> str:
        """
        获取答案 - 使用搜索结果 + 内容获取 + AI 提取

        Args:
            query: 搜索查询

        Returns:
            搜索结果摘要（增强版）
        """
        if not query or not query.strip():
            return "错误：查询不能为空"

        logger.info(f"WebSearchAnswerTool called with query: {query}")

        try:
            # 第一步：Tavily 搜索获取 URL 列表
            result = self.search_service.search(
                user_id=self.user_id,
                query=query,
                max_results=5,  # 获取 5 个结果
                search_depth="advanced"
            )

            if not result.get("success"):
                error = result.get("error", "")
                if error == "daily_limit_exceeded":
                    return "抱歉，今日搜索次数已达上限"
                else:
                    return f"搜索失败：{result.get('message', '未知错误')}"

            results = result.get("results", [])
            if not results:
                return f"未找到与'{query}'相关的结果"

            # 第二步：获取前 3 个结果的完整内容（多级回退）
            urls = [r.get("url") for r in results[:3] if r.get("url")]
            if not urls:
                return self.search_service.format_for_ai(results, query)

            logger.info(f"Fetching content from {len(urls)} URLs...")
            fetched_contents = []

            # 使用同步包装器方法
            page_contents = self.content_fetcher.batch_fetch_sync(urls, max_concurrent=2)

            # 第三步：AI 提取关键信息
            for i, page_content in enumerate(page_contents):
                if page_content is None:
                    continue

                try:
                    # 使用同步包装器方法
                    extracted = self.content_extractor.extract_content_sync(
                        page_content=page_content.content,
                        query=query,
                        url=page_content.url
                    )

                    if extracted:
                        fetched_contents.append({
                            "title": extracted.title,
                            "url": page_content.url,
                            "summary": extracted.summary,
                            "key_points": extracted.key_points,
                            "relevance": extracted.relevance_score,
                            "source": page_content.source
                        })
                        logger.info(f"Extracted content from {page_content.url}")
                except Exception as e:
                    logger.error(f"Extract failed for {page_content.url}: {e}")
                    continue

            # 第四步：格式化输出
            if not fetched_contents:
                # 如果 AI 提取失败，回退到原始搜索结果
                logger.warning("AI extraction failed, falling back to raw results")
                return self.search_service.format_for_ai(results, query)

            # 构建增强的摘要
            formatted = f"搜索查询: {query}\n\n"
            formatted += f"找到 {len(fetched_contents)} 个高质量结果:\n\n"

            for i, content in enumerate(fetched_contents, 1):
                formatted += f"[{i}] {content['title']}\n"
                formatted += f"来源: {content['url']}\n"
                formatted += f"相关性: {content['relevance']:.0%}\n"
                formatted += f"摘要:\n{content['summary']}\n\n"
                formatted += f"关键要点:\n"
                for point in content['key_points']:
                    formatted += f"  - {point}\n"
                formatted += "\n"

            logger.info(f"WebSearchAnswerTool returned {len(fetched_contents)} extracted results")
            return formatted

        except Exception as e:
            logger.error(f"WebSearchAnswerTool error: {e}", exc_info=True)
            return f"搜索出错：{str(e)}"
