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

    "LLM配置"
    QWEN_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
    QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL = "qwen3-max"

    DEEP_SEEK_API_KEY = os.environ.get("DEEP_SEEK_API_KEY")

    MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
    MINIMAX_BASE_URL = "https://api.minimax.ai/v1"

    "数据库配置"
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


    "文件解析配置"
    MINERU_API_KEY = os.environ.get("MINERU_API_KEY")
