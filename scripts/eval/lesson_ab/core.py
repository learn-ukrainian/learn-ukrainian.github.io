"""Manifest, blind key and mechanical checks for the lesson-section A/B comparison.

The manifest names, per task, the plan, the writing prompt (with its SHA-256)
and the two blind outputs A and B. Which writer produced A and which B lives
only in the key file, read at unblinding. Outputs are imported: this harness
did not run the writers, so it records their file digests and the manifest's
provenance note and never claims an execution attestation for them.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml

from scripts.eval.uk_preamble.common import (
    CEFR_LEVELS,
    SEATS,
    HarnessError,
    cyrillic_words,
    read_json,
    sha256_file,
    sha256_text,
)
from scripts.eval.uk_preamble.scoring import SourcesClient
from scripts.verification.stress import _stress_positions_in_marked_string

HARNESS_VERSION = "uk-lesson-ab/1"
SIDES = ("A", "B")
FAMILIES = frozenset(seat.family for seat in SEATS.values())
_TASK_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class LessonTask:
    task_id: str
    level: str
    plan_path: Path
    plan_text: str
    prompt_path: Path
    prompt_text: str
    texts: dict[str, str]
    digests: dict[str, str]  # plan, prompt, A, B


@dataclass(frozen=True)
class Manifest:
    path: Path
    sha256: str
    evaluation_id: str
    writer_families: tuple[str, ...]
    key_sha256: str | None
    provenance: str
    tasks: tuple[LessonTask, ...]


def _resolve(base: Path, value: Any, what: str) -> Path:
    if not isinstance(value, str) or not value:
        raise HarnessError(f"{what}: expected a path string")
    path = Path(value).expanduser()
    path = path if path.is_absolute() else base / path
    if not path.is_file():
        raise HarnessError(f"{what}: {path} is not a file")
    return path.resolve()


def plan_level(plan: dict[str, Any], override: Any) -> str:
    """The CEFR level for vocabulary checks: the manifest's, else the plan's ``level``, else its ``cefr_min``."""
    for value in (override, plan.get("level"), plan.get("cefr_min")):
        if isinstance(value, str) and value.upper() in CEFR_LEVELS:
            return value.upper()
    raise HarnessError(f"no CEFR level in the plan (level={plan.get('level')!r}); set 'level' in the manifest")


def _load_task(base: Path, entry: Any, index: int) -> LessonTask:
    if not isinstance(entry, dict):
        raise HarnessError(f"tasks[{index}]: expected an object")
    task_id = entry.get("task_id")
    if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
        raise HarnessError(f"tasks[{index}].task_id: expected lowercase letters, digits and '-' (1-64)")
    where = f"task {task_id}"
    plan_path = _resolve(base, entry.get("plan_path"), f"{where}: plan_path")
    prompt_path = _resolve(base, entry.get("prompt_path"), f"{where}: prompt_path")
    prompt_sha = entry.get("prompt_sha256")
    if not isinstance(prompt_sha, str) or not _SHA256.fullmatch(prompt_sha):
        raise HarnessError(f"{where}: prompt_sha256 must be a lowercase hex SHA-256")
    if sha256_file(prompt_path) != prompt_sha:
        raise HarnessError(f"{where}: {prompt_path} does not match prompt_sha256")
    plan_text = plan_path.read_text(encoding="utf-8")
    plan = yaml.safe_load(plan_text)
    if not isinstance(plan, dict):
        raise HarnessError(f"{where}: {plan_path} is not a YAML mapping")
    outputs = {
        side: _resolve(base, entry.get(f"output_{side.lower()}"), f"{where}: output_{side.lower()}") for side in SIDES
    }
    texts = {side: path.read_text(encoding="utf-8") for side, path in outputs.items()}
    for side, text in texts.items():
        if not text.strip():
            raise HarnessError(f"{where}: output {side} is empty")
    digests = {"plan": sha256_text(plan_text), "prompt": prompt_sha}
    digests.update({side: sha256_text(texts[side]) for side in SIDES})
    return LessonTask(
        task_id=task_id,
        level=plan_level(plan, entry.get("level")),
        plan_path=plan_path,
        plan_text=plan_text,
        prompt_path=prompt_path,
        prompt_text=prompt_path.read_text(encoding="utf-8"),
        texts=texts,
        digests=digests,
    )


def load_manifest(path: Path) -> Manifest:
    """Read and verify the manifest; relative paths resolve against its directory."""
    path = path.expanduser().resolve()
    data = read_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list) or not data["tasks"]:
        raise HarnessError(f"{path}: expected an object with a non-empty 'tasks' list")
    families = data.get("writer_families")
    if not isinstance(families, list) or not families or any(f not in FAMILIES for f in families):
        raise HarnessError(f"writer_families must list the writers' model families, from {sorted(FAMILIES)}")
    key_sha = data.get("key_sha256")
    if key_sha is not None and (not isinstance(key_sha, str) or not _SHA256.fullmatch(key_sha)):
        raise HarnessError("key_sha256 must be a lowercase hex SHA-256 when present")
    tasks = tuple(_load_task(path.parent, entry, index) for index, entry in enumerate(data["tasks"]))
    ids = [task.task_id for task in tasks]
    if len(set(ids)) != len(ids):
        raise HarnessError("task ids must be unique")
    return Manifest(
        path=path,
        sha256=sha256_file(path),
        evaluation_id=str(data.get("evaluation_id") or path.stem),
        writer_families=tuple(sorted(set(families))),
        key_sha256=key_sha,
        provenance=str(data.get("provenance") or "not stated"),
        tasks=tasks,
    )


def load_key(path: Path, manifest: Manifest) -> dict[str, Any]:
    """The unblinding key: ``{"writers": {name: family}, "tasks": {task_id: {"A": name, "B": name}}}``.

    Every task maps A and B to the two distinct writers. When the manifest committed
    to the key's SHA-256 before judging, a different key file is refused.
    """
    digest = sha256_file(path)
    if manifest.key_sha256 is not None and digest != manifest.key_sha256:
        raise HarnessError(f"{path} does not match the manifest's key_sha256 commitment")
    data = read_json(path)
    writers = data.get("writers") if isinstance(data, dict) else None
    mapping = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(writers, dict) or len(writers) != 2 or any(f not in FAMILIES for f in writers.values()):
        raise HarnessError(f"{path}: 'writers' must map exactly two writer names to model families")
    if not isinstance(mapping, dict) or set(mapping) != {task.task_id for task in manifest.tasks}:
        raise HarnessError(f"{path}: 'tasks' must cover exactly the manifest's task ids")
    undeclared = sorted(set(writers.values()) - set(manifest.writer_families))
    if undeclared:
        # Judges were admitted against the manifest's families; an undeclared writer family voids that check.
        raise HarnessError(f"{path}: writer families {undeclared} are not in the manifest's writer_families")
    for task_id, sides in mapping.items():
        if not isinstance(sides, dict) or set(sides) != set(SIDES) or set(sides.values()) != set(writers):
            raise HarnessError(f"{path}: task {task_id} must map A and B to the two different writers")
    return {
        "sha256": digest,
        "commitment": "verified" if manifest.key_sha256 else "not committed in the manifest",
        "writers": dict(writers),
        "tasks": {task_id: dict(sides) for task_id, sides in mapping.items()},
    }


# --------------------------------------------------------------------------- mechanical checks

_STRESS_MARKS = frozenset("́̀")
_VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")
_LETTERS = "А-Яа-яІіЇїЄєҐґ"
_PART = rf"[{_LETTERS}][{_LETTERS}\u0300\u0301]*"
# A word starts with a Cyrillic letter, so a mark left by a Latin letter (``café``) is never a word of its own.
_MARKABLE_WORD = re.compile(rf"{_PART}(?:['’ʼ-]{_PART})*")


def strip_stress(text: str) -> str:
    """The text without combining stress marks (NFD, marks removed, NFC); nothing else changes."""
    return unicodedata.normalize(
        "NFC", "".join(ch for ch in unicodedata.normalize("NFD", text) if ch not in _STRESS_MARKS)
    )


# Private-use stand-ins: NFC must not fold a stress mark into its letter (е + grave is ѐ, г + acute is ѓ).
_HIDE_MARKS = str.maketrans({"\u0301": "\ue001", "\u0300": "\ue000"})
_SHOW_MARKS = str.maketrans({"\ue001": "\u0301", "\ue000": "\u0300"})


def marked_words(text: str) -> list[str]:
    """Words carrying a stress mark, in text order; letters are NFC and every mark stays a combining mark."""
    hidden = unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).translate(_HIDE_MARKS))
    words = _MARKABLE_WORD.findall(hidden.translate(_SHOW_MARKS))
    return [w for w in words if _STRESS_MARKS & set(w)]


class ChecksClient(Protocol):
    def ambiguous(self, plain_text: str, marked: list[str]) -> list[str]:
        """Forms ``check_text``'s stress check leaves ambiguous, given the writer's marked forms."""

    def verify(self, word: str) -> dict[str, Any]:
        """``verify_stress`` for one marked word."""

    def attested(self, forms: list[str]) -> set[str]:
        """The forms VESUM attests."""


class LocalChecks:
    """``check_text``'s stress check, ``verify_stress`` and VESUM, in-process on the local sources."""

    def __init__(self) -> None:
        from scripts.verification.check_text import check_text
        from scripts.verification.stress import verify_stress
        from scripts.verification.vesum import verify_words

        self._check_text = check_text
        self._verify = verify_stress
        self._verify_words = verify_words

    def ambiguous(self, plain_text: str, marked: list[str]) -> list[str]:
        result = self._check_text(text=plain_text, checks=["stress"], stress_forms=marked, max_findings=100_000)
        if result.get("status") == "error":
            raise RuntimeError(f"check_text failed: {result.get('error')}")
        return sorted({p["form"] for p in result["problems"] if p["check"] == "stress"})

    def verify(self, word: str) -> dict[str, Any]:
        return self._verify(word)

    def attested(self, forms: list[str]) -> set[str]:
        return {form for form, matches in self._verify_words(forms).items() if matches} if forms else set()


