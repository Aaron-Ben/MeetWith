"""
上传文件api
"""
import os
import logging
import re
import uuid
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote
from typing import Optional, List, Dict, Any

from app.config import Config
from app.models.database import SessionLocal, get_db
from app.models.ppt.project import PPTProject
from app.models.refernce_file import ReferenceFile
from app.services.ppt.file_parser import FileParser
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)

reference_file_router = APIRouter(
    prefix="/api/reference-files",
    tags=["reference_files"]
)


# Pydantic模型定义请求体结构
class AssociateRequest(BaseModel):
    project_id: str


# 工具函数
# 检查文件扩展名
def _allowed_file(filename: str, allowed_extensions: set) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 获取文件类型
def _get_file_type(filename: str) -> str:
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return 'unknown'

# 异步解析文件
def _parse_file_async(file_id: str, file_path: str, filename: str, app) -> None:
    """
    后台任务运行的文件解析逻辑
    """

    db = SessionLocal()
    try:
        reference_file = db.query(ReferenceFile).get(file_id)
        if not reference_file:
            logger.error(f"Reference file {file_id} not found")
            return

        reference_file.parse_status = 'parsing'
        db.commit()

        parser = FileParser(
            mineru_token=Config['MINERU_TOKEN'],
            mineru_api_base=Config['MINERU_API_BASE'],
            google_api_key=Config['GOOGLE_API_KEY'],
            google_api_base=Config['GOOGLE_API_BASE'],
            openai_api_key=Config['OPENAI_API_KEY'],
            openai_api_base=Config['OPENAI_API_BASE'],
            image_caption_model=Config['IMAGE_CAPTION_MODEL'],
            provider_format=Config.get('AI_PROVIDER_FORMAT', 'gemini')
        )

        logger.info(f"Starting to parse file: {filename}")
        batch_id, markdown_content, extract_id, error_message, failed_image_count = parser._parse_file(file_path, filename)

        reference_file.mineru_batch_id = batch_id
        if error_message:
            reference_file.parse_status = 'failed'
            reference_file.error_message = error_message
            logger.error(f"File parsing failed: {error_message}")
        else:
            reference_file.parse_status = 'completed'
            reference_file.markdown_content = markdown_content
            if failed_image_count > 0:
                logger.warning(f"File parsing completed: {filename}, but {failed_image_count} images failed")

        reference_file.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Error in async file parsing: {str(e)}", exc_info=True)
        try:
            db = SessionLocal()
            reference_file = db.query(ReferenceFile).get(file_id)
            if reference_file:
                reference_file.parse_status = 'failed'
                reference_file.error_message = f"Parsing error: {str(e)}"
                reference_file.updated_at = datetime.utcnow()
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {str(db_error)}")
    finally:
        db.close()


