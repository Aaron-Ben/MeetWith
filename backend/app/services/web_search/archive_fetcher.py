"""
Archive.org Wayback Machine 获取器
使用 Wayback Machine CDX API 获取网页历史快照
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class ArchiveFetcher:
    """Archive.org Wayback Machine 获取器"""

    CDX_API = "https://web.archive.org/web/timemap/json"
    WAYBACK_BASE = "https://web.archive.org/web"

    def __init__(self, timeout: int = 10):
        """
        初始化 Archive 获取器

        Args:
            timeout: 请求超时时间(秒)
        """
        self.timeout = timeout
        logger.info("ArchiveFetcher initialized")

    async def _find_snapshot(self, url: str) -> Optional[str]:
        """
        查找最新的网页快照

        Args:
            url: 目标网页 URL

        Returns:
            快照 URL，找不到返回 None
        """
        try:
            # CDX API 查询参数
            params = {
                "url": url,
                "matchType": "exact",
                "filter": ["statuscode:200", "mimetype:text/html"],
                "limit": 1,
                "last": "1"  # 获取最新的一条
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.CDX_API, params=params)
                response.raise_for_status()

                # CDX API 返回格式: [[timestamp, url, mime, status, ...], ...]
                data = response.json()

                if data and len(data) > 1:  # 第一行是字段名
                    # 获取最新快照的 URL
                    snapshot_info = data[1]
                    if len(snapshot_info) > 1:
                        return snapshot_info[1]

                return None

        except Exception as e:
            logger.error(f"Archive snapshot lookup failed: {e}", exc_info=True)
            return None

    async def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从 Wayback Machine 获取网页快照

        Args:
            url: 目标网页 URL

        Returns:
            包含 title 和 content 的字典，失败返回 None
        """
        if not url:
            logger.warning("Empty URL provided")
            return None

        try:
            # 查找快照
            snapshot_url = await self._find_snapshot(url)

            if not snapshot_url:
                logger.warning(f"No snapshot found: {url}")
                return None

            logger.info(f"Fetching from Wayback: {snapshot_url}")

            # 获取快照内容
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(snapshot_url, follow_redirects=True)
                response.raise_for_status()

                # 简单的 HTML 内容提取
                html = response.text

                # 提取标题
                title = self._extract_title(html) or url
                # 提取正文（简化版）
                content = self._extract_content(html)

                return {
                    "title": title,
                    "content": content,
                    "url": url,
                    "snapshot_url": snapshot_url,
                    "snapshot_date": self._extract_snapshot_date(snapshot_url),
                    "source": "archive"
                }

        except httpx.TimeoutException:
            logger.warning(f"Archive fetch timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"Archive fetch failed: {e}", exc_info=True)
            return None

    def _extract_title(self, html: str) -> Optional[str]:
        """从 HTML 提取标题"""
        import re

        # 尝试匹配 <title> 标签
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        return None

    def _extract_content(self, html: str) -> str:
        """从 HTML 提取正文内容（简化版）"""
        import re

        # 移除 script 和 style 标签
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)

        # 移除所有 HTML 标签
        text = re.sub(r'<[^>]+>', '\n', html)

        # 清理多余的空白
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        return text[:5000]  # 限制长度

    def _extract_snapshot_date(self, snapshot_url: str) -> Optional[str]:
        """从快照 URL 提取日期"""
        try:
            # Wayback URL 格式: https://web.archive.org/web/20240101120000/...
            match = re.search(r'/web/(\d{14})/', snapshot_url)
            if match:
                date_str = match.group(1)
                return datetime.strptime(date_str, "%Y%m%d%H%M%S").isoformat()
        except Exception:
            pass

        return None

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return True  # Wayback Machine 始终可用
