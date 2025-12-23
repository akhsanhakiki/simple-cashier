from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Warning: DATABASE_URL not found in environment variables.")

# Connection pooling optimized for free tier (Render + Neon)
# - pool_size: Keep 2 connections ready (Neon free tier has connection limits)
# - max_overflow: Allow up to 3 extra connections when needed
# - pool_pre_ping: Verify connections before using (important for free tiers that may close idle connections)
# - pool_recycle: Recycle connections after 3 minutes (free tiers may close idle connections)
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=2,
    max_overflow=3,
    pool_pre_ping=True,
    pool_recycle=180,  # 3 minutes
    echo=False,  # Disable SQL logging in production
    connect_args={
        "connect_timeout": 5,
        "sslmode": "require"
    }
) if DATABASE_URL else None

def create_db_and_tables():
    if engine:
        SQLModel.metadata.create_all(engine)

def get_session():
    if not engine:
        raise RuntimeError("Database engine is not initialized. Check DATABASE_URL.")
    with Session(engine) as session:
        yield session

