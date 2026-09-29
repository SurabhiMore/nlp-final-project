"""Measure how long each step of a voice question takes.

    python scripts/measure_latency.py                  # 5 questions per exhibit
    python scripts/measure_latency.py --questions 10
    python scripts/measure_latency.py --no-llm         # voice and search only, no model calls

For each question we first turn the question text into speech (standing in for
a visitor's voice), then time the full pipeline in this process:

    speech to text -> search -> answer model -> speech for the first sentence

"Time to first audio" is the sum of those steps: how long a visitor waits after
letting go of the button until they hear the answer start (plus network time,
which this script does not include). We also report the word error rate of the
transcripts against the original question text.

Results are saved to eval/results/latency_results.json.
"""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config, stt  # noqa: E402

try:
    from pipeline import tts
except ImportError:
    tts = None

try:
    from pipeline.retrieve import retrieve  # noqa: E402
except ImportError:
    retrieve = None

VISITOR_VOICE = "af_heart"
TOP_K = int(os.getenv("TOP_K", "8"))  # same setting as the server
STEPS = ["stt_ms", "retrieval_ms", "llm_ms", "tts_first_ms", "time_to_first_audio_ms"]


def ms_since(start):
    return round((time.perf_counter() - start) * 1000)


def word_error_rate(reference, hypothesis):
    ref = "".join(ch.lower() if ch.isalnum() or ch == " " else " " for ch in reference).split()
    hyp = "".join(ch.lower() if ch.isalnum() or ch == " " else " " for ch in hypothesis).split()
    previous = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        current = [i]
        for j, h in enumerate(hyp, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (r != h)))
        previous = current
    return previous[-1] / max(len(ref), 1)


def percentile(values, share):
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(share * (len(ordered) - 1))))
    return ordered[index]


def main():
    parser = argparse.ArgumentParser(description="Time each step of the voice pipeline.")
    parser.add_argument("--questions", type=int, default=5, help="questions per exhibit")
    parser.add_argument("--no-llm", action="store_true", help="skip the answer model")
    parser.add_argument("--pause", type=float, default=0.0,
                        help="seconds to wait between questions, outside the timed steps, so a free tier's "
                             "tokens-per-minute limit does not add retry waits to the model time")
    args = parser.parse_args()

    engine = None
    if not args.no_llm:
        from pipeline import persona as engine

    from eval import datasets

    print(f"Whisper model: {stt.model_name()}   loading models...")
    stt.load()
    if tts is None:
        sys.exit("pipeline.tts is not merged yet. Cannot run latency measurement without TTS.")
    if retrieve is None:
        sys.exit("pipeline.retrieve is not merged yet. Cannot run latency measurement without search.")
    tts.load([VISITOR_VOICE] + [p["voice"]["kokoro_voice"] for p in config.list_personas()])

    rows = []
    for exhibit in config.list_personas():
        pid = exhibit["id"]
        try:
            questions = [q for q in datasets.load_questions(pid) if q["answerable"]][:args.questions]
        except FileNotFoundError:
            continue
        voice = exhibit["voice"]["kokoro_voice"]
        speed = float(exhibit["voice"].get("speed", 1.0))
        pitch = float(exhibit["voice"].get("pitch", 1.0))
        tts.synthesize("Warm up.", voice=voice)  # first call per voice is slower
        for q in questions:
            audio = tts.synthesize(q["question"], voice=VISITOR_VOICE)
            row = {"exhibit": pid, "question_id": q["id"], "question": q["question"]}

            start = time.perf_counter()
            transcript = stt.transcribe(audio)
            row["stt_ms"] = ms_since(start)
            row["transcript"] = transcript
            row["wer"] = round(word_error_rate(q["question"], transcript), 3)

            start = time.perf_counter()
            chunks = retrieve(pid, transcript, k=TOP_K)
            row["retrieval_ms"] = ms_since(start)

            if engine:
                start = time.perf_counter()
                result = engine.answer(pid, transcript, chunks)
                row["llm_ms"] = ms_since(start)
                answer_text = result["answer"]
            else:
                row["llm_ms"] = 0
                # Stand-in answer: the top passage. Its first sentence is usually longer
                # than a real answer's, so speech time here is an overestimate.
                answer_text = chunks[0]["text"] if chunks else "I do not know."

            # The first piece the phone page actually plays (a long first sentence is split at its first comma).
            pieces = tts.speech_chunks(answer_text) or [answer_text]
            start = time.perf_counter()
            tts.synthesize(pieces[0], voice=voice, speed=speed, pitch=pitch)
            row["tts_first_ms"] = ms_since(start)

            row["time_to_first_audio_ms"] = row["stt_ms"] + row["retrieval_ms"] + row["llm_ms"] + row["tts_first_ms"]
            rows.append(row)
            print(f"  {pid:9} {q['id']:6} stt {row['stt_ms']:>6} ms  search {row['retrieval_ms']:>4} ms  "
                  f"llm {row['llm_ms']:>6} ms  tts {row['tts_first_ms']:>6} ms  "
                  f"first audio {row['time_to_first_audio_ms']:>6} ms  wer {row['wer']:.2f}", flush=True)
            if args.pause:
                time.sleep(args.pause)

    if not rows:
        sys.exit("No questions found. Add eval/questions/<exhibit>.jsonl first.")

    summary = {step: {"median": statistics.median(r[step] for r in rows),
                      "p90": percentile([r[step] for r in rows], 0.9),
                      "max": max(r[step] for r in rows)} for step in STEPS}
    summary["mean_wer"] = round(statistics.mean(r["wer"] for r in rows), 3)

    print(f"\n{'step':24} {'median':>8} {'p90':>8} {'max':>8}   (milliseconds)")
    for step in STEPS:
        s = summary[step]
        print(f"{step:24} {s['median']:>8.0f} {s['p90']:>8.0f} {s['max']:>8.0f}")
    print(f"mean word error rate: {summary['mean_wer']:.2f}")

    results_dir = config.EVAL_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / "latency_results.json"
    path.write_text(json.dumps({
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "whisper_model": stt.model_name(),
        "llm": "none" if (args.no_llm or engine is None) else engine.model_label(),
        "summary": summary, "questions": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
