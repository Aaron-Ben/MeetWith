"素材管理的api"
from app.models.ppt.project import PPTProject
from app.models.ppt.material import Material
from app.models.ppt.task import Task
from app.services.ppt.file import FileService
from app.services.ppt.ai_service import AIService
from app.services.ppt.task_manager import task_manager
from app.services.ppt.image_tasks import generate_material_image_task
from app.models.database import SessionLocal
from app.config import Config
from fastapi import (
    APIRouter,
    Request,
    Query,
    Path,
    Body,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Depends
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile
import shutil
import time
import os
import re


material_router = APIRouter(prefix="/api/projects", tags=["Materials (Project)"])
material_global_router = APIRouter(prefix="/api/materials", tags=["Materials (Global)"])

# 常量定义
ALLOWED_MATERIAL_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}

# ------------------------------
# Pydantic模型（请求/响应结构）
# ------------------------------
class SuccessResponse(BaseModel):
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: str = "操作成功"

class ErrorResponse(BaseModel):
    success: bool = False
    error_type: str
    message: str

class AssociateMaterialRequest(BaseModel):
    project_id: str = Field(..., description="目标项目ID")
    material_urls: List[str] = Field(..., description="要关联的素材URL列表", min_items=1)

class GenerateMaterialResponse(BaseModel):
    task_id: str
    status: str = "PENDING"

class MaterialListResponse(BaseModel):
    materials: List[Dict[str, Any]]
    count: int


def get_upload_folder(request: Request) -> str:
    """依赖：获取上传目录配置"""
    upload_folder = request.app.state.config.get("UPLOAD_FOLDER")
    if not upload_folder:
        raise HTTPException(status_code=500, detail={"error_type": "SERVER_ERROR", "message": "UPLOAD_FOLDER未配置"})
    return upload_folder

def _build_material_query(filter_project_id: str):
    """构建素材查询语句"""
    query = Material.query

    if filter_project_id == 'all':
        return query, None
    if filter_project_id == 'none':
        return query.filter(Material.project_id.is_(None)), None

    project = PPTProject.query(Material).filter(Material.id ==(filter_project_id)
    if not project:
        return None, HTTPException(
            status_code=404,
            detail={"error_type": "NOT_FOUND", "message": "Project not found"}
        )

    return query.filter(Material.project_id == filter_project_id), None

def _get_materials_list(filter_project_id: str):
    """获取素材列表"""
    query, error = _build_material_query(filter_project_id)
    if error:
        return None, error
    
    materials = query.order_by(Material.created_at.desc()).all()
    materials_list = [material.to_dict() for material in materials]
    
    return materials_list, None

def _resolve_target_project_id(raw_project_id: Optional[str], allow_none: bool = True):
    """解析目标项目ID"""
    if allow_none and (raw_project_id is None or raw_project_id == 'none'):
        return None, None

    if raw_project_id == 'all':
        return None, HTTPException(
            status_code=400,
            detail={"error_type": "BAD_REQUEST", "message": "project_id cannot be 'all' when uploading materials"}
        )

    if raw_project_id:
        project = PPTProject.query(Material).filter(Material.id ==(raw_project_id)
        if not project:
            return None, HTTPException(
                status_code=404,
                detail={"error_type": "NOT_FOUND", "message": "Project not found"}
            )

    return raw_project_id, None

def _save_material_file(
    file: UploadFile,
    target_project_id: Optional[str],
    upload_folder: str
) -> Material:
    """保存素材文件到磁盘和数据库"""
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail={"error_type": "BAD_REQUEST", "message": "file is required"}
        )

    filename = file.filename
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_MATERIAL_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "BAD_REQUEST",
                "message": f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_MATERIAL_EXTENSIONS))}"
            }
        )

    file_service = FileService(upload_folder)
    if target_project_id:
        materials_dir = file_service._get_materials_dir(target_project_id)
    else:
        materials_dir = file_service.upload_folder / "materials"
        materials_dir.mkdir(exist_ok=True, parents=True)

    timestamp = int(time.time() * 1000)
    base_name = Path(filename).stem
    unique_filename = f"{base_name}_{timestamp}{file_ext}"

    filepath = materials_dir / unique_filename
    with open(str(filepath), "wb") as f:
        f.write(file.file.read())

    relative_path = str(filepath.relative_to(file_service.upload_folder))
    if target_project_id:
        image_url = file_service.get_file_url(target_project_id, 'materials', unique_filename)
    else:
        image_url = f"/files/materials/{unique_filename}"

    material = Material(
        project_id=target_project_id,
        filename=unique_filename,
        relative_path=relative_path,
        url=image_url
    )

    try:
        db.session.add(material)
        db.session.commit()
        return material
    except Exception:
        db.session.rollback()
        raise

