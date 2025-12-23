from typing import Literal
from pydantic import BaseModel

class Segment(BaseModel):
    name: str
    description: str
    size: Literal["short", "medium", "long"]

class Outline(BaseModel):
    segments: list[Segment]

    def model_dump(self, **kwargs):
        return {"segments": [segment.model_dump(**kwargs) for segment in self.segments]}

class Dialogue(BaseModel):
    speaker: str
    dialogue: str

class Transcript(BaseModel):
    transcript: list[Dialogue]
