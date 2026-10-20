"""Tests for answer-state presentation and source-citation contract (issue #29).

These verify that the /ask response provides every field the updated frontend
relies on to render the four UI states (ok, low-evidence, loading, error) and
the source-citation section correctly.

Rules (see tests/README.md):
- No real LLM calls. conftest.py sets LLM_PROVIDER=offline for every test.
- No network. Uses passages already in the repo.
- Use the `client` fixture for all server tests.
"""

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
