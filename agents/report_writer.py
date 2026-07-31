from __future__ import annotations

from agents.base import Agent, InvestigationState


class ReportWriterAgent(Agent):
    name = "report_writer"
    system_prompt = (
        "You are a senior incident responder writing the final report for other analysts. "
        "Structure it as: Summary, Severity, Indicators, ATT&CK mapping (technique IDs and "
        "names), Related past incidents, Recommended mitigations, Next steps. Be precise, "
        "cite technique IDs when you reference them, and do not invent facts not present in "
        "the findings you were given."
    )

    def run(self, state: InvestigationState) -> InvestigationState:
        findings_blob = (
            f"Severity: {state.severity}\n"
            f"IOCs: {state.iocs}\n"
            f"ATT&CK graph findings: {state.graph_findings}\n"
            f"Log evidence: {state.log_findings}\n"
            f"Related past incidents (RAG hits): "
            f"{[{'source': h['id'], 'excerpt': h['text'][:200]} for h in state.intel_findings]}\n"
        )
        state.report = self.ask(f"Write the incident report from these findings:\n\n{findings_blob}")
        state.log(self.name, "generated final report")
        return state
