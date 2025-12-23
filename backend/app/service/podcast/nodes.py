import os
import asyncio
from pathlib import Path
from typing import Dict, List
from loguru import logger
from backend.app.service.podcast.core import Dialogue, Outline, Segment, combine_audio_files
from backend.app.service.podcast.speaker import SpeakerProfile
from backend.app.service.podcast.state import PodcastState
from backend.app.utils.llm_client import LLMClient
from backend.app.utils.tts_client import MiniMaxTTSClient


def generate_outline_node(state: PodcastState) -> Dict:

    """
    使用自定义 LLMClient 生成播客大纲（Outline），不依赖 LangChain

    输入：
        state["content"]       原始内容
        state["briefing"]      播客需求说明
        state["num_segments"]  期望段数
        state["speaker_profile"]  角色配置（可选）

    输出：
        返回 {"outline": Outline(...) }，由调用方写回 state["outline"]。
    """

    logger.info("Generating outline node...")

    content: str = state["content"]
    briefing: str = state["briefing"]
    num_segments: int = state["num_segments"]
    speaker_profile: SpeakerProfile | None = state.get("speaker_profile")
    
    # 构造说话人列表（可选）
    speaker_names: List[str] = []
    if speaker_profile is not None and getattr(speaker_profile, "speakers", None):
        speaker_names = [s.name for s in speaker_profile.speakers]

    # 构造提示词（System + User），要求严格 JSON 输出
    system_prompt = (
        "你是一名资深播客策划编辑。"
        "请根据给定的内容与要求，设计一个结构清晰的播客大纲。"
        "你的输出必须是一个合法的 JSON 对象，不要包含额外解释。"
    )

    user_prompt = f"""
请根据以下信息，生成一份播客大纲（outline），并使用 JSON 格式输出。

[播客需求 Briefing]
{briefing}

[期望段数 num_segments]
{num_segments}

[原始内容 Content]
{content}

[可用说话人 Speakers]
{", ".join(speaker_names) if speaker_names else "无特别指定，可自行安排角色"}

请严格输出如下 JSON 结构（字段名必须一致）：

{{
  "segments": [
    {{
      "name": "本段的标题，简短概括本段内容",
      "description": "本段的详细说明，说明要聊什么、信息重点、节奏",
      "size": "short 或 medium 或 long 三选一，用于表示本段时长/信息量"
    }}
  ]
}}

要求：
1. 必须是合法 JSON（可以被 json.loads 解析），不要出现注释或多余文本。
2. segments 的长度应尽量接近 num_segments，如果内容很多可以适当多一段或少一段，但不要偏差太大。
3. description 要尽量具体，可体现每段的论点/信息点，而不是一句很空泛的话。
"""

    client = LLMClient()

    # 使用 json_object 模式，让服务端直接返回 JSON
    try:
        response_data = client.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=3000,
        )
    except Exception as e:
        logger.error(f"Failed to call LLMClient for outline: {e}")
        raise

    # 解析 JSON 为 Outline/Segment
    if not isinstance(response_data, dict) or "segments" not in response_data:
        logger.error(f"Invalid outline JSON structure: {response_data}")
        raise ValueError("大纲返回 JSON 结构不包含 'segments' 字段")

    segments_data = response_data.get("segments") or []
    if not isinstance(segments_data, list):
        logger.error(f"'segments' should be a list, got: {type(segments_data)}")
        raise ValueError("'segments' 字段必须是列表")

    segments: List[Segment] = []
    for idx, seg in enumerate(segments_data):
        if not isinstance(seg, dict):
            logger.warning(f"Segment[{idx}] is not a dict, skipped: {seg}")
            continue
        try:
            segment = Segment(
                name=seg.get("name", "").strip(),
                description=seg.get("description", "").strip(),
                size=seg.get("size", "medium"),
            )
            segments.append(segment)
        except Exception as e:
            logger.warning(f"Failed to parse segment[{idx}] {seg}: {e}")
            continue

    if not segments:
        logger.error(f"No valid segments parsed from response: {response_data}")
        raise ValueError("未能从模型返回中解析出有效的大纲段落（segments 为空）")

    outline = Outline(segments=segments)
    logger.info(f"Generated outline with {len(outline.segments)} segments")

    return {"outline": outline}


