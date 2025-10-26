# backend/scripts/ingest_local.py
"""
Ingest local PDF/CSV/TXT into Elasticsearch with Vertex embeddings (text-embedding-005).
Creates chunks, embeds, and indexes docs with a 'vector' field (dims=768).
"""

import os, sys, json, re
from typing import List, Sequence

from elasticsearch import Elasticsearch

from vertexai import init as vertex_init
try:
    from vertexai.language_models import TextEmbeddingModel  # type: ignore
except Exception:
    from vertexai.preview.language_models import TextEmbeddingModel  # type: ignore

ES_CLOUD_ID = os.getenv("ES_CLOUD_ID")
ES_API_KEY = os.getenv("ES_API_KEY_B64") or os.getenv("ES_API_KEY")
INDEX = os.getenv("ELASTIC_INDEX", "searchsphere_docs")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
EMBED_MODEL_ID = os.getenv("VERTEX_EMBED_MODEL", "text-embedding-005")

CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
EMBED_BATCH = 64

def get_es() -> Elasticsearch:
    if not ES_CLOUD_ID or not ES_API_KEY:
        raise RuntimeError("Set ES_CLOUD_ID and ES_API_KEY_B64 (or ES_API_KEY)")
    return Elasticsearch(cloud_id=ES_CLOUD_ID, api_key=ES_API_KEY, request_timeout=60)

def ensure_index(es: Elasticsearch):
    mapping = {
        "settings": {
            "index": {"number_of_shards": 1, "number_of_replicas": 1, "knn": True}
        },
        "mappings": {
            "properties": {
                "title":    {"type": "text"},
                "doc_id":   {"type": "keyword"},
                "chunk_id": {"type": "keyword"},
                "url":      {"type": "keyword"},
                "text":     {"type": "text"},
                "team":     {"type": "keyword"},
                "doc_type": {"type": "keyword"},
                "page_num": {"type": "integer"},
                "vector":   {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"},
            }
        },
    }
    if not es.indices.exists(index=INDEX):
        es.indices.create(index=INDEX, body=mapping)

def read_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        return open(path, "r", encoding="utf-8", errors="ignore").read()
    if ext == ".csv":
        try:
            import pandas as pd  # type: ignore
            df = pd.read_csv(path)
            return df.to_string(index=False)
        except Exception:
            return open(path, "r", encoding="utf-8", errors="ignore").read()
    if ext == ".pdf":
        from PyPDF2 import PdfReader  # type: ignore
        reader = PdfReader(path)
        pages = [(p.extract_text() or "").strip() for p in reader.pages]
        return "\n\n".join(pages)
    raise ValueError(f"Unsupported file type: {ext}")

def clean_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text or " ")
    return text.strip()

def chunk(text: str, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
    text = clean_whitespace(text)
    if not text:
        return []
    if len(text) <= size:
        return [text]
    out: List[str] = []
    i = 0
    while i < len(text):
        end = min(i + size, len(text))
        out.append(text[i:end])
        if end == len(text):
            break
        i = max(end - overlap, 0)
    return out

def embed(texts: Sequence[str]) -> List[List[float]]:
    if not texts:
        return []
    vertex_init(project=GCP_PROJECT_ID, location=VERTEX_LOCATION)
    model = TextEmbeddingModel.from_pretrained(EMBED_MODEL_ID)
    vecs: List[List[float]] = []
    for start in range(0, len(texts), EMBED_BATCH):
        batch = list(texts[start:start+EMBED_BATCH])
        resp = model.get_embeddings(batch)  # type: ignore[arg-type]
        vecs.extend([e.values for e in resp])
    return vecs

def guess_doc_type(path: str) -> str:
    return os.path.splitext(path)[1].lower().replace(".", "") or "text"

def main(path: str, team: str = "demo"):
    if not GCP_PROJECT_ID:
        raise RuntimeError("Set GCP_PROJECT_ID")
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        raise RuntimeError("Set GOOGLE_APPLICATION_CREDENTIALS to your service-account JSON")

    es = get_es()
    ensure_index(es)

    title = os.path.basename(path)
    doc_type = guess_doc_type(path)
    raw = read_text(path)
    parts = chunk(raw)
    if not parts:
        print("No text extracted from file; nothing to index.")
        return

    vecs = embed(parts)
    if len(vecs) != len(parts):
        raise RuntimeError(f"Embedding count mismatch: {len(vecs)} vs chunks {len(parts)}")

    for i, (txt, vec) in enumerate(zip(parts, vecs)):
        doc = {
            "title": title,
            "doc_id": title,
            "chunk_id": f"{title}::chunk::{i}",
            "url": f"local://{path}",
            "text": txt,
            "team": team,
            "doc_type": doc_type,
            "page_num": i,       # simple index (pdf page mapping would need extra tracking)
            "vector": vec,
        }
        es.index(index=INDEX, id=f"{title}_{i}", document=doc)

    print(f"✅ Indexed {len(parts)} chunks into '{INDEX}' from {path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/ingest_local.py <file> [team]")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "demo")
