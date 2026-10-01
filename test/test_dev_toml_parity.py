"""``dev.toml`` describes the same package as ``pyproject.toml`` under another name.

The dev channel (``je_editor_dev``) is built by writing ``dev.toml`` to ``pyproject.toml``, while
the tests run against an install made from ``pyproject.toml``. A dependency, a Python floor or a
packaging rule changed on one side only ships a dev package that differs from what was tested:
``dev.toml`` once pinned an older PySide6 than ``pyproject.toml``.
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
