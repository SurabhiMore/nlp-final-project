# Multilingual Evaluation — End-to-End via `/ask` (closes #50)

Evaluation of language detection (`detect_language`), query translation for retrieval
(`translate_for_search`), and multilingual answer generation across `app/server.py` and
`pipeline/persona.py`.

- **Evaluation Dataset:** `eval/questions/multilingual/van-gogh.jsonl` (9 questions across Spanish `es`, Hindi `hi`, and Marathi `mr`)
- **Script:** `eval/run_multilingual.py` — sends each question to the live `/ask` endpoint (not the pipeline directly), so the numbers reflect exactly what a visitor experiences
- **TOP_K:** 8 (matches `app/server.py` default)
- **Model:** `openai/gpt-oss-120b` via Groq
- **Prompt directive used:** `"Reply entirely in <Language>. Do not reply in English; translate the facts from the passages into <Language> while keeping citation IDs in English."`
- **Evaluated:** 2026-11-03

---

## Summary Metrics

| Metric | Target | Actual | Notes |
|---|---|---|---|
| **Language Detection Accuracy** | ≥ 90% | **100% (9 / 9)** | Exact match across `es`, `hi`, and `mr` |
| **Passage Retrieval (with `translate_for_search`)** | ≥ 80% | **100% (9 / 9)** | All 9 non-English queries translated to English keywords; retrieved 8 passages each |
| **Citation Preservation** | 100% | **100% (6 / 6 answered)** | English chunk IDs preserved in all 6 answered responses |
| **Grounded Answer Accuracy** | ≥ 80% | **67% (6 / 9)** | 6 of 9 answered correctly with citations. Theo's job (`vg-multi-02`, `05`, `08`) declined in all languages |
| **Spanish answers in Spanish** | 100% | **100% (3 / 3)** | 2 answered, 1 decline; all in Spanish |
| **Hindi answers in Hindi** | 100% | **100% (3 / 3)** | 2 answered, 1 decline; all in Devanagari |
| **Marathi answers in Marathi** | 100% | **100% (3 / 3)** | 2 answered, 1 decline; all in Devanagari |

---

## Live End-to-End Evaluation Results (`gpt-oss-120b` via Groq)

All 9 questions sent to the live `/ask` endpoint (translate → retrieve → answer):

| ID | Expected | Detected | Passages | Status | Citations | Script | Answer Snippet |
|---|---|---|---|---|---|---|---|
| `vg-multi-01` | `es` | `es` | 8 | answered | `van-gogh-wiki-0007` | Latin-extended (Spanish) | Nací el 30 de marzo de 1853 en Groot‑Zundert, en la provincia de Braba… |
| `vg-multi-02` | `es` | `es` | 8 | not_in_sources | — | Spanish (ASCII) | Mis fuentes no dicen nada al respecto. |
| `vg-multi-03` | `es` | `es` | 8 | answered | `van-gogh-aic-0000` | Latin-extended (Spanish) | Pinté tres versiones de El dormitorio. |
| `vg-multi-04` | `hi` | `hi` | 8 | answered | `van-gogh-wiki-0007` | Devanagari | मैं 30 मार्च 1853 को नॉर्थ ब्राबैंट के ग्रूट‑ज़ुंडर्ट में जन्मा था। |
| `vg-multi-05` | `hi` | `hi` | 8 | not_in_sources | — | Devanagari | मेरे स्रोतों में इसके बारे में कुछ नहीं कहा गया है। |
| `vg-multi-06` | `hi` | `hi` | 8 | answered | `van-gogh-aic-0000` | Devanagari | मैंने बेडरूम की पेंटिंग के तीन संस्करण बनाए थे। |
| `vg-multi-07` | `mr` | `mr` | 8 | answered | `van-gogh-wiki-0007` | Devanagari | मी ३० मार्च १८५३ रोजी ग्रूट‑झुंडर्ट, नॉर्थ ब्राबँट, नेदरलँड्स येथे जन्… |
| `vg-multi-08` | `mr` | `mr` | 8 | not_in_sources | — | Devanagari | माझा भाव थिओ पॅरिसमध्ये कला व्यापारी म्हणून काम करीत होता, पण माझ्या स… |
| `vg-multi-09` | `mr` | `mr` | 8 | answered | `van-gogh-aic-0000` | Devanagari | मी 'द बेडरूम'चे तीन आवृत्त्या काढल्या आहेत. |

