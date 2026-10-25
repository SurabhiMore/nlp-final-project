"""Can the quote checker tell Van Gogh's real words from altered and made-up quotes?

    python -m eval.eval_quotes

The quote set, eval/questions/quotes/van-gogh.jsonl, has four kinds of quote:

  real          sentences copied from his letters                  expected: verbatim
  altered       real sentences with one to three words changed     expected: close paraphrase
  other_person  lines commonly attributed to other people          expected: not found
  popular       popular quotes credited to Van Gogh that are not   expected: not found
                in our letters

Every quote is in the dev half or the test half. The match threshold is chosen on
the dev half only: every whole number from 50 to 99 is tried, and the one with the
best dev accuracy wins (the middle one when several tie). Accuracy, a confusion
table and every wrong result are then reported for the test half.

It also runs the checker on every saved Van Gogh answer (the answer evaluations in
eval/results/ and the user test logs in artifacts/evidence/) and reports how many of
the quotes in them are word for word in his letters.

Results are saved to eval/results/quotes_results.json and quotes_results.md.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval import datasets  # noqa: E402
from pipeline import config  # noqa: E402
from pipeline import quotes as qm  # noqa: E402

PERSONA = "van-gogh"
QUOTE_SET = config.EVAL_DIR / "questions" / "quotes" / f"{PERSONA}.jsonl"
RESULTS_DIR = config.EVAL_DIR / "results"
EVIDENCE_DIR = config.ROOT / "artifacts" / "evidence"
KINDS = {"real": qm.VERBATIM, "altered": qm.CLOSE, "other_person": qm.NOT_FOUND, "popular": qm.NOT_FOUND}
SPLITS = ("dev", "test")
THRESHOLDS = range(50, 100)
SHORT = 7  # quotes of this many words or fewer count as short


def _shown(path):
    """A path relative to the repo when it is inside it."""
    path = Path(path).resolve()
    try:
        return path.relative_to(config.ROOT).as_posix()
    except ValueError:
        return str(path)


def load_quote_set(path=QUOTE_SET):
    """The labelled quotes. Raises ValueError on a missing field, a wrong label or a repeated id."""
    path = Path(path)
    if not path.exists():
        raise ValueError(f"{path} not found.")
    items, seen = [], set()
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            for key in ("id", "quote", "label", "kind", "source", "split"):
                if not item.get(key):
                    raise ValueError(f"{path}:{number} is missing '{key}'")
            if item["kind"] not in KINDS or item["label"] != KINDS[item["kind"]]:
                raise ValueError(f"{path}:{number}: kind {item['kind']!r} must have label {KINDS.get(item['kind'])!r}")
            if item["split"] not in SPLITS:
                raise ValueError(f"{path}:{number}: split must be dev or test")
            if item["id"] in seen:
                raise ValueError(f"{path}:{number}: repeated id {item['id']}")
            seen.add(item["id"])
            items.append(item)
    return items


def score_quotes(items, persona_id=PERSONA):
    """Each item with the checker's best match. The verdict is applied later, once a threshold is chosen."""
    scored = []
    for item in items:
        match = qm.match_quote(item["quote"], persona_id, threshold=0)
        scored.append({**item, "score": match["score"], "passage_id": match["passage_id"], "match": match["match"],
                       "words": len(re.findall(r"\w+", item["quote"]))})
    return scored


def accuracy(rows, threshold):
    return sum(qm.verdict_for(r["score"], threshold) == r["label"] for r in rows) / len(rows) if rows else None


def _rate(rows, threshold):
    value = accuracy(rows, threshold)
    return None if value is None else round(value, 3)


def _fmt(value):
    return "n/a" if value is None else f"{value:.3f}"


