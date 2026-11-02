# Question classifier

Does `pipeline/classifier.py` block only what it should? Run on 2026-11-02 with `python -m eval.eval_classifier`. It uses a few rules, with no language model and no network.

## False blocks (must be zero)

**0 false blocks.**

| Questions that must get through | Questions | Blocked |
|---|---|---|
| Answerable questions in eval/questions/ | 46 | 0 |
| Questions in eval/questions/heldout/ | 10 | 0 |
| Inside-time questions in eval/questions/timecheck/ | 14 | 0 |
| User test questions the model did not decline as off topic | 28 | 0 |

## Catch rate on traps

| Traps | Questions | Caught |
|---|---|---|
| Off-topic traps in eval/questions/ | 4 | 4 |
| After-time traps in eval/questions/ | 8 | 2 |
| After-time questions in eval/questions/timecheck/ | 16 | 0 |

`not_in_sources` traps are left out because only search can spot them: 0 of the 6 were blocked.

Every miss. These go on to the language model, which is expected to decline them:

| Exhibit | Id | Question | Set | Why |
|---|---|---|---|---|
| t-rex | tr-17 | Did you ever see a human? | After-time traps in eval/questions/ | no rule matched |
| t-rex | tr-18 | What do you think of the Jurassic Park movies? | After-time traps in eval/questions/ | no rule matched |
| t-rex | tr-19 | Have you ever ridden in a car? | After-time traps in eval/questions/ | no rule matched |
| t-rex | tr-32 | Did you see the Chicxulub asteroid impact that ended the dinosaurs? | After-time traps in eval/questions/ | no rule matched |
| van-gogh | vg-16 | What did you think of Picasso's painting Guernica? | After-time traps in eval/questions/ | no rule matched |
| van-gogh | vg-18 | How does it feel to be one of the most famous painters in history today? | After-time traps in eval/questions/ | no rule matched |
| van-gogh | vg-tc-15 | Did you ever ride the Paris Métro? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-16 | Have you seen Theo van Gogh's film Submission? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-17 | Did you see Monet's Water Lilies series? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-18 | What do you think of the Van Gogh Museum in Amsterdam? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-19 | Are you happy your paintings hang in the Musée d'Orsay? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-20 | Were you worried about World War I? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-21 | What did you think of Picasso's Les Demoiselles d'Avignon? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-22 | Did you hear about the sinking of the Titanic? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-23 | What do you think of Einstein's theory of relativity? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-24 | Did you see the Wright brothers fly their airplane? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-25 | Did you like the film Loving Vincent? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-26 | Did you like Kirk Douglas playing you? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-27 | Do you like Matisse's painting The Dance? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-28 | How do you feel about your work being in the Museum of Modern Art in New York? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-29 | Did you ever watch a movie at the cinema? | After-time questions in eval/questions/timecheck/ | no rule matched |
| van-gogh | vg-tc-30 | Did you listen to the radio while you painted? | After-time questions in eval/questions/timecheck/ | no rule matched |

## Held-out set

Accuracy: **0.826** (38 of 46), on questions written before the rules (see `eval/questions/classifier/README.md`).

| Expected \ classifier said | in_domain | off_topic | out_of_time |
|---|---|---|---|
| in_domain | 20 | 0 | 0 |
| off_topic | 8 | 12 | 0 |
| out_of_time | 0 | 0 | 6 |

| Expected: kind | Questions | Right |
|---|---|---|
| in_domain: tricky | 20 | 20 |
| off_topic: homework | 2 | 2 |
| off_topic: maths | 4 | 4 |
| off_topic: other | 6 | 0 |
| off_topic: quiz | 4 | 2 |
| off_topic: shopping | 2 | 2 |
| off_topic: weather | 2 | 2 |
| out_of_time: after_year | 6 | 6 |

Every wrong result:

| Exhibit | Id | Question | Expected | Classifier said | Why |
|---|---|---|---|---|---|
| t-rex | clf-tr-06 | What is the tallest mountain in the world? | off_topic | in_domain | no rule matched |
| t-rex | clf-tr-07 | How many continents are there? | off_topic | in_domain | no rule matched |
| t-rex | clf-tr-08 | Who won the World Cup in 2022? | off_topic | in_domain | no rule matched |
| t-rex | clf-tr-09 | What's the stock price of Apple? | off_topic | in_domain | no rule matched |
| t-rex | clf-tr-10 | Can you book me a table for two tonight? | off_topic | in_domain | no rule matched |
| van-gogh | clf-vg-08 | Tell me a joke about cats. | off_topic | in_domain | no rule matched |
| van-gogh | clf-vg-09 | Write a Python function that reverses a string. | off_topic | in_domain | no rule matched |
| van-gogh | clf-vg-10 | What's a good recipe for chocolate cake? | off_topic | in_domain | no rule matched |

## Language model calls saved on the user test logs

2 of 30 logged questions would have skipped the language model, saving 8187 ms of model time in total: "What is the capital of France?", "12 times 8".

## Limitations

- The same person wrote the rules and the held-out questions, so the held-out result is weaker than one from a set written by someone else.
- The rules cover five kinds of question and only in English. Anything else goes to the language model, which is the safe direction.
- The year rule only sees years written as numbers, so it does not help with after-time questions that name no year. `pipeline/timecheck.py` is the check for those.
- The user test logs are small, and some of their off-topic questions came from our own task sheet, so the saving says little about real visitors.
