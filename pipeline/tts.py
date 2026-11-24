"""Text to speech with Kokoro-82M.

Answers are split into sentences and each sentence is turned into its own
audio clip, so the phone can start playing the first sentence while the rest
is still being made.

Kokoro voice names start with a letter for the accent/language:
  a   American English   (e.g. "af_heart", "am_onyx")
  b   British English    (e.g. "bm_lewis")
  h   Hindi              (e.g. "hf_alpha", "hm_omega")
  e   Spanish            (e.g. "ef_dora", "em_alex")

Each exhibit's persona.json sets its voice, speed and, optionally, pitch.
Kokoro has no pitch control of its own, so for a pitch below 1 we generate the
speech faster by the same factor and then stretch the audio back out. That
lowers the pitch (and makes the voice sound bigger, which suits a large
creature) while the speaking speed stays as set.

Kokoro requires espeak-ng for non-English voices (Hindi, Spanish). Install it
via your system package manager (apt install espeak-ng) or via the Dockerfile.

voice_for_language() maps a detected ISO 639-1 language code to the right
Kokoro voice. Marathi (mr) and Kannada (kn) have no Kokoro voice, so it returns
None for those. Callers should check for None and show the answer text only
without attempting to synthesize audio.
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
# Devanagari danda (।) used as a full stop in Hindi and Marathi.
_DEVANAGARI_DANDA = re.compile(r"।\s*")

# Maps ISO 639-1 language code to the Kokoro voice to use.
# None means Kokoro has no voice for that language; callers should skip audio.
_LANG_VOICE = {
    "en": None,   # caller picks the exhibit's configured voice
    "hi": "hf_alpha",
    "es": "ef_dora",
    "mr": None,   # no Marathi voice in Kokoro
    "kn": None,   # no Kannada voice in Kokoro
}

# Kokoro lang codes that need espeak-ng installed on the host.
_ESPEAK_LANG_CODES = {"h", "e"}


def voice_for_language(lang):
    """Return the Kokoro voice name for a detected language, or None to skip TTS.

    Returns None for languages Kokoro cannot speak (Marathi, Kannada) so the
    caller knows to show the answer text only. For English, also returns None
    because the caller should use the exhibit's configured persona voice instead.
    """
    return _LANG_VOICE.get(lang)


def split_sentences(text):
    """Split an answer into sentences, joining very short pieces onto the next one.

    Handles both Latin-script punctuation (.!?) and the Devanagari danda (।)
    used in Hindi and Marathi.
    """
    text = " ".join((text or "").split())
    if not text:
        return []
    # Replace dandas with a period-and-space so the rest of the logic works uniformly.
    text = _DEVANAGARI_DANDA.sub(". ", text).strip()
    text = " ".join(text.split())
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
    if lang_code not in ("a", "b", "h", "e"):
        raise ValueError(f"Voice '{voice}' uses unsupported lang code '{lang_code}'")
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


# ---------------------------------------------------------------- timing for the live page
#
# Kokoro predicts how long each phoneme lasts (Result.pred_dur, in frames of 1/40 s),
# so the live page can shape the exhibit's mouth for every sound as it is spoken,
# and light up each word of the subtitles on time.

FRAMES_PER_SECOND = 40.0
_SHAPE_OF = {}
for _chars, _shape in (
    ("pbm", "PP"), ("fv", "FF"), ("θð", "TH"), ("tdnlɾʔ", "DD"), ("kɡgŋhx", "KK"),
    ("ʃʒʧʤj", "CH"), ("sz", "SS"), ("ɹɚɝr", "RR"), ("ɑaæʌɐɒ", "AA"), ("ɛeɜəᵊ", "EH"),
    ("iɪᵻy", "IH"), ("ɔo", "OH"), ("uʊw", "UU"),
):
    for _char in _chars:
        _SHAPE_OF[_char] = _shape
# misaki writes some diphthongs as one capital letter: A = eɪ, I = aɪ, W = aʊ, Y = ɔɪ, O = oʊ, Q = əʊ
_DIPHTHONGS = {"A": ("EH", "IH"), "I": ("AA", "IH"), "W": ("AA", "UU"), "Y": ("OH", "IH"), "O": ("OH", "UU"), "Q": ("EH", "UU")}
_VOWEL_SHAPES = {"AA", "EH", "IH", "OH", "UU"}
_PAUSES = set(".,!?;:—–…\"“”()[]")


def mouth_shapes(phonemes, durations, start=0.0):
    """Turn Kokoro phonemes and their durations (in 1/40 s frames) into timed mouth shapes.

    Returns [start_s, length_s, shape, stress] lists. shape is one of sil, PP (m, b, p),
    FF, TH, DD, KK, CH, SS, RR, AA, EH, IH, OH, UU; stress is 2 for a vowel with primary
    stress, 1 for secondary stress and 0 otherwise. Stress marks, length marks and spaces
    add their time to the sound before them, and punctuation is a pause.
    """
    segs, t, stress = [], float(start), 0
    for char, frames in zip(phonemes, durations):
        sec = float(frames) / FRAMES_PER_SECOND
        if char in "ˈˌ":
            stress = 2 if char == "ˈ" else 1
            if segs:
                segs[-1][1] += sec
        elif char in "ː ":
            if segs:
                segs[-1][1] += sec
        elif char in _PAUSES:
            segs.append([t, sec, "sil", 0])
        elif char in _DIPHTHONGS:
            first, second = _DIPHTHONGS[char]
            segs.append([t, sec * 0.6, first, stress])
            segs.append([t + sec * 0.6, sec * 0.4, second, 0])
            stress = 0
        else:
            shape = _SHAPE_OF.get(char, "DD")
            vowel = shape in _VOWEL_SHAPES
            segs.append([t, sec, shape, stress if vowel or shape == "RR" else 0])
            if vowel:
                stress = 0
        t += sec
    return segs


def synthesize_timed(text, voice="af_heart", speed=1.0, pitch=1.0):
    """Like synthesize, but also say when each sound and each word is spoken.

    Returns (wav_bytes, {"segs": [[start, length, shape, stress], ...],
    "words": [[word, start, end, space_after], ...]}) with times in seconds from the
    start of the clip. Mouth shapes come for every voice; words only where Kokoro
    gives word timings (English).
    """
    if not 0.5 <= pitch <= 1.5:
        raise ValueError("pitch should be between 0.5 and 1.5")
    pipeline = _pipeline_for(voice)
    pieces, segs, words, offset = [], [], [], 0.0
    for result in pipeline(text, voice=voice, speed=speed / pitch):
        audio = getattr(result, "audio", None)
        if audio is None and isinstance(result, tuple):
            audio = result[-1]
        if audio is None:
            continue
        audio = _to_numpy(audio)
        phonemes = getattr(result, "phonemes", None) or ""
        durations = getattr(result, "pred_dur", None)
        if durations is not None and len(durations) == len(phonemes) + 2:
            frames = [int(d) for d in durations]
            segs += mouth_shapes(phonemes, frames[1:-1], offset + frames[0] / FRAMES_PER_SECOND)
        for token in getattr(result, "tokens", None) or []:
            if token.start_ts is not None and token.end_ts is not None and token.text.strip():
                words.append([token.text, offset + token.start_ts, offset + token.end_ts, 1 if token.whitespace else 0])
        offset += len(audio) / SAMPLE_RATE
        pieces.append(audio)
    if not pieces:
        return b"", {"segs": [], "words": []}
    audio = np.concatenate(pieces)
    if pitch != 1.0:
        audio = _stretch(audio, 1.0 / pitch)
        for seg in segs:
            seg[0] /= pitch
            seg[1] /= pitch
        for word in words:
            word[1] /= pitch
            word[2] /= pitch
    buffer = io.BytesIO()
    sf.write(buffer, audio, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    timing = {
        "segs": [[round(s[0], 3), round(s[1], 3), s[2], s[3]] for s in segs],
        "words": [[w[0], round(w[1], 3), round(w[2], 3), w[3]] for w in words],
    }
    return buffer.getvalue(), timing


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
