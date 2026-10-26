# Speech to text

How well Whisper hears visitors' questions, run on 2026-10-26 with `python -m eval.eval_stt`: 40 clips of the questions in `eval/questions/stt/reference.jsonl`, read by 5 speakers. Machine: Darwin arm64, 10 CPU threads, device cpu.

Word error rate is counted after lowercasing and removing punctuation and accents. "Names right" counts the words of each question that are in the exhibit's vocabulary prompt (such as Theo or Maastrichtian) and also appear in the transcript. Seconds per clip leave out loading the model.

| Setting | Model | Beam | Prompt | Word error rate | Clips exactly right | Names right | Seconds per clip (median) | Seconds per clip (mean) | Real-time factor |
|---|---|---|---|---|---|---|---|---|---|
| current | base | 1 | no | 0.101 | 22 of 40 | 11 of 20 | 0.25 | 0.25 | 0.05 |
| prompt | base | 1 | yes | 0.123 | 20 of 40 | 14 of 20 | 0.27 | 0.27 | 0.06 |
| beam5 | base | 5 | no | 0.084 | 24 of 40 | 12 of 20 | 0.31 | 0.32 | 0.07 |
| prompt_beam5 | base | 5 | yes | 0.098 | 23 of 40 | 18 of 20 | 0.36 | 0.37 | 0.08 |
| small_prompt | small | 1 | yes | 0.053 | 29 of 40 | 19 of 20 | 0.82 | 0.83 | 0.17 |

**Suggested default: small_prompt**, the lowest word error rate with a median of at most 2.0 s per clip.

## By speaker

| Speaker | Accent | current | prompt | beam5 | prompt_beam5 | small_prompt |
|---|---|---|---|---|---|---|
| S1 | not given | 0.109 | 0.152 | 0.076 | 0.076 | 0.065 |
| S2 | not given | 0.120 | 0.141 | 0.098 | 0.120 | 0.033 |
| S3 | not given | 0.121 | 0.086 | 0.086 | 0.086 | 0.086 |
| S4 | not given | 0.109 | 0.164 | 0.091 | 0.182 | 0.091 |
| S5 | not given | 0.033 | 0.050 | 0.067 | 0.033 | 0.000 |

## Low-confidence flag (small_prompt)

A transcript is flagged when Whisper's average log probability per token is below -0.6. At that threshold, 0 of 11 misheard clips were flagged, and 0 of 29 clips that were exactly right were flagged anyway (false alarms).

Suggested threshold for this setting: **-0.35**, the one that best separates misheard clips from right ones (share of misheard clips flagged minus share of right clips flagged). It is chosen on these same clips, so it is a starting point rather than a tested result.

| Threshold | Misheard clips flagged | Right clips flagged |
|---|---|---|
| -0.05 | 11 of 11 | 29 of 29 |
| -0.1 | 11 of 11 | 29 of 29 |
| -0.15 | 11 of 11 | 29 of 29 |
| -0.2 | 11 of 11 | 29 of 29 |
| -0.25 | 10 of 11 | 23 of 29 |
| -0.3 | 9 of 11 | 12 of 29 |
| -0.35 | 7 of 11 | 4 of 29 |
| -0.4 | 5 of 11 | 2 of 29 |
| -0.45 | 4 of 11 | 1 of 29 |
| -0.5 | 4 of 11 | 0 of 29 |
| -0.55 | 2 of 11 | 0 of 29 |
| -0.6 | 0 of 11 | 0 of 29 |
| -0.65 | 0 of 11 | 0 of 29 |
| -0.7 | 0 of 11 | 0 of 29 |
| -0.75 | 0 of 11 | 0 of 29 |
| -0.8 | 0 of 11 | 0 of 29 |
| -0.85 | 0 of 11 | 0 of 29 |
| -0.9 | 0 of 11 | 0 of 29 |
| -0.95 | 0 of 11 | 0 of 29 |
| -1.0 | 0 of 11 | 0 of 29 |
| -1.05 | 0 of 11 | 0 of 29 |
| -1.1 | 0 of 11 | 0 of 29 |
| -1.15 | 0 of 11 | 0 of 29 |
| -1.2 | 0 of 11 | 0 of 29 |

## Vocabulary prompts

- t-rex: A question for Tyrannosaurus rex, about North America, Cretaceous, Osborn, Maastrichtian, Nanotyrannus, Outreach, Mesozoic, United States, Sue, Montana, Tarbosaurus, Triceratops, Wyoming, Tyrannosauridae, Tyrannosaurinae, T-Rex, Stan, Thomas Carr, Daspletosaurus, Burpee Museum, Albertosaurus, Currie, Komodo, Paleobiology, Animalia, Chordata, Gnathostomata, Reptilia, Avetheropoda, Updated, Jane, Zhuchengtyrannus, Gorgosaurus, Edmontosaurus.
- van-gogh: A question for Vincent van Gogh, about Theo, Paris, Gauguin, Arles, Rembrandt, Dutch, Millet, Delacroix, Japanese, Monticelli, Christ, March, July, Bernard, Seurat, French, January, Gift, Israels, Bequest, Daumier, Holland, Provence, November, Saint-Rémy, Zola, Pont-Aven, Brittany, February, Cézanne, Breton, April, Brussels, Ostade, Velasquez, Dutchmen, Nuenen.

## Every misheard clip (small_prompt)

| Speaker | Id | Said | Heard (small_prompt) | Heard (current) | Log prob |
|---|---|---|---|---|---|
| S1 | tr-16 | In which rock formation was Sue found? | In which rock formation was so found. | In which rock formation was so found? | -0.324 |
| S1 | tr-25 | What was the nickname of the specimen found in Saskatchewan, and how heavy was it? | What was the nickname of the specimen found in Sascacheran and how heavy was it? | What was the nickname of the specimen found in Saskatchewan and how heavy was it? | -0.397 |
| S1 | tr-26 | Which horned dinosaur was among your primary prey targets? | Which horn dinosaur was among your primary prey targets? | Which one dinosaur was among your primary prey targets? | -0.41 |
| S1 | tr-32 | Did you see the Chicxulub asteroid impact that ended the dinosaurs? | Did you see the chicks you loob, asteroid impact that ended the dinosaurs? | Did you see the chick's lube asteroid impact that ended the dinosaurs? | -0.591 |
| S2 | vg-06 | When did Paul Gauguin arrive to stay with you in Arles? | When did Paul Gauguin arrive to stay with you and Arles? | When it Paul Guggan arrived to stay with you and alls. | -0.311 |
| S2 | vg-08 | What did the countryside around Arles remind you of? | What did the countryside around Arles remind of you? | What did the countryside around alls remind of you? | -0.266 |
| S3 | vg-14 | When did you paint Wheat Field with Cypresses? | When did you paint wheat field in Cypresses? | When did you paint wheat field in Cypress? | -0.388 |
| S3 | vg-15 | When did you paint Irises? | When did you paint Arises? | When did you paint irises? | -0.546 |
| S3 | vg-23 | Who was your doctor and friend in Auvers-sur-Oise? | Who was your doctor and friend in Aversur, Oise? | Who was your doctor and friend in our suroise? | -0.521 |
| S3 | vg-25 | Which two chairs did you paint while preparing for or living with Gauguin in Arles? | Which two chairs did you paint when preparing for or living with Gauguin in Arles? | which two chairs did you paint when preparing for or living with caution in Arles? | -0.216 |
| S4 | tr-12 | Were you a hunter or a scavenger? | Wario Hunter, Aura Scavenger. | Vario Hunter or a scavenger | -0.579 |
