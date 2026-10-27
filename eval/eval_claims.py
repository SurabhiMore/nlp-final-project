"""Evaluate the claim checker against labelled real and perturbed answers.

    python -m eval.eval_claims
    python -m eval.eval_claims --output eval/results/claims_results.md

Reports precision, recall, and F1 on real and perturbed answers separately,
confirms detection of Session 7 user test failures, and lists every miss
(false negative) and wrongly flagged answer (false positive).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval import datasets
from pipeline.claims import check_claims


def evaluate(labels_path: Path) -> dict:
    vg_chunks = {c["id"]: c for c in datasets.load_chunks("van-gogh")}
    tr_chunks = {c["id"]: c for c in datasets.load_chunks("t-rex")}

    rows = []
    with open(labels_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    results = []
    for r in rows:
        ex = r["exhibit"]
        chunks = vg_chunks if ex == "van-gogh" else tr_chunks
        cited = [chunks[cid] for cid in r.get("citations", []) if cid in chunks]
        flags = check_claims(r["answer"], cited)
        pred_unsupported = len(flags) > 0
        gold_unsupported = bool(r["has_unsupported"])

        if pred_unsupported and gold_unsupported:
            cat = "TP"
        elif pred_unsupported and not gold_unsupported:
            cat = "FP"
        elif not pred_unsupported and gold_unsupported:
            cat = "FN"
        else:
            cat = "TN"

        results.append({
            "row": r,
            "flags": flags,
            "cat": cat,
            "pred": pred_unsupported,
            "gold": gold_unsupported,
        })

    def _calc_metrics(subset):
        tp = sum(1 for item in subset if item["cat"] == "TP")
        fp = sum(1 for item in subset if item["cat"] == "FP")
        fn = sum(1 for item in subset if item["cat"] == "FN")
        tn = sum(1 for item in subset if item["cat"] == "TN")
        total = len(subset)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / total if total > 0 else 1.0
        return {
            "total": total,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "accuracy": round(accuracy, 3),
        }

    real = [res for res in results if not res["row"]["is_perturbed"]]
    pert = [res for res in results if res["row"]["is_perturbed"]]

    return {
        "real": _calc_metrics(real),
        "perturbed": _calc_metrics(pert),
        "overall": _calc_metrics(results),
        "details": results,
    }


def format_report(eval_data: dict) -> str:
    real_m = eval_data["real"]
    pert_m = eval_data["perturbed"]
    all_m = eval_data["overall"]
    details = eval_data["details"]

    false_flags = [d for d in details if d["cat"] == "FP"]
    misses = [d for d in details if d["cat"] == "FN"]

    session07_p2 = next((d for d in details if d["row"]["id"] == "session07-P2-q1"), None)
    session07_p4 = next((d for d in details if d["row"]["id"] == "session07-P4-q1"), None)

    p2_flagged = bool(session07_p2 and session07_p2["pred"])
    p4_flagged = bool(session07_p4 and session07_p4["pred"])

    lines = [
        "# Claim Checker Evaluation Results",
        "",
        "Evaluation of `pipeline/claims.py` against `eval/claims_labels.jsonl`.",
        "",
        "## Summary Metrics",
        "",
        "| Dataset Split | Answers | Unsupported (Gold) | Precision | Recall | F1 Score | Accuracy |",
        "|---|---|---|---|---|---|---|",
        f"| **Real answers** | {real_m['total']} | {real_m['tp'] + real_m['fn']} | **{real_m['precision']:.3f}** | **{real_m['recall']:.3f}** | **{real_m['f1']:.3f}** | **{real_m['accuracy']:.3f}** |",
        f"| **Perturbed answers** | {pert_m['total']} | {pert_m['tp'] + pert_m['fn']} | **{pert_m['precision']:.3f}** | **{pert_m['recall']:.3f}** | **{pert_m['f1']:.3f}** | **{pert_m['accuracy']:.3f}** |",
        f"| **Combined overall** | {all_m['total']} | {all_m['tp'] + all_m['fn']} | **{all_m['precision']:.3f}** | **{all_m['recall']:.3f}** | **{all_m['f1']:.3f}** | **{all_m['accuracy']:.3f}** |",
        "",
        "## Session 7 User Test Failures (Regression Test)",
        "",
        f"- **P2 ('Did you move to Arles?'):** Flagged = `{p2_flagged}` (Flags: `{session07_p2['flags'] if session07_p2 else []}`)",
        "  - Added Auvers-sur-Oise and 1890, both absent from cited passages.",
        f"- **P4 ('Did you die?'):** Flagged = `{p4_flagged}` (Flags: `{session07_p4['flags'] if session07_p4 else []}`)",
        "  - Added July 1890, absent from cited passage.",
        "",
        "## False Flags (Wrongly Flagged / False Positives)",
        "",
    ]

    if not false_flags:
        lines.append("None. All fully supported answers passed without false flags.")
    else:
        lines.append(f"Total false flags: {len(false_flags)}\n")
        lines.append("| ID | Exhibit | Mode | Answer | Flagged Claims |")
        lines.append("|---|---|---|---|---|")
        for ff in false_flags:
            row = ff["row"]
            flags_str = ", ".join(repr(f) for f in ff["flags"])
            lines.append(f"| `{row['id']}` | {row['exhibit']} | {row['mode']} | {row['answer'][:60]}... | {flags_str} |")

    lines.extend([
        "",
        "## Misses (Undetected Unsupported Details / False Negatives)",
        "",
    ])

    if not misses:
        lines.append("None. All answers containing unsupported details were correctly detected.")
    else:
        lines.append(f"Total misses: {len(misses)}\n")
        lines.append("| ID | Exhibit | Mode | Answer | Expected Unsupported Details | Actual Flags |")
        lines.append("|---|---|---|---|---|---|")
        for m in misses:
            row = m["row"]
            exp_str = ", ".join(repr(e) for e in row["unsupported_details"])
            act_str = ", ".join(repr(f) for f in m["flags"]) if m["flags"] else "[]"
            lines.append(f"| `{row['id']}` | {row['exhibit']} | {row['mode']} | {row['answer'][:50]}... | {exp_str} | {act_str} |")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate claim checker against labels.")
    parser.add_argument("--labels", default=str(ROOT / "eval" / "claims_labels.jsonl"), help="Path to claims_labels.jsonl")
    parser.add_argument("--output", default=None, help="Optional path to write markdown results report")
    args = parser.parse_args()

    eval_data = evaluate(Path(args.labels))
    report = format_report(eval_data)
    print(report)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"\nWrote evaluation report to {out_path}")


if __name__ == "__main__":
    main()
