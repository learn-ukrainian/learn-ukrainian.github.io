#!/usr/bin/env python3
"""Cross-module vocabulary progression analytics."""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import statistics
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

SCRIPT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("VOCAB_PROGRESSION_PROJECT_ROOT", str(SCRIPT_ROOT))).resolve()

SCRIPTS_DIR = SCRIPT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit.config import get_word_target

CORE_LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")
CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
PAREN_GLOSS_RE = re.compile(r"\s*\([^)]*\)")
EDGE_PUNCT_RE = re.compile(r"^[^\w'’-]+|[^\w'’-]+$")
APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "′": "'"})


def _strip_stress(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if char not in {"\u0301", "\u0300"})
    return unicodedata.normalize("NFC", stripped)


def normalize_surface(text: str) -> str:
    """Normalize a surface form for DB lookups and deduplication."""
    cleaned = unicodedata.normalize("NFKC", text).translate(APOSTROPHE_TRANSLATION)
    cleaned = _strip_stress(cleaned).lower()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = EDGE_PUNCT_RE.sub("", cleaned)
    return cleaned.strip()


def parse_plan_terms(value: Any) -> list[str]:
    """Flatten vocabulary_hints/prior_words payloads into normalized terms."""
    terms: list[str] = []
    if value is None:
        return terms
    if isinstance(value, str):
        without_gloss = PAREN_GLOSS_RE.sub("", value)
        for part in re.split(r"\s*/\s*", without_gloss):
            normalized = normalize_surface(part)
            if normalized:
                terms.append(normalized)
        return terms
    if isinstance(value, list):
        for item in value:
            terms.extend(parse_plan_terms(item))
        return terms
    if isinstance(value, dict):
        for item in value.values():
            terms.extend(parse_plan_terms(item))
    return terms


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_vocab_entries(path: Path) -> list[dict[str, Any]]:
    data = _load_yaml(path)
    if data is None:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        payload = data.get("vocabulary", data.get("items", []))
        return [item for item in payload if isinstance(item, dict)]
    return []


def _chunked(items: list[str], size: int = 500) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    curriculum_root: Path
    curriculum_manifest: Path
    vesum_db: Path
    sources_db: Path

    @classmethod
    def from_root(cls, root: Path | None = None) -> ProjectPaths:
        resolved_root = Path(root or DATA_ROOT).resolve()
        return cls(
            root=resolved_root,
            curriculum_root=resolved_root / "curriculum" / "l2-uk-en",
            curriculum_manifest=resolved_root / "curriculum" / "l2-uk-en" / "curriculum.yaml",
            vesum_db=resolved_root / "data" / "vesum.db",
            sources_db=resolved_root / "data" / "sources.db",
        )


@dataclass(frozen=True)
class ModuleRecord:
    level: str
    slug: str
    position: int
    plan_path: Path
    vocab_path: Path


@dataclass
class GapRecord:
    term: str
    lookup_key: tuple[str, str]
    references: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class PrematureRecord:
    lemma: str
    level: str
    module: str
    surface_forms: list[str]


@dataclass
class WordProgression:
    lemma: str
    first_intro: str
    modules: list[str]
    positions: list[int]
    rep_count: int
    spacing: list[int]
    mean_spacing: float | None
    median_spacing: float | None
    surface_forms: list[str]
    cefr_level: str | None = None


@dataclass
class NonVesumRecord:
    surface: str
    modules: list[str]
    positions: list[int]
    raw_forms: list[str]


@dataclass
class LevelAnalysis:
    level: str
    target_lemmas: int
    modules: list[ModuleRecord]
    word_progressions: list[WordProgression]
    gaps: list[GapRecord]
    premature: list[PrematureRecord]
    non_vesum: list[NonVesumRecord]
    unique_lemma_count: int
    module_progression_delta: dict[str, dict[str, int]]
    worst_paced_word: WordProgression | None = None


