"""Tests for speech to text tuned to each exhibit, the /transcribe endpoint and eval/eval_stt.py (issue #41).

Whisper is replaced by a fake model in every test except the one marked slow, so
these run in a moment and need no model download.
"""

import json
from types import SimpleNamespace

import pytest

from eval import eval_stt
from pipeline import config, stt

PERSONA = {
    "name": "Ada Lovelace",
    "description": "A mathematician who wrote about the Analytical Engine.",
    "greeting": "Hello, I am Ada.",
    "time_period": {"label": "1815 to 1852, in London"},
}


# ---------------------------------------------------------------- vocabulary prompt

def test_proper_nouns_skip_the_first_word_of_a_sentence():
    assert stt.proper_nouns(["Yesterday we went to Arles. Arles was sunny."]) == ["Arles"]


def test_proper_nouns_keep_multi_word_names_together():
    assert stt.proper_nouns(["They lived in North America, in the Hell Creek area."]) == ["North America", "Hell Creek"]


def test_proper_nouns_drop_words_mostly_written_in_lower_case():
    texts = ["I went to the Museum.", "the museum was big", "a museum, a museum, a museum"]
    assert stt.proper_nouns(texts) == []


def test_proper_nouns_drop_short_words_and_abbreviations():
    assert stt.proper_nouns(["It was in the US and at the NMNH with Al."]) == []


def test_proper_nouns_strip_possessives_and_keep_accents():
    assert stt.proper_nouns(["I painted at Saint-Rémy, then saw Theo's flat and Theo again."]) == ["Theo", "Saint-Rémy"]


def test_proper_nouns_are_most_frequent_first_and_limited():
    text = "We met Theo. We met Theo. We met Theo. We saw Paris. We saw Paris. We met Anton."
    assert stt.proper_nouns([text], limit=2) == ["Theo", "Paris"]


def test_build_prompt_starts_with_the_exhibit_name():
    chunks = [{"text": "She worked with Charles Babbage in London. She met Babbage often."}]
    prompt = stt.build_prompt(PERSONA, chunks)
    assert prompt.startswith("A question for Ada Lovelace, about ")
    assert "Analytical Engine" in prompt and "Charles Babbage" in prompt and "London" in prompt


def test_build_prompt_does_not_repeat_names():
    chunks = [{"text": "Then London again. Then London. We saw Ada and Lovelace."}]
    prompt = stt.build_prompt(PERSONA, chunks)
    assert prompt.count("London") == 1
    assert prompt.count("Lovelace") == 1


def test_build_prompt_stays_within_the_word_limit():
    names = " ".join(f"We met Name{chr(97 + i)}{chr(97 + j)}." for i in range(26) for j in range(4))
    prompt = stt.build_prompt(PERSONA, [{"text": names}], limit=12)
    listed = prompt.split(", about ", 1)[1].rstrip(".").split(", ")
    assert len(PERSONA["name"].split()) + sum(len(n.split()) for n in listed) <= 12


def test_build_prompt_without_any_names():
    persona = {**PERSONA, "description": "", "greeting": "", "time_period": {"label": ""}}
    assert stt.build_prompt(persona, []) == "A question for Ada Lovelace."


@pytest.mark.parametrize("persona_id", [p["id"] for p in config.list_personas()])
def test_every_exhibit_gets_a_prompt_with_its_name(persona_id):
    persona = config.load_persona(persona_id)
    prompt = stt.exhibit_prompt(persona_id)
    assert prompt.startswith(f"A question for {persona['name']}")
    assert len(prompt.split()) <= stt.PROMPT_WORDS + 4  # plus "A question for ... about"


# ---------------------------------------------------------------- confidence flag

def _segment(text, avg_logprob, tokens):
    return SimpleNamespace(text=text, avg_logprob=avg_logprob, tokens=list(range(tokens)))


def test_average_logprob_weights_segments_by_tokens():
    segments = [_segment("a", -0.2, 3), _segment("b", -1.0, 1)]
    assert stt.average_logprob(segments) == pytest.approx(-0.4)


def test_average_logprob_of_nothing_is_none():
    assert stt.average_logprob([]) is None


