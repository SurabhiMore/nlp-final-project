"""Keyword search (BM25) over an exhibit's passages.

    from pipeline.retrieve import retrieve
    retrieve("van-gogh", "Why did you paint The Bedroom?", k=5)

Returns the top k passages, best first, each a copy of the passage with
"score" and "rank" added. Works for any exhibit that has a chunks.jsonl.
The index for each exhibit is built once and rebuilt automatically if the
chunks file changes.
"""

import json
import re
import sys
import threading
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rank_bm25 import BM25Okapi
from pipeline import config

STOPWORDS = set("""
a about above after again against all am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further
had has have having he her here hers herself him himself his how i if in into is it its itself
just me more most my myself no nor not now of off on once only or other our ours ourselves out
over own same she should so some such than that the their theirs them themselves then there
these they this those through to too under until up very was we were what when where which
while who whom why will with would you your yours yourself yourselves
""".split())

_indexes = {}
_lock = threading.Lock()


def _stem(word):
    """A very light stemmer, applied to passages and questions alike.

    Plurals:    "paintings" -> "painting", "stories" -> "story"
    -ed / -ing: "lived" -> "liv", "live" -> "liv"; "meaning" -> "mean"; "named" -> "nam", "name" -> "nam"
    A final "e" is dropped so the base word and its -ed/-ing forms meet.
    Words ending in "ss" or "us" keep their "s" ("class", "Tyrannosaurus").
    """
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us")):
        word = word[:-1]
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) > 4 and word.endswith("ed") and not word.endswith("eed"):
        word = word[:-2]
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [_stem(w) for w in words if w not in STOPWORDS]


_QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})


def normalize_query(question):
    """Clean up a visitor's question before searching. Used for search only:
    the original question is what the answer model sees.

    - Unicode is folded to plain characters and curly quotes made straight
      (speech-to-text and phones often produce them).
    - Lowercased, extra whitespace collapsed.
    - Possessive 's is dropped ("Sue's" -> "sue"), so it does not leave a stray "s" term.
    - "trex", "t-rex" and "t rex" are all written "t rex", the way the passages tokenize "T. rex".
    """
    text = unicodedata.normalize("NFKC", question or "").translate(_QUOTES).lower()
    text = re.sub(r"(\w)'s\b", r"\1", text)
    text = re.sub(r"\bt[\s.\-]*rex\b", "t rex", text)
    return " ".join(text.split())


# Visitor words that never appear in an exhibit's passages, mapped to the words the
# passages use instead. Each entry fixes a failure found in the T-Rex retrieval
# analysis (eval/results/trex_failure_analysis.md); add one only with such evidence.
# The visitor's word is kept, and the passage words are added to the search.
# "heavy -> mass, weigh" was tried for tr-08 and left out: it made tr-08 worse.
TERM_MAP = {
    "t-rex": {
        "finger": ["digit"],        # tr-10: passages say "two clawed digits"
        "horned": ["ceratopsian"],  # tr-26: passages say "ceratopsians such as Triceratops"
        "bite": ["force"],          # tr-09: passages say "bite force"
    },
}


def query_terms(persona_id, question):
    """The search terms for a visitor question: normalized, tokenized, then expanded with TERM_MAP."""
    terms = tokenize(normalize_query(question))
    mapping = {_stem(k): [_stem(v) for v in vs] for k, vs in TERM_MAP.get(persona_id, {}).items()}
    return terms + [extra for term in terms for extra in mapping.get(term, [])]


class _Index:
    def __init__(self, persona_id):
        path = config.chunks_path(persona_id)
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run: python scripts/build_corpus.py --persona {persona_id}")
        self.mtime = path.stat().st_mtime
        with open(path, encoding="utf-8") as handle:
            self.chunks = [json.loads(line) for line in handle if line.strip()]
        corpus = [tokenize(f"{c.get('section', '')} {c['text']}") for c in self.chunks]
        self.bm25 = BM25Okapi(corpus)


def _get_index(persona_id):
    path = config.chunks_path(persona_id)
    with _lock:
        index = _indexes.get(persona_id)
        if index is None or not path.exists() or path.stat().st_mtime != index.mtime:
            index = _Index(persona_id)
            _indexes[persona_id] = index
    return index


def retrieve(persona_id, question, k=5):
    """The k passages that best match the question, best first."""
    index = _get_index(persona_id)
    query = query_terms(persona_id, question)
    if not query:
        return []
    scores = index.bm25.get_scores(query)
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    results = []
    for rank, i in enumerate(order, 1):
        chunk = dict(index.chunks[i])
        chunk["score"] = float(scores[i])
        chunk["rank"] = rank
        results.append(chunk)
    return results