from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy import func
from ..models.tag_category import TagCategory
from ..models.tag import Tag
from ..schemas.tag_categories import TagCategoryCreate, TagCategoryUpdate

class TagCategoryService:
    @staticmethod
    def get_all_categories(db: Session) -> List[TagCategory]:
        """获取所有标签分类，按排序字段排序，包含标签数量统计"""
        categories = db.query(TagCategory).order_by(TagCategory.sort_order, TagCategory.name).all()
        
        # 为每个分类添加标签数量统计
        for category in categories:
            tags_count = db.query(func.count(Tag.id)).filter(Tag.category_id == category.id).scalar()
            category.tags_count = tags_count or 0
            
        return categories
    
    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[TagCategory]:
        """根据ID获取标签分类"""
        return db.query(TagCategory).filter(TagCategory.id == category_id).first()
    
    @staticmethod
    def get_category_by_name(db: Session, name: str) -> Optional[TagCategory]:
        """根据名称获取标签分类"""
        return db.query(TagCategory).filter(TagCategory.name == name).first()
    
    @staticmethod
    def create_category(db: Session, category_data: TagCategoryCreate) -> TagCategory:
        """创建新标签分类"""
        # 检查分类是否已存在
        existing_category = TagCategoryService.get_category_by_name(db, category_data.name)
        if existing_category:
            raise ValueError(f"标签分类 '{category_data.name}' 已存在")
            
        # 创建新分类
        category = TagCategory(
            name=category_data.name,
            color=category_data.color or '#409EFF',
            sort_order=category_data.sort_order or 0,
            description=category_data.description
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def update_category(db: Session, category_id: int, category_data: TagCategoryUpdate) -> Optional[TagCategory]:
        """更新标签分类"""
        category = TagCategoryService.get_category_by_id(db, category_id)
        if not category:
            return None
            
        # 更新字段
        if category_data.name is not None:
            # 检查新名称是否与其他分类冲突
            existing_category = TagCategoryService.get_category_by_name(db, category_data.name)
            if existing_category and existing_category.id != category_id:
                raise ValueError(f"标签分类 '{category_data.name}' 已存在")
            category.name = category_data.name
            
        if category_data.color is not None:
            category.color = category_data.color
            
        if category_data.sort_order is not None:
            category.sort_order = category_data.sort_order
            
        if category_data.description is not None:
            category.description = category_data.description
            
        category.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def delete_category(db: Session, category_id: int) -> bool:
        """删除标签分类"""
        category = TagCategoryService.get_category_by_id(db, category_id)
        if not category:
            return False
            
        # 将该分类下的标签的category_id设为None
        db.query(Tag).filter(Tag.category_id == category_id).update({Tag.category_id: None})
        
        # 删除分类
        db.delete(category)
        db.commit()
        return True
    
    @staticmethod
    def get_category_tags(db: Session, category_id: int) -> List[Tag]:
        """获取指定分类下的所有标签"""
        return db.query(Tag).filter(Tag.category_id == category_id).all()
    
    @staticmethod
    def get_uncategorized_tags(db: Session) -> List[Tag]:
        """获取未分类的标签"""
        return db.query(Tag).filter(Tag.category_id.is_(None)).all()