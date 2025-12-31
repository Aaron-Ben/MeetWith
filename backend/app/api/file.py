"""
文件服务相关接口
"""
import os
from pathlib import Path

from app.config import Config
from fastapi import APIRouter, HTTPException, Path as FastAPIPath
from fastapi.responses import FileResponse

# 适配项目结构的导入
from app.utils.response import error_response  # 统一响应工具

# 初始化日志
import logging
logger = logging.getLogger(__name__)

file_router = APIRouter(prefix="/files", tags=["files"])

@file_router.get("/{project_id}/{file_type}/{filename}")
async def serve_file(
    project_id: str,
    file_type: str,
    filename: str
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
        file_dir = Path(Config.UPLOAD_FOLDER) / project_id / file_type
        
        # 检查目录是否存在
        if not file_dir.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 构建完整文件路径
        file_path = file_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists():
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
    template_id: str,
    filename: str
):
    """
    提供用户模板文件访问
    GET /files/user-templates/{template_id}/{filename}
    """
    try:
        # 构建文件目录路径
        file_dir = Path(Config.UPLOAD_FOLDER) / "user-templates" / template_id
        
        # 检查目录是否存在
        if not file_dir.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 构建完整文件路径
        file_path = file_dir / filename

        # 检查文件是否存在
        if not file_path.exists():
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
    filename: str
):
    """
    提供全局物料文件访问（不绑定项目）
    GET /files/materials/{filename}
    """
    try:
        # 构建文件目录路径
        file_dir = Path(Config.UPLOAD_FOLDER) / "materials"
        
        # 检查目录是否存在
        if not file_dir.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 构建完整文件路径
        file_path = file_dir / filename
        
        # 检查文件是否存在
        if not file_path.exists():
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
        logger.error(f"Serve global material error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)

# ------------------------------ MinerU 文件服务 ------------------------------
@file_router.get("/mineru/{extract_id}/{filepath:path}")
async def serve_mineru_file(
    extract_id: str,
    filepath: str
):
    """
    提供 MinerU 解析结果文件访问（支持子路径）
    GET /files/mineru/{extract_id}/{filepath}
    """
    try:
        # 构建根目录路径
        root_dir = Path(Config.UPLOAD_FOLDER) / "mineru_files" / extract_id
        
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
        
        
        if full_path is not None:
            # 对匹配到的路径进行二次安全校验
            try:
                resolved_matched_path = full_path.resolve(strict=True)
                
                # 验证匹配到的文件仍在根目录内
                if not str(resolved_matched_path).startswith(str(resolved_root_dir)):
                    raise HTTPException(status_code=403, detail="Invalid file path")
                
                # 返回匹配到的文件
                return FileResponse(
                    path=str(resolved_matched_path),
                    filename=full_path.name,
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

        