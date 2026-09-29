"""Export one user test's questions and answers from the server log.

The server writes every question to logs/qa_log.jsonl, which is not committed
because it holds visitors' questions. For a user test we open the page with
?session=P1 (P2, P3, ...) so that person's questions are labelled, then export
just their part into the evidence folder.

Usage (from the repo root):
    python scripts/export_session_log.py --list
    python scripts/export_session_log.py --session P1 --out artifacts/evidence/session05/P1_log.jsonl
    python scripts/export_session_log.py --session P1 --date 2026-09-28 --out ...

Read the exported file before committing it. If a question has something
personal in it, edit that line out by hand.
"""

import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "logs" / "qa_log.jsonl"

KEEP = ["timestamp", "request_id", "session_id", "persona", "mode", "input", "question", "status",
        "answer", "citations", "retrieved", "model", "stt_model", "timings"]


def read_log(path):
    if not path.exists():
        sys.exit(f"No log found at {path}. Start the server and ask a question first.")
    entries = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipping line {number}: not valid JSON", file=sys.stderr)
    return entries


def local_date(timestamp):
    """The log stores UTC times. Compare dates in the local time zone of this laptop."""
    try:
        return datetime.fromisoformat(timestamp).astimezone().date().isoformat()
    except (TypeError, ValueError):
        return ""


def list_sessions(entries):
    sessions = {}
    for entry in entries:
        sid = entry.get("session_id") or "(none)"
        info = sessions.setdefault(sid, {"questions": 0, "first": entry.get("timestamp", "")})
        info["questions"] += 1
    print(f"{'session':<40} {'questions':>9}  first question (UTC)")
    for sid, info in sorted(sessions.items(), key=lambda item: item[1]["first"]):
        print(f"{sid:<40} {info['questions']:>9}  {info['first']}")


def median_of(entries, key):
    values = [e["timings"][key] for e in entries if key in e.get("timings", {})]
    return round(statistics.median(values)) if values else None


def summarize(entries):
    print(f"questions: {len(entries)}")
    print("exhibits: " + ", ".join(f"{k} {v}" for k, v in Counter(e.get("persona") for e in entries).items()))
    print("asked by: " + ", ".join(f"{k} {v}" for k, v in Counter(e.get("input") for e in entries).items()))
    print("status: " + ", ".join(f"{k} {v}" for k, v in Counter(e.get("status") for e in entries).items()))
    for key in ("stt_ms", "retrieval_ms", "llm_ms", "total_ms"):
        value = median_of(entries, key)
        if value is not None:
            print(f"median {key}: {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", help="the label used in the page link, for example P1")
    parser.add_argument("--date", help="only keep questions from this local date, YYYY-MM-DD")
    parser.add_argument("--out", help="where to write the exported lines")
    parser.add_argument("--list", action="store_true", help="list the sessions in the log")
    parser.add_argument("--log", default=str(LOG_PATH), help="path to the server log")
    args = parser.parse_args()

    entries = read_log(Path(args.log))
    if args.list:
        list_sessions(entries)
        return
    if not args.session or not args.out:
        parser.error("--session and --out are required (or use --list)")

    selected = [e for e in entries if e.get("session_id") == args.session]
    if args.date:
        selected = [e for e in selected if local_date(e.get("timestamp")) == args.date]
    if not selected:
        sys.exit(f"No questions found for session {args.session!r}. Run with --list to see what is in the log.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        for entry in selected:
            handle.write(json.dumps({k: entry[k] for k in KEEP if k in entry}, ensure_ascii=False) + "\n")
    print(f"Wrote {len(selected)} lines to {out}")
    summarize(selected)
    print("Read the file before committing it, and remove anything personal.")


if __name__ == "__main__":
    main()
