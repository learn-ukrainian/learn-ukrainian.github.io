"""Read-only word-card lookup behind the Sources MCP ``word_card`` tool (#11084).

Cards ship versioned and improve over versions, so the lookup serves the
current card of a word whether or not it is certified. The status is never
taken from the card: every call replays the exact-artifact certification
boundary (``load_certified_card_for_export``) against the live review ledger.
A card that fails it is returned as ``candidate``: each value is a cited
source assertion awaiting review, not an accepted fact (#8977).

The card store is a host-only assembly build directory (``cards/*.json`` plus
the optional ``ledger.json`` and ``build-manifest.json`` written by
``scripts.atlas.word_card_assembly``), named by ``LU_WORD_CARDS_DIR``. Nothing
here writes, and no host path is echoed in a result.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

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


@dataclass(frozen=True)
class CardStore:
    """A validated, read-only card build directory."""

    cards_dir: Path
    ledger_path: Path | None
    manifest_path: Path | None


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


def resolve_card_store(env: Mapping[str, str] | None = None) -> CardStore | str:
    """Resolve the configured card build, or return a path-free refusal reason."""
    from scripts.storage.topology import is_network_filesystem_path

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
        path = path.resolve(strict=True)
        if not path.is_dir():
            return "not_a_directory"
        if is_network_filesystem_path(path):
            return "locality_network"
    except FileNotFoundError:
        return "store_missing"
    except (OSError, RuntimeError):
        return "store_unavailable"
    cards_dir = path / "cards" if (path / "cards").is_dir() else path
    ledger = path / "ledger.json"
    manifest = path / "build-manifest.json"
    return CardStore(cards_dir, ledger if ledger.is_file() else None, manifest if manifest.is_file() else None)


def _fold(text: str) -> str:
    return text.casefold()


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _read_json(path: Path) -> Any:
    return json.loads(path.read_bytes())


@lru_cache(maxsize=4)
def _spelling_index(cards_dir: str, _mtime_ns: int, _file_count: int) -> tuple[dict[str, tuple[str, ...]], int]:
    """Map folded spellings to card files. The key changes when files are added or removed."""
    index: dict[str, list[str]] = defaultdict(list)
    unreadable = 0
    for path in sorted(Path(cards_dir).glob("*.json")):
        try:
            spelling = _dict(_dict(_read_json(path)).get("key_at_creation")).get("spelling")
        except (OSError, ValueError):
            unreadable += 1
            continue
        key = _spelling_key(spelling)
        if key is None:
            unreadable += 1
            continue
        index[key].append(path.name)
    return {key: tuple(names) for key, names in index.items()}, unreadable


def _store_index(store: CardStore) -> tuple[dict[str, tuple[str, ...]], int, int]:
    names = [entry.name for entry in os.scandir(store.cards_dir) if entry.name.endswith(".json")]
    index, unreadable = _spelling_index(str(store.cards_dir), store.cards_dir.stat().st_mtime_ns, len(names))
    return index, unreadable, len(names)


@lru_cache(maxsize=2)
def _ledger(path: str, _mtime_ns: int, _size: int) -> dict:
    return _dict(_dict(_read_json(Path(path))).get("cards"))


def _ledger_cards(store: CardStore) -> dict:
    if store.ledger_path is None:
        return {}
    try:
        stat = store.ledger_path.stat()
        return _ledger(str(store.ledger_path), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError):
        return {}


def _store_build_id(store: CardStore) -> str | None:
    if store.manifest_path is None:
        return None
    try:
        build_id = _dict(_read_json(store.manifest_path)).get("build_id")
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


def _citation(evidence_id: str, assertion: dict | None) -> dict:
    if assertion is None:
        return {"evidence_id": evidence_id, "missing_assertion": True}
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
        "extraction_confidence": assertion.get("extraction_confidence"),
        "mapping": assertion.get("mapping"),
        "tier": assertion.get("tier"),
    }
    if assertion.get("source_id") == _SOVIET_DICTIONARY_ID:
        citation["role"] = "soviet_colonization_context"
        citation["notice"] = SOVIET_CONTEXT_NOTICE
    return {key: value for key, value in citation.items() if value is not None}


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


def _project_field(resolution: Any, assertions: dict[str, dict], accepted: bool) -> dict:
    resolution = _dict(resolution)
    selected = resolution.get("selected")
    selected_ids = set(selected) if isinstance(selected, list) else {selected} if isinstance(selected, str) else set()
    values = []
    for value in _list(resolution.get("values")):
        value = _dict(value)
        ids = [i for i in _list(value.get("assertion_ids")) if isinstance(i, str)]
        projected = {
            "value": value.get("value_norm"),
            "selected": bool(selected_ids.intersection(ids)),
            "evidence_ids": ids,
            "independence_groups": _list(value.get("independence_groups")),
            "citations": [_citation(i, assertions.get(i)) for i in ids],
        }
        if value.get("declared_set"):
            projected["declared_set"] = True
        values.append(projected)
    field = {"state": resolution.get("state"), "accepted": accepted, "values": values}
    non_voting = [
        {
            "evidence_id": _dict(item).get("assertion_id"),
            "reason": _dict(item).get("reason"),
            "citation": _citation(
                str(_dict(item).get("assertion_id")), assertions.get(_dict(item).get("assertion_id"))
            ),
        }
        for item in _list(resolution.get("non_voting"))
    ]
    if non_voting:
        field["non_voting"] = non_voting
    gaps = _field_gaps(resolution)
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


def _project_card(card: dict, matched_by: str, ledger_entry: dict) -> dict:
    granted, refusals = _certification(card)
    accepted = bool(granted)
    assertions = {
        a["assertion_id"]: a for a in _list(card.get("assertions")) if isinstance(a, dict) and "assertion_id" in a
    }
    fields = {name: _project_field(res, assertions, accepted) for name, res in _dict(card.get("fields")).items()}
    senses = []
    for sense in _list(card.get("senses")):
        sense = _dict(sense)
        senses.append(
            {
                "sense_id": sense.get("sense_id"),
                "order": sense.get("order"),
                "state": sense.get("state"),
                "fields": {
                    name: _project_field(res, assertions, accepted) for name, res in _dict(sense.get("fields")).items()
                },
            }
        )
    key = _dict(card.get("key_at_creation"))
    identity = _dict(card.get("identity"))
    build = _dict(card.get("build"))
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
            "confidence": identity.get("confidence"),
            "method": identity.get("method"),
        },
        "fields": fields,
        "senses": senses,
        "links": [
            {
                "type": _dict(link).get("type"),
                "state": _dict(link).get("state"),
                "card_ids": [
                    _dict(e).get("id")
                    for e in _list(_dict(link).get("endpoints"))
                    if _dict(e).get("id") != card.get("card_id")
                ],
            }
            for link in _list(card.get("links"))
        ],
        "gaps": _card_gaps(card, ledger_entry),
        "evidence_ids": sorted(assertions),
    }
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
    store = resolve_card_store(env)
    base = {"schema": RESULT_SCHEMA, "query": word, "normalized": normalized, "vesum": vesum}
    if isinstance(store, str):
        return {
            **base,
            "result": "no_card",
            "status": "no_card",
            "card_store": {"available": False, "reason": store},
            "message": (
                f"No word card could be checked for '{normalized}': the card store is unavailable ({store}). "
                "Use the per-facet tools."
            ),
            "cards": [],
            "per_facet_tools": PER_FACET_TOOLS,
        }
    from scripts.atlas.word_card_certification import certification_run

    index, unreadable, file_count = _store_index(store)
    wanted = {_fold(normalized): "spelling"}
    for lemma in vesum.get("lemmas", []):
        key = _spelling_key(lemma)
        if key is not None:
            wanted.setdefault(key, "vesum_lemma")
    ledger = _ledger_cards(store)
    cards = []
    # One certification run per call: authority is reread on every lookup, never cached across calls.
    with certification_run():
        for key, matched_by in wanted.items():
            for name in index.get(key, ()):
                try:
                    card = _dict(_read_json(store.cards_dir / name))
                except (OSError, ValueError):
                    unreadable += 1
                    continue
                if _spelling_key(_dict(card.get("key_at_creation")).get("spelling")) != key:
                    continue  # Rewritten in place since indexing; never serve a card for another word.
                cards.append((card, matched_by))
        cards.sort(key=lambda pair: _sort_key(normalized, pair[0]))
        projected = [
            _project_card(card, matched_by, _dict(ledger.get(card.get("card_id")))) for card, matched_by in cards
        ]
    card_store = {
        "available": True,
        "build_id": _store_build_id(store),
        "card_files": file_count,
        "unreadable_card_files": unreadable,
        "ledger": store.ledger_path is not None,
    }
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
