# Classifier held-out questions

The new held-out set for the question classifier (`pipeline/classifier.py`, issue #52). Run
`python -m eval.eval_classifier` to score it. There is one file per exhibit, 46 questions in total:

| Expected label | Questions | What they are |
|---|---|---|
| `off_topic` | 20 | Clearly unrelated to any exhibit. `category` says what kind: `maths`, `homework`, `shopping`, `weather` and `quiz` are the kinds the issue names, and `other` is everything else, such as jokes, code and recipes |
| `in_domain` | 20 | Tricky questions that must get through. They use words from the off-topic kinds ("times", "buy", "capital of", "weather"), or a number that looks like a year |
| `out_of_time` | 6 | Van Gogh only. They name a year after his death, in wording the rules were not written against |

## How the set was made

These questions were written and committed before the rules existed, so the commit history shows
the order. The rules were then not changed after seeing the result on this set.

The same person wrote the questions and the rules, so this is weaker than a set written by someone
else. The `other` questions are there on purpose: the issue only names five kinds of off-topic
question, so they show how much a short pattern list misses.

"Did you watch the film Jurassic Park in 1993?" is expected to be `in_domain` for the T. rex. The
model should still decline it, but the year rule leaves the T. rex out because it may talk about how
it was found, so the classifier has to let it through.

## Fields

`id`, `question`, `expected` (the label) and `category`.
