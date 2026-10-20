"""The before/after search report (eval/compare_retrieval.py)."""
import pytest

from eval.compare_retrieval import compare_set


def _run(ranks):
    questions = [{"id": qid, "question": f"q {qid}", "first_hit_rank": r} for qid, r in ranks.items()]
    summary = {"questions": len(questions), "hit@1": 0.5, "hit@5": 0.5, "hit@8": 0.5, "recall@5": 0.5, "mrr@10": 0.5}
    return {"exhibits": {"t-rex": {"summary": summary, "questions": questions}}}


def test_regressions_and_improvements_are_reported():
    lines, regressions = compare_set("Main", _run({"a": 1, "b": 3, "c": None}), _run({"a": 4, "b": 1, "c": None}))
    text = "\n".join(lines)
    assert regressions == 1
    assert "| a | q a | 1 | 4 | **regression** |" in text
    assert "| b | q b | 3 | 1 | better |" in text
    assert "| c |" not in text  # unchanged miss is not listed


def test_dropping_out_of_the_top_10_is_a_regression():
    _, regressions = compare_set("Main", _run({"a": 6}), _run({"a": None}))
    assert regressions == 1


def test_different_question_sets_are_refused():
    with pytest.raises(ValueError, match="same questions"):
        compare_set("Main", _run({"a": 1}), _run({"b": 1}))
