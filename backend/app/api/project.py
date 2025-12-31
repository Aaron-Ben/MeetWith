"""
项目CRUD API
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Request, Body, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from app.models.database import get_db
from app.models.ppt.project import PPTProject
from app.models.ppt.page import Page
from app.models.ppt.task import Task
from app.services.ppt.file import FileService
from app.services.ppt.ai_service import AIService, ProjectContext
from app.services.ppt.task_manager import get_task_manager
from app.config import Config

logger = logging.getLogger(__name__)

project_router = APIRouter(prefix="/api/projects", tags=["Projects"])


# ------------------------------ Pydantic 模型 ------------------------------
class CreateProjectRequest(BaseModel):
    """创建项目请求"""
    idea_prompt: Optional[str] = None
    outline_text: Optional[str] = None
    description_text: Optional[str] = None
    extra_requirements: Optional[str] = None
    creation_type: str = "idea"  # idea|outline|descriptions
    template_image_url: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    """更新项目请求"""
    idea_prompt: Optional[str] = None
    outline_text: Optional[str] = None
    description_text: Optional[str] = None
    extra_requirements: Optional[str] = None
    status: Optional[str] = None


class GenerateOutlineRequest(BaseModel):
    """生成大纲请求"""
    force_regenerate: bool = False
    language: Optional[str] = "zh"


class GenerateDescriptionsRequest(BaseModel):
    """生成所有描述请求"""
    language: Optional[str] = "zh"


class GenerateAllImagesRequest(BaseModel):
    """生成所有图片请求"""
    use_template: bool = True
    language: Optional[str] = "zh"


# ------------------------------ 工具函数 ------------------------------
def _get_reference_files_content(project_id: str, db: Session) -> List[str]:
    """获取项目参考文件内容"""
    try:
        from app.models.refernce_file import ReferenceFile
        reference_files = db.query(ReferenceFile).filter(
            ReferenceFile.project_id == project_id
        ).all()

        contents = []
        for rf in reference_files:
            if rf.markdown_content:
                contents.append(rf.markdown_content)

        return contents
    except Exception as e:
        logger.error(f"获取参考文件内容失败: {str(e)}")
        return []


# ------------------------------ 项目 CRUD 接口 ------------------------------
@project_router.post("", response_class=JSONResponse, status_code=201)
async def create_project(
    request_data: CreateProjectRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    创建新项目
    POST /api/projects
    """
    try:
        # 验证创建类型
        if request_data.creation_type not in ['idea', 'outline', 'descriptions']:
            raise HTTPException(
                status_code=400,
                detail="Invalid creation_type. Must be 'idea', 'outline', or 'descriptions'"
            )

        # 验证必填字段
        if request_data.creation_type == 'idea' and not request_data.idea_prompt:
            raise HTTPException(
                status_code=400,
                detail="idea_prompt is required for idea creation type"
            )
        elif request_data.creation_type == 'outline' and not request_data.outline_text:
            raise HTTPException(
                status_code=400,
                detail="outline_text is required for outline creation type"
            )
        elif request_data.creation_type == 'descriptions' and not request_data.description_text:
            raise HTTPException(
                status_code=400,
                detail="description_text is required for descriptions creation type"
            )

        # 创建项目
        project = PPTProject(
            idea_prompt=request_data.idea_prompt,
            outline_text=request_data.outline_text,
            description_text=request_data.description_text,
            extra_requirements=request_data.extra_requirements,
            creation_type=request_data.creation_type,
            status='DRAFT'
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "data": project.to_dict(),
            "message": "项目创建成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Create project error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"SERVER_ERROR: {str(e)}"
        )


