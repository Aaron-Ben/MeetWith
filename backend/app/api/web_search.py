"""
Web Search API 路由
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.web_search import SearchService
from app.services.web_search.content_fetcher import ContentFetcher
from app.services.web_search.content_extractor import ContentExtractor

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


class FetchRequest(BaseModel):
    """获取网页内容请求"""
    url: str = Field(..., description="网页 URL")
    force_refresh: bool = Field(False, description="强制刷新，跳过缓存")


class ExtractRequest(BaseModel):
    """提取内容请求"""
    content: str = Field(..., min_length=1, description="网页内容")
    query: str = Field(..., min_length=1, description="用户查询")
    url: Optional[str] = Field(None, description="网页 URL")


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


# =============================== 内容获取端点 ===============================
@router.post("/fetch", response_class=JSONResponse)
async def fetch_page(request: FetchRequest):
    """
    获取网页内容（多级回退）

    POST /api/web-search/fetch

    使用多级回退策略获取网页内容：
    1. LRU 缓存
    2. 直接获取 (trafilatura)
    3. Jina.ai Reader
    4. Archive.org Wayback

    Request Body:
    ```json
    {
        "url": "https://example.com/article",
        "force_refresh": false
    }
    ```

    Response:
    ```json
    {
        "success": true,
        "url": "https://example.com/article",
        "title": "文章标题",
        "content": "文章内容...",
        "source": "direct",
        "fetched_at": "2026-01-01T12:00:00"
    }
    ```
    """
    try:
        fetcher = ContentFetcher()
        result = await fetcher.fetch_page_content(
            url=request.url,
            force_refresh=request.force_refresh
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch content from: {request.url}"
            )

        return {
            "success": True,
            "url": result.url,
            "title": result.title,
            "content": result.content,
            "author": result.author,
            "date": result.date,
            "source": result.source,
            "fetched_at": result.fetched_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fetch endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.post("/batch-fetch", response_class=JSONResponse)
async def batch_fetch_pages(
    urls: List[str] = Query(..., description="URL 列表"),
    max_concurrent: int = Query(3, ge=1, le=10, description="最大并发数")
):
    """
    批量获取网页内容

    POST /api/web-search/batch-fetch?urls=...&max_concurrent=3

    Args:
        urls: URL 列表（最多 10 个）
        max_concurrent: 最大并发数 (1-10)

    Response:
    ```json
    {
        "success": true,
        "results": [
            {
                "url": "https://example.com/1",
                "title": "标题1",
                "content": "内容1...",
                "source": "direct"
            },
            {
                "url": "https://example.com/2",
                "title": "标题2",
                "content": "内容2...",
                "source": "jina"
            }
        ],
        "total": 2,
        "succeeded": 2,
        "failed": 0
    }
    ```
    """
    try:
        if len(urls) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 URLs allowed per batch"
            )

        fetcher = ContentFetcher()
        results = await fetcher.batch_fetch(urls, max_concurrent=max_concurrent)

        succeeded = sum(1 for r in results if r is not None)
        failed = len(results) - succeeded

        return {
            "success": True,
            "results": [
                {
                    "url": r.url,
                    "title": r.title,
                    "content": r.content,
                    "source": r.source,
                    "fetched_at": r.fetched_at
                } if r else {
                    "url": urls[i],
                    "error": "Failed to fetch"
                }
                for i, r in enumerate(results)
            ],
            "total": len(results),
            "succeeded": succeeded,
            "failed": failed
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch fetch endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.post("/extract", response_class=JSONResponse)
async def extract_content(request: ExtractRequest):
    """
    使用 AI 从网页内容中提取关键信息

    POST /api/web-search/extract

    Request Body:
    ```json
    {
        "content": "网页原始内容...",
        "query": "用户查询",
        "url": "https://example.com/article"
    }
    ```

    Response:
    ```json
    {
        "success": true,
        "title": "文章标题",
        "summary": "2-3段摘要...",
        "key_points": ["要点1", "要点2", "要点3"],
        "relevance_score": 0.85,
        "confidence": 0.9
    }
    ```
    """
    try:
        extractor = ContentExtractor()
        result = await extractor.extract_content(
            page_content=request.content,
            query=request.query,
            url=request.url
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract content"
            )

        return {
            "success": True,
            **result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.get("/cache/stats", response_class=JSONResponse)
async def get_cache_stats():
    """
    获取内容缓存统计

    GET /api/web-search/cache/stats

    Response:
    ```json
    {
        "size": 50,
        "max_size": 500,
        "ttl": 3600,
        "usage_percent": 10.0
    }
    ```
    """
    try:
        from app.services.web_search.content_cache import get_content_cache
        cache = get_content_cache()
        return cache.get_stats()

    except Exception as e:
        logger.error(f"Cache stats endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@router.post("/cache/clear", response_class=JSONResponse)
async def clear_cache():
    """
    清空内容缓存

    POST /api/web-search/cache/clear

    Response:
    ```json
    {
        "success": true,
        "message": "Cache cleared successfully"
    }
    ```
    """
    try:
        from app.services.web_search.content_cache import get_content_cache
        cache = get_content_cache()
        cache.clear()

        return {
            "success": True,
            "message": "Cache cleared successfully"
        }

    except Exception as e:
        logger.error(f"Cache clear endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")
