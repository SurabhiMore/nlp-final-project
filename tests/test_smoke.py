"""Smoke tests: what the system does today.

These protect everyone's changes. If one fails after your change, either your
change broke something that used to work, or you changed the behaviour on
purpose; then update the test in the same pull request and say why.
"""
import json

import pytest

from eval import datasets
from pipeline import config
from pipeline.retrieve import retrieve

EXHIBITS = {"t-rex", "van-gogh"}
PASSAGE_FIELDS = {"id", "text", "source", "url", "licence", "score", "rank"}


def test_both_exhibits_load():
    exhibits = {p["id"]: p for p in config.list_personas()}
    assert set(exhibits) == EXHIBITS
    for persona in exhibits.values():
        assert set(config.REQUIRED_KEYS) <= set(persona)


@pytest.mark.parametrize("exhibit", sorted(EXHIBITS))
def test_question_file_passes_the_check(exhibit):
    assert datasets.check(exhibit) == 0


@pytest.mark.parametrize("exhibit", sorted(EXHIBITS))
def test_search_returns_ranked_passages(exhibit):
    results = retrieve(exhibit, "When and where were you born?", k=8)
    assert len(results) == 8
    for passage in results:
        assert PASSAGE_FIELDS <= set(passage)
        assert passage["id"].startswith(exhibit + "-")
    scores = [p["score"] for p in results]
    assert scores == sorted(scores, reverse=True)
    assert [p["rank"] for p in results] == list(range(1, 9))


def test_search_finds_the_passage_for_an_exact_wording_question():
    question = next(q for q in datasets.load_questions("t-rex") if q["id"] == "tr-05")
    support = datasets.supporting_chunk_ids(question, datasets.load_chunks("t-rex"))
    top = {p["id"] for p in retrieve("t-rex", question["question"], k=8)}
    assert support & top


def test_health_reports_every_part_ready(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert set(body["exhibits"]) == EXHIBITS
    assert body["search_ready"] and body["answers_ready"] and body["voice_ready"] and body["page_ready"]


def test_personas_lists_both_exhibits(client):
    items = client.get("/personas").json()
    assert {p["id"] for p in items} == EXHIBITS
    for p in items:
        assert p["greeting"] and p["time_period"]


def test_ask_by_text_returns_a_cited_answer(client):
    response = client.post("/ask", data={"persona": "t-rex", "text": "How fast could you run?"})
    assert response.status_code == 200
    body = response.json()
    for key in ("request_id", "question", "status", "answer", "sentences", "citations", "sound", "timings"):
        assert key in body
    assert body["status"] == "answered"
    assert body["citations"]
    for citation in body["citations"]:
        assert citation["url"].startswith("https://")
        assert citation["licence"]


@pytest.mark.parametrize("data, status_code", [
    ({"persona": "nobody", "text": "hi"}, 404),
    ({"persona": "t-rex", "text": "hi", "mode": "loud"}, 400),
    ({"persona": "t-rex", "text": "   "}, 400),
])
def test_ask_rejects_bad_requests(client, data, status_code):
    assert client.post("/ask", data=data).status_code == status_code


def test_each_question_is_logged_without_audio(client, tmp_path):
    client.post("/ask", data={"persona": "van-gogh", "text": "When were you born?", "session_id": "test"})
    entry = json.loads((tmp_path / "qa_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert entry["question"] == "When were you born?"
    assert entry["session_id"] == "test"
    assert "audio" not in entry


def test_roar_is_served_only_for_the_t_rex(client):
    response = client.get("/sound/t-rex/roar")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert client.get("/sound/van-gogh/roar").status_code == 404


def test_phone_page_is_served(client):
    assert "Echoes.ai" in client.get("/").text
    assert client.get("/static/main.js").status_code == 200


@pytest.mark.slow
def test_voice_round_trip():
    from pipeline import stt, tts

    wav = tts.synthesize("When did you move to Paris?", voice="af_heart")
    assert "paris" in stt.transcribe(wav).lower()
