from __future__ import annotations

import json

from agents.base import Agent, InvestigationState


class TriageAgent(Agent):
    name = "triage"
    system_prompt = (
        "You are a SOC triage analyst. Given a raw alert or incident description, extract "
        "indicators of compromise (process names, file hashes, IPs, domains, technique-like "
        "behaviors) and assign a severity. Respond ONLY with JSON: "
        '{"severity": "low|medium|high|critical", "iocs": ["..."], "summary": "one sentence"}'
    )

    def run(self, state: InvestigationState) -> InvestigationState:
        raw = self.ask(f"Alert:\n{state.alert_text}", json_mode=True)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"severity": "unknown", "iocs": [], "summary": raw[:200]}

        state.severity = parsed.get("severity", "unknown")
        state.iocs = parsed.get("iocs", [])
        state.log(self.name, f"severity={state.severity}, iocs={state.iocs}, summary={parsed.get('summary')}")
        return state
