#!/usr/bin/env python3
"""Enrich and disambiguate heteronyms/homographs in the Word Atlas (#8022).

Identifies lemmas with multiple phonemic stress patterns and distinct lexical
senses in academic authorities (СУМ-11, УМІФ, СУМ-20, VESUM), extracts their
distinct stress, paradigm, gloss, CEFR level, synonyms, and heritage classification,
and attaches a structured ``heteronyms`` array to the Atlas entry.

Usage:
    .venv/bin/python scripts/lexicon/enrich_heteronyms.py --lemma город
    .venv/bin/python scripts/lexicon/enrich_heteronyms.py --lemma замок
    .venv/bin/python scripts/lexicon/enrich_heteronyms.py --scan
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _resolve_primary_checkout() -> Path | None:
    parts = ROOT.parts
    if ".worktrees" in parts:
        return Path(*parts[: parts.index(".worktrees")])
    return ROOT


def _resolve_sources_db() -> Path:
    env_path = os.environ.get("SOURCES_DB_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)
    local = ROOT / "data" / "sources.db"
    if local.is_file() and local.stat().st_size > 1_000_000:
        return local
    primary = _resolve_primary_checkout()
    if primary:
        prim_db = primary / "data" / "sources.db"
        if prim_db.is_file():
            return prim_db
    return local


def _resolve_vesum_db() -> Path:
    env_path = os.environ.get("VESUM_DB_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)
    local = ROOT / "data" / "vesum.db"
    if local.is_file() and local.stat().st_size > 1_000_000:
        return local
    primary = _resolve_primary_checkout()
    if primary:
        prim_db = primary / "data" / "vesum.db"
        if prim_db.is_file():
            return prim_db
    return local


def parse_sum11_heteronyms(lemma: str, definition: str) -> list[dict[str, Any]]:
    """Extract distinct stressed heads and their definitions from a СУМ-11 block."""
    clean_lemma = lemma.lower().replace("-", "").strip()
    matches = list(
        re.finditer(
            rf"(?:^|[\n.!?]\s*)(?P<head>[А-ЯҐІЇЄ\u0300\u0301-]{{{len(clean_lemma)},}})\b\s*,\s*(?P<grammar>[^.]+)\.\s*(?P<body>.*?)(?=(?:[\n.!?]\s*[А-ЯҐІЇЄ\u0300\u0301-]{{{len(clean_lemma)},}}\b\s*,\s*[^.]+\.|$))",
            definition,
            flags=re.DOTALL,
        )
    )
    heads: list[dict[str, Any]] = []
    for m in matches:
        raw_head = m.group("head").strip()
        clean_head = raw_head.lower().replace("\u0300", "").replace("\u0301", "").replace("-", "")
        if clean_head == clean_lemma:
            heads.append(
                {
                    "head": raw_head,
                    "grammar": m.group("grammar").strip(),
                    "body": m.group("body").strip(),
                }
            )
    return heads


CURATED_HETERONYMS: dict[str, list[dict[str, Any]]] = {
    "город": [
        {
            "headword": "горо́д",
            "short_label": "ділянка землі (A2)",
            "gloss": "vegetable garden, garden plot",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None,
            },
            "pronunciation": {
                "ipa": "[ɦɔˈrɔd]",
                "source": "VESUM",
            },
            "stress": {
                "form": "горо́д",
                "source": "ukrainian-word-stress",
            },
            "morphology": {
                "pos": "іменник",
                "paradigm": {
                    "kind": "noun",
                    "cases": {
                        "називний": {"singular": "горо́д", "plural": "горо́ди"},
                        "родовий": {"singular": "горо́ду", "plural": "городі́в"},
                        "давальний": {"singular": "горо́дові / горо́ду", "plural": "горо́дам"},
                        "знахідний": {"singular": "горо́д", "plural": "горо́ди"},
                        "орудний": {"singular": "горо́дом", "plural": "горо́дами"},
                        "місцевий": {"singular": "на горо́ді / горо́ду", "plural": "горо́дах"},
                        "кличний": {"singular": "горо́де", "plural": "горо́ди"},
                    },
                },
                "stress": {
                    "source": "ukrainian-word-stress",
                    "forms": {
                        "городу": "горо́ду",
                        "городом": "горо́дом",
                        "городі": "горо́ді",
                        "городе": "горо́де",
                        "городи": "горо́ди",
                        "городів": "городі́в",
                        "городам": "горо́дам",
                        "городами": "горо́дами",
                        "городах": "горо́дах",
                    },
                },
            },
            "sections": {
                "synonyms": {
                    "source": "СУМ-20",
                    "items": ["грядка", "городчик"],
                },
                "idioms": {
                    "items": [
                        {
                            "phrase": "город ( рідше тин) городити",
                            "definition": "Починати якусь копітку справу.",
                            "source": "Фразеологічний словник української мови",
                        },
                        {
                            "phrase": "камінь у чийсь город",
                            "definition": "Недоброзичливий натяк кому-небудь.",
                            "source": "Фразеологічний словник української мови",
                        },
                    ],
                    "source": "Фразеологічний словник української мови",
                },
                "proverbs": {
                    "items": [
                        {
                            "text": "В хаті гульки, а в городі ані цибульки",
                            "gloss": "Глум з господині, що гуляє, а не пильнує господарства.",
                            "source": "Приповідки або українсько-народня філософія",
                        },
                        {
                            "text": "Мій город, як моя комора",
                            "gloss": "Огородина в літі помагає багато в харчі.",
                            "source": "Приповідки або українсько-народня філософія",
                        },
                        {
                            "text": "Не лазь у городи, бо наробиш шкоди",
                            "gloss": "До чужого діла не мішайся, бо не знаєш його.",
                            "source": "Приповідки або українсько-народня філософія",
                        },
                    ],
                    "source": "Приповідки або українсько-народня філософія",
                },
            },
            "examples": [
                {
                    "uk": "На вихідни́х ми бу́демо працюва́ти на горо́ді.",
                    "en": "On the weekend, we will work in the vegetable garden.",
                    "source": "Anna Ohoiko",
                    "locator": "ohoiko-1000-words entry 168",
                }
            ],
            "distinction_note": "Не плутати з омографом «го́род» (наголос на першому складі: застаріле «місто», фортеця).",
        },
        {
            "headword": "го́род",
            "short_label": "заст. місто",
            "gloss": "city, town, fortified settlement (archaic)",
            "pos": "noun",
            "cefr": None,
            "heritage_status": {
                "classification": "authentic-archaism",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": "treasured",
                "attestations": [
                    {
                        "source": "esum",
                        "ref": "город:1:570",
                        "word": "город",
                        "detail": "город (заст. розм.) «місто», город (< огород) «квітник біля хати»",
                    }
                ],
            },
            "pronunciation": {
                "ipa": "[ˈɦɔrɔd]",
                "source": "kaikki/Wiktionary (CC BY-SA 3.0)",
            },
            "stress": {
                "form": "го́род",
                "source": "kaikki/Wiktionary (CC BY-SA 3.0)",
            },
            "morphology": {
                "pos": "іменник",
                "paradigm": {
                    "kind": "noun",
                    "cases": {
                        "називний": {"singular": "го́род", "plural": "городи́"},
                        "родовий": {"singular": "го́рода (го́роду)", "plural": "городі́в"},
                        "давальний": {"singular": "го́родові / го́роду", "plural": "города́м"},
                        "знахідний": {"singular": "го́род", "plural": "городи́"},
                        "орудний": {"singular": "го́родом", "plural": "города́ми"},
                        "місцевий": {"singular": "у го́роді", "plural": "города́х"},
                        "кличний": {"singular": "го́роде", "plural": "городи́"},
                    },
                },
                "stress": {
                    "source": "Правописний словник Голоскевича (1929)",
                    "forms": {
                        "города": "го́рода",
                        "городу": "го́роду",
                        "городом": "го́родом",
                        "городі": "го́роді",
                        "городи": "городи́",
                        "городів": "городі́в",
                        "городам": "города́м",
                        "городами": "города́ми",
                        "городах": "города́х",
                    },
                },
            },
            "sections": {
                "synonyms": {
                    "source": "СУМ-11: Те саме, що → місто",
                    "items": ["місто"],
                },
            },
            "examples": [
                {
                    "uk": "В тім городі жила Дидона, А город звався Карфаген.",
                    "en": "In that city lived Dido, and the city was called Carthage.",
                    "source": "Іван Котляревський, «Енеїда»",
                    "locator": "Котл., І, 1952, 71",
                }
            ],
            "distinction_note": "Не плутати з сучасним словом «горо́д» (наголос на другому складі: ділянка землі біля хати для вирощування овочів).",
        },
    ],
    "замок": [
        {
            "headword": "за́мок",
            "short_label": "палац, фортеця",
            "gloss": "castle, fortress, palace",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
            },
            "pronunciation": {
                "ipa": "[ˈzamɔk]",
                "source": "kaikki/Wiktionary",
            },
            "stress": {
                "form": "за́мок",
                "source": "ukrainian-word-stress",
            },
            "morphology": {
                "pos": "іменник",
                "paradigm": {
                    "kind": "noun",
                    "cases": {
                        "називний": {"singular": "за́мок", "plural": "замки́"},
                        "родовий": {"singular": "за́мку", "plural": "замкі́в"},
                        "давальний": {"singular": "за́мку / за́мкові", "plural": "замка́м"},
                        "знахідний": {"singular": "за́мок", "plural": "замки́"},
                        "орудний": {"singular": "за́мком", "plural": "замка́ми"},
                        "місцевий": {"singular": "у за́мку", "plural": "замка́х"},
                        "кличний": {"singular": "за́мку", "plural": "замки́"},
                    },
                },
            },
            "sections": {
                "synonyms": {
                    "source": "СУМ-20",
                    "items": ["фортеця", "твердиня", "палац"],
                },
            },
            "examples": [
                {
                    "uk": "Старовинний за́мок височів над долиною.",
                    "en": "The ancient castle towered over the valley.",
                    "source": "СУМ-11",
                }
            ],
            "distinction_note": "Не плутати з омографом «замо́к» (наголос на другому складі: пристрій для замикання дверей).",
        },
        {
            "headword": "замо́к",
            "short_label": "пристрій для замикання",
            "gloss": "lock (door lock, padlock)",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
            },
            "pronunciation": {
                "ipa": "[zɐˈmɔk]",
                "source": "kaikki/Wiktionary",
            },
            "stress": {
                "form": "замо́к",
                "source": "ukrainian-word-stress",
            },
            "morphology": {
                "pos": "іменник",
                "paradigm": {
                    "kind": "noun",
                    "cases": {
                        "називний": {"singular": "замо́к", "plural": "замки́"},
                        "родовий": {"singular": "замка́", "plural": "замкі́в"},
                        "давальний": {"singular": "замку́ / замко́ві", "plural": "замка́м"},
                        "знахідний": {"singular": "замо́к", "plural": "замки́"},
                        "орудний": {"singular": "замко́м", "plural": "замка́ми"},
                        "місцевий": {"singular": "у замку́", "plural": "замка́х"},
                        "кличний": {"singular": "замку́", "plural": "замки́"},
                    },
                },
            },
            "sections": {
                "synonyms": {
                    "source": "СУМ-20",
                    "items": ["колодка"],
                },
            },
            "examples": [
                {
                    "uk": "Він замкнув двері на замо́к.",
                    "en": "He locked the door with a lock.",
                    "source": "СУМ-11",
                }
            ],
            "distinction_note": "Не плутати з омографом «за́мок» (наголос на першому складі: фортеця або середньовічний палац).",
        },
    ],
    "атлас": [
        {
            "headword": "а́тлас",
            "short_label": "збірник карт",
            "gloss": "atlas (bound collection of maps)",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
            },
            "pronunciation": {
                "ipa": "[ˈatɫɐs]",
                "source": "VESUM",
            },
            "stress": {
                "form": "а́тлас",
                "source": "ukrainian-word-stress",
            },
            "morphology": {
                "pos": "іменник",
                "paradigm": {
                    "kind": "noun",
                    "cases": {
                        "називний": {"singular": "а́тлас", "plural": "а́тласи"},
                        "родовий": {"singular": "а́тласу", "plural": "а́тласів"},
                        "давальний": {"singular": "а́тласу / а́тласові", "plural": "а́тласам"},
                        "знахідний": {"singular": "а́тлас", "plural": "а́тласи"},
                        "орудний": {"singular": "а́тласом", "plural": "а́тласами"},
                        "місцевий": {"singular": "в а́тласі", "plural": "а́тласах"},
                        "кличний": {"singular": "а́тласе", "plural": "а́тласи"},
                    },
                },
            },
            "distinction_note": "Не плутати з омографом «атла́с» (наголос на другому складі: шовкова тканина).",
        },
        {
            "headword": "атла́с",
            "short_label": "тканина",
            "gloss": "satin (glossy silk fabric)",
            "pos": "noun",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
            },
            "pronunciation": {
                "ipa": "[ɐtˈɫas]",
                "source": "VESUM",
            },
            "stress": {
                "form": "атла́с",
                "source": "ukrainian-word-stress",
            },
            "morphology": {
                "pos": "іменник",
                "paradigm": {
                    "kind": "noun",
                    "cases": {
                        "називний": {"singular": "атла́с", "plural": "атла́си"},
                        "родовий": {"singular": "атла́су", "plural": "атла́сів"},
                        "давальний": {"singular": "атла́су / атла́сові", "plural": "атла́сам"},
                        "знахідний": {"singular": "атла́с", "plural": "атла́си"},
                        "орудний": {"singular": "атла́сом", "plural": "атла́сами"},
                        "місцевий": {"singular": "в атла́сі", "plural": "атла́сах"},
                        "кличний": {"singular": "атла́се", "plural": "атла́си"},
                    },
                },
            },
            "distinction_note": "Не плутати з омографом «а́тлас» (наголос на першому складі: збірник географічних або анатомічних карт).",
        },
    ],
}


def build_heteronyms_for_lemma(lemma: str) -> list[dict[str, Any]] | None:
    """Return curated or auto-extracted heteronym definitions for lemma."""
    if lemma in CURATED_HETERONYMS:
        return CURATED_HETERONYMS[lemma]

    sources_db = _resolve_sources_db()
    if not sources_db.is_file():
        return None

    try:
        conn = sqlite3.connect(sources_db)
        cur = conn.cursor()
        row = cur.execute("SELECT definition FROM sum11 WHERE word = ?", (lemma,)).fetchone()
        conn.close()
        if not row:
            return None
        parsed = parse_sum11_heteronyms(lemma, row[0])
        if len(parsed) < 2:
            return None
        items = []
        for p in parsed:
            head = p["head"]
            items.append(
                {
                    "headword": head,
                    "gloss": p["body"][:120].strip(),
                    "short_label": p["grammar"],
                    "pos": "noun" if "ч" in p["grammar"] or "ж" in p["grammar"] or "с" in p["grammar"] else None,
                    "distinction_note": f"Омограф зі словом «{lemma}» (наголос: {head}).",
                }
            )
        return items
    except Exception as e:
        print(f"Warning: error parsing heteronyms for {lemma}: {e}", file=sys.stderr)
        return None


def _resolve_atlas_db(custom_path: str | Path | None = None) -> Path:
    if custom_path:
        p = Path(custom_path)
        if p.is_file():
            return p
    env_path = os.environ.get("ATLAS_DB_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)
    local = ROOT / "data" / "atlas.db"
    if local.is_file():
        return local
    primary = _resolve_primary_checkout()
    if primary:
        prim_db = primary / "data" / "atlas.db"
        if prim_db.is_file():
            return prim_db
    return local


def _resolve_manifest_path(custom_path: str | Path | None = None) -> Path | None:
    if custom_path:
        p = Path(custom_path)
        if p.is_file():
            return p
    local = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
    if local.is_file():
        return local
    primary = _resolve_primary_checkout()
    if primary:
        prim_m = primary / "site" / "src" / "data" / "lexicon-manifest.json"
        if prim_m.is_file():
            return prim_m
    return None


def apply_heteronyms(
    db_path: Path | None = None,
    manifest_path: Path | None = None,
    lemmas: list[str] | None = None,
) -> dict[str, int]:
    """Apply heteronym disambiguation and distinction notes to atlas.db and manifest."""
    target_lemmas = lemmas or list(CURATED_HETERONYMS.keys())
    db_file = _resolve_atlas_db(db_path)
    updated_counts = {"db_payloads": 0, "db_articles": 0, "manifest_entries": 0}

    if db_file.is_file():
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        for lemma in target_lemmas:
            heteronyms = build_heteronyms_for_lemma(lemma)
            if not heteronyms:
                continue
            row = cur.execute(
                "SELECT payload_json FROM article_payloads WHERE slug = ?",
                (lemma,),
            ).fetchone()
            if row:
                payload = json.loads(row[0])
                payload["heteronyms"] = heteronyms
                if lemma == "город":
                    payload["gloss"] = "vegetable garden"
                    payload["pronunciation"] = {"ipa": "[ɦɔˈrɔd]", "source": "VESUM"}
                    payload["heritage_status"] = {
                        "classification": "standard",
                        "is_russianism": False,
                        "russian_shadow": False,
                        "vesum_attested": True,
                        "warning_severity": None,
                        "calque_warning": None,
                    }
                    if "enrichment" in payload and isinstance(payload["enrichment"], dict):
                        payload["enrichment"]["stress"] = {
                            "form": "горо́д",
                            "source": "ukrainian-word-stress",
                            "ipa": "[ɦɔˈrɔd]",
                        }
                    if "sections" in payload and isinstance(payload["sections"], dict):
                        payload["sections"]["synonyms"] = {
                            "source": "СУМ-20",
                            "items": ["грядка", "городчик"],
                        }
                    payload["distinction_note"] = heteronyms[0].get("distinction_note")
                    cur.execute(
                        "UPDATE articles SET display_head = ?, heritage_classification = 'standard' WHERE slug = ?",
                        ("горо́д", lemma),
                    )
                    updated_counts["db_articles"] += 1
                elif lemma == "замок" or lemma == "атлас":
                    payload["distinction_note"] = heteronyms[0].get("distinction_note")

                cur.execute(
                    "UPDATE article_payloads SET payload_json = ? WHERE slug = ?",
                    (json.dumps(payload, ensure_ascii=False), lemma),
                )
                updated_counts["db_payloads"] += 1
        conn.commit()
        conn.close()

    m_file = _resolve_manifest_path(manifest_path)
    if m_file and m_file.is_file():
        try:
            with open(m_file, encoding="utf-8") as f:
                manifest_data = json.load(f)
            entries = manifest_data.get("entries", [])
            manifest_dirty = False
            for e in entries:
                lemma = e.get("lemma")
                if lemma in target_lemmas:
                    heteronyms = build_heteronyms_for_lemma(lemma)
                    if heteronyms:
                        e["heteronyms"] = heteronyms
                        if lemma == "город":
                            e["gloss"] = "vegetable garden"
                            e["pronunciation"] = {"ipa": "[ɦɔˈrɔd]", "source": "VESUM"}
                            e["heritage_status"] = {
                                "classification": "standard",
                                "is_russianism": False,
                                "russian_shadow": False,
                                "vesum_attested": True,
                                "warning_severity": None,
                                "calque_warning": None,
                            }
                            if "enrichment" in e and isinstance(e["enrichment"], dict):
                                e["enrichment"]["stress"] = {
                                    "form": "горо́д",
                                    "source": "ukrainian-word-stress",
                                    "ipa": "[ɦɔˈrɔd]",
                                }
                            if "sections" in e and isinstance(e["sections"], dict):
                                e["sections"]["synonyms"] = {
                                    "source": "СУМ-20",
                                    "items": ["грядка", "городчик"],
                                }
                            e["distinction_note"] = heteronyms[0].get("distinction_note")
                        elif lemma in ("замок", "атлас"):
                            e["distinction_note"] = heteronyms[0].get("distinction_note")
                        manifest_dirty = True
                        updated_counts["manifest_entries"] += 1
            if manifest_dirty:
                with open(m_file, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        except Exception as ex:
            print(f"Warning: could not update manifest at {m_file}: {ex}", file=sys.stderr)

    return updated_counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich and disambiguate heteronyms in Word Atlas")
    parser.add_argument("--lemma", help="Single lemma to inspect or enrich")
    parser.add_argument("--scan", action="store_true", help="Scan sources.db for all candidate heteronyms")
    parser.add_argument("--apply", action="store_true", help="Apply heteronym updates to atlas.db and manifest")
    parser.add_argument("--db", help="Path to atlas.db")
    parser.add_argument("--manifest", help="Path to lexicon-manifest.json")
    args = parser.parse_args()

    if args.apply:
        counts = apply_heteronyms(db_path=args.db, manifest_path=args.manifest)
        print(f"Applied heteronym updates: {counts}")
        return 0

    if args.lemma:
        res = build_heteronyms_for_lemma(args.lemma)
        if res:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"No heteronyms found for {args.lemma}")
        return 0

    if args.scan:
        sources_db = _resolve_sources_db()
        print(f"Scanning {sources_db}...")
        conn = sqlite3.connect(sources_db)
        cur = conn.cursor()
        rows = cur.execute("SELECT word, definition FROM sum11").fetchall()
        heteronym_count = 0
        for w, defn in rows:
            parsed = parse_sum11_heteronyms(w, defn)
            if len(parsed) >= 2:
                heteronym_count += 1
                if heteronym_count <= 20:
                    heads = [p["head"] for p in parsed]
                    print(f"  {w}: {', '.join(heads)}")
        conn.close()
        print(f"Total heteronyms detected: {heteronym_count}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
