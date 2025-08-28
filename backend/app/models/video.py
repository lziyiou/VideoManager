from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .setting import Base
from .tag import video_tag

class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String, unique=True)
    size = Column(Float)  # 文件大小（MB）
    duration = Column(Float)  # 视频时长（秒）
    thumbnail_path = Column(String, nullable=True)  # 缩略图路径
    is_favorite = Column(Boolean, default=False)  # 是否收藏
    web_playable = Column(Boolean, default=True)  # 是否可以在网页播放
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    thumbnail_generated = Column(Boolean, default=False)  # 缩略图是否已生成
    
    # 播放进度相关字段
    last_position = Column(Float, default=0.0)  # 最后播放位置（秒）
    watch_progress = Column(Float, default=0.0)  # 观看进度百分比（0-100）
    last_watched_at = Column(DateTime, nullable=True)  # 最后观看时间
    is_completed = Column(Boolean, default=False)  # 是否已看完
    
    # 与Tag模型建立多对多关系
    tags = relationship("Tag", secondary=video_tag, back_populates="videos")