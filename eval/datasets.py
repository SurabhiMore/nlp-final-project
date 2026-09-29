"""
Load exhibit passages and held-out questions, and link questions to passages.

    {
      "id": "vg-01",
      "question": "In which town did you paint The Bedroom?",
      "type": "painting",                 # fact, date, why, painting, quote, outside_time, not_in_sources, off_topic
      "answerable": true,                 # false for traps the guide should decline
      "gold_answer": "Arles, in the south of France.",
      "key_facts": [["Arles"]],           # every inner list must be matched by at least one of its alternatives for an answer to count
      "evidence": ["his beloved \\"Yellow House\\" in Arles"]   # exact text from the sources
    }

Check that every question's evidence and key facts are in the sources:
    python -m eval.datasets --check
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config

QUESTIONS_DIR = config.EVAL_DIR / "questions"
QUESTION_TYPES = {"fact", "date", "why", "painting", "quote", "outside_time", "not_in_sources", "off_topic"}
DECLINE_TYPES = {"outside_time", "not_in_sources", "off_topic"}

def normalize(text):
    """Lowercase, fold accents and quotes, and keep only letters, digits and spaces."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())

def load_chunks(persona_id):
    path = config.chunks_path(persona_id)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run: python scripts/build_corpus.py --persona {persona_id}")
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]

def question_files():
    return sorted(QUESTIONS_DIR.glob("*.jsonl"))

def load_questions(persona_id):
    path = QUESTIONS_DIR / f"{persona_id}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"No question file at {path}")
    questions = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            q = json.loads(line)
            for key in ("id", "question", "type", "answerable", "gold_answer", "key_facts", "evidence"):
                if key not in q:
                    raise ValueError(f"{path}:{number} is missing '{key}'")
            if q["type"] not in QUESTION_TYPES:
                raise ValueError(f"{path}:{number} has unknown type {q['type']!r}")
            if q["answerable"] == (q["type"] in DECLINE_TYPES):
                raise ValueError(f"{path}:{number}: type {q['type']!r} does not match answerable={q['answerable']}")
            questions.append(q)
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} has duplicate question ids")
    return questions

def supporting_chunk_ids(question, chunks):
    """Ids of passages that contain any of the question's evidence text."""
    targets = [normalize(e) for e in question.get("evidence", []) if e.strip()]
    if not targets:
        return set()
    return {c["id"] for c in chunks if any(t in normalize(c["text"]) for t in targets)}

def key_facts_present(text, key_facts):
    """True if every group of key facts has at least one alternative in the text."""
    norm = normalize(text)
    return all(any(normalize(alt) in norm for alt in group) for group in key_facts)

def check(persona_id):
    """Report problems with one exhibit's question file. Returns the number of problems."""
    chunks = load_chunks(persona_id)
    questions = load_questions(persona_id)
    problems = 0
    for q in questions:
        if not q["answerable"]:
            continue
        support = supporting_chunk_ids(q, chunks)
        if not support:
            print(f"  {q['id']}: evidence not found in any passage")
            problems += 1
            continue
        support_text = " ".join(c["text"] for c in chunks if c["id"] in support)
        if not key_facts_present(support_text, q["key_facts"]):
            print(f"  {q['id']}: key facts are not all in the supporting passages")
            problems += 1
        if not key_facts_present(q["gold_answer"], q["key_facts"]):
            print(f"  {q['id']}: key facts are not all in the gold answer")
            problems += 1
    counts = {}
    for q in questions:
        counts[q["type"]] = counts.get(q["type"], 0) + 1
    answerable = sum(q["answerable"] for q in questions)
    print(f"{persona_id}: {len(questions)} questions ({answerable} answerable, "
          f"{len(questions) - answerable} traps) {counts}, problems: {problems}")
    return problems

def main():
    parser = argparse.ArgumentParser(description="Check the held-out question files.")
    parser.add_argument("--check", action="store_true", help="check every question file")
    parser.add_argument("--persona", help="check only this exhibit")
    args = parser.parse_args()
    ids = [args.persona] if args.persona else [p.stem for p in question_files()]
    total = sum(check(pid) for pid in ids)
    sys.exit(1 if total else 0)

if __name__ == "__main__":
    main()