from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.utils.llm_client import LLMClient

app = FastAPI()

# 允许前端（Vite 开发服务器）跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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