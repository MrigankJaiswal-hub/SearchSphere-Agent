# latency logging
# backend/utils/timer.py
import time
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    t0 = time.time()
    yield
    elapsed = (time.time() - t0) * 1000
    print(f"[TIMER] {name}: {elapsed:.1f} ms")
