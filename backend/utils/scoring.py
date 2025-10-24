# weighted scoring logic
# backend/utils/scoring.py
def linear_combine(vec_score: float, bm25_score: float, alpha: float = 0.6) -> float:
    return alpha * (vec_score or 0.0) + (1 - alpha) * (bm25_score or 0.0)
