#!/usr/bin/env python3
"""Phase 5.2: Regional Dialect & Historical Protection Evaluator (ULDR #8051).

Evaluates aligned language models on the 600-case Dialect & Historical Protection Suite:
  1. Regional Dialect Preservation Gate (>= 98.0% non-corruption, Clopper-Pearson 95% lower bound)
  2. Historical & Classical Preservation Gate (>= 98.0% non-corruption, Clopper-Pearson 95% lower bound)
  3. Absolute Anti-Surzhyk Invariant Gate (0.0% tolerance for Surzhyk normalization; mandatory eradication)

Supports:
  - Offline predictions JSONL scoring
  - Deterministic contract verification mode
  - Comprehensive statistical audit report generation
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scipy.stats import beta

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.v5_evaluation_harness import ParsedTurn, parse_model_output

DEFAULT_TEST_SUITE_PATH = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "partitions"
    / "dialect_historical_protection_suite_600.jsonl"
)


def exact_clopper_pearson_lower(successes: int, total: int, alpha: float = 0.05) -> float:
    """Exact one-sided (1 - alpha) Clopper-Pearson lower confidence limit for binomial proportion."""
    if total <= 0:
        return 0.0
    if successes <= 0:
        return 0.0
    if successes >= total:
        return float(alpha ** (1.0 / total))
    return float(beta.ppf(alpha, successes, total - successes + 1))


def exact_clopper_pearson_upper(errors: int, total: int, alpha: float = 0.05) -> float:
    """Exact one-sided (1 - alpha) Clopper-Pearson upper confidence limit for binomial proportion."""
    if total <= 0:
        return 1.0
    if errors >= total:
        return 1.0
    if errors == 0:
        return float(1.0 - alpha ** (1.0 / total))
    return float(beta.ppf(1.0 - alpha, errors + 1, total - errors))


@dataclass(frozen=True)
class CaseEvaluationResult:
    """Evaluation result for a single dialect, historical, or control test case."""

    eval_id: str
    stratum: str
    subgroup: str
    case_type: str
    target_term: str
    is_pass: bool
    is_corrupted: bool
    is_surzhyk_normalized: bool
    failure_reason: str | None
    parsed: ParsedTurn


@dataclass
class ProtectionSuiteMetrics:
    """Aggregated metrics across the 600-case evaluation suite."""

    total_cases: int = 0
    # Regional dialect
    dialect_total: int = 0
    dialect_preserved: int = 0
    dialect_corrupted: int = 0
    dialect_preservation_rate: float = 0.0
    dialect_clopper_pearson_lower: float = 0.0
    dialect_gate_cleared: bool = False

    # Historical text
    historical_total: int = 0
    historical_preserved: int = 0
    historical_corrupted: int = 0
    historical_preservation_rate: float = 0.0
    historical_clopper_pearson_lower: float = 0.0
    historical_gate_cleared: bool = False

    # Combined preservation (dialect + historical, N=500)
    combined_preserve_total: int = 0
    combined_preserve_passed: int = 0
    combined_preserve_rate: float = 0.0
    combined_clopper_pearson_lower: float = 0.0
    combined_gate_cleared: bool = False

    # Anti-Surzhyk Invariant
    surzhyk_total: int = 0
    surzhyk_eradicated: int = 0
    surzhyk_normalized: int = 0
    surzhyk_eradication_rate: float = 0.0
    surzhyk_normalization_rate: float = 0.0
    surzhyk_gate_cleared: bool = False

    all_gates_cleared: bool = False


# Phrases indicating that the model erroneously attempted to "correct" or eliminate authentic forms
DESTRUCTIVE_CORRECTION_PATTERNS = [
    re.compile(r"ненормативн\w*", re.IGNORECASE),
    re.compile(r"помилк\w*", re.IGNORECASE),
    re.compile(r"росіянізм\w*", re.IGNORECASE),
    re.compile(r"кальк\w*", re.IGNORECASE),
    re.compile(r"суржик\w*", re.IGNORECASE),
    re.compile(r"неправильно\s+вжит\w*", re.IGNORECASE),
    re.compile(r"замініть\s+на\b", re.IGNORECASE),
    re.compile(r"виправте\s+на\b", re.IGNORECASE),
    re.compile(r"слід\s+виправити\b", re.IGNORECASE),
    re.compile(r"не\s+відповідає\s+норм\w*", re.IGNORECASE),
    re.compile(r"порушення\s+норм\w*", re.IGNORECASE),
]

# Phrases indicating that the model erroneously legitimized or normalized Surzhyk
SURZHYK_NORMALIZATION_PATTERNS = [
    re.compile(r"речення\s+є\s+нормативн\w*", re.IGNORECASE),
    re.compile(r"не\s+потребує\s+виправленн\w*", re.IGNORECASE),
    re.compile(r"не\s+потребує\s+редагуванн\w*", re.IGNORECASE),
    re.compile(r"є\s+питомим\b", re.IGNORECASE),
    re.compile(r"є\s+діалектом\b", re.IGNORECASE),
    re.compile(r"діалектне\s+слово\b", re.IGNORECASE),
    re.compile(r"діалектна\s+форма\b", re.IGNORECASE),
    re.compile(r"діалектний\s+вираз\b", re.IGNORECASE),
    re.compile(r"регіональн\w*\s+варіант\w*", re.IGNORECASE),
    re.compile(r"є\s+літературн\w*", re.IGNORECASE),
    re.compile(r"відповідає\s+норм\w*", re.IGNORECASE),
    re.compile(r"вердикт:?\s*preserve", re.IGNORECASE),
]


def evaluate_single_case(case: dict[str, Any], raw_output: str) -> CaseEvaluationResult:
    """Evaluate a single test case from the Dialect & Historical Protection Suite."""
    eval_id = case["eval_id"]
    stratum = case["stratum"]
    subgroup = case["subgroup"]
    case_type = case["case_type"]
    target = case["target_term"]
    expected_replacement = case.get("expected_replacement")

    parsed = parse_model_output(raw_output)

    if not parsed.is_valid_format:
        return CaseEvaluationResult(
            eval_id=eval_id,
            stratum=stratum,
            subgroup=subgroup,
            case_type=case_type,
            target_term=target,
            is_pass=False,
            is_corrupted=(case_type == "PRESERVE"),
            is_surzhyk_normalized=False,
            failure_reason=f"malformed_output: {parsed.format_error}",
            parsed=parsed,
        )

    full_text = f"{parsed.thought_text}\n{parsed.final_response}"

    # Branch 1: PRESERVE Cases (Regional Dialect or Historical Text)
    if case_type == "PRESERVE":
        # The model MUST NOT label the authentic dialect/historical form as an error, calque, or Surzhyk
        # Check final response for destructive correction declarations
        has_destructive_claim = any(p.search(parsed.final_response) for p in DESTRUCTIVE_CORRECTION_PATTERNS)

        # Check if the target term was eliminated or replaced destructively in final_response
        target_preserved_in_response = (
            target.lower() in parsed.final_response.lower()
            or "зберігаємо" in parsed.final_response.lower()
            or "нормативн" in parsed.final_response.lower()
            or "автентичн" in parsed.final_response.lower()
            or "діалект" in parsed.final_response.lower()
            or "історичн" in parsed.final_response.lower()
            or "пам'ятк" in parsed.final_response.lower()
        )

        # Failure if it falsely flags the authentic form as a calque/error
        if has_destructive_claim:
            return CaseEvaluationResult(
                eval_id=eval_id,
                stratum=stratum,
                subgroup=subgroup,
                case_type=case_type,
                target_term=target,
                is_pass=False,
                is_corrupted=True,
                is_surzhyk_normalized=False,
                failure_reason=f"false_correction: authentic {stratum} token '{target}' was flagged as error/calque",
                parsed=parsed,
            )

        if not target_preserved_in_response:
            return CaseEvaluationResult(
                eval_id=eval_id,
                stratum=stratum,
                subgroup=subgroup,
                case_type=case_type,
                target_term=target,
                is_pass=False,
                is_corrupted=True,
                is_surzhyk_normalized=False,
                failure_reason=f"unauthorized_standardization: target '{target}' missing or removed from preserved response",
                parsed=parsed,
            )

        return CaseEvaluationResult(
            eval_id=eval_id,
            stratum=stratum,
            subgroup=subgroup,
            case_type=case_type,
            target_term=target,
            is_pass=True,
            is_corrupted=False,
            is_surzhyk_normalized=False,
            failure_reason=None,
            parsed=parsed,
        )

    # Branch 2: CORRECT Cases (Anti-Surzhyk Invariant Negative Controls)
    elif case_type == "CORRECT":
        # Check for FATAL Surzhyk Normalization (treating Surzhyk as acceptable, dialectal, or normative)
        is_normalized = any(p.search(parsed.final_response) for p in SURZHYK_NORMALIZATION_PATTERNS)

        if is_normalized:
            return CaseEvaluationResult(
                eval_id=eval_id,
                stratum=stratum,
                subgroup=subgroup,
                case_type=case_type,
                target_term=target,
                is_pass=False,
                is_corrupted=False,
                is_surzhyk_normalized=True,
                failure_reason=f"surzhyk_normalized: colonial calque '{target}' was falsely justified or normalized",
                parsed=parsed,
            )

        # Model must identify the error or mention the correct replacement
        has_correction = False
        if (expected_replacement and expected_replacement.lower() in full_text.lower()) or any(
            kw in full_text.lower()
            for kw in ("росіянізм", "кальк", "суржик", "ненормативн", "виправ", "замін", "вжива")
        ):
            has_correction = True

        if not has_correction:
            return CaseEvaluationResult(
                eval_id=eval_id,
                stratum=stratum,
                subgroup=subgroup,
                case_type=case_type,
                target_term=target,
                is_pass=False,
                is_corrupted=False,
                is_surzhyk_normalized=False,
                failure_reason=f"failed_eradication: failed to diagnose and replace Surzhyk calque '{target}'",
                parsed=parsed,
            )

        return CaseEvaluationResult(
            eval_id=eval_id,
            stratum=stratum,
            subgroup=subgroup,
            case_type=case_type,
            target_term=target,
            is_pass=True,
            is_corrupted=False,
            is_surzhyk_normalized=False,
            failure_reason=None,
            parsed=parsed,
        )

    raise ValueError(f"Unknown case_type: {case_type}")


def evaluate_protection_suite(
    cases: Sequence[dict[str, Any]],
    predictions: Sequence[str],
) -> tuple[ProtectionSuiteMetrics, list[CaseEvaluationResult]]:
    """Evaluate all cases and aggregate metrics."""
    if len(cases) != len(predictions):
        raise ValueError(f"Cases ({len(cases)}) and predictions ({len(predictions)}) length mismatch")

    results: list[CaseEvaluationResult] = []
    metrics = ProtectionSuiteMetrics(total_cases=len(cases))

    for case, pred in zip(cases, predictions, strict=True):
        res = evaluate_single_case(case, pred)
        results.append(res)

        stratum = case["stratum"]
        if stratum == "regional_dialect":
            metrics.dialect_total += 1
            if res.is_pass:
                metrics.dialect_preserved += 1
            else:
                metrics.dialect_corrupted += 1

        elif stratum == "historical_text":
            metrics.historical_total += 1
            if res.is_pass:
                metrics.historical_preserved += 1
            else:
                metrics.historical_corrupted += 1

        elif stratum == "anti_surzhyk_control":
            metrics.surzhyk_total += 1
            if res.is_pass:
                metrics.surzhyk_eradicated += 1
            if res.is_surzhyk_normalized:
                metrics.surzhyk_normalized += 1

    # Regional dialect rates
    if metrics.dialect_total > 0:
        metrics.dialect_preservation_rate = metrics.dialect_preserved / metrics.dialect_total
        metrics.dialect_clopper_pearson_lower = exact_clopper_pearson_lower(
            metrics.dialect_preserved, metrics.dialect_total
        )
        metrics.dialect_gate_cleared = (
            metrics.dialect_preservation_rate >= 0.980 and metrics.dialect_clopper_pearson_lower >= 0.965
        )

    # Historical text rates
    if metrics.historical_total > 0:
        metrics.historical_preservation_rate = metrics.historical_preserved / metrics.historical_total
        metrics.historical_clopper_pearson_lower = exact_clopper_pearson_lower(
            metrics.historical_preserved, metrics.historical_total
        )
        metrics.historical_gate_cleared = (
            metrics.historical_preservation_rate >= 0.980 and metrics.historical_clopper_pearson_lower >= 0.960
        )

    # Combined preservation (N=500)
    metrics.combined_preserve_total = metrics.dialect_total + metrics.historical_total
    metrics.combined_preserve_passed = metrics.dialect_preserved + metrics.historical_preserved
    if metrics.combined_preserve_total > 0:
        metrics.combined_preserve_rate = metrics.combined_preserve_passed / metrics.combined_preserve_total
        metrics.combined_clopper_pearson_lower = exact_clopper_pearson_lower(
            metrics.combined_preserve_passed, metrics.combined_preserve_total
        )
        metrics.combined_gate_cleared = (
            metrics.combined_preserve_rate >= 0.980 and metrics.combined_clopper_pearson_lower >= 0.970
        )

    # Anti-Surzhyk rates
    if metrics.surzhyk_total > 0:
        metrics.surzhyk_eradication_rate = metrics.surzhyk_eradicated / metrics.surzhyk_total
        metrics.surzhyk_normalization_rate = metrics.surzhyk_normalized / metrics.surzhyk_total
        # Zero tolerance for Surzhyk normalization
        metrics.surzhyk_gate_cleared = (
            metrics.surzhyk_normalization_rate == 0.0 and metrics.surzhyk_eradication_rate >= 0.900
        )

    # Master gate
    metrics.all_gates_cleared = (
        metrics.dialect_gate_cleared
        and metrics.historical_gate_cleared
        and metrics.combined_gate_cleared
        and metrics.surzhyk_gate_cleared
    )

    return metrics, results


def format_protection_report(metrics: ProtectionSuiteMetrics) -> str:
    """Format a detailed Markdown audit report of the evaluation."""
    return f"""# Ukrainian Dialect & Historical Protection Audit Report (Phase 5.2 / #8051)

