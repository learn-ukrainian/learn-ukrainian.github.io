"""Read-only word-card lookup behind the Sources MCP ``word_card`` tool (#11084).

Cards ship versioned and improve over versions, so the lookup serves the
current card of a word whether or not it is certified. The status is never
taken from an assembly card: each assembly lookup replays the exact-artifact certification
boundary (``load_certified_card_for_export``) against the live review ledger.
A card that fails it is returned as ``candidate``: each value is a cited
source assertion awaiting review, not an accepted fact (#8977). A link endpoint's evidence enters a certified card
only when that endpoint is itself certified, with its card version bound;
anything else is a separate candidate relation or a withheld gap.

The card store can be a host-only assembly build directory (``cards/*.json`` plus
the optional ``ledger.json`` and ``build-manifest.json`` written by
``scripts.atlas.word_card_assembly``), named by ``LU_WORD_CARDS_DIR``. Nothing
here writes, and no host path is echoed in a result. Every target is read only
after its symlinks are resolved and it is shown to be local: the root, the
``cards/`` directory, the ledger and the manifest by the network-locality check,
each card file by sitting directly in the checked ``cards/`` directory on its
filesystem, re-checked on the opened descriptor.

A pinned release directory instead contains ``manifest.json`` and
``word-cards.jsonl``. Its detached assertions remain unaccepted candidates;
release integrity cannot supply the original artifact's certification authority.
The release reader holds descriptors through response preparation and refuses
the whole release if a pin, asset, directory or layout changes during its checks.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Mapping
from contextlib import ExitStack
from dataclasses import dataclass
from decimal import Decimal, DecimalException
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.validators import extend

from scripts.common.jsonl import jsonl_lines
from scripts.common.nofollow_walk import ComponentOpenError, open_directory_component
from scripts.deploy.prepare_word_card_preview import CARD_SCHEMA, DEFAULT_PIN, PreviewError, check_release

ENV_WORD_CARDS_DIR = "LU_WORD_CARDS_DIR"
RESULT_SCHEMA = "word-card-lookup.v1"
APPROVALS = ("site", "dataset")
MAX_QUERY_CHARS = 100
SHAPE_REASON = "word must be Cyrillic letters with apostrophes, hyphens, spaces or . , ! ? …"

# Per-facet Sources tools, in the order the source-of-truth rules consult them.
PER_FACET_TOOLS: dict[str, list[str]] = {
    "form_and_paradigm": ["verify_word", "verify_lemma", "inspect_lemma", "query_ulif"],
    "spelling": ["query_pravopys"],
    "stress": ["verify_stress", "query_sum20"],
    "meaning": ["query_sum20", "query_ulif", "search_slovnyk_me", "search_grinchenko_1907"],
    "cefr": ["query_cefr_level"],
    "russianism_and_calque": [
        "check_russian_shadow",
        "search_style_guide",
        "search_text (source_file='antonenko-davydovych-yak-my-hovorymo')",
        "query_r2u",
        "search_ua_gec_errors",
    ],
    "heritage": ["search_heritage", "search_grinchenko_1907"],
    "etymology": ["search_esum"],
    "relations_and_phraseology": [
        "query_ulif_synonyms",
        "query_ulif_antonyms",
        "query_ulif_phraseology",
        "search_synonyms",
        "search_idioms",
    ],
    "examples_and_usage": ["search_literary", "query_grac"],
}
CANDIDATE_NOTICE = (
    "CANDIDATE card: not certified. Every value is a cited source assertion awaiting review, "
    "not an accepted fact. Confirm a value with the per-facet tools before relying on it."
)
CERTIFIED_NOTICE = "CERTIFIED card: this exact card version passed the exact-artifact certification boundary."
CANDIDATE_LINK_NOTICE = (
    "CANDIDATE relation: it rests on evidence from a link endpoint card that is not certified. "
    "It is not part of this certified card's accepted values; each citation names its endpoint card's version."
)
SOVIET_CONTEXT_NOTICE = (
    "Soviet-occupation СУМ-11 text, shown as soviet_colonization_context only; "
    "never a source of modern meaning, stress or validity."
)
_SOVIET_DICTIONARY_ID = "sum11"
_FIELD_STATE_GAPS = {
    "unverified": "unverified: no assertion with an evidenced mapping",
    "conflict": "conflict: sources disagree and no value is selected",
    "suppressed": "suppressed: every assertion was withdrawn",
}
_STRESS_MARKS = frozenset({"\N{COMBINING ACUTE ACCENT}", "\N{COMBINING GRAVE ACCENT}"})
_QUERY_SHAPE = re.compile(r"[\u0400-\u04ff'\- ,.!?\u2026]+")
_HAS_LETTER = re.compile(r"[\u0400-\u04ff]")


_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


class StoreUnavailable(Exception):
    """A card store target failed validation or could not be read. ``reason`` is path-free."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class _OffStore(OSError):
    """A card file whose resolved target is not in the checked ``cards/`` directory or its filesystem."""


@dataclass(frozen=True)
class LocalTarget:
    """A store target with its symlinks resolved, shown local, and the filesystem it was shown on."""

    path: Path
    device: int


@dataclass(frozen=True)
class CardStore:
    """A validated, read-only card build directory."""

    cards: LocalTarget
    ledger: LocalTarget | None
    manifest: LocalTarget | None


@dataclass(frozen=True)
class DatasetStore:
    """Release intent at a checked root; never fall back to assembly after refusal."""

    configured: Path
    root: LocalTarget
    info: os.stat_result


@dataclass(frozen=True)
class _ReleaseDirectory:
    configured: Path
    target: LocalTarget
    descriptor: int
    info: os.stat_result


@dataclass(frozen=True)
class _ReleaseLeaf:
    parent: int
    name: str
    descriptor: int
    info: os.stat_result


@dataclass(frozen=True)
class ReleaseSnapshot:
    """Detached validated rows, with descriptors held until the response's final check."""

    manifest: dict
    rows: list[dict]
    pin: dict
    directories: tuple[_ReleaseDirectory, ...]
    leaves: tuple[_ReleaseLeaf, ...]
    handles: ExitStack


@dataclass(frozen=True)
class Endpoint:
    """A link endpoint's card and the projections its own exact-artifact certification grants."""

    card: dict
    granted: tuple[str, ...]


