"""Answer a visitor's question as the exhibit, using only the retrieved passages.

    from pipeline.persona import answer
    answer("van-gogh", "Why did you paint The Bedroom?", chunks, mode="persona")

Two modes:
  persona   the exhibit answers in the first person (Van Gogh, the T. rex, ...)
  neutral   a plain museum guide answers the same question in the third person.
            This is our baseline: comparing the two tells us whether speaking in
            character makes the answers less accurate.

The prompt is built from persona.json, so it adapts to the kind of exhibit:
a person can quote passages marked as their own words; a creature or object
speaks as a character built from expert sources and says when scientists are
unsure. Nothing here is specific to one exhibit.

The model must reply with JSON: {"answer", "status", "citations"}, plus
"sound" when the exhibit has sounds in its persona.json (the T. rex can roar)
and the visitor asks for one. Citations that are not among the passages we
sent are dropped, so an answer can never cite a passage the model was not
given, and a sound the exhibit does not have is ignored. check_reply() then
makes sure the visitor never sees unreadable model output, an uncited answer,
or a "decline" that answers anyway from the model's own knowledge.

Settings (environment variables or .env, see .env.example):
  LLM_PROVIDER     "openai_compatible" (default) or "offline" (no model, for testing)
  LLM_BASE_URL     e.g. https://api.groq.com/openai/v1
  LLM_API_KEY      your key (not needed for a local Ollama server)
  LLM_MODEL        the model name from your provider's model list
  LLM_TEMPERATURE  default 0.2
  LLM_TIMEOUT      seconds, default 60
  LLM_REASONING_EFFORT  optional, for reasoning models such as gpt-oss: "low" keeps
                   answers fast and uses far fewer tokens of the free daily limit
"""

import json
import os
import re
import time

import requests

from pipeline import config

STATUSES = ("answered", "not_in_sources", "outside_time", "declined")
DECLINED_STATUSES = {"not_in_sources", "outside_time", "declined"}
SUPPORTED_LANGUAGES = {"en", "hi", "mr", "kn", "es"}
NON_ENGLISH_LANGUAGES = {"hi", "mr", "kn", "es"}
LANGUAGE_NAMES = {
    "hi": "Hindi",
    "mr": "Marathi",
    "kn": "Kannada",
    "es": "Spanish",
    "en": "English",
}


def detect_language(text):
    """Detect language of text. Returns an ISO 639-1 code: en, hi, mr, kn, or es.

    Never raises; falls back to 'en' for short or ambiguous input.
    """
    if not text or not isinstance(text, str):
        return "en"
    clean = text.strip()
    if len(clean) < 4:
        return "en"
    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 0
        lang = detect(clean)
        return lang if lang in SUPPORTED_LANGUAGES else "en"
    except Exception:
        return "en"

def _output_rules(sound_names=()):
    exception = "introducing yourself or making a sound" if sound_names else "introducing yourself"
    sound_rule = ""
    if sound_names:
        sound_rule = (f'\nOnly when the visitor asks you to make a sound, also add "sound": "<name>" to the object '
                      f'(one of: {", ".join(sound_names)}). Never add it otherwise.')
    return f"""Reply with a JSON object only, in this exact shape:
{{"answer": "what you say to the visitor", "status": "answered", "citations": ["passage id", "..."]}}
status must be one of: "answered", "not_in_sources", "outside_time", "declined".
If status is "answered", citations must list the ids of the passages you used, at least one, unless you are
only {exception}.
For any other status, citations can be empty.{sound_rule}"""


def settings():
    return {
        "provider": os.getenv("LLM_PROVIDER", "openai_compatible"),
        "base_url": os.getenv("LLM_BASE_URL", "").rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "model": os.getenv("LLM_MODEL", ""),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
        "timeout": float(os.getenv("LLM_TIMEOUT", "60")),
        "reasoning_effort": os.getenv("LLM_REASONING_EFFORT", "").strip(),
    }


