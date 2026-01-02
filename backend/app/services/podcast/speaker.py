from typing import List, Dict
from pydantic import BaseModel


class Voice(BaseModel):
    """TTS voice configuration"""
    name: str
    voice_id: str


class TTSProfile(BaseModel):
    """TTS provider and voice configuration"""
    tts_provider: str
    tts_model: str
    voices: List[Voice]

    def get_voice_mapping(self) -> Dict[str, str]:
        """Get mapping of voice names to voice IDs"""
        return {voice.name: voice.voice_id for voice in self.voices}