Full JSON replies: [`eval/results/multilingual_replies.json`](https://github.com/SurabhiMore/nlp-final-project/blob/f50616a/eval/results/multilingual_replies.json)

> **Note on `vg-multi-08`:** In Marathi, the model actually states Theo's occupation before hedging ("माझा भाव थिओ पॅरिसमध्ये कला व्यापारी म्हणून काम करीत होता, पण माझ्या स्रोतांमध्ये त्याचे काम स्पष्टपणे नमूद नाही." — *My brother Theo was working as an art dealer in Paris, but in my sources his work is not clearly mentioned.*), setting `status: "not_in_sources"`.

---

## Key Findings

### 1. Retrieval: Resolved with `translate_for_search()`
- In `retrieve.py`, `tokenize()` uses `re.findall(r"[a-z0-9]+", ...)` which drops all Devanagari/non-ASCII characters, returning 0 passages for Hindi and Marathi queries.
- `translate_for_search()` in `pipeline/persona.py` (called in `app/server.py` before BM25) translates the visitor's query to English keywords before retrieval, while the original non-English question is passed to `answer()` for response generation.
- `translate_for_search()` uses `_call_llm()` internally, inheriting retry logic (5 attempts, exponential backoff) and rate-limit handling. It explicitly requests and parses JSON, stripping any wrapping JSON object so only clean search keywords reach BM25.
- Both `search_query` and the passage count (`passages: 8`) are returned in the `/ask` JSON response and logged to `qa_log.jsonl`.
- Retrieval improved from 11% → 100% (9/9).

### 2. Reply Check Localization: Resolved
- `check_reply()` previously matched declines with an English-only `_SAYS_NO` regex. Hindi/Marathi declines using `नहीं`, `नाही` were incorrectly overwritten.
- Updated `_SAYS_NO` with Indic and Spanish negation patterns. Bare `ना` was removed to avoid false matches on mid-word occurrences (e.g. `नाम`, `बनाना`). `_fixed_line()` returns localized decline text per language.
- `_ABOUT_YOU` extended with Hindi (`नमस्ते`, `नमस्कार`, `आप कौन हैं/हो`, `तुम कौन हो`, `क्या आप असली`), Marathi (`तुम्ही कोण आहात`, `तुम्ही खरे`), and Spanish (`hola`, `quién eres`, `quien eres`, `eres real`) patterns, so greeting and identity questions in those languages are not incorrectly returned as `not_in_sources`.

### 3. Language Bleed: Resolved with `gpt-oss-120b`
- With `llama3` (8B via Ollama): Hindi and Marathi answers came back in English (0/6) due to language bleed when grounding on English passages.
- With `gpt-oss-120b` (via Groq): Hindi 3/3 ✅ and Marathi 3/3 ✅ answered in full Devanagari. The model follows the system prompt instruction reliably.

### 4. Theo Question Analysis (`vg-multi-02`, `vg-multi-05`, `vg-multi-08`)
- The target passage for Theo's occupation is `van-gogh-aic-0007` ("...where his beloved brother Theo was a dealer").
- In all 3 languages, `van-gogh-aic-0007` was successfully retrieved in the top 8 passages.
- However, `gpt-oss-120b` returned `not_in_sources` in Spanish, Hindi, and Marathi.
- **English comparison test:** Asking the identical question in English ("*What was your brother Theo's job in Paris?*") with the same passages yielded the exact same outcome:
  ```json
  {
    "status": "not_in_sources",
    "check": null,
    "answer": "My sources do not say what my brother Theo's occupation was in Paris.",
    "citations": []
  }
  ```
- Because `check` is `null` in both English and non-English runs, the decline is not triggered by `check_reply` or a translation artifact. Rather, the model's reasoning deems a passing mention in an artwork provenance note ("was a dealer") insufficient evidence to definitively state Theo's occupation, so it declines conservatively.

### 5. Speech & Audio Limitation (Known Limit — Out of Scope for #50)
- Speech-to-text (`pipeline/stt.py`) is English-optimised (Whisper); non-English audio is transcribed in English.
- Text-to-speech (`pipeline/tts.py`, Kokoro-82M) supports English voices only; the answer is spoken in the English voice regardless of the detected language.
- Full voice multilingual support is a future milestone (roadmap Sessions 10–12).

### 6. Short Spanish Questions (Known Limit)
- `langdetect` requires sufficient text to distinguish languages. Very short Spanish questions (fewer than ~5 words), such as `"¿Qué pintaste?"`, may be classified as `en` rather than `es`. In those cases the answer is returned in English. Longer questions are detected reliably.

---

## Previous Run (`llama3` via Ollama) — Historical Reference

| Language | Passages Retrieved | Answer Language |
|---|---|---|
| Spanish (3 q) | 3/3 | Spanish ✅ |
| Hindi (3 q) | 3/3 | English ❌ (language bleed) |
| Marathi (3 q) | 3/3 | English ❌ (language bleed) |

`llama3` (8B) ignored the system prompt language instruction when English passages were in context. This is a known limitation of small open-weights models and is resolved by using `gpt-oss-120b`.
