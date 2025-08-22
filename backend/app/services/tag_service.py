from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy import func
from ..models.tag import Tag, video_tag
from ..models.video import Video
from ..models.tag_category import TagCategory

class TagService:
    @staticmethod
    def get_all_tags(db: Session) -> List[Tag]:
        """获取所有标签，包含分类信息和标签统计"""
        # 获取所有标签，包含分类信息
        tags = (
            db.query(Tag)
            .outerjoin(TagCategory, Tag.category_id == TagCategory.id)
            .all()
        )
        
        # 为每个标签设置tags_count属性
        for tag in tags:
            tag_count = (
                db.query(func.count(video_tag.c.video_id))
                .filter(video_tag.c.tag_id == tag.id)
                .scalar()
            )
            tag.tags_count = tag_count or 0
            
        return tags
    
    @staticmethod
    def get_tag_by_id(db: Session, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签"""
        return db.query(Tag).filter(Tag.id == tag_id).first()
    
    @staticmethod
    def get_tag_by_name(db: Session, name: str) -> Optional[Tag]:
        """根据名称获取标签"""
        return db.query(Tag).filter(Tag.name == name).first()
    
    @staticmethod
    def create_tag(db: Session, name: str, category_id: Optional[int] = None) -> Tag:
        """创建新标签"""
        # 检查标签是否已存在
        existing_tag = TagService.get_tag_by_name(db, name)
        if existing_tag:
            return existing_tag
            
        # 创建新标签
        tag = Tag(name=name, category_id=category_id)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    
    @staticmethod
    def update_tag(db: Session, tag_id: int, name: str) -> Optional[Tag]:
        """更新标签"""
        tag = TagService.get_tag_by_id(db, tag_id)
        if not tag:
            return None
            
        tag.name = name
        tag.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tag)
        return tag
    
    @staticmethod
    def delete_tag(db: Session, tag_id: int) -> bool:
        """删除标签"""
        tag = TagService.get_tag_by_id(db, tag_id)
        if not tag:
            return False
            
        db.delete(tag)
        db.commit()
        return True
    
    @staticmethod
    def get_tags_by_category(db: Session, category_id: Optional[int] = None) -> List[Tag]:
        """根据分类获取标签"""
        if category_id is None:
            # 获取未分类的标签
            return db.query(Tag).filter(Tag.category_id.is_(None)).all()
        else:
            # 获取指定分类的标签
            return db.query(Tag).filter(Tag.category_id == category_id).all()
    
    @staticmethod
    def get_tags_grouped_by_category(db: Session) -> dict:
        """获取按分类分组的标签"""
        # 获取所有分类
        categories = db.query(TagCategory).order_by(TagCategory.sort_order, TagCategory.name).all()
        # 获取未分类的标签
        uncategorized_tags = db.query(Tag).filter(Tag.category_id.is_(None)).all()
        
        result = {}
        
        # 添加分类及其标签
        for category in categories:
            category_tags = db.query(Tag).filter(Tag.category_id == category.id).all()
            if category_tags:  # 只添加有标签的分类
                result[category.name] = {
                    'category': category,
                    'tags': category_tags
                }
        
        # 添加未分类的标签
        if uncategorized_tags:
            result['未分类'] = {
                'category': None,
                'tags': uncategorized_tags
            }
        
        return result
    
    @staticmethod
    def assign_tag_to_category(db: Session, tag_id: int, category_id: Optional[int]) -> bool:
        """将标签分配到指定分类"""
        tag = TagService.get_tag_by_id(db, tag_id)
        if not tag:
            return False
        
        # 如果指定了分类ID，检查分类是否存在
        if category_id is not None:
            category = db.query(TagCategory).filter(TagCategory.id == category_id).first()
            if not category:
                return False
        
        tag.category_id = category_id
        tag.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def get_video_tags(db: Session, video_id: int) -> List[Tag]:
        """获取视频的所有标签"""
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return []
        return video.tags
    
    @staticmethod
    def add_tag_to_video(db: Session, video_id: int, tag_id: int) -> bool:
        """为视频添加标签"""
        video = db.query(Video).filter(Video.id == video_id).first()
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not video or not tag:
            return False
            
        # 检查标签是否已添加到视频
        if tag not in video.tags:
            video.tags.append(tag)
            db.commit()
        
        return True
    
    @staticmethod
    def remove_tag_from_video(db: Session, video_id: int, tag_id: int) -> bool:
        """从视频中移除标签"""
        video = db.query(Video).filter(Video.id == video_id).first()
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not video or not tag:
            return False
            
        # 检查标签是否已添加到视频
        if tag in video.tags:
            video.tags.remove(tag)
            db.commit()
        
        return True
    
    @staticmethod
    def update_video_tags(db: Session, video_id: int, tag_ids: List[int]) -> bool:
        """更新视频的标签（替换所有标签）"""
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return False
            
        # 清空现有标签
        video.tags = []
        
        # 添加新标签
        for tag_id in tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if tag:
                video.tags.append(tag)
        
        db.commit()
        return True