class VesumLookup:
    """Thin cached VESUM lookup layer."""

    def __init__(self, db_path: Path):
        if not db_path.exists():
            raise FileNotFoundError(f"VESUM database not found at {db_path}")
        self._conn = sqlite3.connect(str(db_path))
        self._cache: dict[str, str | None] = {}

    def close(self) -> None:
        self._conn.close()

    def prefetch(self, surfaces: Iterable[str]) -> None:
        pending = sorted(
            {
                normalize_surface(surface)
                for surface in surfaces
                if normalize_surface(surface)
                and " " not in normalize_surface(surface)
                and "/" not in normalize_surface(surface)
                and normalize_surface(surface) not in self._cache
            }
        )
        for chunk in _chunked(pending):
            placeholders = ",".join("?" for _ in chunk)
            rows = self._conn.execute(
                f"SELECT word_form, lemma FROM forms WHERE word_form IN ({placeholders})",
                chunk,
            ).fetchall()
            found = {
                normalize_surface(word_form): normalize_surface(lemma)
                for word_form, lemma in rows
            }
            for surface in chunk:
                self._cache[surface] = found.get(surface)

    def lemma_for(self, surface: str) -> str | None:
        normalized = normalize_surface(surface)
        if normalized in self._cache:
            cached = self._cache[normalized]
            if cached is not None:
                return cached
        if not normalized or " " in normalized or "/" in normalized:
            self._cache[normalized] = None
            return None

        row = self._conn.execute(
            "SELECT lemma FROM forms WHERE word_form = ? COLLATE NOCASE LIMIT 1",
            (normalized,),
        ).fetchone()
        lemma = normalize_surface(row[0]) if row else None
        self._cache[normalized] = lemma
        return lemma


class PulsLookup:
    """Thin cached PULS CEFR lookup layer."""

    def __init__(self, db_path: Path):
        if not db_path.exists():
            raise FileNotFoundError(f"Sources database not found at {db_path}")
        self._conn = sqlite3.connect(str(db_path))
        self._cache: dict[str, str | None] = {}

    def close(self) -> None:
        self._conn.close()

    def prefetch(self, lemmas: Iterable[str]) -> None:
        pending = sorted(
            {
                normalize_surface(lemma)
                for lemma in lemmas
                if normalize_surface(lemma) and normalize_surface(lemma) not in self._cache
            }
        )
        for chunk in _chunked(pending):
            placeholders = ",".join("?" for _ in chunk)
            rows = self._conn.execute(
                f"SELECT word, level FROM puls_cefr WHERE word IN ({placeholders})",
                chunk,
            ).fetchall()
            bucket: dict[str, list[str]] = defaultdict(list)
            for word, level in rows:
                normalized_word = normalize_surface(word)
                normalized_level = str(level).upper()
                if normalized_level in CEFR_ORDER:
                    bucket[normalized_word].append(normalized_level)
            for lemma in chunk:
                levels = sorted(set(bucket.get(lemma, [])), key=CEFR_ORDER.get)
                self._cache[lemma] = levels[0] if levels else None

    def level_for(self, lemma: str) -> str | None:
        normalized = normalize_surface(lemma)
        if normalized in self._cache:
            cached = self._cache[normalized]
            if cached is not None:
                return cached
        rows = self._conn.execute(
            "SELECT level FROM puls_cefr WHERE word = ? COLLATE NOCASE",
            (normalized,),
        ).fetchall()
        levels = sorted(
            {
                str(row[0]).upper()
                for row in rows
                if str(row[0]).upper() in CEFR_ORDER
            },
            key=CEFR_ORDER.get,
        )
        result = levels[0] if levels else None
        self._cache[normalized] = result
        return result


