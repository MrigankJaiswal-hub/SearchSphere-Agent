# backend/routers/eval.py
from __future__ import annotations

import os
from typing import List, Optional, Tuple, Dict, Any
from collections.abc import Iterable

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from services.vertex_embeddings import embed_texts
from services.elastic_client import get_es, search_knn, search_bm25
from services.rank_fusion import rrf_fuse
from utils.eval import batch_precision
from utils.metrics import set_eval_precision

# ---------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------
INDEX = os.getenv("ELASTIC_INDEX", "searchsphere_docs")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
EMBED_MODEL = os.getenv("VERTEX_EMBED_MODEL", "text-embedding-005")

router = APIRouter()

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------
class Filters(BaseModel):
    team: Optional[List[str]] = None
    doc_type: Optional[List[str]] = None
    since: Optional[str] = None


class EvalItem(BaseModel):
    query: str
    relevant_ids: List[str]


class EvalRequest(BaseModel):
    k: int = 10
    items: List[EvalItem]
    filters: Optional[Filters] = None


# ---------------------------------------------------------------------
# Endpoint: /api/eval/precision
# ---------------------------------------------------------------------
@router.post("/eval/precision")
def eval_precision(req: EvalRequest = Body(...)) -> Dict[str, Any]:
    """
    Compute Precision@k across multiple (query, relevant_ids) pairs using
    hybrid retrieval (BM25 + kNN fused via Reciprocal Rank Fusion).
    """
    # 1️⃣ Ensure Elasticsearch is ready
    try:
        es = get_es()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Elasticsearch not ready: {e}")

    k = max(1, min(50, req.k))
    per_item: List[Tuple[List[Dict[str, Any]], Iterable[str]]] = []
    errors: List[str] = []

    # 2️⃣ Loop through each evaluation item
    for it in req.items:
        qvec = None

        # Step 1 — Embed query text
        try:
            qvec = embed_texts([it.query], location=LOCATION, model=EMBED_MODEL)[0]
        except Exception as e:
            errors.append(f"Embedding failed for '{it.query[:30]}…': {e}")

        # Step 2 — BM25 search
        try:
            bm25_hits = search_bm25(
                es=es, index=INDEX, query_text=it.query, k=max(60, k), filters=req.filters
            )
        except Exception as e:
            bm25_hits = []
            errors.append(f"BM25 search failed for '{it.query[:30]}…': {e}")

        # Step 3 — kNN search (if embeddings available)
        knn_hits: List[Dict[str, Any]] = []
        if qvec is not None:
            try:
                knn_hits = search_knn(
                    es=es,
                    index=INDEX,
                    query_vector=qvec,
                    k=max(60, k),
                    filters=req.filters,
                )
            except Exception as e:
                knn_hits = []
                errors.append(f"kNN search failed for '{it.query[:30]}…': {e}")

        # Step 4 — Fuse results (fallback to BM25 if fusion fails)
        try:
            fused = rrf_fuse(knn_hits, bm25_hits, top_k=max(60, k))
        except Exception:
            fused = bm25_hits[: max(60, k)]

        # Append pair (fused results, relevant_ids)
        per_item.append((fused, list(it.relevant_ids)))

    # 3️⃣ Evaluate precision@k
    try:
        agg = batch_precision(per_item, k=k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")

    # 4️⃣ Update metrics for dashboard
    try:
        set_eval_precision(k, agg.get("p_at_k", 0.0))
    except Exception:
        pass

    # 5️⃣ Construct response
    response: Dict[str, Any] = {
        "k": k,
        "p_at_k": agg.get("p_at_k", 0.0),
        "queries": agg.get("queries", []),
    }
    if errors:
        response["warnings"] = errors

    return response
