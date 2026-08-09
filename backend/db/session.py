import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base

def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres:postgres@localhost:5432/postgres"
    
    # Remove channel_binding param (not supported by psycopg conninfo)
    if "channel_binding" in database_url:
        import re
        database_url = re.sub(r'[&?]channel_binding=[^&]*', '', database_url)
    
    # SQLAlchemy requires the +psycopg driver prefix
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
    engine = create_engine(database_url)
    return engine

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
