"""
Web Search 搜索服务
"""
import logging
from typing import List, Dict, Optional
from .tavily_service import TavilyService
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class SearchService:
    """网络搜索服务"""

    def __init__(self):
        """初始化搜索服务"""
        self.tavily = TavilyService()
        self.rate_limiter = RateLimiter()

    def search(
        self,
        user_id: str,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict:
        """
        执行搜索（带限流检查）

        Args:
            user_id: 用户ID
            query: 搜索查询
            max_results: 最大结果数
            search_depth: 搜索深度
            include_domains: 包含的域名
            exclude_domains: 排除的域名

        Returns:
            搜索结果字典
        """
        # 检查限流
        can_search, used_count = self.rate_limiter.check_limit()
        if not can_search:
            logger.warning(f"Search limit exceeded for user {user_id}")
            return {
                "success": False,
                "error": "daily_limit_exceeded",
                "message": f"Daily search limit reached ({used_count}/{self.rate_limiter.daily_limit})",
                "usage": {
                    "used": used_count,
                    "limit": self.rate_limiter.daily_limit
                }
            }

        # 检查服务可用性
        if not self.tavily.is_available():
            logger.error("Tavily service not available")
            return {
                "success": False,
                "error": "service_unavailable",
                "message": "Search service is not configured properly"
            }

        # 执行搜索
        try:
            results = self.tavily.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains
            )

            # 记录使用
            self.rate_limiter.record_usage(user_id, query, len(results))

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "usage": {
                    "used": used_count + 1,
                    "limit": self.rate_limiter.daily_limit,
                    "remaining": self.rate_limiter.daily_limit - used_count - 1
                }
            }

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}", exc_info=True)
            return {
                "success": False,
                "error": "search_failed",
                "message": str(e)
            }

    def format_for_ai(self, results: List[Dict], query: str) -> str:
        """
        格式化结果为 AI 可读格式

        Args:
            results: 搜索结果
            query: 原始查询

        Returns:
            格式化文本
        """
        return self.tavily.format_results_for_ai(results, query)

    def get_answer(self, query: str, search_depth: str = "basic") -> Optional[str]:
        """
        获取 AI 生成的答案

        Args:
            query: 搜索查询
            search_depth: 搜索深度

        Returns:
            生成的答案
        """
        if not self.tavily.is_available():
            return None

        return self.tavily.get_answer(query, search_depth)

    def get_usage_stats(self) -> Dict:
        """
        获取使用统计

        Returns:
            使用统计字典
        """
        return self.rate_limiter.get_usage_stats()

    def check_availability(self) -> Dict:
        """
        检查服务可用性

        Returns:
            可用性信息
        """
        return {
            "tavily_available": self.tavily.is_available(),
            "daily_limit": self.rate_limiter.daily_limit
        }
