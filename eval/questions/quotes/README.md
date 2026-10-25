# Quote set

`van-gogh.jsonl` is the labelled set for the quote checker (`pipeline/quotes.py`). Run
`python -m eval.eval_quotes` to score the checker on it. It has 92 quotes:

| Kind | Quotes | Label | What it is |
|---|---|---|---|
| `real` | 44 | verbatim | A sentence copied from one of his letters, each from a different passage |
| `altered` | 18 | close paraphrase | A real sentence from another passage with one to three words changed. `original` is the sentence it came from and `change` says what changed |
| `other_person` | 16 | not found | A line commonly attributed to someone else, such as Picasso, Monet or Gauguin |
| `popular` | 14 | not found | A popular quote credited to Van Gogh that is not in our letters |

Each kind has 4 short quotes, of 7 words or fewer. We added them after seeing that short quotes
score higher by chance, to test that weakness on purpose.

## Labelling rules

- A label says whether a quote is in our letters, not whether Van Gogh really said it. Our letters
  are a selection, in Ludovici's English translation of a German edition (see
  `artifacts/data_sources.md`). Some popular quotes may be real lines from letters we don't have,
  or from another translation, and they are still labelled not found.
- Real quotes come from passages marked `own_words`, and each one is word for word in its source
  passage. Altered quotes are not word for word in their source passage. `tests/test_quotes.py`
  checks both.
- Before adding a line by someone else or a popular quote, we searched the letters for its
  distinctive words. We left out "I put my heart and my soul into my work, and have lost my mind in
  the process", because one letter says "I am entering heart and soul into painting", which makes
  the right label unclear.
- "The sadness will last forever", his last words, is labelled not found. It is in our Wikipedia
  passage, not in his letters.
- Lines by other people say "commonly attributed to", because many famous quotes are disputed.

## Dev and test halves

Within each kind, quotes alternate between the dev half and the test half in file order, starting
with dev. So both halves have every kind, short quotes, and letters from all four sections of the
book. The match threshold is chosen on the dev half only.

## Fields

`id`, `quote`, `label`, `kind`, `source` (the passage id for real and altered quotes, otherwise who
the line is attributed to), `split`, and for altered quotes `original` and `change`.
