"""Tests for text to speech: sentence splitting, voice selection, and Hindi danda handling."""

import pytest

from pipeline import tts


# ---------------------------------------------------------------- sentence splitting

def test_split_sentences_basic_punctuation():
    result = tts.split_sentences("I painted this. It was my best work.")
    assert len(result) == 2
    assert result[0] == "I painted this."
    assert result[1] == "It was my best work."


def test_split_sentences_hindi_danda():
    """The Devanagari danda (।) should work as a sentence boundary."""
    text = "मैं एक संग्रहालय गाइड हूँ। मैं आपकी मदद करूँगा।"
    result = tts.split_sentences(text)
    assert len(result) == 2
    assert "संग्रहालय" in result[0]
    assert "मदद" in result[1]


def test_split_sentences_mixed_danda_and_period():
    """A mix of dandas and Latin periods should both be treated as sentence boundaries."""
    text = "मैं Van Gogh हूँ। I painted The Bedroom. यह मेरी कहानी है।"
    result = tts.split_sentences(text)
    assert len(result) == 3


def test_split_sentences_danda_only():
    text = "एक। दो। तीन वाक्य यहाँ है।"
    result = tts.split_sentences(text)
    # Short one-word pieces are joined onto the next.
    assert len(result) >= 1
    assert all(len(s.split()) >= 1 for s in result)


def test_split_sentences_empty_and_whitespace():
    assert tts.split_sentences("") == []
    assert tts.split_sentences(None) == []
    assert tts.split_sentences("   ") == []


def test_split_sentences_keeps_abbreviations_together():
    result = tts.split_sentences("I worked with Dr. Smith. He was great.")
    assert len(result) == 2
    assert result[0] == "I worked with Dr. Smith."


# ---------------------------------------------------------------- voice_for_language

def test_voice_for_language_english_returns_none():
    # English: caller should use the exhibit's configured voice, not a multilang voice.
    assert tts.voice_for_language("en") is None


def test_voice_for_language_hindi_returns_a_voice():
    voice = tts.voice_for_language("hi")
    assert voice is not None
    assert voice.startswith("h"), f"Hindi voice should start with 'h', got {voice!r}"


def test_voice_for_language_spanish_returns_a_voice():
    voice = tts.voice_for_language("es")
    assert voice is not None
    assert voice.startswith("e"), f"Spanish voice should start with 'e', got {voice!r}"


def test_voice_for_language_marathi_returns_none():
    """No Kokoro voice for Marathi: caller should show text only."""
    assert tts.voice_for_language("mr") is None


def test_voice_for_language_kannada_returns_none():
    """No Kokoro voice for Kannada: caller should show text only."""
    assert tts.voice_for_language("kn") is None


def test_voice_for_language_unknown_returns_none():
    assert tts.voice_for_language("fr") is None
    assert tts.voice_for_language("") is None
    assert tts.voice_for_language(None) is None


# ---------------------------------------------------------------- pipeline_for guard

def test_pipeline_for_rejects_unsupported_lang_code():
    """Voice 'xf_alpha' has lang code 'x', which is not supported."""
    with pytest.raises(ValueError, match="unsupported lang code"):
        tts._pipeline_for("xf_alpha")


def test_pipeline_for_accepts_hindi_lang_code(monkeypatch):
    """Voice 'hf_alpha' should not raise on the lang code check."""
    class FakePipeline:
        pass

    captured = {}

    def fake_KPipeline(lang_code, repo_id):
        captured["lang_code"] = lang_code
        return FakePipeline()

    import pipeline.tts as tts_mod
    monkeypatch.setitem(tts_mod._pipelines, "h", None)  # pre-populate to skip real load
    # Remove it so the branch runs.
    del tts_mod._pipelines["h"]

    def fake_import(lang_code, repo_id):
        captured["lang_code"] = lang_code
        return FakePipeline()

    monkeypatch.setattr(
        "pipeline.tts._pipelines",
        {k: v for k, v in tts_mod._pipelines.items() if k != "h"},
    )

    # Monkeypatch KPipeline at the module level.
    import sys
    kokoro_mod = type(sys)("kokoro")
    kokoro_mod.KPipeline = fake_import
    monkeypatch.setitem(sys.modules, "kokoro", kokoro_mod)

    result = tts._pipeline_for("hf_alpha")
    assert isinstance(result, FakePipeline)
    assert captured["lang_code"] == "h"


# ---------------------------------------------------------------- speech_chunks with danda

def test_speech_chunks_with_hindi_danda():
    """speech_chunks should split on dandas and not return empty chunks."""
    text = "मैंने पेरिस में बहुत पेंटिंग की। मेरे भाई थियो ने मेरी मदद की।"
    chunks = tts.speech_chunks(text)
    assert len(chunks) >= 1
    assert all(c.strip() for c in chunks)
