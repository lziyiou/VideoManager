from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .tags import Tag

class VideoBase(BaseModel):
    filename: str
    filepath: str
    size: float
    duration: float
    thumbnail_path: Optional[str] = None
    is_favorite: bool = False
    web_playable: bool = True

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: Optional[List[Tag]] = None

    class Config:
        from_attributes = True