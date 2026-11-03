"""Run multilingual evaluation questions directly through the pipeline.

Usage:
    python -m eval.run_multilingual

Reads eval/questions/multilingual/van-gogh.jsonl, calls translate_for_search
then retrieve then answer for each question, and prints a results table.
"""

import json
import sys
import time
from pathlib import Path

# Ensure repo root is on path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import persona as persona_mod, retrieve as retrieve_mod

QUESTIONS_FILE = Path(__file__).parent / "questions" / "multilingual" / "van-gogh.jsonl"
PERSONA_ID = "van-gogh"
TOP_K = 5

LANG_NAMES = {"es": "Spanish", "hi": "Hindi", "mr": "Marathi", "en": "English", "kn": "Kannada"}

def detect_script(text):
    """Heuristic: does the answer contain non-ASCII chars from a Devanagari/Spanish range?"""
    devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    latin_ext  = sum(1 for c in text if c in "áéíóúüñ¿¡àèìòù")
    if devanagari > 3:
        return "Devanagari"
    if latin_ext > 0:
        return "Latin-extended (Spanish)"
    return "ASCII/English"


def run():
    questions = []
    with open(QUESTIONS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    print(f"\nRunning {len(questions)} multilingual questions against persona '{PERSONA_ID}' …\n")

    rows = []
    for q in questions:
        qid      = q["id"]
        expected = q["language"]
        question = q["question"]

        # 1. Translate for BM25 search
        search_q = persona_mod.translate_for_search(question)

        # 2. Retrieve passages using the translated query
        chunks = retrieve_mod.retrieve(PERSONA_ID, search_q, k=TOP_K)

        # 3. Answer using the ORIGINAL non-English question
        result = persona_mod.answer(PERSONA_ID, question, chunks)

        detected  = result.get("detected_language", "?")
        status    = result.get("status", "?")
        citations = result.get("citations", [])
        answer_text = result.get("answer", "")
        script    = detect_script(answer_text)
        snippet   = answer_text[:90].replace("\n", " ")

        rows.append({
            "id": qid,
            "expected": expected,
            "detected": detected,
            "passages": len(chunks),
            "status": status,
            "citations": citations,
            "script": script,
            "snippet": snippet,
            "answer": answer_text,
            "search_q": search_q,
        })
        ok = "✅" if detected == expected else "❌"
        lang_ok = "✅" if (expected == "es" and "Latin" in script) or \
                          (expected in ("hi", "mr") and "Devanagari" in script) or \
                          (expected == "en" and script == "ASCII/English") else "❌"
        print(f"[{ok}] {qid:15s}  lang={detected}/{expected}  passages={len(chunks)}  script={script}  {lang_ok}")
        print(f"       search_q : {search_q[:80]}")
        print(f"       answer   : {snippet}\n")
        time.sleep(0.3)   # be polite to rate limits

    return rows


def make_table(rows):
    lines = [
        "| ID | Expected | Detected | Passages | Status | Citations | Script | Answer Snippet |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        cits = ", ".join(r["citations"]) if r["citations"] else "—"
        lines.append(
            f"| `{r['id']}` | `{r['expected']}` | `{r['detected']}` "
            f"| {r['passages']} | {r['status']} | {cits} "
            f"| {r['script']} | {r['snippet'][:70]} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    rows = run()

    # Summary
    lang_correct = sum(1 for r in rows if r["detected"] == r["expected"])
    es_script_ok = sum(1 for r in rows if r["expected"] == "es" and "Latin" in r["script"])
    hi_script_ok = sum(1 for r in rows if r["expected"] == "hi" and "Devanagari" in r["script"])
    mr_script_ok = sum(1 for r in rows if r["expected"] == "mr" and "Devanagari" in r["script"])
    total_es = sum(1 for r in rows if r["expected"] == "es")
    total_hi = sum(1 for r in rows if r["expected"] == "hi")
    total_mr = sum(1 for r in rows if r["expected"] == "mr")
    retrieval_ok = sum(1 for r in rows if r["passages"] > 0)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Language detection accuracy : {lang_correct}/{len(rows)}")
    print(f"Retrieval success           : {retrieval_ok}/{len(rows)}")
    print(f"Spanish in Spanish script   : {es_script_ok}/{total_es}")
    print(f"Hindi in Devanagari         : {hi_script_ok}/{total_hi}")
    print(f"Marathi in Devanagari       : {mr_script_ok}/{total_mr}")
    print()
    print(make_table(rows))

