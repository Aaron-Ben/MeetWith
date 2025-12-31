"""
任务模型 - 用于跟踪AI生成的异步任务
"""
import uuid
import json
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.database import Base


class Task(Base):
    """异步任务模型"""

    __tablename__ = 'tasks'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='任务ID（UUID）'
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('ppt_projects.id'),
        nullable=True,
        comment='关联项目ID'
    )

    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment='任务类型：GENERATE_OUTLINE|GENERATE_DESCRIPTIONS|GENERATE_PAGE_IMAGE|EDIT_PAGE_IMAGE|GENERATE_MATERIAL'
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='PENDING',
        comment='任务状态：PENDING|IN_PROGRESS|COMPLETED|FAILED'
    )

    progress: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='任务进度信息（JSON格式）'
    )

    result: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment='任务结果（JSON格式）'
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='错误信息'
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

    ppt_project: Mapped['PPTProject'] = relationship(
        'PPTProject',
        back_populates='tasks',
        lazy='selectin'
    )

    def get_progress(self) -> dict:
        """获取进度信息"""
        if self.progress:
            try:
                return json.loads(self.progress)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_progress(self, progress_data: dict):
        """设置进度信息"""
        self.progress = json.dumps(progress_data, ensure_ascii=False)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'task_id': self.id,
            'project_id': self.project_id,
            'task_type': self.task_type,
            'status': self.status,
            'progress': self.get_progress(),
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Task {self.id}: {self.task_type} - {self.status}>'
