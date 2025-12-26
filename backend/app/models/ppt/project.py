"""
一个完整的ppt项目
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.models.__init__ import Base

class PPTProject(Base):
    __tablename__ = 'ppt_projects'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_prompt = Column(Text, nullable=True)
    outline_text = Column(Text, nullable=True)  # 用户输入的大纲文本（用于outline类型）
    description_text = Column(Text, nullable=True)  # 用户输入的描述文本（用于description类型）
    extra_requirements = Column(Text, nullable=True)  # 额外要求，应用到每个页面的AI提示词
    creation_type = Column(String(20), nullable=False, default='idea')  # idea|outline|descriptions
    template_image_path = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default='DRAFT')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pages = relationship(
        'Page',
        back_populates='ppt_project',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Page.order_index',
    )
    tasks = relationship(
        'Task',
        back_populates='ppt_project',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    materials = relationship(
        'Material',
        back_populates='ppt_project',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

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
            data['pages'] = [page.to_dict() for page in self.pages.order_by('order_index')]

        return data

    def __repr__(self):
        return f'<Project {self.id}: {self.status}>'