def model_label():
    s = settings()
    return "offline-extractive (testing only)" if s["provider"] == "offline" else s["model"]


# ---------------------------------------------------------------- prompts

def _persona_prompt(persona):
    name = persona["name"]
    period = persona["time_period"]
    if persona["perspective"] == "own_words":
        time_rule = (
            f"Your time is {period['label']}. {period['boundary']} Check this before anything else. If the "
            "question is about something that happened after your time (a later event, invention, film, "
            "person or artwork), or asks what you think of it, do not answer it. Say in character that it "
            "came after your time, so you cannot know it, and set status to \"outside_time\". Do this even "
            "if a passage mentions it, because passages written later describe things you never saw. You "
            "may use general knowledge to judge whether something came after your time, but never to answer."
        )
        voice_rule = (
            "Passages marked \"own words\" are your own writing. You may quote them word for word. "
            "Never present anything else as your own words, and never invent a quote."
        )
    else:
        time_rule = (
            f"Your time is {period['label']}. {period['boundary']} You may share what scientists and "
            "curators have learned about you since then, including when and how you were found and named, "
            "because that is what the passages are for. But check this before anything else: if the "
            "question asks whether you saw, met or used something from after your time, or what you think "
            "of it (people, films, machines, today's world), do not answer it. Say in character that it "
            "came long after your time, so you cannot know it, and set status to \"outside_time\", even if "
            "a passage mentions it. You may use general knowledge to judge whether something came after your "
            "time, but never to answer."
        )
        voice_rule = (
            f"You are a character built from what scientists and curators have written about {name}. "
            "Speak in the first person, but when the passages show that scientists disagree or are unsure, "
            "say so plainly, for example \"scientists think\". Never invent a quote."
        )
    sounds = persona.get("sounds", {})
    sound_rule = ""
    if sounds:
        listed = "; ".join(f"{key}: {value['description']}" for key, value in sounds.items())
        sound_rule = (
            f"\n9. You can make these sounds ({listed}). If the visitor asks you to make one, set \"sound\" to "
            "its name, set status to \"answered\", and add one short, playful line to say just before it, like a "
            "lead-in. Don't write the sound itself in the answer (no \"ROAR\" or *roar*), because it is played "
            "right after your line. Never claim it is exactly what you sounded like."
        )
    return f"""You are {name}, talking with a museum visitor through a voice guide called Echoes.ai.
About you: {persona['description']}
Speak in the first person as {name}. Speaking style: {persona['speaking_style']}

Rules:
1. For facts, use only the passages below. Do not add facts from anywhere else, even if you know them.
2. {time_rule}
3. If the passages do not answer the question, say so briefly and in character (for example, that your sources do not say), and set status to "not_in_sources". Never guess.
4. {voice_rule}
5. If the question has nothing to do with you or the museum, gently steer the visitor back, in character, and set status to "declined".
6. If the visitor greets you or asks who you are, introduce yourself by name in one or two sentences using only "About you" above, and set status to "answered".
7. If asked whether you are real, say you are an AI guide speaking as {name}.
8. Keep it short: at most three sentences, because your answer is read aloud. No lists, no markdown, no emojis. Even when you do not answer, speak as {name} and give the reason in one short sentence.{sound_rule}

{_output_rules(tuple(sounds))}"""


def _neutral_prompt(persona):
    name = persona["name"]
    period = persona["time_period"]
    return f"""You are a friendly museum guide answering visitors' questions about {name}.
About {name}: {persona['description']}
Visitors sometimes speak to {name} directly, as "you". Answer as the guide, talking about {name} in the third person, in plain language.

Rules:
1. Use only the passages below. Do not add facts from anywhere else, even if you know them.
2. {name}'s time is {period['label']}. {period['boundary']} Check this before anything else. A question asked to "you" is asked to {name}, so "what do you think of X" means what {name} thought of X. If the question asks what {name} thought of, saw or experienced something from after that time, explain in one sentence that {name} could not have known it, and set status to "outside_time", even if a passage mentions it. You may use general knowledge to judge whether something came after that time, but never to answer.
3. If the passages do not answer the question, say so briefly and set status to "not_in_sources". Never guess.
4. Never invent a quote.
5. If the question has nothing to do with {name} or the museum, gently steer back and set status to "declined".
6. If the visitor greets you or asks who you are, say you are the museum's guide for {name}, and set status to "answered".
7. Keep it short: at most three sentences, because the answer is read aloud. No lists, no markdown, no emojis.

{_output_rules()}"""


