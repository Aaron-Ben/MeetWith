"""
一个完整的ppt项目
"""
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

class PPTProject(Base):
    __tablename__ = 'ppt_projects'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='项目ID（UUID）'
    )

    idea_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='想法提示'
    )

    outline_text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='用户输入的大纲文本（用于outline类型）'
    )

    description_text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='用户输入的描述文本（用于description类型）'
    )

    extra_requirements: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='额外要求，应用到每个页面的AI提示词'
    )

    creation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='idea',
        comment='项目创建类型：idea|outline|descriptions'
    )

    template_image_path: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment='模板图片路径'
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='DRAFT',
        comment='项目状态：DRAFT|REVIEW|APPROVED|REJECTED'
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

    pages: Mapped[List['Page']] = relationship(
        'Page',
        back_populates='ppt_project',
        cascade='all, delete-orphan',
        order_by='Page.order_index',
    )

    tasks: Mapped[List['Task']] = relationship(
        'Task',
        back_populates='ppt_project',
        cascade='all, delete-orphan',
    )

    reference_files: Mapped[List['ReferenceFile']] = relationship(
        'ReferenceFile',
        back_populates='project',
        foreign_keys='ReferenceFile.project_id',
        cascade='all, delete-orphan',
    )

    # materials: Mapped['Material'] = relationship(
    #     'Material',
    #     back_populates='ppt_project',
    #     cascade='all, delete-orphan',
    # )

    def to_dict(self, include_pages=False):
        """Convert to dictionary"""
        data = {
            'project_id': self.id,
            'idea_prompt': self.idea_prompt,
            'outline_text': self.outline_text,
            'description_text': self.description_text,
            'extra_requirements': self.extra_requirements,
            'creation_type': self.creation_type,
            'template_image_url': f'/files/{self.id}/template/{self.template_image_path.split("/")[-1]}'
            if self.template_image_path
            else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_pages:
            if self.pages is not None:
                data['pages'] = [page.to_dict() for page in sorted(self.pages, key=lambda p: p.order_index)]
            else:
                data['pages'] = []

        return data

    def __repr__(self):
        return f'<Project {self.id}: {self.status}>'
