"""
Auto-generated from plugin: TavilySearch
Command: TavilySearch
Do not edit manually - regenerate with PluginManager.generate_tool_code()
"""

from typing import Dict, Any
from ..client import call_mcp_tool


async def tavily_search(query: str, topic: str = 'general', search_depth: str = 'basic', max_results: str = 5) -> Dict[str, Any]:
    """
使用 Tavily API 进行网络搜索。

参数:
    query: 搜索关键词
    topic: 搜索主题 ('general', 'news', 等)
    search_depth: 搜索深度 ('basic' 或 'advanced')
    max_results: 最大结果数

返回:
    包含搜索结果的 JSON 对象
"""

    # See plugin manifest for usage examples and VCP format

    # Build input parameters
    input_data = {
        'query': query,
        'topic': topic,
        'search_depth': search_depth,
        'max_results': max_results
    }

    # Call the underlying plugin via MCP client
    return await call_mcp_tool(
        tool_name='TavilySearch',
        input_data=input_data
    )
