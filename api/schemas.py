from pydantic import BaseModel
from typing import List, Optional

class RecommendationRequest(BaseModel):
    file_base64: str

class RecommendationSchema(BaseModel):
    id: Optional[int]
    short_desc: Optional[str]
    long_desc: Optional[str]
    
    goal: Optional[str]  # ENUM
    activity_type: Optional[str]  # ENUM
    
    categories: Optional[List[str]]  # SET becomes a list of strings
    concerns: Optional[List[str]]  # SET becomes a list of strings
    
    daytime: Optional[str]  # ENUM
    weekdays: Optional[str]  # ENUM
    season: Optional[str]  # ENUM
    
    is_outdoor: Optional[bool]
    is_basic: Optional[bool]
    is_advanced: Optional[bool]
    
    gender: Optional[str]
    src_title: Optional[str]
    src_reference: Optional[str]
    src_pub_year: Optional[int]  # YEAR -> int
    src_pub_type: Optional[str]
    src_field_of_study: Optional[str]
    src_doi: Optional[str]
    src_hyperlink: Optional[str]
    src_pub_venue: Optional[str]
    src_citations: Optional[int]
    src_cit_influential: Optional[int]

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationSchema]
