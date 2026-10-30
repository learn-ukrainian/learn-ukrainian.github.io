"""Freeze the published A1-v1 rows and their source-backed lemma dispositions.

Use for #11943 AC-01 inventory replay, never card generation or certification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_sources as pilot_sources
from scripts.common.repo_root import main_checkout_root
from scripts.lexicon import ulif_raw_cache
from scripts.lib.readonly_sqlite import open_readonly
from scripts.verification import vesum

ROOT = Path(__file__).resolve().parents[2]
FREEZE = "770dadd3fb7d69512f5c05eaff6aa499c25f52fc"
VOCABULARY = "curriculum/l2-uk-en/a1-v1"
OUTPUT = Path("registry/atlas/a1-v1-inventory.json")
PILOT = Path("registry/atlas/pilot/pilot-v1.json")
REGISTRY = Path("registry/atlas/identity/registry.json")
PINS = {
    str(PILOT): "19caa9148c76294156f12b4d1b11c11f4563ba0facac142460dd927543a7bc71",
    str(REGISTRY): "681be77e60edbe621ca68e680db2bffbbd9e99267b011fb0515e090fe8d8a06d",
}
POS = {
    "noun": "noun", "noun plural": "noun", "plural noun": "noun", "noun form": "noun",
    "noun in vocative": "noun", "proper noun": "noun", "proper noun plural": "noun",
    "name in vocative": "noun", "verb": "verb", "verb form": "verb", "infinitive": "verb",
    "modal verb form": "verb", "reflexive verb form": "verb", "command": "verb",
    "imperative": "verb", "adjective": "adj", "adj": "adj", "adverb": "adv", "adv": "adv",
    "negative adverb": "adv", "preposition": "prep", "conjunction": "conj", "conj": "conj",
    "particle": "part", "interjection": "intj", "numeral": "numr",
}
NAMES = {"proper noun", "proper noun plural", "name in vocative"}
PRONOUNS = {"pronoun", "pronoun form", "negative pronoun"}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def serialize(value: dict) -> str:
    """One record per line; large source replies do not need repeated indentation."""
    fields = []
    for key, item in sorted(value.items()):
        head = "  " + json.dumps(key) + ": "
        if isinstance(item, dict):
            records = ["    " + json.dumps(k, ensure_ascii=False) + ": " + canonical(v).decode()
                       for k, v in sorted(item.items())]
            fields.append(head + "{\n" + ",\n".join(records) + "\n  }")
        elif isinstance(item, list):
            fields.append(head + "[\n" + ",\n".join("    " + canonical(v).decode() for v in item) + "\n  ]")
        else:
            fields.append(head + canonical(item).decode())
    return "{\n" + ",\n".join(fields) + "\n}\n"


def unstressed(value: str) -> str:
    return unicodedata.normalize("NFC", value).replace("\u0301", "").strip()


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], timeout=30)


def frozen_rows(root: Path, revision: str = FREEZE) -> tuple[list[dict], list[dict]]:
    paths = git(root, "ls-tree", "-r", "--name-only", revision, VOCABULARY).decode().splitlines()
    files, inventory = [], []
    for path in sorted(p for p in paths if p.endswith("/vocabulary.yaml")):
        body = git(root, "show", f"{revision}:{path}")
        document = yaml.safe_load(body)
        rows = document if isinstance(document, list) else document["items"]
        files.append({"path": path, "sha256": hashlib.sha256(body).hexdigest(), "rows": len(rows),
                      "git_blob": git(root, "rev-parse", f"{revision}:{path}").decode().strip()})
        for index, row in enumerate(rows):
            literal = row.get("lemma", row.get("word"))
            if not isinstance(literal, str) or not literal.strip():
                raise ValueError("Vocabulary row has no nonempty lemma or word")
            inventory.append({"id": f"{path}#/{index}" if isinstance(document, list)
                              else f"{path}#/items/{index}", "source": row,
                              "literal": literal, "key": unstressed(literal).casefold()})
    return files, inventory


class Evidence:
    """The Sources tools' own read-only backend, with content-bound query receipts."""

    def __init__(self, db: Path):
        self.db = db
        self.words: dict[str, dict] = {}
        self.lemmas: dict[str, dict] = {}
        self.identity: dict | None = None

    def word(self, value: str) -> dict:
        if value not in self.words:
            inspection = vesum.inspect_word(value, db_path=self.db).as_dict()
            if inspection["status"] == "UNAVAILABLE":
                raise ValueError("Sources inspect_word unavailable")
            if self.identity is None:
                self.identity = inspection["pipeline_identity"]
            if not self.identity or inspection["pipeline_identity"] != self.identity:
                raise ValueError("VESUM pipeline identity missing or changed during inventory")
            matches = sorted(vesum.verify_word(value, db_path=self.db), key=canonical)
            # Shared import metadata is published once. Full entry-qualified
            # analyses stay in inspect_word; the compatibility query has a receipt.
            del inspection["pipeline_identity"], inspection["source_version"]
            verification = {"match_count": len(matches), "sha256": digest(matches)}
            self.words[value] = {"inspect_word": inspection, "verify_word": verification,
                                 "sha256": digest({"inspection": inspection, "verification": verification})}
        return self.words[value]

    def lemma(self, value: str) -> dict:
        if value not in self.lemmas:
            forms = sorted(vesum.verify_lemma(value, db_path=self.db), key=canonical)
            self.lemmas[value] = {"tool": "verify_lemma", "query": value, "forms": len(forms),
                                  "sha256": digest(forms), "head_evidence": value}
            self.word(value)
        return self.lemmas[value]


