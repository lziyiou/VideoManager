from pydantic import BaseModel, Field
from typing import Optional

class DirectoryPath(BaseModel):
    directory_path: str

class VideosPerPageSetting(BaseModel):
    videos_per_page: int = Field(ge=1, le=100, description="每页显示的视频数量，范围1-100")

class SettingUpdate(BaseModel):
    key: str
    value: str

class SettingResponse(BaseModel):
    key: str
    value: str