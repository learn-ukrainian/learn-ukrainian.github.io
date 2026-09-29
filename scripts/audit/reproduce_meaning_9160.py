"""Reproduce the unpublished #9160 meaning-containment evaluation shards.

The pinned release and local source snapshots are inputs. Nothing here uploads,
publishes, or changes the release pointer.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.audit import generate_practice_deck as deck
from scripts.practice.meaning_containment import english, load_sum11_definitions

LEVELS = ("A1", "A2", "B1", "B2", "C1")
PACKAGE_SHA256 = "d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19"
ATLAS_SHA256 = "fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca"
SOURCES_SHA256 = "7868ce16f3cc8280676f08f436b94563ba20e3e7909ad236f06c2bdce19baa7b"
MEANING_MODES = frozenset({"flashcards", "matching", "choice", "synonym"})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"source snapshot mismatch: {path.name}: {actual}")


def evaluate(package: Path, atlas_db: Path, sources_db: Path, output: Path) -> dict:
    require_hash(package, PACKAGE_SHA256)
    require_hash(atlas_db, ATLAS_SHA256)
    require_hash(sources_db, SOURCES_SHA256)
    archive = json.loads(gzip.decompress(package.read_bytes()))
    if archive.get("deckVersion") != "atlas-practice-v1-f1e1cf95470ce319":
        raise ValueError("wrong frozen deck version")
    files = {item["path"]: item["content"].encode("utf-8") for item in archive["files"]}
    if len(files) != 55:
        raise ValueError("frozen release must contain 55 unique shards")
    entries = deck.read_atlas_db(atlas_db)
    by_id = {}
    for entry in entries:
        by_id.setdefault(deck._stable_lemma_id(entry), entry)

    output.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict] = {}
    changed: dict[str, bytes] = {}
    verifier = deck.JsonVesumVerifier({})
    for level in LEVELS:
        lex_name = f"practice-lexemes.{level}.json"
        idx_name = f"practice-index.{level}.json"
        lex_payload = json.loads(files[lex_name])
        idx_payload = json.loads(files[idx_name])
        rows = lex_payload["lexemes"]
        if len(rows) != len(idx_payload["items"]):
            raise ValueError(f"index/lexeme count mismatch: {level}")
        missing = [row["lemmaId"] for row in rows if row["lemmaId"] not in by_id]
        if missing:
            raise ValueError(f"{level}: {len(missing)} published rows lack Atlas entries")
        # Ukrainian source text is never cleaned into a new display. The same
        # word СУМ-11 snapshot is a rejection filter for any retained field.
        definitions = load_sum11_definitions({row["lemma"] for row in rows}, sources_db)
        reason_counts: Counter[str] = Counter()
        mode_before: Counter[str] = Counter()
        mode_after: Counter[str] = Counter()
        mode_reasons: dict[str, Counter[str]] = defaultdict(Counter)
        retained_en = retained_uk = changed_display = 0
        withheld_lemmas: dict[str, list[str]] = defaultdict(list)
        for row, item in zip(rows, idx_payload["items"], strict=True):
            if row["lemmaId"] != item["lemmaId"]:
                raise ValueError(f"index order mismatch: {level}: {row['lemmaId']}")
            before = set(item["modes"])
            mode_before.update(before & MEANING_MODES)
            entry = by_id[row["lemmaId"]]
            result = deck._build_lexeme(entry, verifier, definitions)
            if result is None:
                raise ValueError(f"builder lost published row: {level}: {row['lemmaId']}")
            old_gloss = row["gloss"]
            for field in ("gloss", "glossClean", "meaningSource", "meaningWithheldReason", "meaningMcEligible"):
                row[field] = result[field]
            if row["gloss"] != old_gloss:
                changed_display += 1
            if row["gloss"]:
                if english(row["gloss"]):
                    retained_en += 1
                else:
                    retained_uk += 1
                if not row["meaningMcEligible"]:
                    for mode in before & {"matching", "choice"}:
                        mode_reasons[mode]["meaning_mc_ineligible"] += 1
                    item["modes"] = [mode for mode in item["modes"] if mode not in {"matching", "choice"}]
            else:
                reason = row["meaningWithheldReason"] or "unknown"
                reason_counts[reason] += 1
                withheld_lemmas[reason].append(row["lemma"])
                item["modes"] = [mode for mode in item["modes"] if mode not in MEANING_MODES]
                for mode in before & MEANING_MODES:
                    mode_reasons[mode][reason] += 1
            mode_after.update(set(item["modes"]) & MEANING_MODES)
        for payload, name in ((lex_payload, lex_name), (idx_payload, idx_name)):
            budget = payload["sizeBudget"]
            payload["sizeBudget"] = deck._size_budget(payload, budget["rawLimitBytes"], budget["gzipLimitBytes"])
            if not payload["sizeBudget"]["ok"]:
                raise ValueError(f"size budget exceeded: {name}")
            changed[name] = deck._json_bytes(payload)
        summary[level] = {
            "rows": len(rows), "retained_en": retained_en, "retained_uk": retained_uk,
            "withheld": sum(reason_counts.values()), "changed_display_from_release": changed_display,
            "reasons": dict(sorted(reason_counts.items())),
            "modes": {mode: {"before": mode_before[mode], "after": mode_after[mode],
                              "withheld_reasons": dict(sorted(mode_reasons[mode].items()))}
                      for mode in sorted(MEANING_MODES)},
            "withheld_lemmas": {reason: sorted(lemmas, key=str.casefold) for reason, lemmas in sorted(withheld_lemmas.items())},
        }
    for name, content in files.items():
        (output / name).write_bytes(changed.get(name, content))
    summary["hashes"] = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                         for level in LEVELS
                         for name in (f"practice-lexemes.{level}.json", f"practice-index.{level}.json", f"practice-synonym.{level}.json")}
    (output / "meaning-9160-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--atlas-db", type=Path, required=True)
    parser.add_argument("--sources-db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.package, args.atlas_db, args.sources_db, args.output)
    for level in LEVELS:
        item = result[level]
        print(f"{level}: {item['rows']} rows; {item['retained_en']} EN; {item['retained_uk']} UK; {item['withheld']} withheld")


if __name__ == "__main__":
    main()