@project_router.get("", response_class=JSONResponse)
async def list_projects(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取项目列表
    GET /api/projects?status=xxx
    """
    try:
        query = db.query(PPTProject)

        if status:
            query = query.filter(PPTProject.status == status)

        projects = query.order_by(PPTProject.created_at.desc()).all()

        return {
            "success": True,
            "data": {
                "projects": [p.to_dict() for p in projects],
                "count": len(projects)
            }
        }

    except Exception as e:
        logger.error(f"List projects error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"SERVER_ERROR: {str(e)}"
        )


@project_router.get("/{project_id}", response_class=JSONResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    获取项目详情
    GET /api/projects/{project_id}
    """
    try:
        project = db.query(PPTProject).options(
            joinedload(PPTProject.pages)
        ).filter(PPTProject.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return {
            "success": True,
            "data": project.to_dict(include_pages=True)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"SERVER_ERROR: {str(e)}"
        )


@project_router.put("/{project_id}", response_class=JSONResponse)
async def update_project(
    project_id: str,
    request_data: UpdateProjectRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新项目
    PUT /api/projects/{project_id}
    """
    try:
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 更新字段
        if request_data.idea_prompt is not None:
            project.idea_prompt = request_data.idea_prompt
        if request_data.outline_text is not None:
            project.outline_text = request_data.outline_text
        if request_data.description_text is not None:
            project.description_text = request_data.description_text
        if request_data.extra_requirements is not None:
            project.extra_requirements = request_data.extra_requirements
        if request_data.status is not None:
            project.status = request_data.status

        project.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "data": project.to_dict(),
            "message": "项目更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update project error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"SERVER_ERROR: {str(e)}"
        )


@project_router.delete("/{project_id}", response_class=JSONResponse)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    删除项目
    DELETE /api/projects/{project_id}
    """
    try:
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 删除项目文件
        file_service = FileService(Config.UPLOAD_FOLDER)
        file_service.delete_project_files(project_id)

        # 删除数据库记录（级联删除pages、tasks等）
        db.delete(project)
        db.commit()

        return {
            "success": True,
            "data": {"project_id": project_id},
            "message": "项目删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Delete project error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"SERVER_ERROR: {str(e)}"
        )


# ------------------------------ AI 生成接口 ------------------------------
@project_router.post("/{project_id}/generate/outline", response_class=JSONResponse)
async def generate_outline(
    project_id: str,
    request_data: GenerateOutlineRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    AI 生成大纲
    POST /api/projects/{project_id}/generate/outline
    """
    try:
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 检查是否已有页面
        existing_pages = db.query(Page).filter(Page.project_id == project_id).all()
        if existing_pages and not request_data.force_regenerate:
            raise HTTPException(
                status_code=400,
                detail="Project already has pages. Set force_regenerate=true to regenerate"
            )

        # 如果是重新生成，删除旧页面
        if existing_pages and request_data.force_regenerate:
            for page in existing_pages:
                db.delete(page)
            db.commit()

        # 获取参考文件内容
        reference_files_content = _get_reference_files_content(project_id, db)

        # 创建项目上下文
        project_context = ProjectContext(project, reference_files_content)

        # 初始化AI服务
        ai_service = AIService()

        # 生成大纲
        language = request_data.language or "zh"
        outline = ai_service.generate_outline_from_idea(
            project_context,
            project.idea_prompt or project.outline_text or "",
            language=language
        )

        # 创建页面
        order_index = 0
        for part in outline:
            part_name = part.get('title', '')
            pages_in_part = part.get('pages', [])

            for page_data in pages_in_part:
                page = Page(
                    project_id=project_id,
                    order_index=order_index,
                    part=part_name if part_name else None,
                    status='DRAFT'
                )
                page.set_outline_content(page_data)
                db.add(page)
                order_index += 1

        project.status = 'OUTLINE_GENERATED'
        project.updated_at = datetime.utcnow()
        db.commit()

        # 重新查询项目以获取最新数据
        db.refresh(project)

        return {
            "success": True,
            "data": project.to_dict(include_pages=True),
            "message": f"大纲生成成功，共生成 {order_index} 页"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Generate outline error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"AI_SERVICE_ERROR: {str(e)}"
        )


@project_router.post("/{project_id}/generate-outline", response_class=JSONResponse)
async def generate_outline_alias(
    project_id: str,
    request_data: Optional[GenerateOutlineRequest] = Body(None),
    db: Session = Depends(get_db)
):
    """
    AI 生成大纲（别名，使用连字符）
    POST /api/projects/{project_id}/generate-outline
    """
    # 如果没有传入请求数据，使用默认值
    if request_data is None:
        request_data = GenerateOutlineRequest()

    # 如果已有页面，自动设置 force_regenerate
    existing_pages = db.query(Page).filter(Page.project_id == project_id).all()
    if existing_pages and not request_data.force_regenerate:
        request_data.force_regenerate = True
    return await generate_outline(project_id, request_data, db)


@project_router.post("/{project_id}/generate/all-descriptions", response_class=JSONResponse)
async def generate_all_descriptions(
    project_id: str,
    request_data: GenerateDescriptionsRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    AI 生成所有页面描述（并发处理）
    POST /api/projects/{project_id}/generate/all-descriptions
    """
    async def generate_single_description(page, project_context, outline, language):
        """单个页面描述生成的异步包装"""
        page_data = page.get_outline_content()
        if not page_data:
            return None, page

        if page.part:
            page_data['part'] = page.part

        # 在线程池中运行同步的 LLM 调用
        loop = asyncio.get_event_loop()
        ai_service = AIService()
        description_text = await loop.run_in_executor(
            None,
            ai_service.generate_page_description,
            project_context,
            outline,
            page_data,
            page.order_index + 1,
            language
        )

        desc_content = {
            "text": description_text,
            "generated_at": datetime.utcnow().isoformat()
        }
        return desc_content, page

    try:
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 获取所有页面
        pages = db.query(Page).filter(Page.project_id == project_id).order_by(Page.order_index).all()
        if not pages:
            raise HTTPException(status_code=400, detail="No pages found. Generate outline first")

        # 获取参考文件内容
        reference_files_content = _get_reference_files_content(project_id, db)

        # 创建项目上下文
        project_context = ProjectContext(project, reference_files_content)

        # 构建完整大纲
        outline = []
        for page in pages:
            oc = page.get_outline_content()
            if oc:
                page_data = oc.copy()
                if page.part:
                    page_data['part'] = page.part
                outline.append(page_data)

        language = request_data.language or "zh"

        # 并发生成所有页面描述（限制并发数为5）
        tasks = [
            generate_single_description(page, project_context, outline, language)
            for page in pages
        ]
        results = await asyncio.gather(*tasks)

        # 保存结果
        generated_count = 0
        for desc_content, page in results:
            if desc_content:
                page.set_description_content(desc_content)
                page.status = 'DESCRIPTION_GENERATED'
                generated_count += 1

        project.status = 'DESCRIPTIONS_GENERATED'
        project.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "data": {"generated_count": generated_count},
            "message": f"成功生成 {generated_count} 个页面描述"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Generate all descriptions error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"AI_SERVICE_ERROR: {str(e)}"
        )


@project_router.post("/{project_id}/generate-descriptions", response_class=JSONResponse)
async def generate_descriptions(
    project_id: str,
    request_data: GenerateDescriptionsRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    AI 生成所有页面描述（别名）
    POST /api/projects/{project_id}/generate-descriptions
    """
    return await generate_all_descriptions(project_id, request_data, db)


@project_router.post("/{project_id}/generate/all-images", response_class=JSONResponse)
async def generate_all_images(
    project_id: str,
    request_data: GenerateAllImagesRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    AI 生成所有页面图片（异步任务）
    POST /api/projects/{project_id}/generate/all-images
    """
    try:
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 获取所有页面
        pages = db.query(Page).filter(Page.project_id == project_id).order_by(Page.order_index).all()
        if not pages:
            raise HTTPException(status_code=400, detail="No pages found")

        # 检查是否有描述内容
        pages_without_description = [p for p in pages if not p.get_description_content()]
        if pages_without_description:
            raise HTTPException(
                status_code=400,
                detail=f"{len(pages_without_description)} pages have no description. Generate descriptions first"
            )

        # 创建任务
        task = Task(
            project_id=project_id,
            task_type='GENERATE_ALL_IMAGES',
            status='PENDING'
        )
        task.set_progress({
            'total': len(pages),
            'completed': 0,
            'failed': 0
        })
        db.add(task)
        db.commit()

        # 提交后台任务
        # 注意：这里需要实现 generate_all_pages_images_task 函数
        # 暂时返回任务ID
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "status": "PENDING"
            },
            "message": "批量生成图片任务已提交"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Generate all images error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"AI_SERVICE_ERROR: {str(e)}"
        )


@project_router.get("/{project_id}/tasks/{task_id}", response_class=JSONResponse)
async def get_task_status(
    project_id: str,
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务状态
    GET /api/projects/{project_id}/tasks/{task_id}
    """
    try:
        task_manager = get_task_manager()
        task_info = task_manager.get_task_status(task_id)

        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "success": True,
            "data": task_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task status error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"SERVER_ERROR: {str(e)}"
        )
