"""Every GitHub Actions step pins its action to a commit SHA.

A tag such as ``@v4`` can be moved to new code at any time (the 2025
tj-actions/changed-files compromise rewrote tags), so each ``uses:`` names a
full 40-hex commit and carries the release it corresponds to as a comment,
which is what Dependabot reads and updates. Pinning also keeps Node 20 actions
from lingering unnoticed: GitHub removed Node 20 from its runners on 2026-09-23.

The jobs that hold the PyPI token get the same treatment for their Python tools:
they install only ``.github/requirements/publish.txt``, pinned by version and hash,
and build without isolation so that the build backend is the locked one too.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
# packaging 隨 pytest 安裝；build 在 --no-isolation 下也是用它檢查 build-system.requires。
# packaging is installed with pytest, and is what build itself checks build-system.requires with
# under --no-isolation.
from packaging.requirements import Requirement

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".github" / "workflows").is_dir())
_WORKFLOWS = sorted((_ROOT / ".github" / "workflows").glob("*.yml"))
_USES = re.compile(r"^\s*(?:-\s*)?uses:\s*(\S+)(.*)$")
_PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")
_LOCAL = re.compile(r"^\./")
_VERSION_COMMENT = re.compile(r"^\s+#\s*v\d+(\.\d+)*\s*$")


def _uses(path: Path) -> list[tuple[int, str, str]]:
    """Return ``(line number, action reference, rest of line)`` for each remote ``uses:``."""
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = _USES.match(line)
        if match and not _LOCAL.match(match.group(1)):
            found.append((number, match.group(1), match.group(2)))
    return found


def test_workflows_exist():
    assert _WORKFLOWS


@pytest.mark.parametrize("workflow", _WORKFLOWS, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_commit_with_its_version(workflow):
    bad = [f"{workflow.name}:{number} {ref}{rest}"
           for number, ref, rest in _uses(workflow)
           if not (_PINNED.match(ref) and _VERSION_COMMENT.match(rest))]
    assert bad == []


def test_one_version_per_action():
    # The same action at two different commits means a partial upgrade.
    seen: dict[str, set[str]] = {}
    for workflow in _WORKFLOWS:
        for _number, ref, _rest in _uses(workflow):
            action, _, sha = ref.partition("@")
            seen.setdefault(action, set()).add(sha)
    assert {action: shas for action, shas in seen.items() if len(shas) > 1} == {}


def test_dependabot_keeps_pins_current_on_dev():
    # Pinned SHAs only stay current if something bumps them; every update
    # goes to dev because main is the release branch. Parsed as text: PyYAML
    # is not a test dependency.
    text = (_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    blocks = re.split(r"^\s*-\s*package-ecosystem:", text, flags=re.MULTILINE)[1:]
    ecosystems = {block.split()[0].strip("\"'") for block in blocks}
    assert {"pip", "github-actions"} <= ecosystems
    assert all(re.search(r"^\s*target-branch:\s*\"dev\"", block, re.MULTILINE)
               for block in blocks)
    # 發佈工作的鎖定檔不在根目錄，pip 那一項只寫 "/" 的話沒有人會更新它。
    # The publish jobs' lock is not in the root, so a pip entry that names only "/" leaves it to go stale.
    pip = next(block for block in blocks if block.split()[0].strip("\"'") == "pip")
    assert re.search(r'^\s*-\s*"/\.github/requirements"\s*$', pip, re.MULTILINE)


def test_dependabot_waits_a_week_before_proposing_a_release():
    # A compromised release is usually found and yanked within days. Dependabot's
    # own default wait is 3 days, and zizmor's dependabot-cooldown audit asks
    # for 7. The wait never delays security updates.
    text = (_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    blocks = re.split(r"^\s*-\s*package-ecosystem:", text, flags=re.MULTILINE)[1:]
    days = [re.search(r"^\s*default-days:\s*(\d+)", block, re.MULTILINE) for block in blocks]
    assert blocks and all(match and int(match.group(1)) >= 7 for match in days)


def _checkout_steps(path: Path) -> list[tuple[int, str]]:
    """Return ``(line number, step text)`` for each ``actions/checkout`` step."""
    lines = path.read_text(encoding="utf-8").splitlines()
    steps = []
    for index, line in enumerate(lines):
        if not re.search(r"uses:\s*actions/checkout@", line):
            continue
        column = line.index("uses:")
        body = [line]
        for following in lines[index + 1:]:
            indent = len(following) - len(following.lstrip())
            if following.strip() and (indent < column or following.lstrip().startswith("- ")):
                break
            body.append(following)
        steps.append((index + 1, "\n".join(body)))
    return steps


@pytest.mark.parametrize("workflow", _WORKFLOWS, ids=lambda p: p.name)
def test_every_checkout_decides_on_persisted_credentials(workflow):
    # actions/checkout leaves the job token in .git/config unless told not
    # to, where every later step (and any uploaded workspace) can read it.
    # Only jobs that push keep it, and they say so.
    bad = [f"{workflow.name}:{number}" for number, step in _checkout_steps(workflow)
           if not re.search(r"^\s*persist-credentials:\s*(true|false)\b", step, re.MULTILINE)]
    assert bad == []


_JOB_HEAD = re.compile(r"^  [A-Za-z0-9_-]+:\s*(#.*)?$")


def _jobs(path: Path) -> list[tuple[str, str]]:
    """Return ``(job id, job text)`` for each job under ``jobs:`` in a workflow."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(r"^jobs:\s*(#.*)?$", line))
    heads = [i for i in range(start + 1, len(lines)) if _JOB_HEAD.match(lines[i])]
    ends = [*heads[1:], len(lines)]
    return [(lines[i].strip().rstrip(":"), "\n".join(lines[i:end])) for i, end in zip(heads, ends)]


@pytest.mark.parametrize("workflow", _WORKFLOWS, ids=lambda p: p.name)
def test_every_job_has_a_timeout(workflow):
    # Without timeout-minutes a hung job runs for GitHub's default six hours.
    # Each job sets about three times its slowest recent run, at least 15 minutes.
    bad = [name for name, body in _jobs(workflow)
           if "runs-on:" in body and not re.search(r"^\s*timeout-minutes:", body, re.MULTILINE)]
    assert bad == []


_REQUIREMENTS = _ROOT / ".github" / "requirements"
# 用到這個密鑰的工作就是發佈工作
# A job that reads this secret is a publish job.
_PUBLISH_MARKER = "secrets.PYPI_API_TOKEN"
_LOCKED_INSTALL = ("python -m pip install --require-hashes --only-binary :all: "
                   "-r .github/requirements/publish.txt")
_PIP_INSTALL = re.compile(r"\bpipx?\d*\s+install\b")
_BUILD = re.compile(r"-m build\b")
_NO_ISOLATION = "--no-isolation"
# 發佈工作可能拿來建置的中繼資料：stable.yml 用 pyproject.toml，publish-dev 把 dev.toml 寫成 pyproject.toml。
# The metadata a publish job can build from: stable.yml uses pyproject.toml, and publish-dev writes
# dev.toml over pyproject.toml.
_METADATA_FILES = ("pyproject.toml", "dev.toml")
_DISTRIBUTION = re.compile(r"[A-Za-z0-9._-]+")
_PINNED_LINE = re.compile(r"^[A-Za-z0-9._-]+==\S+ \\$")
_PUBLISH_JOBS = {f"{workflow.name}:{name}": body for workflow in _WORKFLOWS
                 for name, body in _jobs(workflow) if _PUBLISH_MARKER in body}


def _commands(job: str) -> list[str]:
    """Return each line of a job's text with its comment and indentation removed."""
    return [line.split("#", 1)[0].strip() for line in job.splitlines()]


def _pip_installs(job: str) -> list[str]:
    """Return each line of a job's text that runs ``pip install``, comments left out."""
    return [line for line in _commands(job) if _PIP_INSTALL.search(line)]


def _builds(job: str) -> list[str]:
    """Return each line of a job's text that runs ``python -m build``, comments left out."""
    return [line for line in _commands(job) if _BUILD.search(line)]


def _locked_blocks() -> list[str]:
    """Return ``publish.txt`` cut into one block per requirement: the pin line and its hash lines."""
    text = (_REQUIREMENTS / "publish.txt").read_text(encoding="utf-8")
    return re.split(r"^(?=[^\s#])", text, flags=re.MULTILINE)[1:]


def _canonical(name: str) -> str:
    """Return the PEP 503 form of a distribution name (``tomli_w`` and ``tomli-w`` are one)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _distributions(requirements: list[str]) -> set[str]:
    """Return the PEP 503 name each requirement starts with."""
    return {_canonical(_DISTRIBUTION.match(requirement).group()) for requirement in requirements}


def _locked_versions() -> dict[str, str]:
    """Return the version ``publish.txt`` pins for each distribution, keyed by PEP 503 name."""
    pins = (block.splitlines()[0].rstrip(" \\").split("==", 1) for block in _locked_blocks())
    return {_canonical(name): version for name, version in pins}


def _unmet_by_the_lock(requirement: str) -> bool:
    """Return whether ``publish.txt`` has no pin that satisfies a ``build-system.requires`` entry."""
    wanted = Requirement(requirement)
    locked = _locked_versions().get(_canonical(wanted.name))
    return locked is None or not wanted.specifier.contains(locked, prereleases=True)


def test_the_publish_jobs_are_the_two_that_hold_the_pypi_token():
    # 下面的測試以這份清單為對象；找不到工作的話它們會沒有東西可查而直接通過。
    # The tests below run over this list; with no job found they would pass with nothing to check.
    assert sorted(_PUBLISH_JOBS) == ["dev.yml:publish-dev", "stable.yml:publish_to_pypi"]


@pytest.mark.parametrize("job", list(_PUBLISH_JOBS.values()), ids=list(_PUBLISH_JOBS))
def test_a_job_holding_the_pypi_token_installs_only_the_locked_tooling(job):
    # 沒鎖版本的 pip install（升級 pip 也算）會讓 PyPI 上當天最新的套件在上傳前、token 在手時執行。
    # 指令要自己佔一行（`run: |` 底下）：跟 `run:` 寫在同一行的話，`:all: ` 的冒號加空白是 YAML 語法錯誤。
    # An unpinned pip install, upgrading pip included, runs whatever is newest on PyPI that day in the
    # job that is about to upload with the token. The command has a line to itself under `run: |`:
    # on the same line as `run:`, the colon and space of `:all: ` are a YAML syntax error.
    assert _pip_installs(job) == [_LOCKED_INSTALL]


def test_every_locked_requirement_has_a_version_and_a_hash():
    # --require-hashes 遇到沒有雜湊的需求會讓發佈工作在安裝時失敗；在這裡先擋下來。
    # --require-hashes fails the publish job at install time on a requirement without a hash; catch it here.
    blocks = _locked_blocks()
    bad = [block.splitlines()[0] for block in blocks
           if not (_PINNED_LINE.match(block.splitlines()[0]) and "--hash=sha256:" in block)]
    assert blocks and bad == []


def test_the_lock_holds_every_tool_the_publish_jobs_ask_for():
    # publish.in 加了工具卻沒有重新產生 publish.txt，工作就裝不到它。
    # A tool added to publish.in without regenerating publish.txt is not installed by the jobs.
    lines = (_REQUIREMENTS / "publish.in").read_text(encoding="utf-8").splitlines()
    asked = _distributions([line for line in lines if line.strip() and not line.startswith("#")])
    assert asked and asked <= _distributions(_locked_blocks())


@pytest.mark.parametrize("job", list(_PUBLISH_JOBS.values()), ids=list(_PUBLISH_JOBS))
def test_a_job_holding_the_pypi_token_builds_with_the_locked_backend(job):
    # 隔離建置會另開環境，下載當下 PyPI 上最新的 setuptools 來執行；那一份不在鎖定檔裡，而 token 就在這個工作手上。
    # An isolated build makes its own environment and runs whatever setuptools is newest on PyPI at
    # that moment: outside the lock, in the job that holds the token.
    builds = _builds(job)
    assert builds and all(_NO_ISOLATION in command.split() for command in builds)


@pytest.mark.parametrize("metadata", _METADATA_FILES)
def test_the_lock_satisfies_build_system_requires(metadata):
    # --no-isolation 只檢查 build-system.requires、不安裝；下限被調高（Dependabot 會改這些檔）卻沒有
    # 重新產生鎖定檔的話，要在這裡失敗，而不是等到發佈工作建置時才失敗。
    # --no-isolation checks build-system.requires instead of installing it, so a floor raised without
    # regenerating the lock (Dependabot edits these files) has to fail here, not in the publish job.
    tomllib = pytest.importorskip("tomllib")  # stdlib from 3.11; CI also runs 3.10
    with (_ROOT / metadata).open("rb") as handle:
        requires = tomllib.load(handle)["build-system"]["requires"]
    assert requires and [item for item in requires if _unmet_by_the_lock(item)] == []