def _curriculum_modules(paths: ProjectPaths, level: str) -> list[str]:
    curriculum = _load_yaml(paths.curriculum_manifest) or {}
    modules = curriculum.get("levels", {}).get(level, {}).get("modules", [])
    if not isinstance(modules, list):
        raise ValueError(f"Invalid module list for level {level}")
    return [str(item).split("#", 1)[0].strip() for item in modules if str(item).strip()]


def _module_records(paths: ProjectPaths, level: str) -> list[ModuleRecord]:
    records: list[ModuleRecord] = []
    for index, slug in enumerate(_curriculum_modules(paths, level), start=1):
        records.append(
            ModuleRecord(
                level=level,
                slug=slug,
                position=index,
                plan_path=paths.curriculum_root / "plans" / level / f"{slug}.yaml",
                vocab_path=paths.curriculum_root / level / "vocabulary" / f"{slug}.yaml",
            )
        )
    return records


def _is_premature(level: str, candidate_level: str | None) -> bool:
    if candidate_level is None:
        return False
    return CEFR_ORDER[candidate_level] > CEFR_ORDER[level.upper()]


def _mean(values: Iterable[int]) -> float | None:
    items = list(values)
    if not items:
        return None
    return float(statistics.mean(items))


def _median(values: Iterable[int]) -> float | None:
    items = list(values)
    if not items:
        return None
    return float(statistics.median(items))


