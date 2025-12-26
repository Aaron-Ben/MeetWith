from pathlib import Path
from typing import Literal, Union
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from pydantic import BaseModel
from loguru import logger
import uuid


class Segment(BaseModel):
    name: str
    description: str
    size: Literal["short", "medium", "long"]

class Outline(BaseModel):
    segments: list[Segment]

    def model_dump(self, **kwargs):
        return {"segments": [segment.model_dump(**kwargs) for segment in self.segments]}

# 对话的结构
class Dialogue(BaseModel):
    # 发言人
    speaker: str

    # 内容
    dialogue: str

class Transcript(BaseModel):
    transcript: list[Dialogue]


async def combine_audio_files(
    audio_dir: Union[Path, str], final_filename: str, final_output_dir: Union[Path, str]
):
    """
    Combines multiple audio files into a single MP3 file using moviepy.
    Expects 'audio_segments_data' in inputs: a list of strings, where each string is a path to an audio file.
    Also expects 'final_filename' in inputs: a string for the desired output filename (e.g., "podcast_episode.mp3").
    Example input: {
        "audio_segments_data": ["path/to/audio1.mp3", "path/to/audio2.mp3"],
        "final_filename": "my_podcast.mp3"
    }
    Output: {"combined_audio_path": "output/audio/my_podcast.mp3"}
    """
    logger.info("[Core Function] combine_audio_files called.")
    if isinstance(audio_dir, str):
        audio_dir = Path(audio_dir)
    if isinstance(final_output_dir, str):
        final_output_dir = Path(final_output_dir)
    list_of_audio_paths = sorted(audio_dir.glob("*.mp3"))
    output_filename_from_input = final_filename

    logger.debug(list_of_audio_paths)

    if not list_of_audio_paths:
        logger.warning(
            "combine_audio_files: No audio segment data (list of paths) provided."
        )
        return {"combined_audio_path": "ERROR: No audio segment data"}

    if not isinstance(list_of_audio_paths, list):
        logger.error(
            f"combine_audio_files: 'audio_segments_data' is not a list. Received: {type(list_of_audio_paths)}"
        )
        return {
            "combined_audio_path": "ERROR: audio_segments_data must be a list of file paths"
        }

    clips = []
    valid_clips = []
    for i, file_path in enumerate(list_of_audio_paths):
        if not isinstance(file_path, Path):
            logger.warning(
                f"combine_audio_files: Item {i} in audio_segments_data is not a string path: {file_path}. Skipping."
            )
            continue

        try:
            if file_path.exists() and file_path.is_file():
                clip = AudioFileClip(str(file_path))
                clips.append(clip)
                valid_clips.append(clips[-1])  # Keep track of valid clips for later
            else:
                logger.error(
                    f"combine_audio_files: File not found or not a file: {file_path}"
                )
        except Exception as e:
            logger.error(
                f"combine_audio_files: Error loading audio clip {file_path}: {e}"
            )

    if not clips:
        logger.error("combine_audio_files: No valid audio clips could be loaded.")
        return {"combined_audio_path": "ERROR: No valid clips"}

    try:
        # Ensure all clips are closed after concatenation, even if it fails during the process.
        # MoviePy's concatenate_audioclips might not close source clips if it errors out mid-way.
        final_clip = concatenate_audioclips(clips)
    except Exception as e:
        logger.error(f"Error during concatenate_audioclips: {e}")
        for clip_obj in clips:
            try:
                clip_obj.close()
            except Exception as close_exc:
                logger.debug(f"Error closing clip during error handling: {close_exc}")
        return {"combined_audio_path": f"ERROR: Concatenation failed - {e}"}

    output_dir = final_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use the filename from input if provided, otherwise generate one.
    if output_filename_from_input and isinstance(output_filename_from_input, str):
        # Basic sanitization for filename (optional, depending on how robust it needs to be)
        # For now, assume it's a simple filename like 'episode.mp3'
        output_filename = Path(
            output_filename_from_input
        ).name  # Use only the filename part
        if not output_filename.endswith(".mp3"):
            output_filename += ".mp3"  # Ensure .mp3 extension
    else:
        output_filename = f"combined_{uuid.uuid4().hex}.mp3"
        logger.warning(
            f"'final_filename' not provided or invalid in inputs. Using generated name: {output_filename}"
        )

    output_path = output_dir / output_filename

    try:
        final_clip.write_audiofile(output_path, codec="mp3")
        logger.info(f"Successfully combined audio to: {output_path.resolve()}")
        return {
            "combined_audio_path": str(output_path.resolve()),
            "original_segments_count": len(valid_clips),
            "total_duration_seconds": final_clip.duration,
        }
    except Exception as e:
        logger.error(f"Error writing final audio file {output_path}: {e}")
        return {"combined_audio_path": f"ERROR: Failed to write output audio - {e}"}
    finally:
        final_clip.close()  # Close the final concatenated clip
        for clip_obj in clips:  # Ensure all source clips are closed
            try:
                clip_obj.close()
            except Exception as close_exc:
                logger.debug(f"Error closing source clip: {close_exc}")

