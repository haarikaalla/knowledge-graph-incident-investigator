"""
Parses a MITRE ATT&CK STIX 2.1 bundle (enterprise-attack.json) into our
GraphStore schema. This is real threat-intel data, not synthetic — the
techniques, groups, software, and mitigations below are the actual public
ATT&CK knowledge base: https://github.com/mitre/cti

STIX types we keep (the rest, e.g. detection-strategy/analytic objects,
are noise for a demo graph and are dropped):
  attack-pattern  -> Technique
  intrusion-set   -> Group   (a named threat actor)
  malware, tool   -> Software
  course-of-action -> Mitigation
  campaign        -> Campaign
  relationship    -> Edge between the above
"""
from __future__ import annotations

import json
from pathlib import Path

from core.graph_store import GraphStore, Node, Edge

STIX_TO_NODE_TYPE = {
    "attack-pattern": "technique",
    "intrusion-set": "group",
    "malware": "software",
    "tool": "software",
    "course-of-action": "mitigation",
    "campaign": "campaign",
}


def _external_id(obj: dict) -> str | None:
    for ref in obj.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def load_attack_graph(stix_path: str | Path, max_relationships: int | None = None) -> GraphStore:
    data = json.loads(Path(stix_path).read_text())
    objects = data["objects"]

    store = GraphStore()
    stix_id_to_node_id: dict[str, str] = {}

    # Pass 1: entity nodes
    for obj in objects:
        otype = obj.get("type")
        if otype not in STIX_TO_NODE_TYPE:
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        node_type = STIX_TO_NODE_TYPE[otype]
        attack_id = _external_id(obj) or obj["id"]
        node = Node(
            id=attack_id,
            type=node_type,
            props={
                "name": obj.get("name", ""),
                "description": (obj.get("description") or "")[:500],
                "platforms": obj.get("x_mitre_platforms", []),
                "tactics": [p.get("phase_name") for p in obj.get("kill_chain_phases", [])],
            },
        )
        store.add_node(node)
        stix_id_to_node_id[obj["id"]] = attack_id

    # Pass 2: relationships
    rel_count = 0
    for obj in objects:
        if obj.get("type") != "relationship":
            continue
        src, tgt = obj.get("source_ref"), obj.get("target_ref")
        if src not in stix_id_to_node_id or tgt not in stix_id_to_node_id:
            continue
        store.add_edge(
            Edge(
                source=stix_id_to_node_id[src],
                target=stix_id_to_node_id[tgt],
                type=obj.get("relationship_type", "related-to"),
            )
        )
        rel_count += 1
        if max_relationships and rel_count >= max_relationships:
            break

    return store
