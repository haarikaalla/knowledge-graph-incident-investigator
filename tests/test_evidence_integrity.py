import json
from unittest.mock import patch

import numpy as np
import pytest

from agents.base import InvestigationState
from agents.report_writer import ReportWriterAgent
from agents.triage import TriageAgent
from core.vector_store import VectorStore


def test_vector_round_trip_and_search(tmp_path):
    store = VectorStore()
    with patch("core.vector_store.embed", side_effect=[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]):
        store.add("incident-1", "first")
        store.add("incident-2", "second")
        store.save(tmp_path / "index")
        loaded = VectorStore.load(tmp_path / "index")
        assert loaded.search("first", top_k=1)[0]["id"] == "incident-1"


def test_vector_rejects_invalid_embeddings_without_mutating_index():
    store = VectorStore()
    with patch("core.vector_store.embed", return_value=[1.0, 0.0]):
        store.add("one", "text")
    for invalid in ([0.0, 0.0], [float("nan"), 1.0], [1.0, 0.0, 0.0]):
        with patch("core.vector_store.embed", return_value=invalid):
            with pytest.raises(ValueError):
                store.add("two", "text")
    assert store.ids == ["one"]


def test_vector_load_rejects_mismatched_sidecar(tmp_path):
    path = tmp_path / "index"
    store = VectorStore()
    with patch("core.vector_store.embed", return_value=[1.0, 0.0]):
        store.add("one", "text")
    store.save(path)
    sidecar = json.loads(path.with_suffix(".json").read_text())
    sidecar["ids"].append("ghost")
    path.with_suffix(".json").write_text(json.dumps(sidecar))
    with pytest.raises(ValueError, match="mismatched"):
        VectorStore.load(path)


def test_vector_load_rejects_nonfinite_index(tmp_path):
    path = tmp_path / "index"
    store = VectorStore()
    with patch("core.vector_store.embed", return_value=[1.0, 0.0]):
        store.add("one", "text")
    store.save(path)
    np.savez_compressed(path.with_suffix(".npz"), vectors=np.array([[float("nan"), 0.0]]))
    with pytest.raises(ValueError, match="non-finite"):
        VectorStore.load(path)


def test_triage_normalises_untrusted_model_output():
    agent = TriageAgent.__new__(TriageAgent)
    state = InvestigationState(alert_text="alert")
    with patch.object(agent, "ask", return_value=json.dumps({"severity": ["critical"], "iocs": [" 1.2.3.4 ", "1.2.3.4", 9, ""], "summary": ["bad"]})):
        result = agent.run(state)
    assert result.severity == "unknown"
    assert result.iocs == ["1.2.3.4"]
    with patch.object(agent, "ask", return_value="[]"):
        result = agent.run(InvestigationState(alert_text="alert"))
    assert result.severity == "unknown"
    assert result.iocs == []


def test_report_appends_deterministic_evidence_references():
    agent = ReportWriterAgent.__new__(ReportWriterAgent)
    state = InvestigationState(
        alert_text="alert",
        graph_findings=[{"technique_id": "T1566.002"}],
        intel_findings=[{"id": "incident-1", "text": "synthetic case"}],
    )
    with patch.object(agent, "ask", return_value="Analyst draft"):
        result = agent.run(state)
    assert "T1566.002" in result.report
    assert "incident-1" in result.report
    assert "Supporting log supplied: no" in result.report
