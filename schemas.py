from pydantic import BaseModel
from typing import Optional  # <--- import Optional


class DemoProjectSchema(BaseModel):
    title: str
    description: str
    doc_url: Optional[str] = None  # <--- use Optional instead of str | None

    class Config:
        orm_mode = True