def test_low_confidence_flag_uses_the_threshold(monkeypatch):
    assert stt.is_low_confidence(-0.9, threshold=-0.6)
    assert not stt.is_low_confidence(-0.3, threshold=-0.6)
    assert stt.is_low_confidence(None)
    monkeypatch.setenv("WHISPER_LOW_CONFIDENCE", "-0.2")
    assert stt.is_low_confidence(-0.3)


class FakeModel:
    def __init__(self, segments, duration=2.0):
        self.segments, self.duration, self.calls = segments, duration, []

    def transcribe(self, audio, **kwargs):
        self.calls.append(kwargs)
        return iter(self.segments), SimpleNamespace(duration=self.duration)


@pytest.fixture
def fake_model(monkeypatch):
    model = FakeModel([_segment(" When did you arrive in Arles?", -0.2, 5)])
    monkeypatch.setattr(stt, "_get_model", lambda name=None: model)
    return model


def test_transcribe_detailed_uses_the_exhibit_prompt_and_beam(fake_model, monkeypatch):
    monkeypatch.setenv("WHISPER_BEAM_SIZE", "5")
    heard = stt.transcribe_detailed(b"audio", persona_id="van-gogh")
    assert heard["text"] == "When did you arrive in Arles?"
    assert heard["low_confidence"] is False
    assert heard["avg_logprob"] == -0.2
    assert fake_model.calls[0]["initial_prompt"] == stt.exhibit_prompt("van-gogh")
    assert fake_model.calls[0]["beam_size"] == 5


def test_prompt_can_be_turned_off(fake_model, monkeypatch):
    monkeypatch.setenv("WHISPER_PROMPT", "0")
    stt.transcribe_detailed(b"audio", persona_id="van-gogh")
    assert fake_model.calls[0]["initial_prompt"] is None


def test_unsure_transcript_is_flagged(monkeypatch):
    monkeypatch.setattr(stt, "_get_model", lambda name=None: FakeModel([_segment("How welcome you smell", -1.1, 4)]))
    assert stt.transcribe_detailed(b"audio", persona_id="t-rex")["low_confidence"] is True


def test_empty_audio_is_not_sent_to_whisper(fake_model):
    heard = stt.transcribe_detailed(b"", persona_id="t-rex")
    assert heard["text"] == "" and heard["low_confidence"] is True
    assert fake_model.calls == []


def test_transcribe_still_returns_plain_text(fake_model):
    assert stt.transcribe(b"audio") == "When did you arrive in Arles?"


# ---------------------------------------------------------------- /transcribe and /ask

def _fake_transcribe(text="When did you arrive in Arles?", low=False, calls=None):
    def fake(audio_bytes, persona_id=None, **kwargs):
        if calls is not None:
            calls.append(persona_id)
        return {"text": text, "avg_logprob": -0.9 if low else -0.2, "low_confidence": low,
                "duration_s": 2.0, "model": "base", "beam_size": 1, "prompt": ""}
    return fake


def _audio():
    return {"audio": ("question.webm", b"fake audio", "audio/webm")}


def test_transcribe_returns_the_text_without_answering(client, monkeypatch):
    calls = []
    monkeypatch.setattr(stt, "transcribe_detailed", _fake_transcribe(calls=calls))
    response = client.post("/transcribe", data={"persona": "van-gogh"}, files=_audio())
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "When did you arrive in Arles?"
    assert body["low_confidence"] is False
    assert "stt_ms" in body["timings"]
    assert "answer" not in body
    assert calls == ["van-gogh"]


def test_transcribe_passes_the_low_confidence_flag(client, monkeypatch):
    monkeypatch.setattr(stt, "transcribe_detailed", _fake_transcribe("How welcome you smell", low=True))
    body = client.post("/transcribe", data={"persona": "t-rex"}, files=_audio()).json()
    assert body["low_confidence"] is True


def test_transcribe_rejects_empty_audio(client):
    files = {"audio": ("question.webm", b"", "audio/webm")}
    assert client.post("/transcribe", data={"persona": "van-gogh"}, files=files).status_code == 400


def test_transcribe_unknown_exhibit_is_404(client):
    assert client.post("/transcribe", data={"persona": "nobody"}, files=_audio()).status_code == 404


def test_transcribe_timeout_is_503(client, monkeypatch):
    def too_slow(*args, **kwargs):
        raise RuntimeError("Transcription timed out after 30.0s.")
    monkeypatch.setattr(stt, "transcribe_detailed", too_slow)
    assert client.post("/transcribe", data={"persona": "van-gogh"}, files=_audio()).status_code == 503


