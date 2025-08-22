from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.setting_service import SettingService
from ..schemas.settings import DirectoryPath
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

@settingsRouter.get("/settings")
def get_all_settings(db: Session = Depends(get_db)) -> List[Dict[str, str]]:
    return SettingService.get_all_settings(db)