# Claim Checker Labelling Rules & Dataset (`eval/claims_labels.jsonl`)

This document defines the labelling rules, schema, and methodology for evaluating the claim checker (`pipeline/claims.py`) against factual grounding failures.

## 1. Background and Goal

In Session 7 user testing, visitors asked questions where the guide responded with answers that cited valid passages, but silently added specific factual details that the cited passages did not contain:
- **Participant P2 ("Did you move to Arles?"):** Cited passages `van-gogh-wiki-0050` and `van-gogh-wiki-0027` (about moving to Arles and leasing the Yellow House in May 1888), but the model appended that he later moved to *Auvers-sur-Oise in 1890*. Neither Auvers nor 1890 was in the cited passages. P2 rated the answer 5 out of 5 for believing it.
- **Participant P4 ("Did you die?"):** Cited `van-gogh-gut40393-0251` (which describes his final days and deathbed), but the model answered *"I died in July 1890"*. The cited letter does not mention July or 1890.

The reply filter in `pipeline/persona.py` (`check_reply()`) cannot catch these errors because the answer cites valid passages and has status `answered`. The claim checker (`pipeline/claims.py`) provides offline factual grounding verification without requiring any LLM calls.

---

## 2. Definition of Checkable Claims

The checker extracts five types of factual claims from an answer:
1. **Dates & Month-Years:** Full or partial calendar dates (e.g. `July 1890`, `February 1888`, `23 October 1888`).
2. **Years & Geological Ages:** Bare 4-digit years or decades (`1890`, `1890s`, `1905`), and geological periods (`66 million years ago`).
3. **Measurements:** Number + unit combinations (e.g. `12.3 m`, `8.8 tons`, `30.5 cm`, `35,000 newtons`).
4. **Numbers & Quantities:** Bare numerals (`28`, `13`) and numeric words (`two`, `three`, `four`, `seven`) representing counts or quantities.
5. **Proper Names & Locations:** Capitalized multi- or single-word sequences that are not common English words (e.g. `Henry Fairfield Osborn`, `Auvers-sur-Oise`, `Smithsonian`, `Laramidia`, `The Bedroom`).

### Allowed Matching Variants
- **Case and accents:** All matching is case-insensitive and NFKD-normalized (e.g. `Saint-Rémy` matches `saint-remy`).
- **Unit synonyms:** Standard equivalents are treated identically (e.g. `12 m`, `12 metres`, `12 meters`).
- **Unit conversions:** Parenthetical conversions (e.g. `(12 in)` alongside `30.5 cm`) match if the passage contains an equivalent measurement in the same dimension.
- **Sub-name matching:** A single-word name matches if it appears in a full name in the passage (e.g. `Theo` in `Theo van Gogh`).
- **Exhibit persona self-references:** The exhibit's own persona tokens (`Vincent`, `Van Gogh`, `Tyrannosaurus`, `T. rex`) are never flagged as unsupported.
- **Bidirectional numbers:** Word numbers (`two`, `four`) match digits (`2`, `4`) and vice versa.

---

## 3. Supported vs. Unsupported Detail

An answer is labelled:
- **`has_unsupported: false` (Fully Supported):** Every extracted claim (dates, numbers, quantities, names) is present in or directly supported by the cited passages.
- **`has_unsupported: true` (Contains Unsupported Detail):** At least one extracted claim cannot be found in the cited passages, meaning it came from the model's parametric memory or hallucination.

### Real Unsupported Cases in the Evaluation Set
Real unsupported details in the standard test replies are rare because retrieval provides relevant passages. The 8 real cases across `grounding_replies.jsonl` and Session 7 logs are:
1. **`session07-P2-q1` (van-gogh):** Added `Auvers-sur-Oise` and `1890` (passages only cover Arles and the Yellow House lease in 1888).
2. **`session07-P4-q1` (van-gogh):** Added `July 1890` (passage describes his deathbed without stating the date).
3. **`grounding-t-rex-persona-tr-04`:** Added `Henry Fairfield Osborn` (passage `t-rex-si-0014` only has `Osborn, 1905`).
4. **`grounding-t-rex-neutral-tr-04`:** Added `Henry Fairfield Osborn` (same as above).
5. **`grounding-t-rex-neutral-tr-14`:** Added `Smithsonian` (passage `t-rex-si-0004` only says `Education and Outreach collection`).
6. **`grounding-van-gogh-neutral-vg-06`:** Added `Paul Gauguin` (passage `van-gogh-wiki-0030` only refers to `Gauguin`).
7. **`grounding-van-gogh-persona-vg-27`:** Added `Arles` (passage `van-gogh-wiki-0031` describes the ear incident at the Yellow House without naming Arles).
8. **`grounding-van-gogh-neutral-vg-27`:** Added `Arles` (same as above).

All remaining 85 real answers are fully supported by their citations.

---

## 4. Perturbation Methodology

Because real unsupported answers are rare (8 of 93 real answers), we construct **30 controlled perturbed answers** from fully supported grounding replies.

Each perturbed answer modifies **exactly one** factual entity to an unsupported value that does not appear in the cited passages:
- **10 Date Perturbations:** e.g. altering geological dates (`69 to 66 million years ago` -> `85 to 80 million years ago`), birth/death/creation years (`1853` -> `1865`, `1900` -> `1925`), and months/years (`February 1888` -> `April 1891`).
- **10 Number / Quantity Perturbations:** e.g. specimen lengths (`12.3 metres` -> `16.5 metres`), weights (`8.8 tons` -> `14.5 tons`), sprint speeds (`4.5–6.8 m/s` -> `12.5–15.8 m/s`), finger counts (`two clawed fingers` -> `four clawed fingers`), age at death (`28 years` -> `55 years`), and painting counts (`three versions` -> `seven versions`).
- **10 Name / Place Perturbations:** e.g. paleocontinents (`Laramidia` -> `Gondwana`), discoverers (`Barnum Brown` -> `Roy Chapman Andrews`), formations (`Hell Creek Formation` -> `Morrison Formation`), cities (`Paris` -> `London`), and artwork titles (`The Potato Eaters` -> `Water Lilies`).

Every perturbation records:
- `perturbation_type`: `"date"`, `"number"`, or `"name"`
- `original_value`: the original supported text
- `perturbed_value`: the unsupported replacement text

---

## 5. Dataset Schema (`eval/claims_labels.jsonl`)

Each line is a JSON object with:
```json
{
  "id": "grounding-t-rex-persona-tr-04",
  "source": "grounding_replies",
  "is_perturbed": false,
  "exhibit": "t-rex",
  "mode": "persona",
  "question_id": "tr-04",
  "question": "Who named you Tyrannosaurus rex and when?",
  "answer": "I was named Tyrannosaurus rex by Henry Fairfield Osborn in 1905.",
  "citations": ["t-rex-si-0014"],
  "has_unsupported": true,
  "unsupported_details": ["Henry Fairfield Osborn"],
  "perturbation_type": null,
  "original_value": null,
  "perturbed_value": null
}
```

Total entries: **123**
- **Real answers:** 93 (88 from `grounding_replies.jsonl` + 5 from Session 7 user test logs)
  - Fully supported: 85
  - Unsupported details: 8
- **Perturbed answers:** 30 (all 30 have unsupported details)
