from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.utils.llm_client import LLMClient
from app.models.database import init_db

# Import all models to ensure they're registered with SQLAlchemy before init_db() is called
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
from app.services.agent import AgentService
from app.utils.llm_client import LLMClient

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    use_tools: Optional[bool] = True  # 是否使用 Agent 工具

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # 如果启用工具，使用 Agent 服务
    if req.use_tools:
        agent = AgentService(user_id=req.user_id)
        reply = agent.chat(req.messages)
    else:
        client = LLMClient()
        reply = client.chat(req.messages)
    return {"reply": reply}

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    client = LLMClient()

    def token_generator():
        for chunk in client.chat_stream(req.messages):
            yield chunk

    return StreamingResponse(token_generator(), media_type="text/plain")

# 新增：获取可用工具列表
@app.get("/api/tools")
async def get_tools():
    """获取可用的 Agent 工具列表"""
    return {
        "tools": [],
        "enabled": False
    }

# ==================== PPT 项目相关路由 ====================
from app.api.file import file_router

# 注册所有路由
app.include_router(file_router)

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