@reference_file_router.post("/upload", response_class=JSONResponse)
def upload_reference_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """上传参考文件"""
    try:
        original_filename = file.filename
        if not original_filename:
            content_disposition = file.headers.get('content-disposition', '')
            if content_disposition:
                filename_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
                if filename_match:
                    original_filename = filename_match.group(1).strip('"\'')
                    try:
                        original_filename = unquote(original_filename)
                    except:
                        pass

        if not original_filename:
            raise HTTPException(status_code=400, detail="No file selected or filename could not be determined")

        logger.info(f"Received file upload: {original_filename}")

        allowed_extensions = Config.ALLOWED_REFERENCE_FILE_EXTENSIONS
        if not _allowed_file(original_filename, allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )

        # 处理project_id
        if project_id in ['none', '']:
            project_id = None
        else:
            if project_id and not db.query(PPTProject).get(project_id):
                raise HTTPException(status_code=404, detail="Project not found")

        # 处理文件名
        filename = original_filename
        if not filename:
            ext = _get_file_type(original_filename) or 'file'
            filename = f"file_{uuid.uuid4().hex[:8]}.{ext}"
            logger.warning(f"Sanitized filename to: {filename}")

        # 保存文件
        upload_folder = Config.UPLOAD_FOLDER
        reference_files_dir = Path(upload_folder) / 'reference_files'
        reference_files_dir.mkdir(parents=True, exist_ok=True)

        unique_id = str(uuid.uuid4())[:8]
        file_type = _get_file_type(original_filename)
        unique_filename = f"{unique_id}_{filename}"
        file_path = reference_files_dir / unique_filename

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        file_size = os.path.getsize(file_path)

        # 创建数据库记录
        reference_file = ReferenceFile(
            project_id=project_id,
            filename=original_filename,
            file_path=str(file_path.relative_to(upload_folder)),
            file_size=file_size,
            file_type=file_type,
            parse_status='pending'
        )
        db.add(reference_file)
        db.commit()
        db.refresh(reference_file)

        logger.info(f"File uploaded: {original_filename} (ID: {reference_file.id})")
        return {"status": "success", "data": {"file": reference_file.to_dict()}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading reference file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@reference_file_router.get("/{file_id}", response_class=JSONResponse)
def get_reference_file(file_id: str, db: Session = Depends(get_db)):
    """获取文件详情"""
    reference_file = db.query(ReferenceFile).get(file_id)
    if not reference_file:
        raise HTTPException(status_code=404, detail="Reference file not found")
    
    return {
        "status": "success",
        "data": {"file": reference_file.to_dict(include_content=True, include_failed_count=True)}
    }


@reference_file_router.delete("/{file_id}", response_class=JSONResponse)
def delete_reference_file(file_id: str, db: Session = Depends(get_db)):
    """删除文件"""
    reference_file = db.query(ReferenceFile).get(file_id)
    if not reference_file:
        raise HTTPException(status_code=404, detail="Reference file not found")

    # 删除磁盘文件
    try:
        file_path = Path(Config.UPLOAD_FOLDER) / reference_file.file_path
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file from disk: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete file from disk: {str(e)}")

    # 删除数据库记录
    db.delete(reference_file)
    db.commit()
    return {"status": "success", "data": {"message": "File deleted successfully"}}


@reference_file_router.get("/project/{project_id}", response_class=JSONResponse)
def list_project_reference_files(project_id: str, db: Session = Depends(get_db)):
    """列出项目关联的文件"""
    try:
        if project_id == 'all':
            reference_files = db.query(ReferenceFile).all()
        elif project_id in ['global', 'none']:
            reference_files = db.query(ReferenceFile).filter_by(project_id=None).all()
        else:
            if not db.query(PPTProject).get(project_id):
                raise HTTPException(status_code=404, detail="Project not found")
            reference_files = db.query(ReferenceFile).filter_by(project_id=project_id).all()

        return {
            "status": "success",
            "data": {"files": [f.to_dict(include_content=False) for f in reference_files]}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing reference files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SERVER_ERROR: {str(e)}")


@reference_file_router.post("/{file_id}/parse", response_class=JSONResponse)
def trigger_file_parse(file_id: str, db: Session = Depends(get_db)):
    """触发文件解析"""
    reference_file = db.query(ReferenceFile).get(file_id)
    if not reference_file:
        raise HTTPException(status_code=404, detail="Reference file not found")

    if reference_file.parse_status == 'parsing':
        return {
            "status": "success",
            "data": {
                "file": reference_file.to_dict(),
                "message": "File is already being parsed"
            }
        }

    # 重置解析状态
    if reference_file.parse_status in ['completed', 'failed']:
        reference_file.parse_status = 'pending'
        reference_file.error_message = None
        reference_file.markdown_content = None
        reference_file.mineru_batch_id = None
        db.commit()

    # 检查文件是否存在
    file_path = Path(Config.UPLOAD_FOLDER) / reference_file.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"FILE_NOT_FOUND: {file_path}")

    # 启动异步解析（传递None作为app，因为解析函数不实际使用它）
    thread = threading.Thread(
        target=_parse_file_async,
        args=(reference_file.id, str(file_path), reference_file.filename, None)
    )
    thread.daemon = True
    thread.start()

    logger.info(f"Triggered parsing for file: {reference_file.filename} (ID: {file_id})")
    return {
        "status": "success",
        "data": {
            "file": reference_file.to_dict(),
            "message": "Parsing started"
        }
    }


@reference_file_router.post("/{file_id}/associate", response_class=JSONResponse)
def associate_file_to_project(
    file_id: str,
    data: AssociateRequest,
    db: Session = Depends(get_db)
):
    """关联文件到项目"""
    reference_file = db.query(ReferenceFile).get(file_id)
    if not reference_file:
        raise HTTPException(status_code=404, detail="Reference file not found")

    project = db.query(PPTProject).get(data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    reference_file.project_id = data.project_id
    reference_file.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reference_file)

    return {"status": "success", "data": {"file": reference_file.to_dict()}}


@reference_file_router.post("/{file_id}/dissociate", response_class=JSONResponse)
def dissociate_file_from_project(file_id: str, db: Session = Depends(get_db)):
    """解除文件与项目的关联"""
    reference_file = db.query(ReferenceFile).get(file_id)
    if not reference_file:
        raise HTTPException(status_code=404, detail="Reference file not found")

    reference_file.project_id = None
    reference_file.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reference_file)

    return {
        "status": "success",
        "data": {
            "file": reference_file.to_dict(),
            "message": "File removed from project"
        }
    }