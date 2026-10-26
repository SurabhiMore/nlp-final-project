# Spoken question set

`reference.jsonl` holds 40 questions for testing speech to text: 20 for each exhibit, copied word for word
from the held-out question files (`from` says which one). We picked questions with the names Whisper finds
hard, such as Theo, Gauguin, Arles, Saint-Rémy, Auvers-sur-Oise, Maastrichtian, Triceratops and Chicxulub,
together with plain ones. The vocabulary prompt is built from `persona.json` and the passages only, never from
these questions.

## Recording

Ask teammates and friends to read the questions aloud. Before recording, tell each person what the clips are
for, that the audio stays on our laptops and is deleted after the evaluation, and that only the transcripts
are committed. Record only people who agree. Try to get as many different accents as possible.

1. Give each person a speaker label: S1, S2, S3 and so on. Never use their name.
2. Have them read each question once, naturally, as if they were asking the exhibit. Record each question as
   its own clip in a quiet-ish room, on a phone or a laptop. Any format works (m4a, webm, mp3, wav, ogg).
3. Name each clip after the question id and put it in the speaker's folder:

   ```
   data/stt_audio/S1/vg-01.m4a
   data/stt_audio/S1/vg-02.m4a
   ...
   data/stt_audio/S2/tr-h09.m4a
   ```

   `data/` is in `.gitignore`, so the audio is never committed.
4. Optionally, write down each speaker's accent (no names) in `data/stt_audio/speakers.json`:

   ```json
   {"S1": {"accent": "Indian English"}, "S2": {"accent": "US English, Midwest"}}
   ```

5. Check which clips are still missing:

   ```bash
   python -m eval.eval_stt --check
   ```

We need at least 40 clips in all. One speaker reading every question is enough for that; more speakers give a
fairer picture.

## Running the evaluation

```bash
python -m eval.eval_stt
```

This writes `eval/results/stt_results.json` and `eval/results/stt_results.md`: word error rate, clips exactly
right, exhibit names heard right and seconds per clip for each setting, results by speaker, how well the
low-confidence flag picks out misheard clips, and every misheard clip. The first run downloads Whisper `small`
(about 460 MB). Delete the audio once the results are committed.
