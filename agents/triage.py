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
            parsed = {}

        if not isinstance(parsed, dict):
            parsed = {}
        severity = parsed.get("severity")
        state.severity = severity if isinstance(severity, str) and severity in {"low", "medium", "high", "critical"} else "unknown"
        candidates = parsed.get("iocs")
        if not isinstance(candidates, list):
            candidates = []
        state.iocs = list(dict.fromkeys(
            item.strip() for item in candidates[:50]
            if isinstance(item, str) and 0 < len(item.strip()) <= 256
        ))
        summary = parsed.get("summary")
        summary = summary[:200] if isinstance(summary, str) else "Unvalidated model output"

        state.log(self.name, f"severity={state.severity}, iocs={state.iocs}, summary={summary}")
        return state
