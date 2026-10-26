"""The quote checker (pipeline/quotes.py) and its evaluation (eval/eval_quotes.py)."""
import json
import os

import pytest

from eval import datasets
from eval import eval_quotes as ev
from pipeline import config
from pipeline import quotes as qm

REAL = "I can only choose between being a good and a bad painter."   # van-gogh-gut40393-0057
REAL_ID = "van-gogh-gut40393-0057"


def test_a_line_from_his_letters_is_verbatim():
    result = qm.match_quote(REAL, "van-gogh")
    assert result["verdict"] == qm.VERBATIM
    assert result["score"] == 100
    assert result["passage_id"] == REAL_ID
    assert qm.normalize(result["match"]) == qm.normalize(REAL)


@pytest.mark.parametrize("quote", [
    "i can ONLY choose between being a good, and a bad painter!!",
    "“I can only choose between being a good and a bad painter”",
], ids=["case-and-punctuation", "curly-quotes"])
def test_case_and_punctuation_do_not_matter(quote):
    assert qm.match_quote(quote, "van-gogh")["verdict"] == qm.VERBATIM


@pytest.mark.parametrize("quote", ["To-day I shall write to our sister", "Today I shall write to our sister"])
def test_hyphens_do_not_matter(quote):
    assert qm.match_quote(quote, "van-gogh")["verdict"] == qm.VERBATIM


def test_one_changed_word_is_a_close_paraphrase_of_the_right_passage():
    result = qm.match_quote("I can only choose between being a great and a bad painter.", "van-gogh")
    assert result["verdict"] == qm.CLOSE
    assert result["passage_id"] == REAL_ID


def test_a_line_by_someone_else_is_not_found():
    quote = "Every child is an artist. The problem is how to remain an artist once we grow up."
    assert qm.match_quote(quote, "van-gogh")["verdict"] == qm.NOT_FOUND


def test_the_closest_text_is_taken_from_the_passage():
    result = qm.match_quote("I can only choose between being a great and a bad painter.", "van-gogh")
    passage = next(p for p in qm.own_words_passages("van-gogh") if p.id == result["passage_id"])
    assert result["match"] and result["match"] in passage.text


def test_an_exhibit_without_own_words_finds_no_quote():
    assert qm.own_words_passages("t-rex") == []
    result = qm.match_quote(REAL, "t-rex")
    assert result["verdict"] == qm.NOT_FOUND
    assert result["passage_id"] is None
    assert all(r["verdict"] == qm.NOT_FOUND for r in qm.check_quote(f'Did you say "{REAL}"?', "t-rex"))


@pytest.mark.parametrize("score, verdict", [(100, qm.VERBATIM), (99.9, qm.CLOSE), (qm.THRESHOLD, qm.CLOSE),
                                            (qm.THRESHOLD - 0.1, qm.NOT_FOUND)])
def test_verdict_for_a_score(score, verdict):
    assert qm.verdict_for(score) == verdict


@pytest.mark.parametrize("text, expected", [
    ('Did you really say "the sadness will last forever"?', ["the sadness will last forever"]),
    ("Did you really say the sadness will last forever?", ["the sadness will last forever"]),
    ("Is it true you wrote to Theo that art is greater and longer than our lives?",
     ["art is greater and longer than our lives"]),
    ("He wrote ‘I don’t know what I’m doing’ to Theo.", ["I don’t know what I’m doing"]),
    ("He said 'I can only choose between being a good and a bad painter' once.", [REAL.rstrip(".")]),
    ("What did you write to Theo about Japan?", []),
    ("Did you write letters to your brother every week?", []),
    ("I painted “Café Terrace at Night” that year.", []),
    ('She called it "very lovely" and left.', []),
    ("No quotes here at all.", []),
], ids=["double-quotes", "did-you-say", "wrote-that", "curly-single-with-apostrophes", "straight-single",
        "what-did-you-write", "write-letters", "painting-title", "too-short", "no-quote"])
def test_find_quotes(text, expected):
    assert qm.find_quotes(text) == expected


def test_each_quote_in_an_answer_is_checked():
    answer = f'I once wrote "{REAL}" and later "Every child is an artist, so they say."'
    results = qm.check_quote(answer, "van-gogh")
    assert [r["verdict"] for r in results] == [qm.VERBATIM, qm.NOT_FOUND]


