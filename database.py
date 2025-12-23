from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Warning: DATABASE_URL not found in environment variables.")

# Connection pooling optimized for free tier (Render + Neon)
# - pool_size: Keep 3 connections ready (optimized for better performance)
# - max_overflow: Allow up to 5 extra connections when needed
# - pool_pre_ping: Verify connections before using (important for free tiers that may close idle connections)
# - pool_recycle: Recycle connections after 2 minutes (free tiers may close idle connections faster)
# - pool_timeout: Timeout for getting connection from pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=3,  # Increased from 2 for better performance
    max_overflow=5,  # Increased from 3 for better concurrency
    pool_pre_ping=True,
    pool_recycle=120,  # Reduced from 180 (2 minutes) for faster connection refresh
    pool_timeout=10,  # Added timeout for getting connection from pool
    echo=False,  # Disable SQL logging in production
    connect_args={
        "connect_timeout": 3,  # Reduced from 5 for faster failure detection
        "sslmode": "require",
        "application_name": "simple_cashier"  # Helpful for database monitoring
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

