#!/usr/bin/env python3
"""Tool-backed residual census for #6371 textbook leftovers.

Reads only committed oneshot inventories and in-repo textbook leftover lists.
Does not invent lemmas, start a corpus dump, or touch private PDFs.

Teacher-P1 admission bar (issue #6369): ``approve_for_publish`` plus a
learner-English gloss (Latin letters, no Ukrainian letters). Oneshot bulk
rows carry SUM-11 Ukrainian dumps and therefore stay residual unless a
later enrichment pass supplies an English anchor.

Admission of named leftovers is refused when ``data/vesum.db`` or
``data/sources.db`` is missing. This module never writes the live Atlas
pointer.

Run from the repository root::

    .venv/bin/python -m scripts.lexicon.census_atlas_6371_textbook_leftover --report
    .venv/bin/python -m scripts.lexicon.census_atlas_6371_textbook_leftover \\
        --write-report --report
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.build_data_manifest import _lemma_key

ONESHOT_INVENTORY = (
    PROJECT_ROOT / "data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml"
)
ONESHOT_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-07-19-textbook-jsonl-curated-bulk-approve.yaml"
)
NAMED_INVENTORIES: tuple[Path, ...] = (
    PROJECT_ROOT / "data/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/vashulenko-grade3-family-numerals.yaml",
)
NAMED_DECISIONS: tuple[Path, ...] = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-06-30-third-approved-textbook-ledger-batch.yaml",
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-07-03-fourth-approved-textbook-ledger-batch.yaml",
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-07-03-fifth-approved-textbook-ledger-batch.yaml",
)
DEFAULT_POINTER = PROJECT_ROOT / "site/src/data/lexicon-manifest.pointer.json"
DEFAULT_MANIFEST = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
DEFAULT_VESUM = PROJECT_ROOT / "data/vesum.db"
DEFAULT_SOURCES_DB = PROJECT_ROOT / "data/sources.db"
DEFAULT_REPORT_MD = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/oneshot/textbook-leftover-residual-census-6371.md"
)
DEFAULT_REPORT_JSON = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/oneshot/textbook-leftover-residual-census-6371.json"
)

CENSUS_ID = "atlas-6371-textbook-leftover-residual.v1"
_UKRAINIAN_LETTERS = frozenset("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя")
_ITEM_START = re.compile(r"^(?P<indent> *)- (?P<rest>\S.*)$")
_FIELD = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z0-9_]+):(?: (?P<value>.*))?$")
_ENTRY_LEMMA = re.compile(r'^      "lemma": "((?:\\.|[^"\\])*)"', re.MULTILINE)
_ENTRIES_ARRAY = "\n  \"entries\": ["
_YAML_QUOTED = re.compile(r"^(?P<q>['\"])(?P<body>.*)(?P=q)$")


@dataclass(frozen=True)
class InventoryRow:
    lemma: str
    gloss: str
    source_path: str
    locator: str = ""


@dataclass(frozen=True)
class DecisionRow:
    lemma: str
    decision: str
    approved_gloss: str
    source_path: str
    inventory_path: str = ""


@dataclass
class ArtifactStatus:
    path: str
    present: bool
    detail: str = ""


@dataclass
class CensusResult:
    census_id: str = CENSUS_ID
    artifacts: dict[str, ArtifactStatus] = field(default_factory=dict)
    oneshot: dict[str, Any] = field(default_factory=dict)
    named: dict[str, Any] = field(default_factory=dict)
    atlas: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    admission: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "census_id": self.census_id,
            "artifacts": {
                key: {"path": row.path, "present": row.present, "detail": row.detail}
                for key, row in self.artifacts.items()
            },
            "oneshot": self.oneshot,
            "named": self.named,
            "atlas": self.atlas,
            "blockers": list(self.blockers),
            "admission": self.admission,
        }


def is_learner_english(text: str | None) -> bool:
    """Same bar as teacher P1 (``promote_teacher_lesson_intake._is_english``)."""
    if not text:
        return False
    normalised = " ".join(text.split()).casefold()
    if "gloss pending" in normalised or "teacher-lesson headword" in normalised:
        return False
    letters = {char.casefold() for char in normalised if char.isalpha()}
    has_latin = any("a" <= char <= "z" for char in letters)
    has_ukrainian = bool(letters & _UKRAINIAN_LETTERS)
    return has_latin and not has_ukrainian


def _unquote_yaml_scalar(value: str) -> str:
    text = value.strip()
    match = _YAML_QUOTED.fullmatch(text)
    if not match:
        return text
    body = match.group("body")
    if match.group("q") == '"':
        return body.replace('\\"', '"').replace("\\\\", "\\")
    return body.replace("''", "'")


def iter_yaml_list_maps(path: Path, *, item_indent: int) -> Iterator[dict[str, str]]:
    """Yield mapping items from a YAML list without loading the whole document.

    Only first-level scalars on each item are captured. Folded/plain
    continuations are joined with a single space. Nested maps are ignored.
    """
    current: dict[str, str] | None = None
    last_key: str | None = None
    field_indent = item_indent + 2
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            start = _ITEM_START.match(line)
            if start and len(start.group("indent")) == item_indent:
                if current is not None:
                    yield current
                current = {}
                last_key = None
                rest = start.group("rest")
                field = _FIELD.match(" " * field_indent + rest)
                if field:
                    last_key = field.group("key")
                    current[last_key] = _unquote_yaml_scalar(field.group("value") or "")
                continue
            if current is None:
                continue
            field = _FIELD.match(line)
            if field and len(field.group("indent")) == field_indent:
                last_key = field.group("key")
                current[last_key] = _unquote_yaml_scalar(field.group("value") or "")
                continue
            if last_key and line.startswith(" " * (field_indent + 2)):
                extra = line.strip()
                if extra:
                    previous = current.get(last_key, "")
                    current[last_key] = f"{previous} {extra}".strip() if previous else extra
    if current is not None:
        yield current


def load_named_inventory_rows(
    paths: Sequence[Path] | None = None,
    *,
    project_root: Path = PROJECT_ROOT,
) -> list[InventoryRow]:
    """Read the small named leftover inventories without importing ``scripts.audit``."""
    rows: list[InventoryRow] = []
    for path in paths or NAMED_INVENTORIES:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"{path}: expected a mapping")
        rel = str(path.relative_to(project_root)) if path.is_relative_to(project_root) else str(path)
        for source in payload.get("sources") or []:
            if not isinstance(source, Mapping):
                continue
            for item in source.get("headwords") or []:
                if not isinstance(item, Mapping):
                    continue
                lemma = str(item.get("lemma") or item.get("headword") or item.get("word") or "").strip()
                if not lemma:
                    continue
                rows.append(
                    InventoryRow(
                        lemma=lemma,
                        gloss=str(item.get("gloss") or ""),
                        source_path=rel,
                        locator=str(item.get("locator") or ""),
                    )
                )
    return rows


def load_named_decisions(paths: Sequence[Path] | None = None) -> list[DecisionRow]:
    rows: list[DecisionRow] = []
    for path in paths or NAMED_DECISIONS:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"{path}: expected a mapping")
        for item in payload.get("decisions") or []:
            if not isinstance(item, Mapping):
                continue
            source = item.get("source_inventory") if isinstance(item.get("source_inventory"), Mapping) else {}
            rows.append(
                DecisionRow(
                    lemma=str(item.get("lemma") or "").strip(),
                    decision=str(item.get("decision") or "").strip(),
                    approved_gloss=str(item.get("approved_gloss") or "").strip(),
                    source_path=str(path),
                    inventory_path=str(source.get("path") or ""),
                )
            )
    return rows


def load_oneshot_inventory_rows(path: Path = ONESHOT_INVENTORY) -> list[InventoryRow]:
    rows: list[InventoryRow] = []
    rel = str(path)
    for item in iter_yaml_list_maps(path, item_indent=2):
        lemma = str(item.get("lemma") or "").strip()
        if not lemma:
            continue
        rows.append(
            InventoryRow(
                lemma=lemma,
                gloss=str(item.get("gloss") or ""),
                source_path=rel,
                locator=str(item.get("locator") or ""),
            )
        )
    return rows


def load_oneshot_decisions(path: Path = ONESHOT_DECISIONS) -> list[DecisionRow]:
    rows: list[DecisionRow] = []
    rel = str(path)
    for item in iter_yaml_list_maps(path, item_indent=0):
        lemma = str(item.get("lemma") or "").strip()
        if not lemma:
            continue
        rows.append(
            DecisionRow(
                lemma=lemma,
                decision=str(item.get("decision") or ""),
                approved_gloss=str(item.get("approved_gloss") or ""),
                source_path=rel,
                inventory_path=str(item.get("path") or ""),
            )
        )
    return rows


def _unescape_json_string(raw: str) -> str:
    return json.loads(f'"{raw}"')


def iter_manifest_lemmas_from_text(text: str) -> Iterator[str]:
    """Yield Atlas *entry* lemmas, not nested synonym/sample lemma fields.

    The published release manifest is pretty-printed with each entry lemma at
    a fixed indent after the top-level ``entries`` array. Compact fixture
    JSON falls back to ``json.loads``.
    """
    start = text.find(_ENTRIES_ARRAY)
    if start != -1:
        for match in _ENTRY_LEMMA.finditer(text, start):
            yield _unescape_json_string(match.group(1))
        return
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        return
    for entry in payload.get("entries") or []:
        if isinstance(entry, Mapping) and entry.get("lemma"):
            yield str(entry["lemma"])


def load_atlas_lemma_keys(
    *,
    manifest_path: Path | None = None,
    pointer_path: Path = DEFAULT_POINTER,
    allow_download: bool = False,
) -> dict[str, Any]:
    """Return Atlas lemma keys from a local manifest or (optionally) the pointer asset."""
    report: dict[str, Any] = {
        "loaded": False,
        "source": None,
        "entry_lemmas": 0,
        "unique_keys": 0,
        "pointer": _display_path(pointer_path) if pointer_path.is_file() else None,
        "error": None,
    }
    keys: set[str] = set()
    if manifest_path and manifest_path.is_file():
        text = manifest_path.read_text(encoding="utf-8")
        lemmas = list(iter_manifest_lemmas_from_text(text))
        keys = {_lemma_key(lemma) for lemma in lemmas if lemma}
        report.update(
            {
                "loaded": True,
                "source": str(manifest_path),
                "entry_lemmas": len(lemmas),
                "unique_keys": len(keys),
            }
        )
        report["keys"] = keys
        return report
    default_manifest = DEFAULT_MANIFEST
    if default_manifest.is_file():
        text = default_manifest.read_text(encoding="utf-8")
        lemmas = list(iter_manifest_lemmas_from_text(text))
        keys = {_lemma_key(lemma) for lemma in lemmas if lemma}
        report.update(
            {
                "loaded": True,
                "source": str(default_manifest),
                "entry_lemmas": len(lemmas),
                "unique_keys": len(keys),
            }
        )
        report["keys"] = keys
        return report
    if allow_download and pointer_path.is_file():
        try:
            from scripts.lexicon import manifest_io

            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            gz_bytes = manifest_io._download(pointer, attempt=0)
            import gzip
            import hashlib

            gz_sha = hashlib.sha256(gz_bytes).hexdigest()
            if gz_sha != pointer.get("gz_sha256"):
                raise ValueError(f"gz sha256 mismatch: expected {pointer.get('gz_sha256')}, got {gz_sha}")
            json_bytes = gzip.decompress(gz_bytes)
            json_sha = hashlib.sha256(json_bytes).hexdigest()
            if json_sha != pointer.get("json_sha256"):
                raise ValueError(
                    f"json sha256 mismatch: expected {pointer.get('json_sha256')}, got {json_sha}"
                )
            lemmas = list(iter_manifest_lemmas_from_text(json_bytes.decode("utf-8")))
            keys = {_lemma_key(lemma) for lemma in lemmas if lemma}
            report.update(
                {
                    "loaded": True,
                    "source": pointer.get("asset_url"),
                    "entry_lemmas": len(lemmas),
                    "unique_keys": len(keys),
                    "json_sha256": json_sha,
                    "gz_sha256": gz_sha,
                }
            )
            report["keys"] = keys
            return report
        except Exception as exc:  # noqa: BLE001 — census must record the exact blocker
            report["error"] = f"{type(exc).__name__}: {exc}"
            report["keys"] = keys
            return report
    report["error"] = "atlas catalog unavailable (no hydrated manifest; download disabled or failed)"
    report["keys"] = keys
    return report


def _display_path(path: Path, project_root: Path = PROJECT_ROOT) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def _artifact(path: Path, *, required_name: str, project_root: Path = PROJECT_ROOT) -> ArtifactStatus:
    present = path.is_file()
    return ArtifactStatus(
        path=_display_path(path, project_root),
        present=present,
        detail="" if present else f"missing {required_name}",
    )


def _classify_rows(
    *,
    inventory_rows: Sequence[InventoryRow],
    decision_rows: Sequence[DecisionRow],
    atlas_keys: set[str] | None,
) -> dict[str, Any]:
    inventory_keys = {_lemma_key(row.lemma): row for row in inventory_rows if row.lemma}
    approved = [row for row in decision_rows if row.decision == "approve_for_publish" and row.lemma]
    approved_keys = {_lemma_key(row.lemma): row for row in approved}
    english_approved = [
        row for row in approved if is_learner_english(row.approved_gloss)
    ]
    english_inventory = [row for row in inventory_rows if is_learner_english(row.gloss)]
    missing: list[str] = []
    present: list[str] = []
    unknown_atlas = atlas_keys is None
    if atlas_keys is not None:
        for key, row in approved_keys.items():
            if key in atlas_keys:
                present.append(row.lemma)
            else:
                missing.append(row.lemma)
    teacher_p1 = []
    for row in english_approved:
        key = _lemma_key(row.lemma)
        in_atlas = None if unknown_atlas else key in atlas_keys
        teacher_p1.append(
            {
                "lemma": row.lemma,
                "approved_gloss": row.approved_gloss,
                "in_atlas": in_atlas,
                "inventory_path": row.inventory_path,
            }
        )
    return {
        "inventory_rows": len(inventory_rows),
        "inventory_unique_lemmas": len(inventory_keys),
        "approved_decisions": len(approved),
        "approved_unique_lemmas": len(approved_keys),
        "inventory_english_gloss_rows": len(english_inventory),
        "approved_english_gloss_rows": len(english_approved),
        "already_in_atlas": None if unknown_atlas else len(present),
        "missing_from_atlas": None if unknown_atlas else len(missing),
        "missing_lemmas": [] if unknown_atlas else sorted(missing),
        "teacher_p1_eligible": teacher_p1,
        "teacher_p1_eligible_count": len(teacher_p1),
        "teacher_p1_missing_from_atlas": (
            None
            if unknown_atlas
            else sorted(item["lemma"] for item in teacher_p1 if item["in_atlas"] is False)
        ),
    }


def build_census(
    *,
    project_root: Path = PROJECT_ROOT,
    oneshot_inventory: Path | None = None,
    oneshot_decisions: Path | None = None,
    named_inventories: Sequence[Path] | None = None,
    named_decisions: Sequence[Path] | None = None,
    manifest_path: Path | None = None,
    pointer_path: Path | None = None,
    vesum_path: Path | None = None,
    sources_path: Path | None = None,
    allow_download: bool = False,
) -> CensusResult:
    oneshot_inventory = oneshot_inventory or (project_root / ONESHOT_INVENTORY.relative_to(PROJECT_ROOT))
    oneshot_decisions = oneshot_decisions or (project_root / ONESHOT_DECISIONS.relative_to(PROJECT_ROOT))
    named_inventories = named_inventories or tuple(
        project_root / path.relative_to(PROJECT_ROOT) for path in NAMED_INVENTORIES
    )
    named_decisions = named_decisions or tuple(
        project_root / path.relative_to(PROJECT_ROOT) for path in NAMED_DECISIONS
    )
    pointer_path = pointer_path or (project_root / DEFAULT_POINTER.relative_to(PROJECT_ROOT))
    vesum_path = vesum_path or (project_root / DEFAULT_VESUM.relative_to(PROJECT_ROOT))
    sources_path = sources_path or (project_root / DEFAULT_SOURCES_DB.relative_to(PROJECT_ROOT))

    result = CensusResult()
    result.artifacts["oneshot_inventory"] = _artifact(
        oneshot_inventory, required_name="oneshot textbook inventory", project_root=project_root
    )
    result.artifacts["oneshot_decisions"] = _artifact(
        oneshot_decisions, required_name="oneshot textbook decisions", project_root=project_root
    )
    for index, path in enumerate(named_inventories):
        result.artifacts[f"named_inventory_{index}"] = _artifact(
            path, required_name="named textbook inventory", project_root=project_root
        )
    for index, path in enumerate(named_decisions):
        result.artifacts[f"named_decisions_{index}"] = _artifact(
            path, required_name="named textbook decisions", project_root=project_root
        )
    result.artifacts["vesum_db"] = _artifact(
        vesum_path, required_name="data/vesum.db", project_root=project_root
    )
    result.artifacts["sources_db"] = _artifact(
        sources_path, required_name="data/sources.db", project_root=project_root
    )
    result.artifacts["pointer"] = _artifact(
        pointer_path, required_name="lexicon-manifest.pointer.json", project_root=project_root
    )

    if not result.artifacts["vesum_db"].present:
        result.blockers.append("data/vesum.db")
    if not result.artifacts["sources_db"].present:
        result.blockers.append("data/sources.db")

    atlas = load_atlas_lemma_keys(
        manifest_path=manifest_path,
        pointer_path=pointer_path,
        allow_download=allow_download,
    )
    atlas_keys: set[str] | None = atlas.get("keys") if atlas.get("loaded") else None
    result.atlas = {key: value for key, value in atlas.items() if key != "keys"}
    if not atlas.get("loaded"):
        result.blockers.append("atlas_catalog")
        if atlas.get("error"):
            result.atlas["error"] = atlas["error"]

    if result.artifacts["oneshot_inventory"].present and result.artifacts["oneshot_decisions"].present:
        result.oneshot = _classify_rows(
            inventory_rows=load_oneshot_inventory_rows(oneshot_inventory),
            decision_rows=load_oneshot_decisions(oneshot_decisions),
            atlas_keys=atlas_keys,
        )
    else:
        result.oneshot = {"error": "oneshot inventory or decisions missing"}

    missing_named = [
        result.artifacts[key].path
        for key in result.artifacts
        if key.startswith("named_") and not result.artifacts[key].present
    ]
    if missing_named:
        result.named = {"error": "named leftover files missing", "missing": missing_named}
    else:
        result.named = _classify_rows(
            inventory_rows=load_named_inventory_rows(named_inventories, project_root=project_root),
            decision_rows=load_named_decisions(named_decisions),
            atlas_keys=atlas_keys,
        )

    named_missing = list(result.named.get("teacher_p1_missing_from_atlas") or [])
    oneshot_english_missing = [
        item["lemma"]
        for item in result.oneshot.get("teacher_p1_eligible") or []
        if item.get("in_atlas") is False
    ]
    admit_named = named_missing
    result.admission = {
        "policy": (
            "Admit only leftovers already approved the same way as teacher P1: "
            "approve_for_publish + learner-English gloss, lemma taken verbatim "
            "from a committed inventory. Refuse invented lemmas, oneshot SUM-11 "
            "dumps, and any write when vesum.db or sources.db is missing."
        ),
        "named_teacher_p1_missing": admit_named,
        "oneshot_teacher_p1_missing": oneshot_english_missing,
        "admitted_this_run": [],
        "refused": True,
        "refuse_reason": None,
    }
    reasons: list[str] = []
    if result.blockers:
        reasons.append("BLOCKED: missing " + ", ".join(result.blockers))
    if atlas.get("loaded") and not admit_named:
        reasons.append(
            "no named teacher-P1 leftovers are missing from the Atlas catalog"
        )
    if reasons:
        result.admission["refuse_reason"] = "; ".join(reasons)
    else:
        result.admission["refused"] = False
        result.admission["refuse_reason"] = None
    return result


def render_report(census: CensusResult) -> str:
    payload = census.to_json()
    oneshot = payload["oneshot"]
    named = payload["named"]
    atlas = payload["atlas"]
    admission = payload["admission"]
    lines = [
        "# Textbook leftover residual census (#6371)",
        "",
        f"Census id: `{payload['census_id']}`",
        "",
        "Source of truth is the committed oneshot textbook inventory plus the",
        "in-repo Bolshakova/Vashulenko leftover lists and their already-approved",
        "ledgers. This report does not invent lemmas, dump corpus, or commit PDFs.",
        "",
        "## Artifacts",
        "",
        "| artifact | present | path |",
        "| --- | --- | --- |",
    ]
    for key, row in payload["artifacts"].items():
        flag = "yes" if row["present"] else "**NO**"
        lines.append(f"| `{key}` | {flag} | `{row['path']}` |")
    lines.extend(
        [
            "",
            "## Blockers",
            "",
        ]
    )
    if payload["blockers"]:
        for item in payload["blockers"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Atlas catalog",
            "",
            f"- loaded: `{atlas.get('loaded')}`",
            f"- source: `{atlas.get('source')}`",
            f"- unique keys: `{atlas.get('unique_keys')}`",
            f"- entry lemmas: `{atlas.get('entry_lemmas')}`",
            f"- json_sha256: `{atlas.get('json_sha256')}`",
        ]
    )
    if atlas.get("error"):
        lines.append(f"- error: `{atlas['error']}`")
    lines.extend(
        [
            "",
            "## Oneshot bulk (`textbook-jsonl-curated-2026-07-19`)",
            "",
            f"- inventory rows: `{oneshot.get('inventory_rows')}`",
            f"- approved decisions: `{oneshot.get('approved_decisions')}`",
            f"- approved unique lemmas: `{oneshot.get('approved_unique_lemmas')}`",
            f"- approved English-gloss rows (teacher P1 bar): `{oneshot.get('approved_english_gloss_rows')}`",
            f"- already in Atlas: `{oneshot.get('already_in_atlas')}`",
            f"- missing from Atlas: `{oneshot.get('missing_from_atlas')}`",
            "",
            "Oneshot approved glosses are SUM-11 Ukrainian dumps. They are **not**",
            "teacher-P1 eligible and must not be admitted from this census.",
            "",
        ]
    )
    oneshot_missing = oneshot.get("missing_lemmas") or []
    if oneshot_missing:
        lines.append("Sample of oneshot leftovers still missing (first 10, lemma-only):")
        lines.append("")
        for lemma in oneshot_missing[:10]:
            lines.append(f"- `{lemma}`")
        lines.append("")
    lines.extend(
        [
            "## Named leftover inventories (Bolshakova + Vashulenko)",
            "",
            f"- inventory rows: `{named.get('inventory_rows')}`",
            f"- approved decisions: `{named.get('approved_decisions')}`",
            f"- approved unique lemmas: `{named.get('approved_unique_lemmas')}`",
            f"- approved English-gloss rows (teacher P1 bar): `{named.get('approved_english_gloss_rows')}`",
            f"- already in Atlas: `{named.get('already_in_atlas')}`",
            f"- missing from Atlas: `{named.get('missing_from_atlas')}`",
            "",
            "### Named teacher-P1 leftovers still missing",
            "",
        ]
    )
    missing_named = admission.get("named_teacher_p1_missing") or []
    if missing_named:
        for lemma in missing_named:
            lines.append(f"- `{lemma}`")
    elif atlas.get("loaded"):
        lines.append("- none — every unique named leftover with an English learner gloss is already in Atlas")
    else:
        lines.append("- unknown — Atlas catalog was not loaded")
    lines.extend(
        [
            "",
            "## Admission",
            "",
            admission.get("policy", ""),
            "",
            f"- refused: `{admission.get('refused')}`",
            f"- reason: {admission.get('refuse_reason')}",
            f"- admitted this run: `{admission.get('admitted_this_run')}`",
            "",
            "Issue #6371 stays open. Practice/deck publish and pointer flip are",
            "out of scope until the blockers above are cleared on a host that",
            "has `data/vesum.db` and `data/sources.db`.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def refuse_invented_lemmas(lemmas: Iterable[str], allowed: set[str]) -> None:
    extra = sorted({lemma for lemma in lemmas if _lemma_key(lemma) not in allowed})
    if extra:
        raise ValueError(f"refusing invented lemmas not in committed leftover lists: {extra}")


def admission_allowed_keys(census: CensusResult) -> set[str]:
    """Lemma keys that already have teacher-P1 approval on a named leftover list."""
    allowed: set[str] = set()
    for item in census.named.get("teacher_p1_eligible") or []:
        lemma = str(item.get("lemma") or "")
        if lemma:
            allowed.add(_lemma_key(lemma))
    return allowed


def write_report(
    census: CensusResult,
    *,
    markdown_path: Path = DEFAULT_REPORT_MD,
    json_path: Path = DEFAULT_REPORT_JSON,
) -> tuple[Path, Path]:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_report(census), encoding="utf-8")
    json_path.write_text(
        json.dumps(census.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return markdown_path, json_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="Print the markdown census to stdout")
    parser.add_argument("--write-report", action="store_true", help="Write the committed oneshot report files")
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Hydrate lemma keys from the committed release pointer when the local manifest is absent",
    )
    parser.add_argument("--manifest", type=Path, default=None, help="Optional local Atlas manifest")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    census = build_census(manifest_path=args.manifest, allow_download=args.allow_download)
    if args.write_report:
        write_report(census)
    rendered = render_report(census)
    if args.report:
        sys.stdout.write(rendered)
    if args.json_out:
        args.json_out.write_text(
            json.dumps(census.to_json(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if census.blockers:
        print("BLOCKED: missing " + ", ".join(census.blockers), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
