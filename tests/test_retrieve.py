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


# ------------------------------------------------------------ terminology map

from pipeline.retrieve import TERM_MAP, query_terms  # noqa: E402


@pytest.mark.parametrize("question, added", [
    ("How many fingers did you have?", "digit"),
    ("How many FINGERS did you have?", "digit"),
    ("Which horned dinosaurs did you eat?", "ceratopsian"),
    ("How strong was your bite?", "forc"),
])
def test_terminology_variants_add_the_passage_word(question, added):
    terms = query_terms("t-rex", question)
    assert added in terms
    # the visitor's own words are kept too
    assert set(tokenize(normalize_query(question))) <= set(terms)


def test_ordinary_questions_are_not_expanded():
    question = "Who discovered the famous skeleton called Sue?"
    assert query_terms("t-rex", question) == tokenize(normalize_query(question))


def test_map_only_applies_to_its_exhibit():
    assert "digit" not in query_terms("van-gogh", "How many fingers did you paint?")


def test_every_mapped_word_is_in_the_t_rex_passages():
    from eval import datasets
    corpus = set()
    for c in datasets.load_chunks("t-rex"):
        corpus.update(tokenize(c["text"]))
    for words in TERM_MAP["t-rex"].values():
        for w in words:
            assert tokenize(w)[0] in corpus, f"{w!r} never appears in the passages"


@pytest.mark.parametrize("question, expected", [
    ("How many fingers did you have on each hand?", "t-rex-wiki-0000"),  # tr-10
    ("How strong was your bite?", "t-rex-wiki-0001"),                    # tr-09
])
def test_terminology_map_finds_the_passage(question, expected):
    assert expected in [r["id"] for r in retrieve("t-rex", question, k=5)]


# ------------------------------------------------------------ reciprocal rank fusion

from pipeline.retrieve import get_search_mode, reciprocal_rank_fusion  # noqa: E402


def test_rrf_combines_and_ranks_candidates():
    # doc 1 is rank 2 in list A and rank 1 in list B -> should score highest overall
    ranking_a = [0, 1]
    ranking_b = [1, 2]
    scores = reciprocal_rank_fusion([ranking_a, ranking_b], k=60)

    # 1/(60+1) ~ 0.01639; 1/(60+2) ~ 0.01613
    assert scores[1] > scores[0]
    assert scores[0] > scores[2]

    ordered = sorted(scores.keys(), key=lambda idx: scores[idx], reverse=True)
    assert ordered == [1, 0, 2]


def test_rrf_empty_rankings():
    assert reciprocal_rank_fusion([]) == {}
    assert reciprocal_rank_fusion([[]]) == {}


# ------------------------------------------------------------ search mode setting

def test_search_mode_defaults_to_bm25(monkeypatch):
    monkeypatch.delenv("SEARCH_MODE", raising=False)
    assert get_search_mode() == "bm25"


@pytest.mark.parametrize("mode", ["bm25", "dense", "hybrid"])
def test_search_mode_reads_env_var(monkeypatch, mode):
    monkeypatch.setenv("SEARCH_MODE", mode)
    assert get_search_mode() == mode


def test_search_mode_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("SEARCH_MODE", "super-vector-search")
    assert get_search_mode() == "bm25"


# ------------------------------------------------------------ embedding cache rebuild

import json  # noqa: E402
import numpy as np  # noqa: E402
from pipeline.retrieve import _Index  # noqa: E402


def test_embedding_cache_rebuild_and_reload(tmp_path, monkeypatch):
    chunks_file = tmp_path / "chunks.jsonl"
    chunks_data = [
        {"id": "c-01", "text": "Sunflowers in a vase.", "section": "Art"},
        {"id": "c-02", "text": "A bedroom in Arles.", "section": "Letters"},
    ]
    chunks_file.write_text("\n".join(json.dumps(c) for c in chunks_data) + "\n", encoding="utf-8")

    monkeypatch.setattr("pipeline.config.chunks_path", lambda pid: chunks_file)
    monkeypatch.setattr("pipeline.config.persona_dir", lambda pid: tmp_path)

    encode_calls = []

    class DummyModel:
        def encode(self, texts, **kwargs):
            encode_calls.append(texts)
            return np.ones((len(texts), 384), dtype=np.float32)

    monkeypatch.setattr("pipeline.retrieve._get_embedding_model", lambda: DummyModel())

    # 1. First retrieval must compute embeddings and save cache file
    idx = _Index("dummy")
    emb1 = idx.get_embeddings()
    assert len(encode_calls) == 1
    assert emb1.shape == (2, 384)
    cache_path = tmp_path / "embeddings.npy"
    assert cache_path.exists()

    # 2. Second index instance with same mtime loads from cache without calling encode
    idx2 = _Index("dummy")
    emb2 = idx2.get_embeddings()
    assert len(encode_calls) == 1  # no new call
    assert np.array_equal(emb1, emb2)

    # 3. Touch chunks file with newer timestamp -> index must rebuild embeddings
    import time
    time.sleep(0.01)
    chunks_file.touch()
    idx3 = _Index("dummy")
    emb3 = idx3.get_embeddings()
    assert len(encode_calls) == 2  # re-encoded because chunks changed
    assert emb3.shape == (2, 384)


def test_retrieve_all_modes_return_compatible_structure(tmp_path, monkeypatch):
    chunks_file = tmp_path / "chunks.jsonl"
    chunks_data = [
        {"id": "c-01", "text": "Sunflowers in a vase.", "section": "Art"},
        {"id": "c-02", "text": "A bedroom in Arles.", "section": "Letters"},
        {"id": "c-03", "text": "Starry night over the Rhone.", "section": "Night"},
    ]
    chunks_file.write_text("\n".join(json.dumps(c) for c in chunks_data) + "\n", encoding="utf-8")

    monkeypatch.setattr("pipeline.config.chunks_path", lambda pid: chunks_file)
    monkeypatch.setattr("pipeline.config.persona_dir", lambda pid: tmp_path)

    class DummyModel:
        def encode(self, texts, **kwargs):
            if isinstance(texts, str):
                return np.ones(384, dtype=np.float32)
            return np.ones((len(texts), 384), dtype=np.float32)

    monkeypatch.setattr("pipeline.retrieve._get_embedding_model", lambda: DummyModel())

    from pipeline.retrieve import _indexes
    _indexes.pop("dummy_exhibit", None)

    question = "Sunflowers?"
    for mode in ("bm25", "dense", "hybrid"):
        results = retrieve("dummy_exhibit", question, k=3, mode=mode)
        assert len(results) == 3
        assert [r["rank"] for r in results] == [1, 2, 3]
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
        for r in results:
            assert {"id", "text", "score", "rank"} <= set(r)
            assert isinstance(r["score"], float)

