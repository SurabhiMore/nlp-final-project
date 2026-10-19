# Evaluation Question Coverage Summary

This document summarizes the held-out answer-evaluation datasets for the **Van Gogh** and **T-Rex** exhibits following the expansion and validation under Issue #27.

## 1. Overview Statistics

| Exhibit | Original Questions | Added Questions | Total Questions | Answerable | Traps / Unanswerable |
|---|---|---|---|---|---|
| **Van Gogh** (`van-gogh`) | 22 (`vg-01` to `vg-22`) | 10 (`vg-23` to `vg-32`) | **32** | 23 (71.9%) | 9 (28.1%) |
| **T-Rex** (`t-rex`) | 22 (`tr-01` to `tr-22`) | 10 (`tr-23` to `tr-32`) | **32** | 23 (71.9%) | 9 (28.1%) |
| **Total** | 44 | 20 | **64** | 46 (71.9%) | 18 (28.1%) |

---

## 2. Question Type Breakdown

| Question Type | Target Category | Van Gogh | T-Rex | Combined |
|---|---|---|---|---|
| `fact` | Direct factual inquiries & scientific data | 6 | 19 | 25 |
| `date` | Chronological & historical milestones | 6 | 2 | 8 |
| `painting` | Artworks, motifs, and composition details | 6 | 0 | 6 |
| `quote` | Historical quotations & documented words | 4 | 0 | 4 |
| `why` | Causal, behavioral, and biological reasons | 1 | 2 | 3 |
| `outside_time` | Chronological boundary traps (after subject era) | 4 | 4 | 8 |
| `not_in_sources` | Plausible inquiries unsupported by the corpus | 3 | 3 | 6 |
| `off_topic` | Irrelevant or general knowledge distractions | 2 | 2 | 4 |
| **Total** | | **32** | **32** | **64** |

---

## 3. Van Gogh Newly Added Questions (`vg-23` – `vg-32`)

| ID | Type | Answerable | Question | Supporting Chunk ID(s) | Focus / Failure Exposure |
|---|---|---|---|---|---|
| `vg-23` | `fact` | Yes | Who was your doctor and friend in Auvers-sur-Oise? | `van-gogh-wiki-0039` | Doctor/caregiver relationship in his final period |
| `vg-24` | `painting` | Yes | At which asylum were you staying when you created The Starry Night? | `van-gogh-wiki-0035` | Asylum location grounding (*The Starry Night*) |
| `vg-25` | `painting` | Yes | Which two chairs did you paint while preparing for or living with Gauguin in Arles? | `van-gogh-wiki-0030` | Paired artworks (*Van Gogh's Chair* and *Gauguin's Chair*) |
| `vg-26` | `fact` | Yes | What was your father's profession, and what church did he serve? | `van-gogh-wiki-0007` | Alternate terminology & family background (minister, Dutch Reformed Church) |
| `vg-27` | `date` | Yes | When did you injure your left ear with a razor in Arles? | `van-gogh-wiki-0031` | Historical date grounding (23 December 1888) |
| `vg-28` | `fact` | Yes | What three things became your staple diet while living in poverty in Antwerp? | `van-gogh-wiki-0019` | Multi-item fact recall (bread, coffee, tobacco) |
| `vg-29` | `quote` | Yes | What were your reported last words before you died in Auvers? | `van-gogh-wiki-0041` | Documented final quotation ("The sadness will last forever") |
| `vg-30` | `fact` | Yes | Did you cut off your entire ear or only part of it? | `van-gogh-wiki-0002`, `van-gogh-wiki-0031` | Answer grounding: sources say "severed part of his own left ear" / "either wholly or in part" — tests whether model cites uncertainty correctly |
| `vg-31` | `outside_time` | No | What do you think of Don McLean's 1971 song 'Vincent (Starry, Starry Night)'? | None | Time boundary: cultural work created post-1890 |
| `vg-32` | `not_in_sources` | No | What did you write to Theo about Leonardo da Vinci's Mona Lisa? | None | Retrieval trap: tests resistance to hallucination on unmentioned masterworks |

---

## 4. T-Rex Newly Added Questions (`tr-23` – `tr-32`)

| ID | Type | Answerable | Question | Supporting Chunk ID(s) | Focus / Failure Exposure |
|---|---|---|---|---|---|
| `tr-23` | `fact` | Yes | How good was your sense of smell? | `t-rex-wiki-0082` | Sensory capability (large olfactory bulbs/nerves, vulture comparison) |
| `tr-24` | `fact` | Yes | What kind of vision did you have, and how far could you see objects clearly? | `t-rex-wiki-0080` | Binocular vision & 6 km far point distance |
| `tr-25` | `fact` | Yes | What was the nickname of the specimen found in Saskatchewan, and how heavy was it? | `t-rex-wiki-0011` | Famous specimen ("Scotty", 8.87 tonnes) |
| `tr-26` | `fact` | Yes | Which horned dinosaur was among your primary prey targets? | `t-rex-wiki-0081` | Predation & prey species (Triceratops) |
| `tr-27` | `fact` | Yes | How long was your largest tooth found so far including its root? | `t-rex-wiki-0014` | Anatomy & size extremes (30.5 cm / 12 in) |
| `tr-28` | `why` | Yes | Did you hunt primarily during the day or at night? | `t-rex-wiki-0082` | Behavioral science inference (diurnal hunting based on eye f-number) |
| `tr-29` | `fact` | Yes | What was your estimated body temperature, and was your metabolism warm-blooded? | `t-rex-wiki-0063` | Physiology & isotopic temperature (36.3 °C / endothermic) |
| `tr-30` | `not_in_sources` | No | Did you roar with an open mouth like the T-Rex in movies? | None | Trap: movie vocal tropes unsupported by fossil record |
| `tr-31` | `not_in_sources` | No | How many weeks did it take for your eggs to hatch in a nest? | None | Trap: nesting duration unrecorded in corpus |
| `tr-32` | `outside_time` | No | Did you see the Chicxulub asteroid impact that ended the dinosaurs? | None | Persona boundary: individual organism cannot recount the post-impact extinction |

---

## 5. Dataset Validation Capabilities

The validation harness (`eval/datasets.py`) enforces:
1. **JSON Syntax and Structure**: Detects and pinpoints line-by-line malformed JSON or non-object records.
2. **Schema & Field Integrity**: Enforces presence and non-emptiness of `id`, `question`, `type`, `answerable`, `gold_answer`, `key_facts`, and `evidence`.
3. **ID Uniqueness**: Guarantees no duplicate question IDs exist and lists duplicate IDs upon detection.
4. **Coherence Rules**:
   - `answerable == False` must match `type in {"outside_time", "not_in_sources", "off_topic"}`.
   - Unanswerable traps must have empty `evidence: []` and `key_facts: []`.
   - Answerable questions must have verified, non-empty `evidence` strings and `key_facts` groups.
5. **Corpus & Chunk Grounding**:
   - Supporting passages are mapped through exact `evidence` text snippets rather than hardcoded chunk IDs. Because chunk IDs shift whenever the corpus is rebuilt (`scripts/build_corpus.py`), anchoring to verified evidence text ensures long-term dataset stability.
   - For every answerable question, `datasets.supporting_chunk_ids` dynamically resolves the supporting chunk IDs from the corpus at runtime.
   - Every evidence substring is validated to exist in at least one corpus passage.
   - Every group in `key_facts` must have at least one alternative present in the cited chunk(s) and in the `gold_answer`.
