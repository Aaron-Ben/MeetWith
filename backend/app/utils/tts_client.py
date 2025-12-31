import asyncio
import os
from pathlib import Path

import httpx
from loguru import logger
from app.config import Config


class MiniMaxTTSClient:
    """
    MiniMax 异步语音合成（T2A Async）客户端封装。

    使用流程（基于官方文档）：
      1. POST /v1/t2a_async_v2 创建语音合成任务，获得 task_id
      2. 循环 GET /v1/query/t2a_async_query_v2?task_id=xxx 查询状态
      3. 当任务成功时，从响应中获取 file_id
      4. GET /v1/files/retrieve_content?file_id=xxx 下载音频数据

    环境变量：
      - MINIMAX_API_KEY       必填
      - MINIMAX_TTS_BASE_URL 可选，默认 https://api.minimaxi.com
      - MINIMAX_TTS_MODEL    可选，默认 speech-2.6-hd
    """

    def __init__(
        self,
    ):
        self.api_key = Config.MINIMAX_API_KEY
        self.base_url = Config.MINIMAX_BASE_URL
        self.model = Config.MINIMAX_TTS_MODEL
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        *,
        speed: float = 1.0,
        vol: int = 10,
        pitch: float = 1.0,
        sample_rate: int = 32000,
        bitrate: int = 128000,
        audio_format: str = "mp3",
        channel: int = 2,
        max_polls: int = 60,
        poll_interval: float = 2.0,
    ) -> Path:
        """
        调用 MiniMax 异步 TTS，将 text 合成为语音文件写入 output_path。
        """
        create_url = f"{self.base_url}/v1/t2a_async_v2"
        query_url = f"{self.base_url}/v1/query/t2a_async_query_v2"
        download_url = f"{self.base_url}/v1/files/retrieve_content"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "text": text,
            "language_boost": "auto",
            "voice_setting": {
                "voice_id": voice_id,
                "speed": int(speed),
                "vol": int(vol),
                "pitch": int(pitch),
            },
            # 按官方示例补上字段，先给一个空的 tone 列表
            "pronunciation_dict": {
                "tone": [
                    # 可以按需填入 "词/(yin1)(yin2)" 这样的条目
                ]
            },
            "audio_setting": {
                "audio_sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": audio_format,
                "channel": channel,
            },
            # 按官方示例增加 voice_modify，可先用默认值
            "voice_modify": {
                "pitch": 0,
                "intensity": 0,
                "timbre": 0,
                "sound_effects": "spacious_echo",
            },
        }

        logger.info(f"MiniMax TTS creating task, model={self.model}, voice_id={voice_id}")
        logger.info(f"MiniMax TTS create payload: {payload}")


        async with httpx.AsyncClient(timeout=60) as client:
            # 1) 创建任务
            try:
                resp = await client.post(create_url, json=payload, headers=headers)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(f"MiniMax TTS create task failed: {e!r}")
                raise

            data = resp.json()
            base_resp = data.get("base_resp") or {}
            status_code = base_resp.get("status_code", 0)
            status_msg = base_resp.get("status_msg", "")

            if status_code != 0:
                logger.error(
                    f"MiniMax TTS create task failed with error: "
                    f"status_code={status_code}, status_msg={status_msg}"
                )
                raise ValueError(
                    f"MiniMax TTS 创建任务失败：status_code={status_code}, status_msg={status_msg}"
                )

            task_id = data.get("task_id") or data.get("data", {}).get("task_id")
            if not task_id:
                logger.error(f"MiniMax TTS create task response missing task_id: {data}")
                raise ValueError("MiniMax TTS 创建任务失败，未返回 task_id")

            logger.info(f"MiniMax TTS task created, task_id={task_id}")

            # 2) 轮询任务状态
            file_id = None
            for attempt in range(max_polls):
                try:
                    q_resp = await client.get(
                        query_url,
                        params={"task_id": task_id},
                        headers=headers,
                    )
                    q_resp.raise_for_status()
                except httpx.HTTPError as e:
                    logger.warning(
                        f"MiniMax TTS query failed (attempt {attempt}): {e!r}"
                    )
                    await asyncio.sleep(poll_interval)
                    continue

                q_data = q_resp.json()

                # 每隔几次打印一下完整响应，方便调试
                if attempt == 0 or attempt % 5 == 0:
                    logger.info(f"MiniMax TTS query response (attempt {attempt}): {q_data}")

                # 先检查 query 的 base_resp 是否报错
                q_base_resp = q_data.get("base_resp") or {}
                q_status_code = q_base_resp.get("status_code", 0)
                q_status_msg = q_base_resp.get("status_msg", "")
                if q_status_code != 0:
                    logger.error(
                        f"MiniMax TTS query error: status_code={q_status_code}, "
                        f"status_msg={q_status_msg}, data={q_data}"
                    )
                    raise ValueError(
                        f"MiniMax TTS 查询任务状态失败：status_code={q_status_code}, "
                        f"status_msg={q_status_msg}"
                    )

                data_field = q_data.get("data") or q_data
                raw_status = (
                    data_field.get("task_status")
                    or data_field.get("state")
                    or data_field.get("status")
                )
                status = str(raw_status).upper() if raw_status is not None else ""

                if status in ("SUCCESS", "SUCCEEDED", "DONE", "FINISHED"):
                    file_id = data_field.get("file_id") or data_field.get(
                        "audio_file_id"
                    )
                    if not file_id:
                        logger.error(
                            f"MiniMax TTS success but no file_id in response: {q_data}"
                        )
                        raise ValueError("MiniMax TTS 任务完成但未返回 file_id")
                    logger.info(
                        f"MiniMax TTS task succeeded, file_id={file_id}, task_id={task_id}"
                    )
                    break

                if status in ("FAILED", "ERROR"):
                    logger.error(f"MiniMax TTS task failed: {q_data}")
                    raise ValueError(f"MiniMax TTS 任务失败：{q_data}")

                await asyncio.sleep(poll_interval)

            if not file_id:
                raise TimeoutError(
                    f"MiniMax TTS 任务超时未完成，task_id={task_id}, polls={max_polls}"
                )

            # 3) 下载音频内容
            try:
                d_resp = await client.get(
                    download_url,
                    params={"file_id": file_id},
                    headers=headers,
                )
                d_resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(
                    f"MiniMax TTS download failed, file_id={file_id}: {e!r}"
                )
                raise

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(d_resp.content)

        logger.info(f"MiniMax TTS generated audio file: {output_path}")
        return output_path