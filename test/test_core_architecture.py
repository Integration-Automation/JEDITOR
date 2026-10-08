"""Tests that hold the line between the core service layer and Qt."""
from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from je_editor import core

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPO_ROOT / "je_editor"
CORE_ROOT = PACKAGE_ROOT / "core"
# The legacy facade: it imports the whole Qt application, and every import of a
# sub-package runs it. It is left out of the import graph for that reason, and
# the runtime probe below is what shows the core layer works without it.
TOP_LEVEL_INIT = PACKAGE_ROOT / "__init__.py"

# Top-level modules that bring Qt, or an application built on it, into a process
QT_MODULES = frozenset({"PySide6", "shiboken6", "qt_material", "qtconsole", "frontengine"})
# The parts of je_editor that are the Qt application
UI_MODULES = ("je_editor.pyside_ui", "je_editor.start_editor")
# The packages below the UI: logic only
LOGIC_PACKAGES = ("core", "adapters", "utils", "code_scan", "git_client", "plugins")
# The modules below the UI that reach upwards today. This is a ratchet: the set
# may shrink, and a new entry needs a reason as good as these.
KNOWN_UPWARD_IMPORTS = {
    # Reads the system locale through QLocale (QtCore, no widgets)
    "je_editor/utils/multi_language/locale_match.py": {"PySide6.QtCore"},
    # The highlighting tables the plugin API fills; that module itself is Qt-free
    "je_editor/plugins/__init__.py": {"je_editor.pyside_ui.code.syntax.syntax_setting"},
}
# Run in a child process: build the services where no Qt module can be imported.
# argv[1] is the je_editor directory, argv[2] the comma-separated modules to refuse.
QT_FREE_PROBE = textwrap.dedent(
    """
    import sys
    import types

    package_root, blocked = sys.argv[1], set(sys.argv[2].split(","))


    class RefuseQt:
        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] in blocked:
                raise ImportError(f"{name} is blocked in this probe")
            return None


    sys.meta_path.insert(0, RefuseQt())
    bare = types.ModuleType("je_editor")
    bare.__path__ = [package_root]
    sys.modules["je_editor"] = bare

    from je_editor.core import (
        Diagnostic, EditorServices, Severity, TextDocument, TextRange, Workspace, to_uri
    )

    services = EditorServices(Workspace.single_root(package_root))
    uri = to_uri(package_root + "/probe.py")
    services.documents.open(TextDocument(uri, "import os\\n", "python"))
    services.diagnostics.publish("probe", uri, [
        Diagnostic("unused import", TextRange.from_lines(1), Severity.WARNING)])
    loaded_qt = sorted(name for name in sys.modules if name.split(".")[0] in blocked)
    print(len(services.workspace.roots), len(services.documents),
          services.diagnostics.counts()[Severity.WARNING], loaded_qt)
    services.shutdown()
    """
)


