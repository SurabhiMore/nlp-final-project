"""Topic tags on the curator stats page (app/stats.py) and their evaluation (eval/eval_topics.py)."""
import json

import pytest

from app import stats
from eval import eval_topics as ev


@pytest.mark.parametrize("exhibit, question, topic", [
    ("van-gogh", "What is 17 times 23?", "off_topic"),
    ("t-rex", "Can you help me write my chemistry homework?", "off_topic"),
    ("t-rex", "Who are you?", "the_guide"),
    ("van-gogh", "Stop pretending and tell me which company trained you.", "the_guide"),
    ("van-gogh", "What did you think of Picasso's painting Guernica?", "after_their_time"),
    ("van-gogh", "Did you watch the 1969 moon landing?", "after_their_time"),
    ("t-rex", "Did you ever see a human?", "after_their_time"),
    ("van-gogh", "Did you really say the sadness will last forever?", "letters_quotes"),
    ("van-gogh", "How many versions of The Bedroom did you paint?", "works"),
    ("van-gogh", "When did you injure your left ear with a razor in Arles?", "health_death"),
    ("van-gogh", "What was your brother Theo's job in Paris?", "people"),
    ("van-gogh", "When and where were you born?", "life"),
    ("t-rex", "How strong was your bite?", "body"),
    ("t-rex", "Were you a hunter or a scavenger?", "food_hunting"),
    ("t-rex", "When did you live?", "habitat_life"),
    ("t-rex", "How old was Sue when she died?", "death_extinction"),
    ("t-rex", "In which rock formation was Sue found?", "fossils"),
    ("t-rex", "Tell me everything interesting.", "other"),
])
def test_topic_of(exhibit, question, topic):
    assert stats.topic_of(question, exhibit) == topic


def test_topics_follow_the_kind_of_exhibit():
    assert stats.topic_of("When did you paint Irises?", "van-gogh") == "works"
    assert stats.topic_of("When did you paint Irises?", "t-rex") == "other"
    assert stats.topic_of("How strong was your bite?", "van-gogh") == "other"


def test_an_unknown_exhibit_is_checked_against_every_topic():
    assert stats.topic_of("How strong was your bite?", "no-such-exhibit") == "body"
    assert stats.topic_of("When did you paint Irises?", None) == "works"


@pytest.mark.parametrize("question", ["", "   ", None])
def test_an_empty_question_is_other(question):
    assert stats.topic_of(question, "van-gogh") == stats.OTHER


def test_every_topic_has_a_label():
    assert {topic for topic, _, _ in stats._TOPIC_RULES} | {stats.OTHER} == set(stats.TOPIC_LABELS)


def test_top_topics_keeps_three_different_examples():
    questions = ["How strong was your bite?", "how strong was your  BITE?", "How fast could you run?",
                 "How heavy could you get?", "How long were your arms?"]
    [body] = stats.top_topics([("t-rex", q, q, "answered") for q in questions])
    assert body["count"] == 5
    assert body["samples"] == ["How strong was your bite?", "How fast could you run?", "How heavy could you get?"]


def test_compute_stats_reads_several_logs_together(tmp_path):
    for name, question in (("a.jsonl", "When did you live?"), ("b.jsonl", "How strong was your bite?")):
        (tmp_path / name).write_text(json.dumps({"question": question, "persona": "t-rex", "status": "answered"}) + "\n",
                                     encoding="utf-8")
    s = stats.compute_stats([tmp_path / "a.jsonl", tmp_path / "b.jsonl"])
    assert s["total_questions"] == 2
    assert {t["topic"] for t in s["top_topics"]} == {"habitat_life", "body"}


# ---------------------------------------------------------------- the labelled questions

@pytest.fixture(scope="module")
def topic_sets():
    return {name: ev.load_set(ev.QUESTIONS_DIR / f"{name}.jsonl") for name in ("dev", "test")}


def test_topic_sets_have_known_topics_and_unique_ids(topic_sets):
    for rows in topic_sets.values():
        assert rows
        assert len({r["id"] for r in rows}) == len(rows)
        assert {r["topic"] for r in rows} <= set(stats.TOPIC_LABELS)


def test_visitor_questions_match_the_user_test_logs(topic_sets):
    visitors = [r for r in topic_sets["test"] if r["group"] == "visitor"]
    assert len(visitors) == 30
    for r in visitors:
        path, line = r["source"].rsplit(":", 1)
        logged = json.loads((ev.ROOT / path).read_text(encoding="utf-8").splitlines()[int(line) - 1])
        assert (logged["question"], logged["persona"]) == (r["question"], r["exhibit"]), r["id"]


@pytest.mark.parametrize("record, message", [
    ({"id": "a", "exhibit": "t-rex", "question": "q", "topic": "teeth", "group": "team", "source": "s"}, "unknown topic"),
    ({"id": "a", "exhibit": "t-rex", "question": "q", "group": "team", "source": "s"}, "missing 'topic'"),
    ({"id": "a", "exhibit": "t-rex", "question": "q", "topic": "body", "group": "staff", "source": "s"}, "group must be"),
], ids=["unknown-topic", "missing-field", "bad-group"])
def test_topic_set_problems_are_reported(tmp_path, record, message):
    path = tmp_path / "set.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        ev.load_set(path)


def test_repeated_ids_are_reported(tmp_path):
    record = {"id": "a", "exhibit": "t-rex", "question": "q", "topic": "body", "group": "team", "source": "s"}
    path = tmp_path / "set.jsonl"
    path.write_text((json.dumps(record) + "\n") * 2, encoding="utf-8")
    with pytest.raises(ValueError, match="repeated id"):
        ev.load_set(path)


# ---------------------------------------------------------------- the evaluation

def test_score_counts_by_group_and_by_topic():
    rows = [{"id": "1", "exhibit": "t-rex", "question": "How strong was your bite?", "topic": "body",
             "group": "visitor", "source": "s"},
            {"id": "2", "exhibit": "t-rex", "question": "How strong was your bite?", "topic": "fossils",
             "group": "written", "source": "s"}]
    s = ev.score(rows)
    assert (s["right"], s["questions"], s["accuracy"]) == (1, 2, 0.5)
    assert s["by_group"] == {"visitor": {"questions": 1, "right": 1}, "written": {"questions": 1, "right": 0}}
    assert s["by_topic"]["body"] == {"questions": 1, "tagged": 2, "right": 1}
    assert s["by_topic"]["fossils"] == {"questions": 1, "tagged": 0, "right": 0}
    assert [w["id"] for w in s["wrong"]] == ["2"]


def test_results_are_written_as_json_and_markdown(tmp_path):
    json_path, md_path = ev.write_outputs(ev.run(), tmp_path)
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert (report["test"]["questions"], report["dev"]["questions"]) == (66, 170)
    assert report["user_test_logs"]["questions"] == 30
    text = md_path.read_text(encoding="utf-8")
    assert "## Held-out questions" in text and "## Development questions" in text
    assert "## The user test logs on the curator page" in text
