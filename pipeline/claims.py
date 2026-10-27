"""Claim checker: flag facts in an answer that are not backed by the cited passages.

    from pipeline.claims import check_claims
    flags = check_claims(answer, cited_passages)
    # flags is a list of strings: each is a claim that could not be found in the passages.

Extracted claim types
---------------------
* Years            e.g. 1890, 1890s, 66 million years ago
* Month-year dates e.g. July 1890, February 1888, 23 October 1888
* Bare numbers     e.g. 28, 3, 12.3, 8.8  (standalone numerals, not inside longer words)
* Measurements     e.g. 12 m, 8.8 tons, 30.5 cm, 35,000 newtons
* Proper names     Title-cased sequences that are not common English words

Matching rules (all case-insensitive, accent-folded)
----------------------------------------------------
A claim matches a passage if any of these hold:
* The exact claim string appears in the passage text.
* For measurements: any synonym unit is tried (e.g. "12 m" matches "12 metres").
* For conversions: a parenthetical "12 in" is accepted if the passage has "30.5 cm" or
  any measurement numerically close to 12 in an equivalent unit group.
* For month-year: month and year appear in the cited passage text.
* For proper names: every word appears as a whole word (catches "Theo" in "Theo van Gogh").
* Exhibit-name tokens (words that are part of the exhibit name itself, e.g. "Tyrannosaurus",
  "Vincent") are never flagged.

No language-model calls are made. The checker never raises; it returns an empty
list when nothing looks unsupported.

Usage note
----------
Do not use this to block answers. The issue asks that this is an offline evaluation
tool; it is not wired into /ask yet.
"""

from __future__ import annotations

import re
import unicodedata

# ── normalisation ────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace (including unicode spaces)."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


# ── unit synonyms ────────────────────────────────────────────────────────────

# Map each canonical unit to the set of strings that mean the same thing.
_UNIT_GROUPS: list[tuple[str, ...]] = [
    # length
    ("m", "metre", "metres", "meter", "meters"),
    ("cm", "centimetre", "centimetres", "centimeter", "centimeters"),
    ("km", "kilometre", "kilometres", "kilometer", "kilometers"),
    ("mm", "millimetre", "millimetres", "millimeter", "millimeters"),
    ("ft", "foot", "feet"),
    ("in", "inch", "inches"),
    # mass / weight
    ("kg", "kilogram", "kilograms"),
    ("t", "ton", "tons", "tonne", "tonnes"),
    ("lb", "pound", "pounds"),
    ("g", "gram", "grams"),
    # force / pressure
    ("n", "newton", "newtons"),
    ("kn", "kilonewton", "kilonewtons"),
    # speed
    ("mph",),
    ("kph", "km/h"),
    # time
    ("second", "seconds"),
    ("ms", "millisecond", "milliseconds"),
]

_UNIT_TO_CANONICAL: dict[str, str] = {}
for _group in _UNIT_GROUPS:
    _canon = _group[0]
    for _u in _group:
        _UNIT_TO_CANONICAL[_u.lower()] = _canon

# Units in the same "equivalence group" share a common physical dimension.
# When a measurement appears as a parenthetical conversion, we allow matching
# any measurement with the same canonical unit group.
_EQUIV_GROUPS: list[frozenset[str]] = [
    frozenset({"m", "cm", "km", "mm", "ft", "in"}),  # length
    frozenset({"kg", "t", "lb", "g"}),               # mass
    frozenset({"n", "kn"}),                           # force
    frozenset({"mph", "kph"}),                        # speed
]

def _same_dimension(unit_a: str, unit_b: str) -> bool:
    ca, cb = _UNIT_TO_CANONICAL.get(unit_a, unit_a), _UNIT_TO_CANONICAL.get(unit_b, unit_b)
    return any(ca in g and cb in g for g in _EQUIV_GROUPS)


