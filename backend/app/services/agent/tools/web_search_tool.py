"""
Web Search Agent 工具
"""
import logging
from typing import Optional
from app.services.agent.base_tool import BaseTool
from app.services.web_search import SearchService

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
    网络搜索答案工具 - 使用搜索结果获取信息
    """

    def get_description(self) -> str:
        return """WebSearchAnswer(query: str) -> str
使用网络搜索获取相关信息并返回摘要。

适用场景：
- 需要最新信息的问题
- 事实性问题
- 需要验证或补充信息

参数：
- query: 问题或搜索查询

返回：搜索结果的详细摘要
"""

    def __init__(self):
        super().__init__()
        self.search_service = SearchService()
        # 使用 anonymous 用户ID进行搜索
        self.user_id = "anonymous"

    def run(self, query: str) -> str:
        """
        获取答案 - 使用搜索结果而不是 Tavily 的 get_answer

        Args:
            query: 搜索查询

        Returns:
            搜索结果摘要
        """
        if not query or not query.strip():
            return "错误：查询不能为空"

        logger.info(f"WebSearchAnswerTool called with query: {query}")

        try:
            # 使用 search 方法获取详细结果
            result = self.search_service.search(
                user_id=self.user_id,
                query=query,
                max_results=10,  # 获取更多结果
                search_depth="advanced"  # 使用深度搜索
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

            logger.info(f"WebSearchAnswerTool returned {len(results)} results, {len(formatted)} chars")
            return formatted

        except Exception as e:
            logger.error(f"WebSearchAnswerTool error: {e}", exc_info=True)
            return f"搜索出错：{str(e)}"
