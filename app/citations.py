"""The sentence of a cited passage that backs an answer.

/ask sends the first 220 characters of each cited passage as its snippet, which is
often not the part the answer used. best_quote picks the sentence of the passage that
shares the most words with the answer, so the live page can show the line the answer
rests on (a letter writing itself, for example).
"""

import re

_WORD = re.compile(r"[\w']+", re.UNICODE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# "T. rex" and "H. F. Osborn" should not end a sentence.
_INITIAL = re.compile(r"(?:^|\s)[A-Z]\.$")
_STOP = set(
    "a an and are as at be been but by for from had has have he her his i in is it its me my of on or "
    "our she so than that the their them then there they this to was we were what when which who with "
    "would you your about also could some".split()
)


def _sentences(passage):
    pieces = [p.strip() for p in _SENTENCE_END.split(passage or "") if p.strip()]
    merged = []
    for piece in pieces:
        if merged and _INITIAL.search(merged[-1]):
            merged[-1] = merged[-1] + " " + piece
        else:
            merged.append(piece)
    return merged


def _content_words(text):
    return {w for w in _WORD.findall((text or "").lower()) if w not in _STOP}


def best_quote(passage, answer, limit=320):
    """The sentence of `passage` with the most words in common with `answer`.

    Ties go to the earlier sentence. Sentences longer than `limit` characters are cut
    at a word boundary and end with an ellipsis. Returns "" for an empty passage.
    """
    sentences = _sentences(passage)
    if not sentences:
        return ""
    wanted = _content_words(answer)
    best = max(sentences, key=lambda s: len(wanted & _content_words(s)))
    if len(best) > limit:
        best = best[:limit].rsplit(" ", 1)[0] + "…"
    return best
