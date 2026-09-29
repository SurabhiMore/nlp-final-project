"""Text to speech with Kokoro-82M.

Answers are split into sentences and each sentence is turned into its own
audio clip, so the phone can start playing the first sentence while the rest
is still being made.

Kokoro voice names start with a letter for the accent: "a" for American
English, "b" for British English (for example "af_heart", "bm_lewis").

Each exhibit's persona.json sets its voice, speed and, optionally, pitch.
Kokoro has no pitch control of its own, so for a pitch below 1 we generate the
speech faster by the same factor and then stretch the audio back out. That
lowers the pitch (and makes the voice sound bigger, which suits a large
creature) while the speaking speed stays as set.
"""

import io
import re
import threading
import time

import numpy as np
import soundfile as sf

SAMPLE_RATE = 24000
_pipelines = {}
_lock = threading.Lock()

_SENTENCE_END = re.compile(r"(?<=[.!?])[\"')\]]*\s+")
_CLAUSE_BREAK = re.compile(r"(?<=[,;:])\s+")
# A full stop after one of these does not end a sentence: "T. rex", "H. F. Osborn", "Dr. Smith".
_ABBREVIATION = re.compile(r"(?:\b[A-Z]|\b(?:Mr|Mrs|Ms|Dr|St|Prof|Jr|Sr|vs|etc|No|approx|e\.g|i\.e))\.$")


def split_sentences(text):
    """Split an answer into sentences, joining very short pieces onto the next one."""
    text = " ".join((text or "").split())
    if not text:
        return []
    parts = []
    for piece in (p.strip() for p in _SENTENCE_END.split(text) if p.strip()):
        if parts and _ABBREVIATION.search(parts[-1]):
            parts[-1] = parts[-1] + " " + piece
        else:
            parts.append(piece)
    sentences = []
    carry = ""
    for part in parts:
        part = (carry + " " + part).strip() if carry else part
        if len(part.split()) < 3:
            carry = part
            continue
        sentences.append(part)
        carry = ""
    if carry:
        if sentences:
            sentences[-1] = sentences[-1] + " " + carry
        else:
            sentences.append(carry)
    return sentences


def speech_chunks(text):
    """The pieces of an answer to speak, in order.

    Like split_sentences, but a long first sentence is split at its first comma,
    semicolon or colon when that leaves an opening of 3 to 12 words. On a CPU,
    speech takes about as long to make as to play, so a short opening starts the
    voice sooner, and the rest is made while the opening plays.
    """
    sentences = split_sentences(text)
    if not sentences:
        return []
    first = sentences[0]
    if len(first.split()) > 8:
        parts = _CLAUSE_BREAK.split(first, maxsplit=1)
        if len(parts) == 2 and 3 <= len(parts[0].split()) <= 12 and len(parts[1].split()) >= 3:
            return [parts[0], parts[1]] + sentences[1:]
    return sentences


def _pipeline_for(voice):
    lang_code = (voice or "a")[0]
    if lang_code not in ("a", "b"):
        raise ValueError(f"Voice '{voice}' is not an English Kokoro voice")
    with _lock:
        if lang_code not in _pipelines:
            from kokoro import KPipeline

            _pipelines[lang_code] = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M")
    return _pipelines[lang_code]


def load(voices=("af_heart",)):
    """Load the Kokoro pipelines now instead of on the first request."""
    for voice in voices:
        _pipeline_for(voice)


def _to_numpy(audio):
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    return np.asarray(audio, dtype=np.float32)


def _stretch(audio, factor):
    """Resample so the clip lasts `factor` times as long at the same sample rate."""
    length = max(1, int(round(len(audio) * factor)))
    positions = np.linspace(0, len(audio) - 1, length)
    return np.interp(positions, np.arange(len(audio)), audio).astype(np.float32)


def synthesize(text, voice="af_heart", speed=1.0, pitch=1.0):
    """Return WAV bytes (24 kHz, 16-bit) for the given text.

    pitch 1.0 is the voice as it is; 0.85 is about three semitones deeper.
    """
    if not 0.5 <= pitch <= 1.5:
        raise ValueError("pitch should be between 0.5 and 1.5")
    pipeline = _pipeline_for(voice)
    pieces = []
    for result in pipeline(text, voice=voice, speed=speed / pitch):
        audio = getattr(result, "audio", None)
        if audio is None and isinstance(result, tuple):
            audio = result[-1]
        if audio is not None:
            pieces.append(_to_numpy(audio))
    if not pieces:
        return b""
    audio = np.concatenate(pieces)
    if pitch != 1.0:
        audio = _stretch(audio, 1.0 / pitch)
    buffer = io.BytesIO()
    sf.write(buffer, audio, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def synthesize_sentences(text, voice="af_heart", speed=1.0, pitch=1.0):
    """Make one audio clip per piece of the answer (see speech_chunks).

    Returns a list of {"sentence", "wav", "ms"} in reading order.
    """
    clips = []
    for sentence in speech_chunks(text):
        start = time.perf_counter()
        wav = synthesize(sentence, voice=voice, speed=speed, pitch=pitch)
        clips.append({
            "sentence": sentence,
            "wav": wav,
            "ms": round((time.perf_counter() - start) * 1000),
        })
    return clips
