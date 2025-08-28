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
    last_position: float = 0.0
    watch_progress: float = 0.0
    last_watched_at: Optional[datetime] = None
    is_completed: bool = False

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: Optional[List[Tag]] = None

    class Config:
        from_attributes = True

class VideoProgressUpdate(BaseModel):
    """播放进度更新模型"""
    last_position: float
    watch_progress: Optional[float] = None
    is_completed: Optional[bool] = None

class VideoProgress(BaseModel):
    """播放进度响应模型"""
    video_id: int
    last_position: float
    watch_progress: float
    last_watched_at: Optional[datetime]
    is_completed: bool
    
    class Config:
        from_attributes = True