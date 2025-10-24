# split long docs → overlapping chunks
# backend/utils/chunker.py
from typing import List
from pdfminer.high_level import extract_text
import io, csv

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 150

def chunk_text(text: str, chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_OVERLAP) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap
        if start < 0: start = 0
    return chunks

def read_pdf_bytes(b: bytes) -> str:
    with io.BytesIO(b) as f:
        return extract_text(f)

def read_text_bytes(b: bytes) -> str:
    return b.decode("utf-8", errors="ignore")

def read_csv_bytes(b: bytes) -> str:
    f = io.StringIO(b.decode("utf-8", errors="ignore"))
    rdr = csv.reader(f)
    lines = []
    for row in rdr:
        lines.append(", ".join(row))
    return "\n".join(lines)