def compatible(analysis: dict, label: str, name: bool) -> bool:
    tags = analysis["tags"].split(":")
    return (("prop" in tags) == name
            and (label not in POS or analysis["pos"] == POS[label])
            and (label not in PRONOUNS or "pron" in tags))


def readings(proof: dict) -> list[dict]:
    inspection = proof["inspect_word"]
    return inspection["clean_analyses"] + inspection["marked_analyses"]


def disposition(row: dict, evidence: Evidence) -> dict:
    literal, label = unstressed(row["literal"]), row["source"]["pos"]
    name = label in NAMES
    if "/" in literal:
        alternatives = [p.strip() for p in literal.split("/")]
        for part in alternatives:
            evidence.word(part)
        return {"kind": "slash_alternatives", "reason": "alternatives_need_separate_context",
                "alternatives": alternatives, "evidence": alternatives}
    if len(literal.split()) > 1 or (not name and ("phrase" in label or label == "expression")):
        return {"kind": "name" if name else "phrase", "reason": "multiword_identity_unresolved",
                "literal": literal, "lemma": None, "candidates": []}
    # Case folding groups the denominator only. Only explicitly common words get
    # a lowercase lookup; names retain the exact supplied case.
    lookup = literal if name else literal.lower()
    proof = evidence.word(lookup)
    candidates = readings(proof)
    compatible_rows = [a for a in candidates if compatible(a, label, name)]
    entries = sorted({a["entry_id"] for a in compatible_rows})
    result = {"kind": "name" if name else "unresolved", "evidence": lookup,
              "candidates": entries, "lemma": None, "reason": "no_attested_compatible_reading"}
    if len(entries) > 1:
        return dict(result, kind="name" if name else "ambiguous", reason="multiple_vesum_entries")
    if not entries:
        return result
    if proof["inspect_word"]["status"] != "CLEAN":
        return dict(result, reason="marked_or_mixed_readings")
    candidate = compatible_rows[0]
    lemma = candidate["lemma"]
    lemma_proof = evidence.lemma(lemma)
    head = evidence.word(lemma)
    if not lemma_proof["forms"] or not any(a["entry_id"] == entries[0] for a in readings(head)):
        return dict(result, reason="lemma_not_attested_for_entry")
    return dict(result, kind="name" if name else "lemma", lemma=lemma,
                entry_id=entries[0], pos=candidate["pos"], reason="one_compatible_vesum_entry")


