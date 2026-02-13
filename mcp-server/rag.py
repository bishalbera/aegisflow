import re
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class DeviceManualRetriever:
    """
    Simple vector-based retrieval over a markdown equipment manual.

    Chunks the document by ## sections, encodes with sentence-transformers,
    and returns the top-k most relevant chunks for a query.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self, manual_path: str):
        self.manual_path = manual_path
        self.model = SentenceTransformer(self.MODEL_NAME)
        self.chunks: List[str] = []
        self.embeddings: np.ndarray = np.array([])
        self._load_and_index()

    def _load_and_index(self):
        with open(self.manual_path, "r") as f:
            text = f.read()

        raw_chunks = re.split(r"(?=^##\s)", text, flags=re.MULTILINE)
        raw_chunks = [c.strip() for c in raw_chunks if c.strip()]

        final_chunks = []
        for chunk in raw_chunks:
            sub = re.split(r"(?=^###\s)", chunk, flags=re.MULTILINE)
            for s in sub:
                s = s.strip()
                if s:
                    final_chunks.append(s)

        self.chunks = final_chunks
        self.embeddings = self.model.encode(final_chunks, convert_to_numpy=True, show_progress_bar=False)

    def query(self, text: str, k: int = 3) -> List[str]:
        """Return the top-k most relevant manual sections for the query."""
        if not self.chunks:
            return []

        query_emb = self.model.encode([text], convert_to_numpy=True)

        norms_chunks = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norms_query = np.linalg.norm(query_emb, axis=1, keepdims=True)
        sim = (self.embeddings @ query_emb.T) / (norms_chunks * norms_query + 1e-10)
        scores = sim[:, 0]

        top_indices = np.argsort(scores)[::-1][:k]
        return [self.chunks[i] for i in top_indices]
