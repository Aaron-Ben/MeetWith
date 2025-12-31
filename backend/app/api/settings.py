"""
设置相关 API
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.database import get_db

logger = logging.getLogger(__name__)

settings_router = APIRouter(prefix="/api", tags=["Settings"])


# ------------------------------ Pydantic 模型 ------------------------------
class SettingsResponse(BaseModel):
    """设置响应"""
    language: str


class SettingsUpdateRequest(BaseModel):
    """设置更新请求"""
    language: Optional[str] = None


# ------------------------------ 简单内存存储 ------------------------------
# 注意：生产环境应该使用数据库存储设置
_settings_store = {
    "language": "zh"  # 默认中文
}


# ------------------------------ 设置接口 ------------------------------
@settings_router.get("/output-language", response_class=JSONResponse)
async def get_output_language():
    """
    获取输出语言设置
    GET /api/output-language
    """
    return {
        "success": True,
        "data": {
            "language": _settings_store.get("language", "zh")
        }
    }


@settings_router.get("/settings", response_class=JSONResponse)
async def get_settings():
    """
    获取所有设置
    GET /api/settings
    """
    return {
        "success": True,
        "data": {
            "id": "default",
            "language": _settings_store.get("language", "zh"),
        }
    }


@settings_router.put("/settings", response_class=JSONResponse)
async def update_settings(request_data: SettingsUpdateRequest):
    """
    更新设置
    PUT /api/settings
    """
    if request_data.language is not None:
        if request_data.language not in ["zh", "en"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid language. Must be 'zh' or 'en'"
            )
        _settings_store["language"] = request_data.language

    return {
        "success": True,
        "data": {
            "id": "default",
            "language": _settings_store.get("language", "zh"),
        },
        "message": "设置更新成功"
    }
