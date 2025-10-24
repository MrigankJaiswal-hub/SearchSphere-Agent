# Pydantic models for validation
# backend/utils/schema_models.py
from typing import List, Optional
from pydantic import BaseModel

class SearchHit(BaseModel):
    title: str
    url: Optional[str]
    snippet: Optional[str]
    score: Optional[float]