def _passages_block(chunks):
    blocks = []
    for chunk in chunks:
        label = chunk.get("source", "")
        section = chunk.get("section", "")
        if section and section not in label:
            label += f", {section}"
        if chunk.get("own_words"):
            label += "; own words"
        blocks.append(f"[{chunk['id']}] ({label})\n{chunk['text']}")
    return "\n\n".join(blocks) if blocks else "(no passages found)"


def build_messages(persona, question, chunks, mode="persona"):
    if mode not in ("persona", "neutral"):
        raise ValueError("mode must be 'persona' or 'neutral'")
    lang = detect_language(question)
    system = _persona_prompt(persona) if mode == "persona" else _neutral_prompt(persona)
    if lang in NON_ENGLISH_LANGUAGES:
        lang_name = LANGUAGE_NAMES[lang]
        system += (
            f"\n\nReply entirely in {lang_name}. Do not reply in English; translate the facts "
            f"from the passages into {lang_name} while keeping citation IDs in English."
        )
    user = f"Passages:\n\n{_passages_block(chunks)}\n\nVisitor's question: {question}\n\nReply with JSON only."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# ---------------------------------------------------------------- calling the model

def _call_llm(messages, s):
    if not s["base_url"] or not s["model"]:
        raise RuntimeError(
            "No language model configured. Set LLM_BASE_URL and LLM_MODEL in .env "
            "(see .env.example), or set LLM_PROVIDER=offline to test without a model.")
    headers = {"Content-Type": "application/json"}
    if s["api_key"]:
        headers["Authorization"] = f"Bearer {s['api_key']}"
    body = {
        "model": s["model"],
        "messages": messages,
        "temperature": s["temperature"],
        "response_format": {"type": "json_object"},
    }
    if s["reasoning_effort"]:
        body["reasoning_effort"] = s["reasoning_effort"]
    url = f"{s['base_url']}/chat/completions"
    for attempt in range(5):
        try:
            response = requests.post(url, json=body, headers=headers, timeout=s["timeout"])
        except (requests.Timeout, requests.ConnectionError) as error:
            if attempt < 4:
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"Could not reach the language model: {error}") from error
        if response.status_code == 400 and "response_format" in body:
            body.pop("response_format")  # some providers do not support JSON mode
            continue
        if response.status_code == 400 and "reasoning_effort" in body:
            body.pop("reasoning_effort")  # only reasoning models accept this
            continue
        if response.status_code in (429, 500, 502, 503) and attempt < 4:
            header = response.headers.get("retry-after")
            wait = float(header) if header and header.replace(".", "", 1).isdigit() else 2 ** attempt * 2
            if wait > 60:
                # A long wait usually means a daily limit. Fail now rather than hang for hours.
                raise RuntimeError(f"The language model is rate limited for about {wait / 60:.0f} more minutes. "
                                   "Try again later or switch to a model with a higher limit.")
            time.sleep(wait)
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"The language model returned {response.status_code}: {response.text[:300]}")
        content = response.json()["choices"][0]["message"].get("content")
        if not content or not content.strip():
            raise RuntimeError("The language model sent an empty reply.")
        return content
    raise RuntimeError("The language model kept refusing requests (rate limited). Try again shortly.")


