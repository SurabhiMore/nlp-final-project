import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.stats import compute_stats  # noqa: E402

LOG_PATH = ROOT / "logs" / "qa_log.jsonl"


def main():
    s = compute_stats(LOG_PATH)
    print(f"Total questions: {s['total_questions']}\n")
    print("Per exhibit")
    for ex, c in s["per_exhibit"].items():
        print(f"  {ex:<20} answered={c['answered']}  declined={c['declined']}  not_in_sources={c['not_in_sources']}")
    if not s["per_exhibit"]:
        print("  (none)")
    for title, key in (("Top questions", "top_questions"),
                       ("Corpus gaps (not_in_sources)", "top_not_in_sources")):
        print(f"\n{title}")
        for q in s[key]:
            print(f"  {q['count']:>3}  {q['question']}")
        if not s[key]:
            print("  (none)")
    print(f"\nLatency: p50={s['latency_ms']['p50']} ms  p95={s['latency_ms']['p95']} ms")


if __name__ == "__main__":
    main()
