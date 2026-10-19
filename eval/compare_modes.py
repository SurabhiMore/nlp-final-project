"""Paired comparison of the persona and the plain museum guide.

    python -m eval.compare_modes
    python -m eval.compare_modes --results eval/results/answers_results.json

eval_answers.py asks every held-out question twice, once as the exhibit
(persona) and once as a plain museum guide, with the same retrieved passages,
so the two answers to a question form a pair. This script matches the pairs by
exhibit and question id, never by row order, and counts four outcomes:

  both correct, persona only, plain guide only, both wrong

"Correct" is the grounded score from eval_answers.py: the right answer backed
by a cited passage, or, for a trap question, a decline.

Only the questions where the two modes disagree (the discordant pairs) say
anything about which mode is better. The exact McNemar test asks how likely a
split at least this uneven would be if both modes were equally good, treating
each discordant question as a coin flip. With few discordant questions the test
cannot reach significance however the split falls, and the output says so.

To show how big the gap could plausibly be, it also gives a 95% interval for
persona minus plain guide accuracy, using Newcombe's method for paired yes/no
results (Newcombe 1998, method 10). It stays sensible with very few
disagreements, where simpler intervals collapse to zero width.

Outputs, in eval/results/:
  compare_modes.json   every number, plus each question's outcome
  compare_modes.md     the same as tables
"""

import argparse
import json
import sys
from fractions import Fraction
from math import comb, sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config  # noqa: E402

RESULTS_DIR = config.EVAL_DIR / "results"
MODES = ("persona", "neutral")
LABEL = {"persona": "persona", "neutral": "plain guide"}
OUTCOMES = ("both correct", "persona only", "plain guide only", "both wrong")
ALPHA = 0.05
Z = 1.959964  # two-sided 95%


def pair_results(rows):
    """Match the two modes' results by exhibit and question id.

    Returns {(exhibit, question_id): {"persona": bool, "neutral": bool, "question": str}}.
    Raises ValueError when a result appears twice, a mode is missing for a
    question, or a call failed, because any of these would make the comparison
    unfair.
    """
    pairs, problems = {}, []
    for row in rows:
        mode = row.get("mode")
        if mode not in MODES:
            continue
        key = (row["exhibit"], row["question_id"])
        entry = pairs.setdefault(key, {"question": row.get("question", ""), "failed": set()})
        name = f"{key[0]}/{key[1]}"
        if mode in entry or mode in entry["failed"]:
            problems.append(f"{name}: two {LABEL[mode]} results")
        elif row.get("status") == "error":
            entry["failed"].add(mode)
            problems.append(f"{name}: the {LABEL[mode]} call failed, rerun eval_answers with --resume")
        else:
            entry[mode] = bool(row["grounded"])
    for (exhibit, question_id), entry in pairs.items():
        for mode in MODES:
            if mode not in entry and mode not in entry["failed"]:
                problems.append(f"{exhibit}/{question_id}: no {LABEL[mode]} result")
    if problems:
        raise ValueError("Cannot pair the results:\n  " + "\n  ".join(problems))
    for entry in pairs.values():
        del entry["failed"]
    return pairs


def outcome(persona, neutral):
    if persona and neutral:
        return "both correct"
    if persona:
        return "persona only"
    if neutral:
        return "plain guide only"
    return "both wrong"


