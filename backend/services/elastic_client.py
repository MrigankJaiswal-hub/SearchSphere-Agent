# backend/services/elastic_client.py
# Init, bulk ops, and search helpers (BM25 + kNN) for Elasticsearch.
# backend/services/elastic_client.py
# Init, bulk ops, and search helpers (BM25 + kNN) for Elasticsearch.

import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, cast

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import AuthenticationException  # type: ignore[attr-defined]

# ---------------------------------------------------------------------
# Defaults / Env toggles
# ---------------------------------------------------------------------
TEXT_FIELD = os.getenv("ELASTIC_TEXT_FIELD", "text")
# IMPORTANT: your ingest uses 'vector'; make this the default
VECTOR_FIELD = os.getenv("ELASTIC_VECTOR_FIELD", "vector")

ES_DEBUG = (os.getenv("ES_DEBUG") or "0").lower() not in ("0", "false", "no")
ENABLE_HIGHLIGHT = (os.getenv("ES_ENABLE_HIGHLIGHT") or "0").lower() not in ("0", "false", "no")

# Comma-separated list of fields to fetch from ES; reduces payload & latency
_source_env = os.getenv(
    "ES_SOURCE_FIELDS",
    "title,url,text,team,doc_type,page_num"
)
SOURCE_FIELDS: List[str] = [s.strip() for s in _source_env.split(",") if s.strip()]

# Global default for kNN candidate pool (can be overridden per-call)
KNN_NUM_CANDIDATES = int(os.getenv("ES_KNN_NUM_CANDIDATES", "120"))

# ---------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------
def get_es() -> Elasticsearch:
    """
    Build an ES client from environment variables and verify the connection.

    Priority (first match wins):
      1) Direct endpoint/host
      2) Elastic Cloud ID + API key
      3) Self-managed URL + basic auth
    """
    endpoint: Optional[str] = os.getenv("ELASTIC_ENDPOINT") or os.getenv("ELASTIC_HOST")
    api_key_b64: Optional[str] = os.getenv("ELASTIC_API_KEY")
    username: Optional[str] = os.getenv("ELASTIC_USERNAME")
    password: Optional[str] = os.getenv("ELASTIC_PASSWORD")

    cloud_id: Optional[str] = os.getenv("ELASTIC_CLOUD_ID")
    api_key_id: Optional[str] = os.getenv("ELASTIC_API_KEY_ID")
    api_key_secret: Optional[str] = (
        os.getenv("ELASTIC_API_KEY_SECRET")
        or os.getenv("ELASTIC_API_KEY_VALUE")
        or os.getenv("ELASTIC_API_KEY_PLAIN")
    )

    es_url: Optional[str] = os.getenv("ELASTIC_URL")

    def _mask(s: Optional[str]) -> str:
        if not s:
            return "<none>"
        s = s.strip()
        if len(s) <= 10:
            return "***"
        return s[:6] + "..." + s[-4:]

    if ES_DEBUG:
        print("[es] endpoint:", endpoint or "<none>")
        print("[es] cloud_id present:", bool(cloud_id))
        print("[es] api_key_b64:", _mask(api_key_b64))
        print("[es] api_key_id:", _mask(api_key_id))
        print("[es] api_key_secret:", _mask(api_key_secret))
        print("[es] url:", es_url or "<none>")
        print("[es] user present:", bool(username), "pass present:", bool(password))

    if endpoint:
        if api_key_b64:
            es = Elasticsearch(endpoint, api_key=api_key_b64)
        elif username and password:
            es = Elasticsearch(endpoint, basic_auth=(username, password), verify_certs=True)
        else:
            raise RuntimeError(
                "Endpoint is set but missing credentials. Provide ELASTIC_API_KEY "
                "or ELASTIC_USERNAME/ELASTIC_PASSWORD."
            )

    elif cloud_id and (api_key_b64 or (api_key_id and api_key_secret)):
        if api_key_b64:
            es = Elasticsearch(cloud_id=cloud_id, api_key=api_key_b64)
        else:
            api_key_pair: Tuple[str, str] = (cast(str, api_key_id), cast(str, api_key_secret))
            es = Elasticsearch(cloud_id=cloud_id, api_key=api_key_pair)

    elif es_url and username and password:
        es = Elasticsearch(es_url, basic_auth=(username, password), verify_certs=True)

    else:
        raise RuntimeError(
            "Elasticsearch credentials not set. Provide one of:\n"
            "1) ELASTIC_ENDPOINT/ELASTIC_HOST + (ELASTIC_API_KEY | ELASTIC_USERNAME+ELASTIC_PASSWORD)\n"
            "2) ELASTIC_CLOUD_ID + (ELASTIC_API_KEY | ELASTIC_API_KEY_ID+ELASTIC_API_KEY_SECRET)\n"
            "3) ELASTIC_URL + ELASTIC_USERNAME + ELASTIC_PASSWORD"
        )

    try:
        es.info()
    except AuthenticationException:
        raise RuntimeError("Elasticsearch auth/connection failed: security_exception")
    except Exception as e:
        raise RuntimeError(f"Elasticsearch auth/connection failed: {type(e).__name__}: {e}")

    return es


