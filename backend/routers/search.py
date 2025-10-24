# backend/routers/search.py
from __future__ import annotations

import os
import time
import inspect
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, root_validator

from elasticsearch import AuthenticationException, AuthorizationException, ApiError
from services.elastic_client import get_es, search_knn, search_bm25
from services.rank_fusion import rrf_fuse
from utils.metrics import record

router = APIRouter()
ES_INDEX = os.getenv("ELASTIC_INDEX", os.getenv("ES_INDEX", "searchsphere_docs"))
DEMO_FALLBACK = (os.getenv("DEMO_RESULTS") or "1") not in ("0", "false", "False")

# NEW: env-tunable candidate pool for kNN (try 80–160 depending on index size)
KNN_NUM_CANDIDATES = int(os.getenv("ES_KNN_NUM_CANDIDATES", "120"))

# ------------------------------- Models --------------------------------
class SearchBody(BaseModel):
    q: Optional[str] = None
    query: Optional[str] = None
    k: int = 10
    mode: str = "hybrid"  # "bm25" | "knn" | "hybrid"
    filters: Optional[Dict[str, Any]] = None
    query_vector: Optional[List[float]] = None

    @root_validator(pre=True)
    def unify_query(cls, values):
        # Soft default prevents dev hot-reload 422s
        text = (values.get("query") or values.get("q") or "").strip()
        values["query"] = text if text else "*"
        return values


# ------------------------------ Helpers --------------------------------
def _call_with_supported(func, **candidates):
    """Call func with only the kwargs it accepts (elastic helpers differ slightly)."""
    params = set(inspect.signature(func).parameters.keys())
    kwargs = {k: v for k, v in candidates.items() if k in params}
    return func(**kwargs)


def _as_list(x: Any) -> List[Dict[str, Any]]:
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        for key in ("results", "hits", "docs"):
            v = x.get(key)
            if isinstance(v, list):
                return v
    return [x] if x is not None else []


def _safe_str(x: Any) -> str:
    return x if isinstance(x, str) else ""


