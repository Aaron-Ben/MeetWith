"""
Auto-generated from plugin: DailyNoteEditor
Command: EditDailyNote
Do not edit manually - regenerate with PluginManager.generate_tool_code()
"""

from typing import Dict, Any
from ..client import call_mcp_tool


async def edit_daily_note(target: str, replace: str) -> Dict[str, Any]:
    """
编辑指定角色的日记内容，通过查找并替换旧内容来实现。

参数:
    target: 要查找并替换的旧内容（最少 15 字符）
    replace: 新的内容

安全性:
    - target 字段长度不能少于 15 字符
    - 一次调用只能修改一个日记文件中的匹配内容

返回:
    编辑结果
"""

    # See plugin manifest for usage examples and VCP format

    # Build input parameters
    input_data = {
        'target': target,
        'replace': replace
    }

    # Call the underlying plugin via MCP client
    return await call_mcp_tool(
        tool_name='DailyNoteEditor',
        input_data=input_data
    )
