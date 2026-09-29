"""Grounded answer accuracy: the persona against the plain museum guide.

    python -m eval.eval_answers                       # both exhibits, both modes
    python -m eval.eval_answers --persona t-rex --limit 5
    python -m eval.eval_answers --sleep 20            # pause between calls on a free tier
    python -m eval.eval_answers --resume              # continue a run that was stopped
    python -m eval.eval_answers --score-handcheck eval/results/handcheck.csv

For every held-out question we search the exhibit's passages, then ask the
answer engine in "persona" mode and in "neutral" mode. A question counts as
correct when:

  answerable question  status is "answered", every key fact is in the answer,
                       and it cites at least one passage that supports it
                       (a passage containing the evidence or the key facts)
  trap question        the guide declines (status "not_in_sources",
                       "outside_time" or "declined")

Grounded answer accuracy (our north-star metric) is the share of all questions
answered correctly in this sense. The automatic check is strict and simple, so
we also hand-label a random sample (handcheck.csv) and measure how often the
automatic check agrees with us.

Outputs, in eval/results/:
  answers_results.json   every answer, its score, and the summary
  handcheck.csv          a random sample to label by hand

Every answer is also saved to answers_progress.jsonl as soon as it arrives. If a
free tier's daily limit stops the run, the same command with --resume skips the
answers already saved (same model and settings only) and finishes the rest, for
example later or with a teammate's key for the same LLM_MODEL. The progress
file is deleted once a run finishes with no failed calls.
"""

import argparse
import csv
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval import datasets  # noqa: E402
from pipeline import config, persona as engine  # noqa: E402
from pipeline.retrieve import retrieve  # noqa: E402

RESULTS_DIR = config.EVAL_DIR / "results"
PROGRESS_PATH = RESULTS_DIR / "answers_progress.jsonl"
# Same setting as the server, so we measure what the product actually does.
TOP_K = int(os.getenv("TOP_K", "8"))
HUMAN_LABELS = ("grounded", "partial", "hallucinated", "declined_ok", "declined_wrong")


def score(question, result, chunks_by_id, support_ids):
    cited = [cid for cid in result["citations"] if cid in chunks_by_id]
    if not question["answerable"]:
        correct = result["status"] in engine.DECLINED_STATUSES
        return {"correct": correct, "grounded": correct, "facts_in_answer": None, "backed_by_citation": None}
    facts = datasets.key_facts_present(result["answer"], question["key_facts"])
    cited_text = " ".join(chunks_by_id[cid]["text"] for cid in cited)
    backed = bool(cited) and (
        bool(set(cited) & support_ids) or datasets.key_facts_present(cited_text, question["key_facts"]))
    correct = result["status"] == "answered" and facts
    return {"correct": correct, "grounded": correct and backed,
            "facts_in_answer": facts, "backed_by_citation": backed}


def summarize(rows):
    n = len(rows)
    answerable = [r for r in rows if r["answerable"]]
    traps = [r for r in rows if not r["answerable"]]

    def share(items, key):
        return round(sum(1 for r in items if r[key]) / len(items), 3) if items else None

    times = [r["llm_ms"] for r in rows if r["status"] != "error"]
    return {
        "questions": n,
        "grounded_accuracy": share(rows, "grounded"),
        "answerable_questions": len(answerable),
        "answer_accuracy": share(answerable, "correct"),
        "grounded_on_answerable": share(answerable, "grounded"),
        "trap_questions": len(traps),
        "decline_accuracy": share(traps, "correct"),
        "answered_without_citation": sum(1 for r in rows if r["status"] == "answered" and not r["citations"]),
        "invalid_citations": sum(len(r.get("invalid_citations") or []) for r in rows),
        "errors": sum(1 for r in rows if r["status"] == "error"),
        "median_llm_ms": round(statistics.median(times)) if times else None,
    }


