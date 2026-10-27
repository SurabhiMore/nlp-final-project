"""Precision and recall of the time-boundary check (pipeline/timecheck.py).

    python -m eval.eval_timecheck                     # fills the Wikidata cache if needed
    python -m eval.eval_timecheck --offline           # cache only, no network
    python -m eval.eval_timecheck --answers eval/results/timecheck_answers.json

Questions checked, per exhibit with an end_year in persona.json:
  eval/questions/<exhibit>.jsonl            the existing set; label = type is "outside_time"
  eval/questions/timecheck/<exhibit>.jsonl  the new set; label = the "after_time" field

A false flag is a real question the check would block, so every one is listed.

With --answers (the output of eval_answers.py run on eval/questions/timecheck)
it also counts, per mode, how many after-time questions the model answered
anyway, and how many of those the check would have caught.

Outputs, in eval/results/:
  timecheck_results.json   every question, its label, the check's verdict and reasons
  timecheck_results.md     the same as tables
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval import datasets  # noqa: E402
from pipeline import config  # noqa: E402
from pipeline.timecheck import WikidataCache, check_time, end_year  # noqa: E402

RESULTS_DIR = config.EVAL_DIR / "results"
NEW_DIR = datasets.QUESTIONS_DIR / "timecheck"


def load_persona(persona_id):
    return json.loads((config.PERSONAS_DIR / persona_id / "persona.json").read_text(encoding="utf-8"))


def labelled_questions(persona_id):
    rows = []
    for q in datasets.load_questions(persona_id):
        rows.append({**q, "set": "existing", "after_time": q["type"] == "outside_time"})
    if (NEW_DIR / f"{persona_id}.jsonl").exists():
        for q in datasets.load_questions(persona_id, NEW_DIR):
            if "after_time" not in q:
                raise ValueError(f"{q['id']} in {NEW_DIR} needs an 'after_time' true/false field")
            rows.append({**q, "set": "new"})
    return rows


def scores(rows):
    tp = sum(r["after_time"] and r["flag"] for r in rows)
    fp = sum(not r["after_time"] and r["flag"] for r in rows)
    fn = sum(r["after_time"] and not r["flag"] for r in rows)
    tn = len(rows) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {"n": len(rows), "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall}


def model_summary(answers_path, checked):
    flags = {(r["exhibit"], r["id"]): r["flag"] for r in checked}
    labels = {(r["exhibit"], r["id"]): r["after_time"] for r in checked}
    out = {}
    for a in json.loads(Path(answers_path).read_text(encoding="utf-8"))["answers"]:
        key = (a["exhibit"], a["id"])
        if not labels.get(key):
            continue
        m = out.setdefault(a["mode"], {"after_time_questions": 0, "answered_anyway": 0,
                                        "answered_anyway_and_flagged": 0, "ids": []})
        m["after_time_questions"] += 1
        if a.get("status") == "answered":
            m["answered_anyway"] += 1
            m["ids"].append(a["id"])
            m["answered_anyway_and_flagged"] += bool(flags.get(key))
    return out


def fmt(x):
    return "n/a" if x is None else f"{x:.2f}"


def write_markdown(output, path):
    lines = ["# Time-boundary check", "", f"Run at {output['run_at']}. Command: `python -m eval.eval_timecheck"
             + (" --offline" if output["offline"] else "") + "`", "",
             "| exhibit / set | questions | flagged right | false flags | missed | precision | recall |",
             "|---|---|---|---|---|---|---|"]
    for name, s in output["summary"].items():
        lines.append(f"| {name} | {s['n']} | {s['tp']} | {s['fp']} | {s['fn']} | {fmt(s['precision'])} | {fmt(s['recall'])} |")
    for title, wanted in (("False flags (real questions the check would block)", (False, True)),
                          ("Missed after-time questions", (True, False))):
        lines += ["", f"## {title}", ""]
        hits = [r for r in output["questions"] if (r["after_time"], r["flag"]) == wanted]
        lines += [f"- `{r['id']}` {r['question']} — {'; '.join(r['reasons']) or 'no reason'}" for r in hits] or ["None."]
    if output.get("model"):
        lines += ["", "## The model on the new questions", "",
                  "| mode | after-time questions | answered anyway | of those, flagged by the check |", "|---|---|---|---|"]
        for mode, m in output["model"].items():
            lines.append(f"| {mode} | {m['after_time_questions']} | {m['answered_anyway']} | {m['answered_anyway_and_flagged']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Precision and recall of the time-boundary check.")
    parser.add_argument("--offline", action="store_true", help="use the Wikidata cache only")
    parser.add_argument("--answers", help="eval_answers.py results on the new questions")
    args = parser.parse_args()

    cache = WikidataCache(offline=args.offline)
    checked, skipped = [], []
    for path in datasets.question_files():
        persona_id = path.stem
        persona = load_persona(persona_id)
        if end_year(persona) is None:
            skipped.append(persona_id)
            continue
        for q in labelled_questions(persona_id):
            verdict = check_time(q["question"], persona, cache)
            checked.append({"exhibit": persona_id, "id": q["id"], "set": q["set"], "question": q["question"],
                            "after_time": q["after_time"], "flag": verdict["flag"], "reasons": verdict["reasons"],
                            "entities": verdict["entities"]})

    summary = {"all": scores(checked)}
    for key in sorted({(r["exhibit"], r["set"]) for r in checked}):
        summary["/".join(key)] = scores([r for r in checked if (r["exhibit"], r["set"]) == key])

    output = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "offline": args.offline,
              "skipped_exhibits": skipped, "cache": {"hits": cache.hits, "misses": cache.misses},
              "summary": summary, "questions": checked}
    if args.answers:
        output["model"] = model_summary(args.answers, checked)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "timecheck_results.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(output, RESULTS_DIR / "timecheck_results.md")
    for name, s in summary.items():
        print(f"{name:24} n={s['n']:3}  precision={fmt(s['precision'])}  recall={fmt(s['recall'])}  false flags={s['fp']}")
    print(f"cache hits {cache.hits}, misses {cache.misses}; skipped (no end_year): {', '.join(skipped) or 'none'}")
    if args.offline and cache.misses:
        print("Warning: some names were not in the cache and were treated as unknown. Run once without --offline.")


if __name__ == "__main__":
    main()