def _normalize_hit(hit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize output for the frontend cards. Avoids 'Untitled' / 'No snippet'.
    """
    src = hit.get("source") or hit.get("_source") or {}
    if not isinstance(src, dict):
        src = {}

    title = _safe_str(
        src.get("title")
        or src.get("page_title")
        or src.get("doc_id")
        or src.get("url")
        or "Untitled"
    )
    url = _safe_str(src.get("url"))
    text = _safe_str(src.get("text") or src.get("content") or "")

    # Prefer highlight when present
    snippet = ""
    hl = hit.get("highlight")
    if isinstance(hl, dict):
        for key in ("text", "content", "body", "raw"):
            vals = hl.get(key)
            if isinstance(vals, list) and vals:
                snippet = _safe_str(vals[0])
                break

    # Better fallback: finish at a sentence boundary
    if not snippet and text:
        s = text[:360]
        p = max(s.rfind("."), s.rfind("!"), s.rfind("?"))
        snippet = s[: p + 1] if p > 60 else s[:240]

    # Derive title from URL if still untitled
    if (not title or title == "Untitled") and url:
        try:
            from urllib.parse import urlparse
            u = urlparse(url)
            derived = (u.netloc or "") + (u.path or "")
            title = derived or "Untitled"
        except Exception:
            pass

    return {
        "id": hit.get("id") or hit.get("_id"),
        "score": hit.get("score") or hit.get("_score"),
        "index": hit.get("index"),
        "title": (title or "Untitled").strip(),
        "url": url or None,
        "snippet": (snippet or "").strip(),
        "team": src.get("team"),
        "doc_type": src.get("doc_type"),
    }


def _safe_search(func, label: str, **kwargs) -> List[Dict[str, Any]]:
    try:
        res = _call_with_supported(func, **kwargs)
        return _as_list(res)
    except (AuthenticationException, AuthorizationException):
        raise HTTPException(status_code=502, detail=f"Elasticsearch authentication failed during {label}")
    except ApiError as e:
        raise HTTPException(status_code=502, detail=f"Elasticsearch API error during {label}: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{label} search failed: {e}")


def _demo_results() -> List[Dict[str, Any]]:
    """Shown only if ES returns zero hits, to keep the UI demonstrable."""
    demo = [
        {
            "_id": "demo1",
            "_source": {
                "title": "FinOps Optimization Overview",
                "url": "https://example.com/finops",
                "text": "A quick overview of hybrid search and cost optimization patterns with Elastic and Vertex AI.",
                "team": "finops",
                "doc_type": "guide",
            },
        },
        {
            "_id": "demo2",
            "_source": {
                "title": "Elastic + Vertex AI Hybrid RAG",
                "url": "https://example.com/rag",
                "text": "How BM25 and kNN embeddings fuse via Reciprocal Rank Fusion to improve recall and precision.",
                "team": "research",
                "doc_type": "pdf",
            },
        },
    ]
    return [_normalize_hit(h) for h in demo]


# ------------------------------ Endpoint --------------------------------
@router.post("/search")
def search(body: SearchBody = Body(...)) -> Dict[str, Any]:
    """
    Unified search endpoint for BM25, kNN, and hybrid.
    Returns normalized hits safe for the UI + __latency_ms for the front-end badge.
    """
    t0 = time.perf_counter()

    try:
        es = get_es()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Elasticsearch not ready: {e}")

    k = max(1, min(50, body.k))
    pool = max(60, k)   # give fusion headroom
    common = dict(
        es=es,
        index=ES_INDEX,
        query=body.query,
        query_text=body.query,
        k=pool,
        size=pool,
        filters=body.filters,
    )

    mode = (body.mode or "hybrid").lower()

    # BM25
    if mode == "bm25":
        bm_hits = _safe_search(search_bm25, "BM25", **common)
        norm = [_normalize_hit(h) for h in bm_hits[:k]]
        elapsed = (time.perf_counter() - t0) * 1000.0
        record("search", elapsed)
        if not norm and DEMO_FALLBACK:
            return {"results": _demo_results(), "mode": "demo", "__latency_ms": elapsed}
        return {"results": norm, "mode": "bm25", "__latency_ms": elapsed}

    # kNN
    if mode == "knn":
        if not body.query_vector:
            elapsed = (time.perf_counter() - t0) * 1000.0
            record("search", elapsed)
            return {"results": [], "mode": "knn", "warning": "query_vector missing", "__latency_ms": elapsed}
        # NEW: pass num_candidates (env-tunable)
        knn_hits = _safe_search(
            search_knn,
            "kNN",
            **{**common, "query_vector": body.query_vector, "num_candidates": KNN_NUM_CANDIDATES}
        )
        norm = [_normalize_hit(h) for h in knn_hits[:k]]
        elapsed = (time.perf_counter() - t0) * 1000.0
        record("search", elapsed)
        if not norm and DEMO_FALLBACK:
            return {"results": _demo_results(), "mode": "demo", "__latency_ms": elapsed}
        return {"results": norm, "mode": "knn", "__latency_ms": elapsed}

    # hybrid
    bm_hits = _safe_search(search_bm25, "BM25", **common)
    knn_hits: List[Dict[str, Any]] = []
    if body.query_vector:
        try:
            # NEW: pass num_candidates (env-tunable)
            knn_hits = _safe_search(
                search_knn,
                "kNN",
                **{**common, "query_vector": body.query_vector, "num_candidates": KNN_NUM_CANDIDATES}
            )
        except HTTPException:
            knn_hits = []

    fused = rrf_fuse(knn_hits, bm_hits, top_k=k) if knn_hits else bm_hits[:k]
    norm = [_normalize_hit(h) for h in fused]
    elapsed = (time.perf_counter() - t0) * 1000.0
    record("search", elapsed)

    if not norm and DEMO_FALLBACK:
        return {"results": _demo_results(), "mode": "demo", "__latency_ms": elapsed}

    return {"results": norm, "mode": "hybrid", "__latency_ms": elapsed}
