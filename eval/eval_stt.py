"""How well does speech to text hear visitors' questions, and how long does it take?

    python -m eval.eval_stt
    python -m eval.eval_stt --settings current prompt     # only some settings
    python -m eval.eval_stt --audio-dir path/to/clips      # recordings somewhere else
    python -m eval.eval_stt --check                        # which clips each speaker still has to record

The reference set, eval/questions/stt/reference.jsonl, has 40 held-out questions,
20 per exhibit. Each speaker reads them aloud and saves one clip per question:

    data/stt_audio/S1/vg-01.webm
    data/stt_audio/S1/tr-h04.m4a
    data/stt_audio/S2/...

Speaker folders are named S1, S2 and so on, never by name. Any format that
Whisper can decode works (webm, m4a, mp3, wav, ogg). data/ is not committed, so
the audio stays out of the repo. An optional data/stt_audio/speakers.json says
what accent each speaker has, for example {"S1": {"accent": "Indian English"}}.
See eval/questions/stt/README.md for how to record them.

Every clip is transcribed with each setting:

  current       base, beam_size=1, no prompt (the setup before issue #41)
  prompt        base, beam_size=1, the exhibit's vocabulary prompt
  beam5         base, beam_size=5, no prompt
  prompt_beam5  base, beam_size=5, the exhibit's vocabulary prompt
  small_prompt  small, beam_size=1, the exhibit's vocabulary prompt

and scored with word error rate (after lowercasing and removing punctuation and
accents), how many clips came out exactly right, how many exhibit names were
heard right, and seconds per clip. Each model transcribes one clip before timing
starts, so loading it is not counted.

The suggested default is the setting with the lowest word error rate whose median
seconds per clip is at most --max-seconds (default 2.0). For that setting it also
suggests a threshold for the low-confidence flag: the one that best separates
misheard clips from clips that came out right (share of misheard clips flagged
minus share of right clips flagged). It is chosen on the same clips it is
reported on, so treat it as a starting point.

Results are saved to eval/results/stt_results.json and stt_results.md. They hold
the transcripts and scores, never the audio.
"""

import argparse
import json
import os
import platform
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval.datasets import normalize  # noqa: E402
from pipeline import config  # noqa: E402
from pipeline import stt  # noqa: E402

REFERENCE = config.EVAL_DIR / "questions" / "stt" / "reference.jsonl"
AUDIO_DIR = config.ROOT / "data" / "stt_audio"
RESULTS_DIR = config.EVAL_DIR / "results"
AUDIO_EXTENSIONS = {".webm", ".m4a", ".mp4", ".mp3", ".wav", ".ogg", ".flac", ".aac"}
SPEAKER = re.compile(r"^S\d{1,3}$")
PROMPT_FILLER = set(normalize("A question for about").split())
THRESHOLDS = [round(-0.05 * n, 2) for n in range(1, 25)]  # -0.05 to -1.2

SETTINGS = {
    "current": {"model": "base", "beam": 1, "prompt": False},
    "prompt": {"model": "base", "beam": 1, "prompt": True},
    "beam5": {"model": "base", "beam": 5, "prompt": False},
    "prompt_beam5": {"model": "base", "beam": 5, "prompt": True},
    "small_prompt": {"model": "small", "beam": 1, "prompt": True},
}


# ---------------------------------------------------------------- data

def _shown(path):
    """A path relative to the repo when it is inside it."""
    path = Path(path).resolve()
    try:
        return path.relative_to(config.ROOT).as_posix()
    except ValueError:
        return str(path)


def load_reference(path=REFERENCE):
    """The questions to read aloud, by id. Raises ValueError on a missing field or a repeated id."""
    path = Path(path)
    items = {}
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            for key in ("id", "persona", "text"):
                if not item.get(key):
                    raise ValueError(f"{path}:{number} is missing '{key}'")
            if item["id"] in items:
                raise ValueError(f"{path}:{number}: repeated id {item['id']}")
            items[item["id"]] = item
    return items


def find_clips(audio_dir, reference):
    """(speaker, question id, path) for every recording, and a list of files that were skipped and why."""
    audio_dir = Path(audio_dir)
    clips, skipped = [], []
    if not audio_dir.is_dir():
        return clips, skipped
    for folder in sorted(p for p in audio_dir.iterdir() if p.is_dir()):
        if not SPEAKER.match(folder.name):
            skipped.append(f"{folder.name}/: speaker folders are named S1, S2, ... (never a name)")
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            if path.stem not in reference:
                skipped.append(f"{folder.name}/{path.name}: no question with id {path.stem}")
                continue
            clips.append((folder.name, path.stem, path))
    return clips, skipped