def imports_in(source: str, package: str = "") -> set[str]:
    """
    Every module a piece of source imports, wherever the import statement is.

    ``from a import b`` reports both ``a`` and ``a.b``, since ``b`` may be a
    sub-module. Imports inside functions count: they run as soon as the function
    does.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parents = package.split(".")[:len(package.split(".")) - node.level + 1]
                base = ".".join(part for part in (*parents, base) if part)
            found.add(base)
            found.update(f"{base}.{alias.name}" for alias in node.names)
    return found


def is_forbidden(module: str) -> bool:
    """Whether importing a module pulls in Qt or the Qt application."""
    if module.split(".")[0] in QT_MODULES:
        return True
    return any(module == ui or module.startswith(f"{ui}.") for ui in UI_MODULES)


def module_file(module: str) -> Path | None:
    """The file a dotted je_editor module name refers to, if it is a module."""
    base = REPO_ROOT.joinpath(*module.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def package_of(path: Path) -> str:
    """The dotted package a file belongs to."""
    parts = path.relative_to(REPO_ROOT).with_suffix("").parts
    return ".".join(parts[:-1])


def files_imported_by(path: Path) -> set[Path]:
    """The je_editor files importing *path* causes to run, package inits included."""
    files: set[Path] = set()
    for module in imports_in(path.read_text(encoding="utf-8"), package_of(path)):
        if module.split(".")[0] != PACKAGE_ROOT.name:
            continue
        parts = module.split(".")
        for depth in range(2, len(parts) + 1):
            found = module_file(".".join(parts[:depth]))
            if found is not None and found != TOP_LEVEL_INIT:
                files.add(found)
    return files


def reachable_from(start: list[Path]) -> set[Path]:
    """Every je_editor file the start files import, directly or through another."""
    seen: set[Path] = set()
    pending = list(start)
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        pending.extend(files_imported_by(path))
    return seen


def forbidden_imports(path: Path) -> set[str]:
    """
    The imports of a file that pull in Qt or the Qt application.

    ``from PySide6.QtCore import QLocale`` is reported once, as ``PySide6.QtCore``:
    a name beneath a module that is already listed adds nothing.
    """
    modules = imports_in(path.read_text(encoding="utf-8"), package_of(path))
    hits = {module for module in modules if is_forbidden(module)}
    return {
        module for module in hits
        if not any(module.startswith(f"{other}.") for other in hits)
    }


@pytest.fixture(scope="module")
def reachable():
    """Every je_editor file the core package causes to be imported."""
    return reachable_from(sorted(CORE_ROOT.rglob("*.py")))


@pytest.fixture(scope="module")
def probe():
    """The result of building the services in a process that cannot import Qt."""
    # This interpreter running a literal defined above; no shell, and the only
    # arguments are a path and a list of names from this file.
    return subprocess.run(  # nosemgrep  # nosec B603
        [sys.executable, "-c", QT_FREE_PROBE, str(PACKAGE_ROOT), ",".join(sorted(QT_MODULES))],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120, cwd=str(REPO_ROOT), check=False,
    )


class TestTheImportScanner:
    """The guard is only worth having if it sees what it is meant to catch."""

    def test_a_plain_import_is_seen(self):
        assert "PySide6.QtWidgets" in imports_in("import PySide6.QtWidgets\n")

    def test_an_import_inside_a_function_is_seen(self):
        source = "def build():\n    from PySide6.QtWidgets import QWidget\n    return QWidget\n"
        assert "PySide6.QtWidgets" in imports_in(source)

    def test_a_sub_module_named_in_a_from_import_is_seen(self):
        assert "je_editor.pyside_ui" in imports_in("from je_editor import pyside_ui\n")

    def test_a_relative_import_is_resolved(self):
        assert "je_editor.core.uri" in imports_in("from ..uri import x\n", "je_editor.core.workspace")

    @pytest.mark.parametrize("module", [
        "PySide6", "PySide6.QtCore", "qt_material", "qtconsole.rich_jupyter_widget",
        "je_editor.pyside_ui", "je_editor.pyside_ui.main_ui.main_editor", "je_editor.start_editor",
    ])
    def test_qt_and_the_ui_are_forbidden(self, module):
        assert is_forbidden(module)

    @pytest.mark.parametrize("module", [
        "json", "je_editor.utils.lsp.lsp_protocol", "je_editor.core", "PySide6_helper",
        "je_editor.pyside_ui_notes",
    ])
    def test_everything_else_is_allowed(self, module):
        assert not is_forbidden(module)


class TestTheCoreLayerIsQtFree:
    """
    Nothing the core layer imports, however indirectly, is Qt or a widget.

    The core services have to be usable by a host application that never builds
    the JEditor window, and one Qt import anywhere beneath them ends that.
    """

    def test_the_scan_covers_the_core_package(self, reachable):
        assert CORE_ROOT / "services" / "editor_services.py" in reachable

    def test_the_scan_follows_imports_out_of_the_core_package(self, reachable):
        assert PACKAGE_ROOT / "utils" / "lsp" / "lsp_protocol.py" in reachable

    def test_nothing_reachable_imports_qt_or_the_ui(self, reachable):
        offenders = {
            path.relative_to(REPO_ROOT).as_posix(): sorted(forbidden_imports(path))
            for path in reachable if forbidden_imports(path)
        }
        assert offenders == {}


class TestTheLogicPackagesStayBelowTheUi:
    """
    The packages under the UI import neither Qt nor the UI, bar the known cases.

    ``pyside_ui`` depends on them, never the other way round. The two modules
    that already reach upwards are written down so a third cannot slip in.
    """

    def test_only_the_known_modules_reach_upwards(self):
        found = {}
        for package in LOGIC_PACKAGES:
            for path in sorted((PACKAGE_ROOT / package).rglob("*.py")):
                hits = forbidden_imports(path)
                if hits:
                    found[path.relative_to(REPO_ROOT).as_posix()] = hits
        assert found == KNOWN_UPWARD_IMPORTS


class TestTheCoreLayerRunsWithoutQt:
    """
    The service layer is built and used in a process where Qt cannot be imported.

    ``je_editor`` is registered as a bare package first, so its ``__init__`` (the
    Qt application's facade) does not run, and an import hook refuses every Qt
    module. If the probe still builds the services, opens a document and reports
    a diagnostic, the layer really does stand on its own.
    """

    def test_the_probe_runs_to_the_end(self, probe):
        assert probe.returncode == 0, probe.stderr[-2000:]

    def test_the_services_work_and_no_qt_module_was_loaded(self, probe):
        assert probe.stdout.split() == ["1", "1", "1", "[]"]


class TestThePublicNamesOfTheCoreLayer:
    """Every name the core package promises is really there."""

    def test_each_exported_name_exists(self):
        missing = [name for name in core.__all__ if not hasattr(core, name)]
        assert missing == []

    def test_no_name_is_exported_twice(self):
        assert len(core.__all__) == len(set(core.__all__))