def mark_attested(word: str, readings: list[dict[str, Any]]) -> bool:
    """The writer's marks equal a reading's stress positions; a single mark on one position of a
    multi-position reading of an unhyphenated word is a variant stress and is attested too."""
    _, marks = _stress_positions_in_marked_string(word)
    for reading in readings:
        positions = set(reading.get("vowel_indices") or [])
        if set(marks) == positions or (len(marks) == 1 and "-" not in word and set(marks) <= positions):
            return True
    return False


def stress_metrics(text: str, plain: str, checks: ChecksClient) -> dict[str, Any]:
    """Each distinct marked word is attested (a source reading matches the mark), wrong (readings
    exist and none matches) or unverified (no trusted reading, e.g. not found or one syllable)."""
    marked = marked_words(text)
    attested: list[str] = []
    wrong: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []
    for word in sorted(set(marked)):
        result = checks.verify(word)
        matches = result.get("matches") or []
        if mark_attested(word, matches):
            attested.append(word)
        elif matches:
            wrong.append({"form": word, "attested": sorted({m.get("stressed_form") for m in matches})})
        else:
            reason = result.get("reason") or result.get("error") or result.get("status")
            unverified.append({"form": word, "reason": reason})
    polysyllabic = [w for w in cyrillic_words(plain) if sum(ch in _VOWELS for ch in w) >= 2]
    ambiguous = checks.ambiguous(plain, sorted(set(marked)))
    return {
        "stress_marked": len(marked),
        "stress_mark_coverage": len(marked) / len(polysyllabic) if polysyllabic else None,
        "stress_attested": len(attested),
        "stress_wrong": len(wrong),
        "stress_wrong_forms": wrong,
        "stress_unverified": len(unverified),
        "stress_unverified_forms": unverified,
        "stress_ambiguous_unresolved": len(ambiguous),
        "stress_ambiguous_forms": ambiguous,
    }


