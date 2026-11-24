"""Tests for the live page (/live) and what it needs from the server.

No real model calls and no network (see tests/README.md). Kokoro is only loaded in the
test marked slow.
"""

import base64
import json
import re
from pathlib import Path

import pytest

from app.citations import best_quote
from pipeline import tts

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "app" / "static" / "live"


# ---------------------------------------------------------------- the page and its files

def test_live_page_is_served(client):
    response = client.get("/live")
    assert response.status_code == 200
    assert "/static/live/app.js" in response.text
    # three.js comes from our own static folder, so the page does not depend on a CDN
    assert "/static/vendor/three/three.module.min.js" in response.text


def test_plain_page_is_still_at_the_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "/static/main.js" in response.text


def test_live_files_are_served(client):
    for path in (
        "/static/live/app.js", "/static/live/scenes.js", "/static/live/sound.js", "/static/live/state.js",
        "/static/live/live.css", "/static/live/trex.glb", "/static/vendor/three/three.module.min.js",
        "/static/vendor/three/addons/loaders/GLTFLoader.js", "/static/vendor/three/addons/utils/BufferGeometryUtils.js",
    ):
        assert client.get(path).status_code == 200, path


def test_every_picture_the_scenes_load_exists():
    scripts = "".join((LIVE / name).read_text(encoding="utf-8") for name in ("app.js", "scenes.js"))
    names = re.findall(r"'([\w-]+\.(?:jpg|png))'", scripts)
    assert names
    for name in names:
        assert (LIVE / "art" / name).exists(), name
    assert (LIVE / "trex.glb").read_bytes()[:4] == b"glTF"


