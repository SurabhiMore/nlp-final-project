"""Speech to text with Whisper, run through faster-whisper.

faster-whisper runs the same Whisper weights with CTranslate2, which is much
faster than plain PyTorch on a CPU. A model loads the first time it is used.

Which model we use depends on the hardware. On our laptops, large-v3-turbo took
about 14 seconds to transcribe a 2.5 second question on the CPU, while "base"
took about 1.6 seconds and gave the same transcript. So the default is "base"
on a CPU and "large-v3-turbo" on a GPU.

Each exhibit gets its own vocabulary prompt (Whisper's initial_prompt): the
exhibit's name and the proper nouns from persona.json and its passages, such as
Theo, Arles or Maastrichtian. Whisper reads it as text that came just before the
question, so it is more likely to spell those names right. The prompt is built
the same way for every exhibit; see build_prompt.

Every transcript also gets a confidence flag from Whisper's average log
probability per token. The phone page asks the visitor to check a transcript
that is flagged before sending it.

eval/eval_stt.py measures word error rate and seconds per clip for each setting
and suggests the defaults below; its results are in eval/results/stt_results.md.

Settings (environment variables, all optional):
  WHISPER_MODEL           overrides the default model, e.g. "small" or "large-v3-turbo"
  WHISPER_DEVICE          "cpu" (default) or "cuda"
  WHISPER_COMPUTE_TYPE    default "int8" on CPU, "float16" on GPU
  WHISPER_BEAM_SIZE       default 1
  WHISPER_PROMPT          "1" (default) to use the exhibit's vocabulary prompt, "0" to turn it off
  WHISPER_LOW_CONFIDENCE  average log probability below which a transcript is flagged, default -0.6
  WHISPER_TIMEOUT         seconds before giving up on one clip, default 30 (0 means no limit)
"""

import concurrent.futures
import functools
import io
import json
import os
import re
import threading
from collections import Counter

DEFAULT_BEAM_SIZE = 1
DEFAULT_LOW_CONFIDENCE = -0.6
PROMPT_WORDS = 40  # Whisper keeps only the last 223 tokens of a prompt, so keep it well under that

_models = {}
_lock = threading.Lock()

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*")
_TOKEN = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*|\S")


def device():
    return os.getenv("WHISPER_DEVICE", "cpu")


def model_name():
    default = "large-v3-turbo" if device() == "cuda" else "base"
    return os.getenv("WHISPER_MODEL", default)


def beam_size():
    return int(os.getenv("WHISPER_BEAM_SIZE", DEFAULT_BEAM_SIZE))


def prompt_enabled():
    return os.getenv("WHISPER_PROMPT", "1") != "0"


def low_confidence_threshold():
    return float(os.getenv("WHISPER_LOW_CONFIDENCE", DEFAULT_LOW_CONFIDENCE))


def _get_model(name=None):
    name = name or model_name()
    with _lock:
        if name not in _models:
            from faster_whisper import WhisperModel

            default_compute = "float16" if device() == "cuda" else "int8"
            _models[name] = WhisperModel(
                name,
                device=device(),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", default_compute),
                cpu_threads=os.cpu_count() or 4,
            )
    return _models[name]


def load(name=None):
    """Load a model now instead of on the first request."""
    _get_model(name)


# ---------------------------------------------------------------- vocabulary prompt

def _strip_possessive(word):
    return re.sub(r"['’]s$", "", word)


def proper_nouns(texts, limit=PROMPT_WORDS):
    """The most frequent names in some texts, most frequent first.

    A name is a run of one to three capitalised words that does not start a
    sentence, such as "Arles" or "North America". Every word in it must be
    almost never written in lower case. Words of one or two letters and
    all-capital words (abbreviations) are left out.
    """
    names, capitalised, lower = Counter(), Counter(), Counter()
    for text in texts:
        for sentence in _SENTENCE.split(text or ""):
            run, past_first_word = [], False
            for token in _TOKEN.findall(sentence) + ["."]:
                if _WORD.fullmatch(token):
                    word = _strip_possessive(token)
                    if word[0].isupper() and past_first_word:
                        run.append(word)
                        capitalised[word] += 1
                        continue
                    if word[0].islower():
                        lower[word.lower()] += 1
                    past_first_word = True
                if run:
                    names[" ".join(run)] += 1
                    run = []

    def is_name(phrase):
        words = phrase.split()
        return len(words) <= 3 and all(
            len(w) >= 3 and not w.isupper() and lower[w.lower()] <= capitalised[w] * 0.1 for w in words
        )
    return [phrase for phrase, _ in names.most_common() if is_name(phrase)][:limit]