def split_capitalised(metrics: dict[str, Any], checks: ChecksClient) -> None:
    """Move capitalised forms whose lowercase VESUM attests out of ``vesum_invalid``.

    ``check_text`` licenses a capital only at a sentence, line, list or speech-turn
    start, so a quoted example (``Запитання «Можна карткою?»``) is reported too.
    Those stay visible as ``vesum_capitalised``; ``vesum_invalid`` keeps forms
    VESUM attests in no case.
    """
    invalid = metrics["vesum_invalid_forms"]
    lowered = {form: form[:1].lower() + form[1:] for form in invalid if form[:1].isupper()}
    known = checks.attested(sorted(set(lowered.values())))
    capitalised = sorted(form for form, lower in lowered.items() if lower in known)
    metrics["vesum_capitalised_forms"] = capitalised
    metrics["vesum_capitalised"] = len(capitalised)
    metrics["vesum_invalid_forms"] = [form for form in invalid if form not in capitalised]
    metrics["vesum_invalid"] = len(metrics["vesum_invalid_forms"])


def mechanical_checks(
    manifest: Manifest,
    sources: SourcesClient,
    checks: ChecksClient,
    log: Callable[[str], None] = lambda _message: None,
) -> list[dict[str, Any]]:
    """One record per (task, side); a text whose checks fail is kept with its reason, never dropped."""
    records = []
    for task in manifest.tasks:
        for side in SIDES:
            text = task.texts[side]
            plain = strip_stress(text)
            record: dict[str, Any] = {
                "task_id": task.task_id,
                "side": side,
                "level": task.level,
                "sha256": task.digests[side],
                "provenance": {"kind": "imported", "execution_attested": False, "note": manifest.provenance},
            }
            try:
                metrics = sources.writing_metrics(plain, task.level)
                split_capitalised(metrics, checks)
                metrics.update(stress_metrics(text, plain, checks))
            except (RuntimeError, OSError) as exc:
                log(f"mechanical-failed {task.task_id}-{side}: {exc}")
                records.append({**record, "failed": True, "reason": str(exc), "metrics": None})
                continue
            records.append({**record, "failed": False, "reason": None, "metrics": metrics})
    return records
