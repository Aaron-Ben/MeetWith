"""
Auto-generated from plugin: DailyNoteGet
Command: DailyNoteGetRequest
Do not edit manually - regenerate with PluginManager.generate_tool_code()
"""

from typing import Dict, Any
from ..client import call_mcp_tool


async def daily_note_get_request() -> Dict[str, Any]:
    """
获取所有角色的日记内容。

返回:
    JSON 格式的日记内容，键为角色名，值为日记内容
    示例: {"角色名1": "日记内容...", "角色名2": "日记内容..."}
"""

    # See plugin manifest for usage examples and VCP format

    # Build input parameters
    input_data = {
        # No parameters
    }

    # Call the underlying plugin via MCP client
    return await call_mcp_tool(
        tool_name='DailyNoteGet',
        input_data=input_data
    )
