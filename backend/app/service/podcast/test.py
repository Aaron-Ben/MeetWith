import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from app.service.podcast.state import PodcastState
from app.service.podcast.speaker import SpeakerProfile, Speaker
from app.service.podcast.nodes import (
    generate_outline_node,
    generate_transcript_node,
)


# 加载 .env（优先项目根目录，其次 backend/.env），与 test1.py 保持风格一致
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


async def generate_podcast_text_only_local(
    content: str,
    briefing: str,
    episode_name: str,
    output_dir: str,
    num_segments: int = 3,
) -> dict:
    """
    使用本地的 generate_outline_node / generate_transcript_node + LLMClient，
    只生成文本大纲和对话，不生成音频，并将结果保存到 JSON 文件。
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 构造一个简单的说话人配置（只用于生成对话角色，不会触发 TTS）
    speaker_profile = SpeakerProfile(
        tts_provider="dummy",
        tts_model="dummy",
        speakers=[
            Speaker(
                name="主持人",
                voice_id="host",
                backstory="负责引导节奏的主持人",
                personality="理性、友好、结构清晰",
            ),
            Speaker(
                name="嘉宾",
                voice_id="guest",
                backstory="对话题有经验的嘉宾",
                personality="专业、幽默、善于举例",
            ),
        ],
    )

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

    # 1) 使用本地节点生成大纲
    outline_result = generate_outline_node(state)
    state["outline"] = outline_result["outline"]

    # 2) 使用本地节点生成对话
    transcript_result = generate_transcript_node(state)
    state["transcript"] = transcript_result["transcript"]

    # 3) 保存到 JSON 文件（路径与 test1.py 保持一致）
    outline = state["outline"]
    transcript = state["transcript"]

    outline_path = output_path / "outline.json"
    transcript_path = output_path / "transcript.json"

    if outline is not None:
        outline_path.write_text(
            outline.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    if transcript:
        transcript_path.write_text(
            json.dumps(
                [d.model_dump() for d in transcript],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return {
        "outline_path": outline_path,
        "transcript_path": transcript_path,
        "segments_count": len(transcript),
    }


async def main():
    # 与 test1.py 一样，读取 xiecheng.txt 作为内容来源
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]  # 与 test1.py 保持相同写法
    input_path = project_root / "input" / "xiecheng.txt"

    # 如果文件不存在会抛异常，方便你及时发现
    content_text = input_path.read_text(encoding="utf-8")

    result = await generate_podcast_text_only_local(
        content=content_text,
        briefing="Create an engaging discussion about...",
        episode_name="my_podcast",
        output_dir="output/my_podcast_text_only",
        num_segments=3,
    )
    print("✅ 本地节点文本生成完成：")
    print(f"  大纲文件: {result['outline_path']}")
    print(f"  对话文件: {result['transcript_path']}")
    print(f"  对话段数: {result['segments_count']}")


if __name__ == "__main__":
    asyncio.run(main())