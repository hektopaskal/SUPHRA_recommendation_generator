from fastapi import FastAPI
from api.routes import router

from loguru import logger
import sys
# Initialize logger
logger.remove()
logger.add(sys.stdout, level="INFO")

from dotenv import load_dotenv 
load_dotenv()
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI(
    title="SUPHRA Recommendation API",
    description="Send a paper and get tailored recommendations.",
    version="0.1.0"
)

# Create DB connection pool
DATABASE_URL = os.getenv("DATABASE_URL")
# Engine for connection pool
logger.info("Initializing database connection pool")
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False
    )
    # SessionLocal hands out a session from the pool when needed
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize database connection pool: {e}")
    engine = None
    SessionLocal = None

app.include_router(router)

