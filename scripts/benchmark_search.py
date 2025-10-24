# scripts/benchmark_search.py
"""
Run Precision@K against your live backend (local or Cloud Run).
Usage:
  python scripts/benchmark_search.py --base http://localhost:8080 --k 10 --file groundtruth.json
"""

import argparse, json, requests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Backend base (e.g., http://localhost:8080)")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--file", required=True, help="Path to groundtruth JSON")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Normalize to EvalRequest
    items = [{"query": q["query"], "relevant_ids": q["relevant_ids"]} for q in payload.get("items", [])]
    req = {"k": args.k, "items": items, "filters": payload.get("filters")}
    r = requests.post(f"{args.base}/api/eval/precision", json=req, timeout=120)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    main()
