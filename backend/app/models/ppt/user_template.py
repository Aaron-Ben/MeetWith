"""
用户上传模版
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.models.__init__ import Base

class UserTemplate(Base):
    __tablename__ = 'user_templates'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    template_file_path = Column(String(200), nullable=False)
    template_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

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
