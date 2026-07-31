"""
Graph store abstraction.

Design note: this wraps NetworkX so the whole project runs with zero
external services. Every method here maps 1:1 onto a Cypher equivalent
(shown in each docstring), so swapping the backend for Neo4j later is a
~20-line change confined to this one file — nothing in agents/ or
core/vector_store.py needs to know which backend is in use.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx


@dataclass
class Node:
    id: str
    type: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    type: str
    props: dict[str, Any] = field(default_factory=dict)


class GraphStore:
    """A directed, typed property graph.

    Swap-to-Neo4j guide (when you outgrow single-machine demo use):
      - add_node()      -> MERGE (n:{type} {id: $id}) SET n += $props
      - add_edge()      -> MATCH (a {id:$s}),(b {id:$t}) MERGE (a)-[r:{type}]->(b) SET r += $props
      - neighbors()      -> MATCH (n {id:$id})-[r]-(m) RETURN m, r
      - shortest_path()  -> MATCH p=shortestPath((a {id:$s})-[*..hops]-(b {id:$t})) RETURN p
      - find_by_type()   -> MATCH (n:{type}) WHERE n.name CONTAINS $q RETURN n
    """

    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

    # -- writes -----------------------------------------------------------
    def add_node(self, node: Node) -> None:
        self.g.add_node(node.id, type=node.type, **node.props)

    def add_edge(self, edge: Edge) -> None:
        self.g.add_edge(edge.source, edge.target, key=edge.type, type=edge.type, **edge.props)

    # -- reads --------------------------------------------------------------
    def get_node(self, node_id: str) -> dict[str, Any] | None:
        if node_id not in self.g:
            return None
        return {"id": node_id, **self.g.nodes[node_id]}

    def neighbors(self, node_id: str, edge_type: str | None = None, direction: str = "out") -> list[dict]:
        if node_id not in self.g:
            return []
        results = []
        edges = self.g.out_edges(node_id, data=True) if direction == "out" else self.g.in_edges(node_id, data=True)
        for u, v, data in edges:
            if edge_type and data.get("type") != edge_type:
                continue
            other = v if direction == "out" else u
            results.append({"node": self.get_node(other), "relation": data.get("type")})
        return results

    def shortest_path(self, source: str, target: str, max_hops: int = 4) -> list[str] | None:
        try:
            path = nx.shortest_path(self.g.to_undirected(), source, target)
            if len(path) - 1 > max_hops:
                return None
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def find_by_type(self, node_type: str, query: str | None = None, limit: int = 20) -> list[dict]:
        out = []
        for nid, data in self.g.nodes(data=True):
            if data.get("type") != node_type:
                continue
            if query and query.lower() not in str(data.get("name", "")).lower():
                continue
            out.append({"id": nid, **data})
            if len(out) >= limit:
                break
        return out

    def stats(self) -> dict[str, int]:
        type_counts: dict[str, int] = {}
        for _, data in self.g.nodes(data=True):
            t = data.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        return {"nodes": self.g.number_of_nodes(), "edges": self.g.number_of_edges(), **type_counts}

    # -- persistence --------------------------------------------------------
    def save(self, path: str | Path) -> None:
        data = {
            "nodes": [{"id": n, **d} for n, d in self.g.nodes(data=True)],
            "edges": [{"source": u, "target": v, "type": d.get("type"), "props": {k: val for k, val in d.items() if k not in ("type",)}}
                      for u, v, d in self.g.edges(data=True)],
        }
        Path(path).write_text(json.dumps(data))

    @classmethod
    def load(cls, path: str | Path) -> "GraphStore":
        store = cls()
        data = json.loads(Path(path).read_text())
        for n in data["nodes"]:
            nid = n.pop("id")
            store.g.add_node(nid, **n)
        for e in data["edges"]:
            store.g.add_edge(e["source"], e["target"], key=e["type"], type=e["type"], **e.get("props", {}))
        return store
