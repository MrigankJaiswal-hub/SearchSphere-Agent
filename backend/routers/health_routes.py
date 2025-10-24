# backend/routers/health_routes.py
from __future__ import annotations

import os
from fastapi import APIRouter
from fastapi.responses import Response

from services.elastic_client import get_es  # Elastic only (no bedrock)
import vertexai
from vertexai.generative_models import GenerativeModel

# Optional embeddings warmup if you have the helper
try:
    from services.vertex_embeddings import embed_texts  # type: ignore
    HAVE_EMBED = True
except Exception:
    HAVE_EMBED = False

router = APIRouter()

INDEX = os.getenv("ELASTIC_INDEX", "searchsphere_docs")

# Vertex config
PROJECT = (
    os.getenv("GCP_PROJECT_ID")
    or os.getenv("VERTEX_PROJECT")
    or os.getenv("GOOGLE_CLOUD_PROJECT")
)
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
MODEL = os.getenv("VERTEX_CHAT_MODEL", "gemini-2.0-flash-001")
EMBED_MODEL = os.getenv("VERTEX_EMBED_MODEL", "text-embedding-005")

BUILD_SHA = os.getenv("BUILD_SHA", "dev")


@router.get("/healthz")
def healthz():
    es_ok = False
    index_ok = False
    es_reason = None

    vertex_ok = False
    vertex_reason = None

    # --- Elastic ping ---
    try:
        es = get_es()
        _info = es.info()
        es_ok = True
        try:
            index_ok = bool(es.indices.exists(index=INDEX))
        except Exception as e:
            es_reason = f"indices.exists error: {e}"
    except Exception as e:
        es_reason = f"es_connect_failed: {e}"

    # --- Vertex ping (very light) ---
    try:
        if not PROJECT:
            vertex_reason = "missing GCP project (set GCP_PROJECT_ID / GOOGLE_CLOUD_PROJECT)"
        else:
            vertexai.init(project=PROJECT, location=LOCATION)
            try:
                # A tiny content call to verify the endpoint. Fast & cheap for flash model.
                _ = GenerativeModel(MODEL).generate_content("ping").text
                vertex_ok = True
            except Exception as e:
                vertex_reason = f"generate_failed: {e}"
    except Exception as e:
        vertex_reason = f"vertex_init_failed: {e}"

    ok = es_ok and vertex_ok

    return {
        "ok": ok,
        "build": BUILD_SHA,
        "index": INDEX,
        "elastic": {"ok": es_ok, "index_ok": index_ok, "reason": es_reason},
        "vertex": {
            "ok": vertex_ok,
            "project": PROJECT,
            "location": LOCATION,
            "model": MODEL,
            "reason": vertex_reason,
        },
    }


@router.get("/warmup")
def warmup():
    """
    Preload low-latency paths so the first user doesn't pay cold-start:
      - ES: tiny match_all on INDEX
      - Vertex chat: 1-token 'ping'
      - Vertex embeddings: optional, 1 tiny vector
    """
    results = {
        "ok": True,
        "elastic": {"ok": False, "took": None, "reason": None},
        "vertex_chat": {"ok": False, "reason": None},
        "vertex_embed": {"ok": False, "dims": None, "reason": None},
        "build": BUILD_SHA,
        "index": INDEX,
    }

    # --- ES tiny query ---
    try:
        es = get_es()
        res = es.search(
            index=INDEX,
            body={"query": {"match_all": {}}, "size": 1, "_source": False},
        )
        took = res.get("took")
        results["elastic"]["ok"] = True
        results["elastic"]["took"] = took
    except Exception as e:
        results["ok"] = False
        results["elastic"]["reason"] = str(e)

    # --- Vertex chat ---
    try:
        if not PROJECT:
            raise RuntimeError("missing GCP project (set GCP_PROJECT_ID / GOOGLE_CLOUD_PROJECT)")
        vertexai.init(project=PROJECT, location=LOCATION)
        _ = GenerativeModel(MODEL).generate_content("ping").text
        results["vertex_chat"]["ok"] = True
    except Exception as e:
        results["ok"] = False
        results["vertex_chat"]["reason"] = str(e)

    # --- Vertex embed (optional) ---
    if HAVE_EMBED:
        try:
            vec = embed_texts(["warmup"], location=LOCATION, model=EMBED_MODEL)[0]
            results["vertex_embed"]["ok"] = True
            results["vertex_embed"]["dims"] = len(vec) if hasattr(vec, "__len__") else None
        except Exception as e:
            results["ok"] = False
            results["vertex_embed"]["reason"] = str(e)

    return results


@router.get("/favicon.ico")
def favicon_silence():
    # Prevent noisy 404s in API logs; UI serves its own favicon.
    return Response(status_code=204)
