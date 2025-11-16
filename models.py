from sqlalchemy import Column, Integer, String, Text
from db import Base


class Project(Base):
    """
    Database model for a project.
    """

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    tech_stack = Column(String(200), nullable=True)
    github_link = Column(String(200), nullable=True)
    demo_link = Column(String(200), nullable=True)
    image_url = Column(Text, nullable=True)  # store as stringified JSON
