# entrypoint (FastAPI init + routers)
# backend/app.py
# entrypoint (FastAPI init + routers)
# backend/app.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers.ingest import router as ingest_router
from routers.search import router as search_router
from routers.chat import router as chat_router
from routers.analytics import router as analytics_router
from routers.eval import router as eval_router
from routers.label_assist import router as label_assist_router
from routers.health_routes import router as health_router

# metrics router is optional in your tree; import defensively
try:
    from routers.metrics import router as metrics_router  # type: ignore
except Exception:
    from fastapi import APIRouter
    metrics_router = APIRouter()

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "searchsphere-backend")

app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    description="Elastic + Vertex AI hybrid RAG backend",
)

# CORS (relaxed for local dev)
default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
env_origins = os.getenv("CORS_ALLOW_ORIGINS")
allow_origins = env_origins.split(",") if env_origins else default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ingest_router, prefix="/api", tags=["ingest"])
app.include_router(search_router, prefix="/api", tags=["search"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(analytics_router, prefix="/api", tags=["analytics"])
app.include_router(eval_router, prefix="/api", tags=["evaluation"])
app.include_router(label_assist_router, prefix="/api", tags=["evaluation"])
app.include_router(metrics_router, prefix="/api", tags=["metrics"])
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(health_router)

# @app.get("/healthz")
# def health():
#     return {"status": "ok"}