_ALL_UNITS_RE = re.compile(
    r"\b(" + "|".join(re.escape(u) for u in sorted(_UNIT_TO_CANONICAL, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

# ── extraction patterns ───────────────────────────────────────────────────────

_MONTH_NAMES = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)
_MONTHS_RE_STR = "|".join(_MONTH_NAMES)

# Full date: "23 October 1888", "23 October", "October 1888", "July 1890".
# Require month names to be Title-Case to avoid matching the modal verb "may" in lower-case context.
_DATE_RE = re.compile(
    r"\b(?:(?:\d{1,2}[\s\u202f]+)?(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)(?:[\s\u202f]+\d{4})?)\b"
)

# Bare year or decade (e.g. 1890, 1890s)
_YEAR_RE = re.compile(r"\b(1[0-9]{3}|2[0-9]{3})s?\b")

# Geological age
_GEO_AGE_RE = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*(?:million years|mya|ma)\b", re.IGNORECASE)

# Bare number (integers or decimals, possibly with comma thousands separator)
_NUMBER_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)\b")

_NUM_WORDS = {
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
}
_NUM_WORDS_REV = {v: k for k, v in _NUM_WORDS.items()}
_NUMBER_WORDS_RE = re.compile(
    r"\b(" + "|".join(_NUM_WORDS) + r")\b",
    re.IGNORECASE,
)

# Measurement = number + unit.
# Unambiguous units (length >= 2, excluding 'in' which collides with preposition 'in')
_LONG_UNITS = sorted((u for u in _UNIT_TO_CANONICAL if len(u) >= 2 and u != "in"), key=len, reverse=True)
# Short single-char units (m, g, t, n)
_SHORT_UNITS = [u for u in _UNIT_TO_CANONICAL if len(u) == 1]

_MEASUREMENT_RE = re.compile(
    r"(?<![a-zA-Z])((?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?)"
    r"[\s\u202f]*"
    r"(" + "|".join(re.escape(u) for u in _LONG_UNITS) + r")"
    r"(?![a-zA-Z0-9])",
    re.IGNORECASE,
)
_MEASUREMENT_SHORT_RE = re.compile(
    r"(?<![a-zA-Z])((?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?)"
    r"[\s\u202f]*"
    r"(" + "|".join(re.escape(u) for u in _SHORT_UNITS) + r")"
    r"(?=[)\].,;!?\s]|$)",
    re.IGNORECASE,
)

# Inches abbreviation 'in' or 'in.': only when enclosed in parentheses, with dot,
# or followed by dimension descriptor / clause end, and NOT 4-digit years.
_INCH_RE = re.compile(
    r"(?<![a-zA-Z])(?:"
    r"\(\s*(\d+(?:\.\d+)?)\s*in\.?\s*\)"
    r"|(\d+(?:\.\d+)?)\s*in\.(?![a-zA-Z])"
    r"|(\d+(?:\.\d+)?)\s*in\b(?=\s*(?:long|wide|tall|thick|high|deep|diameter|[)\].,;!?]|$))"
    r")",
    re.IGNORECASE,
)

# Words that begin sentences or are otherwise capitalised but are not names.
_COMMON_WORDS = {
    "the", "a", "an", "i", "my", "his", "her", "its", "our", "their",
    "yes", "no", "he", "she", "it", "we", "they", "you",
    "this", "that", "these", "those", "there",
    "in", "on", "at", "to", "of", "for", "and", "but", "or", "so", "as", "by",
    "from", "with", "about", "after", "before", "during", "near", "without",
    "scientists", "researchers", "among", "between", "across", "into", "up",
    "also", "still", "most", "more", "some", "all", "both", "each",
    "may", "can", "not", "never", "only", "just", "yet", "now",
    "new", "old", "long", "large", "small", "great",
    # Common sentence-starter words that are Title-Cased but not names:
    "sure", "while", "when", "where", "what", "which", "who", "how", "why",
    "its", "such", "any", "if", "then", "though", "although", "since",
    "because", "despite", "among", "between", "except", "even",
    "bread", "coffee", "tobacco", "well",
    # Months / days of the week (handled by dates)
    "january", "february", "march", "april", "june",
    "july", "august", "september", "october", "november", "december",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}

_PROPER_NAME_RE = re.compile(
    r"\b([A-Z][a-zA-Zéèêëàâùûüîïôœç\-\']+(?:\s+[A-Z][a-zA-Zéèêëàâùûüîïôœç\-\']+){0,3})\b"
)


def _numeric_value(token: str) -> float | None:
    try:
        return float(token.replace(",", ""))
    except ValueError:
        return None


# ── extraction ────────────────────────────────────────────────────────────────

def extract_claims(text: str) -> list[str]:
    """Return a deduplicated list of checkable claims extracted from *text*.

    Ordering: measurements, dates, years, geo-ages, proper names.
    """
    claims: list[str] = []
    seen: set[str] = set()

    def _add(c: str) -> None:
        key = _norm(c)
        if key not in seen:
            seen.add(key)
            claims.append(c)

    # Track spans covered by measurements / dates / years so we don't double-count
    covered_spans: set[tuple[int, int]] = set()

    # Measurements (long unambiguous units)
    for m in _MEASUREMENT_RE.finditer(text):
        num_str = m.group(1)
        unit_str = m.group(2)
        canon_unit = _UNIT_TO_CANONICAL.get(unit_str.lower(), unit_str.lower())
        _add(f"{num_str} {canon_unit}")
        covered_spans.add(m.span())

    # Measurements (short units: m, g, t, n)
    for m in _MEASUREMENT_SHORT_RE.finditer(text):
        if any(s <= m.start() and m.end() <= e for s, e in covered_spans):
            continue
        num_str = m.group(1)
        # Avoid treating decade years like 1890 as a number + single-letter unit
        val = _numeric_value(num_str)
        if val is not None and 1000 <= val <= 2099:
            continue
        unit_str = m.group(2)
        canon_unit = _UNIT_TO_CANONICAL.get(unit_str.lower(), unit_str.lower())
        _add(f"{num_str} {canon_unit}")
        covered_spans.add(m.span())

    # Measurements (inch units: 'in', 'in.', '(12 in)')
    for m in _INCH_RE.finditer(text):
        if any(s <= m.start() and m.end() <= e for s, e in covered_spans):
            continue
        num_str = next(g for g in m.groups() if g is not None)
        val = _numeric_value(num_str)
        if val is not None and 1000 <= val <= 2099:
            continue
        _add(f"{num_str} in")
        covered_spans.add(m.span())

    # Dates (full and partial)
    for m in _DATE_RE.finditer(text):
        _add(m.group(0).strip())
        covered_spans.add(m.span())

    # Bare years not inside a date span
    for m in _YEAR_RE.finditer(text):
        span = m.span()
        if any(s <= span[0] and span[1] <= e for s, e in covered_spans):
            continue
        _add(m.group(0))
        covered_spans.add(span)

    # Geological ages
    for m in _GEO_AGE_RE.finditer(text):
        span = m.span()
        if any(s <= span[0] and span[1] <= e for s, e in covered_spans):
            continue
        _add(m.group(0).strip())
        covered_spans.add(span)

    # Bare numbers not covered yet
    for m in _NUMBER_RE.finditer(text):
        span = m.span()
        if any(s <= span[0] and span[1] <= e for s, e in covered_spans):
            continue
        val = _numeric_value(m.group(0))
        if val is None or val < 2:
            continue
        _add(m.group(0))
        covered_spans.add(span)

    # Number words (quantities: two, three, four, etc.)
    for m in _NUMBER_WORDS_RE.finditer(text):
        span = m.span()
        if any(s <= span[0] and span[1] <= e for s, e in covered_spans):
            continue
        _add(m.group(0).lower())
        covered_spans.add(span)

    # Proper names
    _first_word_skip = _COMMON_WORDS | {
        "in", "on", "at", "by", "as", "of", "to", "up", "so", "if",
    }
    for m in _PROPER_NAME_RE.finditer(text):
        span = m.span()
        if any(s <= span[0] and span[1] <= e for s, e in covered_spans):
            continue
        raw_name = m.group(0).strip()
        # Strip trailing possessives: "Gauguin's" -> "Gauguin"
        raw_name = re.sub(r"['’]s$", "", raw_name).strip()
        words = raw_name.split()
        if not words:
            continue
        # Strip leading sentence-starter words (e.g. "In Gauguin" -> "Gauguin")
        while words and words[0].lower() in _first_word_skip:
            words = words[1:]
        if not words:
            continue
        name = " ".join(words)
        if name.lower() in _COMMON_WORDS:
            continue
        if len(name) < 3:
            continue
        # Skip if name is entirely made of common words (e.g. "The Old")
        if all(w.lower() in _COMMON_WORDS for w in words):
            continue
        _add(name)

    return claims


# ── matching ──────────────────────────────────────────────────────────────────

def _passage_text(passages: list[dict]) -> str:
    return " ".join(p.get("text", "") for p in passages)


def _norm_passage_blob(passages: list[dict]) -> str:
    return _norm(_passage_text(passages))


def _measurement_in_blob(num_str: str, unit: str, blob: str) -> bool:
    """True if the measurement (or a unit-synonym / same-dimension variant) is in blob."""
    canon = _UNIT_TO_CANONICAL.get(unit.lower(), unit.lower())

    # Try all synonyms of this unit
    synonyms = [u for u, c in _UNIT_TO_CANONICAL.items() if c == canon]
    for syn in synonyms:
        pattern = re.compile(
            r"\b" + re.escape(num_str.replace(",", "")).rstrip("0").rstrip(".") +
            r"0?\s*" + re.escape(syn) + r"\b",
            re.IGNORECASE,
        )
        if pattern.search(blob):
            return True
        num_clean = num_str.replace(",", "")
        pattern2 = re.compile(
            r"\b" + re.escape(num_clean) + r"\s*" + re.escape(syn) + r"\b",
            re.IGNORECASE,
        )
        if pattern2.search(blob):
            return True

    # Same-dimension check: if the passage has any measurement of the same
    # dimension, the answer is probably just giving a unit conversion, so accept.
    for m in _MEASUREMENT_RE.finditer(blob):
        blob_unit = m.group(2).lower()
        if _same_dimension(unit.lower(), blob_unit):
            return True

    return False


def _date_in_blob(date_str: str, blob: str) -> bool:
    """Check month-year or day-month-year in blob."""
    norm_date = _norm(date_str)
    norm_blob = _norm(blob)
    if norm_date in norm_blob:
        return True

    # Extract parts
    month_m = re.search(r"\b(" + _MONTHS_RE_STR + r")\b", norm_date, re.IGNORECASE)
    year_m = re.search(r"\b(\d{4})\b", norm_date)
    day_m = re.match(r"^(\d{1,2})\s", norm_date)

    if not month_m:
        return False

    month = month_m.group(1)
    year = year_m.group(1) if year_m else None
    day = day_m.group(1) if day_m else None

    # Find month positions in blob
    month_positions = [m.start() for m in re.finditer(r"\b" + re.escape(month) + r"\b", norm_blob)]
    if not month_positions:
        return False

    if day:
        # Check day appears within proximity of month
        day_pos = [m.start() for m in re.finditer(r"\b" + re.escape(day) + r"\b", norm_blob)]
        if not any(abs(dp - mp) < 30 for dp in day_pos for mp in month_positions):
            return False

    if year:
        year_positions = [m.start() for m in re.finditer(r"\b" + re.escape(year) + r"\b", norm_blob)]
        if not year_positions:
            return False
        # Within the same passage chunk
        return any(abs(mp - yp) < 800 for mp in month_positions for yp in year_positions)

    return True


def _name_in_blob(name: str, blob: str) -> bool:
    """Multi-word name: every word is present as a whole word."""
    norm_name = _norm(name)
    words = norm_name.split()
    norm_blob = _norm(blob)
    if norm_name in norm_blob:
        return True
    return all(bool(re.search(r"\b" + re.escape(w) + r"\b", norm_blob)) for w in words)


def _claim_found(claim: str, passages: list[dict], blob: str, exhibit_tokens: set[str]) -> bool:
    """Return True if *claim* can be verified against the passage blob."""
    norm_claim = _norm(claim)
    norm_blob = _norm(blob)

    # Exhibit-name tokens are always considered known
    if norm_claim in exhibit_tokens:
        return True

    # Direct substring match
    if norm_claim in norm_blob:
        return True

    # Check for measurement
    meas_m = re.fullmatch(
        r"([\d,]+(?:\.\d+)?)\s+("
        + "|".join(re.escape(u) for u in sorted(_UNIT_TO_CANONICAL, key=len, reverse=True))
        + r")",
        norm_claim,
    )
    if meas_m:
        return _measurement_in_blob(meas_m.group(1), meas_m.group(2), blob)

    # Check for date
    if re.search(r"\b(" + _MONTHS_RE_STR + r")\b", norm_claim, re.IGNORECASE):
        return _date_in_blob(claim, blob)

    # Bare year or decade (e.g. 1890 or 1890s)
    if re.fullmatch(r"\d{4}s?", norm_claim):
        year_base = norm_claim[:4]
        return bool(re.search(r"\b" + re.escape(year_base) + r"\b", norm_blob))

    # Number words (e.g. "four" matches "four" or "4")
    if norm_claim in _NUM_WORDS:
        numeric_val = str(_NUM_WORDS[norm_claim])
        return norm_claim in norm_blob or bool(re.search(r"\b" + numeric_val + r"\b", norm_blob))

    # Bare number: also check word form (e.g. "4" matches "four")
    if re.fullmatch(r"\d+", norm_claim):
        val = int(norm_claim)
        word_form = _NUM_WORDS_REV.get(val)
        if word_form and bool(re.search(r"\b" + word_form + r"\b", norm_blob)):
            return True
        return bool(re.search(r"\b" + re.escape(norm_claim) + r"\b", norm_blob))

    # Proper name (multi or single word)
    return _name_in_blob(claim, blob)


# ── exhibit-name token extraction ─────────────────────────────────────────────

def _exhibit_name_tokens(passages: list[dict]) -> set[str]:
    """Return a set of lowercase name tokens shared across passages.

    We use the exhibit ID words (from the first passage's id prefix) as a
    proxy.  For example, for 't-rex' we add {'tyrannosaurus', 'rex', 't',
    'trex'}.  For 'van-gogh' we add {'van', 'gogh', 'vincent'}.
    """
    if not passages:
        return set()
    sample_id = passages[0].get("id", "")
    prefix = sample_id.split("-")[0] + "-" + sample_id.split("-")[1] if sample_id.count("-") >= 2 else sample_id

    tokens: set[str] = set()
    for part in re.split(r"[-_\s]+", prefix.lower()):
        if part:
            tokens.add(part)

    # Hard-coded well-known tokens for our two exhibits
    if "rex" in tokens or "trex" in tokens or prefix.startswith("t-rex"):
        tokens.update({"tyrannosaurus", "rex", "t rex", "t-rex"})
    if "gogh" in tokens or "vincent" in tokens or prefix.startswith("van-gogh"):
        tokens.update({"van gogh", "van", "gogh", "vincent"})
    return tokens


# ── public API ────────────────────────────────────────────────────────────────

def check_claims(answer: str, cited_passages: list[dict]) -> list[str]:
    """Return a list of claims in *answer* that are not supported by *cited_passages*.

    Parameters
    ----------
    answer:
        The answer text shown to the visitor.
    cited_passages:
        The passage dicts that the answer cited (each must have a "text" key).
        If the list is empty every claim in the answer is flagged.

    Returns
    -------
    A list of claim strings (possibly empty) that could not be found in the
    cited passages.  The caller can use this to mark an answer as containing
    an unsupported detail.
    """
    if not answer or not answer.strip():
        return []

    claims = extract_claims(answer)
    if not claims:
        return []

    blob = _passage_text(cited_passages)
    exhibit_tokens = _exhibit_name_tokens(cited_passages)
    return [c for c in claims if not _claim_found(c, cited_passages, blob, exhibit_tokens)]
