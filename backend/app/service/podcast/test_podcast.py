from pathlib import Path
import asyncio

from app.service.podcast.nodes import generate_podcast
from app.service.podcast.speaker import Speaker, SpeakerProfile
from app.service.podcast.state import PodcastState
from asyncio.subprocess import DEVNULL
import shutil


current_file = Path(__file__).resolve()
root_env = current_file.parents[4] / ".env"
input_path = current_file.parents[3] / "input" / "携程.txt"

async def test(
    content: str,
    briefing: str,
    num_segments: int,
    output_path: Path,
    episode_name: str,
    speaker_profile: SpeakerProfile,
):

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

    async for event in generate_podcast(state):
        et = event.get("event")
        if et == "outline_generated":
            outline = event["outline"]
            print(f"[EVENT] outline_generated, segments = {len(outline.segments)}")
        elif et == "transcript_generated":
            transcript = event["transcript"]
            print(f"[EVENT] transcript_generated, dialogues = {len(transcript)}")
        elif et == "audio_clip_generated":
            clip_path = Path(event["path"])
            print(f"[EVENT] audio_clip_generated index={event['index']}, path={clip_path}")

            if shutil.which("ffplay"):
                player = "ffplay"
                args = ["-nodisp", "-autoexit", str(clip_path)]
            else:
                player = "afplay"
                args = [str(clip_path)]
        
            proc = await asyncio.create_subprocess_exec(
                player,
                *args,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
            await proc.wait()
        
        elif et == "final_audio_ready":
            print(f"[EVENT] final_audio_ready: {event['final_output_file_path']}")
        else:
            print(f"[EVENT] unknown: {event}")
    

def main():
    content = input_path.read_text()
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

    asyncio.run(test(
        content=content,
        briefing="为这个文章内容生成一份技术播客",
        num_segments=3,
        output_path=Path("./output"),
        episode_name="test",
        speaker_profile=speaker_profile,
    ))

    print("done")

if __name__ == "__main__":
    main()

