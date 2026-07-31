from __future__ import annotations

from dataclasses import dataclass, field

from core.graph_store import GraphStore
from core.ollama_client import chat
from core.vector_store import VectorStore


@dataclass
class InvestigationState:
    """Shared scratchpad every agent reads from and writes to."""
    alert_text: str
    iocs: list[str] = field(default_factory=list)
    severity: str | None = None
    graph_findings: list[dict] = field(default_factory=list)
    log_findings: list[dict] = field(default_factory=list)
    intel_findings: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    report: str | None = None

    def log(self, agent: str, message: str) -> None:
        self.notes.append(f"[{agent}] {message}")


class Agent:
    name = "base"
    system_prompt = "You are a helpful assistant."

    def __init__(self, graph: GraphStore, vectors: VectorStore, model: str = "llama3.1") -> None:
        self.graph = graph
        self.vectors = vectors
        self.model = model

    def ask(self, prompt: str, json_mode: bool = False) -> str:
        return chat(prompt, system=self.system_prompt, model=self.model, json_mode=json_mode)

    def run(self, state: InvestigationState) -> InvestigationState:
        raise NotImplementedError
