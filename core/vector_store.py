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


def _unit_vector(values: list[float], expected_dim: int | None = None) -> np.ndarray:
    """Reject malformed embeddings before they can enter a saved index."""
    vector = np.asarray(values, dtype=np.float32)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError("Embedding must be a nonempty one-dimensional vector")
    if expected_dim is not None and vector.size != expected_dim:
        raise ValueError(f"Embedding dimension {vector.size} does not match index dimension {expected_dim}")
    if not np.isfinite(vector).all():
        raise ValueError("Embedding contains a non-finite value")
    length = float(np.linalg.norm(vector))
    if not np.isfinite(length) or length <= 0:
        raise ValueError("Embedding has zero or invalid length")
    return vector / length


class VectorStore:
    def __init__(self) -> None:
        self.ids: list[str] = []
        self.texts: list[str] = []
        self.metadata: list[dict] = []
        self.vectors: np.ndarray | None = None  # shape (n, dim)

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        if not doc_id or doc_id in self.ids:
            raise ValueError("Document ID must be nonempty and unique")
        expected_dim = self.vectors.shape[1] if self.vectors is not None else None
        vec = _unit_vector(embed(text), expected_dim)
        self.ids.append(doc_id)
        self.texts.append(text)
        self.metadata.append(metadata or {})
        if self.vectors is None:
            self.vectors = vec.reshape(1, -1)
        else:
            self.vectors = np.vstack([self.vectors, vec])

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if self.vectors is None or len(self.ids) == 0:
            return []
        q = _unit_vector(embed(query), self.vectors.shape[1])
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
        vectors = self.vectors if self.vectors is not None else np.empty((0, 0), dtype=np.float32)
        np.savez_compressed(path.with_suffix(".npz"), vectors=vectors)
        path.with_suffix(".json").write_text(
            json.dumps({"ids": self.ids, "texts": self.texts, "metadata": self.metadata})
        )

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        path = Path(path)
        store = cls()
        sidecar = json.loads(path.with_suffix(".json").read_text())
        ids, texts, metadata = sidecar["ids"], sidecar["texts"], sidecar["metadata"]
        if not all(isinstance(part, list) for part in (ids, texts, metadata)):
            raise ValueError("Invalid vector sidecar: expected lists")
        if not all(isinstance(value, str) and value for value in ids):
            raise ValueError("Invalid vector sidecar: document IDs must be nonempty strings")
        if len(ids) != len(texts) or len(ids) != len(metadata) or len(set(ids)) != len(ids):
            raise ValueError("Vector sidecar has mismatched or duplicate document entries")
        if not all(isinstance(value, str) for value in texts) or not all(isinstance(value, dict) for value in metadata):
            raise ValueError("Invalid vector sidecar: malformed text or metadata")
        with np.load(path.with_suffix(".npz"), allow_pickle=False) as npz:
            vectors = npz["vectors"].copy()
        if vectors.ndim != 2 or vectors.shape[0] != len(ids) or (len(ids) and vectors.shape[1] == 0):
            raise ValueError("Vector index shape does not match the sidecar")
        if not np.isfinite(vectors).all():
            raise ValueError("Vector index contains non-finite values")
        if len(ids) and not np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-3):
            raise ValueError("Vector index contains unnormalized embeddings")
        store.ids, store.texts, store.metadata = ids, texts, metadata
        store.vectors = vectors if len(ids) else None
        return store
