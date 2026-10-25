"""Check whether a quote attributed to an exhibit really appears in its own words.

    from pipeline.quotes import check_quote
    check_quote('Did you really say "the sadness will last forever"?', "van-gogh")

Visitors ask "did you really say that?", and the persona may quote passages marked
as the exhibit's own words (for Van Gogh, his letters). check_quote finds the quotes
in an answer or a question and looks for each one in those passages only:

    verbatim          the quote is in a passage word for word, ignoring case,
                      punctuation, accents, apostrophes and hyphens
    close paraphrase  part of a passage is close to it: a fuzzy score of THRESHOLD
                      or more out of 100
    not found         nothing in the exhibit's own words is that close

The fuzzy score is rapidfuzz's partial ratio: the quote is compared with every
stretch of a passage of the same length, and the best score counts. THRESHOLD was
chosen on the development half of eval/questions/quotes/van-gogh.jsonl by
python -m eval.eval_quotes. An exhibit with no own words, such as the T. rex, has
nothing to match, so every quote is not found. No language model is called.

What counts as a quote: text in quotation marks, or what follows "did you say"
or "did you write that" in a question, with at least MIN_WORDS words. Quoted
painting titles ("Café Terrace at Night") are skipped.
"""

import json
import re
import sys
import threading
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rapidfuzz import fuzz, process
from pipeline import config

VERBATIM = "verbatim"
CLOSE = "close paraphrase"
NOT_FOUND = "not found"
VERDICTS = (VERBATIM, CLOSE, NOT_FOUND)

THRESHOLD = 80  # chosen by python -m eval.eval_quotes on the development half
MIN_WORDS = 4

_APOSTROPHES = set("'’‘`´")
_HYPHENS = {"-", "\u2010", "\u2011", "\u00ad"}  # hyphen, Unicode hyphens and the soft hyphen

_lock = threading.Lock()
_passages = {}


def _normalize_with_map(text):
    """Normalized text, plus the index in `text` that each normalized character came from."""
    text = text or ""
    out, where = [], []
    for i, ch in enumerate(text):
        # A double hyphen is a dash between words, not a hyphen inside one.
        if ch == "-" and ("-" in text[i - 1:i] or "-" in text[i + 1:i + 2]):
            ch = " "
        for c in unicodedata.normalize("NFKD", ch):
            if unicodedata.combining(c) or c in _APOSTROPHES or c in _HYPHENS:
                continue
            if not c.isalnum():
                if out and out[-1] != " ":
                    out.append(" ")
                    where.append(i)
                continue
            for lower in c.lower():
                if not unicodedata.combining(lower):
                    out.append(lower)
                    where.append(i)
    if out and out[-1] == " ":
        out.pop()
        where.pop()
    return "".join(out), where


def normalize(text):
    """Lowercase, fold accents, drop apostrophes and hyphens, and turn other punctuation into spaces."""
    return _normalize_with_map(text)[0]


class _Passage:
    def __init__(self, chunk):
        self.id = chunk["id"]
        self.text = chunk["text"]
        self.source = chunk.get("source", "")
        self.norm, self.where = _normalize_with_map(self.text)

    def original(self, start, end):
        """The original text behind normalized characters start to end, widened to whole words."""
        while start < end and self.norm[start] == " ":
            start += 1
        while end > start and self.norm[end - 1] == " ":
            end -= 1
        if start >= end:
            return ""
        lo, hi = self.where[start], self.where[end - 1] + 1
        while lo > 0 and self.text[lo - 1].isalnum():
            lo -= 1
        while hi < len(self.text) and self.text[hi].isalnum():
            hi += 1
        return self.text[lo:hi]


def own_words_passages(persona_id):
    """The exhibit's passages marked as its own words, reloaded if chunks.jsonl changes."""
    path = config.chunks_path(persona_id)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python scripts/build_corpus.py --persona {persona_id}")
    mtime = path.stat().st_mtime
    with _lock:
        cached = _passages.get(persona_id)
        if cached is None or cached[0] != mtime:
            with open(path, encoding="utf-8") as handle:
                chunks = [json.loads(line) for line in handle if line.strip()]
            cached = (mtime, [_Passage(c) for c in chunks if c.get("own_words")])
            _passages[persona_id] = cached
    return cached[1]