def parse_reply(text, allowed_ids, allowed_sounds=()):
    """Turn the model's reply into {"answer", "status", "citations", "invalid_citations", "sound"}.

    Never raises. A reply that is not a JSON object, or has an answer that is not
    text, comes back with parse_error set, and check_reply() replaces it.
    """
    obj = None
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text or "", re.S)
        if match:
            try:
                obj = json.loads(match.group(0))
            except json.JSONDecodeError:
                obj = None
    if not isinstance(obj, dict) or not isinstance(obj.get("answer", ""), (str, type(None))):
        return {"answer": (text or "").strip() if isinstance(text, str) else "", "status": "answered",
                "citations": [], "invalid_citations": [], "sound": None, "parse_error": True}

    answer_text = (obj.get("answer") or "").strip()
    status = str(obj.get("status") or "").strip().lower()
    if status not in STATUSES:
        status = "answered" if answer_text else "declined"
    raw = obj.get("citations") or []
    if isinstance(raw, (str, int, float)):
        raw = [raw]
    elif not isinstance(raw, list):
        raw = [json.dumps(raw)]  # a dict or other shape: no usable ids, keep it visible as invalid
    cited, invalid = [], []
    for item in raw:
        cid = str(item).strip().strip("[]")
        if cid in allowed_ids:
            if cid not in cited:
                cited.append(cid)
        else:
            invalid.append(cid)
    sound = obj.get("sound")
    sound = sound.strip().lower() if isinstance(sound, str) else ""
    return {"answer": answer_text, "status": status, "citations": cited, "invalid_citations": invalid,
            "sound": sound if sound in allowed_sounds else None}


# ---------------------------------------------------------------- checking the reply

# A real decline says no somewhere: "my sources do not say", "after my time, so I cannot
# know it", "I can only help with...". In our evaluation the model sometimes set a decline
# status but then answered anyway from its own knowledge ("rex is Latin for king"), with
# nothing to cite. A decline without any of these words is replaced with a fixed line.
_SAYS_NO = re.compile(
    r"\b(?:not|no|never|cannot|nothing|only|beyond)\b|n't\b"
    r"|\b(?:nunca|nada|tampoco|ningun|ninguna|ninguno)\b"
    r"|(?:नहीं|कुछ नहीं)"
    r"|(?:नाही|नाहीत|काही नाही|नव्हते)"
    r"|(?:ಇಲ್ಲ|ಏನೂ ಇಲ್ಲ|ಸಾಧ್ಯವಿಲ್ಲ|ಗೊತ್ತಿಲ್ಲ|ತಿಳಿದಿಲ್ಲ|ಹೇಳಲಾಗಿಲ್ಲ)",
    re.I
)
# Greetings and "who are you" questions are answered from persona.json, not from passages,
# so they may be answered without a citation (rule 6 and 7 of the prompt).
# Patterns cover English, Spanish ("hola", "quién eres", "eres real"), Hindi ("नमस्ते",
# "आप कौन हैं/हो", "क्या आप असली"), Marathi ("तुम्ही कोण आहात", "तुम्ही खरे"), and
# Kannada ("ನಮಸ್ಕಾರ", "ನೀವು ಯಾರು", "ನೀವು ನಿಜವಾದ").
_ABOUT_YOU = re.compile(
    r"^\W*(?:hi|hello|hey|good (?:morning|afternoon|evening)|greetings)\b"
    r"|\bwho (?:are|r) (?:you|u)\b|\bwhat are you\b|\bintroduce yourself\b|\bare you (?:real|an? ai|a robot)\b"
    # Spanish greetings & identity
    r"|\b(?:hola|buenos d[ií]as|buenas tardes|buenas noches)\b"
    r"|qui[eé]n (?:eres|es usted)|eres (?:real|una? ia|un robot)"
    # Hindi greetings & identity
    r"|नमस्ते|नमस्कार|प्रणाम"
    r"|आप कौन (?:हैं|हो)|तुम कौन हो|क्या आप (?:असली|एआई|रोबोट)"
    # Marathi identity
    r"|तुम्ही कोण आहात|तुम्ही (?:खरे|एआय|रोबोट)"
    # Kannada greetings & identity
    r"|ನಮಸ್ಕಾರ|ನಮಸ್ತೆ|ಶುಭೋದಯ|ಶುಭ ಸಂಜೆ"
    r"|ನೀವು ಯಾರು|ನೀನು ಯಾರು|ನಿಮ್ಮ ಪರಿಚಯ|ನೀವು (?:ನಿಜವಾದ|ಎಐ|ರೋಬೋಟ್)",
    re.I | re.UNICODE)
