"""
页面图片版本模型 - 支持图片版本管理
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base


class PageImageVersion(Base):
    """页面图片版本模型"""

    __tablename__ = 'page_image_versions'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='版本ID（UUID）'
    )

    page_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('pages.id'),
        nullable=False,
        comment='所属页面ID'
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='版本号'
    )

    image_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment='图片文件路径'
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment='是否为当前使用的版本'
    )

    generation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment='生成类型：INITIAL|REGENERATION|EDIT'
    )

    edit_instruction: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment='编辑指令（用于EDIT类型）'
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='创建时间'
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'version_id': self.id,
            'page_id': self.page_id,
            'version_number': self.version_number,
            'image_path': self.image_path,
            'image_url': f'/files/{self.image_path.split("/")[0]}/pages/{self.image_path.split("/")[-1]}'
            if self.image_path else None,
            'is_current': self.is_current,
            'generation_type': self.generation_type,
            'edit_instruction': self.edit_instruction,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<PageImageVersion {self.id}: v{self.version_number} - {"current" if self.is_current else "old"}>'
