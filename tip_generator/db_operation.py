import mariadb
from mariadb import Connection
from sqlalchemy import text, insert
from sqlalchemy.orm import Session
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import SET, ENUM, TINYINT, YEAR
from sqlalchemy.ext.declarative import declarative_base

import sys
import pandas as pd
from pathlib import Path
import json

import typer
from typing import Optional
from loguru import logger
import traceback

# for similarity search with sentence embedding:
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
import hdbscan

from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

from litellm import embedding

# initialize typer and loguru
app = typer.Typer()
logger.remove()
logger.add(sys.stdout, level="INFO")


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
    __tablename__ = "embedding"

    id = Column(Integer, primary_key=True)
    embedding = Column(Text)  # VECTOR(1536)


# Connect to MariaDB
def connect_to_db(
    login: dict
)-> Connection:
    try:
        conn = mariadb.connect(
            user=login["user"],
            password=login["password"],
            host=login["host"],  # or 127.0.0.1
            port=login["port"],  # default mariadb port
            database=login["database"]
        )
        logger.info("Successfully connected to the database.")
        return conn
    except mariadb.Error as e:
        logger.error(f"Error while connecting to the database: {e}")
        return None


def insert_into_db(
        table : str,
        recommendations: pd.DataFrame
):
    """
    Inserts recommendations that are stored in pandas DataFrame with already matching column names!
    """
    # build insertion statement
    table = table
    rows = recommendations.to_dict(orient="records")
    try:
        from app import SessionLocal
    except ImportError:
        logger.error("SessionLocal not found!")
        return None
    # Try to insert recommendations and there corresponding embeddings
    try: # TODO seperate into more try-except blocks
        # Create session
        session : Session = SessionLocal()
        # Bulk insert recommendations
        session.execute(insert(Recommendation), rows)
        logger.debug("Successfully inserted recommendations into the database.")
        # Query 'id' and 'short_desc' of inserted recommendations
        result = session.execute(text("SELECT id, short_desc FROM recommendation WHERE id >= LAST_INSERT_ID()"))
        result = [tuple(row) for row in result.fetchall()]
        short_descs = [row[1] for row in result]
        # Extract embeddings
        emb = embedding(model='text-embedding-ada-002', input=short_descs)
        emb = [e["embedding"] for e in emb["data"]] # cut off metadata from response
        logger.debug("Successfully extracted embeddings.")
        # Prepare the embeddings for sqlalchemy bulk insertion
        embeddings_data = [
            {"id": int(row[0]), "embedding": json.dumps(emb[i])} for i, row in enumerate(result)
        ]
        # Build and execute the insert statement
        stmt = insert(Embedding).values(
            id=text(":id"),
            embedding=text("Vec_FromText(:embedding)")
        )
        session.execute(stmt, embeddings_data)
        logger.debug("Successfully inserted embeddings into the database.")
        session.commit()
        logger.debug("Committed the transaction.")
        logger.info("Upload completed.")
        # Return List of ids of inserted recommendations
    except mariadb.Error as e:
        if e.errno == 1146:
            raise Exception("Table does not exist!")
        else:
            logger.error(f"Error while uploading to the database: {e}")
    finally:
        session.close()
        logger.debug("Closed cursor after insert operation.")

# Delete recommendations by their ID? TODO


# Find similar recommendations via sentence embeddings
def find_similarities(
        conn: Connection,
        table: str,
        th: int #treshold for semantic similarity clustering
):
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    cursor = conn.cursor()
    cursor.execute(f"SELECT id, short_desc FROM {table}")
    table = cursor.fetchall() #comes as list of tuples(=rows)
    tabledf = pd.DataFrame(table)
    embeddings = model.encode(tabledf[1].to_list()) # extract tips scince id is not supposed to be embedded


    print()
    print(tabledf)
    print()

    # Perform Agglomerative Clustering
    agg_clustering = AgglomerativeClustering(
        n_clusters=None, distance_threshold=th, linkage='ward')
    
    agg_table = pd.DataFrame(tabledf)
    print("AGGTABLE")
    print(agg_table)
    print()


    print("TABLEDF")
    print(tabledf)
    print()
    print("#####################################################################")
    agg_table[2] = agg_clustering.fit_predict(embeddings)

    print("AGGTABLE")
    print(agg_table)
    print()


    print("TABLEDF")
    print(tabledf)
    print()
    agg_table.columns = ["id", "tip", "cluster"]
    #grouped_df = tabledf.sort_values(by='cluster').reset_index(drop=True)

    # Perform HDBSCAN CLUSTERING
    hdb_clustering = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1)
    hdb_clustering.fit(embeddings)
    hdb_table = pd.DataFrame(tabledf)
    hdb_table[2] = hdb_clustering.labels_

    print("HDBTABLE")
    print(hdb_table)
    print()

    hdb_table.columns = ["id", "tip", "cluster"]

    return agg_table.sort_values(by='cluster').reset_index(drop=True), hdb_table.sort_values(by='cluster').reset_index(drop=True)

@app.command()
def find_similarities_command(
    threshold: Optional[float] = typer.Option(
        4, help="Threshold for clustering. Set to 4, if not specified")
):
    """Find tips that are semantically similar."""

    user = "root"
    password = "rootpw"
    host = "localhost"
    port = 3306
    database = "copy_fellmann"
    table = "recommendation"
    try:
        connection = mariadb.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        logger.info("Connection successful!")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)

    agg_clusters, hdb_clusters = find_similarities(connection,table, threshold)

    print("AGGLOMERATIVE CLUSTERING")
    print("######################################################################")
    print(agg_clusters)
    print("######################################################################")
    print()
    print("HDBSCAN")
    print("######################################################################")
    print(hdb_clusters)
    print("######################################################################")



@app.command()
def insert_data_from_csv(csv_file_path: str = typer.Argument(..., help="Path to csv file")):
    """Give Path to csv_file and insert data from a CSV file into MariaDB."""

    connection = 0
    cursor = connection.cursor()

    df = pd.read_csv(csv_file_path)
    df = df.astype(str)

    for _, row in df.iterrows():  # _ is index
        sql_query = "INSERT INTO pt_recommendations (Tip, Information, Category, Goal, Focus, Activity_type, Daytime, Weekday, Validity_Flag, Weather, Concerns, AuthorsPaperCountCitationCount, citationCount, fieldsOfStudy, influentialCitationCount, publicationDate, publicationTypes, publicationVenue, referenceCount, title, tldr, url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql_query, tuple(row))

    connection.commit()
    cursor.close()
    connection.close()

    logger.info("Data inserted successfully!")


# run typer app
if __name__ == "__main__":
    app()
