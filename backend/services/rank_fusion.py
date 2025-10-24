# reciprocal rank fusion, re-scoring
# backend/services/rank_fusion.py
from typing import List, Dict, Any

def _key(hit: Dict[str, Any]) -> str:
    src = hit.get("_source", {})
    return f"{src.get('doc_id')}::{src.get('page_num')}::{hit.get('_id')}"

def rrf_fuse(knn_hits: List[Dict[str, Any]], bm25_hits: List[Dict[str, Any]], top_k=12, k_const: int = 60) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion: score = Σ (1 / (k_const + rank)).
    De-duplicates by doc_id+page_num.
    """
    ranks = {}
    for rank, h in enumerate(knn_hits, start=1):
        k = _key(h)
        if k not in ranks:
            ranks[k] = {"hit": h, "score": 0.0}
        ranks[k]["score"] += 1.0 / (k_const + rank)

    for rank, h in enumerate(bm25_hits, start=1):
        k = _key(h)
        if k not in ranks:
            ranks[k] = {"hit": h, "score": 0.0}
        ranks[k]["score"] += 1.0 / (k_const + rank)

    fused = sorted(ranks.values(), key=lambda x: x["score"], reverse=True)
    return [x["hit"] for x in fused[:top_k]]
