"""Keyword search (BM25) over an exhibit's passages.

    from pipeline.retrieve import retrieve
    retrieve("van-gogh", "Why did you paint The Bedroom?", k=5)

Returns the top k passages, best first, each a copy of the passage with
"score" and "rank" added. Works for any exhibit that has a chunks.jsonl.
The index for each exhibit is built once and rebuilt automatically if the
chunks file changes.
"""

import json
import os
import re
import sys
import threading
import unicodedata
from pathlib import Path

import numpy as np
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

DEFAULT_SEARCH_MODE = "bm25"
VALID_SEARCH_MODES = {"bm25", "dense", "hybrid"}
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
RRF_K = 60

_indexes = {}
_lock = threading.Lock()
_embedding_model = None
_model_lock = threading.Lock()


def get_search_mode():
    mode = os.environ.get("SEARCH_MODE", DEFAULT_SEARCH_MODE).lower().strip()
    return mode if mode in VALID_SEARCH_MODES else DEFAULT_SEARCH_MODE


def _get_embedding_model():
    """Load sentence-transformers lazily so BM25-only runs don't incur startup cost."""
    global _embedding_model
    if _embedding_model is None:
        with _model_lock:
            if _embedding_model is None:
                from sentence_transformers import SentenceTransformer
                _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


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
        self.persona_id = persona_id
        path = config.chunks_path(persona_id)
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run: python scripts/build_corpus.py --persona {persona_id}")
        self.mtime = path.stat().st_mtime
        with open(path, encoding="utf-8") as handle:
            self.chunks = [json.loads(line) for line in handle if line.strip()]
        corpus = [tokenize(f"{c.get('section', '')} {c['text']}") for c in self.chunks]
        self.bm25 = BM25Okapi(corpus)
        self.embeddings = None
        self.cache_path = config.persona_dir(persona_id) / "embeddings.npy"

    def get_embeddings(self):
        """Passage embeddings, loaded from cache or computed and saved if missing/outdated."""
        if self.embeddings is not None:
            return self.embeddings

        if self.cache_path.exists() and self.cache_path.stat().st_mtime >= self.mtime:
            try:
                cached = np.load(self.cache_path)
                if len(cached) == len(self.chunks):
                    self.embeddings = cached
                    return self.embeddings
            except Exception:
                pass  # corrupted or invalid cache; recompute below

        texts = [f"{c['section']}: {c['text']}" if c.get("section") else c["text"]
                 for c in self.chunks]
        model = _get_embedding_model()
        self.embeddings = model.encode(texts, batch_size=64, show_progress_bar=False,
                                       normalize_embeddings=True)
        try:
            np.save(self.cache_path, self.embeddings)
        except OSError:
            pass
        return self.embeddings


def _get_index(persona_id):
    path = config.chunks_path(persona_id)
    with _lock:
        index = _indexes.get(persona_id)
        if index is None or not path.exists() or path.stat().st_mtime != index.mtime:
            index = _Index(persona_id)
            _indexes[persona_id] = index
    return index


def reciprocal_rank_fusion(rankings, k=RRF_K):
    """Combine ranked candidate lists using Reciprocal Rank Fusion.

    Each ranking is a sequence of chunk indices ordered from best to worst.
    Returns a dict mapping chunk_index -> rrf_score.
    """
    scores = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking, 1):
            scores[idx] = scores.get(idx, 0.0) + (1.0 / (k + rank))
    return scores


def retrieve(persona_id, question, k=5, mode=None):
    """The k passages that best match the question, best first.

    mode can be "bm25", "dense", or "hybrid" (defaults to SEARCH_MODE env var, then "bm25").
    """
    search_mode = (mode or get_search_mode()).lower().strip()
    if search_mode not in VALID_SEARCH_MODES:
        search_mode = DEFAULT_SEARCH_MODE

    index = _get_index(persona_id)
    terms = query_terms(persona_id, question)
    if not terms:
        return []

    if search_mode == "bm25":
        scores = index.bm25.get_scores(terms)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        assigned_scores = scores

    elif search_mode == "dense":
        embeddings = index.get_embeddings()
        q_emb = _get_embedding_model().encode(question, normalize_embeddings=True)
        scores = embeddings @ q_emb
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        assigned_scores = scores

    elif search_mode == "hybrid":
        bm25_scores = index.bm25.get_scores(terms)
        bm25_order = [i for i in sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
                      if bm25_scores[i] > 0]

        embeddings = index.get_embeddings()
        q_emb = _get_embedding_model().encode(question, normalize_embeddings=True)
        dense_scores = embeddings @ q_emb
        dense_order = sorted(range(len(dense_scores)), key=lambda i: dense_scores[i], reverse=True)

        rrf = reciprocal_rank_fusion([bm25_order, dense_order], k=RRF_K)
        order = sorted(rrf.keys(), key=lambda i: rrf[i], reverse=True)[:k]
        assigned_scores = rrf

    results = []
    for rank, i in enumerate(order, 1):
        chunk = dict(index.chunks[i])
        chunk["score"] = float(assigned_scores[i])
        chunk["rank"] = rank
        results.append(chunk)
    return results
