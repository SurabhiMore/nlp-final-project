"""Echoes.ai web server.

Run from the repo root:
    uvicorn app.server:app --reload

Endpoints:
    GET  /            the phone page (app/static/index.html)
    GET  /health      what is loaded and working
    GET  /personas    the exhibits visitors can talk to
    POST /ask         a question (voice or text) in, a cited answer out
    POST /speak       one sentence in, a WAV clip out
    GET  /sound/{exhibit}/{name}   an exhibit's sound effect, such as the T. rex roar

The page calls /ask first and shows the answer straight away, then asks /speak
for each sentence in turn, playing sentence one while sentence two is made.
"""

import base64
import json
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from pipeline import config

try:
    from pipeline import retrieve as retrieval
except ImportError:
    retrieval = None
try:
    from pipeline import persona as persona_engine
except ImportError:
    persona_engine = None
try:
    from pipeline import tts
except ImportError:
    tts = None

STATIC_DIR = Path(__file__).resolve().parent / "static"
LOG_PATH = config.LOGS_DIR / "qa_log.jsonl"
TOP_K = int(os.getenv("TOP_K", "8"))
_log_lock = threading.Lock()

@asynccontextmanager
async def lifespan(_app):
    """Set PRELOAD_MODELS=1 to load Whisper and Kokoro at startup instead of on first use."""
    if os.getenv("PRELOAD_MODELS") == "1":
        from pipeline import stt

        stt.load()
        if tts is not None:
            exhibits = config.list_personas()
            voices = {p["voice"]["kokoro_voice"] for p in exhibits} or {"af_heart"}
            tts.load(voices)
            for p in exhibits:  # the first sentence in each voice is slow, so get it out of the way now
                tts.synthesize("Hello.", voice=p["voice"]["kokoro_voice"],
                               speed=float(p["voice"].get("speed", 1.0)),
                               pitch=float(p["voice"].get("pitch", 1.0)))
    yield


app = FastAPI(title="Echoes.ai", lifespan=lifespan)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _ms(start):
    return round((time.perf_counter() - start) * 1000)


def _get_persona(persona_id):
    try:
        return config.load_persona(persona_id)
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=404, detail=str(error))


def _write_log(entry):
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with _log_lock:
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")


@app.get("/", response_class=HTMLResponse)
def home():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse("<h1>Echoes.ai</h1><p>The phone page has not been added yet.</p>")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "exhibits": [p["id"] for p in config.list_personas()],
        "search_ready": retrieval is not None,
        "answers_ready": persona_engine is not None,
        "voice_ready": tts is not None,
        "page_ready": (STATIC_DIR / "index.html").exists(),
    }


@app.get("/personas")
def personas():
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "subject_type": p["subject_type"],
            "greeting": p["greeting"],
            "time_period": p["time_period"]["label"],
        }
        for p in config.list_personas()
    ]


