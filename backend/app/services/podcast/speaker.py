
from typing import List, Dict
from pydantic import BaseModel

class Speaker(BaseModel):
    name: str
    voice_id: str
    backstory: str
    personality: str

class SpeakerProfile(BaseModel):
    tts_provider: str
    tts_model: str
    speakers: List[Speaker]


    def get_voice_mapping(self) -> Dict[str, str]:
        """Get mapping of speaker names to voice IDs"""
        return {speaker.name: speaker.voice_id for speaker in self.speakers}
