import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Project
from db import get_db
from typing import List

router = APIRouter()

@router.get("/projects", response_model=List[dict])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    result = []
    for p in projects:
        images = []
        if p.image_url:
            try:
                images = json.loads(p.image_url)  # parse the string as JSON
            except json.JSONDecodeError:
                images = []  # fallback
        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "tech_stack": p.tech_stack,
            "github_link": p.github_link,
            "demo_link": p.demo_link,
            "images": images  # <-- send as proper list
        })
    return result
