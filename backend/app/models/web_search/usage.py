"""
Web Search 使用记录模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from app.models.database import Base


class WebSearchUsage(Base):
    """网络搜索使用记录"""
    __tablename__ = "web_search_usage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    query = Column(Text, nullable=False)
    results_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 复合索引用于查询今日使用量
    __table_args__ = (
        Index('idx_web_search_created_at', 'created_at'),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query': self.query,
            'results_count': self.results_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
