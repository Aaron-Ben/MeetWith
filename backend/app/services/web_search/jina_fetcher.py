"""
Jina.ai Reader API 获取器
使用 Jina.ai Reader API 绕过机器人检测和 JS 渲染
"""
import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class JinaFetcher:
    """Jina.ai Reader API 获取器"""

    BASE_URL = "https://r.jina.ai/http://"

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Jina.ai 获取器

        Args:
            api_key: Jina API Key (可选，免费版不需要)
        """
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.timeout = int(os.getenv("JINA_TIMEOUT", "10"))

        # 如果有 API Key，使用付费版 API
        if self.api_key:
            self.base_url = "https://r.jina.ai/"
            self.headers = {"Authorization": f"Bearer {self.api_key}"}
        else:
            self.base_url = self.BASE_URL
            self.headers = {}

        logger.info(f"JinaFetcher initialized (api_key_configured={bool(self.api_key)})")

    async def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        """
        使用 Jina.ai Reader 获取网页内容

        Args:
            url: 目标网页 URL

        Returns:
            包含 title 和 content 的字典，失败返回 None
        """
        if not url:
            logger.warning("Empty URL provided")
            return None

        try:
            # 构建请求 URL
            encoded_url = url.replace("https://", "").replace("http://", "")
            request_url = f"{self.base_url}{encoded_url}"

            logger.info(f"Fetching with Jina: {url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    request_url,
                    headers=self.headers,
                    follow_redirects=True
                )
                response.raise_for_status()

                # Jina.ai 返回 Markdown 格式的文本
                content = response.text

                # 尝试从内容中提取标题（第一行通常是标题）
                lines = content.strip().split("\n")
                title = lines[0].strip("#").strip() if lines else url
                full_content = "\n".join(lines[1:]) if len(lines) > 1 else content

                return {
                    "title": title,
                    "content": full_content.strip(),
                    "url": url,
                    "source": "jina"
                }

        except httpx.TimeoutException:
            logger.warning(f"Jina fetch timeout: {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"Jina fetch HTTP error {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"Jina fetch failed: {e}", exc_info=True)
            return None

    def is_available(self) -> bool:
        """
        检查服务是否可用

        Returns:
            是否可用
        """
        return True  # Jina.ai 免费版始终可用
