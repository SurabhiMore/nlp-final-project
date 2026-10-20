"""Answer generation: grounding, citation checks and model replies that go wrong (issue #28).

No model is called. Each test hands answer() a made-up model reply and the passages that
search gave for a real held-out question, frozen in eval/fixtures/frozen_passages.json, so
these tests do not change when search changes.
"""
import json

import pytest

from eval import eval_grounding
from pipeline import config, persona as engine

FROZEN = eval_grounding.load_frozen()


def frozen(exhibit, question_id):
    item = next(i for i in FROZEN["exhibits"][exhibit] if i["question"]["id"] == question_id)
    return item["question"], item["passages"], item["support_ids"]


@pytest.fixture
def model_says(monkeypatch):
    """Make answer() go through the real model path, with the model's reply made up by the test."""
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_BASE_URL", "http://model.invalid/v1")
    monkeypatch.setenv("LLM_MODEL", "made-up-model")

    def set_reply(reply):
        monkeypatch.setattr(engine, "_call_llm", lambda messages, s: reply)
    return set_reply


def reply(answer, status="answered", citations=()):
    return json.dumps({"answer": answer, "status": status, "citations": list(citations)})


def assert_safe(result, passages):
    """What every answer must satisfy, whatever the model sent."""
    assert result["status"] in engine.STATUSES
    assert result["answer"].strip()
    assert not result["answer"].lstrip().startswith(("{", "["))
    assert set(result["citations"]) <= {p["id"] for p in passages}
    if result["status"] == "answered":
        assert result["citations"] or result.get("sound")


# ---------------------------------------------------------------- supported question

def test_supported_answer_keeps_its_citation(model_says):
    q, passages, support = frozen("van-gogh", "vg-04")  # When did you arrive in Arles?
    cited = next(p["id"] for p in passages if p["id"] in support)
    model_says(reply("I arrived in Arles in February 1888.", citations=[cited]))
    result = engine.answer("van-gogh", q["question"], passages)
    assert result["status"] == "answered"
    assert result["citations"] == [cited]
    assert result["answer"] == "I arrived in Arles in February 1888."
    assert result["check"] is None
    assert_safe(result, passages)


# ---------------------------------------------------------------- related question, no evidence

def test_honest_not_in_sources_is_kept_as_written(model_says):
    q, passages, _ = frozen("van-gogh", "vg-20")  # What was the name of your childhood dog?
    model_says(reply("I have no record of a childhood dog in my letters.", "not_in_sources"))
    result = engine.answer("van-gogh", q["question"], passages)
    assert (result["status"], result["check"]) == ("not_in_sources", None)
    assert result["answer"] == "I have no record of a childhood dog in my letters."


@pytest.mark.parametrize("exhibit, question_id, leaked", [
    ("t-rex", "tr-03", 'The word "rex" is Latin for "king", so my name means "tyrant lizard king".'),
    ("van-gogh", "vg-03", "My brother Theo worked as an art dealer in Paris."),
], ids=["rex-means-king", "theo-art-dealer"])
def test_decline_that_answers_from_model_knowledge_is_replaced(model_says, exhibit, question_id, leaked):
    # Both are real replies from the 2026-09-29 evaluation: status not_in_sources, no citation,
    # but the text states the answer from the model's own knowledge.
    q, passages, _ = frozen(exhibit, question_id)
    model_says(reply(leaked, "not_in_sources"))
    result = engine.answer(exhibit, q["question"], passages)
    assert result["status"] == "not_in_sources"
    assert result["check"] == "decline_that_answers"
    assert result["answer"] != leaked
    assert "king" not in result["answer"] and "dealer" not in result["answer"]
    assert_safe(result, passages)


def test_answer_with_no_citation_becomes_not_in_sources(model_says):
    q, passages, _ = frozen("t-rex", "tr-31")  # How many weeks did it take for your eggs to hatch?
    model_says(reply("My eggs took about twelve weeks to hatch."))
    result = engine.answer("t-rex", q["question"], passages)
    assert (result["status"], result["check"]) == ("not_in_sources", "uncited_answer")
    assert "twelve" not in result["answer"]


# ---------------------------------------------------------------- off-topic question

def test_off_topic_decline_is_kept_as_written(model_says):
    q, passages, _ = frozen("t-rex", "tr-21")  # What is the capital of France?
    text = "I'm a dinosaur, not a guide to modern geography, so I can't answer that."
    model_says(reply(text, "declined"))
    result = engine.answer("t-rex", q["question"], passages)
    assert (result["status"], result["answer"], result["check"]) == ("declined", text, None)


def test_off_topic_decline_that_does_not_say_no_gets_a_clear_line(model_says):
    # Real neutral reply from 2026-09-29; the hand check noted it should say more clearly it is off topic.
    q, passages, _ = frozen("t-rex", "tr-21")
    model_says(reply("I'm the museum's guide for Tyrannosaurus rex, here to answer questions about that dinosaur.",
                     "declined"))
    result = engine.answer("t-rex", q["question"], passages, mode="neutral")
    assert result["status"] == "declined"
    assert result["answer"] == "I can only answer questions about Tyrannosaurus rex and the museum."


def test_off_topic_answer_from_model_knowledge_is_not_shown(model_says):
    q, passages, _ = frozen("t-rex", "tr-21")
    model_says(reply("The capital of France is Paris."))
    result = engine.answer("t-rex", q["question"], passages)
    assert result["status"] in engine.DECLINED_STATUSES
    assert "Paris" not in result["answer"]


# ---------------------------------------------------------------- invalid source ids