@app.post("/ask")
async def ask(
    persona: str = Form(...),
    text: str | None = Form(None),
    audio: UploadFile | None = File(None),
    mode: str = Form("persona"),
    speak: bool = Form(False),
    session_id: str | None = Form(None),
):
    """Answer one visitor question.

    Send either `audio` (a recording) or `text`. `mode` is "persona" (the
    exhibit talks) or "neutral" (a plain museum guide, our baseline). Set
    `speak` to true to get audio for every sentence in this same response.
    """
    if retrieval is None or persona_engine is None:
        missing = [label for label, mod in [("search", retrieval), ("answer generation", persona_engine)] if mod is None]
        raise HTTPException(status_code=503, detail=f"Not ready yet: {', '.join(missing)}.")
    if mode not in ("persona", "neutral"):
        raise HTTPException(status_code=400, detail="mode must be 'persona' or 'neutral'")

    exhibit = _get_persona(persona)
    request_id = uuid.uuid4().hex[:12]
    timings = {}
    total_start = time.perf_counter()

    question = (text or "").strip()
    source = "text"
    if audio is not None:
        audio_bytes = await audio.read()  # kept in memory only, never saved
        if audio_bytes:
            from pipeline import stt

            start = time.perf_counter()
            question = stt.transcribe(audio_bytes)
            timings["stt_ms"] = _ms(start)
            source = "audio"
    if not question:
        raise HTTPException(status_code=400, detail="We could not hear a question. Please try again.")

    start = time.perf_counter()
    chunks = retrieval.retrieve(persona, question, k=TOP_K)
    timings["retrieval_ms"] = _ms(start)

    start = time.perf_counter()
    try:
        result = persona_engine.answer(persona, question, chunks, mode=mode)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"The language model did not respond: {error}")
    timings["llm_ms"] = _ms(start)

    by_id = {c["id"]: c for c in chunks}
    citations = [
        {
            "id": cid,
            "source": by_id[cid].get("source", ""),
            "url": by_id[cid].get("url", ""),
            "licence": by_id[cid].get("licence", ""),
            "snippet": by_id[cid]["text"][:220],
        }
        for cid in result["citations"]
        if cid in by_id
    ]

    sound = None
    if result.get("sound") and config.sound_path(persona, result["sound"]):
        sound = {
            "name": result["sound"],
            "url": f"/sound/{persona}/{result['sound']}",
            "note": exhibit.get("sounds", {}).get(result["sound"], {}).get("description", ""),
        }

    sentences = tts.speech_chunks(result["answer"]) if tts else []
    audio_clips = []
    if speak and sentences:
        voice = exhibit["voice"]["kokoro_voice"]
        speed = float(exhibit["voice"].get("speed", 1.0))
        pitch = float(exhibit["voice"].get("pitch", 1.0))
        start = time.perf_counter()
        for clip in tts.synthesize_sentences(result["answer"], voice=voice, speed=speed, pitch=pitch):
            audio_clips.append({
                "sentence": clip["sentence"],
                "wav_base64": base64.b64encode(clip["wav"]).decode("ascii"),
            })
            if "tts_first_ms" not in timings:
                timings["tts_first_ms"] = clip["ms"]
        timings["tts_total_ms"] = _ms(start)

    timings["total_ms"] = _ms(total_start)

    _write_log({
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_id": request_id,
        "session_id": session_id or "",
        "persona": persona,
        "mode": mode,
        "input": source,
        "question": question,
        "retrieved": [{"id": c["id"], "score": round(float(c.get("score", 0)), 3)} for c in chunks],
        "status": result["status"],
        "answer": result["answer"],
        "citations": result["citations"],
        "sound": sound["name"] if sound else "",
        "model": result.get("model", ""),
        "stt_model": _stt_model_name() if source == "audio" else "",
        "timings": timings,
    })

    return {
        "request_id": request_id,
        "persona": persona,
        "mode": mode,
        "question": question,
        "status": result["status"],
        "answer": result["answer"],
        "sentences": sentences,
        "citations": citations,
        "sound": sound,
        "audio": audio_clips,
        "timings": timings,
    }


@app.post("/speak")
def speak_sentence(persona: str = Form(...), text: str = Form(...)):
    """Turn one sentence into speech in the exhibit's voice."""
    if tts is None:
        raise HTTPException(status_code=503, detail="Text to speech is not merged yet.")
    exhibit = _get_persona(persona)
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text to speak.")
    if len(text) > 600:
        raise HTTPException(status_code=400, detail="Send one sentence at a time.")

    start = time.perf_counter()
    wav = tts.synthesize(
        text,
        voice=exhibit["voice"]["kokoro_voice"],
        speed=float(exhibit["voice"].get("speed", 1.0)),
        pitch=float(exhibit["voice"].get("pitch", 1.0)),
    )
    return Response(content=wav, media_type="audio/wav", headers={"X-TTS-ms": str(_ms(start))})


@app.get("/sound/{persona_id}/{name}")
def exhibit_sound(persona_id: str, name: str):
    """One of the sound effects listed in an exhibit's persona.json."""
    try:
        path = config.sound_path(persona_id, name)
    except (FileNotFoundError, ValueError):
        path = None
    if path is None:
        raise HTTPException(status_code=404, detail="No such sound.")
    return FileResponse(path, media_type="audio/wav")


def _stt_model_name():
    from pipeline import stt

    return stt.model_name()
