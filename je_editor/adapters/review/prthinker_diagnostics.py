"""Map versioned review findings to editor diagnostics / 將審查結果轉為診斷。"""

from pathlib import Path, PurePosixPath, PureWindowsPath

from je_editor.core.diagnostics.diagnostic_model import Diagnostic, QuickFix, Severity, TextEdit, TextRange
from je_editor.core.uri.resource_uri import to_uri

SOURCE = "prthinker"
SEVERITIES = {"error": Severity.ERROR, "warning": Severity.WARNING, "info": Severity.INFORMATION}


def diagnostic_from_finding(finding: dict, workdir: Path) -> Diagnostic:
    """Reject escaping paths before publishing / 發布前拒絕越界路徑。"""
    relative = finding.get("path", finding.get("file_path", ""))
    path = Path(relative)
    if not relative or PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).root:
        raise ValueError("finding path must be relative")
    target = workdir / path
    if PureWindowsPath(relative).drive or not target.resolve().is_relative_to(workdir.resolve()):
        raise ValueError("finding path escapes workspace")
    line = max(1, int(finding.get("line", 1)))
    end = max(line, int(finding.get("end_line") or line))
    span = TextRange.from_lines(line, 1, end, 1)
    suggestion = finding.get("suggestion") or ""
    fixes = ()
    if suggestion:
        edits = (TextEdit(TextRange.from_lines(line, 1, end + 1, 1), suggestion.rstrip("\n") + "\n"),)
        fixes = (QuickFix("Apply proposed change", edits),)
    return Diagnostic(message=str(finding.get("comment", finding.get("message", ""))), range=span,
                      severity=SEVERITIES.get(finding.get("severity"), Severity.INFORMATION),
                      source=SOURCE, uri=to_uri(target), fixes=fixes)


class ReviewDiagnostics:
    """Replace one review's findings and reject stale events / 取代審查結果並拒絕過期事件。"""

    def __init__(self, store, workdir: Path):
        self.store, self.workdir = store, workdir
        self.request_id = ""
        self.by_uri = {}
        self.status = ""

    def begin(self, request_id: str):
        self.store.clear(source=SOURCE)
        self.request_id, self.by_uri, self.status = request_id, {}, "running"

    def receive(self, event: dict):
        if event.get("protocol_version") != 1:
            raise ValueError("unsupported review protocol")
        if event.get("request_id") != self.request_id:
            return False
        if event.get("event") == "finding":
            diagnostic = diagnostic_from_finding(event["finding"], self.workdir)
            self.by_uri.setdefault(diagnostic.uri, []).append(diagnostic)
            self.store.publish(SOURCE, diagnostic.uri, self.by_uri[diagnostic.uri])
        if event.get("event") == "terminal":
            self.status = event["status"]
        return True
