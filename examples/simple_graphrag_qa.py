"""
Simple GraphRAG Q&A — a minimal, self-contained example of the core
knowledge-graph + RAG pattern, independent of the security use case.

This is the "start here" example: no ATT&CK data, no agents, no external
downloads — just entity extraction -> graph -> hybrid retrieval -> answer,
on a tiny hardcoded document set. Read this file top to bottom to
understand the pattern before looking at the full multi-agent platform.

Usage:
    python -m examples.simple_graphrag_qa "How is Project Atlas related to the Berlin team?"
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.graph_store import GraphStore, Node, Edge  # noqa: E402
from core.vector_store import VectorStore  # noqa: E402
from core.ollama_client import chat  # noqa: E402

# A tiny, hand-written document set — swap this for your own docs.
DOCS = {
    "doc1": "Project Atlas is led by the Berlin engineering team. It ships a new "
            "search ranking model and is scheduled to launch in Q3.",
    "doc2": "The Berlin team also owns Project Nimbus, an internal analytics "
            "dashboard used by the sales organization.",
    "doc3": "Project Atlas depends on the shared embeddings service, which is "
            "maintained by the Platform team in Amsterdam.",
}

# In a real pipeline you'd extract these with an LLM call (see
# core/attack_loader.py or agents/investigator.py for that pattern). Kept
# hardcoded here so this example needs zero setup beyond Ollama running.
ENTITIES = [
    Node("Project Atlas", "project", {"status": "in progress"}),
    Node("Project Nimbus", "project", {"status": "shipped"}),
    Node("Berlin Team", "team", {}),
    Node("Platform Team", "team", {}),
    Node("Embeddings Service", "service", {}),
]
RELATIONSHIPS = [
    Edge("Berlin Team", "Project Atlas", "owns"),
    Edge("Berlin Team", "Project Nimbus", "owns"),
    Edge("Project Atlas", "Embeddings Service", "depends_on"),
    Edge("Platform Team", "Embeddings Service", "maintains"),
]


def build() -> tuple[GraphStore, VectorStore]:
    graph = GraphStore()
    for n in ENTITIES:
        graph.add_node(n)
    for e in RELATIONSHIPS:
        graph.add_edge(e)

    vectors = VectorStore()
    for doc_id, text in DOCS.items():
        vectors.add(doc_id, text)

    return graph, vectors


def answer(question: str, graph: GraphStore, vectors: VectorStore) -> str:
    # Graph side: pull related entities so the model has structured context.
    graph_context = []
    for node_id in graph.g.nodes:
        if node_id.lower() in question.lower():
            for nbr in graph.neighbors(node_id):
                graph_context.append(f"{node_id} --{nbr['relation']}--> {nbr['node']['id']}")

    # Vector side: semantic search over the raw documents.
    doc_hits = vectors.search(question, top_k=2)
    doc_context = [h["text"] for h in doc_hits]

    prompt = (
        f"Graph relationships:\n{chr(10).join(graph_context) or 'none found'}\n\n"
        f"Relevant document excerpts:\n{chr(10).join(doc_context)}\n\n"
        f"Question: {question}\n\n"
        f"Answer using only the information above."
    )
    return chat(prompt, system="You are a precise assistant that only uses given context.")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How is Project Atlas related to the Berlin team?"
    g, v = build()
    print(answer(q, g, v))