def test_passages_reload_when_the_chunks_file_changes(tmp_path, monkeypatch):
    path = tmp_path / "chunks.jsonl"
    monkeypatch.setattr(config, "chunks_path", lambda persona_id: path)

    def write(texts):
        path.write_text("".join(json.dumps({"id": f"x-{i}", "text": t, "own_words": True}) + "\n"
                                for i, t in enumerate(texts)), encoding="utf-8")

    write(["The first letter."])
    assert len(qm.own_words_passages("test-exhibit")) == 1
    write(["The first letter.", "The second letter."])
    os.utime(path, (path.stat().st_atime, path.stat().st_mtime + 5))
    assert len(qm.own_words_passages("test-exhibit")) == 2


# ---------------------------------------------------------------- the quote set

@pytest.fixture(scope="module")
def quote_set():
    return ev.load_quote_set()


def test_quote_set_has_every_kind_in_both_halves(quote_set):
    for kind, label in ev.KINDS.items():
        for half in ev.SPLITS:
            rows = [q for q in quote_set if q["kind"] == kind and q["split"] == half]
            assert rows, f"no {kind} quotes in the {half} half"
            assert all(q["label"] == label for q in rows)


def test_real_quotes_are_word_for_word_in_their_letter(quote_set):
    chunks = {c["id"]: c for c in datasets.load_chunks("van-gogh")}
    for q in quote_set:
        if q["kind"] == "real":
            assert chunks[q["source"]]["own_words"], q["id"]
            assert q["quote"] in chunks[q["source"]]["text"], q["id"]


def test_altered_quotes_are_changed_from_a_real_line(quote_set):
    chunks = {c["id"]: c for c in datasets.load_chunks("van-gogh")}
    for q in quote_set:
        if q["kind"] == "altered":
            assert q["original"] in chunks[q["source"]]["text"], q["id"]
            assert q["quote"] != q["original"] and q["quote"] not in chunks[q["source"]]["text"], q["id"]


@pytest.mark.parametrize("record, message", [
    ({"id": "a", "quote": "x", "label": "verbatim", "kind": "real", "split": "dev"}, "missing 'source'"),
    ({"id": "a", "quote": "x", "label": "verbatim", "kind": "popular", "source": "s", "split": "dev"}, "must have label"),
    ({"id": "a", "quote": "x", "label": "verbatim", "kind": "real", "source": "s", "split": "train"}, "dev or test"),
], ids=["missing-field", "wrong-label", "bad-split"])
def test_quote_set_problems_are_reported(tmp_path, record, message):
    path = tmp_path / "quotes.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        ev.load_quote_set(path)


def test_repeated_quote_ids_are_reported(tmp_path):
    record = {"id": "a", "quote": "x", "label": "verbatim", "kind": "real", "source": "s", "split": "dev"}
    path = tmp_path / "quotes.jsonl"
    path.write_text((json.dumps(record) + "\n") * 2, encoding="utf-8")
    with pytest.raises(ValueError, match="repeated id"):
        ev.load_quote_set(path)


# ---------------------------------------------------------------- the evaluation

def test_threshold_is_the_middle_of_the_tied_ones():
    dev = [{"score": 90, "label": qm.CLOSE}, {"score": 70, "label": qm.NOT_FOUND}]
    threshold, best, tied = ev.choose_threshold(dev)
    assert best == 1.0
    assert (tied[0], tied[-1]) == (71, 90)
    assert threshold == 80


def test_checker_uses_the_threshold_chosen_on_the_dev_half(quote_set):
    dev = [q for q in ev.score_quotes(quote_set) if q["split"] == "dev"]
    assert ev.choose_threshold(dev)[0] == qm.THRESHOLD


def test_reply_text_reads_json_replies_and_falls_back_to_the_raw_text():
    assert ev._reply_text('{"answer": "Hello", "status": "answered"}') == "Hello"
    assert ev._reply_text("not json") == "not json"


def test_saved_answers_include_the_user_test_logs():
    sources = {source for source, _, _ in ev.saved_answers()}
    assert "grounding_replies.jsonl" in sources
    assert any(source.startswith("session07/") for source in sources)


def test_results_are_written_as_json_and_markdown(tmp_path, quote_set):
    small = tmp_path / "quotes.jsonl"
    rows = [q for q in quote_set if q["id"] in {"vgq-01", "vgq-02", "vgq-45", "vgq-46", "vgq-63", "vgq-64"}]
    small.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in rows), encoding="utf-8")
    report = ev.run(small)
    json_path, md_path = ev.write_outputs(report, tmp_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["quotes"] == 6
    text = md_path.read_text(encoding="utf-8")
    assert "## Test half" in text and "## Every wrong result" in text and "## Quotes in saved Van Gogh answers" in text
