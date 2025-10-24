# /api/chat    (RAG + Gemini)
# /api/chat    (RAG + Gemini with graceful fallback)
# /api/chat    (RAG + Gemini with graceful fallback)
# backend/routers/chat.py
from __future__ import annotations

import os
import time
import traceback
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from utils.metrics import record
from services.vertex_embeddings import embed_texts
from services.elastic_client import get_es, search_knn, search_bm25
from services.rank_fusion import rrf_fuse
import services.gemini_rag as gemini_rag  # keep as module import

INDEX = os.getenv("ELASTIC_INDEX", "searchsphere_docs")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
EMBED_MODEL = os.getenv("VERTEX_EMBED_MODEL", "text-embedding-005")
# Works in your project; gemini_rag has its own internal fallbacks too.
CHAT_MODEL = os.getenv("VERTEX_CHAT_MODEL", "gemini-2.0-flash-001")

router = APIRouter()


class Filters(BaseModel):
    team: Optional[List[str]] = None
    doc_type: Optional[List[str]] = None
    since: Optional[str] = None


class ChatRequest(BaseModel):
    query: str
    k: Optional[int] = 8
    filters: Optional[Filters] = None


def _safe_str(x: Any) -> str:
    return x if isinstance(x, str) else ""


def _normalize_hit_source(hit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an ES hit (from services.elastic_client._format_hits) so the UI/LLM
    always has sane fields: title/url/snippet/text.
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

    # Prefer ES highlights when present
    snippet = ""
    hl = hit.get("highlight")
    if isinstance(hl, dict):
        for key in ("text", "content", "body", "raw"):
            if isinstance(hl.get(key), list) and hl[key]:
                snippet = _safe_str(hl[key][0])
                break
    if not snippet:
        snippet = text[:240]

    return {
        "title": title,
        "url": url,
        "text": text[:4000],  # keep context bounded for the LLM
        "snippet": snippet,
    }


def _exists(path: Optional[str]) -> bool:
    try:
        return bool(path and os.path.exists(path))
    except Exception:
        return False


def _make_citations(contexts: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
    """Always return a citations list, even if URLs are missing."""
    cites: List[Dict[str, Any]] = []
    for c in contexts[:k]:
        cites.append({
            "title": c.get("title") or "Untitled",
            "url": c.get("url") or None,
            "snippet": (c.get("snippet") or c.get("text", "")[:160]).strip(),
        })
    return cites


@router.post("/chat")
def chat(req: ChatRequest = Body(...)) -> Dict[str, Any]:
    """
    Retrieval-augmented chat:
      1) Embed query (Vertex)
      2) Retrieve via BM25 + kNN (Elasticsearch)
      3) Fuse via RRF
      4) Answer with citations (Gemini) with graceful fallback
    """
    t0 = time.perf_counter()
    k = max(1, min(20, req.k or 8))

    # 1) ES client
    try:
        es = get_es()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Elasticsearch not ready: {e}")

    # 2) Embedding
    qvec: Optional[List[float]] = None
    embed_err: Optional[str] = None
    try:
        qvec = embed_texts([req.query], location=LOCATION, model=EMBED_MODEL)[0]
    except Exception as e:
        embed_err = f"Embedding failed: {type(e).__name__}: {e}"

    # 3) Retrieve
    bm25_hits: List[Dict[str, Any]] = []
    bm_err: Optional[str] = None
    try:
        bm25_hits = search_bm25(
            es=es, index=INDEX, query_text=req.query, k=max(60, k), filters=req.filters
        )
    except Exception as e:
        bm_err = f"BM25 failed: {type(e).__name__}: {e}"

    knn_hits: List[Dict[str, Any]] = []
    knn_err: Optional[str] = None
    if qvec is not None:
        try:
            knn_hits = search_knn(
                es=es, index=INDEX, query_vector=qvec, k=max(60, k), filters=req.filters
            )
        except Exception as e:
            knn_err = f"kNN failed: {type(e).__name__}: {e}"
    else:
        knn_err = embed_err or "embedding_unavailable"

    # 4) Fuse (fallback to BM25 if needed)
    try:
        fused = rrf_fuse(knn_hits, bm25_hits, top_k=k)
    except Exception:
        fused = bm25_hits[:k]

    contexts = [_normalize_hit_source(h) for h in fused]

    # 5) LLM
    try:
        answer, model_citations = gemini_rag.answer_with_citations(
            req.query, contexts, model=CHAT_MODEL
        )
        citations = model_citations if model_citations else _make_citations(contexts, k)

        record("chat", (time.perf_counter() - t0) * 1000.0)
        result: Dict[str, Any] = {
            "answer": answer,
            "citations": citations,
            "top_k_used": len(contexts),
        }
        if embed_err or bm_err or knn_err:
            result["debug"] = {
                "embed_err": embed_err,
                "bm25_err": bm_err,
                "knn_err": knn_err,
            }
        return result

    except Exception as e:
        # Graceful fallback
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        tb = traceback.format_exc(limit=2)
        warning = (
            f"LLM failed: {type(e).__name__}: {e} "
            f"(GOOGLE_APPLICATION_CREDENTIALS='{cred_path}', exists={_exists(cred_path)})"
        )
        if embed_err:
            warning = f"{embed_err} | {warning}"

        lines = []
        for i, c in enumerate(contexts[:k], 1):
            piece = c.get("snippet") or c.get("text", "")[:200]
            lines.append(f"{i}. {c.get('title', 'Untitled')}: {piece}")

        fallback_answer = (
            "I couldn’t reach the chat model right now. Here are the most relevant snippets:\n\n"
            + ("\n".join(lines) if lines else "No context available.")
        )

        citations = _make_citations(contexts, k)
        record("chat", (time.perf_counter() - t0) * 1000.0)

        return {
            "answer": fallback_answer,
            "citations": citations,
            "top_k_used": len(contexts),
            "warning": warning,
            "trace": tb,
        }
