"""
Shared paths and exhibit (persona) configuration.

Every exhibit lives in personas/<id>/ and is described by a persona.json file.

Adding a new exhibit means adding a new folder with a persona.json and running scripts/build_corpus.py. No code changes are needed.
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = ROOT / "personas"
LOGS_DIR = ROOT / "logs"
EVAL_DIR = ROOT / "eval"

REQUIRED_KEYS = [
    "id", "name", "subject_type", "perspective", "time_period",
    "description", "speaking_style", "greeting", "voice", "sources",
]
SUBJECT_TYPES = {"person", "creature", "object", "place"}
PERSPECTIVES = {"own_words", "character"}
_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

def load_env(path=ROOT / ".env"):
    """
    Read KEY=VALUE lines from .env into the environment.
    Values already set in the environment win, so a real environment variable always overrides the file.
    """
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

load_env()

def persona_dir(persona_id):
    if not _ID_PATTERN.match(persona_id or ""):
        raise ValueError(f"Invalid exhibit id: {persona_id!r}")
    return PERSONAS_DIR / persona_id

def chunks_path(persona_id):
    return persona_dir(persona_id) / "chunks.jsonl"

def load_persona(persona_id):
    """Load and check one exhibit's persona.json."""
    path = persona_dir(persona_id) / "persona.json"
    if not path.exists():
        raise FileNotFoundError(f"No persona.json for exhibit '{persona_id}'")
    data = json.loads(path.read_text(encoding="utf-8"))

    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"{path} is missing: {', '.join(missing)}")
    if data["id"] != persona_id:
        raise ValueError(f"{path}: id '{data['id']}' does not match folder '{persona_id}'")
    if data["subject_type"] not in SUBJECT_TYPES:
        raise ValueError(f"{path}: subject_type must be one of {sorted(SUBJECT_TYPES)}")
    if data["perspective"] not in PERSPECTIVES:
        raise ValueError(f"{path}: perspective must be one of {sorted(PERSPECTIVES)}")
    for key in ("start", "end", "label", "boundary"):
        if key not in data["time_period"]:
            raise ValueError(f"{path}: time_period is missing '{key}'")
    for name, sound in data.get("sounds", {}).items():
        if not _ID_PATTERN.match(name):
            raise ValueError(f"{path}: sound name '{name}' should be lowercase letters and dashes")
        if not (path.parent / sound.get("file", "")).is_file():
            raise ValueError(f"{path}: sound '{name}' needs a file inside personas/{persona_id}/")
        if not sound.get("description"):
            raise ValueError(f"{path}: sound '{name}' needs a description")
    return data

def sound_path(persona_id, name):
    """The audio file for one of an exhibit's sounds, or None if it has no such sound."""
    persona = load_persona(persona_id)
    sound = persona.get("sounds", {}).get(name)
    if not sound:
        return None
    folder = persona_dir(persona_id).resolve()
    path = (folder / sound["file"]).resolve()
    return path if folder in path.parents and path.is_file() else None

def list_personas():
    """All exhibits that have a persona.json, sorted by id."""
    if not PERSONAS_DIR.exists():
        return []
    ids = sorted(p.parent.name for p in PERSONAS_DIR.glob("*/persona.json"))
    return [load_persona(pid) for pid in ids]