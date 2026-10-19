"""Tests for the paired persona vs plain guide comparison (eval/compare_modes.py)."""
import json
import random

import pytest

from eval import compare_modes as cm


def rows_for(results, exhibit="t-rex"):
    """Answer rows like eval_answers.py writes, from {question_id: (persona_right, guide_right)}."""
    rows = []
    for qid, (persona, guide) in results.items():
        for mode, right in (("persona", persona), ("neutral", guide)):
            rows.append({"exhibit": exhibit, "question_id": qid, "question": f"Question {qid}?",
                         "mode": mode, "grounded": right, "status": "answered"})
    return rows


SAMPLE = {"q1": (True, True), "q2": (True, False), "q3": (False, True), "q4": (False, True), "q5": (False, False)}


def test_counts_the_four_outcomes():
    s = cm.summarize(cm.pair_results(rows_for(SAMPLE)))
    assert s["outcomes"] == {"both correct": 1, "persona only": 1, "plain guide only": 2, "both wrong": 1}
    assert (s["persona_correct"], s["plain_guide_correct"]) == (2, 3)
    assert (s["persona_accuracy"], s["plain_guide_accuracy"]) == (0.4, 0.6)
    assert s["difference_points"] == -20.0
    assert s["discordant"] == 3


def test_pairs_by_question_id_not_row_order():
    rows = rows_for(SAMPLE)
    shuffled = rows[:]
    random.Random(7).shuffle(shuffled)
    assert cm.summarize(cm.pair_results(shuffled)) == cm.summarize(cm.pair_results(rows))


def test_same_question_id_in_two_exhibits_stays_separate():
    pairs = cm.pair_results(rows_for({"q1": (True, False)}) + rows_for({"q1": (False, True)}, exhibit="van-gogh"))
    assert pairs[("t-rex", "q1")]["persona"] is True
    assert pairs[("van-gogh", "q1")]["persona"] is False


@pytest.mark.parametrize("b, c, expected", [
    (0, 0, 1.0),
    (1, 2, 1.0),
    (0, 6, 0.03125),
    (2, 8, 0.109375),
    (5, 5, 1.0),
])
def test_exact_mcnemar_p_values(b, c, expected):
    assert cm.exact_mcnemar(b, c) == pytest.approx(expected)


def test_no_discordant_pairs_does_not_crash():
    s = cm.summarize(cm.pair_results(rows_for({"q1": (True, True), "q2": (False, False)})))
    assert s["discordant"] == 0
    assert s["mcnemar_exact_p"] == 1.0
    assert "no difference to test" in s["conclusion"]


def test_small_sample_is_called_too_small():
    s = cm.summarize(cm.pair_results(rows_for(SAMPLE)))
    assert s["smallest_possible_p"] == 0.25
    assert "too small" in s["conclusion"]


def test_clear_win_is_reported_with_its_p_value():
    s = cm.summarize(cm.pair_results(rows_for({f"q{i}": (True, False) for i in range(7)})))
    assert s["mcnemar_exact_p"] == pytest.approx(0.0156, abs=1e-4)
    assert s["conclusion"].startswith("The persona was right on 7 of the 7")


def test_duplicate_result_is_rejected():
    rows = rows_for(SAMPLE)
    with pytest.raises(ValueError, match="t-rex/q1: two persona results"):
        cm.pair_results(rows + [rows[0]])


def test_missing_mode_is_rejected():
    rows = [r for r in rows_for(SAMPLE) if not (r["question_id"] == "q2" and r["mode"] == "neutral")]
    with pytest.raises(ValueError, match="t-rex/q2: no plain guide result"):
        cm.pair_results(rows)


def test_failed_call_is_rejected():
    rows = rows_for(SAMPLE)
    rows[0] = dict(rows[0], status="error")
    with pytest.raises(ValueError, match="persona call failed"):
        cm.pair_results(rows)


def test_writes_json_and_markdown(tmp_path):
    results = tmp_path / "answers_results.json"
    results.write_text(json.dumps({"run_at": "today", "model": "test-model", "passages_per_question": 8,
                                   "answers": rows_for(SAMPLE)}), encoding="utf-8")
    json_path, md_path = cm.write_outputs(cm.compare(results), tmp_path)
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved["overall"]["questions"] == 5
    assert len(saved["questions"]) == 5
    markdown = md_path.read_text(encoding="utf-8")
    assert "| All | 5 |" in markdown
    assert "q2: Question q2?" in markdown


def test_saved_answer_results_pair_cleanly():
    data = json.loads((cm.RESULTS_DIR / "answers_results.json").read_text(encoding="utf-8"))
    pairs = cm.pair_results(data["answers"])
    assert len(pairs) == len({(r["exhibit"], r["question_id"]) for r in data["answers"]})