# ---------------------------------------------------------------------
# Filters helper
# ---------------------------------------------------------------------
def _filters_to_es(filters: Optional[Union[Dict[str, Any], Any]]) -> List[Dict[str, Any]]:
    """
    Convert Filters model (or plain dict/obj) into ES filter clauses.
    Supports:
      - team:     list[str]  -> terms filter on 'team'
      - doc_type: list[str]  -> terms filter on 'doc_type'
      - since:    ISO date   -> range filter on 'created_at'
    """
    if not filters:
        return []

    if hasattr(filters, "model_dump"):
        raw: Dict[str, Any] = cast(Any, filters).model_dump()
    elif isinstance(filters, dict):
        raw = filters
    else:
        raw = {
            "team": getattr(filters, "team", None),
            "doc_type": getattr(filters, "doc_type", None),
            "since": getattr(filters, "since", None),
        }

    clauses: List[Dict[str, Any]] = []

    teams = raw.get("team")
    if teams:
        clauses.append({"terms": {"team": teams}})

    doctypes = raw.get("doc_type")
    if doctypes:
        clauses.append({"terms": {"doc_type": doctypes}})

    since = raw.get("since")
    if since:
        try:
            s = str(since)
            _ = datetime.fromisoformat(s.replace("Z", "+00:00"))
            clauses.append({"range": {"created_at": {"gte": s}}})
        except Exception:
            pass

    return clauses


