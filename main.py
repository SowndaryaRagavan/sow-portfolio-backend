# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from supabase import create_client, Client
from db import get_db
from models import Project, DemoProject
import os
from dotenv import load_dotenv
import re

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


@app.get("/check-env")
def check_env():
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY_SET": bool(os.getenv("SUPABASE_KEY")),
        "BUCKET_NAME": os.getenv("BUCKET_NAME")
    }


@app.post("/demo-projects/upload")
async def add_demo_project(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    print("UPLOAD API HIT")
    try:
        content = await file.read()
        print("FILE RECEIVED:", len(content))
        filename = f"uploads/{file.filename}"

        bucket = supabase.storage.from_(BUCKET_NAME)

        # Step 1 → If file exists, delete it
        try:
            bucket.remove([filename])
        except:
            pass  # ignore if not found

        # Step 2 → Upload fresh file
        bucket.upload(filename, content, {"cacheControl": "3600"})

        # Step 3 → Get public URL
        doc_url = bucket.get_public_url(filename)
        print("PUBLIC PDF URL:", doc_url)

        # Step 4 → Save DB
        db_project = DemoProject(
            title=title,
            description=description,
            doc_url=doc_url
        )
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

    try:
        # Extract correct relative Supabase path
        # Example public URL:
        # https://xxx.supabase.co/storage/v1/object/public/demo-pdfs/uploads/myfile.pdf
        #
        # We need: uploads/myfile.pdf
        parts = project.doc_url.split("/")
        relative_path = "/".join(parts[-2:])  # uploads/myfile.pdf

        # Delete from Supabase bucket
        supabase.storage.from_(BUCKET_NAME).remove([relative_path])

        # Delete from DB
        db.delete(project)
        db.commit()

        return {"message": "Project deleted successfully"}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

