"""
配置管理
"""

import os
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env)
else:
    load_dotenv()

class Config:

    "LLM配置"
    LLM_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL","https://dashscope.aliyuncs.com/compatible-mode/v1")
    LLM_MODEL = os.environ.get("LLM_MODEL_NAME","qwen3-max")
