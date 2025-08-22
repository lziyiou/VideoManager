from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TagCategoryBase(BaseModel):
    name: str
    color: Optional[str] = '#409EFF'
    sort_order: Optional[int] = 0
    description: Optional[str] = None

class TagCategoryCreate(TagCategoryBase):
    pass

class TagCategoryUpdate(TagCategoryBase):
    name: Optional[str] = None

class TagCategory(TagCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags_count: Optional[int] = None

    class Config:
        from_attributes = True