#!/usr/bin/env python3
"""Read-only evidence pack for Atlas English-anchor curation (#5133).

This deliberately re-runs the Atlas audit command rather than accepting a
hand-maintained lemma list.  It supplies the two source signals the Stage 1
worksheet records for each still-unglossed entry:

* every Балла EN→UK headword whose definition contains the lemma as a whole
  Ukrainian word; and
* the matching СУМ-11 row, including its sovietization marker.

The module never writes a manifest or a source database.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import sqlite3
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.audit_atlas_poc_richness import audit_manifest
from scripts.lexicon import enrich_manifest
from scripts.verification.vesum import verify_words

AUDIT_COMMAND = (
    ".venv/bin/python",
    "scripts/audit/audit_atlas_poc_richness.py",
    "--max-search-no-visible-gloss",
    "0",
    "--max-old-gate-no-english-anchor",
    "0",
    "--max-poc-thin-pages",
    "900",
    "--format",
    "tsv",
    "--limit",
    "300",
)
SOURCES_DB = ROOT / "data" / "sources.db"
UKRAINIAN_LETTERS = "А-Яа-яЄєІіЇїҐґ"
MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
WORKSHEET = ROOT / "data" / "lexicon" / "anchor_curation_worksheet.yaml"


@dataclass(frozen=True)
class AtlasEntry:
    """The stable fields required by the Stage 1 worksheet."""

    lemma: str
    cefr: str
    url_slug: str


@dataclass(frozen=True)
class Sum11Evidence:
    """A raw source row; curators paraphrase its primary sense in the worksheet."""

    definition: str
    sovietization_risk: int
    sovietization_keywords: str


@dataclass(frozen=True)
class Proposal:
    """A human-curated anchor and paraphrase, never a generated translation."""

    anchor: str | None
    sum11_sense: str
    confidence: str
    notes: str | None = None


# These proposals are deliberately separate from the source extraction below:
# a suggestion is never selected automatically from a Балла headword. Entries
# absent here and from СУМ-11 are explicit low-confidence abstentions.
PROPOSALS: dict[str, Proposal] = {
    "бажане": Proposal("desired thing", "Something wanted or wished for.", "medium", "Substantivized neuter adjective; Балла hint `wish` sense-checked."),
    "вітамінізація": Proposal("vitamin fortification", "Adding vitamins to food or a diet.", "medium", "No exact СУМ-11 headword; Балла hint `fortification` sense-checked."),
    "гейби": Proposal("as if", "A dialectal conjunction meaning as if or like.", "high"),
    "генрі": Proposal("henry", "The SI unit of electrical inductance.", "medium", "No exact СУМ-11 headword; Балла headword `henry` is the unit, not the name."),
    "гіповітаміноз": Proposal("vitamin deficiency", "An illness caused by insufficient vitamins.", "high"),
    "денно": Proposal("daily", "Every day; also, for a working day.", "high"),
    "дитяча": Proposal("nursery", "A room for children.", "medium", "Substantivized feminine adjective; `bathinette` is a noisy Балла match."),
    "домашні": Proposal("household", "People or things belonging to the home.", "medium", "Substantivized plural adjective; Балла home/household hints sense-checked."),
    "достоту": Proposal("exactly", "Exactly; truly or really.", "high"),
    "дурненький": Proposal("silly", "Somewhat foolish; also an affectionate form of foolish.", "high"),
    "емоційно": Proposal("emotionally", "In an emotional manner.", "high"),
    "жертовність": Proposal("self-sacrifice", "Readiness to make a sacrifice for someone or something.", "high"),
    "зазвучати": Proposal("begin to sound", "To begin making or filling with sound.", "high"),
    "зайве": Proposal("the unnecessary", "Something extra or not needed.", "medium", "Substantivized neuter adjective; Балла `redundancy` hint sense-checked."),
    "замкнуто": Proposal("reservedly", "In a withdrawn or closed-off manner.", "high"),
    "замішування": Proposal("kneading", "The act of kneading dough; also mixing in.", "high"),
    "заповнений": Proposal("filled", "Filled or occupied with something.", "high"),
    "зарахований": Proposal("enrolled", "Accepted into an institution or counted as belonging to something.", "high"),
    "засвоюватися": Proposal("be absorbed", "To be taken in or assimilated by an organism.", "high"),
    "засинання": Proposal("falling asleep", "The process of falling asleep.", "high"),
    "захопливо": Proposal("engagingly", "In an exciting or captivating way.", "high"),
    "звикання": Proposal("getting used to", "The process of becoming accustomed to something.", "high"),
    "здирати": Proposal("strip off", "To remove or tear off an outer layer.", "high"),
    "зернові": Proposal("cereals", "Grain crops used for food.", "medium", "Substantivized plural adjective; Балла `cereal` hint sense-checked."),
    "знайома": Proposal("female acquaintance", "A woman whom one knows.", "medium", "Substantivized feminine adjective; Балла `acquaintance` hint sense-checked."),
    "зумовленість": Proposal("causal dependence", "Dependence on particular causes.", "high"),
    "книжно": Proposal("bookishly", "In a bookish or overly formal manner.", "high"),
    "комендантська": Proposal("curfew", "A restriction requiring people to stay indoors at set hours.", "medium", "Substantivized adjective in the fixed phrase комендантська година; Балла `curfew` hint sense-checked."),
    "компартія": Proposal("Communist Party", "An abbreviation for the Communist Party.", "high"),
    "компромісний": Proposal("compromise", "Formed by or involving a compromise.", "high"),
    "консервований": Proposal("canned", "Preserved for storage, especially as food.", "high"),
    "коротший": Proposal("shorter", "Having less length or duration.", "medium", "Comparative adjective; Балла `shorter` hint sense-checked."),
    "косуля": Proposal("wooden plough", "An archaic type of plough.", "high", "Primary СУМ-11 sense is the farming tool, not the roe deer cross-reference."),
    "коцик": Proposal("small rug", "A small rug or blanket.", "high"),
    "кровити": Proposal("bleed", "To bleed from a wound.", "high"),
    "ледве-ледве": Proposal("barely", "Only just; with difficulty.", "high"),
    "лиш": Proposal("only", "Only; merely.", "high"),
    "літа": Proposal("years", "A period measured in years; years of life.", "high"),
    "мовби": Proposal("as if", "As if; as though.", "high"),
    "мовбито": Proposal("as if", "As if; as though.", "high"),
    "можливе": Proposal("the possible", "Something that is possible.", "medium", "Substantivized neuter adjective; Балла `possible` hint sense-checked."),
    "найважливіше": Proposal("the most important", "The thing that matters most.", "medium", "Substantivized superlative; reviewed against the raw Балла hints rather than auto-copied."),
    "найраніше": Proposal("earliest", "Earlier than all others; at the earliest time.", "high"),
    "наслідковий": Proposal("result clause", "Relating to a result clause in grammar.", "high", "Primary СУМ-11 sense is the grammatical term."),
    "наші": Proposal("our people", "People regarded as one's own group.", "medium", "Substantivized plural possessive; Балла `ours` hint sense-checked."),
    "недосипання": Proposal("lack of sleep", "The state or result of not getting enough sleep.", "high"),
    "незвично": Proposal("unusually", "In an unfamiliar or strange way.", "high"),
    "ненадійно": Proposal("unreliably", "In an unreliable or insecure way.", "high"),
    "неперевершено": Proposal("superbly", "In an unsurpassed way.", "high"),
    "неповторно": Proposal("uniquely", "In a unique, unrepeatable way.", "high"),
    "нестямно": Proposal("frantically", "In an uncontrollably excited or distraught way.", "high"),
    "нехарактерний": Proposal("uncharacteristic", "Not typical or characteristic.", "medium", "No exact СУМ-11 headword; Балла `uncharacteristic` hint sense-checked."),
    "обгризання": Proposal("nibbling", "The act of gnawing or nibbling away.", "medium", "No exact СУМ-11 headword; Балла `nibble` hint sense-checked."),
    "обприскування": Proposal("spraying", "The act of spraying something with liquid.", "high"),
    "образливо": Proposal("offensively", "In an insulting or hurtful way.", "high"),
    "оброблений": Proposal("processed", "Treated, worked, or processed.", "high"),
    "обтирання": Proposal("rubbing down", "The act of rubbing or wiping the body or a surface.", "high"),
    "опірність": Proposal("resistance", "The ability to resist or withstand something.", "high"),
    "ослаблений": Proposal("weakened", "Made weak or less strong.", "high"),
    "пекельно": Proposal("hellishly", "In an extremely intense or dreadful way.", "high"),
    "повинно": Proposal("should", "Expressing what ought to happen or be done.", "high"),
    "повів": Proposal("gust", "A gust or faint waft of wind.", "high"),
    "повішати": Proposal("hang up", "To hang several things or hang things in different places.", "high"),
    "пожувати": Proposal("chew", "To chew for a while.", "high"),
    "політехніка": Proposal("polytechnic institute", "A polytechnic educational institution.", "high"),
    "попити": Proposal("drink some", "To drink for a while or drink some liquid.", "high"),
    "попрати": Proposal("wash clothes", "To wash clothes or other laundry.", "high"),
    "посмажити": Proposal("fry", "To fry something, often completely or in quantity.", "high"),
    "приглушено": Proposal("quietly", "In a muffled or subdued way.", "high"),
    "примружено": Proposal("squinting", "With the eyes partly closed or narrowed.", "high"),
    "приналежність": Proposal("belonging", "The state of belonging or being affiliated.", "high"),
    "пропущений": Proposal("omitted", "Missed, omitted, or allowed to pass through.", "high"),
    "півлітровий": Proposal("half-liter", "Having a capacity of half a liter.", "high"),
    "підпільно": Proposal("underground", "Secretly or illegally, outside official control.", "high"),
    "радикально": Proposal("radically", "In a thorough or fundamental way.", "high"),
    "рано-вранці": Proposal("early morning", "Very early, at dawn.", "high"),
    "рекомендуватися": Proposal("introduce oneself", "To give one's name when meeting someone.", "high"),
    "ризиковано": Proposal("riskily", "In a risky way.", "high"),
    "ринопластика": Proposal("rhinoplasty", "Surgery to reconstruct or reshape the nose.", "high"),
    "розгадування": Proposal("solving", "The act of guessing or solving something.", "high"),
    "розлитий": Proposal("spilled", "Poured or spread out over a surface.", "high"),
    "самонавіювання": Proposal("self-suggestion", "The practice of influencing oneself by suggestion.", "high"),
    "святково": Proposal("festively", "In a festive or celebratory way.", "high"),
    "свіжо": Proposal("freshly", "In a fresh or cool way; just recently.", "high"),
    "сигаретний": Proposal("cigarette", "Relating to cigarettes or their manufacture.", "high"),
    "синтезуватися": Proposal("become unified", "To become a unified whole; also, to form by synthesis.", "medium", "Primary СУМ-11 sense precedes the chemical sense."),
    "скрипт": Proposal("manuscript", "An archaic word for a manuscript.", "high"),
    "споживаний": Proposal("consumed", "Used up or consumed.", "high"),
    "спохмурніти": Proposal("become gloomy", "To become gloomy or dark; of a face, to frown.", "high"),
    "спричинений": Proposal("caused", "Brought about by something.", "high"),
    "спровокований": Proposal("provoked", "Brought about or triggered by someone or something.", "high"),
    "стало": Proposal("steadily", "In a steady or constant manner.", "high"),
    "стиглий": Proposal("ripe", "Fully ripe or mature.", "high"),
    "стильно": Proposal("stylishly", "In a stylish manner.", "high"),
    "супроводжуватися": Proposal("be accompanied", "To occur together with another action or event.", "high"),
    "сфокусуватися": Proposal("come into focus", "To bring oneself into focus.", "medium", "СУМ-11 points to the primary sense of фокусуватися."),
    "так-так": Proposal("yes indeed", "An emphatic affirmation; also an imitative ticking sound.", "high"),
    "теплоізоляція": Proposal("insulation", "Protection against heat loss or heat effects.", "high"),
    "тирозин": Proposal("tyrosine", "An amino acid found in almost all proteins.", "high"),
    "травмуватися": Proposal("get injured", "To receive an injury or become damaged.", "high"),
    "тривало": Proposal("for a long time", "For a long duration.", "high"),
    "тривожно": Proposal("anxiously", "In an anxious or alarmed way.", "high"),
    "триптофан": Proposal("tryptophan", "An essential amino acid found in many proteins.", "high"),
    "трубочка": Proposal("small tube", "A small tube or tube-shaped object.", "high"),
    "уникання": Proposal("avoidance", "The act of avoiding something.", "high"),
    "янголятко": Proposal("little angel", "An affectionate diminutive of angel.", "high"),
    "ять": Proposal("yat letter", "The name of a historical letter in the old alphabet.", "high"),
    "ідеально": Proposal("ideally", "In an ideal manner.", "high"),
    "інформування": Proposal("informing", "The act of giving information.", "high"),
    "інше": Proposal("the other thing", "Something else or different.", "medium", "Substantivized neuter adjective; Балла `other` hint sense-checked."),
    "інші": Proposal("others", "Other people or things.", "medium", "Substantivized plural adjective; Балла `other` hint sense-checked."),
}


def audit_entries() -> list[AtlasEntry]:
    """Return #5132's post-cached-fill ``search_no_visible_gloss`` bucket.

    #5132 deliberately committed only enrichment code, not a regenerated
    manifest. Consequently the literal issue command reports the pre-fill 196
    rows in this checkout. We first run that command as the required preamble,
    then apply its bounded cached-ukreng operation in memory and audit the
    resulting manifest through the same audit implementation. No cache or
    manifest file is written.
    """
    result = subprocess.run(
        AUDIT_COMMAND,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(result.stderr.strip() or "Atlas richness audit did not run")
    rows = csv.DictReader(result.stdout.splitlines(), delimiter="\t")
    prefill_entries = [
        AtlasEntry(
            lemma=row["lemma"].strip(),
            cefr=row["cefr"].strip(),
            url_slug=row["url_slug"].strip(),
        )
        for row in rows
        if row.get("bucket") == "search_no_visible_gloss"
    ]
    if len(prefill_entries) == 158:
        return prefill_entries
    if len(prefill_entries) != 196:
        raise RuntimeError(
            "Issue audit produced an unexpected search_no_visible_gloss count: "
            f"{len(prefill_entries)}"
        )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    working_manifest = copy.deepcopy(manifest)
    filled = 0
    for entry in working_manifest.get("entries", []):
        if not isinstance(entry, dict):
            continue
        lemma = str(entry.get("lemma") or "").strip()
        if not lemma:
            continue
        cache = enrich_manifest._load_slovnyk_cache_file(enrich_manifest._slovnyk_cache_path(lemma))
        filled += enrich_manifest._fill_learner_english_anchor_from_slovnyk_cache(entry, lemma, cache)

    summary = audit_manifest(working_manifest, sample_limit=300)
    postfill_rows = summary["samples"]["search_no_visible_gloss"]
    entries = [
        AtlasEntry(
            lemma=str(row["lemma"]).strip(),
            cefr=str(row["cefr"]).strip(),
            url_slug=str(row["url_slug"]).strip(),
        )
        for row in postfill_rows
    ]
    if filled != 38 or len(entries) != 158:
        raise RuntimeError(
            "Cached ukreng simulation did not reproduce #5132's 38-fill/158-remainder proof: "
            f"filled={filled}, remaining={len(entries)}"
        )
    if not entries:
        raise RuntimeError("Atlas audit returned no search_no_visible_gloss entries")
    if len({entry.lemma for entry in entries}) != len(entries):
        raise RuntimeError("Atlas audit returned duplicate lemmas")
    return entries


def _whole_ukrainian_word_pattern(lemma: str) -> re.Pattern[str]:
    escaped = re.escape(lemma)
    return re.compile(
        rf"(?<![{UKRAINIAN_LETTERS}]){escaped}(?![{UKRAINIAN_LETTERS}])",
        flags=re.IGNORECASE,
    )


def balla_reverse_hints(conn: sqlite3.Connection, lemma: str) -> list[str]:
    """Return raw EN headwords for whole-word matches in Балла definitions."""
    pattern = _whole_ukrainian_word_pattern(lemma)
    hints: list[str] = []
    seen: set[str] = set()
    for word, definition in conn.execute("SELECT word, definition FROM balla_en_uk ORDER BY id"):
        if not pattern.search(str(definition)):
            continue
        hint = str(word).strip()
        if hint and hint not in seen:
            seen.add(hint)
            hints.append(hint)
    return hints


def sum11_evidence(conn: sqlite3.Connection, lemma: str) -> Sum11Evidence | None:
    """Return the exact СУМ-11 row for a lemma, if the read-only DB has one."""
    row = conn.execute(
        """
        SELECT definition, sovietization_risk, sovietization_keywords
        FROM sum11
        WHERE word = ? COLLATE NOCASE
        ORDER BY id
        LIMIT 1
        """,
        (lemma,),
    ).fetchone()
    if row is None:
        return None
    return Sum11Evidence(
        definition=str(row[0]),
        sovietization_risk=int(row[1]),
        sovietization_keywords=str(row[2]),
    )


def vesum_verified(lemmas: Iterable[str]) -> dict[str, bool]:
    """Verify every exact lemma surface through the repository VESUM adapter."""
    unique_lemmas = list(dict.fromkeys(lemmas))
    results = verify_words(unique_lemmas)
    return {lemma: bool(results.get(lemma)) for lemma in unique_lemmas}


def evidence_records() -> list[dict[str, Any]]:
    """Build records suitable for source-grounded panel review; do not curate them."""
    entries = audit_entries()
    verified = vesum_verified(entry.lemma for entry in entries)
    records: list[dict[str, Any]] = []
    with sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True) as conn:
        for entry in entries:
            sum11 = sum11_evidence(conn, entry.lemma)
            records.append(
                {
                    "lemma": entry.lemma,
                    "cefr": entry.cefr,
                    "url_slug": entry.url_slug,
                    "vesum_verified": verified[entry.lemma],
                    "balla_reverse_hints": balla_reverse_hints(conn, entry.lemma),
                    "sum11_definition": sum11.definition if sum11 else None,
                    "sovietization_risk": sum11.sovietization_risk if sum11 else None,
                    "sovietization_keywords": sum11.sovietization_keywords if sum11 else None,
                }
            )
    return records


def _proposal_for(record: dict[str, Any]) -> Proposal:
    proposal = PROPOSALS.get(str(record["lemma"]))
    if proposal is not None:
        return proposal
    if record["sum11_definition"]:
        raise RuntimeError(f"Missing curated proposal for СУМ-11-backed lemma {record['lemma']}")
    return Proposal(
        None,
        "No exact СУМ-11 headword.",
        "low",
        "No sense-specific source supports an anchor; retained for reviewer adjudication.",
    )


def worksheet_payload() -> dict[str, Any]:
    """Return the complete, fail-closed Stage 1 curation worksheet."""
    records = evidence_records()
    worksheet_records: list[dict[str, Any]] = []
    for record in records:
        if not record["vesum_verified"]:
            raise RuntimeError(f"VESUM did not verify {record['lemma']}")
        proposal = _proposal_for(record)
        if proposal.anchor is None and proposal.confidence != "low":
            raise RuntimeError(f"Anchor abstention for {record['lemma']} must be low confidence")
        if proposal.anchor is not None:
            words = proposal.anchor.split()
            if not 1 <= len(words) <= 4:
                raise RuntimeError(f"Anchor for {record['lemma']} must have 1–4 words")
        item: dict[str, Any] = {
            "lemma": record["lemma"],
            "cefr": record["cefr"],
            "url_slug": record["url_slug"],
            "proposed_anchor": proposal.anchor,
            "balla_reverse_hints": record["balla_reverse_hints"],
            "sum11_sense": proposal.sum11_sense,
            "vesum_verified": True,
            "confidence": proposal.confidence,
        }
        if record["sovietization_risk"] and int(record["sovietization_risk"]) > 0:
            item["sovietization_flag"] = True
        if proposal.notes:
            item["notes"] = proposal.notes
        worksheet_records.append(item)

    lemmas = [str(record["lemma"]) for record in worksheet_records]
    if len(worksheet_records) != 158 or len(lemmas) != len(set(lemmas)):
        raise RuntimeError("Worksheet must contain exactly 158 unique lemmas")
    return {
        "schema_version": 1,
        "meta": {
            "issue": "#5133",
            "stage": "1 — proposals only; not consumed by the Atlas manifest",
            "source_scope": "data/sources.db read-only: Балла EN→UK whole-word hints and СУМ-11 senses",
            "audit_command": " ".join(AUDIT_COMMAND),
            "audit_reconciliation": (
                "Literal audit reports 196 because #5132 shipped cached-ukreng fill code without a regenerated "
                "manifest. This worksheet deterministically simulates only that cached 38-fill operation in memory, "
                "then retains its 158-entry remainder; no manifest or cache is written."
            ),
            "anchor_rule": (
                "Anchors are curator proposals, never copied automatically from Балла. Null plus low confidence is the "
                "fail-closed outcome when no sense-specific source supports an anchor."
            ),
        },
        "records": worksheet_records,
    }


def write_worksheet(path: Path = WORKSHEET) -> None:
    """Materialize the review-only worksheet from verified, read-only evidence."""
    payload = worksheet_payload()
    rendered = yaml.safe_dump(
        payload,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=100,
    )
    path.write_text(rendered, encoding="utf-8")


def _format_panel_record(record: dict[str, Any]) -> str:
    hints = ", ".join(record["balla_reverse_hints"]) or "(none)"
    sum11 = record["sum11_definition"] or "(no СУМ-11 entry)"
    risk = record["sovietization_risk"]
    return (
        f"{record['lemma']} [{record['cefr']}; slug={record['url_slug']}; "
        f"VESUM={record['vesum_verified']}; sovietization_risk={risk}]\n"
        f"  Балла raw hints: {hints}\n"
        f"  СУМ-11: {sum11}"
    )


def _format_compact_record(record: dict[str, Any]) -> str:
    hints = ", ".join(record["balla_reverse_hints"]) or "(none)"
    definition = record["sum11_definition"] or "(no СУМ-11 entry)"
    source_excerpt = " ".join(str(definition).split())[:700]
    return (
        f"{record['lemma']}\t{record['cefr']}\t{record['url_slug']}\t"
        f"risk={record['sovietization_risk']}\tballa={hints}\tSUM-11={source_excerpt}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel-batch",
        type=int,
        default=0,
        help="Zero-based batch number for text output (requires --batch-size).",
    )
    parser.add_argument("--batch-size", type=int, default=158)
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit one tab-separated source-evidence line per record for curation.",
    )
    parser.add_argument(
        "--write-worksheet",
        action="store_true",
        help="Write the verified Stage 1 worksheet to data/lexicon/.",
    )
    args = parser.parse_args()
    if args.write_worksheet:
        write_worksheet()
        print(f"wrote {WORKSHEET.relative_to(ROOT)}")
        return 0
    records = evidence_records()
    start = args.panel_batch * args.batch_size
    batch = records[start : start + args.batch_size]
    if not batch:
        raise SystemExit(f"No evidence records in batch {args.panel_batch}")
    if args.compact:
        print("\n".join(_format_compact_record(record) for record in batch))
        return 0
    print("#5133 English learner-anchor evidence pack (read-only source data)")
    print(
        "Recommend a 1–4 word lower-case English learner anchor and a one-line "
        "English paraphrase of the primary СУМ-11 sense. Do not copy Балла hints "
        "without sense-checking; flag unclear records low."
    )
    print()
    print("\n\n".join(_format_panel_record(record) for record in batch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
