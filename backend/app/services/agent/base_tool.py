"""
Agent 工具基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Agent 工具基类"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.get_description()

    @abstractmethod
    def get_description(self) -> str:
        """获取工具描述，用于 AI 理解工具用途"""
        pass

    @abstractmethod
    def run(self, **kwargs) -> str:
        """执行工具"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于提示词"""
        return {
            "name": self.name,
            "description": self.description
        }
