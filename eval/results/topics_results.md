# Topics on the curator stats page

Do visitor questions land in the right topic? Run on 2026-11-10 with `python -m eval.eval_topics`. `app/stats.py` tags each question with keyword rules, with no language model and no network. The labelled questions, and how they were made, are described in `eval/questions/topics/README.md`.

## Held-out questions

**56 of 66 right (0.848).** Questions real visitors asked in the user tests: 29 of 30. Questions written for the set: 27 of 36.

| Topic | Questions | Tagged by the rules | Right |
|---|---|---|---|
| Not about the exhibit (`off_topic`) | 4 | 3 | 3 |
| The guide itself (`the_guide`) | 3 | 2 | 2 |
| After their time (`after_their_time`) | 4 | 2 | 2 |
| Works and how they were made (`works`) | 8 | 9 | 7 |
| Letters and quotes (`letters_quotes`) | 2 | 2 | 2 |
| Family and friends (`people`) | 6 | 5 | 5 |
| Life, places and money (`life`) | 5 | 5 | 5 |
| Health and death (`health_death`) | 6 | 6 | 6 |
| Body, senses and sounds (`body`) | 8 | 10 | 8 |
| Food and hunting (`food_hunting`) | 3 | 3 | 3 |
| Where and how they lived (`habitat_life`) | 5 | 6 | 4 |
| Death and extinction (`death_extinction`) | 2 | 0 | 0 |
| Fossils, names and science (`fossils`) | 6 | 6 | 5 |
| Other or unclear (`other`) | 4 | 7 | 4 |

Every wrong result:

| Id | Exhibit | Question | Expected | Rules said |
|---|---|---|---|---|
| visit-s08-p6-2 | van-gogh | Start date of Gauguin's visit to Van Gogh's yellow house. | people | works |
| top-vg-02 | van-gogh | Which of your pictures took you the longest? | works | other |
| top-vg-15 | van-gogh | Do you know how much your paintings sell for now? | after_their_time | works |
| top-vg-16 | van-gogh | Have you seen the immersive Van Gogh shows? | after_their_time | other |
| top-tr-09 | t-rex | How big were your babies? | habitat_life | body |
| top-tr-10 | t-rex | Why did all the dinosaurs disappear? | death_extinction | habitat_life |
| top-tr-11 | t-rex | How long did you usually live? | death_extinction | habitat_life |
| top-tr-15 | t-rex | Are birds really your cousins? | fossils | other |
| top-tr-17 | t-rex | Can you do your loudest roar? | the_guide | body |
| top-tr-18 | t-rex | What time does the museum close? | off_topic | fossils |

## Development questions

The rules were written on these, so this is not a fair test: 166 of 170 right (0.976).

Every wrong result:

| Id | Exhibit | Question | Expected | Rules said |
|---|---|---|---|---|
| tr-07 | t-rex | How long is the most complete T. rex skeleton? | body | fossils |
| tr-27 | t-rex | How long was your largest tooth found so far including its root? | body | fossils |
| tr-30 | t-rex | Did you roar with an open mouth like the T-Rex in movies? | body | after_their_time |
| clf-vg-19 | van-gogh | What happened to you in 1890? | life | other |

## The user test logs on the curator page

What `/stats` shows for the 30 questions in all 6 user test logs read together (`python scripts/report_stats.py --log artifacts/evidence/session0*/P*_log.jsonl`):

| Topic | Questions | Not in sources | For example |
|---|---|---|---|
| Works and how they were made | 6 | 3 | bedroom / What was your inspiration behind your paintings? / Name your first pin brush. |
| Body, senses and sounds | 5 | 1 | How welcome you smell. / for your teeth / what sound was your roar |
| Other or unclear | 4 | 2 | What was... / on the back. / Tell me everything interesting about this exhibit. |
| Health and death | 3 | 0 | Did you die? / The doctor that treated Vincent van Gogh at the very end of his life. / identify the physician who cared for Van Gogh during his final days. |
| Family and friends | 2 | 1 | What did your brother Theo do for a living? / And exactly that, Paul Gauguin, come to stay with Van Gogh and Arles. |
| Fossils, names and science | 2 | 0 | The top formation was the T-Rex skeleton named Sue, discovered in... / The specific geological rock formation where the Sue T-Rex fossil was excavated. |
| Life, places and money | 2 | 1 | Did you move to Arles? / The name of the dog, you had as a boy. |
| Not about the exhibit | 2 | 0 | What is the capital of France? / 12 times 8 |
| Where and how they lived | 2 | 2 | A long-distance take to hatch in weeks. / Many hours to do sleep a day. |
| After their time | 1 | 0 | You ever meet a human. |
| The guide itself | 1 | 1 | can you hello in spanish |

## Limitations

- The same person labelled the questions and wrote the rules, so the held-out result is weaker than one from labels made by someone else. The visitor questions are the stronger test, because real people chose the words.
- The rules only know the words on their lists. A question that says the same thing in other words goes to the wrong topic or to Other.
- English only. A question in another language is tagged by the English search query the server saves for it.
- Each question gets one topic, the first that matches, so a question about two things counts once.
- The held-out set is small: some topics have only two questions in it.
