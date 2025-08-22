from sqlalchemy import Column, String, Integer, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .setting import Base

# 定义视频和标签的多对多关联表
video_tag = Table(
    'video_tag',
    Base.metadata,
    Column('video_id', Integer, ForeignKey('videos.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category_id = Column(Integer, ForeignKey('tag_categories.id'), nullable=True)  # 标签分类外键
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 与Video模型建立多对多关系
    videos = relationship("Video", secondary=video_tag, back_populates="tags")
    # 与TagCategory模型建立多对一关系
    category = relationship("TagCategory", back_populates="tags")