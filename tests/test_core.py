import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.graph_store import GraphStore, Node, Edge


def build_sample_graph() -> GraphStore:
    g = GraphStore()
    g.add_node(Node("A", "person", {"name": "Alice"}))
    g.add_node(Node("B", "person", {"name": "Bob"}))
    g.add_node(Node("C", "project", {"name": "X"}))
    g.add_edge(Edge("A", "C", "owns"))
    g.add_edge(Edge("B", "C", "contributes_to"))
    return g


def test_add_and_get_node():
    g = build_sample_graph()
    node = g.get_node("A")
    assert node is not None
    assert node["name"] == "Alice"


def test_neighbors():
    g = build_sample_graph()
    nbrs = g.neighbors("C", direction="in")
    ids = sorted(n["node"]["id"] for n in nbrs)
    assert ids == ["A", "B"]


def test_shortest_path():
    g = build_sample_graph()
    path = g.shortest_path("A", "B")
    assert path == ["A", "C", "B"]


def test_stats():
    g = build_sample_graph()
    stats = g.stats()
    assert stats["nodes"] == 3
    assert stats["edges"] == 2
    assert stats["person"] == 2
    assert stats["project"] == 1


def test_save_and_load_roundtrip():
    g = build_sample_graph()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "graph.json"
        g.save(path)
        loaded = GraphStore.load(path)
        assert loaded.stats() == g.stats()
        assert loaded.get_node("A")["name"] == "Alice"


def test_attack_graph_file_loads_if_present():
    """Sanity check on the real committed ATT&CK graph, if it's been built."""
    attack_path = Path(__file__).resolve().parent.parent / "data" / "attack_graph.json"
    if not attack_path.exists():
        return  # not built in this environment, skip
    g = GraphStore.load(attack_path)
    stats = g.stats()
    assert stats["nodes"] > 0
    assert stats.get("technique", 0) > 0
    assert stats.get("group", 0) > 0
