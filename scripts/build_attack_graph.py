"""
Downloads the real MITRE ATT&CK Enterprise dataset and compiles it into
data/attack_graph.json — a compact node/edge file the rest of the project
reads. Re-run this any time you want the latest ATT&CK release.

Usage:
    python -m scripts.build_attack_graph
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.attack_loader import load_attack_graph  # noqa: E402

ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
RAW_CACHE = Path("data/.cache/enterprise-attack.json")
OUTPUT = Path("data/attack_graph.json")


def main() -> None:
    RAW_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not RAW_CACHE.exists():
        print(f"Downloading ATT&CK dataset from {ATTACK_URL} ...")
        urllib.request.urlretrieve(ATTACK_URL, RAW_CACHE)
    else:
        print(f"Using cached dataset at {RAW_CACHE}")

    print("Parsing STIX bundle into graph schema ...")
    store = load_attack_graph(RAW_CACHE)
    stats = store.stats()
    print("Graph built:", stats)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    store.save(OUTPUT)
    print(f"Saved graph to {OUTPUT} ({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
