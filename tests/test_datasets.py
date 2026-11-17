"""Automated tests for held-out question datasets and validation rules."""

import json
from pathlib import Path

import pytest

from eval import datasets
from pipeline import config

EXHIBITS = {"t-rex", "van-gogh"}
EXPECTED_QUESTION_COUNT = 32


@pytest.mark.parametrize("persona_id", sorted(EXHIBITS))
def test_question_file_passes_validation(persona_id):
    """The question file for each exhibit loads cleanly and has zero validation problems."""
    problems = datasets.check(persona_id)
    assert problems == 0, f"{persona_id} question file had {problems} validation problem(s)"


@pytest.mark.parametrize("persona_id, prefix", [("van-gogh", "vg-"), ("t-rex", "tr-")])
def test_question_counts_and_id_conventions(persona_id, prefix):
    """Each exhibit has exactly 32 questions with unique IDs following its exhibit prefix."""
    questions = datasets.load_questions(persona_id)
    assert len(questions) == EXPECTED_QUESTION_COUNT, (
        f"Expected {EXPECTED_QUESTION_COUNT} questions for {persona_id}, got {len(questions)}"
    )

    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), f"Duplicate question IDs found in {persona_id}"
    for qid in ids:
        assert qid.startswith(prefix), f"Question ID {qid} does not start with {prefix}"


def test_question_ids_are_globally_unique():
    """No question ID is shared across different exhibit question files."""
    all_ids = []
    for pid in EXHIBITS:
        all_ids.extend([q["id"] for q in datasets.load_questions(pid)])
    assert len(all_ids) == len(set(all_ids)), "Duplicate question IDs found across exhibits"


@pytest.mark.parametrize("persona_id", sorted(EXHIBITS))
def test_answerable_questions_have_verified_supporting_chunks(persona_id):
    """Every answerable question has non-empty evidence and resolvable supporting chunks."""
    chunks = datasets.load_chunks(persona_id)
    questions = datasets.load_questions(persona_id)
    answerable = [q for q in questions if q["answerable"]]
    assert len(answerable) > 0

    for q in answerable:
        support = datasets.supporting_chunk_ids(q, chunks)
        assert len(support) > 0, f"{q['id']}: no supporting chunks found for evidence {q.get('evidence')}"
        support_text = " ".join(c["text"] for c in chunks if c["id"] in support)
        assert datasets.key_facts_present(support_text, q["key_facts"]), (
            f"{q['id']}: key facts {q['key_facts']} missing from supporting text"
        )
        assert datasets.key_facts_present(q["gold_answer"], q["key_facts"]), (
            f"{q['id']}: key facts {q['key_facts']} missing from gold answer"
        )


@pytest.mark.parametrize("persona_id", sorted(EXHIBITS))
def test_unanswerable_traps_have_empty_evidence_and_facts(persona_id):
    """Every unanswerable trap question has empty evidence and key_facts lists."""
    questions = datasets.load_questions(persona_id)
    traps = [q for q in questions if not q["answerable"]]
    assert len(traps) > 0

    for q in traps:
        assert q["type"] in datasets.DECLINE_TYPES, f"{q['id']}: trap has unexpected type {q['type']}"
        assert q["evidence"] == [], f"{q['id']}: trap must have empty evidence"
        assert q["key_facts"] == [], f"{q['id']}: trap must have empty key_facts"
        assert q.get("chunks") in (None, []), f"{q['id']}: trap cannot cite chunks"


def test_validation_detects_duplicate_ids(tmp_path, monkeypatch):
    """Validation detects duplicate question IDs in a question file."""
    fake_file = tmp_path / "mock-exhibit.jsonl"
    fake_file.write_text(
        json.dumps({"id": "m-01", "question": "Q1", "type": "fact", "answerable": True,
                    "gold_answer": "A1", "key_facts": [["A1"]], "evidence": ["E1"]}) + "\n" +
        json.dumps({"id": "m-01", "question": "Q2", "type": "fact", "answerable": True,
                    "gold_answer": "A2", "key_facts": [["A2"]], "evidence": ["E2"]}) + "\n",
        encoding="utf-8"
    )
    monkeypatch.setattr(datasets, "QUESTIONS_DIR", tmp_path)
    with pytest.raises(ValueError, match="duplicate question ids: m-01"):
        datasets.load_questions("mock-exhibit")


def test_validation_detects_malformed_json_lines(tmp_path, monkeypatch):
    """Validation catches syntax errors in JSON lines with line numbers."""
    fake_file = tmp_path / "mock-exhibit.jsonl"
    fake_file.write_text('{"id": "m-01", "question": "Unclosed string\n', encoding="utf-8")
    monkeypatch.setattr(datasets, "QUESTIONS_DIR", tmp_path)
    with pytest.raises(ValueError, match="is malformed JSON"):
        datasets.load_questions("mock-exhibit")


def test_validation_detects_non_dict_record(tmp_path, monkeypatch):
    """Validation catches records that are not JSON objects."""
    fake_file = tmp_path / "mock-exhibit.jsonl"
    fake_file.write_text('["not", "a", "dictionary"]\n', encoding="utf-8")
    monkeypatch.setattr(datasets, "QUESTIONS_DIR", tmp_path)
    with pytest.raises(ValueError, match="must be a JSON object"):
        datasets.load_questions("mock-exhibit")


