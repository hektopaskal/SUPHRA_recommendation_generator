import mariadb
from mariadb import Connection
import sys
import pandas as pd
from pathlib import Path
import typer
from typing import Optional
from loguru import logger

# for similarity search with sentence embedding:
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter


# Create a Typer app
app = typer.Typer()


# Connect to MariaDB
def connect_to_db(
    login: dict
):
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
        conn: Connection,
        login: dict,
        recommendations: pd.DataFrame
):
    # build insertion statement
    table = login["table"]
    columns_str = ", ".join(recommendations.columns)  # columns as Str
    # value_subt = ["%s" for _ in range(len(recommendations.columns))] or :
    # SQL placeholder for values in statement
    value_subt = ", ".join(["%s"] * len(recommendations.columns))
    stmt = f"INSERT INTO {table} ({columns_str}) VALUES ({value_subt})"
    # insert recommendations row by row
    recommendations.astype(str)

    try:
        cursor = conn.cursor()
        for _, row in recommendations.iterrows():  # _ is index
            cursor.execute(stmt, tuple(row))
        conn.commit()
        logger.info("Successfully uploaded to the database.")
    except mariadb.Exception as e:
        logger.error(f"Error while uploading to the database: {e}")
    finally:
        cursor.close()
        logger.debug("Closed cursor after insert operation.")


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

    print("Data inserted successfully!")

# Delete recommendations by their ID


# Find similar recommendations via sentence embeddings


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


    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


    try:
        connection = mariadb.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        print("Connection successful!")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)

    cursor = connection.cursor()
    cursor.execute(f"SELECT id, short_desc FROM {table}")
    tips = cursor.fetchall()

    # Create DataFrame with 'Tip' and '#' (index) columns
    tips_df = pd.DataFrame(tips, columns=["id", "short_desc"])

    recommendations = tips_df["short_desc"].tolist()

    embeddings = model.encode(recommendations)

    # Perform Agglomerative Clustering
    agg_clustering = AgglomerativeClustering(
        n_clusters=None, distance_threshold=threshold, linkage='ward')
    labels = agg_clustering.fit_predict(embeddings)

    # Create a DataFrame to hold the cluster labels and their corresponding indices
    tips_df['Cluster'] = labels

    # Group by cluster and get the indices of tips in each cluster
    clustered_tips = tips_df.groupby(
        'Cluster')['id'].apply(list).reset_index()

    # Display the clusters with their corresponding IDs
    print(clustered_tips)
    print("_------------------------------------------")
    # Count the number of elements in each cluster
    cluster_counts = Counter(labels)

    # Find clusters with more than one element
    valid_clusters = [cluster for cluster,
                      count in cluster_counts.items() if count > 1]

    # Filter embeddings and labels to include only the valid clusters
    filtered_embeddings = []
    filtered_labels = []
    filtered_ids = []

    for i, label in enumerate(labels):
        if label in valid_clusters:
            filtered_embeddings.append(embeddings[i])
            filtered_labels.append(label)
            filtered_ids.append(tips_df.iloc[i]['ID'])

    filtered_embeddings = np.array(filtered_embeddings)
    filtered_labels = np.array(filtered_labels)
    filtered_ids = np.array(filtered_ids)

    # Display clusters with IDs
    for i in np.unique(filtered_labels):
        print(f"\nCluster {i}:")
        for idx, label in enumerate(filtered_labels):
            if label == i:
                print(
                    f" - ID: {filtered_ids[idx]}, Tip: {recommendations[idx]}")

    cursor.close()
    connection.close()

    return True




# run typer app
if __name__ == "__main__":
    app()
