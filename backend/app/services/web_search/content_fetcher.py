"""
内容获取器 - 多级回退策略
Cache → Direct → Jina.ai → Archive.org
"""
import os
import logging
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
import trafilatura

from .content_cache import ContentCache, PageContent, get_content_cache
from .jina_fetcher import JinaFetcher
from .archive_fetcher import ArchiveFetcher

logger = logging.getLogger(__name__)


# 随机 User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


class ContentFetcher:
    """
    多级回退内容获取器

    回退链:
    1. Cache (LRU 缓存)
    2. Direct (trafilatura 直接获取)
    3. Jina.ai (Reader API)
    4. Archive.org (Wayback Machine)
    """

    def __init__(
        self,
        cache: Optional[ContentCache] = None,
        use_cache: bool = True,
        timeout: int = 5
    ):
        """
        初始化内容获取器

        Args:
            cache: 内容缓存实例
            use_cache: 是否使用缓存
            timeout: 直接获取的超时时间(秒)
        """
        self.cache = cache or get_content_cache()
        self.use_cache = use_cache
        self.timeout = timeout

        # 初始化备用获取器
        self.jina_fetcher = JinaFetcher()
        self.archive_fetcher = ArchiveFetcher()

        logger.info(
            f"ContentFetcher initialized: "
            f"use_cache={use_cache}, timeout={timeout}s"
        )

    async def fetch_page_content(
        self,
        url: str,
        force_refresh: bool = False
    ) -> Optional[PageContent]:
        """
        获取网页内容（多级回退）

        Args:
            url: 目标网页 URL
            force_refresh: 强制刷新，跳过缓存

        Returns:
            网页内容，失败返回 None
        """
        if not url:
            logger.warning("Empty URL provided")
            return None

        logger.info(f"Fetching page content: {url}")

        # Level 1: 检查缓存
        if self.use_cache and not force_refresh:
            cached = self.cache.get(url)
            if cached:
                logger.info(f"Cache hit: {url}")
                cached.source = "cache"
                return cached

        # Level 2: 直接获取 (trafilatura)
        content = await self._fetch_direct(url)
        if content:
            self._cache_result(url, content)
            return content

        # Level 3: Jina.ai 回退
        logger.info(f"Falling back to Jina.ai: {url}")
        content = await self._fetch_jina(url)
        if content:
            self._cache_result(url, content)
            return content

        # Level 4: Archive.org 回退
        logger.info(f"Falling back to Archive.org: {url}")
        content = await self._fetch_archive(url)
        if content:
            self._cache_result(url, content)
            return content

        logger.error(f"All fetch methods failed: {url}")
        return None

    async def _fetch_direct(self, url: str) -> Optional[PageContent]:
        """
        直接获取网页内容（使用 trafilatura）

        Args:
            url: 目标网页 URL

        Returns:
            网页内容，失败返回 None
        """
        try:
            logger.debug(f"Direct fetch: {url}")

            # 使用随机 User-Agent
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()

                # 使用 trafilatura 提取内容
                html = response.text
                downloaded = trafilatura.utils.load_html(html)

                title = trafilatura.extract_title(downloaded)
                content = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False
                )

                if content:
                    return PageContent(
                        url=url,
                        title=title or self._extract_title_from_html(html),
                        content=content,
                        fetched_at=datetime.now().isoformat(),
                        source="direct"
                    )

                logger.warning(f"Trafilatura extraction failed: {url}")
                return None

        except httpx.TimeoutException:
            logger.warning(f"Direct fetch timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"Direct fetch error: {e}", exc_info=True)
            return None

    async def _fetch_jina(self, url: str) -> Optional[PageContent]:
        """
        使用 Jina.ai Reader 获取内容

        Args:
            url: 目标网页 URL

        Returns:
            网页内容，失败返回 None
        """
        try:
            result = await self.jina_fetcher.fetch(url)
            if result:
                return PageContent(
                    url=url,
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    fetched_at=datetime.now().isoformat(),
                    source="jina"
                )
        except Exception as e:
            logger.error(f"Jina fetch error: {e}", exc_info=True)

        return None

    async def _fetch_archive(self, url: str) -> Optional[PageContent]:
        """
        使用 Archive.org 获取内容

        Args:
            url: 目标网页 URL

        Returns:
            网页内容，失败返回 None
        """
        try:
            result = await self.archive_fetcher.fetch(url)
            if result:
                return PageContent(
                    url=url,
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    fetched_at=datetime.now().isoformat(),
                    source="archive"
                )
        except Exception as e:
            logger.error(f"Archive fetch error: {e}", exc_info=True)

        return None

    def _cache_result(self, url: str, content: PageContent) -> None:
        """缓存结果"""
        if self.use_cache and content:
            self.cache.set(url, content)

    def _extract_title_from_html(self, html: str) -> str:
        """从 HTML 提取标题（备用方法）"""
        import re

        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        return "Untitled"

    async def batch_fetch(
        self,
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[Optional[PageContent]]:
        """
        批量获取网页内容

        Args:
            urls: URL 列表
            max_concurrent: 最大并发数

        Returns:
            内容列表（与输入顺序相同）
        """
        import asyncio

        results = []

        # 分批处理
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            tasks = [self.fetch_page_content(url) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()

    # ========== 同步包装器方法 ==========
    # 这些方法用于在同步上下文中调用异步方法

    def fetch_page_content_sync(self, url: str, force_refresh: bool = False) -> Optional[PageContent]:
        """
        同步版本的 fetch_page_content
        在新的事件循环中运行异步代码，避免与 uvloop 冲突
        """
        import asyncio
        import threading

        def run_in_new_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.fetch_page_content(url, force_refresh))
            finally:
                loop.close()

        # 在单独的线程中运行，避免事件循环冲突
        if threading.current_thread() is not threading.main_thread():
            return run_in_new_loop()
        else:
            # 主线程中使用 ThreadPoolExecutor
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()

    def batch_fetch_sync(self, urls: List[str], max_concurrent: int = 3) -> List[Optional[PageContent]]:
        """
        同步版本的 batch_fetch
        """
        import asyncio
        import threading

        def run_in_new_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.batch_fetch(urls, max_concurrent))
            finally:
                loop.close()

        if threading.current_thread() is not threading.main_thread():
            return run_in_new_loop()
        else:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()
