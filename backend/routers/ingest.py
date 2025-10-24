# /api/ingest  (PDF → chunks → Elastic)
# backend/routers/ingest.py
import io
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Body, HTTPException
from pydantic import BaseModel

from services.elastic_client import get_es, index_docs
from services.vertex_embeddings import embed_texts
from utils.chunker import chunk_text, read_pdf_bytes, read_text_bytes, read_csv_bytes

INDEX = os.getenv("ELASTIC_INDEX", "searchsphere_docs")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
EMBED_MODEL = os.getenv("VERTEX_EMBED_MODEL", "text-embedding-005")

router = APIRouter()

class IngestRequest(BaseModel):
    urls: Optional[List[str]] = None
    text_blobs: Optional[List[str]] = None
    meta: Optional[dict] = None
    doc_type: Optional[str] = "generic"
    team: Optional[str] = "public"

@router.post("/ingest")
async def ingest(
    req: IngestRequest = Body(default=None),
    files: Optional[List[UploadFile]] = File(default=None),
):
    """Ingest PDFs/text/CSV → chunks → embed → Elastic"""
    docs = []
    now = datetime.utcnow().isoformat()

    # 1) Handle uploaded files
    if files:
        for f in files:
            raw = await f.read()
            text = ""
            if f.filename.lower().endswith(".pdf"):
                text = read_pdf_bytes(raw)
            elif f.filename.lower().endswith(".csv"): 
                text = read_csv_bytes(raw)
            else:
                text = read_text_bytes(raw)

            for i, chunk in enumerate(chunk_text(text)):
                docs.append({
                    "doc_id": f.filename,
                    "chunk_id": f"{f.filename}::chunk::{i}",
                    "title": f.filename,
                    "text": chunk,
                    "source": "upload",
                    "url": None,
                    "tags": [],
                    "team": (req.team if req else "public"),
                    "doc_type": (req.doc_type if req else "generic"),
                    "created_at": now,
                    "updated_at": now,
                    "page_num": i
                })

    # 2) Handle raw text blobs (optional)
    if req and req.text_blobs:
        for j, t in enumerate(req.text_blobs):
            for i, chunk in enumerate(chunk_text(t)):
                docs.append({
                    "doc_id": f"blob-{j}",
                    "chunk_id": f"blob-{j}::chunk::{i}",
                    "title": req.meta.get("title") if req and req.meta else f"blob-{j}",
                    "text": chunk,
                    "source": "text",
                    "url": None,
                    "tags": list(req.meta.get("tags", [])) if req and req.meta else [],
                    "team": req.team or "public",
                    "doc_type": req.doc_type or "generic",
                    "created_at": now,
                    "updated_at": now,
                    "page_num": i
                })

    if not docs:
        raise HTTPException(status_code=400, detail="No content to ingest")

    # 3) Embed
    embeddings = embed_texts([d["text"] for d in docs], location=LOCATION, model=EMBED_MODEL)
    for d, vec in zip(docs, embeddings):
        d["text_vector"] = vec

    # 4) Index
    es = get_es()
    index_docs(es, INDEX, docs)

    return {"indexed": len(docs), "index": INDEX}
