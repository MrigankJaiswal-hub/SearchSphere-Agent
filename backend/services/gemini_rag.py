# Gemini 1.5 RAG generator with model-id normalization and smart fallbacks.
# backend/services/gemini_rag.py
"""
Vertex-only Gemini RAG helper.

- Uses Application Default Credentials (service account) via GOOGLE_APPLICATION_CREDENTIALS
- Requires: GCP_PROJECT_ID, VERTEX_LOCATION, VERTEX_CHAT_MODEL (optional; defaults provided)
- Returns: (answer_text, citations_list)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.api_core.exceptions import GoogleAPICallError, NotFound, PermissionDenied


# ---------------------------------------------------------------------------
# System instruction used in the prompt
# ---------------------------------------------------------------------------
SYSTEM = (
    "You are an enterprise search assistant. You MUST use only the provided context. "
    "If the answer is not in the context, say you don't know. "
    "Cite sources inline as [#] where # matches the provided citations list."
)


# ---------------------------------------------------------------------------
# Model ID normalization
# ---------------------------------------------------------------------------
def _normalize_model_id(model: str | None) -> str:
    """
    Map legacy or alias IDs to currently-available Vertex public model IDs.

    You can extend/update this mapping as Google rotates versions.
    """
    if not model or not model.strip():
        return "gemini-2.0-flash-001"

    m = model.strip()
    canonical = {
        # Old -> current public
        "gemini-1.5-pro": "gemini-2.0-flash-001",
        "gemini-1.5-flash": "gemini-2.0-flash-001",
        "gemini-1.5-pro-002": "gemini-2.0-flash-001",
        "gemini-1.5-flash-002": "gemini-2.0-flash-001",
        "gemini-1.5-flash-8b": "gemini-2.0-flash-001",
        "gemini-pro": "gemini-2.0-flash-001",
        "gemini-pro-vision": "gemini-2.0-flash-001",
        "gemini-1.5-pro-latest": "gemini-2.0-flash-001",
        "gemini-1.5-flash-latest": "gemini-2.0-flash-001",
        # Current recommendation
        "gemini-2.0-flash": "gemini-2.0-flash-001",
        "gemini-2.0-flash-001": "gemini-2.0-flash-001",
    }
    return canonical.get(m, m)


# ---------------------------------------------------------------------------
# Vertex init helper
# ---------------------------------------------------------------------------
def _ensure_vertex() -> Tuple[str, str]:
    """
    Initialize Vertex AI with project & location from environment.
    """
    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("VERTEX_LOCATION", "us-central1")

    if not project:
        raise RuntimeError("GCP_PROJECT_ID not set")
    if not location:
        location = "us-central1"

    # Initialize Vertex SDK
    vertexai.init(project=project, location=location)
    return project, location


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def _build_prompt(query: str, contexts: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Build a single text prompt and a citations list the UI can render.

    Each item in `contexts` is expected to contain:
      - title (str)
      - url (optional str)
      - text (str)  -> the content chunk
      - snippet (optional str)
    """
    lines: List[str] = []
    citations: List[Dict[str, Any]] = []

    for i, c in enumerate(contexts, start=1):
        title = c.get("title") or "Document"
        url = c.get("url")
        text = c.get("text") or ""
        snippet = c.get("snippet") or ""

        citations.append(
            {
                "id": i,
                "title": title,
                "url": url,
                "snippet": snippet,
            }
        )
        lines.append(f"[{i}] {title} {url or ''}\n{text}\n")

    prompt = (
        f"{SYSTEM}\n\n"
        f"Query: {query}\n\n"
        f"Context:\n{''.join(lines)}\n"
        f"Answer the query succinctly. Include citations like [1], [2] where relevant."
    )
    return prompt, citations


# ---------------------------------------------------------------------------
# Output text extraction (SDKs sometimes vary)
# ---------------------------------------------------------------------------
def _extract_text(gen_response: Any) -> str:
    """
    Try to extract text from a Vertex response robustly.
    """
    # Most common:
    t = getattr(gen_response, "text", None)
    if isinstance(t, str) and t.strip():
        return t

    # Fallback: try candidates -> content -> parts
    try:
        return gen_response.candidates[0].content.parts[0].text  # type: ignore[attr-defined]
    except Exception:
        pass

    # Last resort: string cast
    return (str(gen_response) or "").strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def answer_with_citations(
    query: str,
    contexts: List[Dict[str, Any]],
    model: Optional[str] = None,
    *,
    temperature: float = 0.2,
    max_output_tokens: int = 2048,
    top_p: float = 0.95,
    top_k: int = 40,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate an answer grounded in `contexts` using a Vertex Gemini model.

    Returns: (answer_text, citations_list)
    Raises: PermissionDenied, NotFound, GoogleAPICallError, RuntimeError (bad config)
    """
    _ensure_vertex()
    model_id = _normalize_model_id(model or os.getenv("VERTEX_CHAT_MODEL"))

    prompt, citations = _build_prompt(query, contexts)

    try:
        gen = GenerativeModel(model_id)
        cfg = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            top_k=top_k,
        )
        response = gen.generate_content(prompt, generation_config=cfg)
        text = _extract_text(response)
        if not text:
            raise GoogleAPICallError("Empty response from model")
        # Optional: print a one-liner for observability
        print(f"[gemini_rag] Vertex success model={model_id}")
        return text, citations

    except NotFound as nf:
        # Model not available in region / project
        print(f"[gemini_rag] Vertex not found model={model_id}: {nf}")
        raise
    except PermissionDenied as pd:
        # Billing/permissions issue; bubble up to the router for a friendly message
        print(f"[gemini_rag] Vertex permission denied model={model_id}: {pd}")
        raise
    except GoogleAPICallError as ge:
        print(f"[gemini_rag] Vertex API error model={model_id}: {ge}")
        raise
    except Exception as e:
        print(f"[gemini_rag] Vertex unexpected error model={model_id}: {e}")
        raise