def check(audio_dir=AUDIO_DIR, reference_path=REFERENCE):
    """Print how many clips each speaker has recorded and which are missing. Returns the number of clips."""
    reference = load_reference(reference_path)
    clips, skipped = find_clips(audio_dir, reference)
    done = {}
    for speaker, qid, _ in clips:
        done.setdefault(speaker, set()).add(qid)
    for speaker in sorted(done, key=lambda s: int(s[1:])):
        missing = [qid for qid in reference if qid not in done[speaker]]
        print(f"{speaker}: {len(done[speaker])} of {len(reference)} clips"
              + (f", missing {' '.join(missing)}" if missing else ""))
    for line in skipped:
        print(f"skipped {line}")
    print(f"{len(clips)} clips in all" if clips else f"No recordings found in {audio_dir}.")
    return len(clips)


def load_speakers(audio_dir):
    path = Path(audio_dir) / "speakers.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {s: {"accent": str(info.get("accent", ""))} for s, info in data.items() if SPEAKER.match(s)}


# ---------------------------------------------------------------- scoring

def word_errors(reference, hypothesis):
    """Substitutions + deletions + insertions to turn the reference words into the hypothesis words."""
    ref, hyp = reference.split(), hypothesis.split()
    previous = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        current = [i]
        for j, h in enumerate(hyp, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (r != h)))
        previous = current
    return previous[-1]


def wer(reference, hypothesis):
    """Word error rate of one transcript, after normalizing both texts."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    return word_errors(ref, hyp) / max(len(ref.split()), 1)


def name_words(reference, persona_id):
    """The words of a question that are in the exhibit's vocabulary prompt, such as theo or arles."""
    vocabulary = set(normalize(stt.exhibit_prompt(persona_id)).split()) - PROMPT_FILLER
    return [w for w in normalize(reference).split() if w in vocabulary]


def summarize(rows, threshold=None):
    """Totals for one setting's rows."""
    ref_words = sum(r["ref_words"] for r in rows)
    names = sum(r["names"] for r in rows)
    seconds = [r["seconds"] for r in rows]
    audio = sum(r["duration_s"] for r in rows)
    flagged = [stt.is_low_confidence(r["avg_logprob"], threshold) for r in rows]
    wrong = [r["errors"] > 0 for r in rows]
    return {
        "clips": len(rows),
        "wer": round(sum(r["errors"] for r in rows) / ref_words, 3) if ref_words else None,
        "exact": sum(not w for w in wrong),
        "names": names,
        "names_right": sum(r["names_right"] for r in rows),
        "seconds_median": round(statistics.median(seconds), 2) if seconds else None,
        "seconds_mean": round(statistics.mean(seconds), 2) if seconds else None,
        "real_time_factor": round(sum(seconds) / audio, 2) if audio else None,
        "flagged": sum(flagged),
        "misheard_flagged": sum(f and w for f, w in zip(flagged, wrong)),
        "misheard": sum(wrong),
        "right_flagged": sum(f and not w for f, w in zip(flagged, wrong)),
    }


def suggest(summaries, max_seconds):
    """The setting with the lowest word error rate within the time budget; the faster one on a tie."""
    fits = [(s["wer"], s["seconds_median"], name) for name, s in summaries.items()
            if s["wer"] is not None and s["seconds_median"] <= max_seconds]
    return min(fits)[2] if fits else None


def suggest_threshold(rows):
    """The flag threshold that best separates misheard clips from right ones; the one that flags fewer on a tie."""
    misheard = sum(r["errors"] > 0 for r in rows)
    right = len(rows) - misheard
    if not misheard or not right:
        return None
    def separation(t):
        s = summarize(rows, t)
        return s["misheard_flagged"] / misheard - s["right_flagged"] / right, -s["flagged"]
    return max(THRESHOLDS, key=separation)


# ---------------------------------------------------------------- running

