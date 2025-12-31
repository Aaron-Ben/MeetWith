"""
工具函数和验证器
"""
from typing import Set, Optional
from app.config import Config


def allowed_file(filename: Optional[str], allowed_extensions: Set[str] = None) -> bool:
    """
    检查文件扩展名是否允许

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合

    Returns:
        是否允许
    """
    if not filename or not isinstance(filename, str):
        return False

    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
