from pydantic import BaseModel

class DirectoryPath(BaseModel):
    directory_path: str