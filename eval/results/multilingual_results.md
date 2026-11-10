# Multilingual Evaluation — End-to-End via `/ask`

Evaluation of language detection (`detect_language`), query translation for retrieval
(`translate_for_search`), and multilingual answer generation across `app/server.py` and
`pipeline/persona.py`.

- **Evaluation Datasets:**
  - `eval/questions/multilingual/van-gogh.jsonl` (12 questions across Spanish `es`, Hindi `hi`, Marathi `mr`, and Kannada `kn`)
  - `eval/questions/multilingual/t-rex.jsonl` (12 questions across Spanish `es`, Hindi `hi`, Marathi `mr`, and Kannada `kn`)
- **Script:** `eval/run_multilingual.py [--persona {van-gogh,t-rex,all}]` — sends each question to the live `/ask` endpoint (or in-process FastAPI TestClient fallback), so numbers reflect the visitor experience
- **TOP_K:** 8 (matches `app/server.py` default)
- **Model:** `openai/gpt-oss-120b` via Groq
- **Prompt directive used:** `"Reply entirely in <Language>. Do not reply in English; translate the facts from the passages into <Language> while keeping citation IDs in English."`
- **Supported Languages:** English (`en`), Spanish (`es`), Hindi (`hi`), Marathi (`mr`), Kannada (`kn`)

---

## Summary Metrics

| Metric | Target | Van Gogh (Actual) | T. rex (Actual) | Notes |
|---|---|---|---|---|
| **Language Detection Accuracy** | ≥ 90% | **100% (12 / 12)** | **100% (12 / 12)** | Exact match across `es`, `hi`, `mr`, and `kn` |
| **Passage Retrieval (with `translate_for_search`)** | ≥ 80% | **100%** | **100%** | Non-English queries translated to English keywords for BM25; 8 passages retrieved |
| **Citation Preservation** | 100% | **100%** | **100%** | English chunk IDs preserved in all answered responses |
| **Spanish answers in Spanish** | 100% | **100% (3 / 3)** | **100% (3 / 3)** | Latin script preserved |
| **Hindi answers in Hindi** | 100% | **100% (3 / 3)** | **100% (3 / 3)** | Devanagari script preserved |
| **Marathi answers in Marathi** | 100% | **100% (3 / 3)** | **100% (3 / 3)** | Devanagari script preserved |
| **Kannada answers in Kannada** | 100% | **100% (3 / 3)** | **100% (3 / 3)** | Kannada script (`U+0C80–U+0CFF`) preserved |

---

## T. rex Multilingual Question Set (`eval/questions/multilingual/t-rex.jsonl`)

12 questions across 4 non-English languages covering core exhibit dimensions (era/date, anatomy/digits, bite force/strength):

| ID | Persona | Expected | Question | Type |
|---|---|---|---|---|
| `tr-multi-01` | `t-rex` | `es` | ¿Cuándo viviste en la Tierra? | date |
| `tr-multi-02` | `t-rex` | `es` | ¿Cuántos dedos tenías en cada mano? | fact |
| `tr-multi-03` | `t-rex` | `es` | ¿Qué tan fuerte era tu mordida? | fact |
| `tr-multi-04` | `t-rex` | `hi` | आप पृथ्वी पर कब जीवित थे? | date |
| `tr-multi-05` | `t-rex` | `hi` | आपके प्रत्येक हाथ में कितनी उंगलियां थीं? | fact |
| `tr-multi-06` | `t-rex` | `hi` | आपके काटने की ताकत (बाइट फोर्स) कितनी थी? | fact |
| `tr-multi-07` | `t-rex` | `mr` | तुम्ही पृथ्वीवर कधी अस्तित्वात होता? | date |
| `tr-multi-08` | `t-rex` | `mr` | तुमच्या प्रत्येक हाताला किती बोटे होती? | fact |
| `tr-multi-09` | `t-rex` | `mr` | तुमच्या जबड्याची चावण्याची ताकद किती होती? | fact |
| `tr-multi-10` | `t-rex` | `kn` | ನೀವು ಭೂಮಿಯ ಮೇಲೆ ಯಾವಾಗ ಜೀವಿಸಿದ್ದೀರಿ? | date |
| `tr-multi-11` | `t-rex` | `kn` | ನಿಮ್ಮ ಪ್ರತಿಯೊಂದು ಕೈಯಲ್ಲಿ ಎಷ್ಟು ಬೆರಳುಗಳು ಇದ್ದವು? | fact |
| `tr-multi-12` | `t-rex` | `kn` | ನಿಮ್ಮ ಕಡಿತದ ಬಲ ಎಷ್ಟು ಪ್ರಬಲವಾಗಿತ್ತು? | fact |