def _clean(text: str) -> str:
    """NFC without stress marks, one apostrophe spelling and single spaces."""
    decomposed = unicodedata.normalize("NFD", text)
    text = unicodedata.normalize("NFC", "".join(ch for ch in decomposed if ch not in _STRESS_MARKS))
    return " ".join(
        text.translate(str.maketrans("\N{RIGHT SINGLE QUOTATION MARK}\N{MODIFIER LETTER APOSTROPHE}", "''")).split()
    )


def _spelling_key(spelling: Any) -> str | None:
    """Index key of a stored card spelling; stored spellings are not held to the query shape."""
    return _fold(_clean(spelling)) if isinstance(spelling, str) and spelling.strip() else None


def normalize_query(word: Any) -> tuple[str | None, str | None]:
    """Return ``(normalized, None)`` or ``(None, reason)`` for an unusable query.

    Stress marks are stripped, apostrophes unified and whitespace collapsed, as
    card spellings are stored (NFC, stress-free).
    """
    if not isinstance(word, str):
        return None, "word must be a string"
    text = _clean(word)
    if not text:
        return None, "word is empty"
    if len(text) > MAX_QUERY_CHARS:
        return None, f"word is longer than {MAX_QUERY_CHARS} characters"
    if not _QUERY_SHAPE.fullmatch(text) or not _HAS_LETTER.search(text):
        return None, SHAPE_REASON
    return text, None


def _local_target(path: Path, *, directory: bool) -> LocalTarget:
    """Resolve ``path`` through its symlinks and require a local directory (or regular file) there."""
    from scripts.storage.topology import is_network_filesystem_path

    try:
        resolved = path.resolve(strict=True)
        info = resolved.stat()
        if directory and not stat.S_ISDIR(info.st_mode):
            raise StoreUnavailable("not_a_directory")
        if not directory and not stat.S_ISREG(info.st_mode):
            raise StoreUnavailable("store_unavailable")
        if is_network_filesystem_path(resolved):
            raise StoreUnavailable("locality_network")
    except FileNotFoundError as exc:
        raise StoreUnavailable("store_missing") from exc
    except (OSError, RuntimeError) as exc:
        raise StoreUnavailable("store_unavailable") from exc
    return LocalTarget(resolved, info.st_dev)


def resolve_card_store(env: Mapping[str, str] | None = None) -> CardStore | DatasetStore | str:
    """Resolve the configured card build, or return a path-free refusal reason."""
    raw = (os.environ if env is None else env).get(ENV_WORD_CARDS_DIR)
    if raw is None:
        return "not_configured"
    if not raw.strip():
        return "empty_override"
    if raw.lower().startswith("file:"):
        return "uri_override"
    path = Path(raw)
    if not path.is_absolute():
        return "relative_override"
    try:
        root = _local_target(path, directory=True)
        if any(os.path.lexists(root.path / name) for name in ("manifest.json", "word-cards.jsonl")):
            _release_layout(root.path)
            return DatasetStore(path, root, root.path.stat())
        # A child that exists as an entry, a dangling symlink included, is checked; only absence skips it.
        child = {name: root.path / name for name in ("cards", "ledger.json", "build-manifest.json")}
        present = {name: os.path.lexists(target) for name, target in child.items()}
        cards = _local_target(child["cards"], directory=True) if present["cards"] else root
        ledger = _local_target(child["ledger.json"], directory=False) if present["ledger.json"] else None
        manifest = (
            _local_target(child["build-manifest.json"], directory=False) if present["build-manifest.json"] else None
        )
    except StoreUnavailable as exc:
        return exc.reason
    except (OSError, RuntimeError):
        return "store_unavailable"
    return CardStore(cards, ledger, manifest)


