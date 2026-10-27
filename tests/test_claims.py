"""Tests for the claim checker (pipeline/claims.py) and evaluation (eval/eval_claims.py)."""

from __future__ import annotations

import pytest

from eval import datasets
from eval import eval_claims as ev
from pipeline import config
from pipeline.claims import check_claims, extract_claims


# ── extraction tests ──────────────────────────────────────────────────────────

def test_extract_dates_and_years():
    text = "Gauguin arrived in Arles on 23 October 1888, and I died in July 1890."
    claims = extract_claims(text)
    assert "23 October 1888" in claims
    assert "July 1890" in claims


def test_extract_bare_years_and_decades():
    text = "I was discovered in 1900, but other specimens followed in the 1890s."
    claims = extract_claims(text)
    assert "1900" in claims
    assert "1890s" in claims


def test_extract_geological_ages():
    text = "I lived about 66 million years ago in the late Cretaceous."
    claims = extract_claims(text)
    assert any("66" in c and "million years" in c.lower() for c in claims)


def test_extract_measurements_and_synonyms():
    text = "The specimen measures 12.3 metres long and weighed 8.8 tons."
    claims = extract_claims(text)
    assert "12.3 m" in claims
    assert "8.8 t" in claims


def test_extract_parenthetical_inches():
    text = "The tooth measured about 30.5 cm (12.0 in) with the root."
    claims = extract_claims(text)
    assert "30.5 cm" in claims
    assert "12.0 in" in claims or "12 in" in claims


def test_no_preposition_in_as_inches():
    """Ensure '1888 in Arles' does not extract '1888 in' as inches."""
    text = "I severed part of my left ear on the evening of 23 December 1888 in Arles."
    claims = extract_claims(text)
    assert "1888 in" not in claims
    assert "23 December 1888" in claims
    assert "Arles" in claims


def test_modal_may_not_extracted_as_month():
    """Lowercase 'may' is a modal verb, not the month May."""
    text = "Theo may have owed money to Gauguin."
    claims = extract_claims(text)
    assert "may" not in claims
    assert "May" not in claims
    assert "Theo" in claims
    assert "Gauguin" in claims


def test_sentence_starter_prepositions_filtered_from_names():
    text = "In Gauguin's portrait of me I was shown while I was painting."
    claims = extract_claims(text)
    assert "In Gauguin" not in claims
    assert "In" not in claims
    assert "Gauguin" in claims


def test_extract_number_words():
    text = "I had two clawed fingers on each hand and painted three versions."
    claims = extract_claims(text)
    assert "two" in claims
    assert "three" in claims


def test_extract_proper_names():
    text = "Barnum Brown excavated fossils in the Hell Creek Formation."
    claims = extract_claims(text)
    assert "Barnum Brown" in claims
    assert "Hell Creek Formation" in claims


# ── matching edge cases ───────────────────────────────────────────────────────

def test_unit_synonym_matching():
    passages = [{"id": "p1", "text": "The complete animal was 12 metres in total length."}]
    # Answer uses short form "12 m"
    flags = check_claims("The animal was about 12 m long.", passages)
    assert flags == []


def test_parenthetical_conversion_accepted():
    passages = [{"id": "p1", "text": "The largest tooth measured 30.5 cm."}]
    # Answer includes inch equivalent (12 in)
    flags = check_claims("The tooth was 30.5 cm (12 in) long.", passages)
    assert flags == []


def test_name_subtoken_matching():
    passages = [{"id": "p1", "text": "He wrote frequent letters to Theo van Gogh in Paris."}]
    # Answer refers to "Theo"
    flags = check_claims("Theo supported him throughout his career.", passages)
    assert flags == []


def test_exhibit_persona_tokens_never_flagged():
    passages = [{"id": "van-gogh-wiki-0001", "text": "A famous Dutch Post-Impressionist painter."}]
    # "Vincent" is part of the persona's identity
    flags = check_claims("I, Vincent, painted many works.", passages)
    assert "Vincent" not in flags


def test_number_words_match_digits_bidirectionally():
    passages = [{"id": "p1", "text": "The creature had 2 clawed fingers on each hand."}]
    # Answer spells it out as "two"
    flags = check_claims("I had two clawed fingers on each hand.", passages)
    assert flags == []


def test_empty_answer_or_passages():
    assert check_claims("", [{"id": "p1", "text": "Some text"}]) == []
    assert check_claims("   ", [{"id": "p1", "text": "Some text"}]) == []
    # If cited passages are empty, all claims are flagged
    flags = check_claims("I arrived in Arles in 1888.", [])
    assert len(flags) > 0


# ── Session 7 regression tests ────────────────────────────────────────────────

def test_session07_p2_failure_regression():
    """Regression test for Session 7 P2: 'Did you move to Arles?'.

    The answer added that he later moved to Auvers-sur-Oise in 1890,
    which was absent from the cited passages.
    """
    vg_chunks = {c["id"]: c for c in datasets.load_chunks("van-gogh")}
    cited = [vg_chunks["van-gogh-wiki-0050"], vg_chunks["van-gogh-wiki-0027"]]
    answer = (
        "Yes, I moved often, for example I signed a lease in Arles in May 1888 and lived "
        "there in the Yellow House, and I later moved to Auvers-sur-Oise in 1890."
    )
    flags = check_claims(answer, cited)
    assert "1890" in flags
    assert "Auvers-sur-Oise" in flags


def test_session07_p4_failure_regression():
    """Regression test for Session 7 P4: 'Did you die?'.

    The answer gave the date 'July 1890', which was absent from the cited letter.
    """
    vg_chunks = {c["id"]: c for c in datasets.load_chunks("van-gogh")}
    cited = [vg_chunks["van-gogh-gut40393-0251"]]
    answer = "Yes, I died in July 1890, as recorded in the letters about my final days."
    flags = check_claims(answer, cited)
    assert any("1890" in f or "July" in f for f in flags)


# ── evaluation harness tests ──────────────────────────────────────────────────

def test_eval_claims_harness_runs():
    labels_path = config.EVAL_DIR / "claims_labels.jsonl"
    assert labels_path.exists()
    results = ev.evaluate(labels_path)
    assert results["real"]["total"] == 93
    assert results["perturbed"]["total"] == 30
    assert results["overall"]["total"] == 123
    assert results["real"]["precision"] >= 0.95
    assert results["real"]["recall"] >= 0.95
    assert results["perturbed"]["precision"] >= 0.95
    assert results["perturbed"]["recall"] >= 0.95
