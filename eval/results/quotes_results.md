# Quote checker

Does `pipeline/quotes.py` tell Van Gogh's real words from altered and made-up quotes? Run on 2026-10-25 with `python -m eval.eval_quotes`, on the 92 quotes in `eval/questions/quotes/van-gogh.jsonl`. The checker only looks in the passages marked as his own words (his letters).

## Threshold, chosen on the dev half only

A quote counts as a close paraphrase when its fuzzy score is 80 or more. Every threshold from 79 to 81 gave the best dev accuracy (1.000 on 46 quotes), and 80 is the middle one. Across the whole set, the lowest score for an altered quote was 76.2 and the highest for a quote that is not in his letters was 81.2.

## Test half (46 quotes)

Accuracy: **0.957**. Quotes of 7 words or fewer: 0.714; longer quotes: 1.000. False quotes called verbatim: 0.

| Expected \ checker said | verbatim | close paraphrase | not found |
|---|---|---|---|
| verbatim | 22 | 0 | 0 |
| close paraphrase | 0 | 8 | 1 |
| not found | 0 | 1 | 14 |

| Kind | Expected | Test accuracy |
|---|---|---|
| real | verbatim | 1.000 |
| altered | close paraphrase | 0.889 |
| other_person | not found | 1.000 |
| popular | not found | 0.857 |

## Every wrong result (both halves)

| Id | Half | Kind | Quote | Expected | Checker said | Score | Closest text in the letters |
|---|---|---|---|---|---|---|---|
| vgq-62 | test | altered | So our father is dead! | close paraphrase | not found | 76.2 | Your father might deplore (van-gogh-gut40393-0120) |
| vgq-92 | test | popular | I paint my dream. | not found | close paraphrase | 81.2 | night in my dream (van-gogh-gut40393-0150) |

## Quotes in saved Van Gogh answers

118 saved answers, 2 quotes in them, 0 word for word in his letters.

| Source | Answers | With a quote | Quotes | Verbatim |
|---|---|---|---|---|
| `answers_results.json` | 44 | 0 | 0 | 0 |
| `grounding_replies.jsonl` | 64 | 2 | 2 | 0 |
| `session05/P1_log.jsonl` | 3 | 0 | 0 | 0 |
| `session07/P2_log.jsonl` | 2 | 0 | 0 | 0 |
| `session07/P3_log.jsonl` | 2 | 0 | 0 | 0 |
| `session07/P4_log.jsonl` | 3 | 0 | 0 | 0 |

2 of the quotes that are not in his letters are word for word in one of the exhibit's other passages (for example Wikipedia), so the answer has a source, just not his own writing.

| Source | Answer | Quote | Checker said | Score | Word for word in another passage |
|---|---|---|---|---|---|
| `grounding_replies.jsonl` | vg-29 persona | The sadness will last forever. | not found | 77.2 | van-gogh-wiki-0041 |
| `grounding_replies.jsonl` | vg-29 neutral | The sadness will last forever. | not found | 77.2 | van-gogh-wiki-0041 |

## Limitations

- We wrote the altered quotes ourselves, and most change only a word or two. Heavier rewording is not tested.
- Our letters are a selection, in Ludovici's English translation of a German edition. A real quote from another translation would usually come out as not found, so not found means not in our letters, not that he never said it.
- Short quotes score higher by chance, because a few words can line up with almost any passage. They are where the checker makes its mistakes.
- Only quotation marks and "did you say ..." questions are treated as quotes, so a quote the model works into a sentence without quotation marks is not checked.
- A quote that runs across two passages can be missed, although passages overlap by about 100 characters.
