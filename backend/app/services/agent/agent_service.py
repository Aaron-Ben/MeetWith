"""
Agent 服务 - 管理 AI 对话
"""
import logging
from typing import List, Dict
from app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AgentService:
    """
    Agent 服务 - AI 对话
    """

    def __init__(self, user_id: str = "anonymous"):
        """
        初始化 Agent 服务

        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.llm_client = LLMClient()

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """
        聊天对话

        Args:
            messages: 消息历史
            temperature: 温度参数

        Returns:
            响应文本
        """
        return self.llm_client.chat(messages, temperature)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ):
        """
        流式聊天

        Args:
            messages: 消息历史
            temperature: 温度参数

        Yields:
            响应片段
        """
        for chunk in self.llm_client.chat_stream(messages, temperature):
            yield chunk

    def get_available_tools(self) -> List[Dict[str, str]]:
        """获取可用工具列表"""
        return []
