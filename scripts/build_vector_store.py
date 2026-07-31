"""
Embeds every incident write-up in data/incidents/*.md into a VectorStore.
Requires Ollama running with the nomic-embed-text model pulled:
    ollama pull nomic-embed-text

Usage:
    python -m scripts.build_vector_store
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.vector_store import VectorStore  # noqa: E402

INCIDENTS_DIR = Path("data/incidents")
OUTPUT = Path("data/incident_vectors")


def main() -> None:
    store = VectorStore()
    md_files = sorted(INCIDENTS_DIR.glob("*.md"))
    if not md_files:
        print(f"No incident files found in {INCIDENTS_DIR}")
        return

    for path in md_files:
        text = path.read_text()
        print(f"Embedding {path.name} ...")
        store.add(doc_id=path.stem, text=text, metadata={"source": str(path)})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    store.save(OUTPUT)
    print(f"Saved vector store to {OUTPUT}.npz / {OUTPUT}.json ({len(md_files)} documents)")


if __name__ == "__main__":
    main()
