"""Decide whether a question needs the search and the language model at all.

    from pipeline.classifier import classify
    classify("What is 17 times 23?", persona)   # {"label": "off_topic", "reason": "..."}

classify returns one of three labels, using a few rules and no language model:

    off_topic    a question that is clearly about something else: maths, homework,
                 shopping, today's weather or a quiz question
    out_of_time  the exhibit wrote in its own words (today, Van Gogh) and the question
                 names a year after its end_year, such as "the 1956 film"
    in_domain    everything else, which goes through the pipeline as usual

Blocking a real question is worse than letting a borderline one through, because the
language model declines those anyway. So the patterns are narrow, anything uncertain is
in_domain, and classify never raises. Questions that mention the exhibit or the museum, or
say "your", are never off topic, and a question that talks about the visitor ("I saw it in
2019") is never out of time. The patterns are in English, so a question in another
language always goes through.

short_circuit turns a label into a reply, using the same fixed lines as the reply check.
/ask and eval/eval_answers.py both call it, so the north star measures what the product
does. Set ENABLE_CLASSIFIER=0 to switch it off. python -m eval.eval_classifier scores it.
"""

import os
import re

from pipeline import persona as engine

IN_DOMAIN = "in_domain"
OFF_TOPIC = "off_topic"
OUT_OF_TIME = "out_of_time"
MODEL_LABEL = "classifier"
_STATUS = {OFF_TOPIC: "declined", OUT_OF_TIME: "outside_time"}

_NUMBER = r"-?\d[\d.,]*"
_OPERATOR = r"(?:times|plus|minus|multiplied by|divided by|over|x|\*|\+|-|/)"
_DEVICE = r"(?:phone|laptop|computer|tablet|tv|television|headphones|camera|car)"
_NOW = r"(?:today|tomorrow|tonight|now|right now|outside|this week|this weekend|here)"
# Whole-question patterns where possible, so "How many times did you paint..." can't match.
_OFF_TOPIC = [
    ("maths", re.compile(rf"^(?:what(?:'?s| is)|how much is|calculate|compute|work out)?\s*{_NUMBER}\s*{_OPERATOR}\s*"
                         rf"{_NUMBER}\s*(?:equals?|is|=)?(?:\s*what)?$")),
    ("maths", re.compile(rf"^(?:what(?:'?s| is)|calculate|compute)\s+the\s+square\s+root\s+of\s+{_NUMBER}$")),
    ("maths", re.compile(r"\bsolve\b.*(?:=|\bfor x\b|\bequation\b)")),
    ("homework", re.compile(r"\b(?:help|do|write|finish|check|fix)\b.*\bmy\s+(?:\w+\s+){0,2}"
                            r"(?:homework|assignment|essay|coursework)\b")),
    ("shopping", re.compile(rf"\b(?:recommend|suggest)\s+(?:me\s+)?(?:a|an|some|the)\s+(?:\w+\s+){{0,3}}?"
                            rf"(?:{_DEVICE}|\w+\s+to buy)\b")),
    ("shopping", re.compile(r"\bshould i (?:buy|purchase)\b")),
    ("shopping", re.compile(rf"^(?:what(?:'?s| is)|which(?: is)?)\s+(?:the\s+)?(?:best|cheapest)\s+(?:\w+\s+)?{_DEVICE}\b")),
    ("weather", re.compile(rf"^(?:what(?:'?s| is)|how(?:'?s| is))\s+the\s+weather(?:\s+like)?(?:\s+{_NOW})?$")),
    ("weather", re.compile(rf"\b(?:is it|will it|is it going to)\s+(?:be\s+)?(?:rain|snow|sunny|cold|hot)\w*\s+{_NOW}$")),
    ("weather", re.compile(r"\bweather forecast\b")),
    ("quiz", re.compile(r"^what(?:'?s| is)\s+the\s+(?:capital|currency)(?:\s+city)?\s+of\s+(?!.*\byou\b)")),
    ("quiz", re.compile(r"^who(?:'?s| is)\s+the\s+(?:current\s+)?(?:president|prime minister)\b(?!.*\byou\b)")),
]
# The prompt counts questions about the exhibit or the museum as on topic.
_ABOUT_EXHIBIT = re.compile(r"\b(?:your|yours|yourself|museum|gallery|exhibit|exhibition)\b")