def verdict_for(score, threshold=THRESHOLD):
    """The verdict for a match score: 100 means word for word."""
    if score >= 100:
        return VERBATIM
    return CLOSE if score >= threshold else NOT_FOUND


def match_quote(quote, persona_id, threshold=THRESHOLD):
    """Look for one quote in the exhibit's own words.

    Returns {"quote", "verdict", "score", "passage_id", "source", "match"}, where match is the
    passage text that came closest. passage_id is None when the exhibit has no own words.
    """
    result = {"quote": quote, "verdict": NOT_FOUND, "score": 0.0, "passage_id": None, "source": "",
              "match": ""}
    q = normalize(quote)
    passages = own_words_passages(persona_id)
    if not q or not passages:
        return result

    for p in passages:
        start = f" {p.norm} ".find(f" {q} ")
        if start >= 0:
            result.update(verdict=VERBATIM, score=100.0, passage_id=p.id, source=p.source,
                          match=p.original(start, start + len(q)))
            return result

    _, score, index = process.extractOne(q, [p.norm for p in passages], scorer=fuzz.partial_ratio)
    best = passages[index]
    span = fuzz.partial_ratio_alignment(q, best.norm)
    score = min(round(score, 1), 99.9)  # 100 is kept for word-for-word matches
    result.update(verdict=verdict_for(score, threshold), score=score, passage_id=best.id,
                  source=best.source, match=best.original(span.dest_start, span.dest_end))
    return result


# ---------------------------------------------------------------- finding quotes

_QUOTED = [
    re.compile(r'"([^"]+)"'),
    re.compile(r"“([^”]+)”"),
    # A single quote mark inside a word ("don't") is an apostrophe, not the end of the quote.
    re.compile(r"‘((?:[^’]|’(?=\w))+)’(?!\w)"),
    re.compile(r"(?<!\w)'((?:[^']|'(?=\w))+)'(?!\w)"),
]
_ASKS = re.compile(r"^\W*(?:[\w’']+\W+){0,3}?(?:did|do|does|have|has|is it true|was it true)\b", re.I)
_REPORTED = re.compile(
    r"\b(?:you|he|vincent|van gogh)\b(?:\s+\w+){0,2}?\s+(?P<verb>say|said|write|wrote|written)\b"
    r"(?:\s+(?:to|in a letter to)\s+(?:theo|bernard|gauguin|your brother|his brother))?"
    r"(?P<link>\s+that\b|\s*[,:])?\s*(?P<quote>[^?!]+)", re.I)
_PRONOUN_I = {"i", "i'm", "i’m", "i've", "i’ve", "i'd", "i’d", "i'll", "i’ll"}


def _is_title(text):
    """True for quoted titles like "Café Terrace at Night": most words after the first are capitalized."""
    words = [w for w in re.findall(r"[^\W\d_][\w'’-]*", text)[1:] if w.lower() not in _PRONOUN_I]
    return bool(words) and sum(w[0].isupper() for w in words) / len(words) > 0.5


def _keep(text):
    text = text.strip().strip("\"'“”‘’").strip()
    text = text.rstrip(" ,;:")
    if len(re.findall(r"\w+", text)) < MIN_WORDS or _is_title(text):
        return None
    return text


def find_quotes(text):
    """The quotes in an answer or a question, in order."""
    text = text or ""
    spans = sorted((m.start(), m.end(), m.group(1)) for pattern in _QUOTED for m in pattern.finditer(text))
    quotes, last_end = [], -1
    for start, end, inner in spans:
        if start < last_end:  # inside a quote already taken, such as 'this' within "...'this'..."
            continue
        kept = _keep(inner)
        if kept:
            quotes.append(kept)
            last_end = end
    if quotes or not _ASKS.search(text):
        return quotes

    m = _REPORTED.search(text)
    if m:
        reported = m.group("quote").strip().rstrip(".")
        direct = m.group("link") or m.group("verb").lower() in ("say", "said") or reported.startswith("I ")
        kept = _keep(reported) if direct else None
        if kept:
            quotes.append(kept)
    return quotes


def check_quote(text, persona_id, threshold=THRESHOLD):
    """Check every quote in an answer or a question. Returns one match_quote result per quote."""
    return [match_quote(q, persona_id, threshold) for q in find_quotes(text)]
