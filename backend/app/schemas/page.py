from typing import List, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    """通用分页响应模型"""
    total: int
    total_pages: int
    items: List[T]