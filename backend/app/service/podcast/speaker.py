
from typing import List
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
