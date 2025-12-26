"""
ppt的页面模型
"""
import uuid
import json
from datetime import datetime

from app.models.database import Base
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column



class Page(Base):

    __tablename__ = 'pages'

    id : Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='页面ID（UUID）'
    )

    project_id : Mapped[str] = mapped_column(
        String(36),
        ForeignKey('projects.id'),
        nullable=False,
        comment='所属项目ID（UUID）'
    )

    order_index : Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='页面顺序索引'
    )

    part : Mapped[str] = mapped_column(
        String(200),
        nullable=True,
        comment='页面部分名称'
    )

    content : Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='页面内容'
    )

    outline_content : Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='页面大纲内容'
    )

    description_content : Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='页面描述内容'
    )

    generated_image_path : Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment='生成的图片路径'
    )
    
    status : Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='DRAFT',
        comment='页面状态'
    )
    created_at : Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='创建时间'
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment='更新时间'
    )

    project: Mapped['Project'] = mapped_column(
        ForeignKey('projects.id'),
        nullable=False,
        comment='所属项目ID（UUID）'
    )

    def get_outline_content(self):
        """Parse outline_content from JSON string"""
        if self.outline_content:
            try:
                return json.loads(self.outline_content)
            except json.JSONDecodeError:
                return None
        return None

    def set_outline_content(self, data):
        """Set outline_content as JSON string"""
        if data:
            self.outline_content = json.dumps(data, ensure_ascii=False)
        else:
            self.outline_content = None

    def get_description_content(self):
        """Parse description_content from JSON string"""
        if self.description_content:
            try:
                return json.loads(self.description_content)
            except json.JSONDecodeError:
                return None
        return None

    def set_description_content(self, data):
        """Set description_content as JSON string"""
        if data:
            self.description_content = json.dumps(data, ensure_ascii=False)
        else:
            self.description_content = None

    def to_dict(self):
        """Convert to dictionary"""
        data = {
            'page_id': self.id,
            'order_index': self.order_index,
            'part': self.part,
            'outline_content': self.get_outline_content(),
            'description_content': self.get_description_content(),
            'generated_image_url': f'/files/{self.project_id}/pages/{self.generated_image_path.split("/")[-1]}'
            if self.generated_image_path
            else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        return data

    def __repr__(self):
        return f'<Page {self.id}: {self.order_index} - {self.status}>'
