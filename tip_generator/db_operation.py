import pandas as pd
from sentence_transformers import SentenceTransformer
import json

# from litellm import embedding

from sqlalchemy import text, insert, bindparam
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.types import String
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import SET, ENUM, TINYINT, YEAR

import sys
from dotenv import load_dotenv
import os
# load environment variables
load_dotenv()
EMB_TABLE = os.environ.get("EMB_TABLE")
OPENS_EMB_MODEL = os.environ.get("OPENS_EMB_MODEL")

import typer
from loguru import logger

# initialize typer and loguru
app = typer.Typer()
logger.remove()
logger.add(sys.stdout, level="INFO")

# SQLAlchemy ORM model

Base = declarative_base()

class Recommendation(Base):
    """
    SQLAlchemy model for the recommendation table.
    """
    __tablename__ = "recommendation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_desc = Column(String(128), nullable=True)  # VARCHAR(128)
    long_desc = Column(String(500), nullable=True)  # VARCHAR(500)
    
    goal = Column(ENUM('augment', 'prevent', 'recover', 'maintain'), nullable=True)  # ENUM
    
    activity_type = Column(ENUM('time management', 'exercise', 'cognitive', 'relax', 'social'), nullable=True)  # ENUM
    
    categories = Column(SET(
        'work', 'success', 'productivity', 'performance', 'focus', 'time management', 
        'happiness', 'mental', 'active reflection', 'awareness', 'well-being', 'health', 'fitness', 'social'
    ), nullable=True)  # SET
    
    concerns = Column(SET(
        'goal-setting', 'self-motivation', 'self-direction', 'self-discipline', 'focus', 
        'mindset', 'time management', 'procrastination', 'stress management', 'mental-health', 
        'work-life balance', 'sleep quality'
    ), nullable=True)  # SET
    
    daytime = Column(ENUM('any', 'morning', 'noon', 'evening', 'end of day'), nullable=True)  # ENUM
    
    weekdays = Column(ENUM('any', 'workdays', 'weekend', 'week start', 'end of workweek', 'public holiday'), nullable=True)  # ENUM
    
    season = Column(ENUM('any', 'spring', 'summer', 'autumn', 'winter', 'holiday season', 'summer vacation'), nullable=True)  # ENUM
    
    is_outdoor = Column(TINYINT(1), nullable=True)  # TINYINT (Boolean)
    is_basic = Column(TINYINT(1), nullable=True)  # TINYINT (Boolean)
    is_advanced = Column(TINYINT(1), nullable=True)  # TINYINT (Boolean)

    gender = Column(String(50), nullable=True)  # VARCHAR(50)
    src_title = Column(String(128), nullable=True)  # VARCHAR(128)
    src_reference = Column(Text, nullable=True)  # TEXT
    src_pub_year = Column(YEAR, nullable=True)  # YEAR
    src_pub_type = Column(String(50), nullable=True)  # VARCHAR(50)
    src_field_of_study = Column(String(64), nullable=True)  # VARCHAR(64)
    src_doi = Column(String(255), nullable=True)  # VARCHAR(255)
    src_hyperlink = Column(String(255), nullable=True)  # VARCHAR(255)
    src_pub_venue = Column(String(255), nullable=True)  # VARCHAR(255)
    src_citations = Column(Integer, nullable=True)  # INT
    src_cit_influential = Column(Integer, nullable=True)  # INT

class Embedding(Base):
    """
    SQLAlchemy model for the embeddings table.
    """
    __tablename__ = EMB_TABLE

    id = Column(Integer, primary_key=True)
    emb = Column(Text)  # VECTOR(1536)


def insert_into_db(
        recommendations: pd.DataFrame
):
    
    #Inserts recommendations that are stored in pandas DataFrame with already matching column names!
    
    # build insertion statement
    rows = recommendations.to_dict(orient="records")
    try:
        from app import SessionLocal
        session : Session = SessionLocal()
    except ImportError:
        logger.error("SessionLocal not found!")
        return None
    # Bulk insert recommendations
    session.execute(insert(Recommendation), rows)
    logger.info("Successfully inserted recommendations into the database.")
    # Query 'id' and 'short_desc' of inserted recommendations
    result = session.execute(text("SELECT id, short_desc FROM recommendation WHERE id >= LAST_INSERT_ID()"))
    result = [tuple(row) for row in result.fetchall()]
    short_descs = [row[1] for row in result]

    """
    # Calculate embeddings with ada002 OpenAI model
    try:
        # Extract embeddings
        emb = embedding(model='text-embedding-ada-002', input=short_descs)
        emb = [e["embedding"] for e in emb["data"]] # cut off metadata from response
        logger.info(f"Successfully extracted embeddings for {len(emb)} recommendations.")
        #logger.info("Successfully extracted embeddings.")
    except Exception as e:
        logger.error(f"Error while extracting embeddings: {e}")
        return None
    """
    
    # load local embedding model
    try:
        model = SentenceTransformer(OPENS_EMB_MODEL, trust_remote_code=True, device="cpu")
        logger.info(f"{OPENS_EMB_MODEL} loaded successfully!")
    except Exception as e:
        logger.info(f"Error loading {OPENS_EMB_MODEL}: {e}")
        return None
    # calculate query vector
    try:
        emb = model.encode(short_descs, convert_to_tensor=True, device="cpu")
        logger.info('Query text encoded successfully.')
    except Exception as e:
        logger.info(f"Error encoding query text: {e}")
        return None

    emb = emb.numpy().tolist()
    # Prepare the embeddings for sqlalchemy bulk insertion
    embeddings_data = [
        {"id": int(row[0]), "emb": json.dumps(emb[i])} for i, row in enumerate(result)
    ]
    # Build and execute the insert statement
    stmt = insert(Embedding).values(
    id=bindparam("id"),
    emb=bindparam("emb")
    )
    try:
        session.execute(stmt, embeddings_data)
        logger.debug("Successfully inserted embeddings into the database.")
        session.commit()
        logger.debug("Committed the transaction.")
        logger.info("Upload completed.")
    # Return List of ids of inserted recommendations
    except Exception as e:
        raise Exception(f"DB-Operation: Error while inserting data: {e}")
    finally:
        session.close()
        logger.debug("Closed cursor after insert operation.")

# Delete recommendations by their ID? TODO

# run typer app
if __name__ == "__main__":
    app()
