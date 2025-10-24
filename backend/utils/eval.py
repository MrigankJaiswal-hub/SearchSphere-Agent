# backend/utils/eval.py
from typing import List, Dict, Any, Tuple, Iterable

def _hit_id(hit: Dict[str, Any]) -> str:
    src = hit.get("_source", {})
    # prefer your stable IDs used at ingest time
    return str(src.get("chunk_id") or f"{src.get('doc_id')}::{src.get('page_num')}")

def precision_at_k(hits: List[Dict[str, Any]], relevant_ids: Iterable[str], k: int = 10) -> float:
    rel = set(str(x) for x in relevant_ids)
    top = hits[:max(1, k)]
    if not top:
        return 0.0
    found = sum(1 for h in top if _hit_id(h) in rel)
    return found / float(len(top))

def batch_precision(results: List[Tuple[List[Dict[str, Any]], Iterable[str]]], k: int = 10) -> Dict[str, float]:
    """
    results: list of (hits, relevant_ids)
    """
    if not results:
        return {"p_at_k": 0.0, "queries": 0}
    scores = [precision_at_k(hits, rel, k) for hits, rel in results]
    return {"p_at_k": sum(scores) / len(scores), "queries": len(scores)}