def transcribe_clip(audio_bytes, persona_id, setting):
    options = SETTINGS[setting]
    prompt = stt.exhibit_prompt(persona_id) if options["prompt"] else ""
    start = time.perf_counter()
    heard = stt.transcribe_detailed(audio_bytes, model=options["model"], beam=options["beam"], prompt=prompt)
    return heard, time.perf_counter() - start


def run(audio_dir=AUDIO_DIR, settings=tuple(SETTINGS), max_seconds=2.0, reference_path=REFERENCE):
    reference = load_reference(reference_path)
    clips, skipped = find_clips(audio_dir, reference)
    if not clips:
        raise SystemExit(f"No recordings found in {audio_dir}. See eval/questions/stt/README.md.")
    audio = {(speaker, qid): path.read_bytes() for speaker, qid, path in clips}

    rows = {name: [] for name in settings}
    for name in settings:
        first_speaker, first_id, _ = clips[0]
        transcribe_clip(audio[(first_speaker, first_id)], reference[first_id]["persona"], name)  # warm-up
        for speaker, qid, _ in clips:
            item = reference[qid]
            heard, seconds = transcribe_clip(audio[(speaker, qid)], item["persona"], name)
            hyp_words = set(normalize(heard["text"]).split())
            names = name_words(item["text"], item["persona"])
            rows[name].append({
                "speaker": speaker, "id": qid, "persona": item["persona"],
                "reference": item["text"], "heard": heard["text"],
                "ref_words": len(normalize(item["text"]).split()),
                "errors": word_errors(normalize(item["text"]), normalize(heard["text"])),
                "names": len(names), "names_right": sum(w in hyp_words for w in names),
                "avg_logprob": heard["avg_logprob"], "duration_s": heard["duration_s"],
                "seconds": round(seconds, 3),
            })
        print(f"{name}: {len(rows[name])} clips done", file=sys.stderr)

    summaries = {name: summarize(r) for name, r in rows.items()}
    speakers = sorted({speaker for speaker, _, _ in clips}, key=lambda s: int(s[1:]))
    chosen = suggest(summaries, max_seconds)
    accents = load_speakers(audio_dir)
    return {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "machine": {"system": f"{platform.system()} {platform.machine()}", "processor": platform.processor(),
                    "cpu_count": os.cpu_count(), "device": stt.device()},
        "reference": _shown(reference_path),
        "clips": len(clips),
        "skipped": skipped,
        "speakers": {s: accents.get(s, {"accent": ""}) for s in speakers},
        "settings": {name: SETTINGS[name] for name in settings},
        "prompts": {pid: stt.exhibit_prompt(pid) for pid in sorted({r["persona"] for r in reference.values()})},
        "low_confidence_threshold": stt.low_confidence_threshold(),
        "max_seconds": max_seconds,
        "suggested": chosen,
        "suggested_threshold": suggest_threshold(rows[chosen]) if chosen else None,
        "summary": summaries,
        "by_speaker": {name: {s: summarize([r for r in rows[name] if r["speaker"] == s])["wer"] for s in speakers}
                       for name in settings},
        "thresholds": {name: {str(t): summarize(rows[name], t) for t in THRESHOLDS} for name in settings},
        "rows": rows,
    }


# ---------------------------------------------------------------- report

def _pct(part, whole):
    return f"{part} of {whole}" if whole else "n/a"


