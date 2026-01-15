"""
Auto-generated from plugin: UrlFetch
Command: UrlFetch
Do not edit manually - regenerate with PluginManager.generate_tool_code()
"""

from typing import Dict, Any
from ..client import call_mcp_tool


async def url_fetch(url: str) -> Dict[str, Any]:
    """
获取指定 URL 的网页内容。

参数:
    url: 目标网页 URL

返回:
    包含网页文本内容的 JSON 对象
"""

    # See plugin manifest for usage examples and VCP format

    # Build input parameters
    input_data = {
        'url': url
    }

    # Call the underlying plugin via MCP client
    return await call_mcp_tool(
        tool_name='UrlFetch',
        input_data=input_data
    )
