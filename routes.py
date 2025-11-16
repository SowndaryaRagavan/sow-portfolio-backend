import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from models import Project

router = APIRouter()


@router.get("/projects")
def get_projects(db: Session = Depends(get_db)):
    """
    Fetch all projects from the database and parse image URLs as a list.
    """
    projects = db.query(Project).all()
    result = []

    for p in projects:
        images = []
        if p.image_url:
            try:
                images = json.loads(p.image_url)  # parse stringified JSON
            except json.JSONDecodeError:
                images = []

        result.append(
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "tech_stack": p.tech_stack,
                "github_link": p.github_link,
                "demo_link": p.demo_link,
                "images": images,
            }
        )
    return result