---

## Van Gogh Multilingual Question Set (`eval/questions/multilingual/van-gogh.jsonl`)

12 questions across 4 non-English languages covering birth/origins, family/Theo, and artworks:

| ID | Persona | Expected | Question | Type |
|---|---|---|---|---|
| `vg-multi-01` | `van-gogh` | `es` | ¿Cuándo y dónde naciste? | date |
| `vg-multi-02` | `van-gogh` | `es` | ¿Cuál era el trabajo de tu hermano Theo en París? | fact |
| `vg-multi-03` | `van-gogh` | `es` | ¿Cuántas versiones de El dormitorio pintaste? | painting |
| `vg-multi-04` | `van-gogh` | `hi` | आपका जन्म कब और कहाँ हुआ था? | date |
| `vg-multi-05` | `van-gogh` | `hi` | पेरिस में आपके भाई थियो का क्या काम था? | fact |
| `vg-multi-06` | `van-gogh` | `hi` | आपने द बेडरूम पेंटिंग के कितने संस्करण बनाए थे? | painting |
| `vg-multi-07` | `van-gogh` | `mr` | तुमचा जन्म कधी आणि कुठे झाला होता? | date |
| `vg-multi-08` | `van-gogh` | `mr` | पॅरिसमध्ये तुमच्या भावाचे थिओचे काय काम होते? | fact |
| `vg-multi-09` | `van-gogh` | `mr` | तुम्ही द बेडरूम या चित्राच्या किती आवृत्त्या काढल्या? | painting |
| `vg-multi-10` | `van-gogh` | `kn` | ನಿಮ್ಮ ಜನನ ಯಾವಾಗ ಮತ್ತು ಎಲ್ಲಿ ಆಯಿತು? | date |
| `vg-multi-11` | `van-gogh` | `kn` | ಪ್ಯಾರಿಸ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಸಹೋದರ ಥಿಯೋ ಅವರ ಕೆಲಸವೇನಾಗಿತ್ತು? | fact |
| `vg-multi-12` | `van-gogh` | `kn` | ನೀವು 'ದಿ ಬೆಡ್‌ರೂಮ್' ಚಿತ್ರದ ಎಷ್ಟು ಆವೃತ್ತಿಗಳನ್ನು ರಚಿಸಿದ್ದೀರಿ? | painting |

---

## Key Findings & Improvements

### 1. Kannada (`kn`) Pipeline Support
- Added Kannada negation tokens (`ಇಲ್ಲ`, `ಏನೂ ಇಲ್ಲ`, `ಸಾಧ್ಯವಿಲ್ಲ`, `ಗೊತ್ತಿಲ್ಲ`, `ತಿಳಿದಿಲ್ಲ`, `ಹೇಳಲಾಗಿಲ್ಲ`) to `_SAYS_NO` regex in `pipeline/persona.py`. This prevents genuine declines in Kannada from being overwritten with fixed templates.
- Added Kannada greeting and identity patterns (`ನಮಸ್ಕಾರ`, `ನಮಸ್ತೆ`, `ಶುಭೋದಯ`, `ಶುಭ ಸಂಜೆ`, `ನೀವು ಯಾರು`, `ನೀನು ಯಾರು`, `ನಿಮ್ಮ ಪರಿಚಯ`, `ನೀವು (?:ನಿಜವಾದ|ಎಐ|ರೋಬೋಟ್)`) to `_ABOUT_YOU` in `pipeline/persona.py`. This ensures visitor greetings in Kannada are not misclassified as uncited answers.
- `_FIXED_LINES["kn"]` provides localized decline templates for both `persona` and `neutral` modes.

### 2. Multi-Exhibit Evaluation Tooling
- Updated `eval/run_multilingual.py` to accept CLI arguments:
  ```bash
  python -m eval.run_multilingual --persona van-gogh
  python -m eval.run_multilingual --persona t-rex
  python -m eval.run_multilingual --persona all
  ```
- Extended `detect_script()` heuristic to detect Kannada script (`\u0C80` <= c <= `\u0CFF`).
- Output JSON results saved to `eval/results/multilingual_replies.json`.

### 3. Retrieval via `translate_for_search()`
- In `retrieve.py`, BM25 word tokenization drops non-ASCII characters. `translate_for_search()` translates visitor queries to concise English keywords before retrieval, enabling 100% retrieval success across Spanish, Hindi, Marathi, and Kannada.
- The raw non-English question is preserved and passed to the LLM system prompt for answering in character.
