import json
from collections import defaultdict
from pathlib import Path
from statistics import quantiles

from rapidfuzz import fuzz

# ASSUMPTION: adjust these to match the real log schema in logs/qa_log.jsonl.
Q_KEYS = ("question", "query", "text")
EXHIBIT_KEYS = ("persona", "persona_id", "exhibit")
STATUS_KEYS = ("status", "outcome", "result")
LATENCY_KEYS = ("total_ms", "latency_ms", "total_latency_ms")

SIMILARITY_THRESHOLD = 85


def _get(row, keys, default=None):
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return default


def _normalize_status(raw):
    s = str(raw or "").lower().strip()
    if "not_in" in s or "no_source" in s:
        return "not_in_sources"
    if "declin" in s or "refus" in s:
        return "declined"
    return "answered"


def read_log(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip corrupt lines instead of crashing
            if isinstance(row, dict):
                rows.append(row)
    return rows


def top_questions(questions, n=10):
    """Greedy fuzzy clustering; returns [{question, count}, ...]."""
    clusters = []
    for q in questions:
        norm = " ".join(q.lower().split())
        if not norm:
            continue
        for c in clusters:
            if fuzz.token_sort_ratio(norm, c["norm"]) >= SIMILARITY_THRESHOLD:
                c["count"] += 1
                break
        else:
            clusters.append({"question": q.strip(), "count": 1, "norm": norm})
    clusters.sort(key=lambda c: -c["count"])
    return [{"question": c["question"], "count": c["count"]} for c in clusters[:n]]


def _percentiles(values):
    if not values:
        return {"p50": 0, "p95": 0}
    if len(values) == 1:
        return {"p50": round(values[0]), "p95": round(values[0])}
    cuts = quantiles(values, n=100, method="inclusive")
    return {"p50": round(cuts[49]), "p95": round(cuts[94])}


def compute_stats(log_path):
    rows = read_log(log_path)
    per_exhibit = defaultdict(lambda: {"answered": 0, "declined": 0, "not_in_sources": 0})
    all_questions, gap_questions, latencies = [], [], []

    for row in rows:
        question = str(_get(row, Q_KEYS, "") or "")
        exhibit = str(_get(row, EXHIBIT_KEYS, "unknown"))
        status = _normalize_status(_get(row, STATUS_KEYS))
        per_exhibit[exhibit][status] += 1
        if question:
            all_questions.append(question)
            if status == "not_in_sources":
                gap_questions.append(question)
        timings = row.get("timings")
        lat = _get(timings, LATENCY_KEYS) if isinstance(timings, dict) else None
        if lat is None:
            lat = _get(row, LATENCY_KEYS)
        if isinstance(lat, (int, float)):
            latencies.append(lat)

    return {
        "total_questions": len(rows),
        "per_exhibit": dict(per_exhibit),
        "top_questions": top_questions(all_questions),
        "top_not_in_sources": top_questions(gap_questions),
        "latency_ms": _percentiles(latencies),
    }
