import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
from podcast_creator.state import PodcastState
from podcast_creator.speakers import load_speaker_config
from podcast_creator.nodes import generate_outline_node, generate_transcript_node


# 加载 .env（优先项目根目录，其次 backend/.env）
current_file = Path(__file__).resolve()
project_root_env = current_file.parents[4] / ".env"   # /Users/xuenai/Code/MeetWith/.env
backend_env = current_file.parents[3] / ".env"        # /Users/xuenai/Code/MeetWith/backend/.env

if project_root_env.exists():
    load_dotenv(project_root_env)
elif backend_env.exists():
    load_dotenv(backend_env)
else:
    # 如果没有 .env，就依赖系统环境变量
    pass


async def generate_podcast_text_only(
    content: str | list[str],
    briefing: str,
    episode_name: str,
    output_dir: str,
    speaker_config: str = "ai_researchers",
    num_segments: int = 3,
) -> dict:
    """
    只使用 DeepSeek 生成大纲和对话，不生成音频，并将结果保存到 JSON 文件。
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 加载说话人配置（仅用于生成更自然的对话，不会触发 TTS）
    speaker_profile = load_speaker_config(speaker_config)

    # 初始化状态（不需要 audio_clips / final_output_file_path）
    state: PodcastState = {
        "content": content,
        "briefing": briefing,
        "num_segments": num_segments,
        "outline": None,
        "transcript": [],
        "audio_clips": [],
        "final_output_file_path": None,
        "output_dir": output_path,
        "episode_name": episode_name,
        "speaker_profile": speaker_profile,
    }

    # 使用 DeepSeek 作为 LLM
    config = {
        "configurable": {
            "outline_provider": "deepseek",
            "outline_model": "deepseek-chat",
            "transcript_provider": "deepseek",
            "transcript_model": "deepseek-chat",
        }
    }

    # 1) 生成大纲
    outline_result = await generate_outline_node(state, config)
    state["outline"] = outline_result["outline"]

    # 2) 基于大纲生成对话
    transcript_result = await generate_transcript_node(state, config)
    state["transcript"] = transcript_result["transcript"]

    # 3) 保存到 JSON 文件
    outline = state["outline"]
    transcript = state["transcript"]

    outline_path = output_path / "outline.json"
    transcript_path = output_path / "transcript.json"

    if outline is not None:
        # Outline 是 Pydantic 模型，使用 model_dump_json
        outline_path.write_text(outline.model_dump_json(indent=2, ensure_ascii=False))

    if transcript:
        # Transcript 是 Dialogue 列表，同样是 Pydantic 模型
        transcript_path.write_text(
            json.dumps(
                [d.model_dump() for d in transcript],
                ensure_ascii=False,
                indent=2,
            )
        )

    return {
        "outline_path": outline_path,
        "transcript_path": transcript_path,
        "segments_count": len(transcript),
    }


async def main():
    # 读取 backend/input/xiecheng.txt 作为内容来源
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]  # /Users/xuenai/Code/MeetWith
    input_path = project_root / "input" / "xiecheng.txt"

    # 如果文件不存在会抛异常，方便你及时发现
    content_text = input_path.read_text(encoding="utf-8")

    result = await generate_podcast_text_only(
        content=content_text,
        briefing="Create an engaging discussion about...",
        episode_name="my_podcast",
        output_dir="output/my_podcast_text_only",
        speaker_config="ai_researchers",
        num_segments=3,
    )
    print("✅ 文本生成完成：")
    print(f"  大纲文件: {result['outline_path']}")
    print(f"  对话文件: {result['transcript_path']}")
    print(f"  对话段数: {result['segments_count']}")


if __name__ == "__main__":
    asyncio.run(main())