_YEAR = r"(1\d{3}|2[01]\d{2})"
# "2100 artworks" and "2000 kg" are amounts, not years.
_AMOUNT = (r"(?:bc|bce|kg|kgs|kilos?|kilograms?|pounds?|lbs?|tons?|tonnes?|km|kilometres?|kilometers?|miles?|metres?|"
           r"meters?|feet|foot|francs?|guilders?|dollars?|euros?|paintings?|pictures?|works?|artworks?|drawings?|"
           r"sketches|letters?|people|visitors|years?|days?|times|bones?|teeth)")
_YEAR_NAMED = re.compile(rf"\b(?:in|of|since|after|from|by|until|till|around|circa|year)\s+{_YEAR}\b(?!\s+{_AMOUNT}\b)"
                         rf"|(?:\bthe|\ba|\ban|\byour|'s)\s+{_YEAR}\s+(?!{_AMOUNT}\b)[a-z]")
_VISITOR = re.compile(r"\b(?:i|i'm|i've|i'd|my|we|our)\b")


def _clean(question):
    text = question.lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip().strip("?!. ")


def _later_year(text, persona):
    """The first year named in the text that is after the exhibit's end_year, or None."""
    if persona.get("perspective") != "own_words":
        return None
    end_year = persona.get("time_period", {}).get("end_year")
    if end_year is None or _VISITOR.search(text):
        return None
    for match in _YEAR_NAMED.finditer(text):
        year = int(match.group(1) or match.group(2))
        if year > end_year:
            return year
    return None


def _off_topic_kind(text, persona):
    """Which kind of off-topic question the text is, or None."""
    name_words = {w for w in re.findall(r"[a-z]+", persona.get("name", "").lower()) if len(w) > 2}
    if _ABOUT_EXHIBIT.search(text) or name_words & set(re.findall(r"[a-z]+", text)):
        return None
    return next((kind for kind, pattern in _OFF_TOPIC if pattern.search(text)), None)


def classify(question, persona):
    """Label one question for one exhibit (its persona.json). Returns {"label", "reason"} and never raises."""
    try:
        if not isinstance(question, str) or not question.strip():
            return {"label": IN_DOMAIN, "reason": "no question to check"}
        text = _clean(question)
        persona = persona or {}
        year = _later_year(text, persona)
        if year:
            end_year = persona["time_period"]["end_year"]
            return {"label": OUT_OF_TIME, "reason": f"names the year {year}, after the exhibit's end year {end_year}"}
        kind = _off_topic_kind(text, persona)
        if kind:
            return {"label": OFF_TOPIC, "reason": f"matches the {kind} patterns"}
        return {"label": IN_DOMAIN, "reason": "no rule matched"}
    except Exception as error:  # a bug here must never stop a visitor's question
        return {"label": IN_DOMAIN, "reason": f"could not check: {type(error).__name__}"}


def enabled():
    return os.getenv("ENABLE_CLASSIFIER", "1").strip().lower() not in ("0", "false", "no", "off")


def short_circuit(question, persona, mode="persona"):
    """The reply to give without search or the language model, or None to run the pipeline as usual."""
    if not enabled():
        return None
    status = _STATUS.get(classify(question, persona)["label"])
    if status is None:
        return None
    return {"answer": engine._fixed_line(status, persona, mode), "status": status, "citations": [], "sound": None,
            "model": MODEL_LABEL, "mode": mode, "llm_ms": 0, "check": MODEL_LABEL}
