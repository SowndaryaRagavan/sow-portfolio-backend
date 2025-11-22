# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from supabase import create_client, Client
from db import get_db
from models import Project, DemoProject
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------- FastAPI setup ---------------- #
app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://sowndarya-ragavan.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Supabase Storage setup ---------------- #
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "demo-pdfs"  # Ensure this bucket exists

# ---------------- Projects Endpoints ---------------- #
@app.get("/projects")
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    result = []
    for p in projects:
        images = []
        if p.image_url:
            try:
                import json
                images = json.loads(p.image_url)
            except json.JSONDecodeError:
                images = []
        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "tech_stack": p.tech_stack,
            "github_link": p.github_link,
            "demo_link": p.demo_link,
            "images": images
        })
    return result

# ---------------- Demo Projects Endpoints ---------------- #
@app.get("/demo-projects")
def get_demo_projects(db: Session = Depends(get_db)):
    projects = db.query(DemoProject).all()
    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "doc_url": p.doc_url
        })
    return result

@app.get("/demo-projects/{project_id}")
def get_demo_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(DemoProject).filter(DemoProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.post("/demo-projects/upload")
async def add_demo_project(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        filename = f"uploads/{file.filename}"  # safer path

        # Upload PDF to Supabase
        supabase.storage.from_(BUCKET_NAME).upload(
            filename, content, {"cacheControl": "3600"}
        )

        doc_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename).public_url

        # Save record in DB
        db_project = DemoProject(title=title, description=description, doc_url=doc_url)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.delete("/demo-projects/{project_id}")
def delete_demo_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(DemoProject).filter(DemoProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete PDF from Supabase Storage
    if project.doc_url:
        try:
            filename = project.doc_url.split("/")[-1]
            supabase.storage.from_(BUCKET_NAME).remove([filename])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    # Delete record from DB
    db.delete(project)
    db.commit()
    return {"detail": "Project deleted successfully"}
