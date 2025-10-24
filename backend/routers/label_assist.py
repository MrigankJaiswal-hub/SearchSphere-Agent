# backend/routers/label_assist.py
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Body
from pydantic import BaseModel

from services.vertex_embeddings import embed_texts
from services.elastic_client import get_es, search_knn, search_bm25
from services.rank_fusion import rrf_fuse

INDEX = os.getenv("ELASTIC_INDEX", "searchsphere_docs")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
EMBED_MODEL = os.getenv("VERTEX_EMBED_MODEL", "text-embedding-005")

router = APIRouter()


# ------------------------ Models ------------------------
class Filters(BaseModel):
    team: Optional[List[str]] = None
    doc_type: Optional[List[str]] = None
    since: Optional[str] = None


class LabelAssistRequest(BaseModel):
    query: str
    k: int = 20
    filters: Optional[Filters] = None


# ------------------------ Helpers ------------------------
def _safe_str(x: Any) -> str:
    return x if isinstance(x, str) else ""


def _sentence_snippet(text: str, max_len: int = 240) -> str:
    """
    Trim a snippet that ends on a sentence boundary (., !, ?)
    but avoid super-short sentences.
    """
    if not text:
        return ""
    s = text[: max_len + 120]  # read a bit more than needed
    p = max(s.rfind("."), s.rfind("!"), s.rfind("?"))
    return (s[: p + 1] if p > 60 else s[:max_len]).strip()


def _derive_title(src: Dict[str, Any]) -> str:
    title = _safe_str(
        src.get("title")
        or src.get("page_title")
        or src.get("doc_id")
        or src.get("url")
        or "Untitled"
    )
    # If still Untitled and URL exists, derive from hostname + path
    if (not title or title == "Untitled") and src.get("url"):
        try:
            from urllib.parse import urlparse
            u = urlparse(src["url"])
            derived = (u.netloc or "") + (u.path or "")
            title = derived or "Untitled"
        except Exception:
            pass
    return title.strip() or "Untitled"


def _derive_chunk_id(h: Dict[str, Any], src: Dict[str, Any]) -> str:
    """
    Prefer explicit chunk_id; fallback to doc_id::chunk::<page_num>;
    else use ES _id.
    """
    cid = _safe_str(src.get("chunk_id"))
    if cid:
        return cid

    doc_id = _safe_str(src.get("doc_id"))
    page_num = src.get("page_num")
    if doc_id and isinstance(page_num, int):
        return f"{doc_id}::chunk::{page_num}"

    # final fallback
    return _safe_str(h.get("_id")) or "unknown::chunk"


# ------------------------ Endpoint ------------------------
@router.post("/eval/label-assist")
def label_assist(req: LabelAssistRequest = Body(...)):
    es = get_es()

    # Embed query once
    qvec = embed_texts([req.query], location=LOCATION, model=EMBED_MODEL)[0]

    # Retrieve a generous pool for fusion headroom
    k = max(1, req.k)
    pool = max(60, k)
    knn_hits = search_knn(
        es,
        INDEX,
        qvec,
        k=pool,
        num_candidates=max(120, pool * 5),
        filters=req.filters,
    )
    bm25_hits = search_bm25(es, INDEX, req.query, k=pool, filters=req.filters)
    fused = rrf_fuse(knn_hits, bm25_hits, top_k=k)

    items: List[Dict[str, Any]] = []
    for h in fused:
        src = h.get("_source") or {}
        if not isinstance(src, dict):
            src = {}

        # Prefer highlight, else sentence-bounded snippet from text/content
        snippet = ""
        hl = h.get("highlight") or {}
        if isinstance(hl, dict):
            for key in ("text", "content", "body", "raw"):
                vals = hl.get(key)
                if isinstance(vals, list) and vals:
                    snippet = _safe_str(vals[0])
                    break
        if not snippet:
            snippet = _sentence_snippet(_safe_str(src.get("text") or src.get("content") or ""))

        title = _derive_title(src)
        chunk_id = _derive_chunk_id(h, src)

        team = _safe_str(src.get("team")) or None
        doc_type = _safe_str(src.get("doc_type")) or None
        page_num = src.get("page_num") if isinstance(src.get("page_num"), int) else None

        # NOTE: we DO NOT stringify missing values; we simply omit them (prevents "None:None")
        item: Dict[str, Any] = {
            "chunk_id": chunk_id,
            "title": title,
            "score": h.get("_score"),
            "snippet": snippet,
        }
        if page_num is not None:
            item["page_num"] = page_num
        if team:
            item["team"] = team
        if doc_type:
            item["doc_type"] = doc_type

        items.append(item)

    return {
        "query": req.query,
        "k": k,
        "candidates": items,
    }
