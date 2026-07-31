from __future__ import annotations

from agents.base import Agent, InvestigationState


class EvidenceAgent(Agent):
    """Parses supporting log lines (passed in via state.notes context or a log
    file) and correlates them with the IOCs triage found. In this demo, logs
    are read from data/incidents/*.log; wire this up to a real SIEM query
    later without touching any other agent."""

    name = "evidence"
    system_prompt = (
        "You are a log analyst. Given raw log lines and a list of indicators of "
        "interest, summarize in 2-3 sentences what happened, in chronological order, "
        "and flag anything unusual. Be concise and factual."
    )

    def __init__(self, *args, log_text: str = "", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.log_text = log_text

    def run(self, state: InvestigationState) -> InvestigationState:
        if not self.log_text:
            state.log(self.name, "no log data provided for this investigation")
            return state

        summary = self.ask(
            f"Indicators of interest: {', '.join(state.iocs)}\n\nLog lines:\n{self.log_text}"
        )
        state.log_findings = [{"summary": summary}]
        state.log(self.name, "correlated log evidence with IOCs")
        return state
