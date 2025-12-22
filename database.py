from sqlmodel import create_engine, SQLModel, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback for local development if not set, though Neon is requested.
# I will output a warning if it's not set.
if not DATABASE_URL:
    print("Warning: DATABASE_URL not found in environment variables.")
    # Default to sqlite for testing if really needed, but user asked for Neon.
    # DATABASE_URL = "sqlite:///./database.db" 

engine = create_engine(DATABASE_URL) if DATABASE_URL else None

def create_db_and_tables():
    if engine:
        SQLModel.metadata.create_all(engine)

def get_session():
    if not engine:
        raise RuntimeError("Database engine is not initialized. Check DATABASE_URL.")
    with Session(engine) as session:
        yield session

