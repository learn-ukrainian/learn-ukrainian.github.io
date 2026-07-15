#!/usr/bin/env python3
"""Curriculum-facing Ukrainian quality-gate calibration harness.

This is a deterministic fixture runner for issue #2156's PR1 scope. It does
not replace the V7 LLM-QG reviewer; it verifies the cheap, high-precision
checks and emits compact evidence so known production failures stay covered
before any costly LLM pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
AUDIT_DIR = Path(__file__).resolve().parent
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))

from content_surface_gates import policy_for_level, scan_module_surface
from llm_qg_store import CONTENT_FILES, content_sha_for_module

FIXTURE_SCHEMA_VERSION = "curriculum_ua_qg_fixtures.v1"
EVIDENCE_SCHEMA_VERSION = "curriculum_ua_qg_evidence.v1"
CHECKER_VERSION = "curriculum_ua_qg_harness.v1"
RULE_SET_CURRICULUM = "curriculum"
RULE_SET_HRAMATKA = "hramatka"
RULE_SETS = (RULE_SET_CURRICULUM, RULE_SET_HRAMATKA)


def _hramatka_rules():
    """Lazy-load the separate hramatka rule module (never merge with PHRASE_RULES).

    Imported on demand so ``python scripts/audit/curriculum_qg_harness.py`` keeps
    working when AUDIT_DIR is on ``sys.path`` (avoids ``scripts.audit`` package
    __init__ circular imports at module import time).
    """
    try:
        import hramatka_qg_rules as mod  # type: ignore
    except ImportError:  # pragma: no cover
        from scripts.audit import hramatka_qg_rules as mod
    return mod
DIMENSION_ORDER = (
    "surface_leakage",
    "level_policy",
    "ukrainian_style",
    "tone_register",
    "seminar_sensitivity",
)
SEVERITY_WEIGHTS = {"critical": 2.5, "warning": 0.75, "info": 0.0}
_LATIN_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]*\b")
_CYRILLIC_WORD_RE = re.compile(r"[\u0400-\u04ff][\u0400-\u04ff'ʼ-]*")


@dataclass(frozen=True, slots=True)
class PhraseRule:
    """One deterministic phrase-level regression rule."""

    rule_id: str
    issue_id: str
    dimension: str
    severity: str
    pattern: re.Pattern[str]
    message: str


PHRASE_RULES: tuple[PhraseRule, ...] = (
    PhraseRule(
        rule_id="b1_awkward_passive_result_state",
        issue_id="AWKWARD_PASSIVE_RESULT_STATE",
        dimension="ukrainian_style",
        severity="critical",
        pattern=re.compile(r"застосунок\s+має\s+бути\s+відкритий", re.IGNORECASE),
        message="Use an active or impersonal Ukrainian instruction instead of a literal passive state.",
    ),
    PhraseRule(
        rule_id="b1_unnatural_anthropomorphic_warning",
        issue_id="UNNATURAL_ANTHROPOMORPHISM",
        dimension="ukrainian_style",
        severity="critical",
        pattern=re.compile(r"Застереження\s+каже:\s*будь\s+обережн[а-яіїєґ]*", re.IGNORECASE),
        message="Abstract lesson metalanguage should not be anthropomorphized as a speaker.",
    ),
    PhraseRule(
        rule_id="b1_bad_behavior_government",
        issue_id="UKRAINIAN_GRAMMAR_CALQUE",
        dimension="ukrainian_style",
        severity="critical",
        pattern=re.compile(r"радить\s+не\s+робити\s+певної\s+поведінки", re.IGNORECASE),
        message="The government and nominalized behavior phrase are translated and unnatural.",
    ),
    PhraseRule(
        rule_id="b1_abstract_result_process_calque",
        issue_id="UNNATURAL_META_REGISTER",
        dimension="ukrainian_style",
        severity="critical",
        pattern=re.compile(
            r"дія\s+має\s+дати\s+конкретний\s+результат\s+чи\s+описати\s+процес\?",
            re.IGNORECASE,
        ),
        message="This abstract prompt-like sentence is not natural learner-facing Ukrainian.",
    ),
    PhraseRule(
        rule_id="b1_window_result_calque",
        issue_id="UKRAINIAN_GRAMMAR_CALQUE",
        dimension="ukrainian_style",
        severity="critical",
        pattern=re.compile(r"доконаний\s+вид\s+дає\s+результат\s+із\s+вікном", re.IGNORECASE),
        message="The metaphor and argument structure are literal and unidiomatic.",
    ),
    PhraseRule(
        rule_id="b1_kitchen_locative_context",
        issue_id="CALQUED_PREPOSITION",
        dimension="ukrainian_style",
        severity="critical",
        pattern=re.compile(r"\bУ\s+кухні\b"),
        message="In this ordinary locative teaching context, use the idiomatic На кухні.",
    ),
)


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def checker_config_hash() -> str:
    """Return a stable hash for deterministic harness configuration."""
    payload = {
        "checker_version": CHECKER_VERSION,
        "dimensions": DIMENSION_ORDER,
        "phrase_rules": [
            {
                "rule_id": rule.rule_id,
                "issue_id": rule.issue_id,
                "dimension": rule.dimension,
                "severity": rule.severity,
                "pattern": rule.pattern.pattern,
            }
            for rule in PHRASE_RULES
        ],
        "severity_weights": SEVERITY_WEIGHTS,
    }
    return _sha256_text(_json_dumps(payload))


def _read_module_texts(module_dir: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for name in CONTENT_FILES:
        path = module_dir / name
        if path.exists():
            texts[name] = path.read_text(encoding="utf-8")
    return texts


def _line_no(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _span_for_excerpt(text: str, excerpt: str, line_hint: int | None = None) -> dict[str, int | None]:
    start = text.find(excerpt)
    if start < 0 and line_hint:
        lines = text.splitlines(keepends=True)
        prefix_len = sum(len(line) for line in lines[: max(line_hint - 1, 0)])
        line_text = lines[line_hint - 1] if 0 <= line_hint - 1 < len(lines) else ""
        line_offset = line_text.find(excerpt)
        if line_offset >= 0:
            start = prefix_len + line_offset
    if start < 0:
        return {"start": None, "end": None}
    return {"start": start, "end": start + len(excerpt)}


def _finding(
    *,
    issue_id: str,
    rule_id: str,
    dimension: str,
    severity: str,
    file: str,
    line: int,
    excerpt: str,
    message: str,
    text: str,
    source: str = "deterministic",
) -> dict[str, Any]:
    span = _span_for_excerpt(text, excerpt, line)
    return {
        "issue_id": issue_id,
        "rule_id": rule_id,
        "dimension": dimension,
        "severity": severity,
        "source": source,
        "file": file,
        "line": line,
        "span": span,
        "excerpt": excerpt[:160],
        "message": message,
    }


def _surface_issue_id(finding_type: str, profile: str) -> str:
    if finding_type == "english_led_line" or finding_type == "english_ratio":
        return "ENGLISH_LEAKAGE"
    if finding_type == "ai_leakage":
        return "AI_LEAKAGE"
    if finding_type == "path_leakage":
        return "PATH_LEAKAGE"
    if finding_type == "pathos_or_register" and profile == "seminar":
        return "SEMINAR_REGISTER_PATHOS"
    if finding_type == "pathos_or_register":
        return "PATHOS_REGISTER_OVERREACH"
    if finding_type == "ukrainian_grammar_calque":
        return "UKRAINIAN_GRAMMAR_CALQUE"
    return finding_type.upper()


def _surface_dimension(finding_type: str, profile: str) -> str:
    if finding_type in {"english_led_line", "english_ratio"}:
        return "level_policy"
    if finding_type in {"ai_leakage", "path_leakage"}:
        return "surface_leakage"
    if finding_type == "pathos_or_register" and profile == "seminar":
        return "seminar_sensitivity"
    if finding_type == "pathos_or_register":
        return "tone_register"
    return "ukrainian_style"


def _surface_findings(module_dir: Path, level: str, texts: Mapping[str, str], profile: str) -> list[dict[str, Any]]:
    report = scan_module_surface(module_dir, level=level)
    findings: list[dict[str, Any]] = []
    for item in report.get("findings", []):
        if not isinstance(item, Mapping):
            continue
        file = str(item.get("source") or "module.md")
        excerpt = str(item.get("text") or "").strip()
        if not excerpt:
            continue
        text = texts.get(file, "")
        finding_type = str(item.get("type") or "surface")
        issue_id = _surface_issue_id(finding_type, profile)
        severity = str(item.get("severity") or "warning")
        if issue_id == "SEMINAR_REGISTER_PATHOS":
            severity = "critical"
        findings.append(
            _finding(
                issue_id=issue_id,
                rule_id=f"surface_{finding_type}",
                dimension=_surface_dimension(finding_type, profile),
                severity=severity,
                file=file,
                line=int(item.get("line") or 0),
                excerpt=excerpt,
                message=str(item.get("message") or finding_type),
                text=text,
            )
        )
    return findings


def _phrase_findings(texts: Mapping[str, str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for file, text in texts.items():
        for rule in PHRASE_RULES:
            for match in rule.pattern.finditer(text):
                findings.append(
                    _finding(
                        issue_id=rule.issue_id,
                        rule_id=rule.rule_id,
                        dimension=rule.dimension,
                        severity=rule.severity,
                        file=file,
                        line=_line_no(text, match.start()),
                        excerpt=match.group(0),
                        message=rule.message,
                        text=text,
                    )
                )
    return findings


def _anchor_findings(texts: Mapping[str, str], profile: str) -> list[dict[str, Any]]:
    """Catch A1 modules where English replaces the Ukrainian anchor entirely."""
    if profile != "a1":
        return []
    text = texts.get("module.md", "")
    latin_words = _LATIN_WORD_RE.findall(text)
    cyrillic_words = _CYRILLIC_WORD_RE.findall(text)
    if len(latin_words) < 16 or cyrillic_words:
        return []
    excerpt = next(
        (
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ),
        text[:80],
    )
    return [
        _finding(
            issue_id="ENGLISH_LEAKAGE",
            rule_id="a1_missing_ukrainian_anchor",
            dimension="level_policy",
            severity="critical",
            file="module.md",
            line=_line_no(text, text.find(excerpt)) if excerpt in text else 1,
            excerpt=excerpt,
            message="A1 may use substantial English scaffolding, but it still needs a Ukrainian anchor.",
            text=text,
        )
    ]


def _dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for finding in findings:
        key = (
            finding.get("issue_id"),
            finding.get("file"),
            finding.get("line"),
            finding.get("excerpt"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(finding)
    return out


def _dimension_scores(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    dimensions: dict[str, dict[str, Any]] = {}
    for dim in DIMENSION_ORDER:
        dim_findings = [finding for finding in findings if finding.get("dimension") == dim]
        penalty = sum(SEVERITY_WEIGHTS.get(str(finding.get("severity")), 0.0) for finding in dim_findings)
        score = max(0.0, round(10.0 - penalty, 1))
        has_critical = any(finding.get("severity") == "critical" for finding in dim_findings)
        has_warning = any(finding.get("severity") == "warning" for finding in dim_findings)
        dimensions[dim] = {
            "score": score,
            "verdict": "FAIL" if has_critical else "WARN" if has_warning else "PASS",
            "findings": dim_findings,
        }
    return dimensions


def _aggregate(dimensions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    scored = {
        dim: float(entry.get("score", 0.0))
        for dim, entry in dimensions.items()
        if isinstance(entry.get("score"), int | float)
    }
    min_dim = min(scored, key=scored.__getitem__) if scored else None
    has_fail = any(entry.get("verdict") == "FAIL" for entry in dimensions.values())
    has_warn = any(entry.get("verdict") == "WARN" for entry in dimensions.values())
    return {
        "verdict": "FAIL" if has_fail else "WARN" if has_warn else "PASS",
        "terminal_verdict": "FAIL" if has_fail else "PASS",
        "min_score": scored[min_dim] if min_dim else None,
        "min_dim": min_dim,
        "failing_dims": [dim for dim, entry in dimensions.items() if entry.get("verdict") == "FAIL"],
        "warning_dims": [dim for dim, entry in dimensions.items() if entry.get("verdict") == "WARN"],
    }


def scan_curriculum_module(
    module_dir: Path,
    *,
    level: str,
    slug: str | None = None,
    fixture_id: str | None = None,
    rule_set: str = RULE_SET_CURRICULUM,
) -> dict[str, Any]:
    """Scan one module directory and return compact deterministic evidence.

    ``rule_set`` selects the checker family:
    - ``curriculum`` (default): writer-failure PHRASE_RULES + surface gates
    - ``hramatka``: structural/generative checks in ``hramatka_qg_rules``
    """
    clean_rule_set = (rule_set or RULE_SET_CURRICULUM).strip().lower()
    if clean_rule_set == RULE_SET_HRAMATKA:
        return _hramatka_rules().scan_hramatka_module(
            module_dir,
            level=level,
            slug=slug,
            fixture_id=fixture_id,
        )

    module_dir = module_dir.resolve()
    clean_level = level.strip().lower()
    clean_slug = slug or module_dir.name
    policy = policy_for_level(clean_level)
    texts = _read_module_texts(module_dir)
    findings = _dedupe_findings(
        [
            *_surface_findings(module_dir, clean_level, texts, policy.family),
            *_phrase_findings(texts),
            *_anchor_findings(texts, policy.family),
        ]
    )
    dimensions = _dimension_scores(findings)
    aggregate = _aggregate(dimensions)
    config_hash = checker_config_hash()
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "rule_set": RULE_SET_CURRICULUM,
        "module_id": f"{clean_level}/{clean_slug}",
        "level": clean_level,
        "slug": clean_slug,
        "level_policy": {
            "family": policy.family,
            "english_policy": policy.english_policy,
        },
        "checker_config": {
            "version": CHECKER_VERSION,
            "config_hash": config_hash,
            "rule_set": RULE_SET_CURRICULUM,
        },
        "content_sha": content_sha_for_module(module_dir),
        "verdict": aggregate["verdict"],
        "terminal_verdict": aggregate["terminal_verdict"],
        "aggregate": aggregate,
        "dimensions": dimensions,
        "checker_runs": [
            {
                "source": "deterministic",
                "checker": CHECKER_VERSION,
                "config_hash": config_hash,
                "provider": None,
                "model": None,
            }
        ],
        "llm_review": {
            "used": False,
            "required": aggregate["verdict"] != "PASS",
            "provider": None,
            "model": None,
            "reason": "Residual LLM-QG review is required for FAIL/WARN modules.",
        },
        "provenance": {
            "created_at": _now_z(),
            "run_id": f"curriculum-qg-{uuid4().hex}",
            "source": "curriculum_qg_harness",
            "fixture_id": fixture_id,
        },
    }


def _write_fixture_module(root: Path, fixture: Mapping[str, Any]) -> Path:
    module = fixture.get("module")
    if not isinstance(module, Mapping):
        raise ValueError(f"fixture {fixture.get('id')} missing module mapping")
    module_dir = root / str(fixture.get("level") or "fixture") / str(fixture.get("slug") or fixture.get("id"))
    module_dir.mkdir(parents=True, exist_ok=True)
    for name in CONTENT_FILES:
        value = module.get(name)
        if value is None:
            value = "[]\n" if name.endswith((".yaml", ".yml")) else ""
        (module_dir / name).write_text(str(value).rstrip() + "\n", encoding="utf-8")
    return module_dir


def _load_fixture_source_module(fixture: Mapping[str, Any]) -> Path:
    raw = fixture.get("source_module_dir")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"fixture {fixture.get('id')} missing source_module_dir")
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _expected_findings_pass(
    evidence: Mapping[str, Any],
    expected: list[Mapping[str, Any]],
) -> tuple[bool, list[dict[str, Any]]]:
    actual: list[Mapping[str, Any]] = []
    dimensions = evidence.get("dimensions")
    if isinstance(dimensions, Mapping):
        for entry in dimensions.values():
            if isinstance(entry, Mapping) and isinstance(entry.get("findings"), list):
                actual.extend(item for item in entry["findings"] if isinstance(item, Mapping))

    missing: list[dict[str, Any]] = []
    for wanted in expected:
        issue_id = str(wanted.get("issue_id") or "")
        excerpt = _normalize_text(wanted.get("excerpt"))
        dimension = str(wanted.get("dimension") or "")
        severity = str(wanted.get("severity") or "")

        matched = False
        for item in actual:
            if issue_id and item.get("issue_id") != issue_id:
                continue
            if dimension and item.get("dimension") != dimension:
                continue
            if severity and item.get("severity") != severity:
                continue
            actual_excerpt = _normalize_text(item.get("excerpt"))
            if excerpt and excerpt not in actual_excerpt:
                continue
            matched = True
            break
        if not matched:
            missing.append(dict(wanted))
    return not missing, missing


def evaluate_fixture(fixture: Mapping[str, Any], *, temp_root: Path) -> dict[str, Any]:
    """Evaluate one labeled fixture and compare it to gold expectations."""
    fixture_id = str(fixture.get("id") or "")
    level = str(fixture.get("level") or "")
    slug = str(fixture.get("slug") or fixture_id)
    if fixture.get("source_module_dir"):
        module_dir = _load_fixture_source_module(fixture)
    else:
        module_dir = _write_fixture_module(temp_root, fixture)

    evidence = scan_curriculum_module(
        module_dir,
        level=level,
        slug=slug,
        fixture_id=fixture_id,
    )
    expected_verdict = str(fixture.get("expected_verdict") or "").upper()
    verdict_passed = not expected_verdict or evidence["verdict"] == expected_verdict
    expected_findings = fixture.get("expected_findings")
    if not isinstance(expected_findings, list):
        expected_findings = []
    findings_passed, missing_findings = _expected_findings_pass(evidence, expected_findings)
    return {
        "id": fixture_id,
        "level": level,
        "slug": slug,
        "expected_verdict": expected_verdict,
        "actual_verdict": evidence["verdict"],
        "passed": verdict_passed and findings_passed,
        "missing_findings": missing_findings,
        "evidence": evidence,
    }


def run_fixtures(path: Path, *, rule_set: str | None = None) -> dict[str, Any]:
    """Run a fixture YAML file and return result rows plus summary.

    Hramatka fixtures use schema ``hramatka_ua_qg_fixtures.v1`` and are
    dispatched to ``hramatka_qg_rules.run_fixtures`` (separate rule set).
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("fixture file must be a mapping")
    schema = data.get("schema_version")
    requested = (rule_set or data.get("rule_set") or RULE_SET_CURRICULUM)
    requested = str(requested).strip().lower()

    hramatka = _hramatka_rules()
    if schema == hramatka.FIXTURE_SCHEMA_VERSION or requested == RULE_SET_HRAMATKA:
        return hramatka.run_fixtures(path)

    if schema != FIXTURE_SCHEMA_VERSION:
        raise ValueError(f"unsupported fixture schema: {schema}")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("fixture file must contain a fixtures list")

    with tempfile.TemporaryDirectory(prefix="curriculum-qg-fixtures-") as raw_tmp:
        tmp_root = Path(raw_tmp)
        results = [
            evaluate_fixture(fixture, temp_root=tmp_root)
            for fixture in fixtures
            if isinstance(fixture, Mapping)
        ]
    passed = sum(1 for result in results if result["passed"])
    return {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "rule_set": RULE_SET_CURRICULUM,
        "fixture_file": str(path),
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
        "results": results,
    }