def generate_transcript_node(state: PodcastState) -> Dict:
    
    """
        使用自定义 LLMClient，根据已有大纲 Outline 生成完整对话 transcript。

        输入：
            state["outline"]          必须已存在
            state["content"]          原始内容，用作上下文
            state["briefing"]         播客需求说明
            state["speaker_profile"]  说话人配置（必须存在，至少一个 speaker）

        输出：
            返回 {"transcript": List[Dialogue]}，由调用方写回 state["transcript"]。
        """
    logger.info("Generating transcript node with custom LLMClient...")

    outline: Outline | None = state.get("outline")
    if outline is None:
        raise ValueError("generate_transcript_node 需要 state['outline'] 不为空")

    speaker_profile: SpeakerProfile | None = state.get("speaker_profile")
    if speaker_profile is None or not getattr(speaker_profile, "speakers", None):
        raise ValueError("generate_transcript_node 需要有效的 speaker_profile（至少一个 speaker）")

    content: str = state["content"]
    briefing: str = state["briefing"]

    speaker_names = [s.name for s in speaker_profile.speakers]

    client = LLMClient()
    all_dialogues: List[Dialogue] = []

    for idx, segment in enumerate(outline.segments):
        logger.info(f"Generating transcript for segment {idx + 1}/{len(outline.segments)}: {segment.name}")

        is_final = idx == len(outline.segments) - 1
        turns = 3 if segment.size == "short" else 6 if segment.size == "medium" else 10

        system_prompt = (
            "你是一名专业的播客文案编剧，擅长为多角色播客编写自然、有信息量的对话。"
            "请根据给定大纲段落和角色信息，编写该段的完整对话。"
            "你的输出必须是一个合法 JSON 对象，不要包含任何多余文本。"
        )

        user_prompt = f"""
请为下面这个播客大纲中的一个段落，生成一段完整的多轮对话，并使用 JSON 格式输出。

[播客需求 Briefing]
{briefing}

[原始内容 Content]
{content}

[当前大纲段落 Segment]
- name: {segment.name}
- description: {segment.description}
- size: {segment.size}
- is_final_segment: {is_final}

[说话人 Speakers]
{", ".join(speaker_names)}

对话要求：
1. 对话轮次（rounds）大致为 {turns} 轮，可以略多或略少。
2. 每一句话都要指定 speaker，speaker 名必须来自上面的 Speakers 列表。
3. 对话内容要紧扣当前段落的 description 和整篇内容，不要跑题。
4. 允许角色之间有追问、补充、反驳等，自然流畅。
5. 语言风格偏口语化，但信息要尽量具体，有观点、有细节。

请严格输出如下 JSON 结构（字段名必须一致）：

{{
  "transcript": [
    {{
      "speaker": "speaker_name_1（必须是上面列出的某个名字）",
      "dialogue": "这一轮说的话"
    }},
    {{
      "speaker": "speaker_name_2",
      "dialogue": "下一轮说的话"
    }}
  ]
}}

要求：
1. 必须是合法 JSON（可以被 json.loads 解析），不要出现注释或多余文本。
2. transcript 列表中的每一项都必须包含 speaker 和 dialogue 两个字段。
3. 不要输出任何 JSON 之外的文字（例如“好的，以下是JSON”之类）。
"""

        try:
            resp = client.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )
        except Exception as e:
            logger.error(f"Failed to call LLMClient for transcript segment {idx}: {e}")
            raise

        if not isinstance(resp, dict) or "transcript" not in resp:
            logger.error(f"Invalid transcript JSON for segment {idx}: {resp}")
            raise ValueError(f"对话返回 JSON 结构不包含 'transcript' 字段（segment {idx}）")

        seg_transcript = resp.get("transcript") or []
        if not isinstance(seg_transcript, list):
            logger.error(f"'transcript' for segment {idx} should be list, got: {type(seg_transcript)}")
            raise ValueError(f"'transcript' 字段必须是列表（segment {idx}）")

        for j, item in enumerate(seg_transcript):
            if not isinstance(item, dict):
                logger.warning(f"Segment {idx} transcript[{j}] is not a dict, skipped: {item}")
                continue
            speaker = (item.get("speaker") or "").strip()
            dialogue_text = (item.get("dialogue") or "").strip()
            if not speaker or not dialogue_text:
                logger.warning(f"Segment {idx} transcript[{j}] has empty fields, skipped: {item}")
                continue
            if speaker not in speaker_names:
                logger.warning(
                    f"Segment {idx} transcript[{j}] speaker '{speaker}' not in speaker_names {speaker_names}, skipped"
                )
                continue
            try:
                dlg = Dialogue(speaker=speaker, dialogue=dialogue_text)
                all_dialogues.append(dlg)
            except Exception as e:
                logger.warning(f"Failed to build Dialogue for segment {idx} transcript[{j}] {item}: {e}")
                continue

    logger.info(f"Generated transcript with {len(all_dialogues)} dialogue segments in total")

    return {"transcript": all_dialogues}


