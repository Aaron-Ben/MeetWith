"""
Agent 服务 - 管理工具调用和 AI 对话
"""
import json
import logging
import re
from datetime import datetime
from typing import List, Dict
from app.utils.llm_client import LLMClient
from app.services.agent import BaseTool, WebSearchTool, WebSearchAnswerTool
from app.config import Config

logger = logging.getLogger(__name__)


# 当前年份
CURRENT_YEAR = datetime.now().year


class AgentService:
    """
    Agent 服务 - 支持工具调用的 AI 对话
    """

    def __init__(self, user_id: str = "anonymous"):
        """
        初始化 Agent 服务

        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.llm_client = LLMClient()
        self.tools = self._init_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.web_search_tool = None
        self.web_answer_tool = None

        # 缓存工具引用
        for tool in self.tools:
            if isinstance(tool, WebSearchTool):
                self.web_search_tool = tool
            elif isinstance(tool, WebSearchAnswerTool):
                self.web_answer_tool = tool

    def _init_tools(self) -> List[BaseTool]:
        """初始化可用工具"""
        tools = []

        # 添加网络搜索工具（如果启用）
        if Config.WEB_SEARCH_ENABLED:
            tools.append(WebSearchTool(user_id=self.user_id))
            tools.append(WebSearchAnswerTool())
            logger.info("WebSearch tools enabled")

        return tools

    def _should_search(self, query: str) -> tuple[bool, str]:
        """
        判断是否需要使用网络搜索

        策略：使用关键词匹配

        Args:
            query: 用户查询

        Returns:
            (是否需要搜索, 搜索查询词)
        """
        # 所有需要搜索的关键词
        search_keywords = [
            # 时间相关
            "最新", "今天", "昨天", "今年", "去年", "现在", "当前", "最近", "目前",
            str(CURRENT_YEAR), str(CURRENT_YEAR - 1), "2024", "2025", "2026", "2027",
            "本周", "上周", "本月", "上月",
            # 实时信息
            "价格", "股价", "汇率", "天气", "比分", "战况", "实时",
            "新闻", "消息", "发布会", "刚刚", "突发",
            # 体育/竞赛相关
            "冠军", "排名", "战绩", "夺冠", "世界杯", "奥运会", "nba", "cba",
            # 技术相关
            "最新版", "更新", "发布", "版本",
            # 数量/事实相关
            "几次", "多少次", "几回", "次数", "谁赢了", "谁是",
            # 询问事实
            "发生了什么", "怎么了", "结果如何", "怎么样了",
        ]

        query_lower = query.lower()

        for keyword in search_keywords:
            if keyword in query or keyword.lower() in query_lower:
                logger.info(f"Matched keyword: {keyword} in query: {query[:50]}...")
                return True, query

        return False, ""

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """
        聊天对话（支持智能网络搜索）

        Args:
            messages: 消息历史
            temperature: 温度参数

        Returns:
            响应文本
        """
        # 如果没有工具，直接调用 LLM
        if not self.tools:
            return self.llm_client.chat(messages, temperature)

        # 获取最后一条用户消息
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break

        if not last_user_message:
            return self.llm_client.chat(messages, temperature)

        # 判断是否需要搜索
        should_search, search_query = self._should_search(last_user_message)

        if should_search and self.web_answer_tool:
            logger.info(f"Query '{last_user_message}' triggers web search")

            # 使用网络搜索获取信息
            try:
                search_result = self.web_answer_tool.run(search_query)

                # 如果搜索结果为空或失败，回退到普通回答
                if not search_result or len(search_result) < 50:
                    logger.warning(f"Search result too short or empty: {len(search_result) if search_result else 0} chars")
                    return self.llm_client.chat(messages, temperature)

                logger.info(f"Got search result: {len(search_result)} chars")

                # 构建增强消息，包含搜索结果
                enhanced_messages = [
                    {
                        "role": "system",
                        "content": f"""你是AI助手。当前是 {CURRENT_YEAR} 年。

【重要】用户的问题需要最新信息。我刚刚从网络上搜索了相关信息，请务必基于以下搜索结果回答：

========== 网络搜索结果 ==========
{search_result}
========== 搜索结果结束 ==========

回答要求：
1. 必须优先使用搜索结果中的信息
2. 搜索结果中有明确数字或事实的，直接引用
3. 如果搜索结果不完整，可以用你的知识补充，但必须明确说明
4. 回答时要具体，不要模糊

现在请基于上述搜索结果回答用户的问题。"""
                    },
                    *messages
                ]

                return self.llm_client.chat(enhanced_messages, temperature)

            except Exception as e:
                logger.error(f"Web search failed: {e}", exc_info=True)
                # 搜索失败，回退到普通回答

        # 不需要搜索或搜索失败，使用普通对话
        return self.llm_client.chat(messages, temperature)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ):
        """
        流式聊天（简化版，不支持工具调用）

        Args:
            messages: 消息历史
            temperature: 温度参数

        Yields:
            响应片段
        """
        # 流式响应暂不支持工具调用
        for chunk in self.llm_client.chat_stream(messages, temperature):
            yield chunk

    def get_available_tools(self) -> List[Dict[str, str]]:
        """获取可用工具列表"""
        return [tool.to_dict() for tool in self.tools]
