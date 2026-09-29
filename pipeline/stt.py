"""Speech to text with Whisper, run through faster-whisper.

faster-whisper runs the same Whisper weights with CTranslate2, which is much
faster than plain PyTorch on a CPU. The model loads the first time it is used.

Which model we use depends on the hardware. On our laptops, large-v3-turbo took
about 14 seconds to transcribe a 2.5 second question on the CPU, while "base"
took about 1.6 seconds and gave the same transcript. So the default is "base"
on a CPU and "large-v3-turbo" on a GPU.

Settings (environment variables, all optional):
  WHISPER_MODEL         overrides the default model, e.g. "small" or "large-v3-turbo"
  WHISPER_DEVICE        "cpu" (default) or "cuda"
  WHISPER_COMPUTE_TYPE  default "int8" on CPU, "float16" on GPU
"""

import concurrent.futures
import io
import os
import threading

_model = None
_lock = threading.Lock()


def device():
    return os.getenv("WHISPER_DEVICE", "cpu")


def model_name():
    default = "large-v3-turbo" if device() == "cuda" else "base"
    return os.getenv("WHISPER_MODEL", default)


def _get_model():
    global _model
    with _lock:
        if _model is None:
            from faster_whisper import WhisperModel

            default_compute = "float16" if device() == "cuda" else "int8"
            _model = WhisperModel(
                model_name(),
                device=device(),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", default_compute),
                cpu_threads=os.cpu_count() or 4,
            )
    return _model


def load():
    """Load the model now instead of on the first request."""
    _get_model()


def transcribe(audio_bytes, language="en"):
    """Turn recorded audio (webm, ogg, wav, mp4 and so on) into text.

    The audio is decoded in memory and never written to disk.
    Raises RuntimeError if transcription takes longer than WHISPER_TIMEOUT seconds
    (default 30). Set WHISPER_TIMEOUT=0 to disable the timeout.
    """
    if not audio_bytes:
        return ""

    def _run():
        segments, _info = _get_model().transcribe(
            io.BytesIO(audio_bytes),
            language=language,
            beam_size=1,
            vad_filter=True,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()

    timeout = float(os.getenv("WHISPER_TIMEOUT", "30") or 0) or None
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise RuntimeError(
                f"Transcription timed out after {timeout}s. "
                "Set WHISPER_TIMEOUT env var to adjust or 0 to disable."
            )
