# Dockerfile for Echoes.ai — Interactive AI Museum Guide
#
# This runs on Hugging Face Spaces, which gives us a free HTTPS URL with a real
# TLS certificate. That matters because browsers only allow the microphone on
# localhost or on https:// — without it, the hold-to-ask button silently fails
# on any phone that isn't on the same machine as the server.
#
# Build locally to test before pushing:
#   docker build -t echoes .
#   docker run -p 7860:7860 --env-file .env echoes
#   open http://localhost:7860
#
# On Hugging Face Spaces, set these three secrets in Space Settings → Variables and secrets:
#   LLM_API_KEY    your API key (Groq, OpenAI-compatible, etc.)
#   LLM_BASE_URL   e.g. https://api.groq.com/openai/v1
#   LLM_MODEL      e.g. openai/gpt-oss-120b

# Python 3.11 is the sweet spot for this project — Kokoro doesn't install on 3.13,
# and 3.10 is approaching end-of-life. Slim keeps the base image under 200 MB.
FROM python:3.11-slim

# ----- system packages -------------------------------------------------------
# ffmpeg:       av (the audio/video library that faster-whisper uses) needs it to
#               decode the webm blobs the browser sends us. Without it, Whisper
#               silently gets empty audio.
# libsndfile1:  soundfile uses this to write the WAV files Kokoro produces.
# git:          some pip packages (e.g. kokoro) fetch small data files at install
#               time via git. Without it those installs fail silently.
# curl:         handy for manual smoke tests inside the running container.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ----- working directory ------------------------------------------------------
# /app is the convention for Hugging Face Spaces. The Space's file system is
# writable here, which matters for the logs/ directory and any cached model weights.
WORKDIR /app

# ----- Python dependencies ----------------------------------------------------
# Copy requirements first so Docker can cache this layer. The expensive part is
# downloading PyTorch (even the CPU build is ~800 MB), so we want to re-use
# the cache whenever requirements.txt hasn't changed.
COPY requirements.txt .

# The --extra-index-url pulls the CPU-only PyTorch wheel (~800 MB) instead of
# the GPU build (~2.5 GB). On the free Spaces CPU tier we have no GPU anyway,
# so the GPU build would just be wasted space.
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Download the spaCy English model. pipeline/timecheck.py uses it to extract
# named entities for the time-boundary check. If it isn't present, timecheck
# falls back to a regex approach — still works, just slightly less accurate.
RUN python -m spacy download en_core_web_sm

# ----- application code -------------------------------------------------------
# Copy everything else after the dependency layer so code changes don't
# bust the expensive pip-install cache.
COPY . .

# ----- runtime environment ----------------------------------------------------
# PRELOAD_MODELS=1 tells the server to load Whisper and Kokoro at startup
# rather than on the first request. The first request is slow either way while
# models initialise — doing it at startup means the loading happens during the
# Spaces health-check window, not in front of a waiting visitor.
ENV PRELOAD_MODELS=1

# HF Spaces expects the app to listen on port 7860. The Space's proxy
# handles the HTTPS termination and forwards plain HTTP to us here.
EXPOSE 7860

# Start the server. --host 0.0.0.0 is required inside Docker — the default
# 127.0.0.1 would make the server unreachable from outside the container.
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "7860"]