async def generate_all_audio_node(state: PodcastState) -> Dict:
    """
    使用自定义 LLMClient，根据已有对话 transcript 生成完整音频。

    输入：
        state["transcript"]       必须已存在
        state["briefing"]        播客需求说明
        state["speaker_profile"] 说话人配置（必须存在，至少一个 speaker）

    输出：
        返回 {"audio_file": str}，由调用方写回 state["audio_file"]。
    """
    transcript = state["transcript"]
    output_dir = state["output_dir"]
    total_segments = len(transcript)

    # Get batch size from environment variable, default to 5
    batch_size = int(os.getenv("TTS_BATCH_SIZE", "5"))
    logger.info(f"Using TTS batch size: {batch_size}")

    assert state.get("speaker_profile") is not None, "speaker_profile must be provided"

    # Get TTS configuration from speaker profile
    speaker_profile = state["speaker_profile"]
    assert speaker_profile is not None, "speaker_profile must be provided"
    tts_provider = speaker_profile.tts_provider
    tts_model = speaker_profile.tts_model
    voices = speaker_profile.get_voice_mapping()

    logger.info(
        f"Generating {total_segments} audio clips in sequential batches of {batch_size}, "
        f"provider={tts_provider}, model={tts_model}"
    )

    all_clip_paths: List[Path] = []

    # Process in sequential batches
    for batch_start in range(0, total_segments, batch_size):
        batch_end = min(batch_start + batch_size, total_segments)
        batch_number = batch_start // batch_size + 1
        total_batches = (total_segments + batch_size - 1) // batch_size

        logger.info(
            f"Processing batch {batch_number}/{total_batches} (clips {batch_start}-{batch_end - 1})"
        )

        # Create tasks for this batch
        batch_tasks = []
        for i in range(batch_start, batch_end):
            dialogue_info = {
                "dialogue": transcript[i],
                "index": i,
                "output_dir": output_dir,
                "tts_provider": tts_provider,
                "tts_model": tts_model,
                "voices": voices,
            }
            task = generate_single_audio_clip(dialogue_info)
            batch_tasks.append(task)

        # Process this batch concurrently (but wait before next batch)
        batch_clip_paths = await asyncio.gather(*batch_tasks)
        all_clip_paths.extend(batch_clip_paths)

        logger.info(f"Completed batch {batch_number}/{total_batches}")

        # Small delay between batches to be extra safe with API limits
        if batch_end < total_segments:
            await asyncio.sleep(1)

    logger.info(f"Generated all {len(all_clip_paths)} audio clips")

    return {"audio_clips": all_clip_paths}


async def generate_single_audio_clip(dialogue_info: Dict) -> Path:
    """
    使用 MiniMaxTTSClient 为单条对话生成一段音频。
    当前仅支持 tts_provider == 'minimax'，否则抛错或后续扩展。
    """
    dialogue = dialogue_info["dialogue"]
    index = dialogue_info["index"]
    output_dir = dialogue_info["output_dir"]
    tts_provider = dialogue_info["tts_provider"]
    tts_model_name = dialogue_info["tts_model"]
    voices = dialogue_info["voices"]

    if tts_provider.lower() not in ("minimax", "minimax_tts"):
        raise ValueError(
            f"当前 generate_single_audio_clip 仅支持 MiniMax TTS，"
            f"但收到 tts_provider='{tts_provider}'"
        )

    logger.info(f"Generating audio clip {index:04d} for {dialogue.speaker}")

    # Create clips directory
    clips_dir = output_dir / "clips"
    clips_dir.mkdir(exist_ok=True, parents=True)

    # Generate filename
    filename = f"{index:04d}.mp3"
    clip_path = clips_dir / filename

    # Create TTS model
    voice_id = voices.get(dialogue.speaker)
    if not voice_id:
        raise ValueError(f"No voice ID found for speaker '{dialogue.speaker}'")

    client = MiniMaxTTSClient(model=tts_model_name or None)

    # Generate audio
    await client.synthesize(
        text=dialogue.dialogue, 
        voice_id=voice_id, 
        output_path=clip_path
    )

    logger.info(f"Generated audio clip: {clip_path}")

    return clip_path


async def combine_audio_node(state: PodcastState) -> Dict:
    """Combine all audio clips into final podcast episode"""
    logger.info("Starting audio combination")

    clips_dir = state["output_dir"] / "clips"
    audio_dir = state["output_dir"] / "audio"

    # Combine audio files
    result = await combine_audio_files(
        clips_dir, f"{state['episode_name']}.mp3", audio_dir
    )

    final_path = Path(result["combined_audio_path"])
    logger.info(f"Combined audio saved to: {final_path}")

    return {"final_output_file_path": final_path}
