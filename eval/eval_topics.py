"""Do visitor questions land in the right topic on the curator stats page?

    python -m eval.eval_topics

Scores the topic rules in app/stats.py on the labelled questions in eval/questions/topics/
(see the README there). Uses no language model and no network. It reports:

  - accuracy on the held-out test.jsonl, split into the 30 questions real visitors asked and
    the 36 written for the set, with every wrong result
  - for each topic on the held-out set: how many questions have it, how many the rules gave
    it, and how many of those were right
  - accuracy on dev.jsonl, the questions the rules were written on
  - what the curator page shows for all the user test logs read together

Results are saved to eval/results/topics_results.json and topics_results.md.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import stats  # noqa: E402
from pipeline import config  # noqa: E402

ROOT = config.ROOT
QUESTIONS_DIR = config.EVAL_DIR / "questions" / "topics"
RESULTS_DIR = config.EVAL_DIR / "results"
EVIDENCE_DIR = ROOT / "artifacts" / "evidence"
FIELDS = ("id", "exhibit", "question", "topic", "group", "source")
GROUPS = ("visitor", "written", "team")


def _shown(path):
    """A path relative to the repo when it is inside it, for the report."""
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def load_set(path):
    """The labelled questions in one file, checked. Raises ValueError on a bad line."""
    path = Path(path)
    rows, seen = [], set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        where = f"{path.name}:{number}"
        for key in FIELDS:
            if not row.get(key):
                raise ValueError(f"{where} is missing '{key}'")
        if row["topic"] not in stats.TOPIC_LABELS:
            raise ValueError(f"{where}: unknown topic {row['topic']!r}")
        if row["group"] not in GROUPS:
            raise ValueError(f"{where}: group must be one of {', '.join(GROUPS)}")
        if row["id"] in seen:
            raise ValueError(f"{where}: repeated id {row['id']}")
        seen.add(row["id"])
        rows.append(row)
    return rows


def score(rows):
    """Accuracy overall, per group and per topic, and every wrong result."""
    right, wrong, by_group = 0, [], {}
    by_topic = {topic: {"questions": 0, "tagged": 0, "right": 0} for topic in stats.TOPIC_LABELS}
    for row in rows:
        tagged = stats.topic_of(row["question"], row["exhibit"])
        ok = tagged == row["topic"]
        right += ok
        group = by_group.setdefault(row["group"], {"questions": 0, "right": 0})
        group["questions"] += 1
        group["right"] += ok
        by_topic[row["topic"]]["questions"] += 1
        by_topic[tagged]["tagged"] += 1
        by_topic[tagged]["right"] += ok
        if not ok:
            wrong.append({**{k: row[k] for k in ("id", "exhibit", "question", "topic", "group")}, "tagged": tagged})
    return {"questions": len(rows), "right": right, "accuracy": round(right / len(rows), 3) if rows else None,
            "by_group": by_group, "by_topic": {t: v for t, v in by_topic.items() if v["questions"] or v["tagged"]},
            "wrong": wrong}


def run(questions_dir=QUESTIONS_DIR, evidence_dir=EVIDENCE_DIR):
    questions_dir = Path(questions_dir)
    logs = sorted(Path(evidence_dir).glob("session*/*_log.jsonl"))
    curator = stats.compute_stats(logs) if logs else {"total_questions": 0, "top_topics": []}
    return {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "test": score(load_set(questions_dir / "test.jsonl")),
        "dev": score(load_set(questions_dir / "dev.jsonl")),
        "user_test_logs": {"files": [_shown(p) for p in logs], "questions": curator["total_questions"],
                           "top_topics": curator["top_topics"]},
    }


def _cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def _wrong_table(wrong):
    if not wrong:
        return ["None."]
    lines = ["| Id | Exhibit | Question | Expected | Rules said |", "|---|---|---|---|---|"]
    lines += [f"| {w['id']} | {w['exhibit']} | {_cell(w['question'])} | {w['topic']} | {w['tagged']} |" for w in wrong]
    return lines


def to_markdown(report):
    t, d, logs = report["test"], report["dev"], report["user_test_logs"]

    def group(name):
        g = t["by_group"].get(name, {"questions": 0, "right": 0})
        return f"{g['right']} of {g['questions']}"

    lines = [
        "# Topics on the curator stats page",
        "",
        f"Do visitor questions land in the right topic? Run on {report['run_at'][:10]} with "
        "`python -m eval.eval_topics`. `app/stats.py` tags each question with keyword rules, with no language "
        "model and no network. The labelled questions, and how they were made, are described in "
        "`eval/questions/topics/README.md`.",
        "",
        "## Held-out questions",
        "",
        f"**{t['right']} of {t['questions']} right ({t['accuracy']:.3f}).** Questions real visitors asked in the "
        f"user tests: {group('visitor')}. Questions written for the set: {group('written')}.",
        "",
        "| Topic | Questions | Tagged by the rules | Right |",
        "|---|---|---|---|",
    ]
    lines += [f"| {stats.TOPIC_LABELS[name]} (`{name}`) | {v['questions']} | {v['tagged']} | {v['right']} |"
              for name, v in t["by_topic"].items()]
    lines += ["", "Every wrong result:", ""] + _wrong_table(t["wrong"])
    lines += ["", "## Development questions", "",
              f"The rules were written on these, so this is not a fair test: {d['right']} of {d['questions']} right "
              f"({d['accuracy']:.3f}).", "", "Every wrong result:", ""] + _wrong_table(d["wrong"])
    lines += ["", "## The user test logs on the curator page", "",
              f"What `/stats` shows for the {logs['questions']} questions in all {len(logs['files'])} user test logs "
              "read together (`python scripts/report_stats.py --log artifacts/evidence/session0*/P*_log.jsonl`):", "",
              "| Topic | Questions | Not in sources | For example |", "|---|---|---|---|"]
    lines += [f"| {x['label']} | {x['count']} | {x['not_in_sources']} | {_cell(' / '.join(x['samples']))} |"
              for x in logs["top_topics"]]
    lines += [
        "",
        "## Limitations",
        "",
        "- The same person labelled the questions and wrote the rules, so the held-out result is weaker than one "
        "from labels made by someone else. The visitor questions are the stronger test, because real people "
        "chose the words.",
        "- The rules only know the words on their lists. A question that says the same thing in other words goes "
        "to the wrong topic or to Other.",
        "- English only. A question in another language is tagged by the English search query the server saves "
        "for it.",
        "- Each question gets one topic, the first that matches, so a question about two things counts once.",
        "- The held-out set is small: some topics have only two questions in it.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(report, out_dir=RESULTS_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / "topics_results.json", out_dir / "topics_results.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="Evaluate the topic tags on the curator stats page.")
    parser.add_argument("--questions", default=str(QUESTIONS_DIR), help="folder with dev.jsonl and test.jsonl")
    parser.add_argument("--out-dir", default=str(RESULTS_DIR), help="where to save the results")
    args = parser.parse_args()
    try:
        report = run(args.questions)
    except ValueError as error:
        sys.exit(str(error))
    t, d = report["test"], report["dev"]
    print(f"held-out: {t['right']} of {t['questions']} ({t['accuracy']}) | visitor questions: "
          f"{t['by_group'].get('visitor', {}).get('right', 0)} of {t['by_group'].get('visitor', {}).get('questions', 0)}"
          f" | dev: {d['right']} of {d['questions']} ({d['accuracy']})")
    for path in write_outputs(report, args.out_dir):
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
