"""
Threat Graph RAG — multi-agent incident investigation CLI.

Usage:
    python cli.py investigate "Suspicious PowerShell process spawned from svchost.exe,
        connecting to an admin share on FIN-SRV02, followed by a scheduled task
        creation at 2AM outside change windows."

    python cli.py investigate --log-file data/incidents/incident_0002.log "..."

    python cli.py stats                # show graph + vector store stats
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.graph_store import GraphStore
from core.vector_store import VectorStore
from core.ollama_client import OllamaError
from agents.supervisor import Supervisor

GRAPH_PATH = Path("data/attack_graph.json")
VECTOR_PATH = Path("data/incident_vectors")


def _load_backends() -> tuple[GraphStore, VectorStore]:
    if not GRAPH_PATH.exists():
        sys.exit(f"Graph not found at {GRAPH_PATH}. Run: python -m scripts.build_attack_graph")
    graph = GraphStore.load(GRAPH_PATH)

    vectors = VectorStore()
    if VECTOR_PATH.with_suffix(".json").exists():
        vectors = VectorStore.load(VECTOR_PATH)
    else:
        print(f"Warning: no vector store at {VECTOR_PATH}. "
              f"Run: python -m scripts.build_vector_store", file=sys.stderr)
    return graph, vectors


def cmd_stats(_: argparse.Namespace) -> None:
    graph, vectors = _load_backends()
    print("Graph:", graph.stats())
    print("Vector store documents:", len(vectors.ids))


def cmd_investigate(args: argparse.Namespace) -> None:
    graph, vectors = _load_backends()
    log_text = Path(args.log_file).read_text() if args.log_file else ""

    supervisor = Supervisor(graph, vectors, model=args.model, log_text=log_text)
    try:
        state = supervisor.investigate(args.alert_text)
    except OllamaError as e:
        sys.exit(str(e))

    print("\n" + "=" * 70)
    print("INCIDENT REPORT")
    print("=" * 70)
    print(state.report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Threat Graph RAG investigation CLI")
    sub = parser.add_subparsers(required=True)

    p_stats = sub.add_parser("stats", help="Show graph and vector store stats")
    p_stats.set_defaults(func=cmd_stats)

    p_inv = sub.add_parser("investigate", help="Run a full multi-agent investigation")
    p_inv.add_argument("alert_text", help="Raw alert / incident description")
    p_inv.add_argument("--log-file", default=None, help="Optional path to supporting log evidence")
    p_inv.add_argument("--model", default="llama3.1", help="Ollama model to use")
    p_inv.set_defaults(func=cmd_investigate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
