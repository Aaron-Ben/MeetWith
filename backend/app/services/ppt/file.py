"""
后台所有文件（图片，模版，导出文件的统一管理）
文件结构
uploads/
    {project_id}/
        template/       # 模版
        pages/          # ppt 页面  
        materials/      # 素材
        exports/        # 导出文件
    materials/          # 全局素材（没有 project_id）
    user-templates/     # 用户模版
        {template_id}/

"""
import os
import time
import shutil
import uuid
from pathlib import Path
from PIL import Image
from fastapi import HTTPException, UploadFile


class FileService:

    def __init__(self, upload_folder:str):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    # upload/{project_id}
    def _get_project_dir(self, project_id: str) -> Path:
        project_dir = self.upload_folder / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    # upload/{project_id}/template
    def _get_template_dir(self, project_id: str) -> Path:
        template_dir = self._get_project_dir(project_id) / "template"
        template_dir.mkdir(parents=True, exist_ok=True)
        return template_dir

    # upload/{project_id}/pages
    def _get_pages_dir(self, project_id: str) -> Path:
        pages_dir = self._get_project_dir(project_id) / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        return pages_dir

    # upload/{project_id}/materials
    def _get_materials_dir(self, project_id: str) -> Path:
        materials_dir = self._get_project_dir(project_id) / "materials"
        materials_dir.mkdir(parents=True, exist_ok=True)
        return materials_dir

    # upload/{project_id}/exports
    def _get_exports_dir(self, project_id: str) -> Path:
        exports_dir = self._get_project_dir(project_id) / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        return exports_dir

    # 保存模版图片
    async def save_template_image(self, project_id: str, file: UploadFile) -> str:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        template_dir = self._get_template_dir(project_id)

        filename = file.filename
        if not filename:
            raise HTTPException(status_code=400, detail="File must have a filename")

        ext = file.content_type.split("/")[-1].lower() if file.content_type else "png"
        if not ext or ext not in ["png", "jpg", "jpeg", "gif"]:
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else "png"

        # 模板文件固定命名
            save_filename = f"template.{ext}"
            filepath = template_dir / save_filename
            
            # 异步保存文件（FastAPI推荐方式）
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # 返回相对路径（POSIX格式，兼容前端）
            relative_path = filepath.relative_to(self.upload_folder).as_posix()
            return relative_path


    def save_generated_image(self, image: Image.Image, project_id: str, 
                           page_id: str, image_format: str = 'PNG', 
                           version_number: int = None) -> str:
        """
        Save generated image with version support (sync version for PIL)
        
        Args:
            image: PIL Image object
            project_id: Project ID
            page_id: Page ID
            image_format: Image format (PNG, JPEG, etc.)
            version_number: Optional version number. If None, uses timestamp-based naming
        
        Returns:
            Relative file path from upload folder
        
        Raises:
            HTTPException: If save fails
        """
        try:
            pages_dir = self._get_pages_dir(project_id)
            
            # 标准化扩展名
            ext = image_format.lower()
            valid_formats = ["png", "jpg", "jpeg", "webp", "gif"]
            if ext not in valid_formats:
                ext = "png"
            
            # 生成带版本号或时间戳的文件名
            if version_number is not None:
                filename = f"{page_id}_v{version_number}.{ext}"
            else:
                timestamp = int(time.time() * 1000)  # 毫秒级时间戳
                filename = f"{page_id}_{timestamp}.{ext}"
            
            filepath = pages_dir / filename
            
            # 保存PIL图片（处理JPEG的RGB转换）
            save_kwargs = {}
            if ext in ["jpg", "jpeg"]:
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                save_kwargs["quality"] = 95
            
            image.save(str(filepath), format=image_format.upper(), **save_kwargs)
            
            # 返回相对路径
            return filepath.relative_to(self.upload_folder).as_posix()
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save generated image: {str(e)}")

    def save_material_image(self, image: Image.Image, project_id: Optional[str],
                            image_format: str = 'PNG') -> str:
        """
        Save standalone generated material image (not bound to a specific page)

        Args:
            image: PIL Image object
            project_id: Project ID (None for global materials)
            image_format: Image format (PNG, JPEG, etc.)

        Returns:
            Relative file path from upload folder
        
        Raises:
            HTTPException: If save fails
        """
        try:
            # 处理全局素材（无project_id）
            if project_id is None:
                materials_dir = self.upload_folder / "materials"
                materials_dir.mkdir(exist_ok=True, parents=True)
            else:
                materials_dir = self._get_materials_dir(project_id)

            # 标准化扩展名
            ext = image_format.lower()
            if ext not in ["png", "jpg", "jpeg", "webp"]:
                ext = "png"

            # 生成唯一文件名
            timestamp = int(time.time() * 1000)
            filename = f"material_{timestamp}.{ext}"
            filepath = materials_dir / filename

            # 保存图片
            save_kwargs = {}
            if ext in ["jpg", "jpeg"]:
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                save_kwargs["quality"] = 95
            
            image.save(str(filepath), format=image_format.upper(), **save_kwargs)

            # 返回相对路径
            return filepath.relative_to(self.upload_folder).as_posix()
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save material image: {str(e)}")
    
    def delete_page_image_version(self, image_path: str) -> bool:
        """
        Delete a specific image version file
        
        Args:
            image_path: Relative path to the image file
        
        Returns:
            True if deleted successfully
        
        Raises:
            HTTPException: If path is invalid
        """
        try:
            filepath = self.upload_folder / image_path.replace('\\', '/')
            # 安全校验：防止路径遍历攻击
            if not filepath.resolve().startswith(self.upload_folder.resolve()):
                raise HTTPException(status_code=403, detail="Invalid file path")
            
            if filepath.exists() and filepath.is_file():
                filepath.unlink()
                return True
            return False
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete image version: {str(e)}")
    
    def get_file_url(self, project_id: Optional[str], file_type: str, filename: str) -> str:
        """
        Generate file URL for frontend access (FastAPI static file path)
        
        Args:
            project_id: Project ID (None for global materials)
            file_type: 'template', 'pages', 'materials', 'exports' or 'user-templates'
            filename: File name
        
        Returns:
            URL path for file access (compatible with FastAPI StaticFiles)
        """
        # 安全校验文件类型
        valid_file_types = ["template", "pages", "materials", "exports", "user-templates"]
        if file_type not in valid_file_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Valid types: {valid_file_types}")
        
        if project_id is None:
            # 全局素材URL
            return f"/static/files/materials/{filename}"
        # 项目相关文件URL
        return f"/static/files/{project_id}/{file_type}/{filename}"
    
    def get_absolute_path(self, relative_path: str) -> str:
        """
        Get absolute file path from relative path
        
        Args:
            relative_path: Relative path from upload folder
        
        Returns:
            Absolute file path
        
        Raises:
            HTTPException: If path is invalid (path traversal)
        """
        try:
            filepath = self.upload_folder / relative_path.replace('\\', '/')
            # 关键安全校验：防止路径遍历攻击
            resolved_path = filepath.resolve()
            if not resolved_path.startswith(self.upload_folder.resolve()):
                raise HTTPException(status_code=403, detail="Path traversal detected")
            return str(resolved_path)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get absolute path: {str(e)}")
    
    def delete_template(self, project_id: str) -> bool:
        """
        Delete template for project
        
        Args:
            project_id: Project ID
        
        Returns:
            True if deleted successfully
        
        Raises:
            HTTPException: If delete fails
        """
        try:
            template_dir = self._get_template_dir(project_id)
            
            # 删除模板目录下所有文件
            for file in template_dir.iterdir():
                if file.is_file():
                    file.unlink()
            
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")
    
    def delete_page_image(self, project_id: str, page_id: str) -> bool:
        """
        Delete page image (all versions)
        
        Args:
            project_id: Project ID
            page_id: Page ID
        
        Returns:
            True if deleted successfully
        
        Raises:
            HTTPException: If delete fails
        """
        try:
            pages_dir = self._get_pages_dir(project_id)
            
            # 删除该page_id的所有版本文件
            deleted_count = 0
            for file in pages_dir.glob(f"{page_id}*.*"):
                if file.is_file():
                    file.unlink()
                    deleted_count += 1
            
            return deleted_count > 0
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete page image: {str(e)}")
    
    def delete_project_files(self, project_id: str) -> bool:
        """
        Delete all files for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            True if deleted successfully
        
        Raises:
            HTTPException: If delete fails
        """
        try:
            project_dir = self._get_project_dir(project_id)
            
            if project_dir.exists() and project_dir.is_dir():
                shutil.rmtree(project_dir)
            
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete project files: {str(e)}")
    
    def file_exists(self, relative_path: str) -> bool:
        """
        Check if file exists (with path traversal protection)
        
        Args:
            relative_path: Relative path from upload folder
        
        Returns:
            True if file exists
        
        Raises:
            HTTPException: If path is invalid
        """
        try:
            filepath = self.upload_folder / relative_path.replace('\\', '/')
            resolved_path = filepath.resolve()
            
            # 路径遍历保护
            if not resolved_path.startswith(self.upload_folder.resolve()):
                return False
            
            return resolved_path.exists() and resolved_path.is_file()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to check file existence: {str(e)}")
    
    def get_template_path(self, project_id: str) -> Optional[str]:
        """
        Get template file path for project
        
        Args:
            project_id: Project ID
        
        Returns:
            Absolute path to template file or None
        
        Raises:
            HTTPException: If path resolution fails
        """
        try:
            template_dir = self._get_template_dir(project_id)
            
            # 查找模板文件（template.*）
            for file in template_dir.iterdir():
                if file.is_file() and file.stem == 'template':
                    # 安全校验路径
                    resolved_path = file.resolve()
                    if resolved_path.startswith(self.upload_folder.resolve()):
                        return str(resolved_path)
            
            return None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get template path: {str(e)}")
    
    def _get_user_templates_dir(self) -> Path:
        """Get user templates directory"""
        templates_dir = self.upload_folder / "user-templates"
        templates_dir.mkdir(exist_ok=True, parents=True)
        return templates_dir
    
    async def save_user_template(self, file: UploadFile, template_id: str) -> str:
        """
        Save user template image file (FastAPI version)
        
        Args:
            file: UploadFile object from FastAPI request
            template_id: Template ID
        
        Returns:
            Relative file path from upload folder
        
        Raises:
            HTTPException: If save fails
        """
        try:
            # 验证文件类型
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            templates_dir = self._get_user_templates_dir()
            template_dir = templates_dir / template_id
            template_dir.mkdir(exist_ok=True, parents=True)
            
            # 处理文件名和扩展名
            if not file.filename:
                raise HTTPException(status_code=400, detail="File has no filename")
            
            ext = file.content_type.split("/")[-1].lower() if file.content_type else "png"
            if not ext or ext not in ["png", "jpg", "jpeg", "webp"]:
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            
            filename = f"template.{ext}"
            filepath = template_dir / filename
            
            # 异步保存文件
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # 返回相对路径
            return filepath.relative_to(self.upload_folder).as_posix()
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save user template: {str(e)}")
    
    def delete_user_template(self, template_id: str) -> bool:
        """
        Delete user template
        
        Args:
            template_id: Template ID
        
        Returns:
            True if deleted successfully
        
        Raises:
            HTTPException: If delete fails
        """
        try:
            templates_dir = self._get_user_templates_dir()
            template_dir = templates_dir / template_id
            
            if template_dir.exists() and template_dir.is_dir():
                shutil.rmtree(template_dir)
            
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete user template: {str(e)}")

