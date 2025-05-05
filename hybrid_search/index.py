import requests
from requests.auth import HTTPBasicAuth
import json

import numpy as np
import pandas as pd

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from loguru import logger
import sys
import ast
# Initialize logger
logger.remove()
logger.add(sys.stdout, level="INFO")

import os
from dotenv import load_dotenv
load_dotenv()

OPENS_URL = "https://localhost:9200/productivity-tips/_bulk"
OPENS_AUTH=HTTPBasicAuth("admin", "Mind2@Mind")
OPENS_EMB_MODEL = os.environ.get("OPENS_EMB_MODEL")

DATABASE_URL = os.environ.get("DATABASE_URL")
table_name = 'emb_jina3' # emb_ada002 emb_jina3 emb_bert

headers = {"Content-Type": "application/x-ndjson"}
#headers = {"Content-Type": "application/json"}



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



def index_current_database():
    try:
        session : Session = SessionLocal()
    except ImportError:
        logger.error("SessionLocal not found!")
        return None
    
    # retrieve id, tip from database
    try:
        result = session.execute(text("SELECT id, short_desc, long_desc FROM recommendation"))
        
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)
    finally:
        session.close()

    # short_descs = df["short_desc"].tolist()
    input =[]
    for short, long in zip(df["short_desc"].tolist(), df['long_desc'].tolist()):
        input.append(f'{short} {long}')
    print(input[0])
    print(input[2])
    print(df)

    # retrieve id, tip from database
    try:
        emb_result = session.execute(text("SELECT id, emb FROM emb_jina3"))
        
        rows = emb_result.fetchall()
        columns = emb_result.keys()
        emb_df = pd.DataFrame(rows, columns=columns)
    finally:
        session.close()

    df['emb'] = [ast.literal_eval(v) for v in emb_df['emb'].tolist()]
    print(df['emb'].tolist()[0])
    print([len(v) for v in df['emb'].tolist()])
    print(df['long_desc'][0])

    # convert to json
    vectors = df['emb'].to_list()
    print(len(vectors))
    print(len(input))

    def l2_normalize(vec):
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm != 0 else vec

    # Build the bulk request body
    bulk_data = ""
    for _, row in df.iterrows():
        # Construct the full text field
        full_text = f"{row['short_desc']} {row['long_desc']}"

        # Metadata line with custom _id
        meta = { "index": { "_id": str(row["id"]) } }

        # Document body
        doc = {
            "text": full_text,
            "text_vector": l2_normalize(row["emb"])
        }

        # Append to bulk payload
        bulk_data += json.dumps(meta) + "\n"
        bulk_data += json.dumps(doc) + "\n"

    # Send the bulk request
    response = requests.post(
        OPENS_URL,
        headers=headers,
        data=bulk_data,
        auth=OPENS_AUTH,
        verify=False  # Only for local/OpenSearch dev setups with self-signed certs
    )

    # Output status
    print(response.status_code)
    print(json.dumps(response.json(), indent=2))