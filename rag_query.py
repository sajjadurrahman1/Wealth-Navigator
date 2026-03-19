import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

INDEX_PATH = Path("rag/data/faiss.index")
META_PATH = Path("rag/data/metadata.jsonl")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class RAGStore:
    def __init__(self):
        if not INDEX_PATH.exists() or not META_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index or metadata not found. Run rag/ingest_pdfs.py first.\n"
                f"Expected index at: {INDEX_PATH.resolve()}\n"
                f"Expected metadata at: {META_PATH.resolve()}"
            )

        try:
            self.model = SentenceTransformer(MODEL_NAME)
            self.index = faiss.read_index(str(INDEX_PATH))
        except Exception as e:
            raise RuntimeError(f"Failed to load RAG index or model: {e}")

        self.meta = []
        try:
            with META_PATH.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():  # Skip empty lines
                        self.meta.append(json.loads(line))
        except Exception as e:
            raise RuntimeError(f"Failed to load metadata: {e}")
        
        if len(self.meta) == 0:
            raise ValueError("Metadata file is empty. Re-run rag/ingest_pdfs.py")

    def search(self, query: str, top_k: int = 5):
        """
        Search the RAG knowledge base for relevant chunks.
        
        Args:
            query: Search query string
            top_k: Number of top results to return (default: 5)
        
        Returns:
            List of dictionaries with 'score', 'source', 'page', and 'text' keys
        """
        if not query or not query.strip():
            return []
        
        if top_k < 1:
            top_k = 1
        top_k = min(top_k, len(self.meta))  # Don't request more than available
        
        try:
            q_vec = self.model.encode([query], normalize_embeddings=True)
            q_vec = np.array(q_vec, dtype="float32")

            scores, ids = self.index.search(q_vec, top_k)

            results = []
            for score, idx in zip(scores[0], ids[0]):
                if idx == -1 or idx >= len(self.meta):
                    continue
                m = self.meta[idx]
                results.append({
                    "score": float(score),
                    "source": m.get("source", "Unknown"),
                    "page": m.get("page", 0),
                    "text": m.get("text", ""),
                })
            return results
        except Exception as e:
            # Return empty list on error rather than crashing
            print(f"RAG search error: {e}")
            return []
