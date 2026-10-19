"""Shared setup for every test.

All tests run with LLM_PROVIDER=offline, so no test ever calls a real language
model or uses up a free-tier limit. The speech models are not preloaded; tests
that need them are marked slow and skipped unless you run: python -m pytest -m slow

Add --save-report to any run to also write a summary of it to tests/results/.
"""
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "tests" / "results"
sys.path.insert(0, str(ROOT))

# Set before any project module is imported, so .env cannot override them.
os.environ["LLM_PROVIDER"] = "offline"
os.environ["PRELOAD_MODELS"] = "0"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """The FastAPI app, with its request log written to a temporary folder instead of logs/."""
    from fastapi.testclient import TestClient

    from app import server
    from pipeline import config

    monkeypatch.setattr(config, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(server, "LOG_PATH", tmp_path / "qa_log.jsonl")
    return TestClient(server.app)


# ---------------------------------------------------------------- test report

_run = {"start": 0.0, "results": {}, "not_run": [], "saved": None}


def pytest_addoption(parser):
    parser.addoption("--save-report", action="store_true", default=False,
                     help="also save a summary of this run to tests/results/")


def pytest_sessionstart(session):
    _run["start"] = time.time()


def pytest_deselected(items):
    _run["not_run"].extend(item.nodeid for item in items)


def pytest_runtest_logreport(report):
    # Keep the call phase, or the setup phase when the test never got to run.
    if report.when == "call" or (report.when == "setup" and not report.passed):
        outcome = "error" if report.when == "setup" and report.failed else report.outcome
        _run["results"][report.nodeid] = (outcome, report.duration)
    elif report.when == "teardown" and report.failed:
        _run["results"][report.nodeid] = ("error", report.duration)


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _split(nodeid):
    path, _, name = nodeid.partition("::")
    return name, Path(path).name


def pytest_sessionfinish(session, exitstatus):
    if not session.config.getoption("--save-report"):
        return
    now = datetime.now().astimezone()
    offset = now.strftime("%z")
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    changed = [line for line in _git("status", "--porcelain").splitlines() if "tests/results/" not in line]
    args = " ".join(f'"{a}"' if " " in a else a for a in session.config.invocation_params.args)

    results = _run["results"]
    counts = {}
    for outcome, _ in results.values():
        counts[outcome] = counts.get(outcome, 0) + 1
    summary = ", ".join(f"{n} {outcome}" for outcome, n in sorted(counts.items()))
    if _run["not_run"]:
        summary += f", {len(_run['not_run'])} not run"
    failing = counts.get("failed", 0) + counts.get("error", 0)

    lines = [
        "# Test report",
        "",
        f"- Run: {now:%Y-%m-%d %H:%M} (UTC{offset[:3]}:{offset[3:]})",
        f"- Code tested: commit {commit} on branch {branch}, "
        + ("with uncommitted changes" if changed else "no uncommitted changes"),
        f"- Command: python -m pytest {args}",
        f"- Python {platform.python_version()} on {platform.system()}",
        f"- Result: {summary} in {time.time() - _run['start']:.1f} s",
        f"- {'All tests that ran passed.' if not failing else f'{failing} test(s) failed.'}",
        "",
        "| Test | File | Result | Time (s) |",
        "|---|---|---|---|",
    ]
    for nodeid, (outcome, duration) in results.items():
        name, file = _split(nodeid)
        lines.append(f"| {name} | {file} | {outcome} | {duration:.2f} |")
    if _run["not_run"]:
        lines += ["", "Not run (left out by the -m option):", ""]
        lines += [f"- {name} ({file})" for name, file in map(_split, _run["not_run"])]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_branch = re.sub(r"[^A-Za-z0-9-]+", "-", branch).strip("-") or commit
    path = RESULTS_DIR / f"{now:%Y-%m-%d}_{safe_branch}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _run["saved"] = path


def pytest_terminal_summary(terminalreporter):
    if _run["saved"]:
        terminalreporter.write_line(f"Test report saved to {_run['saved'].relative_to(ROOT).as_posix()}")
