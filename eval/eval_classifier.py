"""Does the question classifier block only what it should?

    python -m eval.eval_classifier

Uses no language model and no network. Blocking a real question is the worst mistake, so
the first thing it reports is false blocks, which must be zero, on:

  - the answerable questions in eval/questions/
  - the questions in eval/questions/heldout/
  - the inside-time questions in eval/questions/timecheck/
  - the real questions in the user test logs, apart from the ones the model declined as off topic

It then reports:

  - the catch rate on the off-topic and after-time traps. not_in_sources traps are left out,
    because only search can spot them. Misses are harmless: the model declines them anyway
  - accuracy on the held-out set in eval/questions/classifier/ (see the README there)
  - how many language model calls it would have saved on the user test logs

Results are saved to eval/results/classifier_results.json and classifier_results.md.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval import datasets  # noqa: E402
from pipeline import classifier, config  # noqa: E402

RESULTS_DIR = config.EVAL_DIR / "results"
EVIDENCE_DIR = config.ROOT / "artifacts" / "evidence"
TIMECHECK_DIR = datasets.QUESTIONS_DIR / "timecheck"
HELD_OUT_DIR = datasets.QUESTIONS_DIR / "classifier"
LABELS = (classifier.IN_DOMAIN, classifier.OFF_TOPIC, classifier.OUT_OF_TIME)


def _questions(questions_dir=None):
    """Every question in a folder, with the exhibit it belongs to."""
    rows = []
    for path in datasets.question_files(questions_dir):
        for q in datasets.load_questions(path.stem, questions_dir):
            rows.append({**q, "exhibit": path.stem})
    return rows


def log_rows(evidence_dir=EVIDENCE_DIR):
    """Every question from the user test logs."""
    rows = []
    for path in sorted(Path(evidence_dir).glob("session*/*_log.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows.append({"exhibit": r["persona"], "id": path.parent.name, "question": r["question"],
                             "status": r["status"], "llm_ms": r.get("timings", {}).get("llm_ms", 0)})
    return rows


def must_pass_sets():
    """The questions that must never be blocked, by set."""
    return {
        "Answerable questions in eval/questions/": [q for q in _questions() if q["answerable"]],
        "Questions in eval/questions/heldout/": _questions(datasets.HELDOUT_DIR),
        "Inside-time questions in eval/questions/timecheck/": [q for q in _questions(TIMECHECK_DIR)
                                                               if not q["after_time"]],
        "User test questions the model did not decline as off topic": [r for r in log_rows()
                                                                       if r["status"] != "declined"],
    }


def trap_sets():
    """The questions it should catch where it can, by set."""
    main = _questions()
    return {
        "Off-topic traps in eval/questions/": [q for q in main if q["type"] == "off_topic"],
        "After-time traps in eval/questions/": [q for q in main if q["type"] == "outside_time"],
        "After-time questions in eval/questions/timecheck/": [q for q in _questions(TIMECHECK_DIR) if q["after_time"]],
    }


def load_held_out(questions_dir=HELD_OUT_DIR):
    """The labelled held-out questions. Raises ValueError on a missing field, a wrong label or a repeated id."""
    rows, seen = [], set()
    for path in sorted(Path(questions_dir).glob("*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            q = json.loads(line)
            for key in ("id", "question", "expected", "category"):
                if not q.get(key):
                    raise ValueError(f"{path}:{number} is missing '{key}'")
            if q["expected"] not in LABELS:
                raise ValueError(f"{path}:{number}: expected must be one of {LABELS}")
            if q["id"] in seen:
                raise ValueError(f"{path}:{number}: repeated id {q['id']}")
            seen.add(q["id"])
            rows.append({**q, "exhibit": path.stem})
    return rows


def _label(row, personas):
    return classifier.classify(row["question"], personas[row["exhibit"]])


def _entry(row, decision):
    return {"exhibit": row["exhibit"], "id": row["id"], "question": row["question"], **decision}


def evaluate_held_out(rows, personas):
    confusion = {expected: {label: 0 for label in LABELS} for expected in LABELS}
    by_category, wrong = {}, []
    for row in rows:
        decision = _label(row, personas)
        confusion[row["expected"]][decision["label"]] += 1
        right = decision["label"] == row["expected"]
        counts = by_category.setdefault(f"{row['expected']}: {row['category']}", {"questions": 0, "right": 0})
        counts["questions"] += 1
        counts["right"] += right
        if not right:
            wrong.append({**_entry(row, decision), "expected": row["expected"], "category": row["category"]})
    right = sum(confusion[label][label] for label in LABELS)
    return {"questions": len(rows), "right": right, "accuracy": round(right / len(rows), 3) if rows else None,
            "confusion": confusion, "by_category": by_category, "wrong": wrong}


def run(held_out_dir=HELD_OUT_DIR):
    personas = {p.stem: config.load_persona(p.stem) for p in datasets.question_files()}

    must_pass, false_blocks = {}, []
    for name, rows in must_pass_sets().items():
        decisions = [(row, _label(row, personas)) for row in rows]
        blocked = [_entry(row, d) | {"set": name} for row, d in decisions if d["label"] != classifier.IN_DOMAIN]
        must_pass[name] = {"questions": len(rows), "blocked": len(blocked)}
        false_blocks += blocked

    catch, misses = {}, []
    for name, rows in trap_sets().items():
        decisions = [(row, _label(row, personas)) for row in rows]
        missed = [_entry(row, d) | {"set": name} for row, d in decisions if d["label"] == classifier.IN_DOMAIN]
        catch[name] = {"questions": len(rows), "caught": len(rows) - len(missed)}
        misses += missed

    source_traps = [q for q in _questions() if q["type"] == "not_in_sources"]
    source_traps_blocked = [_entry(q, _label(q, personas)) for q in source_traps
                            if _label(q, personas)["label"] != classifier.IN_DOMAIN]

    logs = log_rows()
    saved = [r for r in logs if _label(r, personas)["label"] != classifier.IN_DOMAIN]
    return {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "must_pass": must_pass,
        "false_blocks": false_blocks,
        "catch": catch,
        "misses": misses,
        "not_in_sources_traps": len(source_traps),
        "not_in_sources_traps_blocked": source_traps_blocked,
        "held_out": evaluate_held_out(load_held_out(held_out_dir), personas),
        "user_test_logs": {
            "questions": len(logs),
            "llm_calls_saved": len(saved),
            "llm_ms_saved": sum(r["llm_ms"] for r in saved),
            "questions_saved": [r["question"] for r in saved],
        },
    }


def _question_table(rows, extra=None):
    extra = extra or []
    lines = ["| Exhibit | Id | Question | " + " | ".join(title for title, _ in extra) + (" | " if extra else "") + "Why |",
             "|---|---|---|" + "---|" * (len(extra) + 1)]
    for r in rows:
        cells = "".join(f"{r[key]} | " for _, key in extra)
        lines.append(f"| {r['exhibit']} | {r['id']} | {r['question']} | {cells}{r['reason']} |")
    return lines


def to_markdown(report):
    h = report["held_out"]
    logs = report["user_test_logs"]
    total_blocks = len(report["false_blocks"])
    lines = [
        "# Question classifier",
        "",
        f"Does `pipeline/classifier.py` block only what it should? Run on {report['run_at'][:10]} with "
        "`python -m eval.eval_classifier`. It uses a few rules, with no language model and no network.",
        "",
        "## False blocks (must be zero)",
        "",
        f"**{total_blocks} false blocks.**",
        "",
        "| Questions that must get through | Questions | Blocked |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | {v['questions']} | {v['blocked']} |" for name, v in report["must_pass"].items()]
    if report["false_blocks"]:
        lines += [""] + _question_table(report["false_blocks"], [("Set", "set")])

    lines += ["", "## Catch rate on traps", "", "| Traps | Questions | Caught |", "|---|---|---|"]
    lines += [f"| {name} | {v['questions']} | {v['caught']} |" for name, v in report["catch"].items()]
    lines += ["", f"`not_in_sources` traps are left out because only search can spot them: "
              f"{len(report['not_in_sources_traps_blocked'])} of the {report['not_in_sources_traps']} were blocked.",
              "", "Every miss. These go on to the language model, which is expected to decline them:", ""]
    lines += _question_table(report["misses"], [("Set", "set")])

    lines += ["", "## Held-out set", "", f"Accuracy: **{h['accuracy']:.3f}** ({h['right']} of {h['questions']}), on "
              "questions written before the rules (see `eval/questions/classifier/README.md`).", "",
              "| Expected \\ classifier said | " + " | ".join(LABELS) + " |", "|---|---|---|---|"]
    lines += [f"| {expected} | " + " | ".join(str(row[label]) for label in LABELS) + " |"
              for expected, row in h["confusion"].items()]
    lines += ["", "| Expected: kind | Questions | Right |", "|---|---|---|"]
    lines += [f"| {name} | {v['questions']} | {v['right']} |" for name, v in sorted(h["by_category"].items())]
    lines += ["", "Every wrong result:", ""]
    lines += _question_table(h["wrong"], [("Expected", "expected"), ("Classifier said", "label")]) if h["wrong"] else ["None."]

    lines += ["", "## Language model calls saved on the user test logs", "",
              f"{logs['llm_calls_saved']} of {logs['questions']} logged questions would have skipped the language model, "
              f"saving {logs['llm_ms_saved']} ms of model time in total: "
              + ", ".join(f'"{q}"' for q in logs["questions_saved"]) + ".",
              "", "## Limitations", "",
              "- The same person wrote the rules and the held-out questions, so the held-out result is weaker than one "
              "from a set written by someone else.",
              "- The rules cover five kinds of question and only in English. Anything else goes to the language model, "
              "which is the safe direction.",
              "- The year rule only sees years written as numbers, so it does not help with after-time questions that "
              "name no year. `pipeline/timecheck.py` is the check for those.",
              "- The user test logs are small, and some of their off-topic questions came from our own task sheet, so "
              "the saving says little about real visitors."]
    return "\n".join(lines) + "\n"


def write_outputs(report, out_dir=RESULTS_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / "classifier_results.json", out_dir / "classifier_results.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="Evaluate the question classifier.")
    parser.add_argument("--held-out", default=str(HELD_OUT_DIR), help="folder with the labelled held-out questions")
    parser.add_argument("--out-dir", default=str(RESULTS_DIR), help="where to save the results")
    args = parser.parse_args()
    try:
        report = run(args.held_out)
    except ValueError as error:
        sys.exit(str(error))
    h = report["held_out"]
    print(f"false blocks: {len(report['false_blocks'])} on {sum(v['questions'] for v in report['must_pass'].values())} "
          f"questions | traps caught: {sum(v['caught'] for v in report['catch'].values())} of "
          f"{sum(v['questions'] for v in report['catch'].values())} | held-out accuracy: {h['accuracy']} "
          f"({h['right']} of {h['questions']}) | LLM calls saved on the logs: "
          f"{report['user_test_logs']['llm_calls_saved']} of {report['user_test_logs']['questions']}")
    for path in write_outputs(report, args.out_dir):
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
