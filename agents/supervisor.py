from __future__ import annotations

from core.graph_store import GraphStore
from core.vector_store import VectorStore

from agents.base import InvestigationState
from agents.triage import TriageAgent
from agents.investigator import InvestigatorAgent
from agents.evidence import EvidenceAgent
from agents.threat_intel import ThreatIntelAgent
from agents.report_writer import ReportWriterAgent


class Supervisor:
    """Routes an alert through the fixed pipeline: triage -> investigator ->
    evidence -> threat_intel -> report_writer. Each stage writes to the
    shared InvestigationState, so later agents see everything earlier
    agents found. This is a simple deterministic router; swap in an
    LLM-based router (have the model choose the next agent) once you want
    conditional branching, e.g. skip evidence if there are no logs."""

    def __init__(self, graph: GraphStore, vectors: VectorStore, model: str = "llama3.1", log_text: str = "") -> None:
        self.pipeline = [
            TriageAgent(graph, vectors, model=model),
            InvestigatorAgent(graph, vectors, model=model),
            EvidenceAgent(graph, vectors, model=model, log_text=log_text),
            ThreatIntelAgent(graph, vectors, model=model),
            ReportWriterAgent(graph, vectors, model=model),
        ]

    def investigate(self, alert_text: str, verbose: bool = True) -> InvestigationState:
        state = InvestigationState(alert_text=alert_text)
        for agent in self.pipeline:
            state = agent.run(state)
            if verbose:
                print(state.notes[-1])
        return state
