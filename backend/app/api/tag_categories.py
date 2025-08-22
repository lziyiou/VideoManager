from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..services.tag_category_service import TagCategoryService
from ..schemas.tag_categories import TagCategory, TagCategoryCreate, TagCategoryUpdate

tagCategoriesRouter = APIRouter()

@tagCategoriesRouter.get("/", response_model=List[TagCategory], summary="获取所有标签分类")
def get_all_tag_categories(db: Session = Depends(get_db)):
    """获取所有标签分类"""
    categories = TagCategoryService.get_all_categories(db)
    return categories

@tagCategoriesRouter.get("/{category_id}", response_model=TagCategory, summary="获取标签分类详情")
def get_tag_category(category_id: int, db: Session = Depends(get_db)):
    """根据ID获取标签分类详情"""
    category = TagCategoryService.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="标签分类不存在")
    return category

@tagCategoriesRouter.post("/", response_model=TagCategory, summary="创建标签分类")
def create_tag_category(category: TagCategoryCreate, db: Session = Depends(get_db)):
    """创建新标签分类"""
    return TagCategoryService.create_category(db, category)

@tagCategoriesRouter.put("/{category_id}", response_model=TagCategory, summary="更新标签分类")
def update_tag_category(category_id: int, category: TagCategoryUpdate, db: Session = Depends(get_db)):
    """更新标签分类"""
    updated_category = TagCategoryService.update_category(db, category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="标签分类不存在")
    return updated_category

@tagCategoriesRouter.delete("/{category_id}", summary="删除标签分类")
def delete_tag_category(category_id: int, db: Session = Depends(get_db)):
    """删除标签分类"""
    success = TagCategoryService.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="标签分类不存在")
    return {"message": "标签分类已删除"}

@tagCategoriesRouter.get("/{category_id}/tags", summary="获取分类下的所有标签")
def get_category_tags(category_id: int, db: Session = Depends(get_db)):
    """获取指定分类下的所有标签"""
    tags = TagCategoryService.get_category_tags(db, category_id)
    return tags