def _format_hits(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize ES hits to a compact shape and preserve ES-style keys for the UI."""
    out: List[Dict[str, Any]] = []
    for h in hits:
        src = h.get("_source", {}) or {}
        item: Dict[str, Any] = {
            "id": h.get("_id"),
            "score": h.get("_score"),
            "index": h.get("_index"),
            "source": src,     # friendly key
            "_source": src,    # ES-style key many UIs expect
        }
        if "highlight" in h:
            item["highlight"] = h["highlight"]
        out.append(item)
    return out


# ---------------------------------------------------------------------
# Write / Ingest
# ---------------------------------------------------------------------
def index_docs(docs: List[Dict[str, Any]], index: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
    """Bulk-index docs. Returns (success_count, error_items)."""
    es = get_es()

    actions: List[Dict[str, Any]] = []
    for d in docs:
        _index = index or d.get("_index") or os.getenv("ELASTIC_INDEX", "searchsphere_docs")
        _id = d.get("_id")
        body = {k: v for k, v in d.items() if k not in {"_index", "_id"}}
        action: Dict[str, Any] = {"_op_type": "index", "_index": _index, "_source": body}
        if _id is not None:
            action["_id"] = _id
        actions.append(action)

    result = bulk(es, actions, refresh="wait_for")

    success_count: int = int(result[0])
    items_raw = result[1] if len(result) > 1 else []
    items: List[Dict[str, Any]] = items_raw if isinstance(items_raw, list) else []

    error_items: List[Dict[str, Any]] = []
    if isinstance(items, Iterable):
        for it in items:
            try:
                idx = it.get("index") or it.get("create") or it.get("update") or it.get("delete")
                if isinstance(idx, dict) and idx.get("error"):
                    error_items.append(it)
            except Exception:
                pass

    return success_count, error_items


# ---------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------
def search_knn(
    es: Elasticsearch,
    index: str,
    query_vector: List[float],
    k: int = 12,
    filters: Optional[Union[Dict[str, Any], Any]] = None,
    vector_field: str = VECTOR_FIELD,
    num_candidates: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """kNN search against dense vector field."""
    must_filters = _filters_to_es(filters)

    nc = num_candidates if (isinstance(num_candidates, int) and num_candidates >= k) else KNN_NUM_CANDIDATES

    knn_obj: Dict[str, Any] = {
        "field": vector_field,
        "query_vector": query_vector,
        "k": k,
        "num_candidates": nc,
    }

    body: Dict[str, Any] = {
        "knn": knn_obj,
        "_source": SOURCE_FIELDS or True,
        "size": k,
    }

    if must_filters:
        # Some clusters accept top-level 'filter' with 'knn'; if not, we fallback below
        body["filter"] = must_filters  # type: ignore[assignment]

    try:
        res = es.search(index=index, body=body)
    except Exception:
        # Wrap in a bool query to ensure filters apply across versions
        fallback_body: Dict[str, Any] = {
            "query": {"bool": {"filter": must_filters}} if must_filters else {"match_all": {}},
            "knn": body["knn"],
            "_source": SOURCE_FIELDS or True,
            "size": k,
        }
        res = es.search(index=index, body=fallback_body)

    hits = res.get("hits", {}).get("hits", []) or []
    return _format_hits(hits)


def search_bm25(
    es: Elasticsearch,
    index: str,
    query_text: str,
    k: int = 12,
    filters: Optional[Union[Dict[str, Any], Any]] = None,
    text_field: str = TEXT_FIELD,
) -> List[Dict[str, Any]]:
    """
    Progressive BM25 text search with match_all fallback when query is '*' or empty.
    Uses SOURCE_FIELDS filtering and disables highlight by default for latency.
    """
    filter_clauses = _filters_to_es(filters)

    def _run(body: Dict[str, Any]) -> List[Dict[str, Any]]:
        res = es.search(index=index, body=body)
        return res.get("hits", {}).get("hits", []) or []

    base_bool: Dict[str, Any] = {"must": [], "filter": []}
    if filter_clauses:
        base_bool["filter"] = filter_clauses

    qt = (query_text or "").strip()
    if qt in ("", "*"):
        body0: Dict[str, Any] = {
            "query": {"bool": {**base_bool, "must": [{"match_all": {}}]}},
            "_source": SOURCE_FIELDS or True,
            "size": k,
        }
        hits = _run(body0)
        return _format_hits(hits)

    # 1) Primary match
    body1: Dict[str, Any] = {
        "query": {"bool": {**base_bool, "must": [{"match": {text_field: {"query": qt}}}]}},
        "_source": SOURCE_FIELDS or True,
        "size": k,
    }
    if ENABLE_HIGHLIGHT:
        body1["highlight"] = {"fields": {text_field: {"number_of_fragments": 1}}}
    hits = _run(body1)
    if hits:
        return _format_hits(hits)

    # 2) Multi-match over common fields
    mm_fields = [text_field, "title^2", "content", "body", "meta.*"]
    body2: Dict[str, Any] = {
        "query": {"bool": {**base_bool, "must": [{"multi_match": {"query": qt, "fields": mm_fields}}]}},
        "_source": SOURCE_FIELDS or True,
        "size": k,
    }
    if ENABLE_HIGHLIGHT:
        body2["highlight"] = {"fields": {f: {"number_of_fragments": 1} for f in mm_fields}}
    hits = _run(body2)
    if hits:
        return _format_hits(hits)

    # 3) Query string over all fields
    body3: Dict[str, Any] = {
        "query": {"bool": {**base_bool, "must": [{"query_string": {"query": qt, "default_field": "*"}}]}},
        "_source": SOURCE_FIELDS or True,
        "size": k,
    }
    hits = _run(body3)
    if hits:
        return _format_hits(hits)

    # 4) Last-resort: match_all
    body4: Dict[str, Any] = {
        "query": {"bool": {**base_bool, "must": [{"match_all": {}}]}},
        "_source": SOURCE_FIELDS or True,
        "size": k,
    }
    hits = _run(body4)
    return _format_hits(hits)
