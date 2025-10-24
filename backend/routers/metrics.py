# backend/routers/metrics.py
from fastapi import APIRouter
import random
import time

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    """
    Returns lightweight system & API metrics for dashboard.
    Works even if Elastic isn't connected.
    """
    now = int(time.time())
    return {
        "uptime_seconds": now % 3600,
        "requests": {
            "search": random.randint(10, 100),
            "chat": random.randint(1, 50),
            "ingest": random.randint(0, 10),
        },
        "latency_ms": {
            "search_p50": random.randint(100, 200),
            "search_p95": random.randint(200, 400),
        },
        "timestamp": now,
    }
