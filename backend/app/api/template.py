"""
用户模版api
"""
import logging
import uuid
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.extensions import get_db  # 数据库会话依赖
from app.models.project import Project  # 项目模型
from app.models.user_template import UserTemplate  # 用户模板模型
from app.services.file_service import FileService  # 文件服务
from app.config.settings import settings  # 全局配置
from app.utils.response import success_response, error_response  # 统一响应工具
from app.utils.file_ops import allowed_file  # 文件校验工具

# 初始化日志
logger = logging.getLogger(__name__)

template_router = APIRouter(prefix="/api/projects", tags=["Project Templates"])
user_template_router = APIRouter(prefix="/api/user-templates", tags=["User Templates"])

# ------------------------------ 项目模板接口 ------------------------------
@template_router.post("/{project_id}/template", response_class=JSONResponse)
async def upload_template(
    project_id: str,
    template_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传项目模板图片
    POST /api/projects/{project_id}/template
    """
    try:
        # 查询项目
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 校验文件
        if not template_image.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # 校验文件类型
        if not allowed_file(template_image.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 保存文件
        file_service = FileService(settings.UPLOAD_FOLDER)
        file_path = await file_service.save_template_image(template_image, project_id)  # 适配异步

        # 更新项目
        project.template_image_path = file_path
        project.updated_at = datetime.utcnow()
        db.commit()

        return success_response({
            'template_image_url': f'/files/{project_id}/template/{file_path.split("/")[-1]}'
        })

    except HTTPException as e:
        # 主动抛出的HTTP异常直接返回
        return error_response(e.detail, e.status_code)
    except Exception as e:
        db.rollback()
        logger.error(f"Upload template error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@template_router.delete("/{project_id}/template", response_class=JSONResponse)
async def delete_template(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    删除项目模板
    DELETE /api/projects/{project_id}/template
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not project.template_image_path:
            raise HTTPException(status_code=400, detail="No template to delete")

        # 删除文件
        file_service = FileService(settings.UPLOAD_FOLDER)
        await file_service.delete_template(project_id)  # 适配异步

        # 更新项目
        project.template_image_path = None
        project.updated_at = datetime.utcnow()
        db.commit()

        return success_response(message="Template deleted successfully")

    except HTTPException as e:
        return error_response(e.detail, e.status_code)
    except Exception as e:
        db.rollback()
        logger.error(f"Delete template error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@template_router.get("/templates", response_class=JSONResponse)
async def get_system_templates():
    """
    获取系统预设模板（占位接口）
    GET /api/templates
    """
    # TODO: 实现系统模板逻辑
    templates = []
    return success_response({'templates': templates})

# ------------------------------ 用户模板接口 ------------------------------
@user_template_router.post("", response_class=JSONResponse)
async def upload_user_template(
    template_image: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    上传用户自定义模板
    POST /api/user-templates
    """
    try:
        # 校验文件
        if not template_image.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        if not allowed_file(template_image.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 获取文件大小
        file_size = await template_image.seek(0, 2)  # 异步获取文件大小
        await template_image.seek(0)  # 重置文件指针

        # 生成模板ID
        template_id = str(uuid.uuid4())

        # 保存文件
        file_service = FileService(settings.UPLOAD_FOLDER)
        file_path = await file_service.save_user_template(template_image, template_id)

        # 创建用户模板记录
        template = UserTemplate(
            id=template_id,
            name=name,
            file_path=file_path,
            file_size=file_size,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(template)
        db.commit()
        db.refresh(template)  # 刷新获取完整记录

        return success_response(template.to_dict())

    except HTTPException as e:
        return error_response(e.detail, e.status_code)
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"Upload user template error: {error_msg}", exc_info=True)
        
        # 开发环境返回详细错误，生产环境返回通用错误
        if settings.DEBUG:
            return error_response(f"SERVER_ERROR: {error_msg}\n{traceback.format_exc()}", 500)
        else:
            return error_response(f"SERVER_ERROR: {error_msg}", 500)


@user_template_router.get("", response_class=JSONResponse)
async def list_user_templates(
    db: Session = Depends(get_db)
):
    """
    获取用户模板列表
    GET /api/user-templates
    """
    try:
        templates = db.query(UserTemplate).order_by(UserTemplate.created_at.desc()).all()
        return success_response({
            'templates': [template.to_dict() for template in templates]
        })

    except Exception as e:
        logger.error(f"List user templates error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@user_template_router.delete("/{template_id}", response_class=JSONResponse)
async def delete_user_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    删除用户模板
    DELETE /api/user-templates/{template_id}
    """
    try:
        template = db.query(UserTemplate).filter(UserTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="UserTemplate not found")

        # 删除文件
        file_service = FileService(settings.UPLOAD_FOLDER)
        await file_service.delete_user_template(template_id)

        # 删除数据库记录
        db.delete(template)
        db.commit()

        return success_response(message="Template deleted successfully")

    except HTTPException as e:
        return error_response(e.detail, e.status_code)
    except Exception as e:
        db.rollback()
        logger.error(f"Delete user template error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)