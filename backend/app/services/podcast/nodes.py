import os
import asyncio
from pathlib import Path
from typing import Dict, List
from loguru import logger

from app.services.podcast.speaker import TTSProfile
from app.utils.tts_client import MiniMaxTTSClient


async def generate_audio_batch(
    transcript: List[Dict],
    output_dir: Path,
    tts_profile: TTSProfile,
    batch_size: int = 2
) -> List[Path]:
    """
    Generate audio clips for a batch of dialogue segments using TTS.

    Args:
        transcript: List of dialogue dictionaries with 'speaker' and 'dialogue' keys
        output_dir: Directory to save audio clips
        tts_profile: TTS configuration profile
        batch_size: Number of concurrent TTS requests

    Returns:
        List of paths to generated audio clips
    """
    total_segments = len(transcript)

    # Get TTS configuration from profile
    tts_provider = tts_profile.tts_provider
    tts_model = tts_profile.tts_model
    voices = tts_profile.get_voice_mapping()

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

    return all_clip_paths


async def generate_single_audio_clip(dialogue_info: Dict) -> Path:
    """
    Generate a single audio clip using MiniMax TTS.

    Args:
        dialogue_info: Dictionary containing dialogue text, speaker, and TTS configuration

    Returns:
        Path to the generated audio file

    Raises:
        ValueError: If TTS provider is not supported or speaker voice is not found
    """
    dialogue = dialogue_info["dialogue"]
    index = dialogue_info["index"]
    output_dir = dialogue_info["output_dir"]
    tts_provider = dialogue_info["tts_provider"]
    tts_model_name = dialogue_info["tts_model"]
    voices = dialogue_info["voices"]

    if tts_provider.lower() not in ("minimax", "minimax_tts"):
        raise ValueError(
            f"generate_single_audio_clip only supports MiniMax TTS, "
            f"but got tts_provider='{tts_provider}'"
        )

    # Support both dict and object dialogue formats
    if isinstance(dialogue, dict):
        speaker_name = dialogue.get("speaker", "")
        dialogue_text = dialogue.get("dialogue", "")
    else:
        speaker_name = getattr(dialogue, "speaker", "")
        dialogue_text = getattr(dialogue, "dialogue", "")

    logger.info(f"Generating audio clip {index:04d} for {speaker_name}")

    # Create clips directory
    clips_dir = output_dir / "clips"
    clips_dir.mkdir(exist_ok=True, parents=True)

    # Generate filename
    filename = f"{index:04d}.mp3"
    clip_path = clips_dir / filename

    # Get voice ID for speaker
    voice_id = voices.get(speaker_name)
    if not voice_id:
        raise ValueError(f"No voice ID found for speaker '{speaker_name}'")

    # Create TTS client and generate audio
    client = MiniMaxTTSClient(model=tts_model_name or None)

    await client.synthesize(
        text=dialogue_text,
        voice_id=voice_id,
        output_path=clip_path
    )

    logger.info(f"Generated audio clip: {clip_path}")

    return clip_path


async def generate_all_audio(
    transcript: List[Dict],
    output_dir: Path,
    tts_profile: TTSProfile
) -> List[Path]:
    """
    Generate audio clips for all dialogue segments.

    This is a convenience wrapper around generate_audio_batch that reads
    the batch size from environment variable TTS_BATCH_SIZE (default: 2).

    Args:
        transcript: List of dialogue dictionaries
        output_dir: Directory to save audio clips
        tts_profile: TTS configuration profile

    Returns:
        List of paths to generated audio clips
    """
    # Get batch size from environment variable, default to 2
    batch_size = int(os.getenv("TTS_BATCH_SIZE", "2"))
    logger.info(f"Using TTS batch size: {batch_size}")

    return await generate_audio_batch(transcript, output_dir, tts_profile, batch_size)
