"""
用户上传模版
"""
import uuid
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from app.models.database import Base
from sqlalchemy.orm import Mapped, mapped_column

class UserTemplate(Base):
    __tablename__ = 'user_templates'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='用户模板ID（UUID）'
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='用户模板名称'
    )

    template_file_path: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment='用户模板文件路径'
    )

    template_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='用户模板文件大小'
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='创建时间'
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment='更新时间'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'template_file_path': self.template_file_path,
            'template_size': self.template_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<UserTemplate {self.id} : {self.name}>'
