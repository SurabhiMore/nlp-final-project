"""Time-boundary check: flag questions about things from after the exhibit's time.

    python -m pipeline.timecheck "What did you think of Guernica?" --persona van-gogh
    python -m pipeline.timecheck "..." --persona van-gogh --offline   # cache only, no network

How it works:
  1. Find names, works and events in the question (spaCy if installed, otherwise
     runs of capitalised words), plus any explicit year ("the 1956 film").
  2. Look each name up on Wikidata (top 3 matches) and get its earliest date from
     date of birth (P569), inception (P571), publication date (P577), point in
     time (P585) or start time (P580).
  3. Flag the question if an explicit year is after the exhibit's end year, or if
     EVERY dated Wikidata match for a name is after it. Requiring every match keeps
     ambiguous names such as "Theo" or "Paris" from being flagged.

Names Wikidata does not know, or that have no date, are never flagged.
Every Wikidata answer is cached in eval/fixtures/wikidata_cache.json, so tests
and evaluations run offline once the cache is filled.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config  # noqa: E402

CACHE_PATH = config.EVAL_DIR / "fixtures" / "wikidata_cache.json"
API_URL = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "EchoesAI-museum-guide/0.1 (university NLP project)"}
DATE_PROPERTIES = ("P569", "P571", "P577", "P585", "P580")
ENTITY_LABELS = {"PERSON", "ORG", "GPE", "LOC", "EVENT", "WORK_OF_ART", "PRODUCT", "FAC", "NORP", "LAW"}
YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})s?\b")
CAPS_RE = re.compile(r"\b[A-Z][\w'.-]*(?:\s+(?:of|the|for|de|van|von)?\s*[A-Z][\w'.-]*)*")
STOPWORDS = {"What", "Who", "When", "Where", "Why", "How", "Did", "Do", "Does", "Have", "Has", "Is",
             "Are", "Was", "Were", "Can", "Could", "Would", "Will", "I", "You", "Your", "The", "A", "An",
             "Tell", "Please", "Describe", "Explain", "In", "On", "At"}
TOP_K = 3

_nlp = None


# ---------------------------------------------------------------- cache

class WikidataCache:
    """A JSON file of Wikidata answers. offline=True never calls the network:
    a miss returns None, which the check treats as an unknown name (no flag)."""

    def __init__(self, path=CACHE_PATH, offline=False):
        self.path = Path(path)
        self.offline = offline
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        self.hits = 0
        self.misses = 0

    def get(self, key, fetch):
        if key in self.data:
            self.hits += 1
            return self.data[key]
        self.misses += 1
        if self.offline:
            return None
        value = fetch()
        self.data[key] = value
        self.save()
        return value

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- Wikidata

PAUSE = 1.0  # seconds between requests, so Wikidata does not rate-limit us


def _get(params, retries=6):
    """GET the Wikidata API. On 429 (too many requests) or a server error, wait
    (Retry-After, or 2, 4, 8... seconds) and try again."""
    for attempt in range(retries):
        r = requests.get(API_URL, headers=HEADERS, timeout=20, params=params)
        if r.status_code == 429 or r.status_code >= 500:
            wait = r.headers.get("Retry-After")
            time.sleep(min(float(wait) if wait and wait.isdigit() else 2 ** (attempt + 1), 60))
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()
    r.raise_for_status()
    raise RuntimeError(f"Wikidata kept refusing after {retries} tries: {r.status_code}")


def _search_online(text):
    data = _get({"action": "wbsearchentities", "search": text, "language": "en",
                 "type": "item", "limit": TOP_K, "format": "json"})
    return [hit["id"] for hit in data.get("search", [])]


def _year_online(qid):
    data = _get({"action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"})
    claims = data["entities"][qid].get("claims", {})
    years = []
    for prop in DATE_PROPERTIES:
        for claim in claims.get(prop, []):
            value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            if isinstance(value, dict) and "time" in value:
                years.append(parse_year(value["time"]))
    return min(years) if years else None


def parse_year(wikidata_time):
    """'+1937-01-01T00:00:00Z' -> 1937, '-0066000000-00-00T00:00:00Z' -> -66000000."""
    sign = -1 if wikidata_time.startswith("-") else 1
    return sign * int(wikidata_time.lstrip("+-").split("-", 1)[0])


def search(text, cache):
    return cache.get(f"search:{text.lower()}", lambda: _search_online(text)) or []


def entity_year(qid, cache):
    return cache.get(f"year:{qid}", lambda: _year_online(qid))


# ---------------------------------------------------------------- mentions

def _spacy():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            _nlp = False
    return _nlp


def extract_mentions(question, use_spacy=True):
    nlp = _spacy() if use_spacy else False
    if nlp:
        found = [ent.text for ent in nlp(question).ents if ent.label_ in ENTITY_LABELS]
    else:
        found = [m.group(0).strip() for m in CAPS_RE.finditer(question)]
    # Quoted titles, e.g. 'Vincent (Starry, Starry Night)'
    found += re.findall(r"(?:^|\s)['\"‘“](.{3,}?)['\"’”](?=[\s?.,!]|$)", question)
    # "Picasso's Guernica" -> "Picasso", "Guernica"
    found = [part.strip() for text in found for part in re.split(r"['’]s\b", text) if part.strip()]
    cleaned, seen = [], set()
    for text in found:
        words = text.split()
        while words and words[0] in STOPWORDS:
            words.pop(0)
        text = " ".join(words).strip(" ?.,!'\"")
        if len(text) > 1 and text.lower() not in seen and not YEAR_RE.fullmatch(text):
            seen.add(text.lower())
            cleaned.append(text)
    return cleaned


# ---------------------------------------------------------------- the check

def end_year(persona):
    return persona.get("time_period", {}).get("end_year")


def check_time(question, persona, cache=None, use_spacy=True):
    """Return {"flag": bool, "end_year", "reasons": [...], "entities": [...]}.

    A persona without time_period.end_year is never flagged (T. rex for now).
    """
    end = end_year(persona)
    result = {"flag": False, "end_year": end, "reasons": [], "entities": []}
    if end is None:
        result["reasons"].append("no end_year in persona.json, check skipped")
        return result
    cache = cache or WikidataCache()

    for match in YEAR_RE.finditer(question):
        year = int(match.group(1))
        if year > end:
            result["flag"] = True
            result["reasons"].append(f"the question names the year {year}, after {end}")

    own_names = {w.lower() for w in persona.get("name", "").split()}
    for mention in extract_mentions(question, use_spacy=use_spacy):
        if mention.lower() in own_names or mention.lower() == persona.get("name", "").lower():
            continue
        candidates = [{"qid": qid, "year": entity_year(qid, cache)} for qid in search(mention, cache)]
        result["entities"].append({"text": mention, "candidates": candidates})
        years = [c["year"] for c in candidates if c["year"] is not None]
        if years and min(years) > end:
            result["flag"] = True
            result["reasons"].append(f"'{mention}': every Wikidata match dates after {end} (earliest {min(years)})")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("question")
    parser.add_argument("--persona", required=True)
    parser.add_argument("--offline", action="store_true", help="use the cache only")
    args = parser.parse_args()
    persona = json.loads((config.PERSONAS_DIR / args.persona / "persona.json").read_text(encoding="utf-8"))
    print(json.dumps(check_time(args.question, persona, WikidataCache(offline=args.offline)), indent=2))


if __name__ == "__main__":
    main()
