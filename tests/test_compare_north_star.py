"""Tests for the North Star comparison across sessions (scripts/compare_north_star.py)."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compare_north_star", ROOT / "scripts" / "compare_north_star.py")
cns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cns)


def row(exhibit, mode, qid, status, grounded, answerable=True, citations=("c1",)):
    return {"exhibit": exhibit, "mode": mode, "question_id": qid, "status": status, "grounded": grounded,
            "correct": grounded, "answerable": answerable, "citations": list(citations)}


def write_run(path, rows, model="openai/gpt-oss-120b"):
    path.write_text(json.dumps({"run_at": "2026-11-10T00:00:00+00:00", "model": model, "answers": rows}))
    return path


def test_cell_counts_accuracy_citations_and_declines():
    rows = [row("t-rex", "persona", "q1", "answered", True, citations=("a", "b")),
            row("t-rex", "persona", "q2", "answered", False, citations=()),
            row("t-rex", "persona", "q3", "not_in_sources", True, answerable=False, citations=()),
            row("t-rex", "persona", "q4", "error", False, citations=())]
    c = cns.cell_from_rows(rows)
    assert (c["correct"], c["questions"]) == (2, 4)
    assert c["citations"] == 1.0          # (2 + 0) / 2 answered replies; errors and declines not counted
    assert c["decline_rate"] == 0.25
    assert (c["traps_declined"], c["traps"]) == (1, 1)
    assert c["errors"] == 1


def test_persona_only_run_skips_the_neutral_rows(tmp_path):
    rows = [row(e, "persona", f"{e}-1", "answered", True) for e in cns.EXHIBITS]
    run = cns.load_run(write_run(tmp_path / "s10.json", rows), "Session 10")
    text = cns.table([run])
    assert "| persona | all | 1.000 (2/2)" in text
    assert "neutral" not in text


def test_session7_has_no_citation_or_decline_numbers():
    vg = cns.SESSION7["cells"][("van-gogh", "persona")]
    tr = cns.SESSION7["cells"][("t-rex", "persona")]
    assert vg["correct"] + tr["correct"] == 59
    assert cns.combine([vg, tr])["citations"] is None
    assert "| - | - |" in cns.table([cns.SESSION7])


def test_frontmatter_names_both_models(tmp_path):
    rows = [row(e, "persona", f"{e}-{i}", "answered", i < 30) for e in cns.EXHIBITS for i in range(32)]
    s10 = cns.load_run(write_run(tmp_path / "s10.json", rows), "Session 10")
    block = cns.frontmatter(s10, cns.SESSION7)
    assert "(60 of 64 overall), model openai/gpt-oss-120b" in block
    assert "previous: Van Gogh 0.969, T. rex 0.875 (59 of 64 overall)" in block
