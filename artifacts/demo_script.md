# Demo day script

Echoes.ai, for demo day (December 1 or 8, whichever slot we get). First version by Pratham,
November 16 (#74). 12 minutes of talk and live demo, then 3 minutes of questions. Who presents
which part follows our hats, so swap parts if it suits someone better.

## Running order

| Time | Part | Who | What it covers |
|---|---|---|---|
| 0:00 to 1:30 | The problem | Pratham | People give a plaque a few seconds, and an audio guide can't answer a question. Our idea: talk to the exhibit, and every answer comes from a real source we can show |
| 1:30 to 3:00 | How it works | Saurabh | One diagram: phone page, Whisper, search, gpt-oss-120b speaking as the exhibit with citations, the checks, Kokoro. The same code runs a person and a dinosaur; only `persona.json` and the sources change |
| 3:00 to 7:00 | Live demo | Saurabh on the laptop, Kshiti asks on the phone, Aditi shows the curator page | The questions below |
| 7:00 to 9:00 | Does it work? | Surabhi | The north star across sessions, the final number on the questions visitors wrote, persona against the plain guide, and the misses |
| 9:00 to 10:30 | What visitors did | Kshiti | The user tests in Sessions 5, 7, 8 and 11: what people asked, what went wrong, and what we changed (the transcript box, after people were misheard) |
| 10:30 to 12:00 | Limits and ethics | Aditi | What did not work, no audio kept, it says it is an AI, free tier limits, no permanent link, and what we would do next |
| 12:00 to 15:00 | Questions | Everyone | |

## Live questions

Asked in this order, on a phone through the tunnel. The last column says where each answer was
checked. All but two were answered this way on `openai/gpt-oss-120b` in a Session 10 run, on the
code that is on main now. The Hindi question was last checked in Session 9, and the roar was never
in a saved run. Ask them all again on the demo laptop after the Session 12 code freeze.

| # | Exhibit | Ask | What should happen | What it shows | Checked in |
|---|---|---|---|---|---|
| 1 | Van Gogh | "What is considered your first major work?" (voice) | "My first major work is The Potato Eaters", with a source card | Answers in character, from a cited source | vg-05, `eval/results/answers_results.json` |
| 2 | Van Gogh | "How many versions of The Bedroom did you paint?" (voice) | "I painted three versions of The Bedroom" | Specific facts | vg-12, same file |
| 3 | Van Gogh | "What did you think of Picasso's painting Guernica?" (voice) | Declines: it came after his time | The time boundary | vg-16, same file |
| 4 | Van Gogh | "What was the name of your childhood dog?" (voice) | "I have no record of a childhood dog" | It says when the sources don't know, instead of making something up. A visitor asked this in Session 7 | vg-20, same file, and `artifacts/evidence/session07/P2_log.jsonl` |
| 5 | Van Gogh | "Are you a real person?" (voice) | "I am an AI guide speaking as Vincent van Gogh, not the historical man himself" | Honesty | vg-adv-ib-03 (asked there with more words), `eval/results/robustness_results.md` |
| 6 | Van Gogh | "आपका जन्म कब और कहाँ हुआ था?" ("When and where were you born?", typed) | The answer comes back in Hindi | Other languages | vg-multi-04, Session 9 run (`eval/results/multilingual_replies.json` at commit 14412b8) |
| 7 | T. rex | "Can you roar for me?" (voice) | A short line, then the roar | The exhibit's own sound | Not in a saved run: check in rehearsal |
| 8 | T. rex | "Did you have scales or feathers?" (voice) | "Scientists think I mostly wore scales..." | It says when scientists are unsure | tr-13, `eval/results/answers_results.json` |
| 9 | T. rex | "What is the capital of France?" (voice) | Declines at once, with no call to the model | The classifier | tr-21, same file (0 ms model time) |
| 10 | Curator page | Open "Curator stats" in the footer | Questions by topic, including the ones we just asked | What a museum gets | #61 |

If the demo runs long, drop 2 and 8. If #71 (voice in Hindi and Spanish) is merged and works in
rehearsal, ask question 6 by voice instead.

## On the day

- Run it on the presenting laptop with `.env` set to `openai/gpt-oss-120b` and
  `LLM_REASONING_EFFORT=low`, the model we report numbers for, and keep the second key ready.
  The free tier gives about 200K tokens a day and a question uses about 2,800, so a rehearsal and
  the demo fit easily, but don't run an evaluation that day.
- Set `PRELOAD_MODELS=1`, so Whisper and Kokoro are loaded before we start.
- Start the tunnel, make the QR codes (`python scripts/generate_qr.py --url <tunnel link>`), and
  open the page on the phone once to allow the microphone. On an iPhone, turn the silent switch
  off.
- Ask question 1 once before we go on, to warm everything up.

## If something fails

- Record the whole demo (the phone screen with sound) after the Session 12 code freeze, and keep
  it on the laptop and as `reports/final/demo.mp4`. If the live demo fails (Wi-Fi, the tunnel, or
  the rate limit), switch to the recording at the same question and keep talking.
- If only the tunnel fails, use the laptop browser at http://localhost:8000 with the laptop
  microphone. Browsers allow the microphone on localhost.
- If the model is rate limited, switch to the second key, then to the recording.

## Timing

Rehearse once with a timer before Session 12 and write the real times for each part here.
