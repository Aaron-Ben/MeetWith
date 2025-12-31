"""
AI 图片生成任务 - 用于异步生成PPT页面图片
"""
import logging
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List
from PIL import Image
from app.models.database import SessionLocal
from app.models.ppt.page import Page
from app.models.ppt.project import PPTProject
from app.models.ppt.page_image_version import PageImageVersion
from app.services.ppt.ai_service import AIService
from app.services.ppt.file import FileService
from app.config import Config

logger = logging.getLogger(__name__)


def generate_material_image_task(
    project_id: str,
    prompt: str,
    ai_service: AIService,
    file_service: FileService,
    ref_image_path: Optional[str],
    additional_ref_images: Optional[List[str]],
    aspect_ratio: str,
    resolution: str,
    temp_dir: str,
    app
):
    """
    生成素材图片任务
    注意：这是一个简化版本，实际AI图片生成需要集成具体的AI图片生成API
    """
    db = SessionLocal()
    try:
        # TODO: 集成实际的AI图片生成服务（如DALL-E、Midjourney、Stable Diffusion等）
        logger.info(f"Generating material image for project {project_id} with prompt: {prompt}")

        # 模拟生成图片（实际应该调用AI服务）
        # 这里创建一个占位图片
        from PIL import Image, ImageDraw, ImageFont

        width, height = 1920, 1080
        image = Image.new('RGB', (width, height), color='#f0f0f0')
        draw = ImageDraw.Draw(image)

        # 绘制占位符文字
        draw.text((100, 100), "AI Generated Material", fill='#333333')

        # 保存图片
        image_path = file_service.save_material_image(image, project_id, 'PNG')

        logger.info(f"Material image generated: {image_path}")

    finally:
        db.close()
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def generate_single_page_image_task(
    project_id: str,
    page_id: str,
    ai_service: AIService,
    file_service: FileService,
    outline: List[dict],
    use_template: bool,
    aspect_ratio: str,
    resolution: str,
    app,
    extra_requirements: Optional[str] = None,
    language: str = "zh"
):
    """
    生成单个页面图片任务
    注意：这是一个简化版本，实际AI图片生成需要集成具体的AI图片生成API
    """
    db = SessionLocal()
    try:
        # 获取页面
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            logger.error(f"Page {page_id} not found")
            return

        logger.info(f"Generating image for page {page_id}")

        # TODO: 集成实际的AI图片生成服务
        # 这里创建一个占位图片
        from PIL import Image, ImageDraw, ImageFont

        width, height = 1920, 1080
        image = Image.new('RGB', (width, height), color='#ffffff')
        draw = ImageDraw.Draw(image)

        # 绘制占位符内容
        outline_content = page.get_outline_content()
        title = outline_content.get('title', 'Untitled') if outline_content else 'Untitled'

        draw.text((100, 100), title, fill='#333333')
        draw.text((100, 200), "AI Generated Content", fill='#666666')

        # 获取下一个版本号
        last_version = db.query(PageImageVersion).filter(
            PageImageVersion.page_id == page_id
        ).order_by(PageImageVersion.version_number.desc()).first()

        next_version = (last_version.version_number + 1) if last_version else 1

        # 保存图片
        image_path = file_service.save_generated_image(
            image, project_id, page_id, 'PNG', version_number=next_version
        )

        # 更新页面
        page.generated_image_path = image_path
        page.status = 'IMAGE_GENERATED'
        db.commit()

        # 创建版本记录
        version = PageImageVersion(
            page_id=page_id,
            version_number=next_version,
            image_path=image_path,
            is_current=True,
            generation_type='INITIAL'
        )
        db.add(version)

        # 将其他版本设为非当前
        db.query(PageImageVersion).filter(
            PageImageVersion.page_id == page_id,
            PageImageVersion.id != version.id
        ).update({'is_current': False})

        db.commit()

        logger.info(f"Page image generated: {image_path}")

    except Exception as e:
        logger.error(f"Generate page image error: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


def edit_page_image_task(
    project_id: str,
    page_id: str,
    edit_instruction: str,
    ai_service: AIService,
    file_service: FileService,
    aspect_ratio: str,
    resolution: str,
    original_description: Optional[str],
    additional_ref_images: Optional[List[str]],
    temp_dir: Optional[str],
    app
):
    """
    编辑页面图片任务
    """
    db = SessionLocal()
    try:
        # 获取页面
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            logger.error(f"Page {page_id} not found")
            return

        logger.info(f"Editing image for page {page_id} with instruction: {edit_instruction}")

        # TODO: 集成实际的AI图片编辑服务
        # 这里使用原图作为示例
        from PIL import Image, ImageDraw, ImageFont

        width, height = 1920, 1080
        image = Image.new('RGB', (width, height), color='#ffffff')
        draw = ImageDraw.Draw(image)

        draw.text((100, 100), f"Edited: {edit_instruction[:50]}", fill='#333333')

        # 获取下一个版本号
        last_version = db.query(PageImageVersion).filter(
            PageImageVersion.page_id == page_id
        ).order_by(PageImageVersion.version_number.desc()).first()

        next_version = (last_version.version_number + 1) if last_version else 1

        # 保存图片
        image_path = file_service.save_generated_image(
            image, project_id, page_id, 'PNG', version_number=next_version
        )

        # 更新页面
        page.generated_image_path = image_path
        db.commit()

        # 创建版本记录
        version = PageImageVersion(
            page_id=page_id,
            version_number=next_version,
            image_path=image_path,
            is_current=True,
            generation_type='EDIT',
            edit_instruction=edit_instruction
        )
        db.add(version)

        # 将其他版本设为非当前
        db.query(PageImageVersion).filter(
            PageImageVersion.page_id == page_id,
            PageImageVersion.id != version.id
        ).update({'is_current': False})

        db.commit()

        logger.info(f"Page image edited: {image_path}")

    except Exception as e:
        logger.error(f"Edit page image error: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
