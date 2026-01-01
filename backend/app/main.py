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
from app.models.web_search import WebSearchUsage

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
    # 如果启用工具，先执行工具调用（如搜索），然后流式输出最终响应
    if req.use_tools:
        agent = AgentService(user_id=req.user_id)

        # 先执行完整的 Agent 逻辑（包含搜索）
        final_messages = req.messages.copy()

        # Agent 会先判断是否需要搜索，如果需要就执行搜索
        # 这里我们需要一种方式让 Agent 在搜索后返回增强的消息
        # 简化方案：先获取完整响应，再流式输出（但这样就失去了搜索的意义）
        # 更好的方案：Agent 返回增强后的消息，然后流式生成

        # 获取最后一条用户消息
        last_user_message = None
        for msg in reversed(req.messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break

        if last_user_message:
            # 判断是否需要搜索
            should_search, search_query = agent._should_search(last_user_message)

            if should_search and agent.web_answer_tool:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Stream: Query '{last_user_message}' triggers web search")

                try:
                    search_result = agent.web_answer_tool.run(search_query)

                    if search_result and len(search_result) >= 50:
                        from datetime import datetime
                        CURRENT_YEAR = datetime.now().year

                        # 添加系统消息包含搜索结果
                        final_messages = [
                            {
                                "role": "system",
                                "content": f"""你是AI助手。当前是 {CURRENT_YEAR} 年。

【重要】用户的问题需要最新信息。我刚刚从网络上搜索了相关信息，请务必基于以下搜索结果回答：

========== 网络搜索结果 ==========
{search_result}
========== 搜索结果结束 ==========

回答要求：
1. 必须优先使用搜索结果中的信息
2. 搜索结果中有明确数字或事实的，直接引用
3. 如果搜索结果不完整，可以用你的知识补充，但必须明确说明
4. 回答时要具体，不要模糊

现在请基于上述搜索结果回答用户的问题。"""
                            },
                            *req.messages
                        ]
                        logger.info(f"Stream: Got search result: {len(search_result)} chars")
                except Exception as e:
                    logger.error(f"Stream: Web search failed: {e}")
                    # 搜索失败，使用原始消息

        # 使用增强后的消息进行流式输出
        client = LLMClient()

        def token_generator():
            for chunk in client.chat_stream(final_messages):
                yield chunk

        return StreamingResponse(token_generator(), media_type="text/plain")
    else:
        # 不使用工具，直接流式输出
        client = LLMClient()

        def token_generator():
            for chunk in client.chat_stream(req.messages):
                yield chunk

        return StreamingResponse(token_generator(), media_type="text/plain")

# 新增：获取可用工具列表
@app.get("/api/tools")
async def get_tools():
    """获取可用的 Agent 工具列表"""
    agent = AgentService()
    return {
        "tools": agent.get_available_tools(),
        "enabled": len(agent.tools) > 0
    }

# ==================== PPT 项目相关路由 ====================
from app.api.project import project_router
from app.api.page import page_router
from app.api.template import template_router, user_template_router
from app.api.material import material_router, material_global_router
from app.api.reference_file import reference_file_router
from app.api.export import export_router
from app.api.file import file_router
from app.api.settings import settings_router
from app.api.web_search import router as web_search_router

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
app.include_router(web_search_router)

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