def analyze_level(level: str, paths: ProjectPaths | None = None) -> LevelAnalysis:
    """Analyze vocabulary progression for a single CEFR level."""
    normalized_level = level.lower()
    if normalized_level not in CORE_LEVELS:
        raise ValueError(f"Unsupported level: {level}")

    resolved_paths = paths or ProjectPaths.from_root()
    modules = _module_records(resolved_paths, normalized_level)
    if not modules:
        raise ValueError(f"No modules found for level {level}")

    vesum = VesumLookup(resolved_paths.vesum_db)
    puls = PulsLookup(resolved_paths.sources_db)

    lemma_occurrences: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    lemma_positions: dict[str, dict[str, int]] = defaultdict(dict)
    lemma_cefr: dict[str, str | None] = {}
    premature_modules: dict[str, set[str]] = defaultdict(set)
    plan_candidates: dict[tuple[str, str], GapRecord] = {}
    non_vesum_occurrences: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    non_vesum_positions: dict[str, dict[str, int]] = defaultdict(dict)
    seen_lemma_keys: set[tuple[str, str]] = set()
    seen_surface_keys: set[tuple[str, str]] = set()
    prepared_vocab: dict[str, list[tuple[str, str]]] = {}
    prepared_plan_terms: dict[str, list[tuple[str, str]]] = {}
    lemma_candidates: set[str] = set()

    try:
        for module in modules:
            module_vocab: list[tuple[str, str]] = []
            for entry in _load_vocab_entries(module.vocab_path):
                surface_raw = str(entry.get("word", "")).strip()
                if not surface_raw:
                    continue

                normalized_surface = normalize_surface(surface_raw)
                if not normalized_surface:
                    continue
                module_vocab.append((surface_raw, normalized_surface))
                lemma_candidates.add(normalized_surface)
            prepared_vocab[module.slug] = module_vocab

            plan_data = _load_yaml(module.plan_path) or {}
            module_terms: list[tuple[str, str]] = []
            for key in ("vocabulary_hints", "prior_words"):
                for term in parse_plan_terms(plan_data.get(key)):
                    module_terms.append((key, term))
                    lemma_candidates.add(term)
            prepared_plan_terms[module.slug] = module_terms

        vesum.prefetch(lemma_candidates)

        for module in modules:
            for surface_raw, normalized_surface in prepared_vocab[module.slug]:
                lemma = vesum.lemma_for(normalized_surface)
                if lemma:
                    lemma_occurrences[lemma][module.slug].add(surface_raw)
                    lemma_positions[lemma][module.slug] = module.position
                    seen_lemma_keys.add(("lemma", lemma))
                else:
                    non_vesum_occurrences[normalized_surface][module.slug].add(surface_raw)
                    non_vesum_positions[normalized_surface][module.slug] = module.position
                    seen_surface_keys.add(("surface", normalized_surface))

        puls.prefetch(lemma_occurrences.keys())

        for module in modules:
            for lemma in lemma_occurrences:
                if module.slug not in lemma_occurrences[lemma]:
                    continue
                if lemma not in lemma_cefr:
                    lemma_cefr[lemma] = puls.level_for(lemma)
                if _is_premature(normalized_level, lemma_cefr[lemma]):
                    premature_modules[module.slug].add(lemma)

            for key, term in prepared_plan_terms[module.slug]:
                lookup_lemma = vesum.lemma_for(term)
                lookup_key = ("lemma", lookup_lemma) if lookup_lemma else ("surface", term)
                gap = plan_candidates.setdefault(lookup_key, GapRecord(term=term, lookup_key=lookup_key))
                gap.references.append((module.slug, key))
    finally:
        vesum.close()
        puls.close()

    word_progressions: list[WordProgression] = []
    intro_well_paced_counts: dict[str, int] = defaultdict(int)

    for lemma, module_forms in lemma_occurrences.items():
        ordered_modules = sorted(module_forms, key=lambda slug: lemma_positions[lemma][slug])
        positions = [lemma_positions[lemma][slug] for slug in ordered_modules]
        spacing = [current - previous for previous, current in pairwise(positions)]
        progression = WordProgression(
            lemma=lemma,
            first_intro=ordered_modules[0],
            modules=ordered_modules,
            positions=positions,
            rep_count=max(0, len(ordered_modules) - 1),
            spacing=spacing,
            mean_spacing=_mean(spacing),
            median_spacing=_median(spacing),
            surface_forms=sorted({form for forms in module_forms.values() for form in forms}),
            cefr_level=lemma_cefr.get(lemma),
        )
        if any(3 <= gap <= 5 for gap in spacing):
            intro_well_paced_counts[progression.first_intro] += 1
        word_progressions.append(progression)

    word_progressions.sort(key=lambda item: (item.positions[0], item.lemma))

    gaps: list[GapRecord] = []
    module_gap_counts: dict[str, int] = defaultdict(int)
    seen_gap_keys_per_module: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for gap in plan_candidates.values():
        if gap.lookup_key in seen_lemma_keys or gap.lookup_key in seen_surface_keys:
            continue
        gaps.append(gap)
        for module_slug, _source in gap.references:
            if gap.lookup_key not in seen_gap_keys_per_module[module_slug]:
                module_gap_counts[module_slug] += 1
                seen_gap_keys_per_module[module_slug].add(gap.lookup_key)
    gaps.sort(key=lambda item: (item.references[0][0], item.term))

    premature: list[PrematureRecord] = []
    for module in modules:
        for lemma in sorted(premature_modules.get(module.slug, set())):
            forms = sorted(lemma_occurrences[lemma][module.slug])
            premature.append(
                PrematureRecord(
                    lemma=lemma,
                    level=lemma_cefr.get(lemma) or "",
                    module=module.slug,
                    surface_forms=forms,
                )
            )

    non_vesum: list[NonVesumRecord] = []
    for surface, module_forms in non_vesum_occurrences.items():
        ordered_modules = sorted(module_forms, key=lambda slug: non_vesum_positions[surface][slug])
        non_vesum.append(
            NonVesumRecord(
                surface=surface,
                modules=ordered_modules,
                positions=[non_vesum_positions[surface][slug] for slug in ordered_modules],
                raw_forms=sorted({form for forms in module_forms.values() for form in forms}),
            )
        )
    non_vesum.sort(key=lambda item: (item.positions[0], item.surface))

    module_progression_delta: dict[str, dict[str, int]] = {}
    for module in modules:
        premature_count = len(premature_modules.get(module.slug, set()))
        gap_count = module_gap_counts.get(module.slug, 0)
        well_paced_count = intro_well_paced_counts.get(module.slug, 0)
        delta = (well_paced_count * 2) - gap_count - (premature_count * 5)
        module_progression_delta[module.slug] = {
            "delta": delta,
            "premature": premature_count,
            "gaps": gap_count,
            "well_paced": well_paced_count,
        }

    target_lemmas = get_word_target(normalized_level.upper())
    worst_paced_word = max(
        (item for item in word_progressions if item.spacing),
        key=lambda item: (
            item.median_spacing or 0.0,
            item.mean_spacing or 0.0,
            item.rep_count,
            item.lemma,
        ),
        default=None,
    )

    return LevelAnalysis(
        level=normalized_level,
        target_lemmas=target_lemmas,
        modules=modules,
        word_progressions=word_progressions,
        gaps=gaps,
        premature=premature,
        non_vesum=non_vesum,
        unique_lemma_count=len(word_progressions),
        module_progression_delta=module_progression_delta,
        worst_paced_word=worst_paced_word,
    )


