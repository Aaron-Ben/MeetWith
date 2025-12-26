"""
File api
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Path as FastAPIPath
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from werkzeug.utils import secure_filename

# 适配项目结构的导入
from app.config.settings import settings  # 全局配置
from app.utils.response import error_response  # 统一响应工具
from app.utils.path_utils import find_file_with_prefix  # 路径前缀匹配工具

# 初始化日志
import logging
logger = logging.getLogger(__name__)

file_router = APIRouter(prefix="/files", tags=["Static Files"])

# ------------------------------ 核心文件服务接口 ------------------------------
@file_router.get("/{project_id}/{file_type}/{filename}")
async def serve_file(
    project_id: str = FastAPIPath(..., description="项目UUID"),
    file_type: str = FastAPIPath(..., description="文件类型：template/pages/materials/exports"),
    filename: str = FastAPIPath(..., description="文件名")
):
    """
    提供项目相关静态文件访问
    GET /files/{project_id}/{file_type}/{filename}
    """
    try:
        # 校验文件类型
        if file_type not in ['template', 'pages', 'materials', 'exports']:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 构建文件目录路径
        file_dir = Path(settings.UPLOAD_FOLDER) / project_id / file_type
        
        # 检查目录是否存在
        if not file_dir.exists() or not file_dir.is_dir():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 构建完整文件路径
        file_path = file_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 安全校验：确保文件路径在允许的目录内（防路径遍历）
        try:
            resolved_file_path = file_path.resolve(strict=True)
            resolved_file_dir = file_dir.resolve(strict=True)
            if not str(resolved_file_path).startswith(str(resolved_file_dir)):
                raise HTTPException(status_code=403, detail="Invalid file path")
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid file path")
        
        # 返回文件响应
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Serve file error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)

# ------------------------------ 用户模板文件服务 ------------------------------
@file_router.get("/user-templates/{template_id}/{filename}")
async def serve_user_template(
    template_id: str = FastAPIPath(..., description="模板UUID"),
    filename: str = FastAPIPath(..., description="文件名")
):
    """
    提供用户模板文件访问
    GET /files/user-templates/{template_id}/{filename}
    """
    try:
        # 构建文件目录路径
        file_dir = Path(settings.UPLOAD_FOLDER) / "user-templates" / template_id
        
        # 检查目录是否存在
        if not file_dir.exists() or not file_dir.is_dir():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 构建完整文件路径
        file_path = file_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 安全校验：防路径遍历
        try:
            resolved_file_path = file_path.resolve(strict=True)
            resolved_file_dir = file_dir.resolve(strict=True)
            if not str(resolved_file_path).startswith(str(resolved_file_dir)):
                raise HTTPException(status_code=403, detail="Invalid file path")
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid file path")
        
        # 返回文件响应
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Serve user template error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)

# ------------------------------ 全局物料文件服务 ------------------------------
@file_router.get("/materials/{filename}")
async def serve_global_material(
    filename: str = FastAPIPath(..., description="文件名")
):
    """
    提供全局物料文件访问（不绑定项目）
    GET /files/materials/{filename}
    """
    try:
        # 安全处理文件名
        safe_filename = secure_filename(filename)
        
        # 构建文件目录路径
        file_dir = Path(settings.UPLOAD_FOLDER) / "materials"
        
        # 检查目录是否存在
        if not file_dir.exists() or not file_dir.is_dir():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 构建完整文件路径
        file_path = file_dir / safe_filename
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 安全校验：防路径遍历
        try:
            resolved_file_path = file_path.resolve(strict=True)
            resolved_file_dir = file_dir.resolve(strict=True)
            if not str(resolved_file_path).startswith(str(resolved_file_dir)):
                raise HTTPException(status_code=403, detail="Invalid file path")
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid file path")
        
        # 返回文件响应
        return FileResponse(
            path=str(file_path),
            filename=safe_filename,
            media_type="application/octet-stream"
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Serve global material error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)

# ------------------------------ MinerU 文件服务 ------------------------------
@file_router.get("/mineru/{extract_id}/{filepath:path}")
async def serve_mineru_file(
    extract_id: str = FastAPIPath(..., description="MinerU 提取ID"),
    filepath: str = FastAPIPath(..., description="提取目录内的相对文件路径")
):
    """
    提供 MinerU 解析结果文件访问（支持子路径）
    GET /files/mineru/{extract_id}/{filepath}
    """
    try:
        # 构建根目录路径
        root_dir = Path(settings.UPLOAD_FOLDER) / "mineru_files" / extract_id
        
        # 构建完整文件路径
        full_path = root_dir / filepath
        
        # 安全校验：防路径遍历（核心安全逻辑）
        try:
            resolved_root_dir = root_dir.resolve(strict=True)
            resolved_full_path = full_path.resolve()
            
            # 检查路径是否超出允许的根目录
            if not str(resolved_full_path).startswith(str(resolved_root_dir)):
                raise HTTPException(status_code=403, detail="Invalid file path")
        except FileNotFoundError:
            # 文件不存在，继续执行前缀匹配逻辑
            pass
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid file path")
        
        # 尝试查找前缀匹配的文件（原有核心逻辑）
        matched_path = find_file_with_prefix(full_path)
        
        if matched_path is not None:
            # 对匹配到的路径进行二次安全校验
            try:
                resolved_matched_path = matched_path.resolve(strict=True)
                
                # 验证匹配到的文件仍在根目录内
                if not str(resolved_matched_path).startswith(str(resolved_root_dir)):
                    raise HTTPException(status_code=403, detail="Invalid file path")
                
                # 返回匹配到的文件
                return FileResponse(
                    path=str(resolved_matched_path),
                    filename=matched_path.name,
                    media_type="application/octet-stream"
                )
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="File not found")
            except Exception:
                raise HTTPException(status_code=403, detail="Invalid file path")
        
        # 未找到匹配文件
        raise HTTPException(status_code=404, detail="File not found")
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Serve mineru file error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)