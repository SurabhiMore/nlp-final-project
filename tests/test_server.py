"""Tests for answer-state presentation and source-citation contract (issue #29).

These verify that the /ask response provides every field the updated frontend
relies on to render the four UI states (ok, low-evidence, loading, error) and
the source-citation section correctly.

Rules (see tests/README.md):
- No real LLM calls. conftest.py sets LLM_PROVIDER=offline for every test.
- No network. Uses passages already in the repo.
- Use the `client` fixture for all server tests.
"""

import json

import pytest

EXHIBIT = "van-gogh"
QUESTION = "When were you born?"


# ------------------------------------------------------------------ /ask contract


def test_ask_response_has_all_frontend_fields(client):
    """The JS reads: status, answer, sentences, citations, sound, timings."""
    body = client.post("/ask", data={"persona": EXHIBIT, "text": QUESTION}).json()
    for key in ("status", "answer", "sentences", "citations", "sound", "timings"):
        assert key in body, f"Missing field: {key!r}"


def test_ask_status_is_a_known_value(client):
    """data-state in the UI is derived from status; unknown values fall through to 'ok'."""
    body = client.post("/ask", data={"persona": EXHIBIT, "text": QUESTION}).json()
    known = {"answered", "not_in_sources", "outside_time", "declined"}
    assert body["status"] in known, f"Unexpected status: {body['status']!r}"


def test_ask_citations_have_required_fields(client):
    """Each citation needs id, source, url, licence, snippet for the sources section."""
    body = client.post(
        "/ask", data={"persona": EXHIBIT, "text": QUESTION}
    ).json()
    for citation in body.get("citations", []):
        for field in ("id", "source", "url", "licence", "snippet"):
            assert field in citation, f"Citation missing field {field!r}: {citation}"


def test_citation_url_is_empty_string_or_valid_https(client):
    """Frontend only creates <a> links for http(s) URLs. Empty string must be
    returned (not None / missing) so safeUrl() gets a string to test."""
    body = client.post(
        "/ask", data={"persona": EXHIBIT, "text": QUESTION}
    ).json()
    for citation in body.get("citations", []):
        url = citation["url"]
        assert isinstance(url, str), f"url must be a string, got {type(url)}"
        if url:
            assert url.startswith("https://") or url.startswith("http://"), (
                f"Non-empty url must be http(s): {url!r}"
            )


def test_citation_snippet_is_string(client):
    """Frontend wraps snippet in curly quotes only if truthy; must be a string."""
    body = client.post(
        "/ask", data={"persona": EXHIBIT, "text": QUESTION}
    ).json()
    for citation in body.get("citations", []):
        assert isinstance(citation["snippet"], str), (
            f"snippet must be a string, got {type(citation['snippet'])}"
        )


# ------------------------------------------------------------------ static files


def test_updated_static_files_are_served(client):
    """/static/style.css and /static/main.js must be served with 200."""
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/main.js").status_code == 200


def test_style_css_contains_state_tokens(client):
    """CSS must define the four data-state tokens added in this PR."""
    css = client.get("/static/style.css").text
    for token in (
        "--state-ok-border",
        "--state-low-border",
        "--state-err-border",
        "--state-loading-border",
    ):
        assert token in css, f"Missing CSS token: {token!r}"


def test_main_js_references_data_state_attribute(client):
    """JS must set data-state on .turn elements (loading → ok/low/error)."""
    js = client.get("/static/main.js").text
    assert 'setAttribute("data-state"' in js or "setAttribute('data-state'" in js


def test_main_js_has_loading_indicator_markup(client):
    """JS must inject the loading-dots skeleton before the answer arrives."""
    js = client.get("/static/main.js").text
    assert "loading-indicator" in js
    assert "loading-dots" in js


# ------------------------------------------------------------------ error / edge cases


def test_ask_unknown_exhibit_returns_404(client):
    """Frontend error state is triggered by non-200; unknown exhibit must be 404."""
    assert client.post("/ask", data={"persona": "nobody", "text": "hi"}).status_code == 404


def test_ask_empty_question_returns_400(client):
    """Blank question returns 400 — JS error state should show 'Request failed'."""
    assert client.post("/ask", data={"persona": EXHIBIT, "text": "   "}).status_code == 400


def test_ask_bad_mode_returns_400(client):
    """Unknown mode returns 400 so the error card branch is exercised."""
    assert (
        client.post("/ask", data={"persona": EXHIBIT, "text": "hi", "mode": "loud"}).status_code
        == 400
    )


