"""The question classifier (pipeline/classifier.py) and its evaluation (eval/eval_classifier.py)."""
import json

import pytest

from eval import datasets
from eval import eval_answers
from eval import eval_classifier as ev
from pipeline import classifier, config
from pipeline import persona as engine

VAN_GOGH = config.load_persona("van-gogh")
T_REX = config.load_persona("t-rex")


@pytest.mark.parametrize("question", [
    "What is 17 times 23?",
    "12 times 8",
    "What's the weather?",
    "What is the capital of France?",
    "Can you help me write my chemistry homework?",
    "Can you recommend a good phone to buy?",
])
@pytest.mark.parametrize("persona", [VAN_GOGH, T_REX], ids=["van-gogh", "t-rex"])
def test_clearly_unrelated_questions_are_off_topic(question, persona):
    assert classifier.classify(question, persona)["label"] == classifier.OFF_TOPIC


@pytest.mark.parametrize("question", [
    "Did you enjoy the 1956 film Lust for Life about your life?",
    "What do you think of Don McLean's 1971 song?",
    "What did people say about you in 1950?",
])
def test_a_year_after_his_death_is_out_of_time_for_van_gogh(question):
    decision = classifier.classify(question, VAN_GOGH)
    assert decision["label"] == classifier.OUT_OF_TIME
    assert "1890" in decision["reason"]


@pytest.mark.parametrize("question", [
    "Hello!",
    "Who are you?",
    "Are you real?",
    "Can you roar for me?",
    "what sound was your roar",
    "How welcome you smell.",
    "for your teeth",
    "bedroom",
    "¿Cuál es la capital de Francia?",
    "आपका जन्म कब हुआ था?",
    "What was the weather like in Arles?",
    "How is the weather in Arles?",
    "Where did you work as a missionary in 1879?",
    "How fast could you run?",
    "What happened to you after 1890?",
    "What should I get out of this painting?",
    "Who is the president of the museum?",
    "What is the capital of the country you lived in?",
    "Would you outrun the best sports car?",
    "My essay is about sunflowers. What did they mean to you?",
    "Can you help me with my essay on your paintings?",
    "What is 17 times your height?",
    "What is Van Gogh's capital of France?",
])
@pytest.mark.parametrize("persona", [VAN_GOGH, T_REX], ids=["van-gogh", "t-rex"])
def test_questions_that_must_get_through(question, persona):
    assert classifier.classify(question, persona)["label"] == classifier.IN_DOMAIN


@pytest.mark.parametrize("question", ["Was Sue found in 1990?", "Did you see the 1956 film?", "Who bought Sue in 1997?"])
def test_the_year_rule_leaves_the_t_rex_out(question):
    assert classifier.classify(question, T_REX)["label"] == classifier.IN_DOMAIN


@pytest.mark.parametrize("question", [
    "Did you really paint 2000 paintings?",
    "Were you paid in 1900 francs?",
    "Will people remember you in 2000 years?",
    "I saw your work in 2019. Was it painted in Arles?",
    "My family went to your 1950 show. Did you paint it all?",
])
def test_amounts_and_the_visitors_own_years_are_not_out_of_time(question):
    assert classifier.classify(question, VAN_GOGH)["label"] == classifier.IN_DOMAIN


@pytest.mark.parametrize("question", [None, "", "   ", 123, [], {}])
@pytest.mark.parametrize("persona", [VAN_GOGH, T_REX, None, {}, {"name": None}], ids=["vg", "tr", "none", "empty", "bad"])
def test_classify_never_raises_on_bad_input(question, persona):
    assert classifier.classify(question, persona)["label"] == classifier.IN_DOMAIN


@pytest.mark.parametrize("persona", [{"perspective": "own_words", "time_period": {}},
                                     {"perspective": "own_words"},
                                     {"name": None, "perspective": "own_words", "time_period": {"end_year": "soon"}}],
                         ids=["no-end-year", "no-time-period", "bad-values"])
def test_an_exhibit_with_missing_or_bad_fields_never_raises(persona):
    assert classifier.classify("Did you see the 1956 film?", persona)["label"] == classifier.IN_DOMAIN


def test_every_decision_gives_a_label_and_a_reason():
    for question in ("What is 17 times 23?", "Did you see the 1956 film?", "How fast could you run?"):
        decision = classifier.classify(question, VAN_GOGH)
        assert set(decision) == {"label", "reason"}
        assert decision["label"] in ev.LABELS and decision["reason"]


# ---------------------------------------------------------------- the reply

@pytest.mark.parametrize("question, status", [("What is 17 times 23?", "declined"),
                                              ("Did you see the 1956 film?", "outside_time")])
@pytest.mark.parametrize("mode", ["persona", "neutral"])
def test_a_blocked_question_gets_the_fixed_line(question, status, mode):
    reply = classifier.short_circuit(question, VAN_GOGH, mode)
    assert reply["status"] == status
    assert reply["answer"] == engine._fixed_line(status, VAN_GOGH, mode)
    assert reply["citations"] == [] and reply["sound"] is None
    assert reply["model"] == classifier.MODEL_LABEL


def test_a_question_that_gets_through_has_no_short_circuit():
    assert classifier.short_circuit("How fast could you run?", T_REX) is None


def test_the_fixed_line_counts_as_a_decline_in_the_reply_check():
    reply = classifier.short_circuit("What is 17 times 23?", VAN_GOGH)
    assert engine.check_reply(reply, VAN_GOGH, "What is 17 times 23?")["check"] is None