# Rule 7 of the prompt: asked whether it is real, or told to drop the act, the exhibit says
# it is an AI guide. That is an honest answer about itself, not a fact from the passages,
# so it has nothing to cite and need not contain a "no". Without this, check_reply
# replaced it with a fixed line (vg-adv-ib-02 and vg-adv-ib-03 in the robustness eval).
# Both the reply and the question must match: "As an AI guide, ..." in reply to an
# ordinary question is still an uncited answer and is still replaced.
_TRANSPARENCY = re.compile(
    r"\b(?:an?|the) (?:ai|artificial intelligence|virtual|digital|museum) (?:guide|persona|representation|recreation|character)\b"
    r"|\bdigital persona\b|\bmuseum representation\b|\b(?:a|an ai) simulation\b",
    re.I)
# The visitor asks what the exhibit really is: real, human, alive, an AI or a program,
# or tells it to stop pretending. Questions that _ABOUT_YOU matches count too.
_ASKS_WHAT_YOU_ARE = re.compile(
    r"\b(?:are|r) (?:you|u) (?:\w+ )?(?:real|human|alive|a person|a real person|an? ai|a robot|a bot|a machine|a computer|a program)\b"
    r"|\b(?:language model|llm|chatbot|artificial intelligence)\b|\bai\b"
    r"|\bstop pretending\b|\bdrop the act\b|\b(?:confirm|admit) (?:that )?you(?:'re| are)\b"
    r"|\b(?:who|which company|what company) (?:made|built|trained|created|programmed) (?:you|u)\b",
    re.I)

