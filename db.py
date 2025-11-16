from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace this URL with your Neon database URL
SQLALCHEMY_DATABASE_URL = (
    "postgresql://neondb_owner:npg_ks2jo6taYDZF@ep-floral-poetry-ahdnyg9y-pooler.c-3.us-east-1.aws.neon.tech/"
    "neondb?sslmode=require&channel_binding=require"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency to get a SQLAlchemy DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
