"""Review findings share the existing Problems model / 審查結果共用 Problems 模型。"""

import pytest

from je_editor.adapters.review.prthinker_diagnostics import ReviewDiagnostics, diagnostic_from_finding
from je_editor.core.diagnostics.diagnostic_model import DiagnosticStore, Severity


def test_severity_and_quick_fix(tmp_path):
    finding = {"path": "mod.py", "line": 2, "severity": "warning", "comment": "Validate input",
               "suggestion": "validate(value)"}
    diagnostic = diagnostic_from_finding(finding, tmp_path)
    assert diagnostic.severity == Severity.WARNING
    assert diagnostic.range.start.line == 2
    assert diagnostic.fixes[0].edits[0].new_text == "validate(value)\n"
    with pytest.raises(ValueError):
        diagnostic_from_finding(finding | {"path": "../escape"}, tmp_path)


def test_stale_events_and_replacement(tmp_path):
    store = DiagnosticStore()
    consumer = ReviewDiagnostics(store, tmp_path)
    consumer.begin("new")
    finding = {"protocol_version": 1, "request_id": "old", "event": "finding",
               "finding": {"path": "x.py", "line": 1, "comment": "bug"}}
    assert not consumer.receive(finding)
    assert consumer.receive(finding | {"request_id": "new"})
    assert len(store.select()) == 1
    consumer.begin("next")
    assert store.select() == []