_FIXED_LINES = {
    "en": {
        "persona": {
            "not_in_sources": "My sources do not say anything about that.",
            "outside_time": "That came after my time, so I cannot know it.",
            "declined": "That is not something I can talk about here. Ask me about my own story instead.",
        },
        "neutral": {
            "not_in_sources": "The sources do not say anything about that.",
            "outside_time": "That came after {name}'s time, so {name} could not have known it.",
            "declined": "I can only answer questions about {name} and the museum.",
        },
    },
    "es": {
        "persona": {
            "not_in_sources": "Mis fuentes no dicen nada al respecto.",
            "outside_time": "Eso ocurrió después de mi época, así que no puedo saberlo.",
            "declined": "No puedo hablar de eso aquí. Pregúntame sobre mi propia historia.",
        },
        "neutral": {
            "not_in_sources": "Las fuentes no dicen nada al respecto.",
            "outside_time": "Eso ocurrió después de la época de {name}, por lo que {name} no pudo haberlo sabido.",
            "declined": "Solo puedo responder preguntas sobre {name} y el museo.",
        },
    },
    "hi": {
        "persona": {
            "not_in_sources": "मेरे स्रोतों में इसके बारे में कुछ नहीं कहा गया है।",
            "outside_time": "यह मेरे समय के बाद की बात है, इसलिए मैं इसे नहीं जान सकता।",
            "declined": "मैं यहाँ इसके बारे में बात नहीं कर सकता। इसके बजाय मुझसे मेरी कहानी के बारे में पूछें।",
        },
        "neutral": {
            "not_in_sources": "स्रोतों में इसके बारे में कुछ नहीं कहा गया है।",
            "outside_time": "यह {name} के समय के बाद की बात है, इसलिए {name} इसे नहीं जान सकते थे।",
            "declined": "मैं केवल {name} और संग्रहालय के बारे में सवालों के जवाब दे सकता हूँ।",
        },
    },
    "mr": {
        "persona": {
            "not_in_sources": "माझ्या स्त्रोतांमध्ये याबद्दल काहीही सांगितलेले नाही.",
            "outside_time": "ते माझ्या काळानंतरचे आहे, त्यामुळे मला ते माहित असणे शक्य नाही.",
            "declined": "मी इथे या विषयावर बोलू शकत नाही. त्याऐवजी मला माझ्या स्वतःच्या कथेबद्दल विचारा.",
        },
        "neutral": {
            "not_in_sources": "स्त्रोतांमध्ये याबद्दल काहीही सांगितलेले नाही.",
            "outside_time": "ते {name} यांच्या काळानंतरचे आहे, त्यामुळे {name} यांना ते माहित असणे शक्य नव्हते.",
            "declined": "मी फक्त {name} आणि संग्रहालयाबद्दलच्या प्रश्नांची उत्तरे देऊ शकतो.",
        },
    },
    "kn": {
        "persona": {
            "not_in_sources": "ನನ್ನ ಮೂಲಗಳಲ್ಲಿ ಇದರ ಬಗ್ಗೆ ಏನೂ ಹೇಳಲಾಗಿಲ್ಲ.",
            "outside_time": "ಅದು ನನ್ನ ಕಾಲದ ನಂತರ ಬಂದದ್ದು, ಆದ್ದರಿಂದ ನನಗೆ ಅದು ತಿಳಿದಿರಲು ಸಾಧ್ಯವಿಲ್ಲ.",
            "declined": "ನಾನು ಇಲ್ಲಿ ಅದರ ಬಗ್ಗೆ ಮಾತನಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ. ಬದಲಿಗೆ ನನ್ನ ಕಥೆಯ ಬಗ್ಗೆ ಕೇಳಿ.",
        },
        "neutral": {
            "not_in_sources": "ಮೂಲಗಳಲ್ಲಿ ಇದರ ಬಗ್ಗೆ ಏನೂ ಹೇಳಲಾಗಿಲ್ಲ.",
            "outside_time": "ಅದು {name} ಅವರ ಕಾಲದ ನಂತರದ್ದು, ಆದ್ದರಿಂದ {name} ಅವರಿಗೆ ಅದು ತಿಳಿದಿರಲು ಸಾಧ್ಯವಿಲ್ಲ.",
            "declined": "ನಾನು ಕೇವಲ {name} ಮತ್ತು ವಸ್ತುಸಂಗ್ರಹಾಲಯದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಬಲ್ಲೆ.",
        },
    },
}


def _fixed_line(status, persona, mode, lang="en"):
    name = persona["name"]
    lang_lines = _FIXED_LINES.get(lang, _FIXED_LINES["en"])
    mode_lines = lang_lines.get(mode, lang_lines["persona"])
    template = mode_lines.get(status, _FIXED_LINES["en"][mode][status])
    return template.format(name=name)


def check_reply(result, persona, question, mode="persona"):
    """Make sure what the visitor sees is backed by the passages, whatever the model sent.

    Three deterministic rules, applied after parse_reply():
      1. a reply that could not be read (not JSON, cut off, no answer text) becomes a
         short "not in my sources" line instead of raw model text
      2. "answered" with no valid citation becomes "not_in_sources", unless the visitor
         greeted the exhibit, asked who it is, or asked for a sound
         (a reply in which the exhibit says it is an AI guide, to a visitor who asked
         whether it is real or an AI, skips rules 2 and 3)
      3. a decline whose text does not actually decline (it answers from the model's own
         knowledge) has its text replaced with a fixed decline line for that status

    Returns the same dict shape, plus "check": which rule changed it, or None.
    """
    result = dict(result)
    result["check"] = None
    lang = detect_language(question)
    if result.get("parse_error") or not (result.get("answer", "").strip() or result.get("sound")):
        result.update(answer=_fixed_line("not_in_sources", persona, mode, lang=lang), status="not_in_sources",
                      citations=[], sound=None, check="unreadable_reply")
    elif _TRANSPARENCY.search(result["answer"]) and (
            _ASKS_WHAT_YOU_ARE.search(question or "") or _ABOUT_YOU.search(question or "")):
        pass  # the exhibit says it is an AI guide (rule 7): keep it as the model wrote it
    elif result["status"] == "answered":
        if not result["citations"] and not result.get("sound") and not _ABOUT_YOU.search(question or ""):
            result.update(answer=_fixed_line("not_in_sources", persona, mode, lang=lang), status="not_in_sources",
                          check="uncited_answer")
    elif not _SAYS_NO.search(result["answer"].replace("\u2019", "'")):
        result.update(answer=_fixed_line(result["status"], persona, mode, lang=lang), citations=[],
                      check="decline_that_answers")
    return result