def build_prompt(persona, chunks, limit=PROMPT_WORDS):
    """Whisper's initial_prompt for one exhibit, from its persona.json and passages.

    The exhibit's name and the proper nouns in its description come first, then
    the most frequent proper nouns in its passages, up to `limit` words in all.
    """
    name = persona["name"]
    own = [persona.get("description", ""), persona.get("greeting", ""), persona["time_period"].get("label", "")]
    seen = set(name.lower().split())
    picked, used = [], len(name.split())
    for phrase in proper_nouns(own, limit) + proper_nouns((c["text"] for c in chunks), limit):
        words = phrase.lower().split()
        if all(w in seen for w in words) or used + len(words) > limit:
            continue
        seen.update(words)
        picked.append(phrase)
        used += len(words)
    if not picked:
        return f"A question for {name}."
    return f"A question for {name}, about {', '.join(picked)}."


@functools.lru_cache(maxsize=None)
def exhibit_prompt(persona_id):
    """The vocabulary prompt for an exhibit, built once and then reused."""
    from pipeline import config

    persona = config.load_persona(persona_id)
    path = config.chunks_path(persona_id)
    chunks = []
    if path.exists():
        with open(path, encoding="utf-8") as handle:
            chunks = [json.loads(line) for line in handle if line.strip()]
    return build_prompt(persona, chunks)


# ---------------------------------------------------------------- transcribing

def average_logprob(segments):
    """Whisper's average log probability per token over all segments, or None when nothing was heard.

    Each segment reports its own average, so they are weighted by how many tokens they have.
    """
    total, tokens = 0.0, 0
    for segment in segments:
        count = max(len(segment.tokens or []), 1)
        total += segment.avg_logprob * count
        tokens += count
    return total / tokens if tokens else None


def is_low_confidence(avg_logprob, threshold=None):
    if avg_logprob is None:
        return True
    return avg_logprob < (low_confidence_threshold() if threshold is None else threshold)


def transcribe_detailed(audio_bytes, persona_id=None, language="en", model=None, beam=None, prompt=None):
    """Turn recorded audio (webm, ogg, wav, mp4 and so on) into text, with a confidence flag.

    persona_id picks the exhibit's vocabulary prompt (unless WHISPER_PROMPT=0).
    Pass `prompt` to use other prompt text instead, or "" for no prompt.

    Returns {"text", "avg_logprob", "low_confidence", "duration_s", "model", "beam_size", "prompt"}.
    The audio is decoded in memory and never written to disk.
    Raises RuntimeError if transcription takes longer than WHISPER_TIMEOUT seconds.
    """
    model = model or model_name()
    beam = beam or beam_size()
    if prompt is None:
        prompt = exhibit_prompt(persona_id) if persona_id and prompt_enabled() else ""
    result = {"text": "", "avg_logprob": None, "low_confidence": True, "duration_s": 0.0,
              "model": model, "beam_size": beam, "prompt": prompt}
    if not audio_bytes:
        return result

    def _run():
        segments, info = _get_model(model).transcribe(
            io.BytesIO(audio_bytes),
            language=language,
            beam_size=beam,
            initial_prompt=prompt or None,
            vad_filter=True,
        )
        segments = list(segments)
        return segments, info.duration

    timeout = float(os.getenv("WHISPER_TIMEOUT", "30") or 0) or None
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run)
        try:
            segments, duration = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise RuntimeError(
                f"Transcription timed out after {timeout}s. "
                "Set WHISPER_TIMEOUT env var to adjust or 0 to disable."
            )

    logprob = average_logprob(segments)
    result.update(
        text=" ".join(segment.text.strip() for segment in segments).strip(),
        avg_logprob=None if logprob is None else round(logprob, 3),
        low_confidence=is_low_confidence(logprob),
        duration_s=round(duration, 2),
    )
    return result


def transcribe(audio_bytes, language="en", persona_id=None):
    """Just the text of a recording. See transcribe_detailed."""
    return transcribe_detailed(audio_bytes, persona_id=persona_id, language=language)["text"]