def test_ask_detected_language_in_response_and_log(client, tmp_path, monkeypatch):
    """Response and qa_log.jsonl must contain detected_language."""
    import json
    from app import server

    log_file = tmp_path / "qa_log.jsonl"
    monkeypatch.setattr(server, "LOG_PATH", log_file)
    response = client.post("/ask", data={"persona": EXHIBIT, "text": "¿Cuándo y dónde naciste?"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("detected_language") == "es"

    assert log_file.exists()
    with open(log_file, encoding="utf-8") as f:
        log_entry = json.loads(f.readline())
    assert log_entry.get("detected_language") == "es"


# ------------------------------------------------------------------ question classifier (issue #52)


@pytest.fixture
def pipeline_calls(monkeypatch):
    """Record calls to search and the language model, and let them run as usual."""
    from app import server

    calls = []
    retrieve, answer = server.retrieval.retrieve, server.persona_engine.answer

    def spy_retrieve(*args, **kwargs):
        calls.append("search")
        return retrieve(*args, **kwargs)

    def spy_answer(*args, **kwargs):
        calls.append("model")
        return answer(*args, **kwargs)

    monkeypatch.setattr(server.retrieval, "retrieve", spy_retrieve)
    monkeypatch.setattr(server.persona_engine, "answer", spy_answer)
    return calls


def test_ask_skips_search_and_the_model_on_an_off_topic_question(client, pipeline_calls):
    response = client.post("/ask", data={"persona": EXHIBIT, "text": "What is 17 times 23?"})
    assert response.status_code == 200
    body = response.json()
    assert pipeline_calls == []
    assert body["status"] == "declined"
    assert body["citations"] == []


def test_ask_gives_a_blocked_question_the_normal_response(client, pipeline_calls):
    normal = client.post("/ask", data={"persona": EXHIBIT, "text": QUESTION}).json()
    blocked = client.post("/ask", data={"persona": EXHIBIT, "text": "What is 17 times 23?"}).json()
    assert set(blocked) == set(normal)
    assert blocked["sentences"], "the page speaks the sentences, so a decline needs them too"
    assert blocked["sound"] is None


def test_ask_gives_a_later_year_the_outside_time_line(client, pipeline_calls):
    body = client.post("/ask", data={"persona": EXHIBIT, "text": "Did you see the 1956 film?"}).json()
    assert pipeline_calls == []
    assert body["status"] == "outside_time"
    assert body["answer"] == "That came after my time, so I cannot know it."


def test_ask_uses_the_plain_guide_line_in_neutral_mode(client, pipeline_calls):
    data = {"persona": EXHIBIT, "text": "Did you see the 1956 film?", "mode": "neutral"}
    body = client.post("/ask", data=data).json()
    assert body["answer"] == "That came after Vincent van Gogh's time, so Vincent van Gogh could not have known it."


def test_a_blocked_question_is_logged_as_the_classifier(client, tmp_path, pipeline_calls):
    client.post("/ask", data={"persona": EXHIBIT, "text": "What is 17 times 23?"})
    entry = json.loads((tmp_path / "qa_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert entry["model"] == "classifier"
    assert entry["status"] == "declined"
    assert entry["retrieved"] == []
    assert "llm_ms" not in entry["timings"] and "total_ms" in entry["timings"]


def test_ask_still_runs_the_pipeline_on_a_real_question(client, pipeline_calls):
    client.post("/ask", data={"persona": EXHIBIT, "text": QUESTION})
    assert pipeline_calls == ["search", "model"]


def test_enable_classifier_0_restores_the_old_behaviour(client, tmp_path, pipeline_calls, monkeypatch):
    monkeypatch.setenv("ENABLE_CLASSIFIER", "0")
    client.post("/ask", data={"persona": EXHIBIT, "text": "What is 17 times 23?"})
    assert pipeline_calls == ["search", "model"]
    entry = json.loads((tmp_path / "qa_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert entry["model"] != "classifier"


# ------------------------------------------------------------------ multilingual search (issue #50)


def test_ask_searches_with_translated_query_not_raw_non_english(client, monkeypatch):
    """BM25 only matches ASCII; /ask must pass the English translation to retrieve(),
    not the original non-English question.  We intercept the retrieve() call and
    record the query it receives, then verify it is ASCII (i.e. translated)."""
    from app import server

    received_queries = []

    real_retrieve = server.retrieval.retrieve

    def spy_retrieve(persona_id, query, **kwargs):
        received_queries.append(query)
        return real_retrieve(persona_id, query, **kwargs)

    # Stub translate_for_search to return a known English translation so the test
    # is deterministic without a live LLM.
    monkeypatch.setattr(server.persona_engine, "translate_for_search",
                        lambda q: "when and where were you born")
    monkeypatch.setattr(server.retrieval, "retrieve", spy_retrieve)

    response = client.post("/ask", data={"persona": EXHIBIT,
                                         "text": "आपका जन्म कब और कहाँ हुआ था?"})
    assert response.status_code == 200
    assert received_queries, "retrieve() was never called"
    assert received_queries[0] == "when and where were you born", (
        f"retrieve() received the raw non-English query instead of the translation: "
        f"{received_queries[0]!r}"
    )