@pytest.mark.parametrize("missing_key", ["id", "question", "type", "answerable", "gold_answer", "key_facts", "evidence"])
def test_validation_detects_missing_required_fields(tmp_path, monkeypatch, missing_key):
    """Validation catches missing required fields."""
    record = {"id": "m-01", "question": "Q", "type": "fact", "answerable": True,
              "gold_answer": "A", "key_facts": [["A"]], "evidence": ["E"]}
    del record[missing_key]
    fake_file = tmp_path / "mock-exhibit.jsonl"
    fake_file.write_text(json.dumps(record) + "\n", encoding="utf-8")
    monkeypatch.setattr(datasets, "QUESTIONS_DIR", tmp_path)
    with pytest.raises(ValueError, match=f"is missing '{missing_key}'"):
        datasets.load_questions("mock-exhibit")


def test_validation_detects_type_and_answerable_mismatch(tmp_path, monkeypatch):
    """Validation ensures decline types have answerable=False and vice versa."""
    fake_file = tmp_path / "mock-exhibit.jsonl"
    # fact cannot be answerable=False
    fake_file.write_text(
        json.dumps({"id": "m-01", "question": "Q", "type": "fact", "answerable": False,
                    "gold_answer": "A", "key_facts": [], "evidence": []}) + "\n",
        encoding="utf-8"
    )
    monkeypatch.setattr(datasets, "QUESTIONS_DIR", tmp_path)
    with pytest.raises(ValueError, match="does not match answerable=False"):
        datasets.load_questions("mock-exhibit")


def test_validation_detects_persona_mismatch(tmp_path, monkeypatch):
    """Validation catches questions tagged with a different persona."""
    fake_file = tmp_path / "van-gogh.jsonl"
    fake_file.write_text(
        json.dumps({"id": "vg-99", "persona": "t-rex", "question": "Wrong persona",
                    "type": "fact", "answerable": True, "gold_answer": "A",
                    "key_facts": [["A"]], "evidence": ["E"]}) + "\n",
        encoding="utf-8"
    )
    monkeypatch.setattr(datasets, "QUESTIONS_DIR", tmp_path)
    with pytest.raises(ValueError, match="persona 't-rex' does not match 'van-gogh'"):
        datasets.load_questions("van-gogh")


def test_validation_detects_invalid_chunk_reference_in_check(monkeypatch, capsys):
    """datasets.check reports problems when a question cites a non-existent chunk ID."""
    bad_question = {
        "id": "vg-99",
        "question": "Where is the fake chunk?",
        "type": "fact",
        "answerable": True,
        "gold_answer": "Nowhere.",
        "key_facts": [["Nowhere"]],
        "evidence": ["nonexistent snippet"],
        "chunks": ["non-existent-chunk-9999"],
    }
    monkeypatch.setattr(datasets, "load_questions", lambda pid: [bad_question])
    problems = datasets.check("van-gogh")
    assert problems > 0
    captured = capsys.readouterr()
    assert "not found in van-gogh corpus" in captured.out or "evidence not found in any passage" in captured.out


@pytest.mark.parametrize("text, key_facts, expected", [
    ("I lived about six million years ago.", [["6 million"]], True),
    ("I roamed 6 million years ago.", [["six million"]], True),
    ("I had two clawed fingers.", [["2"]], True),
    ("I had 2 clawed fingers.", [["two"]], True),
    ("I painted three versions.", [["3"]], True),
    ("I painted 3 versions.", [["three"]], True),
    ("It measured twelve metres.", [["12"]], True),
    ("It weighed 8 tons.", [["eight"]], True),
    ("I had twenty teeth.", [["20"]], True),
])
def test_key_facts_present_accepts_number_words(text, key_facts, expected):
    """key_facts_present accepts number words for digits and vice versa."""
    assert datasets.key_facts_present(text, key_facts) == expected


@pytest.mark.parametrize("text, key_facts, expected", [
    ("I could see up to 6 kilometres away.", [["6 km"]], True),
    ("I could see up to 6 kilometers away.", [["6 km"]], True),
    ("I could see up to 6 km away.", [["6 kilometres"]], True),
    ("I could see up to 6 km away.", [["6 kilometers"]], True),
    ("The stride was 9 metres long.", [["9 m"]], True),
    ("The stride was 9 meters long.", [["9 m"]], True),
    ("The stride was 9 m long.", [["9 metres"]], True),
    ("The tooth measured 30 centimetres.", [["30 cm"]], True),
    ("The tooth measured 30 centimeters.", [["30 cm"]], True),
    ("The claw was 15 millimetres.", [["15 mm"]], True),
    ("The claw was 15 millimeters.", [["15 mm"]], True),
])
def test_key_facts_present_accepts_unit_spellings(text, key_facts, expected):
    """key_facts_present accepts standard unit abbreviations and spellings."""
    assert datasets.key_facts_present(text, key_facts) == expected


def test_key_facts_present_accepts_combined_number_and_units():
    """key_facts_present accepts number words combined with unit spellings."""
    text = "I could spot objects as far as six kilometres away."
    key_facts = [["6 km"]]
    assert datasets.key_facts_present(text, key_facts)

    text2 = "I had keen vision up to six kilometers away."
    assert datasets.key_facts_present(text2, [["6 km", "6 kilometers", "6 kilometres"]])

    text3 = "My stride was nine metres."
    assert datasets.key_facts_present(text3, [["9 m"]])


def test_key_facts_present_alternatives():
    """key_facts_present correctly matches synonyms added as alternatives."""
    # tr-09: 'strongest' for 'largest'
    text_bite = "Scientists estimate my bite was the strongest of any land animal."
    assert datasets.key_facts_present(text_bite, [["largest", "strongest"]])

    # tr-28: 'dim light' for 'low-light'
    text_vision = "My eyes were not great in dim light, so I hunted during the day."
    assert datasets.key_facts_present(text_vision, [["day", "diurnal"], ["low-light", "poor", "dim light"]])

