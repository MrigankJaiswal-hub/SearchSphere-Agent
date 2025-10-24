# backend/utils/metrics.py
from collections import deque
from statistics import median
from typing import Deque, Dict, Literal
import threading
from typing import Optional

MetricName = Literal["search", "chat"]

_lock = threading.Lock()
_counters: Dict[MetricName, int] = {"search": 0, "chat": 0}
_latencies: Dict[MetricName, Deque[float]] = {"search": deque(maxlen=500), "chat": deque(maxlen=500)}
_eval: dict = {"k": 10, "p_at_k": 0.0, "runs": 0}

def record(metric: MetricName, latency_ms: float) -> None:
    with _lock:
        _counters[metric] += 1
        _latencies[metric].append(float(latency_ms))

def _percentile(values, p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)

def snapshot() -> Dict[str, dict]:
    with _lock:
        out = {}
        for name in ("search", "chat"):
            arr = list(_latencies[name])
            out[name] = {
                "count": _counters[name],
                "p50_ms": median(arr) if arr else 0.0,
                "p95_ms": _percentile(arr, 0.95) if arr else 0.0,
                "samples": len(arr)
            }
        out["eval"] = dict(_eval)  # include P@K
        return out


def set_eval_precision(k: int, p_at_k: float) -> None:
    with _lock:
        _eval["k"] = int(k)
        _eval["p_at_k"] = float(p_at_k)
        _eval["runs"] += 1

def get_eval_precision() -> dict:
    with _lock:
        return dict(_eval)