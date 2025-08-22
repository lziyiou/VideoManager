from sqlalchemy.orm import Session
from typing import List, Dict
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
    def get_all_settings(db: Session) -> List[Dict[str, str]]:
        settings = db.query(Setting).all()
        return [{'key': setting.key, 'value': setting.value} for setting in settings]