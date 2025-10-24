# backend/routers/analytics.py
from fastapi import APIRouter
from utils.metrics import snapshot

router = APIRouter()

@router.get("/metrics")
def metrics():
    return snapshot()
