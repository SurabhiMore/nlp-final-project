import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import quantiles

from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import classifier, config  # noqa: E402

# ASSUMPTION: adjust these to match the real log schema in logs/qa_log.jsonl.
Q_KEYS = ("question", "query", "text")
EXHIBIT_KEYS = ("persona", "persona_id", "exhibit")
STATUS_KEYS = ("status", "outcome", "result")
LATENCY_KEYS = ("total_ms", "latency_ms", "total_latency_ms")
STATUSES = ("answered", "declined", "not_in_sources", "outside_time")

SIMILARITY_THRESHOLD = 85


def _get(row, keys, default=None):
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return default


def _normalize_status(raw):
    s = str(raw or "").lower().strip()
    if "not_in" in s or "no_source" in s:
        return "not_in_sources"
    if "outside" in s:
        return "outside_time"
    if "declin" in s or "refus" in s:
        return "declined"
    return "answered"


def read_log(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip corrupt lines instead of crashing
            if isinstance(row, dict):
                rows.append(row)
    return rows


def top_questions(questions, n=10):
    """Greedy fuzzy clustering; returns [{question, count}, ...]."""
    clusters = []
    for q in questions:
        norm = " ".join(q.lower().split())
        if not norm:
            continue
        for c in clusters:
            if fuzz.token_sort_ratio(norm, c["norm"]) >= SIMILARITY_THRESHOLD:
                c["count"] += 1
                break
        else:
            clusters.append({"question": q.strip(), "count": 1, "norm": norm})
    clusters.sort(key=lambda c: -c["count"])
    return [{"question": c["question"], "count": c["count"]} for c in clusters[:n]]


# ---------------------------------------------------------------- topics (issue #61)
#
# Curators want to know what visitors are curious about, not only which questions repeat, so
# every question gets one topic. Shared topics come first, then the ones for the exhibit's
# subject_type in persona.json, so a new person or creature gets the same topics, and the first
# match wins. An exhibit we can't load is checked against every topic. The patterns were
# written on eval/questions/topics/dev.jsonl and measured once on the held-out test.jsonl
# (python -m eval.eval_topics). Off-topic questions and years after the exhibit's time are
# also caught by the classifier's rules (pipeline/classifier.py).

OTHER = "other"
TOPIC_LABELS = {
    "off_topic": "Not about the exhibit",
    "the_guide": "The guide itself",
    "after_their_time": "After their time",
    "works": "Works and how they were made",
    "letters_quotes": "Letters and quotes",
    "people": "Family and friends",
    "life": "Life, places and money",
    "health_death": "Health and death",
    "body": "Body, senses and sounds",
    "food_hunting": "Food and hunting",
    "habitat_life": "Where and how they lived",
    "death_extinction": "Death and extinction",
    "fossils": "Fossils, names and science",
    OTHER: "Other or unclear",
}


def _words(*words):
    return r"\b(?:" + "|".join(words) + r")\b"


# (topic, subject types it applies to or None for every exhibit, pattern), in the order they are tried.
_TOPIC_RULES = [(topic, kinds, re.compile(pattern)) for topic, kinds, pattern in [
    ("off_topic", None,
     r"^what(?:'s| is) the capital of\b|\bmy (?:\w+ ){0,2}(?:homework|essay|assignment|test|exam)\b|\d+\s*(?:times"
     r"|plus|minus|x)\s*\d+|" + _words("jokes?", "recipes?", "python", "code", "stock price", "world cup",
                                     "book me a table", "tallest mountain", "continents", "president",
                                     "opening hours")),
    ("the_guide", None,
     r"^(?:hi|hello|hey|good (?:morning|afternoon|evening)|greetings)\b|\b(?:who|what) are you\b"
     r"|\bare you (?:a |an |really |truly )?(?:real|ai|robot|human|alive|person|machine|computer)\b"
     r"|\byou are (?:truly|really|just|actually)\b|\bcan you (?:roar|sing|speak|talk|say)\b|\bin (?:spanish|hindi"
     r"|marathi|kannada|french|german)\b|" + _words("introduce yourself", "language model", "system prompt",
                                                  "your instructions", "which company", "stop pretending")),
    ("after_their_time", None,
     _words("films?", "movies?", "cinema", "tv", "television", "radio", "internet", "smartphones?", "cars?",
            "airplanes?", "aeroplanes?", "wright brothers", "m[eé]tro", "titanic", "world war", "einstein",
            "relativity", "picasso", "matisse", "warhol", "water lilies", "moon landing", "jurassic park", "today",
            "nowadays", "these days", "modern")),
    ("after_their_time", {"creature"}, _words("humans?", "people")),
    ("after_their_time", {"person"},
     _words("auctions?", "museum of modern art", "moma", "van gogh museum", "mus[eé]e d'orsay", "orsay", "famous",
            "fame", "millions?", "kirk douglas", "lust for life", "loving vincent", "don mclean")),
    # Person topics.
    ("letters_quotes", {"person"},
     r"\b(?:did|do) you (?:really |ever |once )?(?:say|write)\b|\byou (?:really |ever |once )?(?:said|wrote)\b|"
     + _words("letters?", "quotes?", "quotation")),
    ("works", {"person"},
     r"\bpaint(?:s|ed|ing|ings)?\b|\b(?:major|first|best|last) work\b|\bthe way you work(?:ed)?\b|"
     + _words("drawings?", "draw", "drew", "sketch\\w*", "canvas(?:es)?", "brush\\w*", "colou?rs?", "yellow", "blue",
              "red", "green", "purple", "style", "technique", "materials?", "perspective", "inspir\\w*",
              "artworks?", "masterpieces?", "portraits?", "self-portraits?", "versions?", "starry night",
              "sunflowers?", "irises", "bedroom", "wheat ?fields?", "cypress(?:es)?", "yellow house", "sower",
              "chairs?", "vineyard", "potato eaters", "woodcuts?", "japanese prints?", "sold", "sell", "selling",
              "buyers?")),
    ("health_death", {"person"},
     _words("ears?", "razor", "ill", "illness", "sick", "sickness", "disease", "asylum", "hospital", "doctors?",
            "physician", "gachet", "mental", "madness", "seizures?", "epilep\\w*", "injur\\w*", "die", "died",
            "dying", "death", "dead", "shot", "gun", "suicide", "last words", "grave", "buried", "funeral",
            "final days", "end of (?:his|your) life", "health")),
    ("people", {"person"},
     _words("theo", "brothers?", "sisters?", "father", "mother", "parents?", "family", "cousins?", "uncle", "aunt",
            "gauguin", "bernard", "mauve", "friends?", "friendship", "wife", "married", "marry", "love", "lovers?",
            "children", "son", "daughter", "relationship", "meet", "met")),
    ("life", {"person"},
     _words("born", "birth", "childhood", "child", "boy", "grow up", "grew up", "school", "young", "home",
            "house", "live", "lived", "living", "move[ds]?", "moving", "arrive[ds]?", "arrival", "stay(?:ed|ing)?",
            "visit\\w*", "travel\\w*", "paris", "arles", "auvers(?:-sur-oise)?", "zundert", "hague", "antwerp",
            "london", "nuenen", "borinage", "amsterdam", "saint-r[eé]my", "netherlands", "holland", "belgium",
            "france", "countryside", "missionary", "preach\\w*", "church", "jobs?", "work as", "worked as",
            "dealer", "money", "poor", "poverty", "rich", "food", "eat", "ate", "diet", "dog", "pets?",
            "telephone", "camera", "kodak", "eiffel")),
    # Creature topics.
    ("death_extinction", {"creature"},
     _words("extinct\\w*", "asteroid", "meteor\\w*", "chicxulub", "die", "died", "dying", "death", "dead", "how old")),
    ("fossils", {"creature"},
     _words("fossils?", "skeletons?", "bones?", "sue", "specimens?", "found", "discover\\w*", "dig", "dug",
            "excavat\\w*", "formation", "rock", "names?", "named", "nickname", "museum", "smithsonian",
            "collection", "casts?", "scientists?", "relatives?", "auction", "paid", "pay")),
    ("food_hunting", {"creature"},
     _words("eat", "eats", "ate", "eating", "food", "hunt\\w*", "prey", "scaveng\\w*", "kill\\w*", "meat",
            "triceratops", "fight\\w*", "attack\\w*", "packs?")),
    ("habitat_life", {"creature"},
     _words("live", "lived", "living", "alive", "habitat", "world", "climate", "weather", "cretaceous",
            "dinosaurs?", "eggs?", "nests?", "hatch\\w*", "young", "sleep\\w*", "alone", "groups?")),
    ("body", {"creature"},
     _words("big", "bigger", "biggest", "size", "tall", "tallest", "long", "length", "heavy", "weigh\\w*",
            "kilos?", "tons?", "tonnes?", "teeth", "tooth", "bite", "jaws?", "skull", "head", "arms?", "hands?",
            "fingers?", "claws?", "legs?", "tail", "skin", "scales", "feathers?", "eyes?", "vision", "see",
            "smell\\w*", "hear\\w*", "brain", "clever", "smart", "fast", "run", "speed", "roar\\w*", "sound\\w*",
            "temperature", "warm-blooded", "metabolism", "colou?rs?", "strong\\w*", "male", "female")),
]]

_personas = {}


def _persona(exhibit):
    """The exhibit's persona.json, or None when it can't be loaded (an old or made-up exhibit id)."""
    if exhibit not in _personas:
        try:
            _personas[exhibit] = config.load_persona(exhibit)
        except Exception:
            _personas[exhibit] = None
    return _personas[exhibit]


def topic_of(question, exhibit=None):
    """The topic of one visitor question, one of TOPIC_LABELS."""
    text = " ".join(str(question or "").lower().replace("’", "'").split())
    if not text:
        return OTHER
    persona = _persona(exhibit) if exhibit else None
    kind = persona["subject_type"] if persona else None
    if persona:
        label = classifier.classify(text, persona)["label"]
        if label == classifier.OFF_TOPIC:
            return "off_topic"
        if label == classifier.OUT_OF_TIME:
            return "after_their_time"
    for topic, kinds, pattern in _TOPIC_RULES:
        if (kinds is None or kind is None or kind in kinds) and pattern.search(text):
            return topic
    return OTHER


def top_topics(entries, samples=3):
    """Group (exhibit, question, text_to_tag, status) entries by topic, most asked first.

    Returns [{topic, label, count, not_in_sources, exhibits, samples}, ...]. text_to_tag is the
    English search query for a question in another language, so its keywords can match.
    """
    groups = {}
    for exhibit, question, text, status in entries:
        topic = topic_of(text or question, exhibit)
        group = groups.setdefault(topic, {"topic": topic, "label": TOPIC_LABELS[topic], "count": 0,
                                          "not_in_sources": 0, "exhibits": {}, "samples": []})
        group["count"] += 1
        group["not_in_sources"] += status == "not_in_sources"
        group["exhibits"][exhibit] = group["exhibits"].get(exhibit, 0) + 1
        seen = {" ".join(s.lower().split()) for s in group["samples"]}
        if len(group["samples"]) < samples and " ".join(question.lower().split()) not in seen:
            group["samples"].append(question.strip())
    return sorted(groups.values(), key=lambda g: (-g["count"], g["label"]))


def _percentiles(values):
    if not values:
        return {"p50": 0, "p95": 0}
    if len(values) == 1:
        return {"p50": round(values[0]), "p95": round(values[0])}
    cuts = quantiles(values, n=100, method="inclusive")
    return {"p50": round(cuts[49]), "p95": round(cuts[94])}


def compute_stats(log_path):
    """Stats for one log, or several logs read together (a list of paths)."""
    paths = log_path if isinstance(log_path, (list, tuple)) else [log_path]
    rows = [row for path in paths for row in read_log(path)]
    per_exhibit = defaultdict(lambda: dict.fromkeys(STATUSES, 0))
    all_questions, gap_questions, latencies, topic_entries = [], [], [], []

    for row in rows:
        question = str(_get(row, Q_KEYS, "") or "")
        exhibit = str(_get(row, EXHIBIT_KEYS, "unknown"))
        status = _normalize_status(_get(row, STATUS_KEYS))
        per_exhibit[exhibit][status] += 1
        if question:
            all_questions.append(question)
            topic_entries.append((exhibit, question, str(row.get("search_query") or question), status))
            if status == "not_in_sources":
                gap_questions.append(question)
        timings = row.get("timings")
        lat = _get(timings, LATENCY_KEYS) if isinstance(timings, dict) else None
        if lat is None:
            lat = _get(row, LATENCY_KEYS)
        if isinstance(lat, (int, float)):
            latencies.append(lat)

    return {
        "total_questions": len(rows),
        "per_exhibit": dict(per_exhibit),
        "top_questions": top_questions(all_questions),
        "top_not_in_sources": top_questions(gap_questions),
        "top_topics": top_topics(topic_entries),
        "latency_ms": _percentiles(latencies),
    }
