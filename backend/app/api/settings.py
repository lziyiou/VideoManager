from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.setting_service import SettingService
from ..schemas.settings import DirectoryPath, VideosPerPageSetting, SettingUpdate, SettingResponse
from typing import List, Dict

settingsRouter = APIRouter()

@settingsRouter.post("/root_directory")
def set_root_directory(directory_data: DirectoryPath, db: Session = Depends(get_db)):
    SettingService.set_root_directory(db, directory_data.directory_path)
    return {"message": "Root directory updated successfully"}

@settingsRouter.get("/root_directory")
def get_root_directory(db: Session = Depends(get_db)):
    root_dir = SettingService.get_root_directory(db)
    return {"root_directory": root_dir}

@settingsRouter.post("/videos_per_page")
def set_videos_per_page(setting_data: VideosPerPageSetting, db: Session = Depends(get_db)):
    SettingService.set_videos_per_page(db, setting_data.videos_per_page)
    return {"message": "Videos per page setting updated successfully"}

@settingsRouter.get("/videos_per_page")
def get_videos_per_page(db: Session = Depends(get_db)):
    videos_per_page = SettingService.get_videos_per_page(db)
    return {"videos_per_page": videos_per_page}

@settingsRouter.post("/setting")
def set_setting(setting_data: SettingUpdate, db: Session = Depends(get_db)):
    # 验证设置键的有效性
    valid_keys = ["root_directory", "videos_per_page"]
    if setting_data.key not in valid_keys:
        raise HTTPException(status_code=400, detail=f"Invalid setting key. Valid keys: {valid_keys}")
    
    SettingService.set_setting(db, setting_data.key, setting_data.value)
    return {"message": f"Setting '{setting_data.key}' updated successfully"}

@settingsRouter.get("/setting/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    value = SettingService.get_setting(db, key)
    if value is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": key, "value": value}

@settingsRouter.get("/settings")
def get_all_settings(db: Session = Depends(get_db)) -> List[Dict[str, str]]:
    return SettingService.get_all_settings(db)