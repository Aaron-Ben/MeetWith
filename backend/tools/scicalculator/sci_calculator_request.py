"""
Auto-generated from plugin: SciCalculator
Command: SciCalculatorRequest
Do not edit manually - regenerate with PluginManager.generate_tool_code()
"""

from typing import Dict, Any
from ..client import call_mcp_tool


async def sci_calculator_request(expression: str) -> Dict[str, Any]:
    """
科学计算器，支持数学运算、统计函数和微积分。

参数:
    expression: 数学表达式字符串

支持功能:
    基础运算: +, -, *, /, //, %, **
    常量: pi, e
    数学函数: sin, cos, tan, sqrt, log, exp, abs 等
    统计函数: mean, median, variance, stdev 等
    微积分: integral(), error_propagation(), confidence_interval()

返回:
    计算结果
"""

    # See plugin manifest for usage examples and VCP format

    # Build input parameters
    input_data = {
        'expression': expression
    }

    # Call the underlying plugin via MCP client
    return await call_mcp_tool(
        tool_name='SciCalculator',
        input_data=input_data
    )
