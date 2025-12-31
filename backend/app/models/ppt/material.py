"""
参考材料模型
"""

from typing import Any, Dict, Optional
from app.models.database import Base
from sqlalchemy import ForeignKey, String, DateTime, func
from datetime import datetime
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship

class Material(Base):

    __tablename__ = 'materials'

    id : Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='参考材料ID（UUID）'
    )

    project_id : Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey('ppt_projects.id'),
        nullable=True,
        comment='关联项目ID（UUID）'
    )

    filename : Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='参考材料名称'
    )

    relative_path : Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='参考材料相对路径'
    )

    url : Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='前端可访问的地址'
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        comment='创建时间'
    )

    updated_at : Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment='更新时间'
    )

    project: Mapped[Optional["PPTProject"]] = relationship(
        "PPTProject",
        back_populates="materials",
        lazy="selectin"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'project_id': self.project_id,
            'filename': self.filename,
            'relative_path': self.relative_path,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Material(id={self.id}, filename={self.filename}, relative_path={self.relative_path}, url={self.url})>"
    