def choose_threshold(dev):
    """The threshold with the best dev accuracy; the middle of the tied ones if several share it."""
    scores = {t: accuracy(dev, t) for t in THRESHOLDS}
    best = max(scores.values())
    tied = [t for t in THRESHOLDS if scores[t] == best]
    return tied[(len(tied) - 1) // 2], best, tied


def confusion(rows, threshold):
    table = {label: {verdict: 0 for verdict in qm.VERDICTS} for label in qm.VERDICTS}
    for r in rows:
        table[r["label"]][qm.verdict_for(r["score"], threshold)] += 1
    return table


def evaluate(scored, threshold):
    test = [r for r in scored if r["split"] == "test"]
    wrong = [{**r, "verdict": qm.verdict_for(r["score"], threshold)} for r in scored
             if qm.verdict_for(r["score"], threshold) != r["label"]]
    return {
        "test_questions": len(test),
        "test_accuracy": _rate(test, threshold),
        "test_confusion": confusion(test, threshold),
        "test_accuracy_by_kind": {k: _rate([r for r in test if r["kind"] == k], threshold) for k in KINDS},
        "test_accuracy_short": _rate([r for r in test if r["words"] <= SHORT], threshold),
        "test_accuracy_longer": _rate([r for r in test if r["words"] > SHORT], threshold),
        "false_quotes_called_verbatim": sum(1 for r in test if r["label"] != qm.VERBATIM
                                           and qm.verdict_for(r["score"], threshold) == qm.VERBATIM),
        "wrong": [{k: r[k] for k in ("id", "split", "kind", "quote", "label", "verdict", "score", "passage_id", "match")}
                  for r in wrong],
    }


# ---------------------------------------------------------------- saved answers

def _reply_text(reply):
    try:
        return json.loads(reply).get("answer", "")
    except (ValueError, AttributeError):
        return reply or ""


def saved_answers(persona_id=PERSONA):
    """(source, label, answer) for every saved answer from this exhibit."""
    answers = []
    path = RESULTS_DIR / "answers_results.json"
    if path.exists():
        for r in json.loads(path.read_text(encoding="utf-8"))["answers"]:
            if r["exhibit"] == persona_id:
                answers.append((path.name, f"{r['question_id']} {r['mode']}", r.get("answer") or ""))
    path = RESULTS_DIR / "grounding_replies.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r["exhibit"] == persona_id:
                    answers.append((path.name, f"{r['question_id']} {r['mode']}", _reply_text(r["reply"])))
    for path in sorted(EVIDENCE_DIR.glob("session*/*_log.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("persona") == persona_id:
                    answers.append((path.relative_to(EVIDENCE_DIR).as_posix(), r.get("session_id", ""), r.get("answer") or ""))
    return answers


def check_saved_answers(threshold, persona_id=PERSONA):
    """Run the checker on every saved answer. For quotes not in the exhibit's own words, also say
    whether they are word for word in one of its other passages (for example Wikipedia)."""
    others = [c for c in datasets.load_chunks(persona_id) if not c.get("own_words")]
    other_norms = [(c["id"], f" {qm.normalize(c['text'])} ") for c in others]
    answers = saved_answers(persona_id)
    quotes, by_source = [], {}
    for source, label, answer in answers:
        counts = by_source.setdefault(source, {"answers": 0, "answers_with_quotes": 0, "quotes": 0, "verbatim": 0})
        results = qm.check_quote(answer, persona_id, threshold)
        counts["answers"] += 1
        counts["answers_with_quotes"] += bool(results)
        for result in results:
            elsewhere = None
            if result["verdict"] != qm.VERBATIM:
                q = f" {qm.normalize(result['quote'])} "
                elsewhere = next((cid for cid, norm in other_norms if q in norm), None)
            counts["quotes"] += 1
            counts["verbatim"] += result["verdict"] == qm.VERBATIM
            quotes.append({"source": source, "answer": label, **{k: result[k] for k in ("quote", "verdict", "score",
                           "passage_id")}, "word_for_word_in_other_passage": elsewhere})
    return {"answers": len(answers), "quotes": len(quotes),
            "verbatim": sum(q["verdict"] == qm.VERBATIM for q in quotes), "by_source": by_source, "all_quotes": quotes}


# ---------------------------------------------------------------- report

def run(quote_set=QUOTE_SET):
    items = load_quote_set(quote_set)
    scored = score_quotes(items)
    dev = [r for r in scored if r["split"] == "dev"]
    threshold, dev_accuracy, tied = choose_threshold(dev)
    altered = [r["score"] for r in scored if r["kind"] == "altered"]
    absent = [r["score"] for r in scored if r["label"] == qm.NOT_FOUND]
    return {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exhibit": PERSONA,
        "quote_set": _shown(quote_set),
        "quotes": len(items),
        "dev_questions": len(dev),
        "threshold": threshold,
        "dev_accuracy": round(dev_accuracy, 3),
        "thresholds_with_best_dev_accuracy": [tied[0], tied[-1]],
        "lowest_altered_score": min(altered),
        "highest_not_found_score": max(absent),
        **evaluate(scored, threshold),
        "saved_answers": check_saved_answers(threshold),
    }


def to_markdown(report):
    t = report["threshold"]
    lines = [
        "# Quote checker",
        "",
        f"Does `pipeline/quotes.py` tell Van Gogh's real words from altered and made-up quotes? Run on "
        f"{report['run_at'][:10]} with `python -m eval.eval_quotes`, on the {report['quotes']} quotes in "
        f"`{report['quote_set']}`. The checker only looks in the passages marked as his own words (his letters).",
        "",
        "## Threshold, chosen on the dev half only",
        "",
        f"A quote counts as a close paraphrase when its fuzzy score is {t} or more. Every threshold from "
        f"{report['thresholds_with_best_dev_accuracy'][0]} to {report['thresholds_with_best_dev_accuracy'][1]} gave "
        f"the best dev accuracy ({report['dev_accuracy']:.3f} on {report['dev_questions']} quotes), and {t} is the "
        f"middle one. Across the whole set, the lowest score for an altered quote was "
        f"{report['lowest_altered_score']} and the highest for a quote that is not in his letters was "
        f"{report['highest_not_found_score']}.",
        "",
        f"## Test half ({report['test_questions']} quotes)",
        "",
        f"Accuracy: **{_fmt(report['test_accuracy'])}**. Quotes of {SHORT} words or fewer: "
        f"{_fmt(report['test_accuracy_short'])}; longer quotes: {_fmt(report['test_accuracy_longer'])}. False quotes "
        f"called verbatim: {report['false_quotes_called_verbatim']}.",
        "",
        "| Expected \\ checker said | verbatim | close paraphrase | not found |",
        "|---|---|---|---|",
    ]
    for label, row in report["test_confusion"].items():
        lines.append(f"| {label} | " + " | ".join(str(row[v]) for v in qm.VERDICTS) + " |")
    lines += ["", "| Kind | Expected | Test accuracy |", "|---|---|---|"]
    lines += [f"| {k} | {KINDS[k]} | {_fmt(v)} |" for k, v in report["test_accuracy_by_kind"].items()]
    lines += ["", "## Every wrong result (both halves)", ""]
    if report["wrong"]:
        lines += ["| Id | Half | Kind | Quote | Expected | Checker said | Score | Closest text in the letters |",
                  "|---|---|---|---|---|---|---|---|"]
        lines += [f"| {w['id']} | {w['split']} | {w['kind']} | {w['quote']} | {w['label']} | {w['verdict']} | "
                  f"{w['score']} | {w['match']} ({w['passage_id']}) |" for w in report["wrong"]]
    else:
        lines.append("None.")

    s = report["saved_answers"]
    lines += [
        "",
        "## Quotes in saved Van Gogh answers",
        "",
        f"{s['answers']} saved answers, {s['quotes']} quotes in them, {s['verbatim']} word for word in his letters.",
        "",
        "| Source | Answers | With a quote | Quotes | Verbatim |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| `{src}` | {v['answers']} | {v['answers_with_quotes']} | {v['quotes']} | {v['verbatim']} |"
              for src, v in s["by_source"].items()]
    sourced = sum(1 for q in s["all_quotes"] if q["word_for_word_in_other_passage"])
    if sourced:
        lines += ["", f"{sourced} of the quotes that are not in his letters are word for word in one of the exhibit's "
                  "other passages (for example Wikipedia), so the answer has a source, just not his own writing."]
    if s["all_quotes"]:
        lines += ["", "| Source | Answer | Quote | Checker said | Score | Word for word in another passage |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| `{q['source']}` | {q['answer']} | {q['quote']} | {q['verdict']} | {q['score']} | "
                  f"{q['word_for_word_in_other_passage'] or 'no'} |" for q in s["all_quotes"]]
    lines += [
        "",
        "## Limitations",
        "",
        "- We wrote the altered quotes ourselves, and most change only a word or two. Heavier rewording is not tested.",
        "- Our letters are a selection, in Ludovici's English translation of a German edition. A real quote from "
        "another translation would usually come out as not found, so not found means not in our letters, not that he "
        "never said it.",
        "- Short quotes score higher by chance, because a few words can line up with almost any passage. They are "
        "where the checker makes its mistakes.",
        "- Only quotation marks and \"did you say ...\" questions are treated as quotes, so a quote the model works "
        "into a sentence without quotation marks is not checked.",
        "- A quote that runs across two passages can be missed, although passages overlap by about 100 characters.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(report, out_dir=RESULTS_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / "quotes_results.json", out_dir / "quotes_results.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="Evaluate the quote checker on real, altered and made-up quotes.")
    parser.add_argument("--quotes", default=str(QUOTE_SET), help="the labelled quote set")
    parser.add_argument("--out-dir", default=str(RESULTS_DIR), help="where to save the results")
    args = parser.parse_args()
    try:
        report = run(args.quotes)
    except ValueError as error:
        sys.exit(str(error))
    print(f"threshold {report['threshold']} (dev accuracy {report['dev_accuracy']:.3f}) | test accuracy "
          f"{_fmt(report['test_accuracy'])} on {report['test_questions']} quotes | short "
          f"{_fmt(report['test_accuracy_short'])} | longer {_fmt(report['test_accuracy_longer'])} | wrong (both halves): "
          f"{len(report['wrong'])}")
    for w in report["wrong"]:
        print(f"  {w['id']} {w['split']:4} {w['kind']:12} expected {w['label']:16} got {w['verdict']:16} {w['score']:5} | {w['quote']}")
    s = report["saved_answers"]
    print(f"saved Van Gogh answers: {s['answers']} | quotes {s['quotes']} | verbatim {s['verbatim']}")
    if report["threshold"] != qm.THRESHOLD:
        print(f"Note: pipeline/quotes.py uses THRESHOLD = {qm.THRESHOLD}; the dev half picked {report['threshold']}.")
    for path in write_outputs(report, args.out_dir):
        print(f"Saved {_shown(path)}")


if __name__ == "__main__":
    main()