def load_progress():
    """Answers saved by an earlier run with the same model and settings, keyed by question and mode."""
    done = {}
    if not PROGRESS_PATH.exists():
        return done
    with open(PROGRESS_PATH, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("model") == engine.model_label() and row.get("passages_per_question") == TOP_K:
                done[(row["exhibit"], row["mode"], row["question_id"])] = row
    return done


def save_progress(row):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_PATH, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(persona_ids, modes, limit=None, sleep=0.0, done=None):
    done = done or {}
    rows = []
    failures_in_a_row = 0
    for persona_id in persona_ids:
        chunks = datasets.load_chunks(persona_id)
        chunks_by_id = {c["id"]: c for c in chunks}
        questions = datasets.load_questions(persona_id)[:limit]
        for q in questions:
            retrieved = retrieve(persona_id, q["question"], k=TOP_K)
            support = datasets.supporting_chunk_ids(q, chunks)
            for mode in modes:
                if (persona_id, mode, q["id"]) in done:
                    rows.append(done[(persona_id, mode, q["id"])])
                    continue
                try:
                    result = engine.answer(persona_id, q["question"], retrieved, mode=mode)
                except Exception as error:  # one failed call should not end a long run
                    result = {"answer": "", "status": "error", "citations": [], "model": engine.model_label(),
                              "llm_ms": 0, "warning": f"{type(error).__name__}: {error}"[:300]}
                    failures_in_a_row += 1
                    if failures_in_a_row >= 3:
                        saved = sum(1 for r in rows if r["status"] != "error")
                        sys.exit(f"Stopped: 3 calls in a row failed. {saved} answers are saved; run the same "
                                 f"command with --resume to finish the rest (later, or with a teammate's key "
                                 f"and the same LLM_MODEL). Last error: {result['warning']}")
                else:
                    failures_in_a_row = 0
                row = {
                    "exhibit": persona_id, "mode": mode, "question_id": q["id"],
                    "question": q["question"], "type": q["type"], "answerable": q["answerable"],
                    "gold_answer": q["gold_answer"],
                    "retrieved": [c["id"] for c in retrieved],
                    "support_in_retrieved": bool(support & {c["id"] for c in retrieved}),
                    **{k: result.get(k) for k in ("answer", "status", "citations", "invalid_citations",
                                                  "model", "llm_ms", "warning", "parse_error")},
                    "passages_per_question": TOP_K,
                }
                row.update(score(q, result, chunks_by_id, support))
                rows.append(row)
                if row["status"] != "error":
                    save_progress(row)
                mark = "ok " if row["grounded"] else "MISS"
                shown = result["answer"][:70] or result.get("warning", "")[:70]
                print(f"  {mark} {persona_id:9} {mode:8} {q['id']:6} {result['status']:15} {shown}", flush=True)
                if sleep:
                    time.sleep(sleep)
    return rows


def has_labels(path):
    if not path.exists():
        return False
    with open(path, encoding="utf-8-sig") as handle:
        return any((r.get("human_label") or "").strip() for r in csv.DictReader(handle))


def write_handcheck(rows, size, path):
    """A random sample to label by hand, with the text of the cited passages next to each answer."""
    rng = random.Random(7)
    sample = rng.sample(rows, min(size, len(rows)))
    texts = {}
    for exhibit in {r["exhibit"] for r in sample}:
        texts.update({c["id"]: c["text"] for c in datasets.load_chunks(exhibit)})
    fields = ["exhibit", "mode", "question_id", "question", "gold_answer", "answer", "status",
              "citations", "cited_passages", "auto_correct", "auto_grounded", "human_label", "notes"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in sample:
            cited = r["citations"] or []
            writer.writerow({
                "exhibit": r["exhibit"], "mode": r["mode"], "question_id": r["question_id"],
                "question": r["question"], "gold_answer": r["gold_answer"], "answer": r["answer"],
                "status": r["status"], "citations": " ".join(cited),
                "cited_passages": " | ".join(f"[{cid}] {texts.get(cid, '')}" for cid in cited),
                "auto_correct": r["correct"], "auto_grounded": r["grounded"],
                "human_label": "", "notes": "",
            })


def score_handcheck(path):
    """Compare hand labels with the automatic check: agreement and Cohen's kappa."""
    # utf-8-sig and the lower() below cope with files saved from Excel.
    with open(path, encoding="utf-8-sig") as handle:
        rows = [r for r in csv.DictReader(handle) if (r.get("human_label") or "").strip()]
    bad = [r["human_label"] for r in rows if r["human_label"].strip() not in HUMAN_LABELS]
    if bad:
        sys.exit(f"Unknown labels {sorted(set(bad))}. Use one of: {', '.join(HUMAN_LABELS)}")
    if not rows:
        sys.exit("No rows have a human_label yet.")
    pairs = [(r["auto_grounded"].strip().lower() == "true", r["human_label"].strip() in ("grounded", "declined_ok"))
             for r in rows]
    n = len(pairs)
    agree = sum(a == h for a, h in pairs) / n
    p_auto = sum(a for a, _ in pairs) / n
    p_human = sum(h for _, h in pairs) / n
    expected = p_auto * p_human + (1 - p_auto) * (1 - p_human)
    kappa = (agree - expected) / (1 - expected) if expected < 1 else 1.0
    print(f"Hand-checked rows: {n}")
    print(f"Automatic check agrees with the hand labels on {agree:.0%} of rows (Cohen's kappa {kappa:.2f})")
    print(f"Accuracy by hand labels: {p_human:.0%}   by the automatic check: {p_auto:.0%}")


def main():
    parser = argparse.ArgumentParser(description="Grounded answer accuracy, persona vs neutral guide.")
    parser.add_argument("--persona", help="only this exhibit")
    parser.add_argument("--modes", default="persona,neutral", help="comma-separated: persona,neutral")
    parser.add_argument("--limit", type=int, help="only the first N questions per exhibit")
    parser.add_argument("--sleep", type=float, default=0.0, help="seconds to wait between calls")
    parser.add_argument("--handcheck", type=int, default=20, help="rows to sample for hand labelling")
    parser.add_argument("--score-handcheck", metavar="CSV", help="score a labelled handcheck file and exit")
    parser.add_argument("--resume", action="store_true", help="keep answers saved by a stopped run")
    args = parser.parse_args()

    if args.score_handcheck:
        score_handcheck(args.score_handcheck)
        return

    settings = engine.settings()
    if settings["provider"] != "offline" and not (settings["base_url"] and settings["model"]):
        sys.exit("No language model configured. Set LLM_BASE_URL and LLM_MODEL in .env (see .env.example).")

    persona_ids = [args.persona] if args.persona else [p.stem for p in datasets.question_files()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    print(f"Model: {engine.model_label()}   passages per question: {TOP_K}", flush=True)
    if args.resume:
        done = load_progress()
        print(f"Resuming: {len(done)} answers already saved for this model.", flush=True)
    else:
        done = {}
        PROGRESS_PATH.unlink(missing_ok=True)
    rows = run(persona_ids, modes, args.limit, args.sleep, done)

    summary = {}
    for persona_id in persona_ids:
        for mode in modes:
            subset = [r for r in rows if r["exhibit"] == persona_id and r["mode"] == mode]
            summary[f"{persona_id}/{mode}"] = summarize(subset)
    for mode in modes:
        summary[f"all/{mode}"] = summarize([r for r in rows if r["mode"] == mode])

    print(f"\n{'':20} {'grounded acc':>12} {'answerable':>11} {'traps':>7} {'no cite':>8} {'errors':>7}")
    def cell(value, width):
        return f"{value:>{width}.2f}" if value is not None else f"{'-':>{width}}"

    for key, row in summary.items():
        print(f"{key:20} {cell(row['grounded_accuracy'], 12)} {cell(row['grounded_on_answerable'], 11)} "
              f"{cell(row['decline_accuracy'], 7)} {row['answered_without_citation']:>8} {row['errors']:>7}")
    failed = sum(1 for r in rows if r["status"] == "error")
    if failed:
        print(f"\nWarning: {failed} calls failed and were scored as wrong. Run again with --resume to retry "
              "just those before reporting these numbers.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": engine.model_label(), "passages_per_question": TOP_K,
        "summary": summary, "answers": rows,
    }
    results_path = RESULTS_DIR / "answers_results.json"
    results_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    handcheck_path = RESULTS_DIR / "handcheck.csv"
    if has_labels(handcheck_path):
        # Never overwrite labels someone has already typed in.
        handcheck_path = RESULTS_DIR / "handcheck_new.csv"
        print("\nhandcheck.csv already has hand labels, so the new sample goes to handcheck_new.csv.")
    write_handcheck(rows, args.handcheck, handcheck_path)
    if not failed:
        PROGRESS_PATH.unlink(missing_ok=True)
    print(f"\nSaved {results_path.relative_to(config.ROOT)} and {handcheck_path.relative_to(config.ROOT)}")
    print("Label the handcheck file (human_label column), then run with --score-handcheck.")


if __name__ == "__main__":
    main()
