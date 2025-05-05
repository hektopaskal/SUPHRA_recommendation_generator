from hybrid_search.search import find_matching_rec
from fastapi import APIRouter, HTTPException
from api.schemas import RecommendationSchema, RecommendationRequest, RecommendationResponse
import base64
import io

from hybrid_search.index import index_current_database

router = APIRouter()

@router.get("/")
def root():
    return {"message": "SUPHRA Recommendation API is running."}

@router.post("/match")
def match(request: str):
    response = find_matching_rec(request)
    return response


    
    
@router.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    try:
        if request.file_base64 == "DEBUG_MODE" :
            fake_recommendations = [
                RecommendationSchema(
                    id=1,
                    short_desc="Recommendation 1 based on your paper.",
                    long_desc="Detailed description 1.",
                ),
                RecommendationSchema(
                    id=2,
                    short_desc="Recommendation 2 based on your paper.",
                    long_desc="Detailed description 2.",
                ),
            ]
            return RecommendationResponse(recommendations=fake_recommendations)
        else:
            # Decode the base64 PDF
            #pdf_bytes = base64.b64decode(request.file_base64)
            #pdf_file = io.BytesIO(pdf_bytes)
            return RecommendationResponse(recommendations=[])

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