class PilotLinks:
    """Reuse pilot allocations only through the existing authenticated matcher."""

    def __init__(self, manifest: dict, registry: dict, sources: pilot_sources.PilotSources):
        allocated, _ = assembly.pilot_allocation(manifest, registry)
        self.sources = sources
        self.records = {r["locator"]: r for r in manifest["selection"]["source_records"]}
        self.units = []
        self.matches = {}
        for unit in manifest["selection"]["units"]:
            entry = allocated[unit["unit_key"]]
            if entry["card_kind"] != "mwe":
                self.units.append((unit, entry))

    def match(self, lemma: str, pos: str, entry_id: int, name: bool) -> dict:
        key = (lemma, pos, entry_id, name)
        if key not in self.matches:
            self.matches[key] = self._match(lemma, pos, entry_id, name)
        return self.matches[key]

    def _match(self, lemma: str, pos: str, entry_id: int, name: bool) -> dict:
        candidates, accepted = [], []
        for unit, entry in self.units:
            key = entry["key_at_creation"]
            if key["spelling"] != lemma or key["pos"] != pos:
                continue
            raw = self.records[unit["anchor_locator"]]["raw_row"]
            observed = self.sources.homonyms(raw["normalized_query"])
            if raw not in observed:
                raise ValueError("Pilot anchor changed in Sources store")
            homonyms = assembly.class_homonyms(SimpleNamespace(sources=self.sources), raw, unit, name)
            keep_gender = any(len(slot) > 1 and any(t in pilot_sources.GENDERS for t in slot)
                              for h in homonyms.values() if h["paradigm"] for slot in h["paradigm"]["slots"])
            forms = [r for r in self.sources.vesum_forms(lemma) if r["pos"] == pos]
            paradigms = pilot_sources.vesum_paradigm(forms, keep_gender)
            paradigms = {k: v for k, v in paradigms.items() if ("prop" in v["flags"]) == name}
            match = pilot_sources.match_identity(raw["id"], homonyms, paradigms)
            candidates.append({"card_id": entry["card_id"], "unit_key": unit["unit_key"],
                               "anchor": unit["anchor_locator"], "match": match})
            if match["vesum_entry"] == entry_id and match["confidence"] == "high":
                accepted.append(entry["card_id"])
        return {"card_id": accepted[0] if len(accepted) == 1 else None, "candidates": candidates,
                "reason": "authenticated_pilot_match" if len(accepted) == 1
                else "pilot_correspondence_unresolved" if candidates else "not_in_pilot"}


def build(evidence: Evidence, links: PilotLinks, files: list[dict], rows: list[dict]) -> dict:
    keys = defaultdict(list)
    for index, row in enumerate(rows):
        row["mapping"] = disposition(row, evidence)
        mapping = row["mapping"]
        mapping["resolution"] = ("resolved" if mapping.get("entry_id") is not None
                                 else "ambiguous" if mapping["reason"] == "multiple_vesum_entries"
                                 else "unresolved")
        if mapping.get("entry_id") is not None:
            mapping["pilot"] = links.match(mapping["lemma"], mapping["pos"], mapping["entry_id"],
                                           mapping["kind"] == "name")
        keys[row["key"]].append(index)
    if (len(files), len(rows), len(keys), sum(len(k.split()) == 1 for k in keys)) != (55, 2144, 1296, 1116):
        raise ValueError("Frozen A1 denominator differs from the readiness report")
    return {
        "schema_version": "atlas-a1-v1-inventory.v1", "issue": 11943, "acceptance": "AC-01",
        "freeze": {"git_commit": FREEZE, "files": files, "pilot_input_sha256": PINS},
        "normalization": {"key": "NFC, remove U+0301, strip edge whitespace, casefold",
                          "identity": "Case retained; VESUM entry_id distinguishes homonyms. No punctuation removal.",
                          "lookup": "Common words lowercased; typed names retain case. Sources folds U+2019/U+02BC to ASCII apostrophe.",
                          "context_pos": POS, "pronoun_labels": sorted(PRONOUNS), "name_labels": sorted(NAMES)},
        "sources": {"vesum_pipeline_identity": evidence.identity,
                    "backend": "scripts.verification.vesum: verify_word, verify_lemma, inspect_word",
                    "pilot_consumed_queries": dict(sorted(links.sources.consumed.items()))},
        "counts": {"files": len(files), "rows": len(rows), "keys": len(keys), "single_token_keys": 1116,
                   "multiword_keys": 180, "dispositions": dict(sorted(Counter(r["mapping"]["kind"] for r in rows).items())),
                   "resolutions": dict(sorted(Counter(r["mapping"]["resolution"] for r in rows).items())),
                   "pilot_linked_rows": sum(bool(r["mapping"].get("pilot", {}).get("card_id")) for r in rows)},
        "keys": dict(sorted(keys.items())),
        "rows": [{k: v for k, v in row.items() if k != "literal"} for row in rows],
        "word_evidence": dict(sorted(evidence.words.items())), "lemma_evidence": dict(sorted(evidence.lemmas.items())),
    }


