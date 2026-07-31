"""
Minimal vector store: embeddings + cosine similarity search, kept in memory
and persisted as a .npz + json sidecar. No FAISS/Chroma dependency — this
scales fine to tens of thousands of chunks, which covers this project.
Swap in FAISS/Chroma/pgvector later if you outgrow it; the interface
(add, search) stays identical.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from core.ollama_client import embed


class VectorStore:
    def __init__(self) -> None:
        self.ids: list[str] = []
        self.texts: list[str] = []
        self.metadata: list[dict] = []
        self.vectors: np.ndarray | None = None  # shape (n, dim)

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        vec = np.array(embed(text), dtype=np.float32)
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        self.ids.append(doc_id)
        self.texts.append(text)
        self.metadata.append(metadata or {})
        if self.vectors is None:
            self.vectors = vec.reshape(1, -1)
        else:
            self.vectors = np.vstack([self.vectors, vec])

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self.vectors is None or len(self.ids) == 0:
            return []
        q = np.array(embed(query), dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-8)
        scores = self.vectors @ q  # cosine similarity, vectors already unit-norm
        top_idx = np.argsort(-scores)[:top_k]
        return [
            {
                "id": self.ids[i],
                "text": self.texts[i],
                "metadata": self.metadata[i],
                "score": float(scores[i]),
            }
            for i in top_idx
        ]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        np.savez_compressed(path.with_suffix(".npz"), vectors=self.vectors)
        path.with_suffix(".json").write_text(
            json.dumps({"ids": self.ids, "texts": self.texts, "metadata": self.metadata})
        )

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        path = Path(path)
        store = cls()
        sidecar = json.loads(path.with_suffix(".json").read_text())
        store.ids = sidecar["ids"]
        store.texts = sidecar["texts"]
        store.metadata = sidecar["metadata"]
        npz = np.load(path.with_suffix(".npz"))
        store.vectors = npz["vectors"]
        return store
