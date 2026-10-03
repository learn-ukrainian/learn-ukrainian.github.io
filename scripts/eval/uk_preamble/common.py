"""Shared constants, seats, normalisation and private-file I/O for the preamble harness."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HARNESS_VERSION = "uk-preamble-harness/1"
BASELINE_VARIANT = "none"
# Pre-registered adoption order (Protocol v2, #9623): adapted-v2 is the candidate, original the alternative.
CANDIDATE_ORDER = ("adapted-v2", "original")
FALSE_ALARM_MAX_RISE = 2.0  # false alarms per 100 protected spans (percentage points)
CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
PROTOCOL_MIN_ERRORS = 60
PROTOCOL_MIN_PROTECTED = 40
PROTOCOL_WRITING_LEVELS = ("A2", "B1", "B2", "C1")

# Error-type labels shared by the set and the review instructions (Protocol v2 strata).
ERROR_TYPES = (
    "spelling",
    "agreement",
    "numeral-noun",
    "vocative",
    "aspect",
    "case-government",
    "prepositional-calque",
    "active-participle-calque",
    "passive-reflexive-calque",
    "noun-chain",
    "lexical-russianism",
    "surzhyk",
    "paronym",
    "english-calque",
    "wrong-combination",
    "punctuation",
    "other",
)


class HarnessError(Exception):
    """Invalid input or state; the CLI exits 2."""


@dataclass(frozen=True)
class Seat:
    seat_id: str
    code: str
    agent: str
    model: str
    effort: str | None
    family: str


SEATS: dict[str, Seat] = {
    "gemini-3.8-flash-high": Seat("gemini-3.8-flash-high", "flash", "agy", "gemini-3.8-flash-high", None, "google"),
    "gpt-6.1-sol": Seat("gpt-6.1-sol", "sol", "codex", "gpt-6.1-sol", "high", "openai"),
    "claude-opus-5-5": Seat("claude-opus-5-5", "opus", "claude", "claude-opus-5-5", "high", "anthropic"),
}


def judge_seats(candidate: str) -> list[Seat]:
    """The two seats whose families differ from the candidate's, in registry order."""
    family = SEATS[candidate].family
    return [seat for seat in SEATS.values() if seat.family != family]


_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "‘": "'", "`": "'", "ʹ": "'", "´": "'"})
_WHITESPACE = re.compile(r"\s+")


def fold_apostrophes(text: str) -> str:
    """Map apostrophe variants to ASCII; length-preserving, so offsets stay valid."""
    return text.translate(_APOSTROPHES)


def normalise(text: str) -> str:
    """Comparison form: NFC, one apostrophe, collapsed whitespace, trimmed."""
    return _WHITESPACE.sub(" ", fold_apostrophes(unicodedata.normalize("NFC", text))).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_private_text(path: Path, text: str) -> None:
    """Atomic owner-only write; results hold private set items and model outputs."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_private_json(path: Path, value: Any) -> None:
    write_private_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
