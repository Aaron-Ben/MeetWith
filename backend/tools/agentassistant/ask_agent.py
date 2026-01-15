"""
Auto-generated from plugin: AgentAssistant
Command: AskAgent
Do not edit manually - regenerate with PluginManager.generate_tool_code()
"""

from typing import Dict, Any
from ..client import call_mcp_tool


async def ask_agent(agent_name: str, prompt: str) -> Dict[str, Any]:
    """
调用一个已配置的 AI Agent 进行咨询。

参数:
    agent_name: Agent 名称
    prompt: 发送给 Agent 的提示词

说明:
    每个 Agent 拥有独立的 5 轮临时对话记忆

返回:
    Agent 的回复内容
"""

    # See plugin manifest for usage examples and VCP format

    # Build input parameters
    input_data = {
        'agent_name': agent_name,
        'prompt': prompt
    }

    # Call the underlying plugin via MCP client
    return await call_mcp_tool(
        tool_name='AgentAssistant',
        input_data=input_data
    )
