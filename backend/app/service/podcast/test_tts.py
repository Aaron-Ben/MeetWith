# 文件: backend/app/service/podcast/test_tts.py
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from backend.app.service.podcast.core import Dialogue
from backend.app.service.podcast.speaker import Speaker, SpeakerProfile
from backend.app.service.podcast.state import PodcastState
from backend.app.service.podcast.nodes import (
    generate_all_audio_node,
    combine_audio_node,
)


# 加载 .env（优先项目根目录，其次 backend/.env），与其它测试保持一致
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


async def generate_podcast_audio_test() -> dict:
    """
    使用 MiniMax TTS 测试音频生成流程：
    - 构造少量对话
    - 生成 clips 下的小音频片段
    - 合成为一条完整 mp3
    """
    output_dir = "output/tts_test"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 构造简单的对话脚本
    transcript = [
        Dialogue(speaker="主持人", dialogue="欢迎收听今天的播客，我们来聊聊一次特别的旅行体验。"),
        Dialogue(speaker="嘉宾", dialogue="是的，这次行程充满了意外和惊喜，我印象最深的是第一天在机场的小插曲。"),
        Dialogue(speaker="主持人", dialogue="那我们就从机场开始说起吧，你当时发生了什么？"),
    ]

    # 构造说话人配置：注意 voice_id 要与你在 MiniMax 上配置的音色一致
    speaker_profile = SpeakerProfile(
        tts_provider="minimax",
        tts_model="speech-2.6-hd",
        speakers=[
            Speaker(
                name="主持人",
                voice_id="audiobook_male_1",  # 示例音色 ID，可按你在 MiniMax 控台的配置调整
                backstory="负责引导节奏的主持人",
                personality="理性、友好、结构清晰",
            ),
            Speaker(
                name="嘉宾",
                voice_id="audiobook_female_1",
                backstory="对话题有经验的嘉宾",
                personality="专业、幽默、善于举例",
            ),
        ],
    )

    # 初始化 PodcastState（这里只关心 transcript / output_dir / episode_name / speaker_profile）
    state: PodcastState = {
        "content": "",                 # 音频阶段不会用到
        "briefing": "测试 MiniMax 语音合成的播客片段。",
        "num_segments": 1,             # 此处无关紧要
        "outline": None,               # 此处无关紧要
        "transcript": transcript,
        "audio_clips": [],
        "final_output_file_path": None,
        "output_dir": output_path,
        "episode_name": "tts_test_episode",
        "speaker_profile": speaker_profile,
    }

    # 1) 生成所有小音频片段
    audio_result = await generate_all_audio_node(state)
    state["audio_clips"] = audio_result["audio_clips"]

    # 2) 合成最终整条音频
    final_result = await combine_audio_node(state)
    state["final_output_file_path"] = final_result["final_output_file_path"]

    return {
        "clips": state["audio_clips"],
        "final_audio": state["final_output_file_path"],
    }


async def main():
    result = await generate_podcast_audio_test()

    logger.info("✅ MiniMax TTS 测试完成：")
    logger.info(f"  生成的小音频片段数: {len(result['clips'])}")
    for p in result["clips"]:
        logger.info(f"    clip: {p}")

    logger.info(f"  合成后的最终音频文件: {result['final_audio']}")


if __name__ == "__main__":
    asyncio.run(main())