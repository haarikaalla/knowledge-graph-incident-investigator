from __future__ import annotations

from agents.base import Agent, InvestigationState


class InvestigatorAgent(Agent):
    """Traverses the shared ATT&CK knowledge graph to find techniques, threat
    groups, and software that match the IOCs/behaviors triage extracted."""

    name = "investigator"
    system_prompt = (
        "You are a threat-intel graph analyst. Given a list of indicators/behaviors, "
        "return the most likely MITRE ATT&CK technique NAMES they match (just names, "
        "comma separated, no explanation)."
    )

    def run(self, state: InvestigationState) -> InvestigationState:
        if not state.iocs:
            state.log(self.name, "no IOCs to investigate")
            return state

        guess = self.ask(f"Indicators/behaviors: {', '.join(state.iocs)}")
        candidate_names = [n.strip() for n in guess.split(",") if n.strip()]

        findings = []
        for name in candidate_names:
            matches = self.graph.find_by_type("technique", query=name, limit=2)
            for tech in matches:
                groups = self.graph.neighbors(tech["id"], edge_type="uses", direction="in")
                group_names = [g["node"]["name"] for g in groups if g["node"] and g["node"]["type"] == "group"][:5]
                mitigations = [
                    m["node"]["name"]
                    for m in self.graph.neighbors(tech["id"], edge_type="mitigates", direction="in")
                    if m["node"]
                ][:5]
                findings.append(
                    {
                        "technique_id": tech["id"],
                        "technique_name": tech["name"],
                        "description": tech.get("description", "")[:300],
                        "known_groups": group_names,
                        "mitigations": mitigations,
                    }
                )

        state.graph_findings = findings
        state.log(self.name, f"matched {len(findings)} technique(s) in the ATT&CK graph")
        return state
