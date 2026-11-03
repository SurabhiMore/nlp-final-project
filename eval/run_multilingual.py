"""Run multilingual evaluation questions through the live /ask endpoint.

Usage:
    python -m eval.run_multilingual

Reads eval/questions/multilingual/van-gogh.jsonl, POSTs each question to the
running /ask endpoint (default http://localhost:8000), collects the JSON
responses, writes the full replies to eval/results/multilingual_replies.json,
and prints a results table. Set ASK_URL to override the base URL.

The script mirrors exactly what a visitor does: it sends the raw non-English
question to /ask, which calls translate_for_search internally before BM25 and
then passes the original question to the LLM.  TOP_K matches the server default
(8), so the retrieval numbers in the results table reflect real behaviour.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests as http

# Ensure repo root is on path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

QUESTIONS_FILE = Path(__file__).parent / "questions" / "multilingual" / "van-gogh.jsonl"
REPLIES_FILE   = Path(__file__).parent / "results" / "multilingual_replies.json"
PERSONA_ID     = "van-gogh"
TOP_K          = 8                   # must match server TOP_K (app/server.py default)
BASE_URL       = os.getenv("ASK_URL", "http://localhost:8000")

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


def ask(question):
    """POST one question to the live /ask endpoint and return the JSON body."""
    resp = http.post(
        f"{BASE_URL}/ask",
        data={"persona": PERSONA_ID, "text": question, "mode": "persona"},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()


def run():
    questions = []
    with open(QUESTIONS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    print(f"\nRunning {len(questions)} multilingual questions against /ask ({BASE_URL}) …\n")

    rows = []
    full_replies = []
    for q in questions:
        qid      = q["id"]
        expected = q["language"]
        question = q["question"]

        try:
            body = ask(question)
        except Exception as exc:
            print(f"[ERROR] {qid}: {exc}\n")
            continue

        full_replies.append({"id": qid, "question": question, "response": body})

        detected    = body.get("detected_language", "?")
        status      = body.get("status", "?")
        citations   = [c["id"] for c in body.get("citations", [])]
        answer_text = body.get("answer", "")
        script      = detect_script(answer_text)
        snippet     = answer_text[:90].replace("\n", " ")

        rows.append({
            "id": qid,
            "expected": expected,
            "detected": detected,
            "passages": len(body.get("citations", [])),
            "status": status,
            "citations": citations,
            "script": script,
            "snippet": snippet,
            "answer": answer_text,
        })
        ok      = "✅" if detected == expected else "❌"
        lang_ok = "✅" if (expected == "es" and "Latin" in script) or \
                          (expected in ("hi", "mr") and "Devanagari" in script) or \
                          (expected == "en" and script == "ASCII/English") else "❌"
        print(f"[{ok}] {qid:15s}  lang={detected}/{expected}  "
              f"passages={len(citations)}  script={script}  {lang_ok}")
        print(f"       answer   : {snippet}\n")
        time.sleep(0.5)   # be polite to rate limits

    # Save full replies
    REPLIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPLIES_FILE.write_text(
        json.dumps(full_replies, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nFull replies saved to {REPLIES_FILE.relative_to(Path(__file__).parent.parent)}\n")

    return rows


def make_table(rows):
    lines = [
        "| ID | Expected | Detected | Passages | Status | Citations | Script | Answer Snippet |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        cits = ", ".join(r["citations"]) if r["citations"] else "—"
        snippet = r["snippet"][:70].replace("|", "\\|")
        lines.append(
            f"| `{r['id']}` | `{r['expected']}` | `{r['detected']}` "
            f"| {r['passages']} | {r['status']} | {cits} "
            f"| {r['script']} | {snippet} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    rows = run()
    if not rows:
        print("No results.")
        sys.exit(1)

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
    print(f"Retrieval success (≥1 pass) : {retrieval_ok}/{len(rows)}")
    print(f"Spanish in Spanish script   : {es_script_ok}/{total_es}")
    print(f"Hindi in Devanagari         : {hi_script_ok}/{total_hi}")
    print(f"Marathi in Devanagari       : {mr_script_ok}/{total_mr}")
    print()
    print(make_table(rows))
