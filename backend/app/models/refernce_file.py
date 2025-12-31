"""
Reference File model - stores uploaded reference files and their parsed content
"""
import uuid
import re
from datetime import datetime
from app.models.database import Base
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ReferenceFile(Base):
    """
    Reference File model - represents an uploaded reference file
    """
    __tablename__ = 'reference_files'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='Reference file ID (UUID)'
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('ppt_projects.id'),
        nullable=True,
        comment='Project ID (UUID) this file belongs to, can be null for global files'
    )

    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment='Original filename'
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment='File path relative to upload folder'
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='File size in bytes'
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment='File type, e.g. pdf, docx, pptx'
    )

    parse_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='pending',
        comment='Parsing status: pending|parsing|completed|failed'
    )

    markdown_content: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='Parsed markdown content with enhanced image descriptions'
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment='Error message if parsing failed'
    )

    mineru_batch_id: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment='Mineru service batch ID'
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='Creation time'
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment='Last update time'
    )

    """
    Relationships
    """

    project: Mapped['PPTProject'] = relationship('PPTProject', back_populates='reference_files', foreign_keys=[project_id])

    
    def to_dict(self, include_content=True, include_failed_count=False):
        """
        Convert to dictionary
        
        Args:
            include_content: Whether to include markdown_content (can be large)
            include_failed_count: Whether to calculate failed image count (can be slow)
        """
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'parse_status': self.parse_status,
            'error_message': self.error_message,
            'mineru_batch_id': self.mineru_batch_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_content:
            result['markdown_content'] = self.markdown_content
        
        # 只有明确要求且文件已解析完成时才计算失败数
        if include_failed_count and self.parse_status == 'completed':
            result['image_caption_failed_count'] = self.count_failed_image_captions()
        
        return result
    
    def count_failed_image_captions(self) -> int:
        """
        Count images in markdown that don't have alt text (failed to generate captions)
        
        Returns:
            Number of images without captions
        """
        if not self.markdown_content:
            return 0
        
        # Match markdown images: ![alt](url)
        pattern = r'!\[(.*?)\]\([^\)]+\)'
        matches = re.findall(pattern, self.markdown_content)
        
        # Count images with empty alt text
        failed_count = sum(1 for alt_text in matches if not alt_text.strip())
        return failed_count
    
    def __repr__(self):
        return f'<ReferenceFile {self.id}: {self.filename} ({self.parse_status})>'