def main(argv: list[str] | None = None) -> int:
    primary = main_checkout_root(ROOT)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.a1_vocabulary_inventory > registry/atlas/a1-v1-inventory.json
  .venv/bin/python -m scripts.atlas.a1_vocabulary_inventory --check

Outputs: JSON to stdout, or comparison with --check. No files or stores are written.
Exit codes: 0 generated or identical; 1 unavailable/drifted input or mismatch; 2 bad arguments.
Related: #11943 AC-01; docs/atlas/word-cards/a1-v1-inventory.md
""")
    parser.add_argument("--check", action="store_true", help="Compare to committed inventory without writing JSON (default: off)")
    parser.add_argument("--vesum-db", type=Path, default=primary / "data/vesum.db",
                        help="Read-only VESUM store (default: primary data/vesum.db); example: fixtures/vesum.db")
    parser.add_argument("--sources-db", type=Path, default=primary / "data/sources.db",
                        help="Read-only Sources store (default: primary data/sources.db); example: fixtures/sources.db")
    parser.add_argument("--raw-cache", type=Path, default=ulif_raw_cache.cache_path(),
                        help="Read-only authenticated ULIF raw cache (default: shared cache); example: fixtures/ulif_raw.sqlite")
    args = parser.parse_args(argv)
    try:
        documents = {}
        for path, expected in PINS.items():
            body = (ROOT / path).read_bytes()
            if hashlib.sha256(body).hexdigest() != expected:
                raise ValueError("Pilot input changed against AC-01 freeze")
            documents[path] = json.loads(body)
        files, rows = frozen_rows(ROOT)
        with ExitStack() as stack:
            connections = [stack.enter_context(open_readonly(p.resolve()))
                           for p in (args.sources_db, args.vesum_db, args.raw_cache)]
            for connection in connections:
                connection.execute("BEGIN")
            sources = pilot_sources.PilotSources(*connections)
            links = PilotLinks(documents[str(PILOT)], documents[str(REGISTRY)], sources)
            # The Sources backend and the pilot matcher must see the same held
            # VESUM snapshot even if the store binding changes during a run.
            with vesum.get_vesum_connection(args.vesum_db) as connection:
                connection.execute("BEGIN")
                result = build(Evidence(args.vesum_db), links, files, rows)
        body = serialize(result)
        if args.check:
            if (ROOT / OUTPUT).read_text(encoding="utf-8") != body:
                raise ValueError("Inventory differs from frozen files or current Sources evidence")
            print(json.dumps(result["counts"], sort_keys=True))
        else:
            sys.stdout.write(body)
        return 0
    except (OSError, ValueError, assembly.foundation.Refusal) as error:
        print(f"Inventory refused: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    finally:
        vesum.close_vesum_conn()


if __name__ == "__main__":
    raise SystemExit(main())
