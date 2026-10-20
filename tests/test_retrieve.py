"""Query normalization and BM25 search (issue #31).

Run with: python -m pytest tests/test_retrieve.py
"""
import pytest

from pipeline.retrieve import _stem, normalize_query, retrieve, tokenize


# ------------------------------------------------------------ normalization

@pytest.mark.parametrize("question", [
    "When did you live?",
    "WHEN DID YOU LIVE?",
    "  when   did you live  ",
    "When did you live?!?",
])
def test_case_whitespace_and_punctuation_do_not_change_the_query(question):
    assert tokenize(normalize_query(question)) == tokenize(normalize_query("When did you live?"))


@pytest.mark.parametrize("spelling", ["T. rex", "T-Rex", "t rex", "TRex", "trex", "T.Rex"])
def test_every_t_rex_spelling_becomes_the_same_terms(spelling):
    assert tokenize(normalize_query(f"Is the {spelling} tooth real?")) == ["t", "rex", "tooth", "real"]


def test_t_rex_rule_leaves_other_words_alone():
    assert normalize_query("The extra rexes in Texas") == "the extra rexes in texas"


@pytest.mark.parametrize("question", ["Who found Sue's skeleton?", "Who found Sue’s skeleton?"])
def test_possessive_leaves_no_stray_s(question):
    assert tokenize(normalize_query(question)) == ["found", "sue", "skeleton"]


def test_curly_quotes_are_straightened():
    assert normalize_query("“King” in Latin") == '"king" in latin'


def test_empty_and_stopword_only_questions():
    assert normalize_query("") == ""
    assert normalize_query(None) == ""
    assert retrieve("t-rex", "   ", k=5) == []
    assert retrieve("t-rex", "what is it?", k=5) == []


# ------------------------------------------------------------ stemming

@pytest.mark.parametrize("a, b", [
    ("lived", "live"), ("living", "live"),
    ("named", "name"), ("meaning", "mean"),
    ("hunted", "hunt"), ("paintings", "painting"), ("stories", "story"),
])
def test_word_forms_meet(a, b):
    assert _stem(a) == _stem(b)


@pytest.mark.parametrize("word", ["tyrannosaurus", "class", "need", "king", "red", "bed"])
def test_short_or_special_words_are_not_mangled(word):
    # "us"/"ss" endings keep their s; "eed", short -ed and short -ing words are left whole
    assert _stem(word) in {word, word[:-1]} and len(_stem(word)) >= 3


# ------------------------------------------------------------ retrieval

def test_return_structure_is_unchanged():
    results = retrieve("t-rex", "Where did you live?", k=5)
    assert len(results) == 5
    assert [r["rank"] for r in results] == [1, 2, 3, 4, 5]
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    for r in results:
        assert {"id", "text", "score", "rank"} <= set(r)
        assert isinstance(r["score"], float)


def test_question_is_not_modified():
    question = "Who named the T-Rex?"
    retrieve("t-rex", question, k=3)
    assert question == "Who named the T-Rex?"


def test_capitalization_variants_retrieve_the_same_passages():
    a = [r["id"] for r in retrieve("t-rex", "how heavy could you get?", k=5)]
    b = [r["id"] for r in retrieve("t-rex", "HOW HEAVY COULD YOU GET?", k=5)]
    assert a == b


def test_spelling_variants_retrieve_the_same_passages():
    a = [r["id"] for r in retrieve("t-rex", "Is the T. rex tooth real?", k=5)]
    b = [r["id"] for r in retrieve("t-rex", "is the trex tooth real", k=5)]
    assert a == b


def test_word_form_fix_finds_the_name_meaning():
    # tr-03: "mean" must now match "meaning" in the introduction passage
    top = [r["id"] for r in retrieve("t-rex", "What does the rex in your name mean?", k=5)]
    assert "t-rex-wiki-0000" in top


@pytest.mark.parametrize("exhibit, question, expected", [
    ("t-rex", "Who discovered the famous skeleton called Sue?", "t-rex-wiki-0007"),
    ("van-gogh", "In which town did you paint The Bedroom?", None),
])
def test_ordinary_questions_still_work(exhibit, question, expected):
    top = retrieve(exhibit, question, k=5)
    assert top, "an ordinary question should find passages"
    if expected:
        assert expected in [r["id"] for r in top]