def exact_mcnemar(b, c):
    """Two-sided exact McNemar p-value for b and c discordant pairs; 1.0 when there are none."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(b, c) + 1))
    return float(min(Fraction(1), Fraction(2 * tail, 2 ** n)))


def smallest_p(n):
    """The smallest p-value the test can give with n discordant pairs, from an n to 0 split."""
    return 1.0 if n == 0 else min(1.0, 2 / 2 ** n)


def wilson(x, n):
    """Wilson score 95% interval for a proportion x / n."""
    p = x / n
    denom = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denom
    half = Z * sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denom
    return centre - half, centre + half


def newcombe_interval(a, b, c, d):
    """95% interval, in points, for persona minus plain guide accuracy from paired counts.

    a = both correct, b = persona only, c = plain guide only, d = both wrong.
    """
    n = a + b + c + d
    p1, p2 = (a + b) / n, (a + c) / n
    l1, u1 = wilson(a + b, n)
    l2, u2 = wilson(a + c, n)
    margins = (a + b) * (c + d) * (a + c) * (b + d)
    phi = (a * d - b * c) / sqrt(margins) if margins > 0 else 0.0
    diff = p1 - p2
    low = diff - sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    high = diff + sqrt(max(0.0, (p2 - l2) ** 2 - 2 * phi * (p2 - l2) * (u1 - p1) + (u1 - p1) ** 2))
    return round(low * 100, 1), round(high * 100, 1)


def conclusion(b, c, p):
    n = b + c
    if n == 0:
        return "Both modes got exactly the same questions right, so there is no difference to test."
    if p < ALPHA:
        better = "persona" if b > c else "plain guide"
        return (f"The {better} was right on {max(b, c)} of the {n} questions where the modes disagreed "
                f"(p = {p:.3f}). On these questions and this model, a split this uneven is unlikely to be chance.")
    text = f"No evidence of a difference (p = {p:.2f})."
    if smallest_p(n) >= ALPHA:
        text += (f" The modes disagreed on only {n} question{'s' if n > 1 else ''}, and even a {n} to 0 split "
                 f"would give p = {smallest_p(n):.3f}, so this sample is too small to show a difference either way.")
    else:
        text += f" The modes disagreed on {n} questions and split {b} to {c}."
    return text


def summarize(pairs):
    n = len(pairs)
    counts = dict.fromkeys(OUTCOMES, 0)
    for entry in pairs.values():
        counts[outcome(entry["persona"], entry["neutral"])] += 1
    persona = counts["both correct"] + counts["persona only"]
    neutral = counts["both correct"] + counts["plain guide only"]
    b, c = counts["persona only"], counts["plain guide only"]
    p = exact_mcnemar(b, c)
    low, high = newcombe_interval(counts["both correct"], b, c, counts["both wrong"])
    text = conclusion(b, c, p) + (f" The 95% interval for the gap runs from {low:+.1f} to {high:+.1f} points "
                                  f"(persona minus plain guide).")
    return {
        "questions": n,
        "persona_correct": persona,
        "plain_guide_correct": neutral,
        "persona_accuracy": round(persona / n, 3),
        "plain_guide_accuracy": round(neutral / n, 3),
        "difference_points": round((persona - neutral) / n * 100, 1),
        "difference_interval_95": [low, high],
        "outcomes": counts,
        "discordant": b + c,
        "mcnemar_exact_p": round(p, 4),
        "smallest_possible_p": round(smallest_p(b + c), 4),
        "conclusion": text,
    }


def compare(results_path):
    path = Path(results_path)
    if not path.exists():
        raise ValueError(f"{path} not found. Run python -m eval.eval_answers first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("answers"), list):
        raise ValueError(f"{path} has no answers list. Is it the output of eval_answers.py?")
    pairs = pair_results(data["answers"])
    if not pairs:
        raise ValueError(f"{path} has no persona or plain guide answers to compare.")
    exhibits = sorted({exhibit for exhibit, _ in pairs})
    try:
        source = path.resolve().relative_to(config.ROOT).as_posix()
    except ValueError:
        source = str(path)
    return {
        "source": {"file": source, "run_at": data.get("run_at"), "model": data.get("model"),
                   "passages_per_question": data.get("passages_per_question")},
        "matched_by": "exhibit and question id",
        "correct_means": "grounded, as scored by eval_answers.py",
        "overall": summarize(pairs),
        "by_exhibit": {ex: summarize({k: v for k, v in pairs.items() if k[0] == ex}) for ex in exhibits},
        "questions": [
            {"exhibit": ex, "question_id": qid, "question": v["question"], "persona_correct": v["persona"],
             "plain_guide_correct": v["neutral"], "outcome": outcome(v["persona"], v["neutral"])}
            for (ex, qid), v in sorted(pairs.items())
        ],
    }


def _row(label, s):
    return (f"| {label} | {s['questions']} | {s['persona_accuracy']:.3f} ({s['persona_correct']}) | "
            f"{s['plain_guide_accuracy']:.3f} ({s['plain_guide_correct']}) | {s['difference_points']:+.1f} | "
            f"{s['difference_interval_95'][0]:+.1f} to {s['difference_interval_95'][1]:+.1f} | "
            f"{s['outcomes']['both correct']} | {s['outcomes']['persona only']} | "
            f"{s['outcomes']['plain guide only']} | {s['outcomes']['both wrong']} | {s['mcnemar_exact_p']:.2f} |")


def to_markdown(report):
    src = report["source"]
    lines = [
        "# Persona vs plain guide",
        "",
        f"Paired comparison on the same held-out questions, matched by {report['matched_by']}. "
        f"Source: `{src['file']}` (run {src['run_at']}, model {src['model']}, "
        f"{src['passages_per_question']} passages per question). "
        f"Correct means {report['correct_means']}.",
        "",
        "| | Questions | Persona | Plain guide | Difference (points) | 95% interval (points) | Both correct "
        "| Persona only | Plain guide only | Both wrong | Exact McNemar p |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
        _row("All", report["overall"]),
    ]
    lines += [_row(ex, s) for ex, s in report["by_exhibit"].items()]
    lines += ["", f"**Conclusion.** {report['overall']['conclusion']}", ""]
    disagree = [q for q in report["questions"] if q["outcome"] in ("persona only", "plain guide only")]
    if disagree:
        lines += ["## Questions where the modes disagree", "", "| Exhibit | Question | Persona | Plain guide |",
                  "|---|---|---|---|"]
        for q in disagree:
            text = q["question"].replace("|", "\\|")
            lines.append(f"| {q['exhibit']} | {q['question_id']}: {text} | "
                         f"{'right' if q['persona_correct'] else 'wrong'} | "
                         f"{'right' if q['plain_guide_correct'] else 'wrong'} |")
        lines.append("")
    lines += [
        "## Limitations",
        "",
        "- Each mode answered each question once, so run-to-run variation of the model is not measured.",
        "- The test treats questions as independent and uses only the questions where the modes disagree.",
        "- The questions were written by the team, so they may not match what visitors really ask.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(report, out_dir=RESULTS_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / "compare_modes.json", out_dir / "compare_modes.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="Paired comparison of the persona and the plain guide.")
    parser.add_argument("--results", default=str(RESULTS_DIR / "answers_results.json"),
                        help="answer results from eval_answers.py")
    parser.add_argument("--out-dir", default=str(RESULTS_DIR), help="where to save the comparison")
    args = parser.parse_args()
    try:
        report = compare(args.results)
    except ValueError as error:
        sys.exit(str(error))
    s = report["overall"]
    print(f"{s['questions']} questions | persona {s['persona_accuracy']:.3f} | plain guide "
          f"{s['plain_guide_accuracy']:.3f} | difference {s['difference_points']:+.1f} points "
          f"(95% interval {s['difference_interval_95'][0]:+.1f} to {s['difference_interval_95'][1]:+.1f}) | "
          f"persona only {s['outcomes']['persona only']} | plain guide only {s['outcomes']['plain guide only']} | "
          f"exact McNemar p = {s['mcnemar_exact_p']:.2f}")
    print(s["conclusion"])
    json_path, md_path = write_outputs(report, args.out_dir)
    for p in (json_path, md_path):
        try:
            print(f"Saved {p.resolve().relative_to(config.ROOT).as_posix()}")
        except ValueError:
            print(f"Saved {p}")


if __name__ == "__main__":
    main()