def _last_log(tmp_path):
    return json.loads((tmp_path / "qa_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])


def test_ask_logs_an_edited_transcript(client, tmp_path):
    data = {"persona": "t-rex", "text": "How well can you smell?", "heard": "How welcome you smell.", "stt_ms": "480"}
    response = client.post("/ask", data=data)
    assert response.status_code == 200
    assert response.json()["question"] == "How well can you smell?"
    entry = _last_log(tmp_path)
    assert entry["input"] == "transcript"
    assert entry["heard"] == "How welcome you smell."
    assert entry["edited"] is True
    assert entry["timings"]["stt_ms"] == 480


def test_ask_logs_a_transcript_sent_unchanged(client, tmp_path):
    client.post("/ask", data={"persona": "van-gogh", "text": "When did you arrive in Arles?",
                              "heard": "When did you arrive in Arles?"})
    entry = _last_log(tmp_path)
    assert entry["input"] == "transcript" and entry["edited"] is False


def test_ask_with_typed_text_is_unchanged(client, tmp_path):
    response = client.post("/ask", data={"persona": "van-gogh", "text": "When were you born?"})
    assert response.status_code == 200
    entry = _last_log(tmp_path)
    assert entry["input"] == "text" and entry["heard"] == "" and entry["edited"] is False
    assert "stt_ms" not in entry["timings"]


def test_ask_with_audio_still_works(client, monkeypatch, tmp_path):
    monkeypatch.setattr(stt, "transcribe", lambda audio_bytes, persona_id=None, **kw: "When were you born?")
    response = client.post("/ask", data={"persona": "van-gogh"}, files=_audio())
    assert response.status_code == 200
    assert response.json()["question"] == "When were you born?"
    assert _last_log(tmp_path)["input"] == "audio"


def test_phone_page_has_the_transcript_step(client):
    html = client.get("/").text
    for element in ('id="heard"', 'id="heard-text"', 'id="heard-warning"', 'id="heard-send"', 'id="heard-redo"'):
        assert element in html
    js = client.get("/static/main.js").text
    assert '"/transcribe"' in js
    assert 'body.append("heard"' in js


# ---------------------------------------------------------------- eval/eval_stt.py

def test_word_errors_counts_substitutions_deletions_and_insertions():
    assert eval_stt.word_errors("how well can you smell", "how well can you smell") == 0
    assert eval_stt.word_errors("how well can you smell", "how welcome you smell") == 2
    assert eval_stt.word_errors("a b c", "a c") == 1
    assert eval_stt.word_errors("a b", "a b c d") == 2


def test_wer_ignores_case_punctuation_and_accents():
    assert eval_stt.wer("Were you a T. rex at Saint-Rémy?", "were you a T-Rex at saint remy") == 0


def test_reference_set_is_forty_held_out_questions_copied_exactly():
    reference = eval_stt.load_reference()
    assert len(reference) >= 40
    by_persona = {}
    for item in reference.values():
        by_persona[item["persona"]] = by_persona.get(item["persona"], 0) + 1
        source = config.ROOT / item["from"]
        questions = {json.loads(line)["id"]: json.loads(line)["question"]
                     for line in source.read_text(encoding="utf-8").splitlines() if line.strip()}
        assert questions[item["id"]] == item["text"]
    assert by_persona == {"t-rex": 20, "van-gogh": 20}


def _make_clips(folder, clips):
    for speaker, qid in clips:
        (folder / speaker).mkdir(parents=True, exist_ok=True)
        (folder / speaker / f"{qid}.wav").write_bytes(f"{speaker} {qid}".encode())


def test_find_clips_skips_named_folders_and_unknown_ids(tmp_path):
    reference = eval_stt.load_reference()
    _make_clips(tmp_path, [("S1", "vg-01"), ("S1", "zz-99"), ("Priya", "vg-01")])
    (tmp_path / "S1" / "notes.txt").write_text("not audio")
    clips, skipped = eval_stt.find_clips(tmp_path, reference)
    assert [(s, q) for s, q, _ in clips] == [("S1", "vg-01")]
    assert len(skipped) == 2
    assert any("never a name" in s for s in skipped)


def test_check_lists_missing_clips(tmp_path, capsys):
    _make_clips(tmp_path, [("S1", "vg-01"), ("S1", "tr-01")])
    assert eval_stt.check(tmp_path) == 2
    out = capsys.readouterr().out
    assert "S1: 2 of 40 clips, missing" in out and "vg-02" in out


def _row(errors, logprob, seconds=0.5):
    return {"ref_words": 5, "errors": errors, "names": 1, "names_right": int(not errors), "seconds": seconds,
            "duration_s": 2.0, "avg_logprob": logprob}


def test_summarize_counts_flags_against_mistakes():
    rows = [_row(0, -0.1), _row(0, -0.8), _row(2, -0.9), _row(1, -0.2)]
    s = eval_stt.summarize(rows, threshold=-0.5)
    assert s["wer"] == pytest.approx(3 / 20, abs=1e-3)
    assert s["exact"] == 2 and s["misheard"] == 2
    assert s["misheard_flagged"] == 1 and s["right_flagged"] == 1
    assert s["names_right"] == 2 and s["names"] == 4


def test_suggest_picks_the_lowest_error_within_the_time_budget():
    summaries = {
        "current": {"wer": 0.20, "seconds_median": 0.3},
        "prompt": {"wer": 0.10, "seconds_median": 0.3},
        "small_prompt": {"wer": 0.05, "seconds_median": 3.0},
    }
    assert eval_stt.suggest(summaries, max_seconds=2.0) == "prompt"
    assert eval_stt.suggest(summaries, max_seconds=5.0) == "small_prompt"
    assert eval_stt.suggest(summaries, max_seconds=0.1) is None


def test_suggest_threshold_separates_misheard_from_right_clips():
    rows = [_row(0, -0.1), _row(0, -0.15), _row(1, -0.5), _row(2, -0.7)]
    threshold = eval_stt.suggest_threshold(rows)
    assert -0.5 < threshold <= -0.15
    assert eval_stt.suggest_threshold([_row(0, -0.1)]) is None


def test_run_scores_every_setting_and_writes_a_report(tmp_path, monkeypatch):
    _make_clips(tmp_path, [("S1", "vg-04"), ("S1", "tr-23"), ("S2", "vg-04")])
    heard_as = {"vg-04": "When did you arrive in Arles?", "tr-23": "How welcome you smell?"}

    def fake(audio_bytes, model=None, beam=None, prompt=None, **kwargs):
        qid = audio_bytes.decode().split()[1]
        text = heard_as[qid] if prompt else heard_as[qid].replace("Arles", "Aral")
        return {"text": text, "avg_logprob": -0.2 if "Arles" in text else -0.8, "low_confidence": False,
                "duration_s": 2.0, "model": model, "beam_size": beam, "prompt": prompt}

    monkeypatch.setattr(stt, "transcribe_detailed", fake)
    report = eval_stt.run(tmp_path, settings=("current", "prompt"))
    assert report["clips"] == 3
    assert report["summary"]["prompt"]["wer"] < report["summary"]["current"]["wer"]
    assert report["summary"]["prompt"]["names_right"] > report["summary"]["current"]["names_right"]
    assert report["suggested"] == "prompt"
    markdown = eval_stt.to_markdown(report)
    assert "| prompt | base | 1 | yes |" in markdown
    assert "How welcome you smell?" in markdown


def test_run_without_recordings_says_where_to_put_them(tmp_path):
    with pytest.raises(SystemExit, match="No recordings found"):
        eval_stt.run(tmp_path / "missing")


# ---------------------------------------------------------------- real models

@pytest.mark.slow
def test_whisper_with_the_exhibit_prompt_is_no_worse_than_without():
    pytest.importorskip("kokoro", reason="kokoro is not installed")
    pytest.importorskip("faster_whisper", reason="faster_whisper is not installed")
    from pipeline import tts

    question = "What was your brother Theo's job in Paris?"
    wav = tts.synthesize(question, voice="af_heart")
    with_prompt = stt.transcribe_detailed(wav, persona_id="van-gogh")
    without = stt.transcribe_detailed(wav, prompt="")
    assert with_prompt["prompt"] == stt.exhibit_prompt("van-gogh")
    assert "paris" in with_prompt["text"].lower()
    assert isinstance(with_prompt["avg_logprob"], float)
    assert eval_stt.wer(question, with_prompt["text"]) <= eval_stt.wer(question, without["text"])
