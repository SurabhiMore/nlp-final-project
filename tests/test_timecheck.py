"""Tests for pipeline/timecheck.py. They never touch the network: every Wikidata
answer comes from a small cache file written into a temporary folder."""
import json

import pytest

from pipeline import timecheck
from pipeline.timecheck import WikidataCache, check_time, parse_year

VAN_GOGH = {"name": "Vincent van Gogh", "time_period": {"start": 1853, "end": 1890, "end_year": 1890}}
T_REX = {"name": "Tyrannosaurus rex", "time_period": {"start": -69000000, "end": -66000000}}

FAKE = {
    "search:guernica": ["Q175036"],
    "year:Q175036": 1937,
    "search:lust for life": ["Q1", "Q2"],       # the 1934 novel and the 1956 film
    "year:Q1": 1934, "year:Q2": 1956,
    "search:theo": ["Q3", "Q4"],                # Theo van Gogh (art dealer, 1857) and the filmmaker (1957)
    "year:Q3": 1857, "year:Q4": 1957,
    "search:paris": ["Q90"], "year:Q90": -300,
    "search:picasso": ["Q5593"], "year:Q5593": 1881,
    "search:zorblax": [],                       # unknown entity
}


@pytest.fixture
def cache(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text(json.dumps(FAKE))
    return WikidataCache(path, offline=True)


def test_parse_year():
    assert parse_year("+1937-01-01T00:00:00Z") == 1937
    assert parse_year("-0066000000-00-00T00:00:00Z") == -66000000


def test_explicit_year_after_end_is_flagged(cache):
    assert check_time("Did you see the 1956 film about you?", VAN_GOGH, cache, use_spacy=False)["flag"]


def test_year_inside_time_not_flagged(cache):
    assert not check_time("What did you paint in 1888?", VAN_GOGH, cache, use_spacy=False)["flag"]


def test_year_equal_to_end_not_flagged(cache):
    assert not check_time("What happened in 1890?", VAN_GOGH, cache, use_spacy=False)["flag"]


def test_work_after_end_is_flagged(cache):
    assert check_time("What did you think of Picasso's Guernica?", VAN_GOGH, cache, use_spacy=False)["flag"]


def test_ambiguous_name_not_flagged(cache):
    # one Theo is from before 1890, so we must not block the question
    assert not check_time("Tell me about Theo.", VAN_GOGH, cache, use_spacy=False)["flag"]
    assert not check_time("Did you like Paris?", VAN_GOGH, cache, use_spacy=False)["flag"]


def test_unknown_entity_not_flagged(cache):
    result = check_time("Have you met Zorblax?", VAN_GOGH, cache, use_spacy=False)
    assert not result["flag"]


def test_cache_miss_offline_is_unknown(cache):
    result = check_time("Did you meet Napoleon?", VAN_GOGH, cache, use_spacy=False)
    assert not result["flag"]
    assert cache.misses >= 1


def test_cache_hit_counted(cache):
    check_time("Did you like Paris?", VAN_GOGH, cache, use_spacy=False)
    assert cache.hits >= 1


def test_cache_miss_online_fetches_and_saves(tmp_path, monkeypatch):
    path = tmp_path / "cache.json"
    monkeypatch.setattr(timecheck, "_search_online", lambda text: ["Q9"])
    monkeypatch.setattr(timecheck, "_year_online", lambda qid: 1969)
    cache = WikidataCache(path)
    assert check_time("Did you see the Moon Landing?", VAN_GOGH, cache, use_spacy=False)["flag"]
    saved = json.loads(path.read_text())
    assert saved["year:Q9"] == 1969


def test_persona_without_end_year_is_skipped(cache):
    result = check_time("Did you see the 1993 film?", T_REX, cache, use_spacy=False)
    assert not result["flag"]
    assert "skipped" in result["reasons"][0]


def test_own_name_is_ignored(cache):
    result = check_time("Vincent, what did you paint?", VAN_GOGH, cache, use_spacy=False)
    assert result["entities"] == []
