"""Run multilingual evaluation questions through the live /ask endpoint.

Usage:
    python -m eval.run_multilingual
    python -m eval.run_multilingual --persona van-gogh
    python -m eval.run_multilingual --persona t-rex
    python -m eval.run_multilingual --persona all

Reads eval/questions/multilingual/{persona}.jsonl, POSTs each question to the
running /ask endpoint (default http://localhost:8000), collects the JSON
responses, writes the full replies to eval/results/multilingual_replies.json,
and prints a results table. Set ASK_URL to override the base URL.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests as http

# Ensure repo root is on path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

QUESTIONS_DIR = Path(__file__).parent / "questions" / "multilingual"
REPLIES_FILE  = Path(__file__).parent / "results" / "multilingual_replies.json"
TOP_K         = 8                   # must match server TOP_K (app/server.py default)
BASE_URL      = os.getenv("ASK_URL", "http://localhost:8000")

LANG_NAMES = {"es": "Spanish", "hi": "Hindi", "mr": "Marathi", "en": "English", "kn": "Kannada"}

_client = None


def detect_script(text):
    """Heuristic: does the answer contain non-ASCII chars from Devanagari, Kannada, or Spanish range?"""
    devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    kannada    = sum(1 for c in text if "\u0C80" <= c <= "\u0CFF")
    latin_ext  = sum(1 for c in text if c in "áéíóúüñ¿¡àèìòù")
    if devanagari > 3:
        return "Devanagari"
    if kannada > 3:
        return "Kannada"
    if latin_ext > 0:
        return "Latin-extended (Spanish)"
    return "ASCII/English"


def ask(question, persona_id="van-gogh"):
    """POST one question to /ask and return the JSON body."""
    global _client
    try:
        resp = http.post(
            f"{BASE_URL}/ask",
            data={"persona": persona_id, "text": question, "mode": "persona"},
            timeout=90,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Fall back to in-process FastAPI TestClient if no server daemon is listening
        if _client is None:
            from fastapi.testclient import TestClient
            from app import server
            _client = TestClient(server.app)
        resp = _client.post(
            "/ask",
            data={"persona": persona_id, "text": question, "mode": "persona"},
        )
        resp.raise_for_status()
        return resp.json()


def run(persona_filter="all"):
    personas = ["van-gogh", "t-rex"] if persona_filter == "all" else [persona_filter]

    all_questions = []
    for pid in personas:
        q_path = QUESTIONS_DIR / f"{pid}.jsonl"
        if not q_path.exists():
            print(f"[WARN] Question file {q_path} not found, skipping.")
            continue
        with open(q_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    item["persona"] = pid
                    all_questions.append(item)

    print(f"\nRunning {len(all_questions)} multilingual questions across {personas} against /ask ({BASE_URL}) …\n")

    rows = []
    full_replies = []
    for q in all_questions:
        qid      = q["id"]
        pid      = q["persona"]
        expected = q["language"]
        question = q["question"]

        try:
            body = ask(question, persona_id=pid)
        except Exception as exc:
            print(f"[ERROR] {qid} ({pid}): {exc}\n")
            continue

        full_replies.append({"id": qid, "persona": pid, "question": question, "response": body})

        detected       = body.get("detected_language", "?")
        search_query   = body.get("search_query", "")
        passages_count = body.get("passages", len(body.get("citations", [])))
        status         = body.get("status", "?")
        citations      = [c["id"] for c in body.get("citations", [])]
        answer_text    = body.get("answer", "")
        script         = detect_script(answer_text)
        snippet        = answer_text[:90].replace("\n", " ")

        rows.append({
            "id": qid,
            "persona": pid,
            "expected": expected,
            "detected": detected,
            "search_query": search_query,
            "passages": passages_count,
            "status": status,
            "citations": citations,
            "script": script,
            "snippet": snippet,
            "answer": answer_text,
        })
        ok      = "✅" if detected == expected else "❌"
        lang_ok = "✅" if (expected == "es" and ("Latin" in script or script == "ASCII/English")) or \
                          (expected in ("hi", "mr") and "Devanagari" in script) or \
                          (expected == "kn" and "Kannada" in script) or \
                          (expected == "en" and script == "ASCII/English") else "❌"
        print(f"[{ok}] {qid:15s} ({pid:8s}) lang={detected}/{expected}  "
              f"passages={passages_count}  script={script}  {lang_ok}")
        print(f"       search_q : {search_query[:80]}")
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
        "| ID | Persona | Expected | Detected | Passages | Status | Citations | Script | Answer Snippet |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        cits = ", ".join(r["citations"]) if r["citations"] else "—"
        snippet = r["snippet"][:70].replace("|", "\\|")
        lines.append(
            f"| `{r['id']}` | `{r.get('persona', 'van-gogh')}` | `{r['expected']}` | `{r['detected']}` "
            f"| {r['passages']} | {r['status']} | {cits} "
            f"| {r['script']} | {snippet} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run multilingual evaluation against /ask")
    parser.add_argument("--persona", choices=["van-gogh", "t-rex", "all"], default="all",
                        help="Which exhibit to evaluate (default: all)")
    args = parser.parse_args()

    rows = run(persona_filter=args.persona)
    if not rows:
        print("No results.")
        sys.exit(1)

    # Summary
    lang_correct = sum(1 for r in rows if r["detected"] == r["expected"])
    es_script_ok = sum(1 for r in rows if r["expected"] == "es" and ("Latin" in r["script"] or r["script"] == "ASCII/English"))
    hi_script_ok = sum(1 for r in rows if r["expected"] == "hi" and "Devanagari" in r["script"])
    mr_script_ok = sum(1 for r in rows if r["expected"] == "mr" and "Devanagari" in r["script"])
    kn_script_ok = sum(1 for r in rows if r["expected"] == "kn" and "Kannada" in r["script"])

    total_es = sum(1 for r in rows if r["expected"] == "es")
    total_hi = sum(1 for r in rows if r["expected"] == "hi")
    total_mr = sum(1 for r in rows if r["expected"] == "mr")
    total_kn = sum(1 for r in rows if r["expected"] == "kn")
    retrieval_ok = sum(1 for r in rows if r["passages"] > 0)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Language detection accuracy : {lang_correct}/{len(rows)}")
    print(f"Retrieval success (≥1 pass) : {retrieval_ok}/{len(rows)}")
    if total_es:
        print(f"Spanish in Spanish script   : {es_script_ok}/{total_es}")
    if total_hi:
        print(f"Hindi in Devanagari         : {hi_script_ok}/{total_hi}")
    if total_mr:
        print(f"Marathi in Devanagari       : {mr_script_ok}/{total_mr}")
    if total_kn:
        print(f"Kannada in Kannada script   : {kn_script_ok}/{total_kn}")
    print()
    print(make_table(rows))
