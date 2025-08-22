from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from .tag_categories import TagCategory

# 标签Schema
class TagBase(BaseModel):
    name: str
    category_id: Optional[int] = None

class TagCreate(TagBase):
    pass

class TagUpdate(TagBase):
    pass

class Tag(TagBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags_count: Optional[int] = None  # 标签关联的视频数量
    category: Optional[TagCategory] = None  # 标签分类信息

    class Config:
        from_attributes = True

class VideoTagUpdate(BaseModel):
    tag_ids: List[int]