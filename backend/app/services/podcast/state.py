from operator import add
from pathlib import Path
from typing import Annotated, List, Optional, TypedDict

from app.services.podcast.core import Dialogue, Outline
from app.services.podcast.speaker import SpeakerProfile



class PodcastState(TypedDict):
    # 输入数据
    content: str
    briefing: str
    num_segments: int

    # 转化成大纲和结构化内容
    outline: Optional[Outline]
    transcript: List[Dialogue]

    # 音频
    audio_clips: Annotated[List[Path], add]
    final_output_file_path: Optional[Path]

    # 输出
    output_dir: Path
    episode_name: str
    speaker_profile: Optional[SpeakerProfile]
