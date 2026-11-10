# Topic questions

Labelled questions for the topic tags on the curator stats page (`app/stats.py`, issue #61).
Run `python -m eval.eval_topics` to score the tags. Each question has exactly one topic.

| File | Questions | What they are |
|---|---|---|
| `dev.jsonl` | 170 | Every question the team already wrote for the other evaluations (answers, held-out T. rex, time check, classifier, adversarial). The topic rules were written by looking at these |
| `test.jsonl` | 66 | Held out. 30 questions real visitors asked in the Session 5, 7 and 8 user tests, copied from their logs as heard (speech mistakes included), and 36 new questions written for this set in a visitor's words |

## Topics

Shared topics apply to every exhibit. The others depend on the exhibit's `subject_type` in its
`persona.json`, so a new person or creature gets the same topics without code changes.

| Topic | Shown as | Exhibits | What goes there |
|---|---|---|---|
| `off_topic` | Not about the exhibit | all | Maths, homework, shopping, today's weather, quiz questions, code, jokes, recipes, news and sport, and museum services such as opening hours |
| `the_guide` | The guide itself | all | Greetings, who or what the guide is, whether it is real or an AI, its instructions, and asking it to do something, like roar or speak another language |
| `after_their_time` | After their time | all | Something from after the exhibit's lifetime: films, songs, later artists, modern inventions, humans for a dinosaur, and for a person their fame, museums and prices today |
| `works` | Works and how they were made | person | Their paintings or other works: which, when, where, how and why, colours, materials, technique, inspiration, how many, and selling them |
| `letters_quotes` | Letters and quotes | person | Their letters, and whether they really said or wrote something |
| `people` | Family and friends | person | Family, friends, fellow artists and love |
| `life` | Life, places and money | person | Birth, childhood, school, homes, cities and travel, jobs, money, food, pets and daily life |
| `health_death` | Health and death | person | Illness, injuries, the asylum, doctors, death and last words |
| `body` | Body, senses and sounds | creature | Size, weight, teeth and bite, arms, skin or feathers, senses, brain, speed, and what they sounded like |
| `food_hunting` | Food and hunting | creature | What they ate, hunting or scavenging, prey and fights |
| `habitat_life` | Where and how they lived | creature | When and where they lived, the world and other animals around them, eggs and young, sleep, living alone or in groups |
| `death_extinction` | Death and extinction | creature | How long they lived, how they died, extinction and the asteroid |
| `fossils` | Fossils, names and science | creature | Fossils and skeletons such as Sue, where and when they were found, who paid for them, museum specimens and casts, the name, how scientists know, and relatives |
| `other` | Other or unclear | all | Too general ("tell me everything"), too garbled to tell, or none of the above |

## Labelling rules

- When a question fits two topics, `off_topic` comes first, then `the_guide`, then
  `after_their_time`, then the exhibit topic that is the main subject.
- A question goes to `after_their_time` only when it asks about the later thing itself. "Did you
  roar like the T. rex in the movies?" is about the roar, so it is `body`.
- A question about a work stays `works` even when it names a person or a place, for example "Which
  two chairs did you paint while preparing for Gauguin?" or "At which asylum were you staying when
  you created The Starry Night?".
- Size and body questions stay `body` even when asked through a skeleton. Questions about a
  specimen itself (its nickname, where it was found, who owns it, whether a cast is real) are
  `fossils`.
- Garbled questions get the topic they were clearly about ("How welcome you smell" is `body`), or
  `other` when it cannot be told ("on the back.").

## How the set was made

Both files were labelled and committed before the topic rules existed, so the commit history
shows the order. The rules were written on `dev.jsonl` only and not changed after seeing the result
on `test.jsonl`.

One person labelled both files and wrote the rules, so this is weaker than labels from someone
else. The 30 visitor questions are the stronger test, because real people chose the words. One of
them, "What is the capital of France?", is also in `dev.jsonl`, because a visitor asked the same
thing the team had written.

## Fields

`id`, `exhibit`, `question`, `topic`, `group` (`team`, `visitor` or `written`) and `source` (the
file the question came from, with the line number for visitor logs).
