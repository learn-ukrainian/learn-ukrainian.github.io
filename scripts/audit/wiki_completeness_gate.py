"""Upstream wiki completeness gate for V7.1 writer builds."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build.phases.wiki_manifest import extract_manifest

CORE_LEVELS = frozenset({"a1", "a2", "b1", "b2", "c1", "c2"})
EARLY_FOUNDATION_DECOLONIZATION_SECTION_ONLY_SLUGS = frozenset(
    {
        "sounds-letters-and-hello",
        "reading-ukrainian",
        "special-signs",
        "stress-and-melody",
    }
)
SEMINAR_LEVELS = frozenset(
    {
        "folk",
        "hist",
        "istorio",
        "bio",
        "lit",
        "lit-essay",
        "lit-hist-fic",
        "lit-fantastika",
        "lit-war",
        "lit-humor",
        "lit-youth",
        "lit-doc",
        "lit-drama",
        "lit-crimea",
        "oes",
        "ruth",
    }
)
SEMINAR_REQUIRED_SECTIONS = (
    "Короткий зміст",
    "Основний зміст",
    "Ключові терміни",
    "Мовні зразки",
    "Деколонізаційна перспектива",
    "Пов'язані статті",
)
SEMINAR_SECTION_HEADING_RES = {
    heading: re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE)
    for heading in SEMINAR_REQUIRED_SECTIONS
}

METHODOLOGY_HEADING_RE = re.compile(r"^##\s+Методичний\s+підхід\b", re.IGNORECASE)
DECOLONIZATION_HEADING_RE = re.compile(r"^##\s+Деколонізаційні\s+застереження\b", re.IGNORECASE)
TEXTBOOK_EXAMPLES_HEADING_RE = re.compile(r"^##\s+Приклади\s+з\s+підручників\b", re.IGNORECASE)
ANY_H2_RE = re.compile(r"^##\s+\S")
SOURCE_REF_RE = re.compile(r"\[S(?P<num>\d+)\]")
BAD_MARKER_RE = re.compile(r"<!--\s*bad\s*-->(?P<body>.*?)<!--\s*/bad\s*-->", re.IGNORECASE | re.DOTALL)
GUILLEMET_NEGATED_PAIR_RE = re.compile(r"«[^»\n]{1,120}»\s*\(\s*не\s+«[^»\n]{1,120}»\s*\)", re.IGNORECASE)
UKRAINIAN_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")

CHECK_TITLES = {
    "methodology": "Методичний підхід",
    "sequence_steps": "Послідовність введення",
    "l2_errors": "Типові помилки L2",
    "decolonization_pairs": "Деколонізаційні застереження",
    "vocabulary_minimum": "Словниковий мінімум",
    "textbook_exercises": "Приклади з підручників",
    "distractor_inventory": "distractor_inventory",
    "chunk_citations_spot_check": "chunk_citations_spot_check",
    "seminar_sections": "seminar_sections",
    "distinct_sources": "distinct_sources",
    "citation_resolution": "citation_resolution",
    "source_ref_resolution": "source_ref_resolution",
    "all_chunk_verify_quote": "all_chunk_verify_quote",
}
CHECK_ORDER = (
    "methodology",
    "sequence_steps",
    "l2_errors",
    "decolonization_pairs",
    "vocabulary_minimum",
    "textbook_exercises",
    "distractor_inventory",
    "chunk_citations_spot_check",
)
SEMINAR_CHECK_ORDER = (
    "seminar_sections",
    "distinct_sources",
    "citation_resolution",
    "source_ref_resolution",
    "all_chunk_verify_quote",
)


def thresholds_for_level(level: str) -> dict[str, Any]:
    """Return V7.1 wiki completeness thresholds for implemented core levels."""
    level_key = level.lower()
    if level_key in SEMINAR_LEVELS:
        return {
            "required_sections": SEMINAR_REQUIRED_SECTIONS,
            "min_distinct_sources": 2,
            "citations_resolve": 100,
            "source_refs_resolve": 100,
            "all_chunk_verify_quote": 100,
        }
    if level_key not in CORE_LEVELS:
        raise ValueError(f"Unknown level for wiki completeness gate: {level!r}")
    if level_key in {"a1", "a2"}:
        return {
            "sequence_steps": 5,
            "l2_errors": 3,
            "decolonization_pairs": 1,
            "vocabulary_minimum": 20,
            "textbook_exercises": 3,
            "distractor_inventory": 6,
            "chunk_citations_spot_check": 3,
        }
    return {
        "sequence_steps": 5,
        "l2_errors": 3,
        "decolonization_pairs": 2,
        "vocabulary_minimum": 50,
        "textbook_exercises": 3,
        "distractor_inventory": 10,
        "chunk_citations_spot_check": 5,
    }


def thresholds_for_module(level: str, slug: str | None) -> dict[str, Any]:
    """Return wiki completeness thresholds adjusted for module-level policy."""
    thresholds = thresholds_for_level(level)
    level_key = level.lower()
    slug_key = (slug or "").lower()
    if level_key in {"a1", "a2"} and slug_key in EARLY_FOUNDATION_DECOLONIZATION_SECTION_ONLY_SLUGS:
        thresholds = dict(thresholds)
        thresholds["decolonization_pairs"] = 0
        thresholds["distractor_inventory"] = 5
    return thresholds


def check_wiki_completeness(
    wiki_path: str | Path,
    *,
    level: str,
    slug: str | None = None,
    verify_quote_fn: Callable[[str, str, Mapping[str, Any]], Mapping[str, Any] | bool] | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable PASS/FAIL report for one compiled wiki."""
    path = Path(wiki_path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    manifest = extract_manifest(path)
    slug_value = slug or str(manifest.get("slug") or path.stem)
    level_key = level.lower()
    thresholds = thresholds_for_module(level_key, slug_value)
    if level_key in SEMINAR_LEVELS:
        return _check_seminar_completeness(
            text,
            lines,
            path,
            level=level_key,
            slug=slug_value,
            thresholds=thresholds,
            verify_quote_fn=verify_quote_fn,
        )

    methodology_text = _section_text(lines, METHODOLOGY_HEADING_RE)
    decolonization_text = _section_text(lines, DECOLONIZATION_HEADING_RE)
    textbook_text = _section_text(lines, TEXTBOOK_EXAMPLES_HEADING_RE)

    decolonization_pairs = _count_decolonization_pairs(decolonization_text)
    l2_distractors = _count_l2_distractors(manifest.get("l2_errors", []))
    decolonization_distractors = _count_decolonization_distractors(decolonization_text)

    checks = {
        "methodology": _section_presence_check(methodology_text, "Methodology section is non-empty."),
        "sequence_steps": _minimum_check(
            len(manifest.get("sequence_steps", [])),
            thresholds["sequence_steps"],
            "sequence step(s) found in ## Послідовність введення.",
        ),
        "l2_errors": _minimum_check(
            len(manifest.get("l2_errors", [])),
            thresholds["l2_errors"],
            "L2 error table row(s) found.",
        ),
        "decolonization_pairs": _decolonization_check(
            decolonization_text,
            decolonization_pairs,
            thresholds["decolonization_pairs"],
        ),
        "vocabulary_minimum": _minimum_check(
            len(manifest.get("wiki_vocabulary_minimum", [])),
            thresholds["vocabulary_minimum"],
            "wiki vocabulary-minimum lemma(s) found.",
        ),
        "textbook_exercises": _minimum_check(
            _count_textbook_exercises(textbook_text),
            thresholds["textbook_exercises"],
            "textbook exercise format(s) with chunk citations found.",
        ),
        "distractor_inventory": _minimum_check(
            l2_distractors + decolonization_distractors,
            thresholds["distractor_inventory"],
            "wrong-form distractor(s) found across L2 errors and decolonization pairs.",
        ),
        "chunk_citations_spot_check": _chunk_citation_check(
            text,
            path,
            thresholds["chunk_citations_spot_check"],
            verify_quote_fn=verify_quote_fn,
        ),
    }

    failed = [name for name in CHECK_ORDER if checks[name]["verdict"] == "FAIL"]
    return {
        "verdict": "FAIL" if failed else "PASS",
        "level": level_key,
        "slug": slug_value,
        "checks": checks,
        "diagnostic": _diagnostic(failed[0], checks[failed[0]]) if failed else "Wiki completeness gate passed.",
    }


def _check_seminar_completeness(
    wiki_text: str,
    lines: list[str],
    wiki_path: Path,
    *,
    level: str,
    slug: str,
    thresholds: Mapping[str, Any],
    verify_quote_fn: Callable[[str, str, Mapping[str, Any]], Mapping[str, Any] | bool] | None,
) -> dict[str, Any]:
    required_sections = tuple(str(section) for section in thresholds["required_sections"])
    citations = _ordered_source_ids(wiki_text)
    sources = _load_source_registry(wiki_path)

    checks = {
        "seminar_sections": _seminar_sections_check(lines, required_sections),
        "distinct_sources": _minimum_check(
            len(citations),
            int(thresholds["min_distinct_sources"]),
            "distinct inline source citation(s) found.",
        ),
        "citation_resolution": _citation_resolution_check(
            citations,
            sources,
            int(thresholds["citations_resolve"]),
        ),
        "source_ref_resolution": _source_ref_resolution_check(
            citations,
            sources,
            int(thresholds["source_refs_resolve"]),
        ),
        "all_chunk_verify_quote": _all_chunk_verify_quote_check(
            wiki_text,
            citations,
            sources,
            int(thresholds["all_chunk_verify_quote"]),
            verify_quote_fn=verify_quote_fn,
        ),
    }

    failed = [name for name in SEMINAR_CHECK_ORDER if checks[name]["verdict"] == "FAIL"]
    return {
        "verdict": "FAIL" if failed else "PASS",
        "level": level,
        "slug": slug,
        "checks": checks,
        "diagnostic": _diagnostic(failed[0], checks[failed[0]]) if failed else "Wiki completeness gate passed.",
    }


def _seminar_sections_check(lines: list[str], required_sections: tuple[str, ...]) -> dict[str, Any]:
    missing_or_empty = [
        heading
        for heading in required_sections
        if not _section_text(lines, SEMINAR_SECTION_HEADING_RES[heading]).strip()
    ]
    actual = len(required_sections) - len(missing_or_empty)
    report = _minimum_check(
        actual,
        len(required_sections),
        f"{actual}/{len(required_sections)} required seminar sections are present and non-empty.",
    )
    if missing_or_empty:
        report["missing_or_empty"] = missing_or_empty
        report["detail"] = "missing or empty seminar section(s): " + ", ".join(missing_or_empty)
    return report


def _citation_resolution_check(
    citations: list[str],
    sources: Mapping[str, Mapping[str, Any]],
    minimum_percent: int,
) -> dict[str, Any]:
    missing = [source_id for source_id in citations if source_id not in sources]
    resolved = len(citations) - len(missing)
    actual_percent = _percent(resolved, len(citations))
    verdict = "PASS" if actual_percent >= minimum_percent else "FAIL"
    report: dict[str, Any] = {
        "verdict": verdict,
        "actual": actual_percent,
        "minimum": minimum_percent,
        "detail": f"{resolved}/{len(citations)} cited source id(s) defined in source registry.",
    }
    if missing:
        report["dangling_ids"] = missing
        report["detail"] = "dangling citation id(s): " + ", ".join(missing)
    return report


def _source_ref_resolution_check(
    citations: list[str],
    sources: Mapping[str, Mapping[str, Any]],
    minimum_percent: int,
) -> dict[str, Any]:
    unresolved = [
        source_id
        for source_id in citations
        if not _source_has_resolvable_reference(sources.get(source_id))
    ]
    resolved = len(citations) - len(unresolved)
    actual_percent = _percent(resolved, len(citations))
    verdict = "PASS" if actual_percent >= minimum_percent else "FAIL"
    report: dict[str, Any] = {
        "verdict": verdict,
        "actual": actual_percent,
        "minimum": minimum_percent,
        "detail": f"{resolved}/{len(citations)} cited source reference(s) resolved.",
    }
    if unresolved:
        report["unresolved_ids"] = unresolved
        report["detail"] = "unresolved source reference id(s): " + ", ".join(unresolved)
    return report


def _all_chunk_verify_quote_check(
    wiki_text: str,
    citations: list[str],
    sources: Mapping[str, Mapping[str, Any]],
    minimum_percent: int,
    *,
    verify_quote_fn: Callable[[str, str, Mapping[str, Any]], Mapping[str, Any] | bool] | None,
) -> dict[str, Any]:
    if verify_quote_fn is None:
        resolved = sum(
            1
            for source_id in citations
            if source_id in sources and _source_has_resolvable_reference(sources.get(source_id))
        )
        actual_percent = _percent(resolved, len(citations))
        verdict = "PASS" if actual_percent >= minimum_percent else "FAIL"
        report: dict[str, Any] = {
            "verdict": verdict,
            "actual": actual_percent,
            "minimum": minimum_percent,
            "detail": (
                f"{resolved}/{len(citations)} source registry ids and references resolved "
                "(verify_quote adapter not configured)"
            ),
        }
        failures = [
            source_id
            for source_id in citations
            if source_id not in sources or not _source_has_resolvable_reference(sources.get(source_id))
        ]
        if failures:
            report["failures"] = failures
        return report

    passed = 0
    failures: list[str] = []
    for source_id in citations:
        source = sources.get(source_id)
        if not _source_has_resolvable_reference(source):
            failures.append(source_id)
            continue
        result = verify_quote_fn(source_id, _citation_context(wiki_text, source_id), source)
        if _verification_passed(result):
            passed += 1
        else:
            failures.append(source_id)

    actual_percent = _percent(passed, len(citations))
    verdict = "PASS" if actual_percent >= minimum_percent else "FAIL"
    report = {
        "verdict": verdict,
        "actual": actual_percent,
        "minimum": minimum_percent,
        "detail": f"{passed}/{len(citations)} verify_quote returned PASS",
    }
    if failures:
        report["failures"] = failures
    return report


def _source_has_resolvable_reference(source: Mapping[str, Any] | None) -> bool:
    if not source:
        return False
    source_type = str(source.get("type") or "").strip().lower()
    if source_type in {"literary", "textbook"}:
        return bool(str(source.get("file") or "").strip())
    if source_type in {"wikipedia", "external", "external_article"}:
        return bool(str(source.get("url") or "").strip())
    return bool(str(source.get("file") or source.get("url") or "").strip())


def _percent(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 100
    return round((numerator / denominator) * 100)


def _section_presence_check(section_text: str, detail: str) -> dict[str, Any]:
    if section_text.strip():
        return {"verdict": "PASS", "detail": detail}
    return {"verdict": "FAIL", "actual": 0, "minimum": 1, "detail": "section missing or empty"}


def _minimum_check(actual: int, minimum: int, detail: str) -> dict[str, Any]:
    verdict = "PASS" if actual >= minimum else "FAIL"
    return {"verdict": verdict, "actual": actual, "minimum": minimum, "detail": detail}


def _decolonization_check(section_text: str, actual_pairs: int, minimum_pairs: int) -> dict[str, Any]:
    if minimum_pairs <= 0:
        if section_text.strip():
            return {
                "verdict": "PASS",
                "actual": actual_pairs,
                "minimum": minimum_pairs,
                "detail": "decolonization section present; bad-form pair inventory not required for early foundation modules.",
            }
        return {
            "verdict": "FAIL",
            "actual": 0,
            "minimum": 1,
            "detail": "decolonization section missing or empty",
        }
    return _minimum_check(actual_pairs, minimum_pairs, "decolonization bad-form pair(s) found.")


def _diagnostic(check_name: str, check: Mapping[str, Any]) -> str:
    title = CHECK_TITLES.get(check_name, check_name)
    actual = check.get("actual")
    minimum = check.get("minimum")
    if actual is not None and minimum is not None:
        return f"Wiki section [{title}] is insufficient ({actual} < {minimum})."
    return f"Wiki section [{title}] is missing or incomplete."


def _section_text(lines: list[str], heading_re: re.Pattern[str]) -> str:
    start = None
    for index, line in enumerate(lines):
        if heading_re.search(line):
            start = index
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if ANY_H2_RE.search(lines[index]):
            end = index
            break
    return "\n".join(lines[start + 1 : end]).strip()


def _count_decolonization_pairs(section_text: str) -> int:
    marked = len(BAD_MARKER_RE.findall(section_text))
    explicit = len(GUILLEMET_NEGATED_PAIR_RE.findall(section_text))
    return marked + explicit


def _count_decolonization_distractors(section_text: str) -> int:
    return _count_decolonization_pairs(section_text)


def _count_l2_distractors(raw_errors: Any) -> int:
    if not isinstance(raw_errors, list):
        return 0
    count = 0
    for error in raw_errors:
        if not isinstance(error, Mapping):
            continue
        incorrect = str(error.get("incorrect") or "")
        parts = [part.strip() for part in re.split(r"\s*/\s*|\s*;\s*", incorrect) if part.strip()]
        count += sum(1 for part in parts if UKRAINIAN_RE.search(part) or "[" in part)
    return count


def _count_textbook_exercises(section_text: str) -> int:
    count = 0
    blocks = re.split(r"(?=^\*\*Вправа\s+\d+\b)", section_text, flags=re.MULTILINE)
    for block in blocks:
        if not block.lstrip().startswith("**Вправа"):
            continue
        if re.search(r"Chunk ID\s*:", block, flags=re.IGNORECASE) and SOURCE_REF_RE.search(block):
            count += 1
    return count


def _chunk_citation_check(
    wiki_text: str,
    wiki_path: Path,
    sample_size: int,
    *,
    verify_quote_fn: Callable[[str, str, Mapping[str, Any]], Mapping[str, Any] | bool] | None,
) -> dict[str, Any]:
    citations = _ordered_source_ids(wiki_text)
    selected = citations[: min(sample_size, len(citations))]
    if len(selected) < sample_size:
        return {
            "verdict": "FAIL",
            "actual": len(selected),
            "minimum": sample_size,
            "detail": f"{len(selected)}/{sample_size} chunk citations available for spot-check",
        }

    sources = _load_source_registry(wiki_path)
    passed = 0
    failures: list[str] = []
    for source_id in selected:
        source = sources.get(source_id, {})
        if verify_quote_fn is None:
            if source:
                passed += 1
            else:
                failures.append(source_id)
            continue
        result = verify_quote_fn(source_id, _citation_context(wiki_text, source_id), source)
        if _verification_passed(result):
            passed += 1
        else:
            failures.append(source_id)

    if verify_quote_fn is None:
        detail = f"{passed}/{len(selected)} source registry ids resolved (verify_quote adapter not configured)"
    else:
        detail = f"{passed}/{len(selected)} verify_quote returned PASS"
    verdict = "PASS" if passed == len(selected) else "FAIL"
    report: dict[str, Any] = {"verdict": verdict, "detail": detail}
    if verdict == "FAIL":
        report.update({"actual": passed, "minimum": len(selected), "failures": failures})
    return report


def _ordered_source_ids(text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in SOURCE_REF_RE.finditer(text):
        source_id = f"S{match.group('num')}"
        if source_id not in seen:
            seen.add(source_id)
            ordered.append(source_id)
    return ordered


def _load_source_registry(wiki_path: Path) -> dict[str, Mapping[str, Any]]:
    registry_path = wiki_path.with_suffix(".sources.yaml")
    if not registry_path.exists():
        return {}
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    sources = data.get("sources", []) if isinstance(data, Mapping) else []
    out: dict[str, Mapping[str, Any]] = {}
    if isinstance(sources, list):
        for item in sources:
            if isinstance(item, Mapping) and item.get("id"):
                out[str(item["id"])] = item
    return out


def _citation_context(text: str, source_id: str) -> str:
    match = re.search(rf"[^.\n]*\[{re.escape(source_id)}\][^.\n]*", text)
    return re.sub(r"\s+", " ", match.group(0)).strip() if match else source_id


def _verification_passed(result: Mapping[str, Any] | bool) -> bool:
    if isinstance(result, bool):
        return result
    if not isinstance(result, Mapping):
        return False
    verdict = result.get("verdict", result.get("passed", result.get("ok")))
    if isinstance(verdict, bool):
        return verdict
    return str(verdict).upper() == "PASS"


def _default_wiki_path(level: str, slug: str) -> Path:
    direct = PROJECT_ROOT / "wiki" / "pedagogy" / level.lower() / f"{slug}.md"
    if direct.exists():
        return direct
    matches = sorted((PROJECT_ROOT / "wiki").glob(f"**/{slug}.md"))
    if not matches:
        raise FileNotFoundError(f"No wiki article found for level={level!r}, slug={slug!r}")
    return matches[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the V7.1 wiki completeness gate")
    parser.add_argument("level")
    parser.add_argument("slug")
    parser.add_argument("--wiki-path", type=Path)
    args = parser.parse_args(argv)

    wiki_path = args.wiki_path or _default_wiki_path(args.level, args.slug)
    report = check_wiki_completeness(wiki_path, level=args.level, slug=args.slug)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
