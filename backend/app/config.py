"""
配置管理
"""
import os
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../.env')
if os.path.exists(project_root_env):
    load_dotenv(project_root_env)
else:
    print("请在backend/.env 文件中配置相关参数")


class Config:

    # ==================== LLM配置 ====================
    QWEN_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
    QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL = "qwen-plus"  # 使用可用的模型

    DEEP_SEEK_API_KEY = os.environ.get("DEEP_SEEK_API_KEY")

    MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
    MINIMAX_BASE_URL = "https://api.minimax.ai/v1"

    # ==================== 数据库配置 ====================
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

    # ==================== 文件解析配置 ====================
    MINERU_API_KEY = os.environ.get("MINERU_API_KEY")
    MINERU_TOKEN = MINERU_API_KEY  # 别名
    MINERU_API_BASE = os.environ.get("MINERU_API_BASE", "https://api.mineru.io")

    # ==================== 文件存储配置 ====================
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./upload")

    # ==================== AI图片生成配置 ====================
    # 默认图片宽高比 (16:9)
    DEFAULT_ASPECT_RATIO = "16:9"
    # 默认分辨率 (宽x高)
    DEFAULT_RESOLUTION = "1920x1080"
    # 最大并行图片生成数
    MAX_IMAGE_WORKERS = 3
    # 图片生成超时时间(秒)
    IMAGE_GENERATION_TIMEOUT = 120

    # ==================== 任务管理配置 ====================
    # 异步任务最大并发数
    MAX_ASYNC_TASKS = 3
    # 任务执行超时时间(秒)
    TASK_TIMEOUT = 600

    # ==================== 导出配置 ====================
    # PPT导出默认格式
    DEFAULT_EXPORT_FORMAT = "pptx"
    # PDF导出DPI
    PDF_EXPORT_DPI = 300

    # ==================== 语言配置 ====================
    # 默认输出语言
    OUTPUT_LANGUAGE = "zh"

    # ==================== 文件上传配置 ====================
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'docx', 'pptx', 'txt', 'md'}
    ALLOWED_REFERENCE_FILE_EXTENSIONS = {'pdf', 'docx', 'pptx', 'txt', 'md'}
    # 最大文件大小 (MB)
    MAX_FILE_SIZE_MB = 50

    # ==================== 其他配置 ====================
    # 日志级别
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    # 调试模式
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
