# Multilingual Language Detection & Response Evaluation

Evaluation of language detection (`detect_language`), query translation for retrieval (`translate_for_search`), and multilingual answer generation across `app/server.py` and `pipeline/persona.py` (Part of #50).

- **Evaluation Dataset:** `eval/questions/multilingual/van-gogh.jsonl` (9 questions across Spanish `es`, Hindi `hi`, and Marathi `mr`).
- **Pipeline:** Live `/ask` endpoint running with `llama3` via Ollama.

---

## Summary Metrics

| Metric | Target | Actual | Notes |
|---|---|---|---|
| **Language Detection Accuracy** | ≥ 90% | **100% (9 / 9)** | Exact match across `es`, `hi`, and `mr` |
| **Passage Retrieval (without query translation)** | — | **11% (1 / 9)** | `retrieve.py` regex `[a-z0-9]+` dropped all Devanagari tokens (0 passages for Hindi & Marathi) |
| **Passage Retrieval (with `translate_for_search`)** | ≥ 80% | **100% (9 / 9)** | Unlocks BM25 search by translating non-English queries to English keywords |
| **Citation Preservation** | 100% | **100% (9 / 9)** | English chunk IDs preserved in all responses (e.g., `van-gogh-wiki-0007`) |
| **Spanish End-to-End Accuracy** | 100% | **100% (3 / 3)** | Natural Spanish responses with cited English passages |
| **Hindi & Marathi Output Language (llama3)** | 100% | **0% (0 / 6 live /ask)** | Model retrieved English passages correctly, but answered in English due to language bleed from English source texts |
| **Reply Check Localization** | 100% | **100%** | `_SAYS_NO` updated for Indic/Spanish negations; fallback decline lines localized |

---

## Live End-to-End `/ask` Evaluation Results

All 9 questions evaluated live through `POST /ask`:

| ID | Expected Lang | Detected Lang | Passages Retrieved | Status | Citations | Answer Snippet | Output Language |
|---|---|---|---|---|---|---|---|
| `vg-multi-01` | `es` | `es` | `wiki-0007`, `gut-0158` | `answered` | `["van-gogh-wiki-0007"]` | "Nací el 30 de marzo de 1853 en Groot-Zundert, en la provincia de North Brabant, Países Bajos." | **Spanish** (Pass) |
| `vg-multi-02` | `es` | `es` | `wiki-0022`, `wiki-0023` | `answered` | `["van-gogh-wiki-0022", "van-gogh-wiki-0023"]` | "Theo tenía una tienda de arte en París, donde vendía obras de impresionistas..." | **Spanish** (Pass) |
| `vg-multi-03` | `es` | `es` | `aic-0000`, `wiki-0035` | `answered` | `["van-gogh-aic-0000"]` | "Tres versiones de El dormitorio pintaste" | **Spanish** (Pass) |
| `vg-multi-04` | `hi` | `hi` | `wiki-0007`, `gut-0158` | `answered` | `["van-gogh-wiki-0007"]` | "Vincent Willem van Gogh was born on 30 March 1853 in Groot-Zundert..." | English (Bleed) |
| `vg-multi-05` | `hi` | `hi` | `wiki-0022`, `wiki-0024` | `answered` | `["van-gogh-wiki-0022"]` | "Theo was an art dealer, and he had a gallery in Paris where he sold paintings..." | English (Bleed) |
| `vg-multi-06` | `hi` | `hi` | `aic-0000`, `wiki-0035` | `answered` | `["van-gogh-aic-0000"]` | "I made two versions of The Bedroom, the first one in October 1888 and the second..." | English (Bleed) |
| `vg-multi-07` | `mr` | `mr` | `wiki-0007`, `gut-0158` | `answered` | `["van-gogh-wiki-0007"]` | "Vincent Willem van Gogh was born on 30 March 1853 in Groot-Zundert..." | English (Bleed) |
| `vg-multi-08` | `mr` | `mr` | `gut-0144`, `gut-0147` | `answered` | `["van-gogh-gut-0144", "van-gogh-gut-0147"]` | "Ah, Theo's work in Paris, you ask? Well, he's been busy with his art dealer business..." | English (Bleed) |
| `vg-multi-09` | `mr` | `mr` | `aic-0000`, `gut-0196` | `answered` | `["van-gogh-aic-0000"]` | "I have painted two versions of The Bedroom. The first one was painted in October 1888..." | English (Bleed) |

---

## Key Findings & Bottlenecks

1. **Retrieval Bottleneck (Resolved):**
   - In `retrieve.py` line 83, `tokenize()` splits queries using `re.findall(r"[a-z0-9]+", text.lower())`. Because Devanagari characters contain no `[a-z0-9]` matches, Hindi and Marathi queries tokenized to `[]` and returned 0 passages through `/ask`.
   - Introducing `translate_for_search()` in `pipeline/persona.py` (called in `app/server.py` before BM25) translates the visitor's query to English for search while preserving the original non-English question for answer generation. This raised retrieval from 11% to 100%.

2. **Reply Check & Decline Bug (Resolved):**
   - `check_reply()` previously checked declines against `_SAYS_NO = re.compile(r"\b(?:not|no|never|cannot|nothing|only|beyond)\b|n't\b")`. Legitimate Hindi and Marathi declines (e.g. using `नहीं` or `नाही`) failed this English-only regex and were incorrectly flagged as `decline_that_answers`, causing them to be overwritten with an English fixed line.
   - Updated `_SAYS_NO` with Spanish, Hindi, and Marathi negations, and localized `_fixed_line` across Spanish, Hindi, Marathi, and Kannada.

3. **Language Bleed with Open-Weights LLMs (Remaining Issue):**
   - For Spanish, the system prompt instruction `"Reply in Spanish while keeping citation IDs in English."` works reliably (3/3 Spanish answers).
   - For Hindi and Marathi, `llama3` (8B) exhibits severe language bleed: when provided passages in English, the model generates answers in English despite the system prompt instruction. Achieving consistent Devanagari generation when grounding on English passages will require either a larger reasoning model (e.g., `gpt-oss-120b`) or a two-stage translation step.

4. **Speech & Audio Limitation (Remaining Issue):**
   - Speech-to-text (`pipeline/stt.py`) is optimized for English, and text-to-speech (`pipeline/tts.py` using Kokoro-82M) only supports English voice models (`af_heart`, etc.). Full voice multilingual support remains an open item for future milestones.
