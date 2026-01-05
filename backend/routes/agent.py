"""Agent routes for managing AI agents"""

import re
import logging
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, Request, HTTPException, UploadFile, File

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
AGENT_DIR = BASE_DIR / 'Agent'


def register_routes(app: FastAPI):
    """Register all agent routes with the FastAPI app"""

    @app.get("/admin_api/agents")
    async def list_agents():
        """获取所有 Agent 列表"""
        try:
            agents = []

            if not AGENT_DIR.exists():
                return {"agents": []}

            for agent_folder in AGENT_DIR.iterdir():
                if agent_folder.is_dir():
                    agent_name = agent_folder.name

                    try:
                        # 尝试读取配置文件
                        config_files = list(agent_folder.glob("*.txt"))
                        content = ""
                        config_path = None

                        if config_files:
                            config_file = config_files[0]
                            content = config_file.read_text(encoding="utf-8")
                            config_path = str(config_file.relative_to(BASE_DIR))

                        # 检查头像文件是否存在
                        avatar_path = agent_folder / "Image" / "avatar.png"
                        avatar_url = f"/Agent/{agent_name}/Image/avatar.png" if avatar_path.exists() else None

                        agent_data = {
                            "id": agent_name,
                            "name": agent_name,
                            "configPath": config_path,
                            "systemPrompt": content,
                            "avatarUrl": avatar_url
                        }
                        agents.append(agent_data)
                    except Exception as e:
                        logger.warning(f"[AgentRoutes] Error reading agent {agent_name}: {e}")
                        # 即使出错也添加 Agent，使用默认值
                        agents.append({
                            "id": agent_name,
                            "name": agent_name,
                            "configPath": None,
                            "systemPrompt": "",
                            "avatarUrl": None
                        })

            return {"agents": agents}
        except Exception as e:
            logger.error("[AgentRoutes] Error listing agents:", e)
            raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

    @app.get("/admin_api/agents/{agent_name}")
    async def get_agent(agent_name: str):
        """获取指定 Agent 的配置"""
        try:
            agent_path = AGENT_DIR / agent_name
            if not agent_path.exists():
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")

            # 尝试读取配置文件
            config_files = list(agent_path.glob("*.txt"))
            content = ""
            config_path = None

            if config_files:
                config_file = config_files[0]
                content = config_file.read_text(encoding="utf-8")
                config_path = str(config_file.relative_to(BASE_DIR))

            # 检查头像文件是否存在
            avatar_path = agent_path / "Image" / "avatar.png"
            avatar_url = f"/Agent/{agent_name}/Image/avatar.png" if avatar_path.exists() else None

            return {
                "id": agent_name,
                "name": agent_name,
                "configPath": config_path,
                "systemPrompt": content,
                "avatarUrl": avatar_url
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AgentRoutes] Error getting agent {agent_name}:", e)
            raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

    @app.post("/admin_api/agents")
    async def create_agent(request: Request):
        """创建新 Agent"""
        try:
            body = await request.json()
            agent_name = body.get('name')
            system_prompt = body.get('systemPrompt', '')

            if not agent_name or not isinstance(agent_name, str):
                raise HTTPException(status_code=400, detail='Agent name is required.')

            # 验证名称不包含非法字符
            if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5\s-]+$', agent_name):
                raise HTTPException(status_code=400, detail='Agent name contains invalid characters.')

            # 检查 Agent 是否已存在
            agent_path = AGENT_DIR / agent_name
            if agent_path.exists():
                raise HTTPException(status_code=409, detail=f"Agent '{agent_name}' already exists.")

            # 创建 Agent 目录
            agent_path.mkdir(parents=True, exist_ok=True)

            # 创建配置文件
            config_file = agent_path / f"{agent_name}.txt"
            config_file.write_text(system_prompt, encoding='utf-8')

            logger.info(f"[AgentRoutes] Created new agent: {agent_name}")

            return {
                "message": f"Agent '{agent_name}' created successfully.",
                "agent": {
                    "id": agent_name,
                    "name": agent_name,
                    "configPath": str(config_file.relative_to(BASE_DIR)),
                    "systemPrompt": system_prompt,
                    "avatarUrl": None
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("[AgentRoutes] Error creating agent:", e)
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

    @app.post("/admin_api/agents/{agent_name}/avatar")
    async def upload_agent_avatar(agent_name: str, file: UploadFile = File(...)):
        """上传 Agent 头像"""
        try:
            agent_path = AGENT_DIR / agent_name
            if not agent_path.exists():
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")

            # 创建 Image 目录
            image_dir = agent_path / "Image"
            image_dir.mkdir(parents=True, exist_ok=True)

            # 检查文件类型
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only image files are allowed.")

            # 保存文件
            avatar_path = image_dir / "avatar.png"
            content = await file.read()
            avatar_path.write_bytes(content)

            logger.info(f"[AgentRoutes] Uploaded avatar for agent {agent_name}")

            return {
                "message": "Avatar uploaded successfully",
                "avatarUrl": f"/Agent/{agent_name}/Image/avatar.png"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AgentRoutes] Error uploading avatar for agent {agent_name}:", e)
            raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")

    @app.delete("/admin_api/agents/{agent_name}")
    async def delete_agent(agent_name: str):
        """删除 Agent"""
        try:
            agent_path = AGENT_DIR / agent_name
            if not agent_path.exists():
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")

            # 删除整个 Agent 目录
            shutil.rmtree(agent_path)

            logger.info(f"[AgentRoutes] Deleted agent: {agent_name}")

            return {"message": f"Agent '{agent_name}' deleted successfully."}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AgentRoutes] Error deleting agent {agent_name}:", e)
            raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")
