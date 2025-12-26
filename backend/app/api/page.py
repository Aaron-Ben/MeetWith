"""
PPT 页面api
"""
import logging
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from fastapi import APIRouter, Request, Body, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# 适配项目结构的导入
from app.extensions import get_db  # 数据库会话依赖
from app.models.ppt.project import PPTProject
from app.models.ppt.page import Page
from app.models.task import Task
from app.services.ai_service import AIService
from app.services.ppt.file import FileService
from app.services.project_context import ProjectContext
from app.services.task_manager import task_manager, generate_single_page_image_task, edit_page_image_task
from app.config.settings import settings  # 全局配置
from app.utils.response import success_response, error_response  # 统一响应工具

# 初始化日志
logger = logging.getLogger(__name__)

page_router = APIRouter(prefix="/api/projects", tags=["Pages"])

# ------------------------------ Pydantic 请求模型（参数校验） ------------------------------
class CreatePageRequest(BaseModel):
    order_index: int
    part: Optional[str] = None
    outline_content: Optional[Dict[str, Any]] = None

class UpdatePageOutlineRequest(BaseModel):
    outline_content: Dict[str, Any]

class UpdatePageDescriptionRequest(BaseModel):
    description_content: Dict[str, Any]

class GenerateDescriptionRequest(BaseModel):
    force_regenerate: bool = False
    language: Optional[str] = None

class GenerateImageRequest(BaseModel):
    use_template: bool = True
    force_regenerate: bool = False
    language: Optional[str] = None

class EditImageContextImages(BaseModel):
    use_template: bool = False
    desc_image_urls: List[str] = []
    uploaded_image_ids: List[str] = []

class EditImageRequest(BaseModel):
    edit_instruction: str
    context_images: Optional[EditImageContextImages] = None

