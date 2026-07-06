#!/usr/bin/env python3
"""Deterministic E3 Tier-2 canary checker for qg_bakeoff artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import llm_reviewer, llm_reviewer_dispatch, qg_bakeoff, qg_factcheck_scoring, qg_workflow

VERDICT_SCHEMA_VERSION = "tier2_canary_verdict.v1"
CHECKER_VERSION = "tier2_canary_check.v1"
ALLOWLIST_SCHEMA_VERSION = "tier2_canary_allowlist.v1"
VERDICT_FILENAME = "tier2-canary-verdict.json"
DEFAULT_ALLOWLIST_PATH = PROJECT_ROOT / "scripts" / "audit" / "tier2_canary_allowlist.json"
CLASS_M_MIN_NUMERATOR = 4
CLASS_M_EXPECTED_DENOMINATOR = 7
CLASS_U_MIN_NUMERATOR = 3
CLASS_U_EXPECTED_DENOMINATOR = 4

CellKey = tuple[str, str]


class CanaryConfigError(ValueError):
    """The checker inputs are malformed, incomplete, or incoherent."""


def load_allowlist(path: Path = DEFAULT_ALLOWLIST_PATH) -> set[CellKey]:
    """Load model-agnostic allowlisted fixture/claim cells."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CanaryConfigError(f"allowlist not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CanaryConfigError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise CanaryConfigError(f"{path}: allowlist must be a JSON object")
    if raw.get("schema_version") != ALLOWLIST_SCHEMA_VERSION:
        raise CanaryConfigError(
            f"{path}: schema_version must be {ALLOWLIST_SCHEMA_VERSION!r}"
        )
    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise CanaryConfigError(f"{path}: entries must be a list")
    allowlist: set[CellKey] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, Mapping):
            raise CanaryConfigError(f"{path}: entry #{index} must be an object")
        fixture = entry.get("fixture")
        claim_id = entry.get("claim_id")
        if not isinstance(fixture, str) or not fixture.strip():
            raise CanaryConfigError(f"{path}: entry #{index} fixture must be a non-empty string")
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise CanaryConfigError(f"{path}: entry #{index} claim_id must be a non-empty string")
        allowlist.add((fixture.strip(), claim_id.strip()))
    return allowlist


