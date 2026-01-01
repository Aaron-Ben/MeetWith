"""
LRU 内容缓存服务
使用 TTL 缓存存储网页内容，减少重复获取
"""
import os
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from cachetools import TTLCache

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    """网页内容数据类"""
    url: str
    title: str
    content: str
    author: Optional[str] = None
    date: Optional[str] = None
    fetched_at: Optional[str] = None
    source: str = "unknown"  # 来源: cache, direct, jina, archive

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageContent":
        """从字典创建"""
        return cls(**data)


class ContentCache:
    """LRU 内容缓存"""

    def __init__(
        self,
        max_size: Optional[int] = None,
        ttl: Optional[int] = None
    ):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数，默认从环境变量读取 (500)
            ttl: 缓存过期时间(秒)，默认从环境变量读取 (3600)
        """
        self.max_size = max_size or int(os.getenv("CONTENT_CACHE_SIZE", "500"))
        self.ttl = ttl or int(os.getenv("CONTENT_CACHE_TTL", "3600"))

        self.cache: TTLCache[str, PageContent] = TTLCache(
            maxsize=self.max_size,
            ttl=self.ttl
        )

        logger.info(f"ContentCache initialized: max_size={self.max_size}, ttl={self.ttl}s")

    def _make_key(self, url: str) -> str:
        """
        生成缓存键

        Args:
            url: 网页 URL

        Returns:
            缓存键 (URL 的 hash)
        """
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[PageContent]:
        """
        从缓存获取内容

        Args:
            url: 网页 URL

        Returns:
            网页内容，如果不存在或已过期返回 None
        """
        key = self._make_key(url)

        if key in self.cache:
            content = self.cache[key]
            logger.debug(f"Cache hit: {url}")
            return content

        logger.debug(f"Cache miss: {url}")
        return None

    def set(self, url: str, content: PageContent) -> None:
        """
        存储内容到缓存

        Args:
            url: 网页 URL
            content: 网页内容
        """
        key = self._make_key(url)

        # 更新获取时间
        content.fetched_at = datetime.now().isoformat()

        self.cache[key] = content
        logger.debug(f"Cached: {url}")

    def has(self, url: str) -> bool:
        """
        检查 URL 是否已缓存

        Args:
            url: 网页 URL

        Returns:
            是否存在且未过期
        """
        key = self._make_key(url)
        return key in self.cache

    def delete(self, url: str) -> bool:
        """
        删除缓存

        Args:
            url: 网页 URL

        Returns:
            是否删除成功
        """
        key = self._make_key(url)

        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Deleted from cache: {url}")
            return True

        return False

    def clear(self) -> None:
        """清空所有缓存"""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "usage_percent": round(len(self.cache) / self.max_size * 100, 2) if self.max_size > 0 else 0
        }

    def warm_up(self, urls_and_contents: Dict[str, PageContent]) -> None:
        """
        预热缓存

        Args:
            urls_and_contents: URL 和内容的映射
        """
        for url, content in urls_and_contents.items():
            self.set(url, content)

        logger.info(f"Cache warmed up with {len(urls_and_contents)} entries")


# 全局单例
_global_cache: Optional[ContentCache] = None


def get_content_cache() -> ContentCache:
    """
    获取全局缓存实例

    Returns:
        ContentCache 单例
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = ContentCache()

    return _global_cache