async def _handle_material_upload(
    request: Request,
    default_project_id: Optional[str] = None
) -> JSONResponse:
    """处理素材上传"""
    try:
        # 获取上传的文件
        file = await request.form.get("file")  # FastAPI异步获取form数据
        if not isinstance(file, UploadFile):
            raise HTTPException(
                status_code=400,
                detail={"error_type": "BAD_REQUEST", "message": "file is required"}
            )
        
        # 解析project_id
        raw_project_id = request.query_params.get('project_id', default_project_id)
        target_project_id, error = _resolve_target_project_id(raw_project_id)
        if error:
            raise error

        # 保存文件
        upload_folder = get_upload_folder(request)
        material = _save_material_file(file, target_project_id, upload_folder)

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "data": material.to_dict(),
                "message": "素材上传成功"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_type": "SERVER_ERROR", "message": str(e)}
        )

# ------------------------------
# 项目维度素材接口
# ------------------------------
@material_router.post(
    "/{project_id}/materials/generate",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
async def generate_material_image(
    request: Request,
    project_id: str,
    prompt: Optional[str] = Form(None),
    ref_image: Optional[UploadFile] = File(None),
    extra_images: List[UploadFile] = File([]),
    json_data: Optional[Dict[str, Any]] = Body(None)
):
    """
    POST /api/projects/{project_id}/materials/generate - 生成素材图片（异步）
    支持JSON/表单/文件上传混合请求
    """
    try:
        # 处理project_id
        if project_id != 'none':
            project = PPTProject.query(Material).filter(Material.id ==(project_id)
            if not project:
                raise HTTPException(
                    status_code=404,
                    detail={"error_type": "NOT_FOUND", "message": "Project not found"}
                )
        else:
            project = None
            project_id = None

        # 解析请求数据（兼容JSON/表单）
        if json_data:
            prompt = json_data.get('prompt', '').strip()
            ref_image = None
            extra_images = []
        else:
            prompt = (prompt or '').strip()

        if not prompt:
            raise HTTPException(
                status_code=400,
                detail={"error_type": "BAD_REQUEST", "message": "prompt is required"}
            )

        # 处理任务的project_id（Task不允许null）
        task_project_id = project_id if project_id is not None else 'global'
        if task_project_id != 'global':
            project = PPTProject.query(Material).filter(Material.id ==(task_project_id)
            if not project:
                raise HTTPException(
                    status_code=404,
                    detail={"error_type": "NOT_FOUND", "message": "Project not found"}
                )

        # 初始化服务
        ai_service = AIService()
        upload_folder = get_upload_folder(request)
        file_service = FileService(upload_folder)

        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp(dir=upload_folder))
        temp_dir_str = str(temp_dir)

        try:
            # 保存参考图
            ref_path_str = None
            if ref_image and ref_image.filename:
                # 安全文件名清理
                clean_name = re.sub(r'[^\w\-_\.]', '_', ref_image.filename or 'ref.png')
                ref_filename = clean_name.strip('.').replace('..', '_')
                ref_path = temp_dir / ref_filename
                with open(str(ref_path), "wb") as f:
                    f.write(ref_image.file.read())
                ref_path_str = str(ref_path)

            # 保存额外参考图
            additional_ref_images = []
            for extra in extra_images:
                if not extra or not extra.filename:
                    continue
                # 安全文件名清理
                clean_name = re.sub(r'[^\w\-_\.]', '_', extra.filename)
                extra_filename = clean_name.strip('.').replace('..', '_')
                extra_path = temp_dir / extra_filename
                with open(str(extra_path), "wb") as f:
                    f.write(extra.file.read())
                additional_ref_images.append(str(extra_path))

            # 创建异步任务
            task = Task(
                project_id=task_project_id,
                task_type='GENERATE_MATERIAL',
                status='PENDING'
            )
            task.set_progress({
                'total': 1,
                'completed': 0,
                'failed': 0
            })
            db.session.add(task)
            db.session.commit()

            # 提交后台任务（复用原task_manager）
            app = request.app  # FastAPI获取app实例
            task_manager.submit_task(
                task.id,
                generate_material_image_task,
                task_project_id,
                prompt,
                ai_service,
                file_service,
                ref_path_str,
                additional_ref_images if additional_ref_images else None,
                request.app.state.config['DEFAULT_ASPECT_RATIO'],
                request.app.state.config['DEFAULT_RESOLUTION'],
                temp_dir_str,
                app
            )

            return {
                "success": True,
                "data": {"task_id": task.id, "status": "PENDING"},
                "message": "素材生成任务已提交"
            }
        
        except Exception as e:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        raise HTTPException(
            status_code=503,
            detail={"error_type": "AI_SERVICE_ERROR", "message": str(e)}
        )

@material_router.get(
    "/{project_id}/materials",
    response_model=MaterialListResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def list_materials(project_id: str = Path(..., description="项目ID")):
    """GET /api/projects/{project_id}/materials - 查询指定项目的素材列表"""
    try:
        materials_list, error = _get_materials_list(project_id)
        if error:
            raise error
        
        return {
            "materials": materials_list,
            "count": len(materials_list)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error_type": "SERVER_ERROR", "message": str(e)}
        )

@material_router.post(
    "/{project_id}/materials/upload",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_material(
    request: Request,
    project_id: str = Path(..., description="项目ID")
):
    """POST /api/projects/{project_id}/materials/upload - 上传项目关联的素材"""
    return await _handle_material_upload(request, default_project_id=project_id)

# ------------------------------
# 全局维度素材接口
# ------------------------------
@material_global_router.get(
    "",
    response_model=MaterialListResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def list_all_materials(
    project_id: str = Query("all", description="过滤维度：all/none/具体项目ID")
):
    """GET /api/materials - 全局素材查询"""
    try:
        materials_list, error = _get_materials_list(project_id)
        if error:
            raise error
        
        return {
            "materials": materials_list,
            "count": len(materials_list)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error_type": "SERVER_ERROR", "message": str(e)}
        )

@material_global_router.post(
    "/upload",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_material_global(request: Request):
    """POST /api/materials/upload - 上传全局素材（不绑定项目）"""
    return await _handle_material_upload(request, default_project_id=None)

@material_global_router.delete(
    "/{material_id}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def delete_material(
    request: Request,
    material_id: str = Path(..., description="素材ID")
):
    """DELETE /api/materials/{material_id} - 删除素材（数据库+文件）"""
    try:
        material = Material.query(Material).filter(Material.id ==(material_id)
        if not material:
            raise HTTPException(
                status_code=404,
                detail={"error_type": "NOT_FOUND", "message": "Material not found"}
            )

        # 删除数据库记录
        db.session.delete(material)
        db.session.commit()

        # 删除文件（失败仅日志）
        upload_folder = get_upload_folder(request)
        file_service = FileService(upload_folder)
        material_path = Path(file_service.get_absolute_path(material.relative_path))
        try:
            if material_path.exists():
                material_path.unlink(missing_ok=True)
        except OSError as e:
            request.app.logger.warning(f"删除素材文件失败 {material_id}: {e}")

        return {
            "success": True,
            "data": {"id": material_id},
            "message": "素材删除成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_type": "SERVER_ERROR", "message": str(e)}
        )

@material_global_router.post(
    "/associate",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def associate_materials_to_project(
    request: Request,
    data: AssociateMaterialRequest = Body(...)
):
    """POST /api/materials/associate - 将全局素材关联到指定项目"""
    try:
        project_id = data.project_id
        material_urls = data.material_urls

        # 验证项目
        project = Project.query(Material).filter(Material.id ==(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail={"error_type": "NOT_FOUND", "message": "Project not found"}
            )
        
        # 更新素材的project_id
        updated_ids = []
        materials_to_update = Material.query.filter(
            Material.url.in_(material_urls),
            Material.project_id.is_(None)
        ).all()
        for material in materials_to_update:
            material.project_id = project_id
            updated_ids.append(material.id)
        
        db.session.commit()
        
        return {
            "success": True,
            "data": {"updated_ids": updated_ids, "count": len(updated_ids)},
            "message": "素材关联成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error_type": "SERVER_ERROR", "message": str(e)}
        )