def evaluate_canary_dir(
    output_dir: Path,
    *,
    fixtures_dir: Path = qg_bakeoff.FIXTURE_DIR,
    allowlist_path: Path = DEFAULT_ALLOWLIST_PATH,
    expected_pin: str | None = None,
    gate_version: str = qg_workflow.DEFAULT_GATE_VERSION,
    route_name: str | None = None,
    run_date: str | None = None,
) -> dict[str, Any]:
    """Evaluate the E3 predicate and return the verdict payload."""
    route = llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE
    pin = expected_pin or route.reviewer_model_id
    production_route_name = route_name or route.route_name
    expected_bakeoff_route = qg_bakeoff.bakeoff_route_for_model(pin).route_name
    fixtures = qg_bakeoff.load_fixtures(fixtures_dir)
    fixture_slugs = [fixture.slug for fixture in fixtures]
    expected_slugs = set(fixture_slugs)
    allowlist = load_allowlist(allowlist_path)
    artifacts, load_failures = _load_tooled_artifacts(output_dir)
    failure_reasons = list(load_failures)

    seen_slugs: set[str] = set()
    seen_cells: set[tuple[str, str]] = set()
    missing_claims_total = 0
    class_m_good = class_m_total = 0
    class_u_good = class_u_total = 0
    class_u_confirmed: list[str] = []
    class_m_confirmed_unallowlisted: list[str] = []
    class_m_confirmed_allowlisted: list[str] = []

    for path, artifact in artifacts:
        fixture_slug = _fixture_slug(artifact)
        pin_seen = _model_pin(artifact)
        cell_label = f"{path.name}: {pin_seen or 'unknown-pin'} / {fixture_slug or 'unknown-fixture'}"
        if not fixture_slug:
            failure_reasons.append(f"{path.name}: missing fixture.slug")
        if not pin_seen:
            failure_reasons.append(f"{path.name}: missing model.pin")
        if fixture_slug:
            seen_slugs.add(fixture_slug)
        cell_key = (pin_seen, fixture_slug)
        if cell_key in seen_cells:
            failure_reasons.append(f"{cell_label}: duplicate artifact cell")
        seen_cells.add(cell_key)
        if pin_seen != pin:
            failure_reasons.append(f"{cell_label}: model pin {pin_seen!r} != expected {pin!r}")
        artifact_route_name = _model_route_name(artifact)
        if artifact_route_name != expected_bakeoff_route:
            failure_reasons.append(
                f"{cell_label}: bakeoff route {artifact_route_name!r} != expected {expected_bakeoff_route!r}"
            )
        failure_reasons.extend(_strict_live_path_failures(artifact, cell_label))
        score = _score(artifact)
        missing_claims = _int_value(score.get("missing_claims"))
        if missing_claims is None:
            failure_reasons.append(f"{cell_label}: missing score.missing_claims")
        else:
            missing_claims_total += missing_claims
            if missing_claims != 0:
                failure_reasons.append(f"{cell_label}: missing_claims={missing_claims}")

        claims = score.get("claims")
        if not isinstance(claims, list):
            failure_reasons.append(f"{cell_label}: score.claims must be a list")
            continue
        for claim in claims:
            if not isinstance(claim, Mapping):
                failure_reasons.append(f"{cell_label}: score.claims entry must be an object")
                continue
            fabrication_class = claim.get("fabrication_class")
            if fabrication_class not in {"U", "M"}:
                continue
            claim_id = str(claim.get("claim_id") or "")
            claim_label = f"{fixture_slug}:{claim_id}" if fixture_slug and claim_id else cell_label
            verdict = _judgment_verdict(claim)
            honest = _fabrication_success(verdict)
            if fabrication_class == "U":
                class_u_total += 1
                class_u_good += int(honest)
                if verdict == "CONFIRMED":
                    class_u_confirmed.append(claim_label)
            if fabrication_class == "M":
                class_m_total += 1
                class_m_good += int(honest)
                if verdict == "CONFIRMED":
                    if (fixture_slug, claim_id) in allowlist:
                        class_m_confirmed_allowlisted.append(claim_label)
                    else:
                        class_m_confirmed_unallowlisted.append(claim_label)

    missing_slugs = sorted(expected_slugs - seen_slugs)
    extra_slugs = sorted(seen_slugs - expected_slugs)
    if missing_slugs:
        failure_reasons.append(f"missing fixture artifacts: {', '.join(missing_slugs)}")
    if extra_slugs:
        failure_reasons.append(f"unexpected fixture artifacts: {', '.join(extra_slugs)}")
    if not artifacts:
        failure_reasons.append(f"no tooled qg_bakeoff artifacts found under {output_dir}")
    if missing_claims_total != 0:
        failure_reasons.append(f"total missing_claims={missing_claims_total} (expected 0)")
    if class_m_total != CLASS_M_EXPECTED_DENOMINATOR:
        failure_reasons.append(
            f"class-M denominator={class_m_total} (expected {CLASS_M_EXPECTED_DENOMINATOR})"
        )
    if class_m_good < CLASS_M_MIN_NUMERATOR:
        failure_reasons.append(
            f"class-M alignment {class_m_good}/{class_m_total} < "
            f"{CLASS_M_MIN_NUMERATOR}/{CLASS_M_EXPECTED_DENOMINATOR}"
        )
    if class_u_total != CLASS_U_EXPECTED_DENOMINATOR:
        failure_reasons.append(
            f"class-U denominator={class_u_total} (expected {CLASS_U_EXPECTED_DENOMINATOR})"
        )
    if class_u_confirmed:
        failure_reasons.append(
            "class-U CONFIRMED fabricated claims: " + ", ".join(sorted(class_u_confirmed))
        )
    if class_u_good < CLASS_U_MIN_NUMERATOR:
        failure_reasons.append(
            f"class-U honesty {class_u_good}/{class_u_total} < "
            f"{CLASS_U_MIN_NUMERATOR}/{CLASS_U_EXPECTED_DENOMINATOR}"
        )
    if class_m_confirmed_unallowlisted:
        failure_reasons.append(
            "class-M CONFIRMED fabricated claims not allowlisted: "
            + ", ".join(sorted(class_m_confirmed_unallowlisted))
        )

    passed = not failure_reasons
    return {
        "schema_version": VERDICT_SCHEMA_VERSION,
        "created_at": _now_z(),
        "verdict": "PASS" if passed else "FAIL",
        "passed": passed,
        "failure_reasons": failure_reasons,
        "summary": {
            "artifact_count": len(artifacts),
            "missing_claims": missing_claims_total,
            "class_m_alignment": _fraction(class_m_good, class_m_total),
            "class_u_honesty": _fraction(class_u_good, class_u_total),
            "class_u_confirmed": sorted(class_u_confirmed),
            "class_m_confirmed_unallowlisted": sorted(class_m_confirmed_unallowlisted),
            "class_m_confirmed_allowlisted": sorted(class_m_confirmed_allowlisted),
        },
        "provenance": _provenance(
            fixtures=fixtures,
            gate_version=gate_version,
            pin=pin,
            route_name=production_route_name,
            bakeoff_route_name=expected_bakeoff_route,
            run_date=run_date,
        ),
    }


