"""
导出生成的文件
"""
import logging
import os

from app.models.database import get_db
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# 适配项目结构的导入
from app.config import Config
from app.models.ppt.project import PPTProject
from app.models.ppt.page import Page
from app.services.ppt.export import ExportService
from app.services.ppt.file import FileService
from app.services.ppt.file_parser import FileParser
from app.utils.response import success_response, error_response

# 初始化日志
logger = logging.getLogger(__name__)

export_router = APIRouter(prefix="/api/projects", tags=["Export"])


# ------------------------------ 基础导出接口 ------------------------------
@export_router.get("/{project_id}/export/pptx", response_class=JSONResponse)
async def export_pptx(
    request: Request,
    project_id: str,
    filename: str = Query(default=None, description="Export filename (with .pptx)"),
    db: Session = Depends(get_db)
):
    """
    导出项目为 PPTX 文件
    GET /api/projects/{project_id}/export/pptx
    """
    try:
        # 查询项目
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="PPTProject not found")

        # 获取项目下所有页面（按排序索引）
        pages = db.query(Page).filter(
            Page.project_id == project_id
        ).order_by(Page.order_index).all()

        if not pages:
            raise HTTPException(status_code=400, detail="No pages found for project")

        # 获取图片路径
        file_service = FileService(Config.UPLOAD_FOLDER)
        image_paths = []
        
        for page in pages:
            if page.generated_image_path:
                abs_path = file_service.get_absolute_path(page.generated_image_path)
                image_paths.append(abs_path)

        if not image_paths:
            raise HTTPException(status_code=400, detail="No generated images found for project")

        # 处理文件名
        if not filename:
            filename = f"presentation_{project_id}.pptx"
        if not filename.endswith('.pptx'):
            filename += '.pptx'

        # 确定导出目录和输出路径
        exports_dir = file_service._get_exports_dir(project_id)
        output_path = os.path.join(exports_dir, filename)

        # 生成 PPTX 文件
        ExportService.create_pptx_from_images(image_paths, output_file=output_path)

        # 构建下载 URL
        download_path = f"/files/{project_id}/exports/{filename}"
        base_url = str(request.base_url).rstrip("/")
        download_url_absolute = f"{base_url}{download_path}"

        return success_response(
            data={
                "download_url": download_path,
                "download_url_absolute": download_url_absolute,
            },
            message="Export PPTX task created"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Export PPTX error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


@export_router.get("/{project_id}/export/pdf", response_class=JSONResponse)
async def export_pdf(
    request: Request,
    project_id: str,
    filename: str = Query(default=None, description="Export filename (with .pdf)"),
    db: Session = Depends(get_db)
):
    """
    导出项目为 PDF 文件
    GET /api/projects/{project_id}/export/pdf
    """
    try:
        # 查询项目
        project = db.query(PPTProject).filter(PPTProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 获取项目下所有页面（按排序索引）
        pages = db.query(Page).filter(
            Page.project_id == project_id
        ).order_by(Page.order_index).all()

        if not pages:
            raise HTTPException(status_code=400, detail="No pages found for project")

        # 获取图片路径
        file_service = FileService(Config.UPLOAD_FOLDER)
        image_paths = []
        
        for page in pages:
            if page.generated_image_path:
                abs_path = file_service.get_absolute_path(page.generated_image_path)
                image_paths.append(abs_path)

        if not image_paths:
            raise HTTPException(status_code=400, detail="No generated images found for project")

        # 处理文件名
        if not filename:
            filename = f"presentation_{project_id}.pdf"
        if not filename.endswith('.pdf'):
            filename += '.pdf'

        # 确定导出目录和输出路径
        exports_dir = file_service._get_exports_dir(project_id)
        output_path = os.path.join(exports_dir, filename)

        # 生成 PDF 文件
        ExportService.create_pdf_from_images(image_paths, output_file=output_path)

        # 构建下载 URL
        download_path = f"/files/{project_id}/exports/{filename}"
        base_url = str(request.base_url).rstrip("/")
        download_url_absolute = f"{base_url}{download_path}"

        return success_response(
            data={
                "download_url": download_path,
                "download_url_absolute": download_url_absolute,
            },
            message="Export PDF task created"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Export PDF error: {str(e)}", exc_info=True)
        return error_response(f"SERVER_ERROR: {str(e)}", 500)


'''
# ------------------------------ 可编辑 PPTX 导出接口 ------------------------------
@export_router.get("/{project_id}/export/editable-pptx", response_class=JSONResponse)
async def export_editable_pptx(
    request: Request,
    project_id: str,
    filename: Optional[str] = Query(None, description="导出的可编辑PPTX文件名"),
    db: Session = Depends(get_db)
):
    导出可编辑的 PPTX 文件（基于 MinerU 解析）
    GET /api/projects/{project_id}/export/editable-pptx
    
    流程：
    1. 收集所有页面图片
    2. 并行生成干净背景图（移除文字/图标）
    3. 将图片转为临时 PDF
    4. 调用 MinerU 解析 PDF
    5. 基于 MinerU 结果生成可编辑 PPTX
    # 初始化临时文件路径（用于finally清理）
    tmp_pdf_path = None
    clean_background_paths = []

    try:
        # 查询项目
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 获取项目下所有页面（按排序索引）
        pages = db.query(Page).filter(
            Page.project_id == project_id
        ).order_by(Page.order_index).all()

        if not pages:
            raise HTTPException(status_code=400, detail="No pages found for project")

        # 获取图片路径
        file_service = FileService(settings.UPLOAD_FOLDER)
        image_paths = []
        
        for page in pages:
            if page.generated_image_path:
                abs_path = file_service.get_absolute_path(page.generated_image_path)
                image_paths.append(abs_path)

        if not image_paths:
            raise HTTPException(status_code=400, detail="No generated images found for project")

        # ------------------------------ 步骤1：并行生成干净背景图 ------------------------------
        logger.info(f"Generating clean backgrounds for {len(image_paths)} images in parallel...")
        
        # 获取全局配置
        aspect_ratio = settings.DEFAULT_ASPECT_RATIO
        resolution = settings.DEFAULT_RESOLUTION
        max_workers = min(len(image_paths), settings.MAX_IMAGE_WORKERS)

        def generate_single_background(index: int, original_image_path: str):
            """生成单张图片的干净背景（线程池执行）"""
            try:
                logger.info(f"Processing background {index+1}/{len(image_paths)}...")
                ai_service = AIService()
                
                clean_bg_path = ExportService.generate_clean_background(
                    original_image_path=original_image_path,
                    ai_service=ai_service,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution
                )
                
                if clean_bg_path:
                    logger.info(f"Clean background {index+1} generated successfully")
                    return (index, clean_bg_path)
                else:
                    logger.warning(f"Failed to generate clean background {index+1}, using original image")
                    return (index, original_image_path)
            except Exception as e:
                logger.error(f"Error generating background {index+1}: {str(e)}")
                return (index, original_image_path)  # 失败时回退到原图

        # 并行处理背景图
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(generate_single_background, i, path): i 
                for i, path in enumerate(image_paths)
            }
            
            for future in as_completed(futures):
                index = futures[future]
                try:
                    idx, bg_path = future.result()
                    results[idx] = bg_path
                except Exception as e:
                    logger.error(f"Future error for index {index}: {str(e)}")
                    results[index] = image_paths[index]

        # 按索引排序，保证页面顺序
        clean_background_paths = [results[i] for i in range(len(image_paths))]
        logger.info(f"Generated {len(clean_background_paths)} clean backgrounds (parallel processing completed)")

        # ------------------------------ 步骤2：生成临时 PDF ------------------------------
        # 创建临时 PDF 文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name
        
        logger.info(f"Creating PDF from {len(image_paths)} images...")
        ExportService.create_pdf_from_images(image_paths, output_file=tmp_pdf_path)
        logger.info(f"PDF created: {tmp_pdf_path}")

        # ------------------------------ 步骤3：调用 MinerU 解析 PDF ------------------------------
        logger.info("Parsing PDF with MinerU...")
        
        # 校验 MinerU 配置
        if not settings.MINERU_TOKEN:
            raise HTTPException(status_code=500, detail="MinerU token not configured")

        # 初始化解析服务
        parser_service = FileParser(
            mineru_token=settings.MINERU_TOKEN,
            mineru_api_base=settings.MINERU_API_BASE
        )

        # 解析 PDF
        batch_id, markdown_content, extract_id, error_message, failed_image_count = parser_service._parse_file(
            file_path=tmp_pdf_path,
            filename=f'presentation_{project_id}.pdf'
        )
        
        if error_message or not extract_id:
            error_msg = error_message or 'Failed to parse PDF with MinerU - no extract_id returned'
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"MinerU parsing completed, extract_id: {extract_id}")

        # ------------------------------ 步骤4：生成可编辑 PPTX ------------------------------
        # 检查 MinerU 结果目录
        mineru_result_dir = os.path.join(
            settings.UPLOAD_FOLDER,
            'mineru_files',
            extract_id
        )
        
        if not os.path.exists(mineru_result_dir):
            raise HTTPException(status_code=500, detail=f'MinerU result directory not found: {mineru_result_dir}')
        
        logger.info(f"Creating editable PPTX from MinerU results: {mineru_result_dir}")

        # 处理文件名
        if not filename:
            filename = f"presentation_editable_{project_id}.pptx"
        if not filename.endswith('.pptx'):
            filename += '.pptx'

        # 确定导出目录和输出路径
        exports_dir = file_service._get_exports_dir(project_id)
        output_path = os.path.join(exports_dir, filename)

        # 获取幻灯片尺寸（从第一张图片）
        with Image.open(image_paths[0]) as first_img:
            slide_width, slide_height = first_img.size

        logger.info(f"Creating editable PPTX with {len(clean_background_paths)} clean background images")
        ExportService.create_editable_pptx_from_mineru(
            mineru_result_dir=mineru_result_dir,
            output_file=output_path,
            slide_width_pixels=slide_width,
            slide_height_pixels=slide_height,
            background_images=clean_background_paths
        )
        
        logger.info(f"Editable PPTX created: {output_path}")

        # 构建下载 URL
        download_path = f"/files/{project_id}/exports/{filename}"
        base_url = str(request.base_url).rstrip("/")
        download_url_absolute = f"{base_url}{download_path}"

        return success_response(
            data={
                "download_url": download_path,
                "download_url_absolute": download_url_absolute,
            },
            message="Editable PPTX export completed"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Error exporting editable PPTX")
        return error_response(f"SERVER_ERROR: {str(e)}", 500)
    finally:
        # ------------------------------ 清理临时文件 ------------------------------
        # 清理临时 PDF
        if tmp_pdf_path and os.path.exists(tmp_pdf_path):
            try:
                os.unlink(tmp_pdf_path)
                logger.info(f"Cleaned up temporary PDF: {tmp_pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary PDF: {str(e)}")
        
        # 清理临时背景图（仅清理非原图的临时文件）
        if clean_background_paths:
            for bg_path in clean_background_paths:
                if bg_path not in image_paths and os.path.exists(bg_path):
                    try:
                        os.unlink(bg_path)
                        logger.debug(f"Cleaned up temporary background: {bg_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary background: {str(e)}")

'''               