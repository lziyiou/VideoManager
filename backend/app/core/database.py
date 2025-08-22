from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..models.setting import Setting, Base
from ..models.video import Video
from ..models.tag import Tag
from ..models.tag_category import TagCategory

SQLALCHEMY_DATABASE_URL = "sqlite:///./video_manager.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库表
init_db()