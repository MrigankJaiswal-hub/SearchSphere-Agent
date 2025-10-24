# text-embedding-005 client
# backend/services/vertex_embeddings.py
import os
from typing import List
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel

def _init_vertex(location: str):
    project = os.getenv("GCP_PROJECT_ID")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID not set")
    aiplatform.init(project=project, location=location)
    vertexai.init(project=project, location=location)

def embed_texts(texts: List[str], location="us-central1", model="text-embedding-005") -> List[List[float]]:
    _init_vertex(location)
    mdl = TextEmbeddingModel.from_pretrained(model)
    # Vertex returns one embedding per input
    res = mdl.get_embeddings(texts)
    return [e.values for e in res]
