"""Re-run the T. rex multilingual questions through the pipeline directly.

This script bypasses the HTTP server and calls the pipeline in-process, so it
always uses the LLM configured in .env (LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL,
LLM_API_KEY) rather than whatever model a background server daemon may have
loaded.

Usage:
    python -m eval.rerun_trex_multilingual

Writes:
    eval/results/multilingual_replies_t-rex.json   (T. rex only)
    eval/results/multilingual_replies.json          (combined, all exhibits)

The combined file is rebuilt by merging multilingual_replies_van-gogh.json
(if it exists) with the fresh T. rex results, so Van Gogh data is preserved.
"""

import json
import sys
import time
from pathlib import Path

# Ensure the repo root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env before importing any pipeline modules so env-vars are set.
from pipeline.config import load_env  # noqa: E402
load_env(ROOT / ".env")

from pipeline import config, persona as persona_mod, retrieve  # noqa: E402

QUESTIONS_DIR = Path(__file__).parent / "questions" / "multilingual"
RESULTS_DIR   = Path(__file__).parent / "results"
TREX_FILE     = RESULTS_DIR / "multilingual_replies_t-rex.json"
COMBINED_FILE = RESULTS_DIR / "multilingual_replies.json"
TOP_K         = 8


def run_question(persona_id, question, top_k=TOP_K):
    """Run one question through retrieve → answer and return the response body."""
    translated = persona_mod.translate_for_search(question)
    chunks = retrieve.retrieve(persona_id, translated, k=top_k)
    result = persona_mod.answer(persona_id, question, chunks, mode="persona")
    # Build the same response shape the /ask endpoint returns.
    return {
        "request_id": "",           # not available in-process
        "persona": persona_id,
        "mode": result.get("mode", "persona"),
        "question": question,
        "detected_language": result.get("detected_language", "en"),
        "search_query": translated,
        "passages": len(chunks),
        "status": result.get("status", ""),
        "answer": result.get("answer", ""),
        "sentences": [s.strip() for s in result.get("answer", "").split(".") if s.strip()],
        "citations": [
            {
                "id": cid,
                "source": next((c.get("source", "") for c in chunks if c["id"] == cid), ""),
                "url": next((c.get("url", "") for c in chunks if c["id"] == cid), ""),
                "licence": next((c.get("licence", "") for c in chunks if c["id"] == cid), ""),
                "snippet": next((c.get("text", "")[:220] for c in chunks if c["id"] == cid), ""),
            }
            for cid in result.get("citations", [])
        ],
        "sound": result.get("sound"),
        "audio": [],
        "timings": {
            "retrieval_ms": 0,
            "llm_ms": result.get("llm_ms", 0),
            "total_ms": result.get("llm_ms", 0),
        },
        "model": result.get("model", ""),
        "check": result.get("check"),
    }


def main():
    from pipeline.persona import model_label, settings as llm_settings
    s = llm_settings()
    print(f"\n{'='*60}")
    print(f"T. rex multilingual rerun")
    print(f"  LLM_PROVIDER : {s['provider']}")
    print(f"  LLM_MODEL    : {s['model'] or '(not set)'}")
    print(f"  LLM_BASE_URL : {s['base_url'] or '(not set)'}")
    if s["provider"] == "offline":
        print("\n  ⚠  LLM_PROVIDER=offline — answers will come from the offline stand-in,")
        print("     not from the real model. Set LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL,")
        print("     and LLM_API_KEY in .env to use the real model.")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}\n")

    q_path = QUESTIONS_DIR / "t-rex.jsonl"
    if not q_path.exists():
        print(f"[ERROR] Question file not found: {q_path}")
        sys.exit(1)

    questions = []
    with open(q_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    print(f"Running {len(questions)} T. rex multilingual questions …\n")

    full_replies = []
    for q in questions:
        qid      = q["id"]
        expected = q["language"]
        question = q["question"]

        print(f"[{qid}] ({expected}) {question[:70]}")
        t0 = time.perf_counter()
        try:
            body = run_question("t-rex", question)
        except Exception as exc:
            print(f"  ✗ ERROR: {exc}\n")
            continue
        elapsed = time.perf_counter() - t0

        full_replies.append({
            "id": qid,
            "persona": "t-rex",
            "question": question,
            "response": body,
        })

        status  = body.get("status", "?")
        answer  = body.get("answer", "")
        passages = body.get("passages", 0)
        model   = body.get("model", "")
        print(f"  status={status}  passages={passages}  llm_ms={body['timings']['llm_ms']}  "
              f"total={elapsed*1000:.0f}ms  model={model}")
        print(f"  answer: {answer[:100]}\n")

        time.sleep(0.5)  # polite rate-limit pause between calls

    # Save per-exhibit file.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TREX_FILE.write_text(
        json.dumps(full_replies, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"T. rex replies saved → {TREX_FILE.relative_to(ROOT)}")

    # Rebuild the combined file by merging all per-exhibit files on disk.
    combined = []
    for exhibit_file in sorted(RESULTS_DIR.glob("multilingual_replies_*.json")):
        combined.extend(json.loads(exhibit_file.read_text(encoding="utf-8")))
    COMBINED_FILE.write_text(
        json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Combined replies saved → {COMBINED_FILE.relative_to(ROOT)}")
    print(f"\nDone. {len(full_replies)} T. rex replies written.\n")


if __name__ == "__main__":
    main()
