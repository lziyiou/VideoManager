from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .setting import Base

class TagCategory(Base):
    __tablename__ = 'tag_categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(String, default='#409EFF')  # 分类颜色，默认为蓝色
    sort_order = Column(Integer, default=0)  # 排序字段，数值越小越靠前
    description = Column(String, nullable=True)  # 分类描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 与Tag模型建立一对多关系
    tags = relationship("Tag", back_populates="category")