import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# VIDEO_FOLDER = r"D:\MyVideos"  # 修改为你的视频目录
VIDEO_FOLDER = r"E:/java/vid"  # 修改为你的视频目录
COVERS_FOLDER = os.path.join(BASE_DIR, "static", "covers")


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