def analyze_levels(levels: Iterable[str], paths: ProjectPaths | None = None) -> list[LevelAnalysis]:
    resolved_paths = paths or ProjectPaths.from_root()
    return [analyze_level(level, resolved_paths) for level in levels]


def module_progression_delta(
    level: str,
    module_slug: str,
    paths: ProjectPaths | None = None,
) -> dict[str, int]:
    analysis = analyze_level(level, paths)
    return analysis.module_progression_delta.get(module_slug, {"delta": 0, "premature": 0, "gaps": 0, "well_paced": 0})


def _fmt_number(value: float | None) -> str:
    if value is None:
        return "-"
    if value.is_integer():
        return str(int(value))
    return f"{value:.1f}"


def _top_reused(analysis: LevelAnalysis, limit: int = 50) -> list[WordProgression]:
    return sorted(
        (item for item in analysis.word_progressions if item.rep_count > 0),
        key=lambda item: (-item.rep_count, item.median_spacing or 0.0, item.positions[0], item.lemma),
    )[:limit]


def _one_and_done(analysis: LevelAnalysis, limit: int = 50) -> list[WordProgression]:
    return sorted(
        (item for item in analysis.word_progressions if item.rep_count == 0),
        key=lambda item: (item.positions[0], item.lemma),
    )[:limit]


def _lines_for_progressions(title: str, rows: list[WordProgression]) -> list[str]:
    lines = [f"## {title}"]
    if not rows:
        lines.append("")
        lines.append("_None_")
        return lines

    lines.extend(
        [
            "",
            "| Lemma | First Intro | Repeats | Modules | Mean Gap | Median Gap |",
            "|---|---|---:|---|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            "| {lemma} | {first_intro} | {rep_count} | {modules} | {mean_gap} | {median_gap} |".format(
                lemma=row.lemma,
                first_intro=row.first_intro,
                rep_count=row.rep_count,
                modules=", ".join(row.modules),
                mean_gap=_fmt_number(row.mean_spacing),
                median_gap=_fmt_number(row.median_spacing),
            )
        )
    return lines


