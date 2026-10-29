# Threat Graph RAG — Multi-Agent Incident Investigation Platform

[![Tests](https://github.com/haarikaalla/knowledge-graph-incident-investigator/actions/workflows/tests.yml/badge.svg)](https://github.com/haarikaalla/knowledge-graph-incident-investigator/actions/workflows/tests.yml)

A knowledge-graph + RAG system for cybersecurity incident investigation,
built on the real **MITRE ATT&CK** knowledge base, with five specialist
agents that share a common graph + vector memory instead of one monolithic
prompt.

Runs entirely locally — no API keys, no cloud calls. Uses [Ollama](https://ollama.com)
for generation and embeddings, [NetworkX](https://networkx.org) for the
graph, and a small numpy-based vector store.

The report is an **analyst aid**, not a confirmed finding. Its deterministic
evidence ledger lists the ATT&CK technique IDs and incident documents actually
matched or retrieved, plus whether supporting log data was supplied. The LLM
narrative still needs human verification.

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

### Evidence and failure boundaries

- Triage accepts only four named severity levels and a bounded list of
  nonempty string indicators. Invalid model JSON becomes `unknown` severity
  with no indicators instead of entering graph search as trusted data.
- Vector embeddings must be finite, nonzero, and the same dimension. A saved
  index is checked against its JSON sidecar before a search can use it.
- The report appends references from program state after the model writes its
  narrative; the model cannot invent entries in this ledger.
- The five agents run in a fixed order. The tests use mocked Ollama responses;
  live investigative quality is not measured by this test suite.

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
  697 technique nodes, 174 group nodes, 44 mitigation nodes, and the
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
git clone https://github.com/haarikaalla/knowledge-graph-incident-investigator.git
cd knowledge-graph-incident-investigator
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
python -m pytest tests/ -v
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

CI runs the offline tests on Python 3.10 and 3.13. The integrity tests cover
malformed LLM triage output, invalid or inconsistent vector files, and the
deterministic report references. For a full local demonstration, build the
index with Ollama, run the investigation command above, and compare the
report's ledger against the graph and retrieved incident files.

**Data handling:** Real case files and logs can contain sensitive information.
The sample incidents are synthetic. Review permissions and retention before
using operational data; this demo has no multi-user access controls or SIEM
integration.

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
