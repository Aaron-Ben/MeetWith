"""
Web Search API 路由
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.web_search import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web-search", tags=["Web Search"])


# =============================== Pydantic 模型 ===============================
class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    max_results: int = Field(5, ge=1, le=10, description="最大结果数")
    search_depth: str = Field("basic", pattern="^(basic|advanced)$", description="搜索深度")
    include_domains: Optional[List[str]] = Field(None, description="包含的域名列表")
    exclude_domains: Optional[List[str]] = Field(None, description="排除的域名列表")
    user_id: str = Field(..., description="用户ID")


class AnswerRequest(BaseModel):
    """获取答案请求"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    search_depth: str = Field("basic", pattern="^(basic|advanced)$", description="搜索深度")


# =============================== 工具函数 ===============================
def get_default_user_id() -> str:
    """获取默认用户ID（生产环境应从认证中获取）"""
    return "anonymous"


# =============================== API 端点 ===============================
@router.post("/search", response_class=JSONResponse)
async def search(request: SearchRequest):
    """
    执行网络搜索

    POST /api/web-search/search

    Request Body:
    ```json
    {
        "query": "搜索内容",
        "max_results": 5,
        "search_depth": "basic",
        "include_domains": ["wikipedia.org"],
        "exclude_domains": ["spam.com"],
        "user_id": "user-123"
    }
    ```

    Response:
    ```json
    {
        "success": true,
        "query": "搜索内容",
        "results": [...],
        "count": 5,
        "usage": {
            "used": 10,
            "limit": 100,
            "remaining": 90
        }
    }
    ```
    """
    try:
        service = SearchService()

        result = service.search(
            user_id=request.user_id,
            query=request.query,
            max_results=request.max_results,
            search_depth=request.search_depth,
            include_domains=request.include_domains,
            exclude_domains=request.exclude_domains
        )

        if not result.get("success"):
            error_code = result.get("error", "unknown_error")
            if error_code == "daily_limit_exceeded":
                raise HTTPException(status_code=429, detail=result.get("message"))
            elif error_code == "service_unavailable":
                raise HTTPException(status_code=503, detail=result.get("message"))
            else:
                raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.post("/answer", response_class=JSONResponse)
async def get_answer(request: AnswerRequest):
    """
    获取 AI 生成的搜索答案

    POST /api/web-search/answer

    Request Body:
    ```json
    {
        "query": "What is Python?",
        "search_depth": "basic"
    }
    ```

    Response:
    ```json
    {
        "success": true,
        "answer": "生成的答案内容..."
    }
    ```
    """
    try:
        service = SearchService()

        answer = service.get_answer(request.query, request.search_depth)

        if answer is None:
            raise HTTPException(
                status_code=503,
                detail="Search service is not available"
            )

        return {
            "success": True,
            "query": request.query,
            "answer": answer
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.get("/usage", response_class=JSONResponse)
async def get_usage():
    """
    获取搜索使用统计

    GET /api/web-search/usage

    Response:
    ```json
    {
        "used": 10,
        "limit": 100,
        "remaining": 90,
        "unique_users_today": 3,
        "reset_at": "2026-01-02T00:00:00"
    }
    ```
    """
    try:
        service = SearchService()
        stats = service.get_usage_stats()
        return stats

    except Exception as e:
        logger.error(f"Usage endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.get("/check-limit", response_class=JSONResponse)
async def check_limit():
    """
    检查限流状态

    GET /api/web-search/check-limit

    Response:
    ```json
    {
        "can_search": true,
        "used": 10,
        "limit": 100,
        "remaining": 90
    }
    ```
    """
    try:
        service = SearchService()
        can_search, used_count = service.rate_limiter.check_limit()

        return {
            "can_search": can_search,
            "used": used_count,
            "limit": service.rate_limiter.daily_limit,
            "remaining": max(0, service.rate_limiter.daily_limit - used_count)
        }

    except Exception as e:
        logger.error(f"Check limit endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.get("/status", response_class=JSONResponse)
async def get_status():
    """
    获取服务状态

    GET /api/web-search/status

    Response:
    ```json
    {
        "tavily_available": true,
        "daily_limit": 100,
        "enabled": true
    }
    ```
    """
    try:
        service = SearchService()
        availability = service.check_availability()

        import os
        enabled = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"

        return {
            **availability,
            "enabled": enabled
        }

    except Exception as e:
        logger.error(f"Status endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")