def test_art_manifest_points_at_files_that_exist():
    manifest = json.loads((LIVE / "art" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest
    for url, art in manifest.items():
        assert url.startswith("https://"), url
        assert (LIVE / "art" / art["image"]).exists(), art["image"]
        if art.get("order"):
            assert (LIVE / "art" / art["order"]).exists(), art["order"]
        for field in ("title", "date", "museum", "licence"):
            assert art[field], (url, field)


def test_art_manifest_covers_every_art_institute_painting_the_van_gogh_sources_cite():
    manifest = json.loads((LIVE / "art" / "manifest.json").read_text(encoding="utf-8"))
    cited = set()
    for line in (ROOT / "personas" / "van-gogh" / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
        url = json.loads(line).get("url", "")
        if url.startswith("https://www.artic.edu/artworks/"):
            cited.add(url.rstrip("/"))
    assert cited
    assert cited <= set(manifest)


# ---------------------------------------------------------------- /personas, /ask and /speak

def test_personas_give_the_years_for_the_time_travel(client):
    exhibits = {e["id"]: e for e in client.get("/personas").json()}
    assert exhibits["van-gogh"]["years"] == [1853, 1890]
    assert exhibits["t-rex"]["years"][1] < 0


def test_personas_list_their_sounds_so_the_t_rex_can_roar_when_it_wakes(client):
    exhibits = {e["id"]: e for e in client.get("/personas").json()}
    assert exhibits["t-rex"]["sounds"] == ["roar"]
    assert exhibits["van-gogh"]["sounds"] == []
    assert client.get("/sound/t-rex/roar").status_code == 200


def test_ask_citations_carry_the_backing_sentence(client):
    body = client.post("/ask", data={"persona": "van-gogh", "text": "When were you born?"}).json()
    for citation in body["citations"]:
        assert isinstance(citation["quote"], str)


def test_speak_without_timing_is_unchanged(client, monkeypatch):
    import app.server as srv

    monkeypatch.setattr(srv.tts, "synthesize", lambda text, **kw: b"RIFFplain")
    response = client.post("/speak", data={"persona": "van-gogh", "text": "I painted three versions."})
    assert response.content == b"RIFFplain"
    assert "x-echoes-timing" not in response.headers


def test_speak_with_timing_sends_the_sounds_and_words(client, monkeypatch):
    import app.server as srv

    calls = []
    timing = {"segs": [[0.4, 0.1, "AA", 2]], "words": [["I", 0.4, 0.55, 1], ["roar", 0.55, 1.0, 0]]}

    def fake_timed(text, **kw):
        calls.append(kw)
        return b"RIFFtimed", timing

    monkeypatch.setattr(srv.tts, "synthesize_timed", fake_timed)
    response = client.post("/speak", data={"persona": "t-rex", "text": "I roar.", "timing": "true"})
    assert response.status_code == 200
    assert response.content == b"RIFFtimed"
    assert json.loads(base64.b64decode(response.headers["x-echoes-timing"])) == timing
    # the exhibit's own voice settings, as without timing
    assert calls[0]["voice"] == "am_onyx"
    assert calls[0]["pitch"] == 0.85


def test_speak_timing_header_carries_words_in_other_scripts(client, monkeypatch):
    import app.server as srv

    timing = {"segs": [], "words": [["नमस्ते", 0.0, 0.5, 0]]}
    monkeypatch.setattr(srv.tts, "synthesize_timed", lambda text, **kw: (b"RIFF", timing))
    response = client.post("/speak", data={"persona": "van-gogh", "text": "नमस्ते", "lang": "hi", "timing": "true"})
    assert json.loads(base64.b64decode(response.headers["x-echoes-timing"]).decode("utf-8")) == timing


# ---------------------------------------------------------------- mouth shapes

def test_mouth_shapes_follow_the_phonemes_and_their_durations():
    # "paint" as Kokoro writes it: p, primary stress, the diphthong A (eɪ), n, t
    segs = tts.mouth_shapes("pˈAnt", [4, 1, 6, 2, 3], start=0.5)
    assert [s[2] for s in segs] == ["PP", "EH", "IH", "DD", "DD"]
    assert segs[0][0] == pytest.approx(0.5)
    assert segs[0][1] == pytest.approx(5 / 40)  # the stress mark's time goes to the sound before it
    assert segs[1][3] == 2  # the stressed vowel is marked
    assert sum(s[1] for s in segs) == pytest.approx(16 / 40)


def test_mouth_shapes_close_the_lips_and_pause_on_punctuation():
    segs = tts.mouth_shapes("mɑ.", [2, 3, 4])
    assert [s[2] for s in segs] == ["PP", "AA", "sil"]


def test_mouth_shapes_give_unknown_symbols_a_neutral_shape():
    segs = tts.mouth_shapes("ʰx", [1, 1])
    assert [s[2] for s in segs] == ["DD", "KK"]


# ---------------------------------------------------------------- the backing sentence

def test_best_quote_picks_the_sentence_that_backs_the_answer():
    passage = (
        "You know that, in my work, I like variety. Mauve's death was a hard blow to me. "
        "I must also paint a starry night, with cypresses, or, perhaps, over a field of ripe corn. "
        "We get wonderful nights here."
    )
    answer = "I wrote that I must paint a starry night with cypresses."
    assert best_quote(passage, answer).startswith("I must also paint a starry night")


def test_best_quote_keeps_initials_inside_a_sentence():
    passage = "Its arms were tiny. T. rex arms are very small relative to overall body size, measuring only 1 meter long."
    assert best_quote(passage, "My arms are very small").startswith("T. rex arms are very small")


def test_best_quote_handles_empty_text_and_cuts_long_sentences():
    assert best_quote("", "anything") == ""
    quote = best_quote(("word " * 200).strip() + ".", "word")
    assert len(quote) <= 321
    assert quote.endswith("…")


@pytest.mark.slow
def test_synthesize_timed_covers_the_whole_clip():
    wav, timing = tts.synthesize_timed("I painted three versions of The Bedroom.", voice="bm_lewis", speed=0.95)
    assert wav[:4] == b"RIFF"
    seconds = (len(wav) - 44) / 2 / tts.SAMPLE_RATE
    last = timing["segs"][-1]
    assert abs(last[0] + last[1] - seconds) < 0.25
    assert [w[0] for w in timing["words"]][:3] == ["I", "painted", "three"]
