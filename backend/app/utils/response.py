"""
统一响应处理工具
"""

from fastapi.responses import JSONResponse
from typing import Any, Optional

from sqlalchemy import JSON

def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> JSONResponse:
    """
    统一成功响应
    
    Args:
        data: 业务数据（任意类型，默认空对象）
        message: 成功提示信息（默认"Success"）
        status_code: HTTP状态码（默认200）
    
    Returns:
        JSONResponse: 标准化成功响应
    """
    response_data = {
        "message": message,
        "data": data
    }

    return JSONResponse(
        content=response_data,
        status_code=status_code
    )


def error_response(
    message: str = "Error",
    data: Any = None,
    status_code: int = 400
) -> JSONResponse:

    """
    统一错误响应
    
    Args:
        message: 错误提示信息（默认"Error"）
        data: Any = None,
        status_code: int = 400
    
    Returns:
        JSONResponse: 标准化错误响应
    """

    response_data = {
        "message": message,
        "data": data
    }

    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

def bad_request_response(
    message: str = "参数缺失",
    data: Any = None,
    status_code: int = 400
) -> JSONResponse:
    return error_response(message=message, data=data, status_code=status_code)
