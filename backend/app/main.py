from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.utils.llm_client import LLMClient
from app.models.database import init_db

# Import all models to ensure they're registered with SQLAlchemy before init_db() is called
from app.models.ppt.project import PPTProject
from app.models.ppt.page import Page
from app.models.ppt.task import Task
from app.models.ppt.material import Material
from app.models.ppt.page_image_version import PageImageVersion
from app.models.ppt.user_template import UserTemplate
from app.models.refernce_file import ReferenceFile

# ==================== 创建 FastAPI 应用 ====================
app = FastAPI(
    title="MeetWith AI PPT API",
    description="AI驱动的PPT生成服务",
    version="1.0.0"
)

# ==================== CORS 配置 ====================
# 允许前端（Vite 开发服务器）跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 启动事件 ====================
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()

# ==================== 聊天相关路由 ====================
client = LLMClient()

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    reply = client.chat(req.messages)
    return {"reply": reply}

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    def token_generator():
        for chunk in client.chat_stream(req.messages):
            yield chunk

    return StreamingResponse(token_generator(), media_type="text/plain")

# ==================== PPT 项目相关路由 ====================
from app.api.project import project_router
from app.api.page import page_router
from app.api.template import template_router, user_template_router
from app.api.material import material_router, material_global_router
from app.api.reference_file import reference_file_router
from app.api.export import export_router
from app.api.file import file_router
from app.api.settings import settings_router

# 注册所有路由
app.include_router(project_router)
app.include_router(page_router)
app.include_router(template_router)
app.include_router(user_template_router)
app.include_router(material_router)
app.include_router(material_global_router)
app.include_router(reference_file_router)
app.include_router(export_router)
app.include_router(file_router)
app.include_router(settings_router)

# ==================== 健康检查 ====================
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "MeetWith AI PPT API"}

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to MeetWith AI PPT API",
        "version": "1.0.0",
        "docs": "/docs"
    }