def _summary_text(payload: Mapping[str, Any]) -> str:
    rule_set = str(payload.get("rule_set") or RULE_SET_CURRICULUM)
    if "results" in payload:
        summary = payload["summary"]
        label = (
            "Hramatka Ukrainian QG Fixtures"
            if rule_set == RULE_SET_HRAMATKA
            else "Curriculum Ukrainian QG Fixtures"
        )
        lines = [
            label,
            f"Rule set: {rule_set}",
            f"Total: {summary['total']}",
            f"Passed: {summary['passed']}",
            f"Failed: {summary['failed']}",
        ]
        for result in payload["results"]:
            mark = "PASS" if result["passed"] else "FAIL"
            lines.append(
                f"- {mark} {result['id']}: expected={result['expected_verdict']} actual={result['actual_verdict']}"
            )
        return "\n".join(lines)
    aggregate = payload["aggregate"]
    label = (
        "Hramatka Ukrainian QG Evidence"
        if rule_set == RULE_SET_HRAMATKA
        else "Curriculum Ukrainian QG Evidence"
    )
    return (
        f"{label}\n"
        f"Rule set: {rule_set}\n"
        f"Module: {payload['module_id']}\n"
        f"Verdict: {payload['verdict']}\n"
        f"Min score: {aggregate['min_score']} ({aggregate['min_dim']})"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--module-dir", type=Path, help="Module directory to scan.")
    source.add_argument("--fixtures", type=Path, help="Fixture YAML file to run.")
    source.add_argument(
        "--lesson-json",
        type=Path,
        help="Hramatka lesson_json file (implies --rule-set hramatka).",
    )
    parser.add_argument("--level", help="Level for --module-dir, e.g. b1.")
    parser.add_argument("--slug", help="Slug for --module-dir. Defaults to directory name.")
    parser.add_argument(
        "--rule-set",
        choices=RULE_SETS,
        default=RULE_SET_CURRICULUM,
        help=(
            "Selectable rule set: 'curriculum' (writer PHRASE_RULES) or "
            "'hramatka' (structural/generative lesson checks). Default: curriculum."
        ),
    )
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    parser.add_argument("--output", type=Path, help="Optional output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.fixtures:
            payload = run_fixtures(args.fixtures, rule_set=args.rule_set)
            failed = int(payload["summary"]["failed"])
        elif args.lesson_json is not None:
            lesson = json.loads(args.lesson_json.read_text(encoding="utf-8"))
            payload = _hramatka_rules().scan_hramatka_lesson(
                lesson,
                slug=args.slug,
            )
            failed = 0 if payload["terminal_verdict"] == "PASS" else 1
        else:
            if not args.level and args.rule_set != RULE_SET_HRAMATKA:
                raise ValueError("--module-dir requires --level")
            payload = scan_curriculum_module(
                args.module_dir,
                level=args.level or "b1",
                slug=args.slug,
                rule_set=args.rule_set,
            )
            failed = 0 if payload["terminal_verdict"] == "PASS" else 1
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if args.format == "json"
        else _summary_text(payload)
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
