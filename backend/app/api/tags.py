from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..services.tag_service import TagService
from ..schemas.tags import Tag, TagCreate, TagUpdate, VideoTagUpdate
from ..schemas.tag_categories import TagCategory

tagsRouter = APIRouter()

@tagsRouter.get("/", response_model=List[Tag], summary="获取所有标签")
def get_all_tags(db: Session = Depends(get_db)):
    """获取所有标签"""
    tags = TagService.get_all_tags(db)
    return tags

@tagsRouter.get("/grouped", summary="获取按分类分组的标签")
def get_tags_grouped_by_category(db: Session = Depends(get_db)):
    """获取按分类分组的标签"""
    return TagService.get_tags_grouped_by_category(db)

@tagsRouter.get("/{tag_id}", response_model=Tag, summary="获取标签详情")
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    """根据ID获取标签详情"""
    tag = TagService.get_tag_by_id(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    return tag

@tagsRouter.post("/", response_model=Tag, summary="创建标签")
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """创建新标签"""
    return TagService.create_tag(db, tag.name, tag.category_id)

@tagsRouter.put("/{tag_id}", response_model=Tag, summary="更新标签")
def update_tag(tag_id: int, tag: TagUpdate, db: Session = Depends(get_db)):
    """更新标签"""
    updated_tag = TagService.update_tag(db, tag_id, tag.name)
    if not updated_tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    return updated_tag

@tagsRouter.delete("/{tag_id}", summary="删除标签")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """删除标签"""
    success = TagService.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"message": "标签删除成功"}

@tagsRouter.put("/{tag_id}/category", response_model=Tag, summary="更新标签分类")
def update_tag_category(tag_id: int, category_id: int = None, db: Session = Depends(get_db)):
    """更新标签分类"""
    success = TagService.assign_tag_to_category(db, tag_id, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="标签不存在")
    return TagService.get_tag_by_id(db, tag_id)

@tagsRouter.get("/video/{video_id}", response_model=List[Tag], summary="获取视频标签")
def get_video_tags(video_id: int, db: Session = Depends(get_db)):
    """获取视频的所有标签"""
    return TagService.get_video_tags(db, video_id)

@tagsRouter.post("/video/{video_id}/tag/{tag_id}", summary="为视频添加标签")
def add_tag_to_video(video_id: int, tag_id: int, db: Session = Depends(get_db)):
    """为视频添加标签"""
    success = TagService.add_tag_to_video(db, video_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="视频或标签不存在")
    return {"message": "标签已添加到视频"}

@tagsRouter.delete("/video/{video_id}/tag/{tag_id}", summary="从视频移除标签")
def remove_tag_from_video(video_id: int, tag_id: int, db: Session = Depends(get_db)):
    """从视频中移除标签"""
    success = TagService.remove_tag_from_video(db, video_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="视频或标签不存在")
    return {"message": "标签已从视频中移除"}

@tagsRouter.put("/video/{video_id}/tags", summary="更新视频标签")
def update_video_tags(video_id: int, tags: VideoTagUpdate, db: Session = Depends(get_db)):
    """更新视频的标签（替换所有标签）"""
    success = TagService.update_video_tags(db, video_id, tags.tag_ids)
    if not success:
        raise HTTPException(status_code=404, detail="视频不存在")
    return {"message": "视频标签已更新"}