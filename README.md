# Threat Graph RAG — Multi-Agent Incident Investigation Platform

A knowledge-graph + RAG system for cybersecurity incident investigation,
built on the real **MITRE ATT&CK** knowledge base, with five specialist
agents that share a common graph + vector memory instead of one monolithic
prompt.

Runs entirely locally — no API keys, no cloud calls. Uses [Ollama](https://ollama.com)
for generation and embeddings, [NetworkX](https://networkx.org) for the
graph, and a small numpy-based vector store.

## Why this exists

Most "GraphRAG" demos are a single pipeline: extract entities, embed
chunks, answer questions. This project goes a step further and shows the
pattern that's actually emerging in production security tooling: **multiple
specialized agents that read and write a shared knowledge graph**, so later
agents benefit from what earlier agents found — instead of every question
being answered from scratch.

```
                    Supervisor
         ┌─────┬────────┬────────┬─────┐
      Triage  Investigator  Evidence  Threat intel
         └─────┴────────┴────────┴─────┘
                        │
        Shared knowledge graph + vector store
                        │
                  Report writer
                        │
                 Incident report
```

| Agent | Role |
|---|---|
| **Triage** | Extracts IOCs and severity from the raw alert |
| **Investigator** | Traverses the ATT&CK graph for matching techniques, known threat groups, mitigations |
| **Evidence** | Correlates supporting log lines with the IOCs |
| **Threat intel** | RAG search over past incident write-ups for relevant precedent |
| **Report writer** | Synthesizes everything into a structured, cited report |

## What's real data vs. synthetic

Being upfront about this, because it matters for how you evaluate/extend it:

- **The knowledge graph is real.** `data/attack_graph.json` is built directly
  from the public [MITRE ATT&CK](https://github.com/mitre/cti) STIX dataset —
  858 real techniques, 189 real threat groups, 268 real mitigations, and the
  real relationships between them (`scripts/build_attack_graph.py`).
- **The incident write-ups are synthetic.** There's no public corpus of real
  breach investigations (companies don't publish those), so `data/incidents/*.md`
  are LLM-plausible incident narratives I wrote, each explicitly grounded in
  a real ATT&CK technique ID (`T1566.002`, `T1021.002`, `T1546.013`) so the
  graph and the documents stay consistent. Each file has `synthetic: true`
  in its frontmatter — treat these as a demo corpus, not real threat intel.
  Swap this directory for your own case files / SIEM export to make it real.

## Project layout

```
core/                    Reusable KG + RAG library (backend-agnostic)
  graph_store.py          NetworkX graph, Neo4j-ready interface
  vector_store.py          Embeddings + cosine similarity search
  ollama_client.py         Local LLM client (chat + embeddings)
  attack_loader.py         STIX -> graph schema parser
agents/                  The five specialist agents + supervisor
examples/
  simple_graphrag_qa.py    Minimal standalone GraphRAG example — start here
                            if you just want the core pattern without the
                            security use case or the agent pipeline
scripts/
  build_attack_graph.py    Downloads real ATT&CK data, builds the graph
  build_vector_store.py    Embeds the incident corpus
data/
  attack_graph.json        Committed — compact, ~2.3MB, real ATT&CK graph
  incidents/                Synthetic incident write-ups + a sample log
tests/test_core.py         Unit tests (no Ollama required)
cli.py                    Main entrypoint
```

## Setup

**1. Install Ollama and pull the two models this project uses:**
```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

ollama pull llama3.1
ollama pull nomic-embed-text
ollama serve   # leave running in a separate terminal
```

**2. Clone and install Python dependencies:**
```bash
git clone https://github.com/<your-username>/threat-graph-rag.git
cd threat-graph-rag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**3. Build the graph and vector store:**
```bash
python -m scripts.build_attack_graph     # ~1 min, downloads real ATT&CK data (~46MB, cached after)
python -m scripts.build_vector_store     # embeds the incident corpus via Ollama
```

**4. Run the tests (no Ollama needed for these):**
```bash
pytest tests/ -v
```

**5. Try the minimal example first** (fastest way to see the core pattern):
```bash
python -m examples.simple_graphrag_qa "How is Project Atlas related to the Berlin team?"
```

**6. Run a full multi-agent investigation:**
```bash
python cli.py investigate "Suspicious process spawned from svchost.exe, \
connecting to an admin share on FIN-SRV02, followed by a scheduled task \
creation at 2AM outside change windows." --log-file data/incidents/incident_0002.log
```

**7. Check what's loaded:**
```bash
python cli.py stats
```

## Extending this project

- **Swap NetworkX for Neo4j**: every method in `core/graph_store.py` has its
  Cypher equivalent in the class docstring — the rest of the codebase only
  talks to this file, so nothing else changes.
- **Swap Ollama for a hosted model**: `core/ollama_client.py` is the only
  file that makes LLM calls; point `chat()`/`embed()` at any other API.
- **Plug in real data**: replace `data/incidents/` with real case files or a
  SIEM export, and re-run `build_vector_store.py`. Replace the log-file
  argument with a live log query in `agents/evidence.py`.
- **Add conditional routing**: `agents/supervisor.py` currently runs a fixed
  pipeline; swap it for an LLM that decides the next agent for
  branching investigations (e.g. skip Evidence if there's no log data).

## License

MIT — see [LICENSE](LICENSE).
