#!/usr/bin/env python3
"""
Topic Summarizer Module
根据消息列表尝试用AI总结一个话题标题。
"""

import re
import logging
from typing import List, Dict, Optional, Any
import httpx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_to_vcp(
    server_url: str,
    api_key: str,
    messages: List[Dict[str, str]],
    options: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    发送请求到 VCP 服务器

    Args:
        server_url: VCP 服务器地址
        api_key: API 密钥
        messages: 消息列表
        options: 额外选项（如 model, temperature, max_tokens）

    Returns:
        API 响应的 JSON 数据，如果失败则返回 None
    """
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "messages": messages,
            **(options or {})
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(server_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    except Exception as e:
        logger.error(f"[TopicSummarizer] VCP API 请求失败: {e}")
        return None


async def summarize_topic_from_messages(
    messages: List[Dict[str, str]],
    agent_name: str,
    vcp_server_url: str,
    vcp_api_key: str,
    user_name: Optional[str] = None
) -> Optional[str]:
    """
    根据消息列表尝试用AI总结一个话题标题。

    Args:
        messages: 聊天消息对象数组，每个消息包含 role 和 content 字段
        agent_name: 当前Agent的名称，可用于提示
        vcp_server_url: VCP 服务器地址
        vcp_api_key: VCP API 密钥
        user_name: 用户名称（可选）

    Returns:
        总结的标题，如果无法总结则返回 None
    """
    if not messages or len(messages) < 4:
        # 至少需要两轮对话 (user, assistant, user, assistant)
        logger.info("[TopicSummarizer] 消息数量不足，无法总结")
        return None

    # 提取最近的4条消息内容用于总结
    display_name = user_name or "用户"
    recent_messages_content = "\n".join([
        f"{display_name if msg['role'] == 'user' else agent_name}: {msg['content']}"
        for msg in messages[-4:]
    ])

    logger.info(f"[TopicSummarizer] 准备总结的内容:\n{recent_messages_content}")

    # AI summarization logic
    summary_prompt = f"""请根据以下对话内容，仅返回一个简洁的话题标题。要求：1. 标题长度控制在10个汉字以内。2. 标题本身不能包含任何标点符号、数字编号或任何非标题文字。3. 直接给出标题文字，不要添加任何解释或前缀。

对话内容：
{recent_messages_content}"""

    vcp_response = await send_to_vcp(
        vcp_server_url,
        vcp_api_key,
        [{"role": "user", "content": summary_prompt}],
        {
            "model": "gemini-2.5-flash-preview-05-20",
            "temperature": 0.3,
            "max_tokens": 30
        }
    )

    if vcp_response and vcp_response.get("choices") and len(vcp_response["choices"]) > 0:
        raw_title = vcp_response["choices"][0]["message"]["content"].strip()

        # 尝试提取第一行作为标题，以应对AI可能返回多行的情况
        raw_title = raw_title.split('\n')[0].strip()

        # 移除所有标点符号、数字编号和常见的前缀/后缀
        # 保留汉字、字母、空格
        cleaned_title = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', '', raw_title)

        # 移除 "1. " 等模式
        cleaned_title = re.sub(r'^\s*\d+\s*[\.\uff0e\s]\s*', '', cleaned_title)

        # 移除 "标题：" 等前缀
        cleaned_title = re.sub(r'^(标题|总结|Topic)[:：\s]*', '', cleaned_title, flags=re.IGNORECASE)

        # 移除所有空格
        cleaned_title = re.sub(r'\s+', '', cleaned_title)

        # 截断到12个字符
        if len(cleaned_title) > 12:
            cleaned_title = cleaned_title[:12]

        logger.info(f"[TopicSummarizer] AI 原始返回: {raw_title}")
        logger.info(f"[TopicSummarizer] 清理并截断后的标题: {cleaned_title}")

        if cleaned_title:
            return cleaned_title

    # 如果AI总结失败，回退到临时逻辑
    logger.warning("[TopicSummarizer] AI 总结失败，尝试备用逻辑")

    user_messages = [msg for msg in messages if msg["role"] == "user"]
    if user_messages:
        last_user_message = user_messages[-1]["content"]
        temp_title = f'关于 "{last_user_message[:15]}{"..." if len(last_user_message) > 15 else ""}" (备用)'
        logger.info(f"[TopicSummarizer] 临时生成的标题 (备用): {temp_title}")
        return temp_title

    return None


# 为了向后兼容，保持原有函数名的别名
summarizeTopicFromMessages = summarize_topic_from_messages


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        messages = [
            {"role": "user", "content": "你好，我想了解Python的异步编程"},
            {"role": "assistant", "content": "Python的异步编程主要使用asyncio库和async/await语法"},
            {"role": "user", "content": "能给我一个简单的例子吗？"},
            {"role": "assistant", "content": "当然，这里有一个使用async/await的简单例子"}
        ]

        # 注意：需要提供实际的服务器地址和API密钥
        result = await summarize_topic_from_messages(
            messages,
            "AI助手",
            "https://your-vcp-server.com/api",
            "your-api-key"
        )
        print(f"总结结果: {result}")

    asyncio.run(test())