def render_level_report(analysis: LevelAnalysis, gaps_only: bool = False) -> str:
    coverage = (analysis.unique_lemma_count / analysis.target_lemmas) * 100 if analysis.target_lemmas else 0.0
    repeated_with_good_spacing = sum(
        1 for item in analysis.word_progressions if any(3 <= gap <= 5 for gap in item.spacing)
    )

    lines = [
        f"# Vocabulary Progression Report: {analysis.level.upper()}",
        "",
        f"- Modules analyzed: {len(analysis.modules)}",
        f"- Unique lemmas: {analysis.unique_lemma_count} / {analysis.target_lemmas} target ({coverage:.1f}%)",
        f"- Premature higher-level lemmas: {len(analysis.premature)}",
        f"- Plan gaps: {len(analysis.gaps)}",
        f"- Non-VESUM surfaces: {len(analysis.non_vesum)}",
        f"- Well-paced repeated lemmas (3-5 module spacing): {repeated_with_good_spacing}",
    ]

    if analysis.worst_paced_word:
        lines.append(
            "- Worst-paced repeated word: "
            f"{analysis.worst_paced_word.lemma} "
            f"(median gap {_fmt_number(analysis.worst_paced_word.median_spacing)}, "
            f"modules {', '.join(analysis.worst_paced_word.modules)})"
        )

    lines.extend(["", "## First Introductions", "", "| Lemma | First Intro | Repeats | Later Modules |", "|---|---|---:|---|"])
    for row in analysis.word_progressions:
        later_modules = ", ".join(row.modules[1:]) if row.rep_count else "-"
        lines.append(f"| {row.lemma} | {row.first_intro} | {row.rep_count} | {later_modules} |")

    lines.extend(["", "## Gap Flags"])
    if analysis.gaps:
        lines.extend(["", "| Term | Lookup Key | Referenced By |", "|---|---|---|"])
        for gap in analysis.gaps:
            refs = ", ".join(f"{module} ({source})" for module, source in gap.references)
            lines.append(f"| {gap.term} | {gap.lookup_key[1]} | {refs} |")
    else:
        lines.extend(["", "_No gaps found._"])

    lines.extend(["", "## Premature Vocabulary"])
    if analysis.premature:
        lines.extend(["", "| Lemma | CEFR | Module | Surface Forms |", "|---|---|---|---|"])
        for item in analysis.premature:
            lines.append(
                f"| {item.lemma} | {item.level} | {item.module} | {', '.join(item.surface_forms)} |"
            )
    else:
        lines.extend(["", "_No premature vocabulary found._"])

    lines.extend(["", "## Non-VESUM Bucket"])
    if analysis.non_vesum:
        lines.extend(["", "| Surface | Modules | Raw Forms |", "|---|---|---|"])
        for item in analysis.non_vesum[:50]:
            lines.append(
                f"| {item.surface} | {', '.join(item.modules)} | {', '.join(item.raw_forms)} |"
            )
        if len(analysis.non_vesum) > 50:
            lines.extend(["", f"_Truncated to 50 of {len(analysis.non_vesum)} non-VESUM surfaces._"])
    else:
        lines.extend(["", "_No non-VESUM surfaces found._"])

    if not gaps_only:
        lines.extend(["", *_lines_for_progressions("Top 50 Most Reused Lemmas", _top_reused(analysis))])
        lines.extend(["", *_lines_for_progressions("50 One-and-Done Lemmas", _one_and_done(analysis))])

    return "\n".join(lines).strip() + "\n"


def render_report(levels: Iterable[str], gaps_only: bool = False, paths: ProjectPaths | None = None) -> str:
    analyses = analyze_levels(levels, paths)
    return "\n\n---\n\n".join(render_level_report(analysis, gaps_only=gaps_only).strip() for analysis in analyses) + "\n"


def available_levels(paths: ProjectPaths | None = None) -> list[str]:
    resolved_paths = paths or ProjectPaths.from_root()
    curriculum = _load_yaml(resolved_paths.curriculum_manifest) or {}
    level_map = curriculum.get("levels", {})
    return [level for level in CORE_LEVELS if level in level_map]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("level", help="CEFR level to analyze, or 'all'")
    parser.add_argument("--report-file", help="Write markdown report to PATH")
    parser.add_argument("--gaps-only", action="store_true", help="Suppress frequency sections")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    resolved_paths = ProjectPaths.from_root()

    level_arg = args.level.lower()
    levels = available_levels(resolved_paths) if level_arg == "all" else [level_arg]

    try:
        report = render_report(levels, gaps_only=args.gaps_only, paths=resolved_paths)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.report_file:
        report_path = Path(args.report_file)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
