from sentence_transformers import SentenceTransformer
import requests
from requests.auth import HTTPBasicAuth
import json

from loguru import logger
import sys
# Initialize logger
logger.remove()
logger.add(sys.stdout, level="INFO")

import os
from dotenv import load_dotenv
load_dotenv()

OPENS_URL = "https://localhost:9200/productivity-tips/_search"
OPENS_AUTH=HTTPBasicAuth("admin", "Mind2@Mind")
OPENS_EMB_MODEL = os.environ.get("OPENS_EMB_MODEL")

def find_matching_rec(query_text: str):
    """
    Find matching recommendations using hybrid search.
    """
    headers = {"Content-Type": "application/json"}
    # load local embedding model
    try:
        #model = AutoModel.from_pretrained(OPENS_EMB_MODEL, trust_remote_code=True)
        model = SentenceTransformer(OPENS_EMB_MODEL, trust_remote_code=True, device="cpu")
        logger.info(f"{OPENS_EMB_MODEL} loaded successfully!")
    except Exception as e:
        logger.info(f"Error loading {OPENS_EMB_MODEL}: {e}")
        return None
    # calculate query vector
    try:
        vector = model.encode([query_text], convert_to_tensor=True, device="cpu")
        logger.info('Query text encoded successfully.')
    except Exception as e:
        logger.info(f"Error encoding query text: {e}")
        return None

    vector = vector.numpy().tolist()[0]

    # prepare hybrid query
    query_body = {
        "size": 5,
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "text": query_text
                        }
                    },
                    {
                        "knn": {
                            "text_vector": {
                                "vector": vector,
                                "k": 1024,
                            }
                        }
                    }
                ]
            }
        }
    }
    # send request
    response = requests.post(OPENS_URL, auth=OPENS_AUTH, headers=headers,
                            data=json.dumps(query_body), verify=False)
    # extract hits
    if response.status_code != 200:
        logger.info("Error in response:", response.status_code, response.text)
        return None
    else:
        logger.info("Response received successfully.")
        hits = response.json()["hits"]["hits"]
    results = [
        {
            "id": hit["_id"],
            "score": hit["_score"],
            "text": hit["_source"]["text"]
        }
        for hit in hits
    ]
    logger.info(f"Found {len(results)} results.")
    logger.info("Results:", results)
    return {"results": results}

# print(find_matching_rec("Try to go for a walk in the morning. It will help you to be more productive during the day."))