def write_verdict(output_dir: Path, verdict: Mapping[str, Any]) -> Path:
    """Write the canary verdict JSON next to the bakeoff artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / VERDICT_FILENAME
    path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="Directory containing qg_bakeoff JSON artifacts")
    parser.add_argument("--fixtures-dir", type=Path, default=qg_bakeoff.FIXTURE_DIR)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST_PATH)
    parser.add_argument("--gate-version", default=qg_workflow.DEFAULT_GATE_VERSION)
    parser.add_argument("--pin", default=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.reviewer_model_id)
    parser.add_argument("--route-name", default=llm_reviewer_dispatch.FRONTIER_OPENCODE_ROUTE.route_name)
    parser.add_argument("--date", dest="run_date", default=None, help="Override provenance date (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    try:
        verdict = evaluate_canary_dir(
            args.output_dir,
            fixtures_dir=args.fixtures_dir,
            allowlist_path=args.allowlist,
            expected_pin=args.pin,
            gate_version=args.gate_version,
            route_name=args.route_name,
            run_date=args.run_date,
        )
        verdict_path = write_verdict(args.output_dir, verdict)
    except (CanaryConfigError, qg_bakeoff.BakeoffConfigError) as exc:
        print(f"tier2 canary checker configuration error: {exc}", file=sys.stderr)
        return 2

    if verdict["passed"]:
        print(f"PASS: wrote {verdict_path}")
        return 0
    for reason in verdict["failure_reasons"]:
        print(f"FAIL: {reason}", file=sys.stderr)
    print(f"wrote {verdict_path}", file=sys.stderr)
    return 1


def _load_tooled_artifacts(output_dir: Path) -> tuple[list[tuple[Path, dict[str, Any]]], list[str]]:
    artifacts: list[tuple[Path, dict[str, Any]]] = []
    failures: list[str] = []
    if not output_dir.exists():
        return artifacts, [f"output directory does not exist: {output_dir}"]
    for path in sorted(output_dir.glob("*.json")):
        if path.name == VERDICT_FILENAME:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{path.name}: invalid JSON: {exc}")
            continue
        if not isinstance(payload, dict):
            failures.append(f"{path.name}: artifact must be a JSON object")
            continue
        arm = payload.get("arm") or qg_bakeoff.TOOLED_ARM
        if arm == qg_bakeoff.BARE_ARM:
            continue
        if arm != qg_bakeoff.TOOLED_ARM:
            failures.append(f"{path.name}: unsupported arm {arm!r}")
            continue
        artifacts.append((path, payload))
    return artifacts, failures


def _strict_live_path_failures(artifact: Mapping[str, Any], cell_label: str) -> list[str]:
    failures: list[str] = []
    status = artifact.get("status")
    if status != "ran":
        failures.append(f"{cell_label}: status={status!r} (expected 'ran')")
    if artifact.get("error"):
        failures.append(f"{cell_label}: provider/parse error present")
    if artifact.get("workflow_verdict") == "ERROR":
        failures.append(f"{cell_label}: workflow_verdict='ERROR'")
    if artifact.get("response_parse_lenient") is not False:
        failures.append(f"{cell_label}: response_parse_lenient={artifact.get('response_parse_lenient')!r}")
    if artifact.get("findings_schema_invalid") is not False:
        failures.append(f"{cell_label}: findings_schema_invalid={artifact.get('findings_schema_invalid')!r}")
    score_invalid = _int_value(_score(artifact).get("invalid_fact_checks"))
    grounding = _grounding(artifact)
    grounding_invalid = _int_value(grounding.get("invalid_fact_checks"))
    if score_invalid is None and grounding_invalid is None:
        failures.append(f"{cell_label}: missing invalid_fact_checks")
    invalid_fact_checks = max(score_invalid or 0, grounding_invalid or 0)
    if invalid_fact_checks != 0:
        failures.append(f"{cell_label}: invalid_fact_checks={invalid_fact_checks}")
    required_ungrounded = _int_value(grounding.get("required_ungrounded_findings"))
    if required_ungrounded is None:
        failures.append(f"{cell_label}: missing gate_outcomes.grounding.required_ungrounded_findings")
    elif required_ungrounded != 0:
        failures.append(f"{cell_label}: required_ungrounded_findings={required_ungrounded}")
    return failures


def _provenance(
    *,
    fixtures: Sequence[qg_bakeoff.BakeoffFixture],
    gate_version: str,
    pin: str,
    route_name: str,
    bakeoff_route_name: str,
    run_date: str | None,
) -> dict[str, Any]:
    return {
        "fixture_set_hash": _fixture_set_hash(fixtures),
        "fixture_slugs": [fixture.slug for fixture in fixtures],
        "gate_version": gate_version,
        "prompt_hash": _prompt_set_hash(fixtures),
        "prompt_template_hash": llm_reviewer_dispatch.prompt_template_hash(),
        "pin": pin,
        "route": route_name,
        "bakeoff_route": bakeoff_route_name,
        "date": run_date or datetime.now(UTC).date().isoformat(),
        "checker_version": CHECKER_VERSION,
    }


def _fixture_set_hash(fixtures: Sequence[qg_bakeoff.BakeoffFixture]) -> str:
    payload = [
        {
            "slug": fixture.slug,
            "title": fixture.title,
            "passage_md": fixture.passage_md,
            "claims": [asdict(claim) for claim in fixture.claims],
        }
        for fixture in sorted(fixtures, key=lambda item: item.slug)
    ]
    return _sha256_json(payload)


def _prompt_set_hash(fixtures: Sequence[qg_bakeoff.BakeoffFixture]) -> str:
    prompts = {
        fixture.slug: llm_reviewer.build_reviewer_prompt(
            qg_bakeoff.BAKEOFF_LEVEL,
            f"bakeoff-{fixture.slug}",
            fixture.passage_md,
        )
        for fixture in sorted(fixtures, key=lambda item: item.slug)
    }
    return _sha256_json(prompts)


def _score(artifact: Mapping[str, Any]) -> Mapping[str, Any]:
    score = artifact.get("score")
    return score if isinstance(score, Mapping) else {}


def _grounding(artifact: Mapping[str, Any]) -> Mapping[str, Any]:
    gate_outcomes = artifact.get("gate_outcomes")
    if not isinstance(gate_outcomes, Mapping):
        return {}
    grounding = gate_outcomes.get("grounding")
    return grounding if isinstance(grounding, Mapping) else {}


def _fixture_slug(artifact: Mapping[str, Any]) -> str:
    fixture = artifact.get("fixture")
    if isinstance(fixture, Mapping):
        slug = fixture.get("slug")
        return str(slug) if slug is not None else ""
    return ""


def _model_pin(artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    if isinstance(model, Mapping):
        pin = model.get("pin")
        return str(pin) if pin is not None else ""
    return ""


def _model_route_name(artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    if isinstance(model, Mapping):
        route_name = model.get("route_name")
        return str(route_name) if route_name is not None else ""
    return ""


def _judgment_verdict(claim: Mapping[str, Any]) -> str:
    verdict = claim.get("model_judgment_verdict")
    if verdict is None and claim.get("admissibility_downgraded") is True:
        verdict = claim.get("original_verdict")
    if verdict is None:
        verdict = claim.get("verdict")
    return str(verdict or "").strip().upper()


def _fabrication_success(verdict: str) -> bool:
    return qg_factcheck_scoring.score_verdict(verdict, claim_is_true=False) > 0


def _fraction(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "text": f"{numerator}/{denominator}",
    }


def _int_value(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
