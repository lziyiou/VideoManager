from fastapi import FastAPI
import uvicorn
from app.api.settings import settingsRouter
from app.api.videos import videosRouter
from app.api.tags import tagsRouter
from app.api.tag_categories import tagCategoriesRouter

app = FastAPI(
    title="Video Manager",
    description="一个简单高效的本地视频管理系统"
)

app.include_router(settingsRouter, prefix="/api/settings", tags=["Settings"])
app.include_router(videosRouter, prefix="/api/videos", tags=["Videos"])
app.include_router(tagsRouter, prefix="/api/tags", tags=["Tags"])
app.include_router(tagCategoriesRouter, prefix="/api/tag-categories", tags=["Tag Categories"])


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="localhost", port=8000, reload=True)