def test_invalid_citation_is_removed_and_valid_one_kept(model_says):
    q, passages, support = frozen("van-gogh", "vg-04")
    valid = next(p["id"] for p in passages if p["id"] in support)
    model_says(reply("I arrived in Arles in February 1888.", citations=["van-gogh-wiki-9999", valid, f"[{valid}]"]))
    result = engine.answer("van-gogh", q["question"], passages)
    assert result["citations"] == [valid]
    assert result["invalid_citations"] == ["van-gogh-wiki-9999"]
    assert result["status"] == "answered"


def test_citing_a_real_passage_that_was_not_supplied_is_rejected(model_says):
    # The id exists in the corpus, but it was not among the passages given for this question.
    q, passages, _ = frozen("van-gogh", "vg-04")
    supplied = {p["id"] for p in passages}
    elsewhere = next(c["id"] for c in map(json.loads, config.chunks_path("van-gogh").read_text("utf-8").splitlines())
                     if c["id"] not in supplied)
    model_says(reply("I arrived in Arles in February 1888.", citations=[elsewhere]))
    result = engine.answer("van-gogh", q["question"], passages)
    assert result["citations"] == []
    assert result["invalid_citations"] == [elsewhere]
    assert (result["status"], result["check"]) == ("not_in_sources", "uncited_answer")


# ---------------------------------------------------------------- malformed model output

MALFORMED = {
    "not-json": "Sure! I arrived in Arles in February 1888.",
    "cut-off": '{"answer": "I arrived in Arles in Feb',
    "empty-object": "{}",
    "null-answer": '{"answer": null, "status": "answered", "citations": []}',
    "answer-is-object": '{"answer": {"text": "1888"}, "status": "answered", "citations": []}',
    "citations-is-number": '{"answer": "I arrived in 1888.", "status": "answered", "citations": 5}',
    "citations-is-object": '{"answer": "I arrived in 1888.", "status": "answered", "citations": {"id": "x"}}',
    "status-is-number": '{"answer": "I arrived in 1888.", "status": 3, "citations": []}',
    "top-level-list": '[{"answer": "I arrived in 1888."}]',
    "sound-is-number": '{"answer": "Here I go!", "status": "answered", "citations": [], "sound": 7}',
    "whitespace": "   ",
}


@pytest.mark.parametrize("raw", MALFORMED.values(), ids=MALFORMED.keys())
def test_malformed_reply_never_crashes_and_never_shows_raw_output(model_says, raw):
    q, passages, _ = frozen("van-gogh", "vg-04")
    model_says(raw)
    result = engine.answer("van-gogh", q["question"], passages)
    assert_safe(result, passages)
    assert result["answer"] != raw.strip()


@pytest.mark.parametrize("raw", MALFORMED.values(), ids=MALFORMED.keys())
def test_parse_reply_never_raises(raw):
    result = engine.parse_reply(raw, {"van-gogh-wiki-0026"})
    assert set(result) >= {"answer", "status", "citations", "invalid_citations", "sound"}


def test_json_wrapped_in_extra_text_is_still_read(model_says):
    q, passages, support = frozen("van-gogh", "vg-04")
    valid = next(p["id"] for p in passages if p["id"] in support)
    model_says("Here is my reply:\n" + reply("I arrived in Arles in February 1888.", citations=[valid]) + "\nThanks!")
    result = engine.answer("van-gogh", q["question"], passages)
    assert (result["status"], result["citations"], result["check"]) == ("answered", [valid], None)


# ---------------------------------------------------------------- answers that need no citation

@pytest.mark.parametrize("question", ["Hello!", "Who are you?", "Are you real?"])
def test_introduction_without_citation_is_still_answered(model_says, question):
    _, passages, _ = frozen("van-gogh", "vg-04")
    model_says(reply("I am Vincent van Gogh, a Dutch painter."))
    result = engine.answer("van-gogh", question, passages)
    assert (result["status"], result["check"]) == ("answered", None)


def test_roar_request_without_citation_keeps_the_sound(model_says):
    _, passages, _ = frozen("t-rex", "tr-01")
    model_says(json.dumps({"answer": "Cover your ears!", "status": "answered", "citations": [], "sound": "roar"}))
    result = engine.answer("t-rex", "Can you roar for me?", passages)
    assert (result["status"], result["sound"], result["check"]) == ("answered", "roar", None)


# ---------------------------------------------------------------- the API contract

def test_ask_returns_the_same_fields_when_the_model_reply_is_broken(client, model_says):
    model_says('{"answer": "I arrived in Arles in Feb')
    response = client.post("/ask", data={"persona": "van-gogh", "text": "When did you arrive in Arles?"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"request_id", "persona", "mode", "question", "status", "answer", "sentences",
                         "citations", "sound", "audio", "timings"}
    assert body["status"] == "not_in_sources"
    assert body["citations"] == []


# ---------------------------------------------------------------- the before and after evaluation

def test_frozen_passages_cover_both_exhibits():
    assert set(FROZEN["exhibits"]) == {"t-rex", "van-gogh"}
    for items in FROZEN["exhibits"].values():
        for item in items:
            assert len(item["passages"]) == FROZEN["passages_per_question"]


def test_evaluation_scores_the_same_reply_before_and_after():
    q, _, _ = frozen("van-gogh", "vg-03")
    replies = {("van-gogh", "persona", "vg-03"): {
        "exhibit": "van-gogh", "mode": "persona", "question_id": "vg-03", "model": "made-up", "llm_ms": 1,
        "reply": reply("My brother Theo worked as an art dealer in Paris.", "not_in_sources")}}
    rows, summary = eval_grounding.evaluate(FROZEN, replies)
    assert len(rows) == 1
    assert summary["all"]["before"]["unsupported_text_shown"] == 1
    assert summary["all"]["after"]["unsupported_text_shown"] == 0
    assert summary["all"]["after"]["changed_by_check"] == {"decline_that_answers": 1}
