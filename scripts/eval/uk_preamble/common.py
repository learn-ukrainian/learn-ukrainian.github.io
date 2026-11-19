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

HARNESS_VERSION = "uk-preamble-harness/3"
# The review-scoring contract frozen in every manifest (#9623, designated decision 2026-10-03).
# Version 1 was the unversioned per-correction diffing; results are never compared across versions.
SCORING_VERSION = "uk-preamble-scoring/2"
BASELINE_VARIANT = "none"
# Pre-registered adoption order (Protocol v2, #9623): adapted-v2 is the candidate, original the alternative.
CANDIDATE_ORDER = ("adapted-v2", "original")
FALSE_ALARM_MAX_RISE = 2.0  # false alarms per 100 protected spans (percentage points)
CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
PROTOCOL_MIN_ERRORS = 60
PROTOCOL_MIN_PROTECTED = 40
PROTOCOL_WRITING_LEVELS = ("A2", "B1", "B2", "C1")
PROTOCOL_REPEATS = 3
PROTOCOL_KINDS = ("review", "writing")

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


APOSTROPHE_VARIANTS = "’ʼ‘`ʹ´"
_APOSTROPHES = str.maketrans(dict.fromkeys(APOSTROPHE_VARIANTS, "'"))
_WHITESPACE = re.compile(r"\s+")


def fold_apostrophes(text: str) -> str:
    """Map apostrophe variants to ASCII; length-preserving, so offsets stay valid."""
    return text.translate(_APOSTROPHES)


def normalise(text: str) -> str:
    """Comparison form: NFC, one apostrophe, collapsed whitespace, trimmed."""
    return _WHITESPACE.sub(" ", fold_apostrophes(unicodedata.normalize("NFC", text))).strip()


# --------------------------------------------------------------------------- scoring tokens

# Folded before tokenising (scoring contract, #9623): apostrophe variants to ASCII; the Unicode
# hyphen U+2010 and non-breaking hyphen U+2011 to the hyphen-minus; the ellipsis to three full stops.
# The soft hyphen, zero-width space/non-joiner/joiner, word joiner and BOM are deleted. Dashes
# (U+2013, U+2014) and quote marks are not folded: hyphen and dash are distinct in the norm.
_SCORING_FOLD = {
    **dict.fromkeys(APOSTROPHE_VARIANTS, "'"),
    "\u2010": "-",
    "\u2011": "-",
    "\u2026": "...",
    **dict.fromkeys("\u00ad\u200b\u200c\u200d\u2060\ufeff", ""),
}
# A word is a run of word characters and combining marks (stress) joined internally by an
# apostrophe or hyphen; two or more full stops are one token; any other non-space character
# is its own token. Whitespace is never a token.
_WORD_CHARS = r"[\w\u0300-\u036f]"
_SCORING_TOKEN = re.compile(rf"{_WORD_CHARS}+(?:['-]{_WORD_CHARS}+)*|\.{{2,}}|\S")


@dataclass(frozen=True)
class Token:
    """One scoring token: ``key`` is its folded form; ``start``/``end`` are offsets into the NFC text."""

    start: int
    end: int
    key: str


def tokenize(text: str) -> list[Token]:
    """The scoring tokens of ``text`` (NFC, folded as above; comparison is case-sensitive)."""
    text = unicodedata.normalize("NFC", text)
    chars: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        for out in _SCORING_FOLD.get(char, char):
            chars.append(out)
            origin.append(index)
    folded = "".join(chars)
    return [Token(origin[m.start()], origin[m.end() - 1] + 1, m.group()) for m in _SCORING_TOKEN.finditer(folded)]


def token_keys(text: str) -> tuple[str, ...]:
    return tuple(token.key for token in tokenize(text))


_CYRILLIC_WORD = re.compile(r"[А-Яа-яІіЇїЄєҐґ]+(?:['’ʼ-][А-Яа-яІіЇїЄєҐґ]+)*")
_LATIN_WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")


def cyrillic_words(text: str) -> list[str]:
    return _CYRILLIC_WORD.findall(text)


def latin_words(text: str) -> list[str]:
    return _LATIN_WORD.findall(text)


def word_count(text: str) -> int:
    """Cyrillic plus Latin-script words; the one length measure for metrics and judge length control."""
    return len(cyrillic_words(text)) + len(latin_words(text))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- private results directory

# Matched whole (``fullmatch``): ``$`` would also accept a trailing newline.
_RUN_TAG = re.compile(r"[a-z0-9][a-z0-9-]{0,31}")
_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}")


def validate_run_tag(tag: str) -> str:
    """A run tag enters task ids and file names: lowercase letters, digits and '-', at most 32 characters."""
    if not _RUN_TAG.fullmatch(tag):
        raise HarnessError(f"--run-tag {tag!r}: expected lowercase letters, digits and '-' (1-32, alphanumeric first)")
    return tag


def enclosing_work_tree(path: Path) -> Path | None:
    """The nearest of ``path`` and its ancestors that holds a ``.git`` entry (a Git work tree), else None."""
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


class ResultsDir:
    """The private results directory; every output path is checked to stay inside it.

    The directory must resolve (symlinks followed) outside every Git work tree, so
    prompts, set items and model outputs can never land in this repository or any
    other checkout where they could be committed. Checked before anything is written.
    """

    def __init__(self, path: Path) -> None:
        root = path.expanduser().resolve()
        tree = enclosing_work_tree(root)
        if tree is not None:
            raise HarnessError(
                f"results directory {root} is inside the Git work tree {tree}; "
                "private prompts and outputs must live outside every repository"
            )
        self.root = root

    def path(self, *parts: str) -> Path:
        """``root/part/...`` after checking each part is a plain file name and the result stays inside root."""
        for part in parts:
            if not _SAFE_NAME.fullmatch(part):
                raise HarnessError(f"unsafe results file name {part!r}")
        candidate = self.root.joinpath(*parts)
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root) or enclosing_work_tree(resolved) is not None:
            raise HarnessError(f"{candidate} resolves to {resolved}, outside the private results directory")
        return candidate


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
