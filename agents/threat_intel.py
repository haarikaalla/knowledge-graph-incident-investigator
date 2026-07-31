from __future__ import annotations

from agents.base import Agent, InvestigationState


class ThreatIntelAgent(Agent):
    """The RAG half of the system: semantic search over past incident write-ups
    and ATT&CK technique descriptions to add context graph traversal alone
    can't give (nuance, past-incident narrative, analyst notes)."""

    name = "threat_intel"

    def run(self, state: InvestigationState) -> InvestigationState:
        query = " ".join(state.iocs) or state.alert_text
        hits = self.vectors.search(query, top_k=3)
        state.intel_findings = hits
        state.log(self.name, f"retrieved {len(hits)} relevant document(s) via vector search")
        return state