# ------------------------------ 页面核心接口 ------------------------------
@page_router.post("/{project_id}/pages", response_class=JSONResponse, status_code=201)
async def create_page(
    project_id: str,
    request_data: CreatePageRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    添加新页面
    POST /api/projects/{project_id}/pages
    """
    try:
        # 查询项目
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 创建新页面
        page = Page(
            project_id=project_id,
            order_index=request_data.order_index,
            part=request_data.part,
            status='DRAFT'
        )

        # 设置大纲内容
        if request_data.outline_content:
            page.set_outline_content(request_data.outline_content)

        db.add(page)
        db.flush()  # 获取page.id但不提交

        # 更新其他页面的排序索引
        other_pages = db.query(Page).filter(
            Page.project_id == project_id,
            Page.order_index >= request_data.order_index
        ).all()

        for p in other_pages:
            if p.id != page.id:
                p.order_index += 1

        # 更新项目时间
        project.updated_at = datetime.utcnow()
        db.commit()

        return success_response(page.to_dict())

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Create page error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@page_router.delete("/{project_id}/pages/{page_id}", response_class=JSONResponse)
async def delete_page(
    project_id: str,
    page_id: str,
    db: Session = Depends(get_db)
):
    """
    删除页面
    DELETE /api/projects/{project_id}/pages/{page_id}
    """
    try:
        # 查询页面
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        # 删除页面图片
        file_service = FileService(settings.UPLOAD_FOLDER)
        await file_service.delete_page_image(project_id, page_id)  # 适配异步

        # 删除页面记录
        db.delete(page)

        # 更新项目时间
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if project:
            project.updated_at = datetime.utcnow()

        db.commit()

        return success_response(message="Page deleted successfully")

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Delete page error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@page_router.put("/{project_id}/pages/{page_id}/outline", response_class=JSONResponse)
async def update_page_outline(
    project_id: str,
    page_id: str,
    request_data: UpdatePageOutlineRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新页面大纲
    PUT /api/projects/{project_id}/pages/{page_id}/outline
    """
    try:
        # 查询页面
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        # 更新大纲内容
        page.set_outline_content(request_data.outline_content)
        page.updated_at = datetime.utcnow()

        # 更新项目时间
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if project:
            project.updated_at = datetime.utcnow()

        db.commit()

        return success_response(page.to_dict())

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Update page outline error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@page_router.put("/{project_id}/pages/{page_id}/description", response_class=JSONResponse)
async def update_page_description(
    project_id: str,
    page_id: str,
    request_data: UpdatePageDescriptionRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新页面描述
    PUT /api/projects/{project_id}/pages/{page_id}/description
    """
    try:
        # 查询页面
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        # 更新描述内容
        page.set_description_content(request_data.description_content)
        page.updated_at = datetime.utcnow()

        # 更新项目时间
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if project:
            project.updated_at = datetime.utcnow()

        db.commit()

        return success_response(page.to_dict())

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Update page description error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)

# ------------------------------ AI 生成相关接口 ------------------------------
@page_router.post("/{project_id}/pages/{page_id}/generate/description", response_class=JSONResponse)
async def generate_page_description(
    project_id: str,
    page_id: str,
    request_data: GenerateDescriptionRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    AI 生成页面描述
    POST /api/projects/{project_id}/pages/{page_id}/generate/description
    """
    try:
        # 查询页面和项目
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 检查是否已生成且不需要强制重新生成
        if page.get_description_content() and not request_data.force_regenerate:
            raise HTTPException(
                status_code=400,
                detail="Description already exists. Set force_regenerate=true to regenerate"
            )

        # 获取大纲内容
        outline_content = page.get_outline_content()
        if not outline_content:
            raise HTTPException(status_code=400, detail="Page must have outline content first")

        # 重构完整大纲
        all_pages = db.query(Page).filter(
            Page.project_id == project_id
        ).order_by(Page.order_index).all()
        
        outline = []
        for p in all_pages:
            oc = p.get_outline_content()
            if oc:
                page_data = oc.copy()
                if p.part:
                    page_data['part'] = p.part
                outline.append(page_data)

        # 初始化 AI 服务
        ai_service = AIService()

        # 获取参考文件内容（复用原有逻辑）
        from app.api.v1.project_controller import _get_project_reference_files_content
        reference_files_content = _get_project_reference_files_content(project_id, db)
        
        # 创建项目上下文
        project_context = ProjectContext(project, reference_files_content)

        # 生成描述
        page_data = outline_content.copy()
        if page.part:
            page_data['part'] = page.part

        language = request_data.language or settings.OUTPUT_LANGUAGE
        desc_text = ai_service.generate_page_description(
            project_context,
            outline,
            page_data,
            page.order_index + 1,
            language=language
        )

        # 保存描述内容
        desc_content = {
            "text": desc_text,
            "generated_at": datetime.utcnow().isoformat()
        }

        page.set_description_content(desc_content)
        page.status = 'DESCRIPTION_GENERATED'
        page.updated_at = datetime.utcnow()

        # 更新项目时间
        project.updated_at = datetime.utcnow()
        db.commit()

        return success_response(page.to_dict())

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Generate page description error: {str(e)}", exc_info=True)
        return error_response(f"AI_SERVICE_ERROR: {str(e)}", 503)


@page_router.post("/{project_id}/pages/{page_id}/generate/image", response_class=JSONResponse, status_code=202)
async def generate_page_image(
    project_id: str,
    page_id: str,
    request_data: GenerateImageRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    AI 生成页面图片（异步任务）
    POST /api/projects/{project_id}/pages/{page_id}/generate/image
    """
    try:
        # 查询页面和项目
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 检查是否已生成且不需要强制重新生成
        if page.generated_image_path and not request_data.force_regenerate:
            raise HTTPException(
                status_code=400,
                detail="Image already exists. Set force_regenerate=true to regenerate"
            )

        # 获取描述内容
        desc_content = page.get_description_content()
        if not desc_content:
            raise HTTPException(status_code=400, detail="Page must have description content first")

        # 重构完整大纲（带part结构）
        all_pages = db.query(Page).filter(
            Page.project_id == project_id
        ).order_by(Page.order_index).all()
        
        outline = []
        current_part = None
        current_part_pages = []

        for p in all_pages:
            oc = p.get_outline_content()
            if not oc:
                continue
                
            page_data = oc.copy()
            
            # 处理part逻辑
            if p.part:
                if current_part and current_part != p.part:
                    outline.append({
                        "part": current_part,
                        "pages": current_part_pages
                    })
                    current_part_pages = []
                
                current_part = p.part
                if 'part' in page_data:
                    del page_data['part']
                current_part_pages.append(page_data)
            else:
                if current_part:
                    outline.append({
                        "part": current_part,
                        "pages": current_part_pages
                    })
                    current_part = None
                    current_part_pages = []
                
                outline.append(page_data)
        
        # 保存最后一个part
        if current_part:
            outline.append({
                "part": current_part,
                "pages": current_part_pages
            })

        # 初始化服务
        ai_service = AIService()
        file_service = FileService(settings.UPLOAD_FOLDER)

        # 获取模板路径
        ref_image_path = None
        if request_data.use_template:
            ref_image_path = await file_service.get_template_path(project_id)  # 适配异步

        if not ref_image_path:
            raise HTTPException(status_code=400, detail="No template image found for project")

        # 处理描述文本
        page_data = page.get_outline_content() or {}
        if page.part:
            page_data['part'] = page.part

        # 提取描述文本
        desc_text = desc_content.get('text', '')
        if not desc_text and desc_content.get('text_content'):
            text_content = desc_content.get('text_content', [])
            if isinstance(text_content, list):
                desc_text = '\n'.join(text_content)
            else:
                desc_text = str(text_content)

        # 提取图片URL
        additional_ref_images = []
        if desc_text:
            image_urls = ai_service.extract_image_urls_from_markdown(desc_text)
            if image_urls:
                logger.info(f"Found {len(image_urls)} image(s) in page {page_id} description")
                additional_ref_images = image_urls

        # 创建异步任务
        task = Task(
            id=str(uuid.uuid4()),
            project_id=project_id,
            task_type='GENERATE_PAGE_IMAGE',
            status='PENDING',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        task.set_progress({
            'total': 1,
            'completed': 0,
            'failed': 0
        })
        db.add(task)
        db.commit()

        # 提交异步任务（适配 FastAPI 后台任务）
        language = request_data.language or settings.OUTPUT_LANGUAGE
        task_manager.submit_task(
            task.id,
            generate_single_page_image_task,
            project_id,
            page_id,
            ai_service,
            file_service,
            outline,
            request_data.use_template,
            settings.DEFAULT_ASPECT_RATIO,
            settings.DEFAULT_RESOLUTION,
            None,  # FastAPI 无需传递 app 实例，可通过配置直接获取
            project.extra_requirements,
            language
        )

        # 返回任务ID
        return success_response({
            'task_id': task.id,
            'page_id': page_id,
            'status': 'PENDING'
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Generate page image error: {str(e)}", exc_info=True)
        return error_response(f"AI_SERVICE_ERROR: {str(e)}", 503)

# ------------------------------ 图片编辑接口 ------------------------------
@page_router.post("/{project_id}/pages/{page_id}/edit/image", response_class=JSONResponse, status_code=202)
async def edit_page_image(
    project_id: str,
    page_id: str,
    # 支持 JSON 和 FormData 混合请求
    edit_instruction: str = Form(...),
    use_template: str = Form("false"),
    desc_image_urls: str = Form("[]"),
    context_images: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    编辑页面图片（异步任务）
    POST /api/projects/{project_id}/pages/{page_id}/edit/image
    支持 JSON 和 multipart/form-data 两种请求格式
    """
    try:
        # 查询页面和项目
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        if not page.generated_image_path:
            raise HTTPException(status_code=400, detail="Page must have generated image first")

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 初始化服务
        ai_service = AIService()
        file_service = FileService(settings.UPLOAD_FOLDER)

        # 解析请求参数
        use_template_bool = use_template.lower() == 'true'
        try:
            desc_image_urls_list = json.loads(desc_image_urls)
        except:
            desc_image_urls_list = []

        # 获取当前图片路径
        current_image_path = file_service.get_absolute_path(page.generated_image_path)

        # 获取原始描述
        original_description = None
        desc_content = page.get_description_content()
        if desc_content:
            original_description = desc_content.get('text') or ''
            if not original_description and desc_content.get('text_content'):
                text_content = desc_content.get('text_content', [])
                if isinstance(text_content, list):
                    original_description = '\n'.join(text_content)
                else:
                    original_description = str(text_content)

        # 收集参考图片
        additional_ref_images = []

        # 1. 添加模板图片
        if use_template_bool:
            template_path = await file_service.get_template_path(project_id)
            if template_path:
                additional_ref_images.append(template_path)

        # 2. 添加描述中的图片URL
        if isinstance(desc_image_urls_list, list):
            additional_ref_images.extend(desc_image_urls_list)

        # 3. 处理上传的图片文件
        temp_dir = None
        if context_images and len(context_images) > 0:
            # 创建临时目录
            temp_dir = Path(tempfile.mkdtemp(dir=settings.UPLOAD_FOLDER))
            try:
                for uploaded_file in context_images:
                    if uploaded_file.filename:
                        # 安全保存文件
                        filename = secure_filename(uploaded_file.filename)
                        temp_path = temp_dir / filename
                        # 异步保存文件
                        with open(temp_path, "wb") as f:
                            f.write(await uploaded_file.read())
                        additional_ref_images.append(str(temp_path))
            except Exception as e:
                # 异常时清理临时目录
                if temp_dir and temp_dir.exists():
                    shutil.rmtree(temp_dir)
                raise e

        # 创建异步任务
        task = Task(
            id=str(uuid.uuid4()),
            project_id=project_id,
            task_type='EDIT_PAGE_IMAGE',
            status='PENDING',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        task.set_progress({
            'total': 1,
            'completed': 0,
            'failed': 0
        })
        db.add(task)
        db.commit()

        # 提交异步任务
        task_manager.submit_task(
            task.id,
            edit_page_image_task,
            project_id,
            page_id,
            edit_instruction,
            ai_service,
            file_service,
            settings.DEFAULT_ASPECT_RATIO,
            settings.DEFAULT_RESOLUTION,
            original_description,
            additional_ref_images if additional_ref_images else None,
            str(temp_dir) if temp_dir else None,
            None  # FastAPI 无需传递 app 实例
        )

        # 返回任务ID
        return success_response({
            'task_id': task.id,
            'page_id': page_id,
            'status': 'PENDING'
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Edit page image error: {str(e)}", exc_info=True)
        return error_response(f"AI_SERVICE_ERROR: {str(e)}", 503)

# ------------------------------ 图片版本管理接口 ------------------------------
@page_router.get("/{project_id}/pages/{page_id}/image-versions", response_class=JSONResponse)
async def get_page_image_versions(
    project_id: str,
    page_id: str,
    db: Session = Depends(get_db)
):
    """
    获取页面图片版本列表
    GET /api/projects/{project_id}/pages/{page_id}/image-versions
    """
    try:
        # 查询页面
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        # 查询版本列表
        versions = db.query(PageImageVersion).filter(
            PageImageVersion.page_id == page_id
        ).order_by(PageImageVersion.version_number.desc()).all()

        return success_response({
            'versions': [v.to_dict() for v in versions]
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Get page image versions error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@page_router.post("/{project_id}/pages/{page_id}/image-versions/{version_id}/set-current", response_class=JSONResponse)
async def set_current_image_version(
    project_id: str,
    page_id: str,
    version_id: str,
    db: Session = Depends(get_db)
):
    """
    设置当前使用的图片版本
    POST /api/projects/{project_id}/pages/{page_id}/image-versions/{version_id}/set-current
    """
    try:
        # 查询页面
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page or page.project_id != project_id:
            raise HTTPException(status_code=404, detail="Page not found")

        # 查询版本
        version = db.query(PageImageVersion).filter(PageImageVersion.id == version_id).first()
        if not version or version.page_id != page_id:
            raise HTTPException(status_code=404, detail="Image Version not found")

        # 将所有版本标记为非当前
        db.query(PageImageVersion).filter(
            PageImageVersion.page_id == page_id
        ).update({'is_current': False})

        # 设置当前版本
        version.is_current = True
        page.generated_image_path = version.image_path
        page.updated_at = datetime.utcnow()

        db.commit()

        return success_response(page.to_dict(include_versions=True))

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Set current image version error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)