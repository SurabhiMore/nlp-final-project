"""Compare the North Star (grounded answer accuracy) across Sessions 7, 8 and 10.

    python scripts/compare_north_star.py
    python scripts/compare_north_star.py --out eval/results/north_star_comparison.md

Sources:
  Session 7   openai/gpt-oss-120b. The 64-question results file was never committed,
              so only the numbers printed in reports/session07.md are known:
              grounded accuracy per exhibit and traps declined. Citations and
              decline rate are shown as "-".
  Session 8   llama3, eval/results/answers_results_session08_llama3.json
              (a copy of answers_results.json taken before the Session 10 rerun).
  Session 10  openai/gpt-oss-120b, eval/results/answers_results.json (issue #64).

Metrics, per exhibit and mode:
  grounded accuracy   correct answers / questions, as scored by eval_answers.py
  citations           mean number of citations per answered reply
  decline rate        share of all questions the guide declined
                      (not_in_sources, outside_time or declined)
  traps declined      trap questions correctly declined, out of all traps
  errors              calls that failed (a run with errors should not be reported)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
DECLINED = {"not_in_sources", "outside_time", "declined"}  # pipeline/persona.py DECLINED_STATUSES
EXHIBITS = ("van-gogh", "t-rex")
MODES = ("persona", "neutral")

# From reports/session07.md ("Metrics" section). Both modes scored 59 of 64, with 18 of 18 traps declined.
SESSION7 = {
    "label": "Session 7", "model": "openai/gpt-oss-120b", "source": "reports/session07.md",
    "cells": {
        (exhibit, mode): {"correct": correct, "questions": 32, "citations": None, "decline_rate": None,
                          "traps_declined": 9, "traps": 9, "errors": 0}
        for mode in MODES
        for exhibit, correct in (("van-gogh", 31), ("t-rex", 28))
    },
}


def cell_from_rows(rows):
    """Metrics for one exhibit and mode from eval_answers.py answer rows."""
    if not rows:
        return None
    answered = [r for r in rows if r["status"] == "answered"]
    traps = [r for r in rows if not r["answerable"]]
    return {
        "correct": sum(1 for r in rows if r["grounded"]),
        "questions": len(rows),
        "citations": round(sum(len(r["citations"] or []) for r in answered) / len(answered), 2) if answered else None,
        "decline_rate": round(sum(1 for r in rows if r["status"] in DECLINED) / len(rows), 3),
        "traps_declined": sum(1 for r in traps if r["correct"]),
        "traps": len(traps),
        "errors": sum(1 for r in rows if r["status"] == "error"),
    }


def load_run(path, label):
    path = Path(path)
    if not path.exists():
        sys.exit(f"{path} is missing. See the docstring at the top of this script for where it comes from.")
    data = json.loads(path.read_text(encoding="utf-8"))
    cells = {}
    for exhibit in EXHIBITS:
        for mode in MODES:
            rows = [r for r in data["answers"] if r["exhibit"] == exhibit and r["mode"] == mode]
            cell = cell_from_rows(rows)
            if cell:
                cells[(exhibit, mode)] = cell
    try:
        source = str(path.resolve().relative_to(ROOT))
    except ValueError:
        source = str(path)
    return {"label": label, "model": data.get("model", "?"), "source": source,
            "run_at": data.get("run_at"), "cells": cells}


def combine(cells):
    """Both exhibits together for one mode."""
    if not cells:
        return None
    total = {"correct": 0, "questions": 0, "traps_declined": 0, "traps": 0, "errors": 0}
    for c in cells:
        for key in total:
            total[key] += c[key]
    # Means cannot be combined without the counts behind them, so recompute only when every part has them.
    known = all(c["citations"] is not None and c["decline_rate"] is not None for c in cells)
    total["citations"] = round(sum(c["citations"] for c in cells) / len(cells), 2) if known else None
    total["decline_rate"] = (round(sum(c["decline_rate"] * c["questions"] for c in cells) / total["questions"], 3)
                             if known else None)
    return total


def fmt_cell(c):
    if c is None:
        return ["not run"] * 5
    acc = c["correct"] / c["questions"]
    return [
        f"{acc:.3f} ({c['correct']}/{c['questions']})",
        "-" if c["citations"] is None else f"{c['citations']:.2f}",
        "-" if c["decline_rate"] is None else f"{c['decline_rate']:.3f}",
        f"{c['traps_declined']}/{c['traps']}",
        str(c["errors"]),
    ]


def table(runs):
    lines = ["| Session | Model | Mode | Exhibit | Grounded accuracy | Citations per answer | Decline rate "
             "| Traps declined | Errors |",
             "|---|---|---|---|---|---|---|---|---|"]
    for mode in MODES:
        for run in runs:
            parts = [(exhibit, run["cells"].get((exhibit, mode))) for exhibit in EXHIBITS]
            present = [c for _, c in parts if c]
            for exhibit, c in parts + [("all", combine(present) if len(present) == len(EXHIBITS) else None)]:
                if c is None and not present:
                    continue  # this mode was not run in this session
                lines.append("| " + " | ".join([run["label"], run["model"], mode, exhibit, *fmt_cell(c)]) + " |")
    return "\n".join(lines)


def frontmatter(latest, previous):
    """The north_star block for the weekly report, persona mode, as in reports/session0*.md."""
    def value(run):
        cells = run["cells"]
        vg, tr = cells.get(("van-gogh", "persona")), cells.get(("t-rex", "persona"))
        if not (vg and tr):
            return "persona mode not run"
        all_ = combine([vg, tr])
        return (f"Van Gogh {vg['correct'] / vg['questions']:.3f}, T. rex {tr['correct'] / tr['questions']:.3f} "
                f"({all_['correct']} of {all_['questions']} overall), model {run['model']}")
    return ("north_star:\n"
            "  metric: Grounded answer accuracy (persona mode, 32 held-out questions per exhibit)\n"
            f"  value: {value(latest)}\n"
            f"  previous: {value(previous)} ({previous['label']}; same model, so like-for-like)")


def main():
    parser = argparse.ArgumentParser(description="North Star comparison across Sessions 7, 8 and 10.")
    parser.add_argument("--session8", default=RESULTS / "answers_results_session08_llama3.json")
    parser.add_argument("--session10", default=RESULTS / "answers_results.json")
    parser.add_argument("--out", help="also write the markdown to this file")
    args = parser.parse_args()

    s8 = load_run(args.session8, "Session 8")
    s10 = load_run(args.session10, "Session 10")
    if s10["model"] != SESSION7["model"]:
        print(f"WARNING: Session 10 results were made with {s10['model']}, not {SESSION7['model']}, "
              "so the comparison with Session 7 is not like-for-like.", file=sys.stderr)
    if any(c["errors"] for c in s10["cells"].values()):
        print("WARNING: the Session 10 run has failed calls. Finish it with "
              "python -m eval.eval_answers --resume before reporting.", file=sys.stderr)

    runs = [SESSION7, s8, s10]
    sources = "\n".join(f"- {r['label']}: {r['model']}, `{r['source']}`"
                        + (f" (run {r['run_at']})" if r.get("run_at") else "") for r in runs)
    text = (f"## North Star across sessions\n\n{table(runs)}\n\n"
            "Session 7 citations and decline rate are not known: its results file was never committed.\n\n"
            f"Sources:\n{sources}\n\n"
            f"Report frontmatter:\n\n```yaml\n{frontmatter(s10, SESSION7)}\n```\n")
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Saved {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