@pytest.mark.parametrize("value", ["0", "false", "no", "off", " OFF "])
def test_enable_classifier_can_switch_it_off(monkeypatch, value):
    monkeypatch.setenv("ENABLE_CLASSIFIER", value)
    assert classifier.short_circuit("What is 17 times 23?", VAN_GOGH) is None


@pytest.mark.parametrize("value", ["1", "true", None])
def test_enable_classifier_is_on_by_default(monkeypatch, value):
    monkeypatch.delenv("ENABLE_CLASSIFIER", raising=False)
    if value is not None:
        monkeypatch.setenv("ENABLE_CLASSIFIER", value)
    assert classifier.short_circuit("What is 17 times 23?", VAN_GOGH) is not None


# ---------------------------------------------------------------- eval_answers uses the same decision

@pytest.fixture
def two_questions(tmp_path, monkeypatch):
    """A question file with one off-topic trap and one real question, and no progress file written."""
    monkeypatch.setattr(eval_answers, "save_progress", lambda row: None)
    rows = {q["id"]: q for q in datasets.load_questions("t-rex")}
    (tmp_path / "t-rex.jsonl").write_text(
        "".join(json.dumps(rows[i]) + "\n" for i in ("tr-21", "tr-11")), encoding="utf-8")
    return tmp_path


def test_eval_answers_makes_the_same_check_as_ask(two_questions):
    rows = {r["question_id"]: r for r in eval_answers.run(["t-rex"], ["persona"], questions_dir=two_questions)}
    assert rows["tr-21"]["model"] == classifier.MODEL_LABEL
    assert rows["tr-21"]["status"] == "declined" and rows["tr-21"]["correct"]
    assert rows["tr-21"]["retrieved"] == []
    assert rows["tr-11"]["model"] != classifier.MODEL_LABEL
    assert rows["tr-11"]["retrieved"]


def test_eval_answers_runs_the_old_way_when_switched_off(two_questions, monkeypatch):
    monkeypatch.setenv("ENABLE_CLASSIFIER", "0")
    rows = {r["question_id"]: r for r in eval_answers.run(["t-rex"], ["persona"], questions_dir=two_questions)}
    assert rows["tr-21"]["model"] != classifier.MODEL_LABEL
    assert rows["tr-21"]["retrieved"]


def test_median_model_time_leaves_out_questions_that_skipped_the_model(two_questions):
    rows = eval_answers.run(["t-rex"], ["persona"], questions_dir=two_questions)
    for row in rows:
        row["llm_ms"] = 0 if row["model"] == classifier.MODEL_LABEL else 500
    assert eval_answers.summarize(rows)["median_llm_ms"] == 500


# ---------------------------------------------------------------- the evaluation

def test_no_question_that_must_get_through_is_blocked():
    for name, rows in ev.must_pass_sets().items():
        assert rows, name
        for row in rows:
            decision = classifier.classify(row["question"], config.load_persona(row["exhibit"]))
            assert decision["label"] == classifier.IN_DOMAIN, f"{name}: {row['question']} ({decision['reason']})"


def test_the_sets_have_the_sizes_the_issue_names():
    sizes = {name: len(rows) for name, rows in {**ev.must_pass_sets(), **ev.trap_sets()}.items()}
    assert list(sizes.values())[:3] == [46, 10, 14]
    assert list(sizes.values())[4:] == [4, 8, 16]


def test_user_test_logs_keep_the_question_and_model_time():
    rows = ev.log_rows()
    assert any(r["question"] == "12 times 8" and r["status"] == "declined" for r in rows)
    assert all("llm_ms" in r for r in rows)


def test_held_out_set_has_every_expected_label():
    rows = ev.load_held_out()
    assert {r["expected"] for r in rows} == set(ev.LABELS)
    assert {r["exhibit"] for r in rows} == {"van-gogh", "t-rex"}


@pytest.mark.parametrize("record, message", [
    ({"id": "a", "question": "q", "expected": "in_domain"}, "missing 'category'"),
    ({"id": "a", "question": "q", "expected": "maybe", "category": "c"}, "expected must be"),
], ids=["missing-field", "bad-label"])
def test_held_out_problems_are_reported(tmp_path, record, message):
    (tmp_path / "van-gogh.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        ev.load_held_out(tmp_path)


def test_repeated_held_out_ids_are_reported(tmp_path):
    record = {"id": "a", "question": "q", "expected": "in_domain", "category": "c"}
    (tmp_path / "van-gogh.jsonl").write_text((json.dumps(record) + "\n") * 2, encoding="utf-8")
    with pytest.raises(ValueError, match="repeated id"):
        ev.load_held_out(tmp_path)


def test_results_are_written_with_every_section(tmp_path):
    rows = [{"id": "a", "question": "What is 17 times 23?", "expected": "off_topic", "category": "maths"},
            {"id": "b", "question": "How fast could you run?", "expected": "off_topic", "category": "other"},
            {"id": "c", "question": "How fast could you run?", "expected": "in_domain", "category": "tricky"}]
    (tmp_path / "t-rex.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    report = ev.run(tmp_path)
    assert report["held_out"]["right"] == 2 and report["held_out"]["accuracy"] == 0.667
    assert [w["id"] for w in report["held_out"]["wrong"]] == ["b"]
    assert report["false_blocks"] == []
    json_path, md_path = ev.write_outputs(report, tmp_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["held_out"]["questions"] == 3
    text = md_path.read_text(encoding="utf-8")
    for section in ("## False blocks", "## Catch rate", "## Held-out set", "Every wrong result", "calls saved", "## Limitations"):
        assert section in text
