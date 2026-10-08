"""``dev.toml`` describes the same package as ``pyproject.toml`` under another name.

The dev channel (``je_editor_dev``) is built by writing ``dev.toml`` to ``pyproject.toml``, while
the tests run against an install made from ``pyproject.toml``. A dependency, a Python floor or a
packaging rule changed on one side only ships a dev package that differs from what was tested:
``dev.toml`` once pinned an older PySide6 than ``pyproject.toml``. ``MANIFEST.in`` is one file for
both channels and keeps the test suite out of either sdist.
"""
from __future__ import annotations

from pathlib import Path

import pytest

tomllib = pytest.importorskip("tomllib")  # stdlib from 3.11; CI also runs 3.10

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT_TABLES = ("scripts", "gui-scripts", "entry-points")


def _load(name: str) -> dict:
    """Return the parsed TOML file ``name`` from the repository root."""
    with (REPO_ROOT / name).open("rb") as handle:
        return tomllib.load(handle)


STABLE_FILE = _load("pyproject.toml")
DEV_FILE = _load("dev.toml")
STABLE = STABLE_FILE["project"]
DEV = DEV_FILE["project"]


def test_package_names_differ():
    assert STABLE["name"] == "je_editor"
    assert DEV["name"] == "je_editor_dev"


def test_runtime_dependencies_match():
    assert sorted(DEV["dependencies"]) == sorted(STABLE["dependencies"])


def test_python_floor_matches():
    assert DEV["requires-python"] == STABLE["requires-python"]


def test_optional_dependency_groups_match():
    assert DEV.get("optional-dependencies", {}) == STABLE.get("optional-dependencies", {})


@pytest.mark.parametrize("table", ENTRY_POINT_TABLES)
def test_entry_points_match(table):
    assert DEV.get(table, {}) == STABLE.get(table, {})


def test_only_the_package_is_shipped():
    # 沒有 include 的話，setuptools 會把有 __init__.py 的 test/ 也當成頂層套件收進 wheel。
    # Without include, setuptools also packages test/ (it has an __init__.py) as a top-level package.
    find = STABLE_FILE["tool"]["setuptools"]["packages"]["find"]
    assert find["include"] == ["je_editor", "je_editor.*"]


def test_shipped_files_match():
    # Package discovery and package data decide which files reach the wheel.
    assert DEV_FILE["tool"]["setuptools"] == STABLE_FILE["tool"]["setuptools"]


def test_the_lint_rules_are_named():
    # ruff's defaults change between releases (118 rules in 0.15, 826 in 0.16), so "ruff check
    # clean" only means something while the rule set is written down.
    assert STABLE_FILE["tool"]["ruff"]["lint"]["select"] == ["E4", "E7", "E9", "F"]


def test_lint_rules_match():
    assert DEV_FILE["tool"]["ruff"] == STABLE_FILE["tool"]["ruff"]


def _manifest_commands() -> list[list[str]]:
    """Return the words of each ``MANIFEST.in`` command, comments and blank lines left out."""
    lines = (REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8").splitlines()
    return [line.split() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def test_the_sdist_leaves_the_tests_out():
    # include 只管 wheel；setuptools 預設仍把 test*/test*.py 收進 sdist，要靠 MANIFEST.in 的 prune 拿掉。
    # 指令依序執行，所以 prune 必須是最後一條，後面的 include 或 graft 會把 test/ 加回來。
    # include only governs the wheel; setuptools still adds test*/test*.py to an sdist by default, and
    # the prune in MANIFEST.in takes it out. Commands run in order, so prune has to be the last one:
    # an include or graft after it would bring test/ back.
    assert _manifest_commands()[-1] == ["prune", Path(__file__).resolve().parent.name]