def to_markdown(report):
    names = list(report["settings"])
    chosen = report["suggested"]
    t = report["low_confidence_threshold"]
    lines = [
        "# Speech to text",
        "",
        f"How well Whisper hears visitors' questions, run on {report['run_at'][:10]} with "
        f"`python -m eval.eval_stt`: {report['clips']} clips of the questions in `{report['reference']}`, "
        f"read by {len(report['speakers'])} speakers. Machine: {report['machine']['system']}, "
        f"{report['machine']['cpu_count']} CPU threads, device {report['machine']['device']}.",
        "",
        "Word error rate is counted after lowercasing and removing punctuation and accents. \"Names right\" "
        "counts the words of each question that are in the exhibit's vocabulary prompt (such as Theo or "
        "Maastrichtian) and also appear in the transcript. Seconds per clip leave out loading the model.",
        "",
        "| Setting | Model | Beam | Prompt | Word error rate | Clips exactly right | Names right "
        "| Seconds per clip (median) | Seconds per clip (mean) | Real-time factor |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name in names:
        s, o = report["summary"][name], report["settings"][name]
        lines.append(
            f"| {name} | {o['model']} | {o['beam']} | {'yes' if o['prompt'] else 'no'} | {s['wer']:.3f} | "
            f"{_pct(s['exact'], s['clips'])} | {_pct(s['names_right'], s['names'])} | {s['seconds_median']} | "
            f"{s['seconds_mean']} | {s['real_time_factor']} |")
    lines += [""]
    if chosen:
        lines.append(f"**Suggested default: {chosen}**, the lowest word error rate with a median of at most "
                     f"{report['max_seconds']} s per clip.")
    else:
        lines.append(f"No setting had a median of {report['max_seconds']} s per clip or less.")

    lines += ["", "## By speaker", "", "| Speaker | Accent | " + " | ".join(names) + " |",
              "|---|---|" + "---|" * len(names)]
    for speaker, info in report["speakers"].items():
        lines.append(f"| {speaker} | {info['accent'] or 'not given'} | "
                     + " | ".join(f"{report['by_speaker'][n][speaker]:.3f}" for n in names) + " |")

    focus = chosen or names[0]
    s = report["summary"][focus]
    lines += [
        "",
        f"## Low-confidence flag ({focus})",
        "",
        f"A transcript is flagged when Whisper's average log probability per token is below {t}. At that "
        f"threshold, {_pct(s['misheard_flagged'], s['misheard'])} misheard clips were flagged, and "
        f"{_pct(s['right_flagged'], s['clips'] - s['misheard'])} clips that were exactly right were flagged "
        "anyway (false alarms).",
        "",
        f"Suggested threshold for this setting: **{report['suggested_threshold']}**, the one that best separates "
        "misheard clips from right ones (share of misheard clips flagged minus share of right clips flagged). It "
        "is chosen on these same clips, so it is a starting point rather than a tested result."
        if report.get("suggested_threshold") is not None else
        "No threshold suggested: every clip was misheard, or every clip was right.",
        "",
        "| Threshold | Misheard clips flagged | Right clips flagged |",
        "|---|---|---|",
    ]
    for threshold, row in report["thresholds"][focus].items():
        lines.append(f"| {threshold} | {_pct(row['misheard_flagged'], row['misheard'])} | "
                     f"{_pct(row['right_flagged'], row['clips'] - row['misheard'])} |")

    lines += ["", "## Vocabulary prompts", ""]
    lines += [f"- {pid}: {prompt}" for pid, prompt in report["prompts"].items()]

    baseline = "current" if "current" in names else names[0]
    lines += ["", f"## Every misheard clip ({focus})", ""]
    by_key = {(r["speaker"], r["id"]): r for r in report["rows"][baseline]}
    wrong = [r for r in report["rows"][focus] if r["errors"]]
    if wrong:
        lines += [f"| Speaker | Id | Said | Heard ({focus}) | Heard ({baseline}) | Log prob |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['speaker']} | {r['id']} | {r['reference']} | {r['heard']} | "
                  f"{by_key[(r['speaker'], r['id'])]['heard']} | {r['avg_logprob']} |" for r in wrong]
    else:
        lines.append("None.")
    if report["skipped"]:
        lines += ["", "## Files skipped", ""] + [f"- {s}" for s in report["skipped"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audio-dir", default=str(AUDIO_DIR), help="folder with one subfolder per speaker")
    parser.add_argument("--settings", nargs="+", choices=list(SETTINGS), default=list(SETTINGS))
    parser.add_argument("--max-seconds", type=float, default=2.0,
                        help="time budget per clip (median) for the suggested default")
    parser.add_argument("--out-dir", default=str(RESULTS_DIR))
    parser.add_argument("--check", action="store_true", help="only list the recordings found and missing")
    args = parser.parse_args()
    if args.check:
        check(args.audio_dir)
        return

    report = run(args.audio_dir, tuple(args.settings), args.max_seconds)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stt_results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "stt_results.md").write_text(to_markdown(report), encoding="utf-8")
    for name, s in report["summary"].items():
        print(f"{name:<13} WER {s['wer']:.3f}  exact {s['exact']}/{s['clips']}  "
              f"names {s['names_right']}/{s['names']}  {s['seconds_median']} s/clip")
    print(f"suggested default: {report['suggested']}, low-confidence threshold {report['suggested_threshold']}")
    print(f"saved {out / 'stt_results.md'}")


if __name__ == "__main__":
    main()