def translate_for_search(question):
    """Translate non-English question to English keywords for BM25 search.

    Uses _call_llm so it gets the same retry logic, 429 handling, and
    reasoning_effort stripping as the main answer path. Leaves English
    questions untouched. If offline or translation fails, returns the
    original question safely.
    """
    lang = detect_language(question)
    if lang not in NON_ENGLISH_LANGUAGES:
        return question
    s = settings()
    if s["provider"] == "offline" or not s["base_url"] or not s["model"]:
        return question
    # Use a short timeout so a slow translation never blocks the full answer.
    s_fast = dict(s, timeout=min(s["timeout"], 10))
    messages = [
        {"role": "system", "content": 'You are a translator. Translate this visitor question into plain English keywords for search. Reply with a JSON object: {"translation": "english search keywords"}'},
        {"role": "user", "content": question},
    ]
    try:
        content = _call_llm(messages, s_fast)
        if not content:
            return question
        content = content.strip()
        # Parse JSON if the model replied with a JSON object (due to response_format: json_object)
        if "{" in content and "}" in content:
            try:
                json_str = content[content.find("{"):content.rfind("}") + 1]
                data = json.loads(json_str)
                if isinstance(data, dict):
                    for key in ("translation", "keywords", "query", "english", "search", "text"):
                        if isinstance(data.get(key), str) and data[key].strip():
                            return data[key].strip()
                    for val in data.values():
                        if isinstance(val, str) and val.strip():
                            return val.strip()
            except Exception:
                pass
        content = content.strip('"\n`* ')
        if content:
            return content
    except Exception:
        pass
    return question


def _offline_answer(chunks):
    """Stand-in for a model so the rest of the system can be tested without an API key."""
    if not chunks or chunks[0].get("score", 0) <= 0:
        return {"answer": "My sources do not say anything about that.", "status": "not_in_sources",
                "citations": [], "invalid_citations": [], "sound": None}
    best = chunks[0]
    sentences = re.split(r"(?<=[.!?])\s+", best["text"])
    return {"answer": " ".join(sentences[:2]), "status": "answered",
            "citations": [best["id"]], "invalid_citations": [], "sound": None}


def answer(persona_id, question, chunks, mode="persona"):
    """Answer one question. Returns answer, status, citations, sound, model, detected_language and llm_ms."""
    persona = config.load_persona(persona_id)
    s = settings()
    start = time.perf_counter()
    if s["provider"] == "offline":
        result = _offline_answer(chunks)
    else:
        reply = _call_llm(build_messages(persona, question, chunks, mode), s)
        sounds = tuple(persona.get("sounds", {})) if mode == "persona" else ()
        result = parse_reply(reply, {c["id"] for c in chunks}, sounds)
    result = check_reply(result, persona, question, mode)
    result["model"] = model_label()
    result["mode"] = mode
    result["detected_language"] = detect_language(question)
    result["llm_ms"] = round((time.perf_counter() - start) * 1000)
    if result["status"] == "answered" and not result["citations"] and not result.get("sound"):
        result["warning"] = "answered without citing a passage"
    return result
