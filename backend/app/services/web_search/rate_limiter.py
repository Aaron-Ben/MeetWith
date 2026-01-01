"""
网络搜索限流器
"""
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.web_search import WebSearchUsage

logger = logging.getLogger(__name__)


class RateLimiter:
    """搜索限流器"""

    def __init__(self, daily_limit: int = None):
        """
        初始化限流器

        Args:
            daily_limit: 每日搜索限额，默认从环境变量读取
        """
        self.daily_limit = daily_limit or int(os.getenv("WEB_SEARCH_DAILY_LIMIT", "100"))
        logger.info(f"RateLimiter initialized with daily limit: {self.daily_limit}")

    def get_today_usage_count(self) -> int:
        """
        获取今日已使用次数

        Returns:
            今日使用次数
        """
        try:
            # 获取今日开始时间
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            db: Session = next(get_db())
            try:
                count = db.query(WebSearchUsage).filter(
                    WebSearchUsage.created_at >= today_start
                ).count()
                return count
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to get today usage: {e}", exc_info=True)
            # 出错时返回限额，防止继续使用
            return self.daily_limit

    def check_limit(self) -> tuple[bool, int]:
        """
        检查是否超过限额

        Returns:
            (是否可以搜索, 今日已使用次数)
        """
        try:
            used = self.get_today_usage_count()
            can_search = used < self.daily_limit

            if not can_search:
                logger.warning(f"Daily search limit reached: {used}/{self.daily_limit}")

            return can_search, used

        except Exception as e:
            logger.error(f"Failed to check limit: {e}", exc_info=True)
            # 出错时保守策略：允许搜索但记录日志
            return True, 0

    def record_usage(self, user_id: str, query: str, results_count: int) -> bool:
        """
        记录搜索使用

        Args:
            user_id: 用户ID
            query: 搜索查询
            results_count: 结果数量

        Returns:
            是否记录成功
        """
        try:
            db: Session = next(get_db())
            try:
                usage = WebSearchUsage(
                    user_id=user_id,
                    query=query[:500] if query else "",  # 限制查询长度
                    results_count=results_count
                )
                db.add(usage)
                db.commit()

                logger.info(f"Recorded search usage: user={user_id}, query='{query[:50]}...', results={results_count}")
                return True

            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to record usage: {e}", exc_info=True)
            return False

    def get_usage_stats(self) -> dict:
        """
        获取使用统计

        Returns:
            使用统计字典
        """
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            db: Session = next(get_db())
            try:
                # 今日使用次数
                today_count = db.query(WebSearchUsage).filter(
                    WebSearchUsage.created_at >= today_start
                ).count()

                # 今日不同用户数
                unique_users = db.query(WebSearchUsage.user_id).filter(
                    WebSearchUsage.created_at >= today_start
                ).distinct().count()

                return {
                    "used": today_count,
                    "limit": self.daily_limit,
                    "remaining": max(0, self.daily_limit - today_count),
                    "unique_users_today": unique_users,
                    "reset_at": (today_start + timedelta(days=1)).isoformat()
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}", exc_info=True)
            return {
                "used": 0,
                "limit": self.daily_limit,
                "remaining": self.daily_limit,
                "unique_users_today": 0,
                "reset_at": None,
                "error": str(e)
            }