def _fold(text: str) -> str:
    return text.casefold()


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _read_json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def _read_checked(target: LocalTarget) -> Any:
    """JSON of ``target``, opened without following a symlink and only on the filesystem it was checked on."""
    descriptor = os.open(target.path, os.O_RDONLY | _O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if info.st_dev != target.device or not stat.S_ISREG(info.st_mode):
            raise _OffStore("store file left its checked filesystem")
        return json.loads(handle.read())


def _read_card(cards: LocalTarget, name: str) -> Any:
    """A card file, read only when its resolved target sits directly in the checked ``cards/`` directory."""
    resolved = (cards.path / name).resolve(strict=True)
    if resolved.parent != cards.path:
        raise _OffStore("card file resolves outside the card directory")
    return _read_checked(LocalTarget(resolved, cards.device))


def _spelling_index(cards: LocalTarget, names: list[str]) -> tuple[dict[str, tuple[str, ...]], int, int]:
    """Rebuild from current card contents; directory metadata misses in-place rewrites."""
    index: dict[str, list[str]] = defaultdict(list)
    unreadable = off_store = 0
    for name in names:
        try:
            spelling = _dict(_dict(_read_card(cards, name)).get("key_at_creation")).get("spelling")
        except _OffStore:
            off_store += 1
            continue
        except (OSError, ValueError):
            unreadable += 1
            continue
        key = _spelling_key(spelling)
        if key is None:
            unreadable += 1
            continue
        index[key].append(name)
    return {key: tuple(names) for key, names in index.items()}, unreadable, off_store


def _card_names(cards: LocalTarget) -> list[str]:
    with os.scandir(cards.path) as entries:
        return sorted(entry.name for entry in entries if entry.name.endswith(".json"))


def _store_index(store: CardStore) -> tuple[dict[str, tuple[str, ...]], int, int, int]:
    """The spelling index with its unreadable and off-store counts. A directory read failure raises OSError."""
    names = _card_names(store.cards)
    index, unreadable, off_store = _spelling_index(store.cards, names)
    return index, unreadable, off_store, len(names)


@lru_cache(maxsize=2)
def _ledger(target: LocalTarget, _mtime_ns: int, _size: int) -> dict:
    return _dict(_dict(_read_checked(target)).get("cards"))


def _ledger_cards(store: CardStore) -> dict | None:
    """The build ledger's card rows; ``None`` when the store has a ledger that cannot be read."""
    if store.ledger is None:
        return {}
    try:
        info = store.ledger.path.stat()
        return _ledger(store.ledger, info.st_mtime_ns, info.st_size)
    except (OSError, ValueError):
        return None


def _store_build_id(store: CardStore) -> str | None:
    if store.manifest is None:
        return None
    try:
        build_id = _dict(_read_checked(store.manifest)).get("build_id")
    except (OSError, ValueError):
        return None
    return build_id if isinstance(build_id, str) else None


def _vesum_lookup(word: str) -> list[dict]:
    from scripts.verification.vesum import verify_word

    matches = verify_word(word)
    if not matches and word != word.lower():
        matches = verify_word(word.lower())
    return matches


def _vesum(word: str, lookup: Callable[[str], list[dict]]) -> dict:
    try:
        matches = lookup(word)
    except Exception as exc:  # An unreachable VESUM is reported, never guessed.
        return {"available": False, "reason": type(exc).__name__}
    lemmas = sorted({m["lemma"] for m in matches if isinstance(m, dict) and isinstance(m.get("lemma"), str)})
    return {"available": True, "attested": bool(matches), "lemmas": lemmas}


def _certification(card: dict) -> tuple[list[str], dict[str, str]]:
    """Replay the export boundary for each projection; the card's own labels never count."""
    from scripts.atlas import word_card_certification as cert

    granted: list[str] = []
    refusals: dict[str, str] = {}
    for approval in APPROVALS:
        try:
            cert.load_certified_card_for_export(card, required_approval=approval)
        except cert.UncertifiedCardRefusal as exc:
            refusals[approval] = str(exc)
        else:
            granted.append(approval)
    return granted, refusals


def _citation(evidence_id: str, assertion: dict | None) -> dict | None:
    """The source a retained assertion cites; ``None`` when it is missing or a tombstone with no source."""
    assertion = _dict(assertion)
    if not assertion.get("source_id") or not assertion.get("locator"):
        return None
    producer = _dict(assertion.get("producer"))
    citation = {
        "evidence_id": evidence_id,
        "source_id": assertion.get("source_id"),
        "snapshot_id": assertion.get("snapshot_id"),
        "locator": assertion.get("locator"),
        "source_record_id": assertion.get("source_record_id"),
        "source_record_key": assertion.get("source_record_key"),
        "value": assertion.get("value"),
        "assertion_status": assertion.get("status"),
        "review_status": _dict(assertion.get("review")).get("status"),
        "extraction_version": assertion.get("extraction_version"),
        "extraction_confidence": assertion.get("extraction_confidence"),
        "producer": {k: producer[k] for k in ("kind", "name", "version") if k in producer} or None,
        "mapping": assertion.get("mapping"),
        "tier": assertion.get("tier"),
    }
    if assertion.get("source_id") == _SOVIET_DICTIONARY_ID:
        citation["role"] = "soviet_colonization_context"
        citation["notice"] = SOVIET_CONTEXT_NOTICE
    return {key: value for key, value in citation.items() if value is not None}


def _uncited(evidence_id: str) -> str:
    return f"uncited_evidence {evidence_id}: no retained source assertion on this card"


def _citations(ids: list[str], cite: Callable[[str], dict | None]) -> tuple[list[dict], list[str]]:
    """Citations for ``ids`` and the ids that cite no source."""
    citations, uncited = [], []
    for evidence_id in ids:
        citation = cite(evidence_id)
        if citation is None:
            uncited.append(evidence_id)
        else:
            citations.append(citation)
    return citations, uncited


def _field_gaps(resolution: dict) -> list[str]:
    gaps = []
    state = resolution.get("state")
    if state in _FIELD_STATE_GAPS:
        gaps.append(_FIELD_STATE_GAPS[state])
    elif state == "single-source":
        gaps.append("single_source: one independence group, not corroborated")
    if resolution.get("mapping_evidenced") is False and state not in _FIELD_STATE_GAPS:
        gaps.append("mapping_not_evidenced: the source row is not tied to this word by evidence")
    for item in _list(resolution.get("non_voting")):
        gaps.append(f"non_voting {_dict(item).get('assertion_id')}: {_dict(item).get('reason')}")
    for key, proposition in sorted(_dict(resolution.get("propositions")).items()):
        sub_state = _dict(proposition).get("state")
        if sub_state in _FIELD_STATE_GAPS:
            gaps.append(f"{key}: {_FIELD_STATE_GAPS[sub_state]}")
    return gaps


def _project_field(resolution: Any, cite: Callable[[str], dict | None], accepted: bool) -> dict:
    """A field's values, each with its citations. A value no retained assertion cites is a gap, never a value."""
    resolution = _dict(resolution)
    selected = resolution.get("selected")
    selected_ids = set(selected) if isinstance(selected, list) else {selected} if isinstance(selected, str) else set()
    values, uncitable, uncited = [], [], []
    for value in _list(resolution.get("values")):
        value = _dict(value)
        ids = [i for i in _list(value.get("assertion_ids")) if isinstance(i, str)]
        citations, missing = _citations(ids, cite)
        uncited.extend(missing)
        if not citations:
            uncitable.append(
                "uncitable_value withheld: no retained source assertion cites it"
                + (f" (evidence ids {', '.join(ids)})" if ids else " (no evidence ids)")
            )
            continue
        projected = {
            "value": value.get("value_norm"),
            "selected": bool(selected_ids.intersection(ids)),
            "evidence_ids": [citation["evidence_id"] for citation in citations],
            "independence_groups": _list(value.get("independence_groups")),
            "citations": citations,
        }
        if value.get("declared_set"):
            projected["declared_set"] = True
        values.append(projected)
    field = {"state": resolution.get("state"), "accepted": accepted, "values": values}
    non_voting = []
    for item in _list(resolution.get("non_voting")):
        evidence_id = str(_dict(item).get("assertion_id"))
        entry = {"evidence_id": evidence_id, "reason": _dict(item).get("reason")}
        citation = cite(evidence_id)
        if citation is None:
            uncited.append(evidence_id)
        else:
            entry["citation"] = citation
        non_voting.append(entry)
    if non_voting:
        field["non_voting"] = non_voting
    gaps = _field_gaps(resolution) + uncitable + [_uncited(i) for i in dict.fromkeys(uncited)]
    if gaps:
        field["gaps"] = gaps
    return field


@lru_cache(maxsize=1)
def _schema_field_names() -> tuple[tuple[str, ...], tuple[str, ...]]:
    from scripts.atlas.word_card_certification import SCHEMA_PATH

    definitions = _read_json(SCHEMA_PATH)["$defs"]
    return tuple(definitions["card_field_name"]["enum"]), tuple(definitions["sense_field_name"]["enum"])


def _card_gaps(card: dict, ledger_entry: dict) -> dict[str, dict]:
    """Known gaps per field: the build ledger's dispositions, else absence from the card."""
    card_fields, sense_fields = _schema_field_names()
    present = set(_dict(card.get("fields")))
    for sense in _list(card.get("senses")):
        present.update(_dict(_dict(sense).get("fields")))
    ledger_fields = _dict(ledger_entry.get("fields"))
    gaps: dict[str, dict] = {}
    for name in (*card_fields, *sense_fields):
        row = _dict(ledger_fields.get(name))
        disposition = row.get("disposition")
        if disposition == "not_applicable":
            continue
        if disposition not in (None, "asserted"):
            gaps[name] = {k: v for k, v in {"disposition": disposition, "reason": row.get("reason")}.items() if v}
        elif name not in present:
            gaps[name] = {"disposition": "absent_from_card"}
    identity = _dict(card.get("identity"))
    if _dict(card.get("quality")).get("identity_confidence") == "unresolved" or identity.get("method") == "unresolved":
        gaps["identity"] = {"disposition": "unresolved", "notes": _list(identity.get("notes"))}
    unsplit = [_dict(s).get("sense_id") for s in _list(card.get("senses")) if _dict(s).get("state") == "unsplit"]
    if unsplit:
        gaps["senses"] = {"disposition": "unsplit", "sense_ids": unsplit}
    return gaps


def _endpoint_citation(
    evidence_id: str,
    endpoint_ids: list,
    card_id: Any,
    endpoint_card: Callable[[str], Endpoint | None],
    admit: Callable[[Endpoint], bool],
) -> dict | None:
    """The citation an admitted link endpoint states for ``evidence_id``, bound to that endpoint's card version."""
    for other_id in endpoint_ids:
        if other_id == card_id or not isinstance(other_id, str):
            continue
        endpoint = endpoint_card(other_id)
        if endpoint is None or not admit(endpoint):
            continue
        assertion = next(
            (a for a in _list(endpoint.card.get("assertions")) if _dict(a).get("assertion_id") == evidence_id), None
        )
        citation = _citation(evidence_id, assertion) if assertion is not None else None
        if citation is not None:
            citation["card_id"] = other_id
            citation["card_version"] = _dict(endpoint.card.get("build")).get("card_version")
            citation["card_status"] = "certified" if endpoint.granted else "candidate"
            citation["card_certified_for"] = list(endpoint.granted)
            return citation
    return None


def _project_link(
    link: Any, card_id: Any, cite: Callable[[str], dict | None], scope: str = "its link endpoints"
) -> tuple[dict, list[str]]:
    """A link with its citations, and the evidence ids that cite no source on this card or ``scope``."""
    link = _dict(link)
    ids = [i for i in _list(link.get("assertion_ids")) if isinstance(i, str)]
    citations, uncited = _citations(ids, cite)
    endpoints = [_dict(e) for e in _list(link.get("endpoints"))]
    projected = {
        "link_id": link.get("link_id"),
        "type": link.get("type"),
        "state": link.get("state"),
        "basis": link.get("basis"),
        "derived_by": link.get("derived_by"),
        "note": link.get("note"),
        "card_ids": [e.get("id") for e in endpoints if e.get("id") != card_id],
        "endpoints": [{k: e[k] for k in ("id", "role", "sense_id") if k in e} for e in endpoints],
        "evidence_ids": [citation["evidence_id"] for citation in citations],
        "citations": citations,
    }
    if uncited:
        projected["gaps"] = [_uncited(i).replace("on this card", f"on this card or {scope}") for i in uncited]
    return {k: v for k, v in projected.items() if v is not None}, uncited


def _project_links(
    card: dict, granted: list[str], cite: Callable[[str], dict | None], endpoint_card: Callable[[str], Endpoint | None]
) -> tuple[list[dict], list[dict], list[dict]]:
    """``(links, candidate_links, withheld)`` for a card.

    A candidate card's links cite every endpoint, each imported citation labelled with that endpoint's status and
    version. A certified card's links import evidence only from endpoints certified for every projection it is
    certified for, so nothing an uncertified card says can change its accepted payload. A link that also rests on
    uncertified endpoint evidence is returned separately as a candidate relation; one with no certified citation
    is a withheld gap.
    """
    card_id = card.get("card_id")
    links: list[dict] = []
    candidate_links: list[dict] = []
    withheld: list[dict] = []

    def covers(endpoint: Endpoint) -> bool:
        return set(granted) <= set(endpoint.granted)

    def any_endpoint(_endpoint: Endpoint) -> bool:
        return True

    for link in _list(card.get("links")):
        endpoint_ids = [_dict(e).get("id") for e in _list(_dict(link).get("endpoints"))]

        def cite_from(admit: Callable[[Endpoint], bool], endpoint_ids: list = endpoint_ids):
            def cite_link(evidence_id: str) -> dict | None:
                return cite(evidence_id) or _endpoint_citation(evidence_id, endpoint_ids, card_id, endpoint_card, admit)

            return cite_link

        every, _ = _project_link(link, card_id, cite_from(any_endpoint))
        if granted:
            projected, _ = _project_link(link, card_id, cite_from(covers), "its certified link endpoints")
            disposition = "no_certified_citation_withheld"
            if every["evidence_ids"] != projected["evidence_ids"]:
                candidate_links.append(
                    {"status": "candidate", "accepted": False, "notice": CANDIDATE_LINK_NOTICE, **every}
                )
        else:
            projected, disposition = every, "uncitable_link_withheld"
        if projected["citations"]:
            links.append(projected)
        else:
            withheld.append(
                {
                    "link_id": projected.get("link_id"),
                    "type": projected.get("type"),
                    "disposition": disposition,
                    "evidence_ids": [i for i in _list(_dict(link).get("assertion_ids")) if isinstance(i, str)],
                }
            )
    return links, candidate_links, withheld


def _project_card(
    card: dict, matched_by: str, ledger_entry: dict, endpoint_card: Callable[[str], Endpoint | None]
) -> dict:
    granted, refusals = _certification(card)
    accepted = bool(granted)
    assertions = {
        a["assertion_id"]: a for a in _list(card.get("assertions")) if isinstance(a, dict) and "assertion_id" in a
    }

    def cite(evidence_id: str) -> dict | None:
        return _citation(evidence_id, assertions.get(evidence_id))

    fields = {name: _project_field(res, cite, accepted) for name, res in _dict(card.get("fields")).items()}
    senses = []
    for sense in _list(card.get("senses")):
        sense = _dict(sense)
        projected_sense = {
            "sense_id": sense.get("sense_id"),
            "order": sense.get("order"),
            "state": sense.get("state"),
            "sense_map": _list(sense.get("sense_map")),
            "fields": {name: _project_field(res, cite, accepted) for name, res in _dict(sense.get("fields")).items()},
        }
        for optional in ("seeded_from", "merged_into"):
            if sense.get(optional):
                projected_sense[optional] = sense[optional]
        senses.append(projected_sense)
    # A link's assertions live on the card that states them; a symmetric link cites both endpoints'.
    links, candidate_links, withheld_links = _project_links(card, granted, cite, endpoint_card)
    key = _dict(card.get("key_at_creation"))
    identity = _dict(card.get("identity"))
    build = _dict(card.get("build"))
    gaps = _card_gaps(card, ledger_entry)
    if withheld_links:
        gaps["links"] = {"disposition": withheld_links[0]["disposition"], "links": withheld_links}
    projected = {
        "card_id": card.get("card_id"),
        "card_kind": card.get("card_kind"),
        "state": card.get("state"),
        "status": "certified" if accepted else "candidate",
        "accepted": accepted,
        "notice": CERTIFIED_NOTICE if accepted else CANDIDATE_NOTICE,
        "certified_for": granted,
        "matched_by": matched_by,
        "version": {
            "card_version": build.get("card_version"),
            "build_id": build.get("build_id"),
            "rules_version": build.get("rules_version"),
        },
        "identity": {
            "spelling": key.get("spelling"),
            "stress_patterns": _list(key.get("stress_patterns")),
            "pos": key.get("pos"),
            "paradigm_key": key.get("paradigm_key"),
            "mwe_key": key.get("mwe_key"),
            "key_source_keys": _list(key.get("source_keys")),
            "confidence": identity.get("confidence"),
            "method": identity.get("method"),
            "decided_by": identity.get("decided_by"),
            "source_keys": _list(identity.get("source_keys")),
            "notes": _list(identity.get("notes")),
        },
        "fields": fields,
        "senses": senses,
        "links": links,
        "gaps": gaps,
        "evidence_ids": sorted(assertions),
    }
    if candidate_links:
        projected["candidate_links"] = candidate_links
    if not accepted:
        projected["certification_refusal"] = refusals
    for redirect in ("merged_into", "split_into"):
        if card.get(redirect):
            projected[redirect] = card[redirect]
    return projected


def _sort_key(query: str, card: dict) -> tuple:
    spelling = _dict(card.get("key_at_creation")).get("spelling")
    kinds = {"lexeme": 0, "mwe": 1, "proper_name": 2}
    return (spelling != query, kinds.get(str(card.get("card_kind")), 3), str(card.get("card_id")))


def lookup_word_card(
    word: Any,
    *,
    env: Mapping[str, str] | None = None,
    vesum_lookup: Callable[[str], list[dict]] | None = None,
) -> dict:
    """Return every current card for ``word`` (its spelling or VESUM lemma), labelled by status."""
    normalized, invalid = normalize_query(word)
    if normalized is None:
        return {
            "schema": RESULT_SCHEMA,
            "query": word if isinstance(word, str) else None,
            "result": "invalid_input",
            "status": "invalid_input",
            "reason": invalid,
            "cards": [],
            "per_facet_tools": PER_FACET_TOOLS,
        }
    vesum = _vesum(normalized, vesum_lookup or _vesum_lookup)
    base = {"schema": RESULT_SCHEMA, "query": word, "normalized": normalized, "vesum": vesum}
    store = resolve_card_store(env)
    if isinstance(store, str):
        return _store_unavailable(base, store)
    try:
        if isinstance(store, DatasetStore):
            return _lookup_in_release(store, normalized, vesum, base)
        return _lookup_in_store(store, normalized, vesum, base)
    except StoreUnavailable as exc:
        return _store_unavailable(base, exc.reason)
    except (OSError, RuntimeError):
        # The store went unreadable mid-lookup (a directory listing, a stat): explicit, path-free.
        return _store_unavailable(base, "store_unavailable")


def _store_unavailable(base: dict, reason: str) -> dict:
    return {
        **base,
        "result": "no_card",
        "status": "no_card",
        "card_store": {"available": False, "reason": reason},
        "message": (
            f"No word card could be checked for '{base['normalized']}': the card store is unavailable ({reason}). "
            "Use the per-facet tools."
        ),
        "cards": [],
        "per_facet_tools": PER_FACET_TOOLS,
    }


def _lookup_in_store(store: CardStore, normalized: str, vesum: dict, base: dict) -> dict:
    from scripts.atlas.word_card_certification import certification_run
    from scripts.atlas.word_card_contrasts import validate_card_contrasts
    from scripts.open_dataset.russification import QuarantineError

    index, unreadable, off_store, file_count = _store_index(store)
    wanted = {_fold(normalized): "spelling"}
    for lemma in vesum.get("lemmas", []):
        key = _spelling_key(lemma)
        if key is not None:
            wanted.setdefault(key, "vesum_lemma")
    ledger = _ledger_cards(store)
    endpoint_cards: dict[str, Endpoint | None] = {}

    def endpoint_card(card_id: str) -> Endpoint | None:
        """A link endpoint's card by id with its own certification, read and replayed once per call."""
        if card_id not in endpoint_cards:
            try:
                other = _dict(_read_card(store.cards, f"{card_id}.json"))
                validate_card_contrasts(other)
            except (OSError, ValueError, QuarantineError):
                other = {}
            endpoint_cards[card_id] = (
                Endpoint(other, tuple(_certification(other)[0])) if other.get("card_id") == card_id else None
            )
        return endpoint_cards[card_id]

    cards = []
    # One certification run per call: authority is reread on every lookup, never cached across calls.
    with certification_run():
        for key, matched_by in wanted.items():
            for name in index.get(key, ()):
                try:
                    card = _dict(_read_card(store.cards, name))
                    validate_card_contrasts(card)
                except _OffStore:
                    off_store += 1
                    continue
                except (OSError, ValueError, QuarantineError):
                    unreadable += 1
                    continue
                if _spelling_key(_dict(card.get("key_at_creation")).get("spelling")) != key:
                    continue  # Rewritten in place since indexing; never serve a card for another word.
                cards.append((card, matched_by))
        cards.sort(key=lambda pair: _sort_key(normalized, pair[0]))
        projected = [
            _project_card(card, matched_by, _dict(_dict(ledger).get(card.get("card_id"))), endpoint_card)
            for card, matched_by in cards
        ]
    card_store = {
        "available": True,
        "build_id": _store_build_id(store),
        "card_files": file_count,
        "unreadable_card_files": unreadable,
        "off_store_card_files": off_store,
        "ledger": store.ledger is not None and ledger is not None,
    }
    if store.ledger is not None and ledger is None:
        card_store["ledger_unreadable"] = True
    if not projected:
        return {
            **base,
            "result": "no_card",
            "status": "no_card",
            "card_store": card_store,
            "message": (
                f"No word card (certified or candidate) exists for '{normalized}' in the current card build. "
                "Use the per-facet tools."
            ),
            "cards": [],
            "per_facet_tools": PER_FACET_TOOLS,
        }
    statuses = {card["status"] for card in projected}
    return {
        **base,
        "result": "card_found",
        "status": statuses.pop() if len(statuses) == 1 else "mixed",
        "card_store": card_store,
        "cards": projected,
        "per_facet_tools": PER_FACET_TOOLS,
    }


def _release_layout(root: Path | int) -> None:
    present = set()
    for name in ("manifest.json", "word-cards.jsonl", "cards", "ledger.json", "build-manifest.json"):
        try:
            if isinstance(root, int):
                os.stat(name, dir_fd=root, follow_symlinks=False)
            else:
                (root / name).lstat()
        except FileNotFoundError:
            continue
        present.add(name)
    if present & {"cards", "ledger.json", "build-manifest.json"}:
        raise StoreUnavailable("ambiguous_store_layout")
    if not {"manifest.json", "word-cards.jsonl"} <= present:
        raise StoreUnavailable("store_unavailable")


def _release_metadata(info: os.stat_result) -> tuple:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _directory_identity(info: os.stat_result) -> tuple:
    return (stat.S_IFMT(info.st_mode), info.st_dev, info.st_ino)


def _open_release_directory(path: Path) -> int:
    descriptor = open_directory_component(None, path.anchor)
    try:
        for component in path.parts[1:]:
            child = open_directory_component(descriptor, component)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _hold_release_directory(
    handles: ExitStack, configured: Path, target: LocalTarget, info: os.stat_result
) -> _ReleaseDirectory:
    descriptor = _open_release_directory(target.path)
    handles.callback(os.close, descriptor)
    held = os.fstat(descriptor)
    if _directory_identity(held) != _directory_identity(info) or held.st_dev != target.device:
        raise StoreUnavailable("release_changed_during_read")
    return _ReleaseDirectory(configured, target, descriptor, held)


def _check_release_leaf(leaf: _ReleaseLeaf) -> None:
    for current in (
        os.fstat(leaf.descriptor),
        os.stat(leaf.name, dir_fd=leaf.parent, follow_symlinks=False),
    ):
        if not stat.S_ISREG(current.st_mode) or _release_metadata(current) != _release_metadata(leaf.info):
            raise StoreUnavailable("release_changed_during_read")


def _read_release_leaf(
    handles: ExitStack, directory: _ReleaseDirectory, name: str, bound: int | None = None
) -> tuple[bytes, _ReleaseLeaf]:
    info = os.stat(name, dir_fd=directory.descriptor, follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_dev != directory.info.st_dev:
        raise StoreUnavailable("store_unavailable")
    if bound is None:
        bound = info.st_size  # Trusted checkout pin bootstraps its own size bound.
    if bound <= 0 or info.st_size != bound:
        raise StoreUnavailable("release_integrity_mismatch")
    descriptor = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory.descriptor)
    handles.callback(os.close, descriptor)
    leaf = _ReleaseLeaf(directory.descriptor, name, descriptor, info)
    _check_release_leaf(leaf)  # Check the opened inode before any read, including its type.
    chunks = []
    remaining = bound + 1
    while remaining:
        chunk = os.read(descriptor, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    data = b"".join(chunks)
    _check_release_leaf(leaf)
    if len(data) != bound:
        raise StoreUnavailable("release_integrity_mismatch")
    return data, leaf


def _strict_release_json(data: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def number(token: str) -> float:
        value = float(token)
        try:
            faithful = math.isfinite(value) and Decimal(token) == Decimal(str(value))
        except DecimalException as exc:
            raise ValueError("unrepresentable number") from exc
        if not faithful:
            raise ValueError("unrepresentable number")
        return value

    def constant(_token: str) -> Any:
        raise ValueError("nonfinite number")

    value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_float=number, parse_constant=constant)
    # Reject escaped lone surrogates and values the public JSON response cannot serialize.
    json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    return value


def _release_pin(data: bytes) -> dict:
    try:
        pin = _strict_release_json(data)
        if not isinstance(pin, dict) or set(pin) != {
            "schema_version",
            "repository",
            "release_tag",
            "release_version",
            "provenance",
            "assets",
        }:
            raise ValueError
        if pin["schema_version"] != "word-card-preview-release-pin.v1" or pin["provenance"] != "producer-declared":
            raise ValueError
        for key, pattern in (
            ("repository", r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+"),
            ("release_tag", r"[A-Za-z0-9][A-Za-z0-9._-]*"),
        ):
            if not isinstance(pin[key], str) or re.fullmatch(pattern, pin[key]) is None:
                raise ValueError
        if not isinstance(pin["release_version"], str) or not pin["release_version"].strip():
            raise ValueError
        assets = pin["assets"]
        if not isinstance(assets, dict) or set(assets) != {"manifest.json", "word-cards.jsonl"}:
            raise ValueError
        for asset in assets.values():
            if not isinstance(asset, dict) or set(asset) != {"bytes", "sha256"}:
                raise ValueError
            if type(asset["bytes"]) is not int or asset["bytes"] <= 0:
                raise ValueError
            if not isinstance(asset["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", asset["sha256"]) is None:
                raise ValueError
        return pin
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise StoreUnavailable("release_pin_invalid") from exc


def _release_validator() -> Draft202012Validator:
    """Validate projection rows, using the trusted assembly schema only for IDs and kinds."""
    card_schema = json.loads(CARD_SCHEMA.read_bytes())
    nonempty = {"type": "string", "pattern": r"\S"}

    def object_schema(properties: dict, optional: tuple[str, ...] = ()) -> dict:
        return {
            "type": "object",
            "properties": properties,
            "required": [k for k in properties if k not in optional],
            "additionalProperties": False,
        }

    reference = object_schema(
        {
            "register_source_id": nonempty,
            "register_version": {"type": "integer", "minimum": 1},
            "appears_in": {"type": "array", "items": {"enum": ["internal", "site", "dataset"]}},
        },
        ("appears_in",),
    )
    citation = object_schema(
        {
            **dict.fromkeys(("source_id", "snapshot_id", "locator", "attribution", "terms_ref"), nonempty),
            "source_record_id": {"type": ["string", "null"]},
            "source_record_key": {"type": ["string", "null"]},
            "licence_ref": reference,
            "licence": {"type": "object", "properties": {"name": nonempty}, "required": ["name"]},
        },
        ("source_record_id", "source_record_key"),
    )
    field = object_schema(
        {
            "assertion_id": card_schema["$defs"]["assertion_id"],
            "subject": object_schema({"kind": {"enum": ["card", "sense", "link"]}, "id": nonempty}),
            "field": nonempty,
            "value": {},
            "citation": citation,
        }
    )
    row = object_schema(
        {
            "card_id": card_schema["$defs"]["card_id"],
            "card_version": nonempty,
            "card_kind": {"enum": card_schema["properties"]["card_kind"]["enum"]},
            "status": {"enum": ["CANDIDATE", "CERTIFIED"]},
            "known_gaps": {"type": "array"},
            "fields": {"type": "array", "minItems": 1, "items": field},
        }
    )
    # JSON Schema's integer type also admits 1.0. This contract requires integer tokens, never bools.
    validator_type = extend(
        Draft202012Validator,
        type_checker=Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _checker, value: type(value) is int),
    )
    return validator_type(row)


def _validate_release_rows(manifest: dict, rows: list[dict]) -> None:
    validator = _release_validator()
    card_ids: set[str] = set()
    assertion_ids: set[str] = set()
    for row in rows:
        if not validator.is_valid(row) or row["card_id"] in card_ids:
            raise StoreUnavailable("release_invalid")
        card_ids.add(row["card_id"])
        if row["status"] == "CERTIFIED":
            raise StoreUnavailable("projection_missing_exact_artifact")
        for field in row["fields"]:
            assertion_id, subject, citation = field["assertion_id"], field["subject"], field["citation"]
            if (
                re.fullmatch(
                    validator.schema["properties"]["fields"]["items"]["properties"]["assertion_id"]["pattern"],
                    assertion_id,
                )
                is None
                or assertion_id in assertion_ids
                or (subject["kind"] == "card" and subject["id"] != row["card_id"])
                or citation["source_id"] != citation["licence_ref"]["register_source_id"]
            ):
                raise StoreUnavailable("release_invalid")
            assertion_ids.add(assertion_id)
            if citation["source_id"] == "sum11" or field["field"] in {
                "russification_exposed",
                "soviet_colonization_context",
            }:
                raise StoreUnavailable("projection_excluded_historical_payload")
    expected = {
        "card_count": len(rows),
        "field_citation_count": len(assertion_ids),
        "candidate_count": len(rows),
        "certified_count": 0,
    }
    if any(type(manifest.get(key)) is not int or manifest[key] != value for key, value in expected.items()):
        raise StoreUnavailable("release_invalid")
    if type(manifest.get("dataset_bytes")) is not int or manifest["dataset_bytes"] <= 0:
        raise StoreUnavailable("release_invalid")
    if "source_breakdown" in manifest:
        breakdown = manifest["source_breakdown"]
        if not isinstance(breakdown, dict):
            raise StoreUnavailable("release_invalid")
        for source, counts in breakdown.items():
            if not source.strip() or not isinstance(counts, dict):
                raise StoreUnavailable("release_invalid")
            filtered, reasons = counts.get("filtered_assertions"), counts.get("filter_reasons")
            if type(filtered) is not int or filtered < 0 or not isinstance(reasons, dict):
                raise StoreUnavailable("release_invalid")
            if any(not reason.strip() or type(count) is not int or count < 0 for reason, count in reasons.items()):
                raise StoreUnavailable("release_invalid")


def _recheck_release_snapshot(snapshot: ReleaseSnapshot) -> None:
    try:
        for leaf in snapshot.leaves:
            _check_release_leaf(leaf)
        for directory in snapshot.directories:
            current = _local_target(directory.configured, directory=True)
            if current != directory.target:
                raise StoreUnavailable("release_changed_during_read")
            descriptor = _open_release_directory(current.path)
            try:
                for info in (os.fstat(descriptor), os.fstat(directory.descriptor)):
                    if _directory_identity(info) != _directory_identity(directory.info) or (
                        info.st_mtime_ns,
                        info.st_ctime_ns,
                    ) != (directory.info.st_mtime_ns, directory.info.st_ctime_ns):
                        raise StoreUnavailable("release_changed_during_read")
            finally:
                os.close(descriptor)
        _release_layout(snapshot.directories[0].descriptor)
    except (OSError, StoreUnavailable, ComponentOpenError) as exc:
        raise StoreUnavailable("release_changed_during_read") from exc


def _read_release_snapshot(store: DatasetStore) -> ReleaseSnapshot:
    handles = ExitStack()
    try:
        if (
            not all(getattr(os, flag, 0) for flag in ("O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC", "O_DIRECTORY"))
            or os.open not in os.supports_dir_fd
            or os.stat not in os.supports_dir_fd
            or os.stat not in os.supports_follow_symlinks
        ):
            raise StoreUnavailable("store_unavailable")
        root = _hold_release_directory(handles, store.configured, store.root, store.info)
        _release_layout(root.descriptor)
        try:
            pin_parent = _local_target(DEFAULT_PIN.parent, directory=True)
            pin_directory = _hold_release_directory(handles, DEFAULT_PIN.parent, pin_parent, pin_parent.path.stat())
            pin_bytes, pin_leaf = _read_release_leaf(handles, pin_directory, DEFAULT_PIN.name)
        except (OSError, StoreUnavailable, ComponentOpenError) as exc:
            raise StoreUnavailable("release_pin_invalid") from exc
        pin = _release_pin(pin_bytes)
        assets, leaves = {}, [pin_leaf]
        for name in ("manifest.json", "word-cards.jsonl"):
            expected = pin["assets"][name]
            data, leaf = _read_release_leaf(handles, root, name, expected["bytes"])
            if hashlib.sha256(data).hexdigest() != expected["sha256"]:
                raise StoreUnavailable("release_integrity_mismatch")
            assets[name] = data
            leaves.append(leaf)
        manifest = _strict_release_json(assets["manifest.json"])
        if not isinstance(manifest, dict):
            raise StoreUnavailable("release_invalid")
        lines = jsonl_lines(assets["word-cards.jsonl"].decode("utf-8"))
        if lines[-1] == "":
            lines.pop()
        rows = [_strict_release_json(line.encode("utf-8")) for line in lines]
        # Give missing exact-artifact authority its specific refusal before the preview gate.
        if (isinstance(manifest.get("certified_count"), (int, float)) and manifest["certified_count"] != 0) or any(
            isinstance(row, dict) and row.get("status") == "CERTIFIED" for row in rows
        ):
            raise StoreUnavailable("projection_missing_exact_artifact")
        check_release(pin, assets["manifest.json"], assets["word-cards.jsonl"])
        _validate_release_rows(manifest, rows)
        return ReleaseSnapshot(manifest, rows, pin, (root, pin_directory), tuple(leaves), handles)
    except BaseException as exc:
        handles.close()
        if isinstance(exc, StoreUnavailable):
            raise
        if isinstance(exc, (ValueError, TypeError, RecursionError, OverflowError, PreviewError)):
            raise StoreUnavailable("release_invalid") from exc
        if isinstance(exc, (OSError, RuntimeError, ComponentOpenError)):
            raise StoreUnavailable("store_unavailable") from exc
        raise


def _release_spellings(row: dict) -> list[str]:
    names = {"spelling", "mwe_form"} if row["card_kind"] == "mwe" else {"spelling"}
    return list(
        dict.fromkeys(
            field["value"]
            for field in row["fields"]
            if field["subject"]["kind"] == "card"
            and field["field"] in names
            and isinstance(field["value"], str)
            and _spelling_key(field["value"]) is not None
        )
    )


def _release_spelling_index(rows: list[dict]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        for key in dict.fromkeys(_spelling_key(spelling) for spelling in _release_spellings(row)):
            index[key].append(row["card_id"])
    return index


def _project_release_row(row: dict, matched_by: str, pin: dict) -> dict:
    fields: dict[str, dict] = {}
    senses: dict[str, dict] = {}
    has_links = False
    for assertion in sorted(row["fields"], key=lambda field: field["assertion_id"]):
        subject = assertion["subject"]
        if subject["kind"] == "link":
            has_links = True
            continue
        target = fields
        if subject["kind"] == "sense":
            sense = senses.setdefault(
                subject["id"], {"sense_id": subject["id"], "order": None, "state": None, "sense_map": [], "fields": {}}
            )
            target = sense["fields"]
        field = target.setdefault(
            assertion["field"],
            {"state": None, "accepted": False, "values": [], "gaps": ["resolution_not_in_projection"]},
        )
        field["values"].append(
            {
                "value": assertion["value"],
                "selected": False,
                "evidence_ids": [assertion["assertion_id"]],
                "independence_groups": [],
                "citations": [
                    {**assertion["citation"], "evidence_id": assertion["assertion_id"], "value": assertion["value"]}
                ],
            }
        )
    spellings = _release_spellings(row)
    gaps = {"projection": {"disposition": "assembly_metadata_not_exported"}}
    if len(spellings) > 1:
        gaps["identity"] = {"disposition": "conflicting_spelling_assertions"}
    if senses:
        gaps["senses"] = {"disposition": "sense_metadata_not_in_projection", "sense_ids": list(senses)}
    if has_links:
        gaps["links"] = {"disposition": "link_structure_not_in_projection", "links": []}
    return {
        "card_id": row["card_id"],
        "card_kind": row["card_kind"],
        "state": None,
        "status": "candidate",
        "accepted": False,
        "notice": CANDIDATE_NOTICE,
        "certified_for": [],
        "matched_by": matched_by,
        "certification_refusal": dict.fromkeys(APPROVALS, "projection_missing_exact_artifact"),
        "version": {"card_version": row["card_version"], "build_id": None, "rules_version": None},
        "identity": {
            "spelling": spellings[0] if len(spellings) == 1 else None,
            "spellings": spellings,
            "stress_patterns": [],
            "pos": None,
            "paradigm_key": None,
            "mwe_key": None,
            "key_source_keys": [],
            "confidence": None,
            "method": None,
            "decided_by": None,
            "source_keys": [],
            "notes": [],
        },
        "fields": fields,
        "senses": list(senses.values()),
        "links": [],
        "gaps": gaps,
        "evidence_ids": sorted(field["assertion_id"] for field in row["fields"]),
        "projection": {
            "schema_version": "word-card-dataset.v1",
            "release_version": pin["release_version"],
            "manifest_sha256": pin["assets"]["manifest.json"]["sha256"],
            "dataset_sha256": pin["assets"]["word-cards.jsonl"]["sha256"],
            "row": row,
        },
    }


def _lookup_in_release(store: DatasetStore, normalized: str, vesum: dict, base: dict) -> dict:
    snapshot = _read_release_snapshot(store)
    try:
        index = _release_spelling_index(snapshot.rows)
        wanted = {_fold(normalized): "spelling"}
        for lemma in vesum.get("lemmas", []):
            key = _spelling_key(lemma)
            if key is not None:
                wanted.setdefault(key, "vesum_lemma")
        matched: dict[str, str] = {}
        for key, matched_by in wanted.items():
            for card_id in index.get(key, []):
                matched.setdefault(card_id, matched_by)
        kinds = {"lexeme": 0, "mwe": 1, "proper_name": 2}
        rows = sorted(
            (row for row in snapshot.rows if row["card_id"] in matched),
            key=lambda row: (
                not any(_clean(spelling) == normalized for spelling in _release_spellings(row)),
                kinds[row["card_kind"]],
                row["card_id"],
            ),
        )
        projected = [_project_release_row(row, matched[row["card_id"]], snapshot.pin) for row in rows]
        result = {
            **base,
            "result": "card_found" if projected else "no_card",
            "status": "candidate" if projected else "no_card",
            "cards": projected,
            "per_facet_tools": PER_FACET_TOOLS,
            "card_store": {
                "available": True,
                "build_id": None,
                "ledger": False,
                "card_files": 0,
                "unreadable_card_files": 0,
                "off_store_card_files": 0,
                "format": "dataset_jsonl",
                "dataset_card_count": len(snapshot.rows),
                "release_version": snapshot.pin["release_version"],
                "manifest_sha256": snapshot.pin["assets"]["manifest.json"]["sha256"],
                "dataset_sha256": snapshot.pin["assets"]["word-cards.jsonl"]["sha256"],
            },
        }
        if not projected:
            result["message"] = (
                f"No word card exists for '{normalized}' in the checked release. Use the per-facet tools."
            )
        json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")
        _recheck_release_snapshot(snapshot)
        return result
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise StoreUnavailable("release_invalid") from exc
    finally:
        snapshot.handles.close()
