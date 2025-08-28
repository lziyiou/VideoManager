from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from ..models.setting import Setting

class SettingService:
    @staticmethod
    def set_root_directory(db: Session, directory_path: str):
        setting = db.query(Setting).filter(Setting.key == "root_directory").first()
        if setting:
            setting.value = directory_path
        else:
            setting = Setting(key="root_directory", value=directory_path)
            db.add(setting)
        db.commit()

    @staticmethod
    def get_root_directory(db: Session) -> str:
        setting = db.query(Setting).filter(Setting.key == "root_directory").first()
        return setting.value if setting else None
    
    @staticmethod
    def set_videos_per_page(db: Session, videos_per_page: int):
        setting = db.query(Setting).filter(Setting.key == "videos_per_page").first()
        if setting:
            setting.value = str(videos_per_page)
        else:
            setting = Setting(key="videos_per_page", value=str(videos_per_page))
            db.add(setting)
        db.commit()
    
    @staticmethod
    def get_videos_per_page(db: Session) -> int:
        setting = db.query(Setting).filter(Setting.key == "videos_per_page").first()
        return int(setting.value) if setting else 20  # 默认每页20个视频
    
    @staticmethod
    def set_setting(db: Session, key: str, value: str):
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.add(setting)
        db.commit()
    
    @staticmethod
    def get_setting(db: Session, key: str) -> Optional[str]:
        setting = db.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else None
        
    @staticmethod
    def get_all_settings(db: Session) -> List[Dict[str, str]]:
        settings = db.query(Setting).all()
        return [{'key': setting.key, 'value': setting.value} for setting in settings]