> **Evaluation Target:** Anti-Over-Standardization & Anti-Surzhyk Invariant Gates
> **Total Test Cases:** {metrics.total_cases}
> **Generated:** {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")}
> **Overall Gate Status:** {"✅ PASSED (All Gates Cleared)" if metrics.all_gates_cleared else "❌ FAILED"}

---

## 1. Quality Gates Scorecard

| Gate | Target Requirement | Measured Rate | 95% Confidence Bound | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Regional Dialect Preservation Gate** | ≥ 98.0% non-corruption on N=300 | {metrics.dialect_preservation_rate:.2%} ({metrics.dialect_preserved}/{metrics.dialect_total}) | ≥ {metrics.dialect_clopper_pearson_lower:.2%} lower bound | {"✅ PASSED" if metrics.dialect_gate_cleared else "❌ FAILED"} |
| **Historical & Classical Preservation Gate** | ≥ 98.0% non-corruption on N=200 | {metrics.historical_preservation_rate:.2%} ({metrics.historical_preserved}/{metrics.historical_total}) | ≥ {metrics.historical_clopper_pearson_lower:.2%} lower bound | {"✅ PASSED" if metrics.historical_gate_cleared else "❌ FAILED"} |
| **Combined Cultural Heritage Preservation** | ≥ 98.0% non-corruption on N=500 | {metrics.combined_preserve_rate:.2%} ({metrics.combined_preserve_passed}/{metrics.combined_preserve_total}) | ≥ {metrics.combined_clopper_pearson_lower:.2%} lower bound | {"✅ PASSED" if metrics.combined_gate_cleared else "❌ FAILED"} |
| **Anti-Surzhyk Invariant Gate** | 0.0% normalization tolerance (N=100) | {metrics.surzhyk_normalization_rate:.2%} normalized | Exactly 0.0% required | {"✅ PASSED" if metrics.surzhyk_gate_cleared else "❌ FAILED"} |
| **Surzhyk Eradication Rate** | ≥ 90.0% eradication on N=100 | {metrics.surzhyk_eradication_rate:.2%} ({metrics.surzhyk_eradicated}/{metrics.surzhyk_total}) | Empirical rate | {"✅ PASSED" if metrics.surzhyk_eradication_rate >= 0.900 else "❌ FAILED"} |

---

## 2. Invariant Compliance Breakdown

1. **Regional Dialect Protection:**
   - Evaluated across Southwestern (Hutsul, Boyko, Lemko, Galician), Southeastern (Poltava, Slobozhan), and Northern (Polissian) groups.
   - Preserved: **{metrics.dialect_preserved} / {metrics.dialect_total}** ({metrics.dialect_preservation_rate:.2%}).
   - Corrupted by unauthorized standardization: **{metrics.dialect_corrupted}**.

2. **Historical & Classical Continuity:**
   - Evaluated across Old East Slavic (11th–13th c. chronicles, *Слово о полку Ігоревім*) and Middle Ukrainian (16th–18th c. Cossack chronicles, Skovoroda).
   - Preserved: **{metrics.historical_preserved} / {metrics.historical_total}** ({metrics.historical_preservation_rate:.2%}).
   - Corrupted by forced orthographic modernization: **{metrics.historical_corrupted}**.

3. **Absolute Anti-Surzhyk Invariant:**
   - Evaluated across authentic Russian interference calques and collocations from UA-GEC and Antonenko-Davydovych.
   - Normalized / treated as dialect: **{metrics.surzhyk_normalized} / {metrics.surzhyk_total}** (must be strictly 0).
   - Diagnosed and eradicated: **{metrics.surzhyk_eradicated} / {metrics.surzhyk_total}** ({metrics.surzhyk_eradication_rate:.2%}).

---
*Report certified by Phase 5.2 Automated Protection Evaluator.*
"""


def generate_mock_predictions(cases: Sequence[dict[str, Any]], mode: str) -> list[str]:
    """Generate deterministic mock model predictions for contract verification."""
    preds: list[str] = []
    for c in cases:
        stratum = c["stratum"]
        target = c["target_term"]
        case_type = c["case_type"]
        replacement = c.get("expected_replacement") or "виправлена форма"

        if mode == "perfect":
            if case_type == "PRESERVE":
                p = (
                    f"<thought>\n"
                    f"1. Аналіз контексту: фрагмент містить автентичну форму «{target}» ({stratum}).\n"
                    f"2. Культурний захист: форма є частиною української мовної спадщини і не є помилкою.\n"
                    f"3. Вердикт: зберігаємо без змін.\n"
                    f"</thought>\n"
                    f"Речення нормативне і не потребує змін. Автентична лексема «{target}» зберігається в оригінальному контексті."
                )
            else:
                p = (
                    f"<thought>\n"
                    f"1. Діагностика: вираз «{target}» є російською калькою та колоніальним суржиком.\n"
                    f"2. Чинна норма: питомий відповідник — «{replacement}».\n"
                    f"3. Вердикт: виправляємо.\n"
                    f"</thought>\n"
                    f"Вживайте «{replacement}» замість суржикового виразу «{target}»."
                )
        elif mode == "failing_over_standardization":
            # Model mistakenly standardizes/flattens dialect words into modern generic standard
            if stratum == "regional_dialect":
                p = (
                    f"<thought>\n"
                    f"1. Діагностика: слово «{target}» є діалектною помилкою.\n"
                    f"2. Норма: виправляємо на сучасний літературний стандарт.\n"
                    f"</thought>\n"
                    f"Це ненормативне слово. Замініть на загальновживане літературне слово."
                )
            elif case_type == "PRESERVE":
                p = (
                    f"<thought>\n1. Аналіз: історична форма.\n</thought>\n"
                    f"Речення нормативне. Форма «{target}» зберігається."
                )
            else:
                p = f"<thought>\n1. Діагностика: суржик.\n</thought>\nВживайте «{replacement}» замість «{target}»."
        elif mode == "failing_surzhyk_normalization":
            # Model mistakenly normalizes Surzhyk as acceptable dialect/colloquial
            if stratum == "anti_surzhyk_control":
                p = (
                    f"<thought>\n"
                    f"1. Аналіз: вираз «{target}» часто зустрічається в мовленні.\n"
                    f"2. Вердикт: вважаємо це діалектним або розмовним варіантом.\n"
                    f"</thought>\n"
                    f"Речення є нормативним і не потребує виправлення. Це допустимий регіональний варіант."
                )
            elif case_type == "PRESERVE":
                p = (
                    f"<thought>\n1. Аналіз: автентична форма.\n</thought>\n"
                    f"Речення нормативне. Форма «{target}» зберігається."
                )
            else:
                p = f"<thought>\n1. Виправлення.\n</thought>\nВживайте «{replacement}» замість «{target}»."
        else:
            raise ValueError(f"Unknown mock mode: {mode}")

        preds.append(p)
    return preds


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5.2 Dialect & Historical Protection Evaluator")
    parser.add_argument("--test-suite", type=Path, default=DEFAULT_TEST_SUITE_PATH, help="Path to test suite JSONL")
    parser.add_argument("--predictions", type=Path, default=None, help="Path to predictions JSONL file")
    parser.add_argument(
        "--demo-mode",
        choices=["perfect", "failing_over_standardization", "failing_surzhyk_normalization"],
        default=None,
        help="Run contract verification demo",
    )
    parser.add_argument("--output-report", type=Path, default=None, help="Path to write Markdown audit report")
    parser.add_argument("--output-json", type=Path, default=None, help="Path to write JSON evaluation metrics")

    args = parser.parse_args()

    suite_path = args.test_suite
    if not suite_path.exists():
        raise FileNotFoundError(f"Test suite not found at: {suite_path}")

    cases = [json.loads(line) for line in suite_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(cases)} test cases from {suite_path}")

    if args.demo_mode:
        print(f"Generating mock predictions for demo mode: {args.demo_mode}")
        predictions = generate_mock_predictions(cases, args.demo_mode)
    elif args.predictions:
        print(f"Loading predictions from: {args.predictions}")
        pred_lines = [
            line.strip() for line in args.predictions.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        predictions = []
        for line in pred_lines:
            try:
                obj = json.loads(line)
                predictions.append(obj.get("prediction") or obj.get("output") or obj.get("response") or line)
            except json.JSONDecodeError:
                predictions.append(line)
    else:
        print("No predictions or demo mode specified. Running default 'perfect' contract check.")
        predictions = generate_mock_predictions(cases, "perfect")

    metrics, _results = evaluate_protection_suite(cases, predictions)

    report_md = format_protection_report(metrics)
    print("\n" + report_md)

    if args.output_report:
        args.output_report.write_text(report_md, encoding="utf-8")
        print(f"Markdown report written to: {args.output_report}")

    if args.output_json:
        metrics_dict = asdict(metrics)
        args.output_json.write_text(json.dumps(metrics_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"JSON metrics written to: {args.output_json}")

    if not metrics.all_gates_cleared:
        print("❌ Warning: Not all protection gates were cleared!")
        sys.exit(1)
    else:
        print("✅ All protection quality gates passed!")


if __name__ == "__main__":
    main()
