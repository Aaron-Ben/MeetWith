"""
Auto-generated from plugin: DailyNoteWrite
Command: DailyNoteWriteRequest
Do not edit manually - regenerate with PluginManager.generate_tool_code()
"""

from typing import Dict, Any
from ..client import call_mcp_tool


async def daily_note_write_request(maidName: str, dateString: str, contentText: str) -> Dict[str, Any]:
    """
为指定角色写入日记内容。

参数:
    maidName: 角色名称
    dateString: 日期字符串
    contentText: 日记内容

返回:
    写入结果
"""

    # See plugin manifest for usage examples and VCP format

    # Build input parameters
    input_data = {
        'maidName': maidName,
        'dateString': dateString,
        'contentText': contentText
    }

    # Call the underlying plugin via MCP client
    return await call_mcp_tool(
        tool_name='DailyNoteWrite',
        input_data=input_data
    )
