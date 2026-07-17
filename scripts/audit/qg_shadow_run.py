#!/usr/bin/env python3
"""Capture one live Tier-2 run and judge it in advisory Layer-B shadow mode.

This driver intentionally does not call the offline ``qg_bakeoff`` runner. It
uses the production QG prompt, policy, dispatcher, and deterministic gates,
then serializes that one authenticated dispatch into the replay artifact that
``layerb_shadow`` already understands.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for path in (str(PROJECT_ROOT), str(SCRIPTS_DIR)):
    with suppress(ValueError):
        sys.path.remove(path)
sys.path[:0] = [str(PROJECT_ROOT), str(SCRIPTS_DIR)]

from scripts.audit import layerb_shadow, llm_qg_shadow_store, llm_reviewer_dispatch, qg_workflow
from scripts.audit.content_surface_gates import policy_for_level
from scripts.audit.qg_run_serializer import RUN_SCHEMA_VERSION, serialize_qg_run_v2
from scripts.common.repo_root import resolve_repo_root

SHADOW_ARTIFACT_ARM = "production_shadow"


@dataclass(frozen=True, slots=True)
class ShadowRunResult:
    """Paths and identifiers produced by one advisory shadow run."""

    tier2_run_id: str
    shadow_run_id: str
    artifact_path: Path
    artifact_sha256: str
    layerb_report_path: Path
    markdown_path: Path
    layerb_exit_code: int


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tier2(record: Mapping[str, Any]) -> dict[str, Any]:
    workflow = record.get("qg_workflow")
    tiers = workflow.get("tiers") if isinstance(workflow, Mapping) else []
    for tier in tiers if isinstance(tiers, list) else []:
        if isinstance(tier, Mapping) and tier.get("tier") == 2:
            return dict(tier)
    raise ValueError("workflow record has no Tier-2 result")


def _approved_live_reviewer(
    target: qg_workflow.ReviewTarget,
    prompt: str,
) -> llm_reviewer_dispatch.DispatchResult:
    """Run the registered live route without module-local raw-response writes."""

    policy = policy_for_level(target.level)
    route = llm_reviewer_dispatch.route_for_review(
        policy_family=policy.family,
        factual_sensitive=policy.family == "seminar",
    )
    return llm_reviewer_dispatch.invoke_bridge_route(
        route,
        prompt,
        f"llm-qg-shadow-{target.level}-{target.slug}-{uuid4().hex[:8]}",
        no_module_persistence=True,
        module_dir=target.module_dir,
    )


def _require_writer_lineage(
    target: qg_workflow.ReviewTarget,
    author_family: str | None,
) -> llm_reviewer_dispatch.AuthorLineage:
    lineage = llm_reviewer_dispatch.resolve_author_lineage(
        level=target.level,
        slug=target.slug,
        module_dir=target.module_dir,
        explicit_author_family=author_family,
    )
    if not lineage.available:
        raise ValueError(
            "production shadow capture requires resolvable writer lineage; "
            "pass --author-family or supply build metadata/git X-Agent lineage"
        )
    if lineage.family == "fixture":
        raise ValueError("writer_family=fixture on a real module is a hard error")
    return lineage


def _artifact_for_capture(
    *,
    target: qg_workflow.ReviewTarget,
    record: Mapping[str, Any],
    tier2: Mapping[str, Any],
    lineage: llm_reviewer_dispatch.AuthorLineage,
) -> dict[str, Any]:
    dispatch = tier2.get("dispatch")
    payload = tier2.get("payload")
    tier2_run_id = tier2.get("tier2_run_id")
    if not isinstance(dispatch, Mapping) or not isinstance(payload, Mapping) or not isinstance(tier2_run_id, str):
        raise ValueError("Tier-2 capture is unavailable; shadow runs require a fresh captured live dispatch")
    qg_workflow_meta = record.get("qg_workflow") if isinstance(record.get("qg_workflow"), Mapping) else {}
    reviewer_family = dispatch.get("reviewer_family") or tier2.get("reviewer_family")
    if not isinstance(reviewer_family, str) or not reviewer_family:
        raise ValueError("Tier-2 capture has no reviewer lineage")
    return serialize_qg_run_v2(
        dispatch,
        payload,
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "arm": SHADOW_ARTIFACT_ARM,
            "run_index": 1,
            "created_at": _now_z(),
            "target": {
                "level": target.level,
                "slug": target.slug,
                "module_dir": str(target.module_dir),
                "content_sha": record.get("content_sha"),
                "prompt_hash": qg_workflow_meta.get("prompt_hash"),
            },
            "tier2_run_id": tier2_run_id,
            "model": {
                "pin": dispatch.get("reviewer_model_id"),
                "family": reviewer_family,
                "route_name": dispatch.get("route_name"),
            },
            "status": tier2.get("status"),
            "workflow_verdict": record.get("workflow_verdict"),
            "attempt_count": len(tier2.get("retry_history") or ()),
            "gate_outcomes": tier2.get("gate_outcomes") or {},
            "raw_response": tier2.get("raw_response"),
            "retry_history": tier2.get("retry_history") or [],
            "tool_call_count": dispatch.get("tool_call_count") or 0,
            "writer_family": lineage.family,
            "writer_lineage": {"source": lineage.source, "evidence": lineage.evidence},
            "qg_reviewer_family": reviewer_family,
        },
    )


def _write_markdown(
    path: Path,
    *,
    target: qg_workflow.ReviewTarget,
    artifact_path: Path,
    report_path: Path,
    report: Mapping[str, Any],
) -> None:
    records = report.get("records") if isinstance(report.get("records"), list) else []
    lines = [
        "# LLM-QG production shadow evidence",
        "",
        "Advisory only: this report does not change canonical LLM-QG gate state.",
        "",
        f"- Module: `{target.level}/{target.slug}`",
        f"- Artifact: `{artifact_path}`",
        f"- Layer-B report: `{report_path}`",
        f"- Tau: `{layerb_shadow.DEFAULT_TAU:.2f}`",
        "",
        "## Verdict rows",
        "",
        "| Fact check | Decision | Relation |",
        "| --- | --- | --- |",
    ]
    verdict_rows = 0
    for row in records:
        if not isinstance(row, Mapping):
            continue
        verdict_rows += 1
        lines.append(
            "| {fact} | {decision} | {relation} |".format(
                fact=str(row.get("fact_check_id") or "unknown").replace("|", "\\|"),
                decision=str(row.get("final_decision") or "AUDIT"),
                relation=str(row.get("aggregate_relation") or "AUDIT"),
            )
        )
    if not verdict_rows:
        lines.append("| none | AUDIT | no grounded fact checks |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_layerb(
    *,
    artifact_dir: Path,
    layerb_dir: Path,
    layerb_dry_run: bool,
    max_judge_calls: int | None,
    judge_command: str | None,
    judge_family: str | None,
    judge_model: str | None,
    judge_model_version: str | None,
    provider_account_lane: str | None,
    judge_attestation: Path | None,
    labels: Path | None,
    corpus_manifests: Sequence[Path],
    fixture_manifests: Sequence[Path],
) -> tuple[int, Path, dict[str, Any]]:
    args = [
        "--artifacts-dir",
        str(artifact_dir),
        "--audit-dir",
        str(layerb_dir),
        "--tau",
        str(layerb_shadow.DEFAULT_TAU),
    ]
    if max_judge_calls is not None:
        args.extend(("--max-judge-calls", str(max_judge_calls)))
    if layerb_dry_run:
        args.append("--dry-run")
    if judge_command is not None:
        args.extend(
            (
                "--judge-command",
                str(judge_command),
                "--judge-family",
                str(judge_family),
                "--judge-model",
                str(judge_model),
                "--judge-model-version",
                str(judge_model_version),
                "--provider-account-lane",
                str(provider_account_lane),
                "--judge-attestation",
                str(judge_attestation),
                "--labels",
                str(labels),
            )
        )
    elif not layerb_dry_run:
        required = {
            "judge_command": judge_command,
            "judge_family": judge_family,
            "judge_model": judge_model,
            "judge_model_version": judge_model_version,
            "provider_account_lane": provider_account_lane,
            "judge_attestation": judge_attestation,
            "labels": labels,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise ValueError("attested Layer-B shadow requires " + ", ".join(missing))

    # Always append manifests if they are passed
    for manifest in corpus_manifests:
        args.extend(("--corpus-manifest", str(manifest)))
    for manifest in fixture_manifests:
        args.extend(("--fixture-manifest", str(manifest)))
    exit_code = layerb_shadow.main(args)
    if exit_code not in {0, 3}:
        raise RuntimeError(f"layerb_shadow failed with exit code {exit_code}")
    report_path = layerb_dir / ("phase1-shadow.partial.json" if exit_code == 3 else "phase1-shadow.json")
    return exit_code, report_path, json.loads(report_path.read_text(encoding="utf-8"))


def run_shadow_module(
    target: qg_workflow.ReviewTarget,
    *,
    audit_dir: Path,
    shadow_db: Path,
    author_family: str | None = None,
    reviewer: qg_workflow.Reviewer | None = None,
    live_reviewer: bool = True,
    reviewer_model_id: str = qg_workflow.DEFAULT_REVIEWER_MODEL_ID,
    reviewer_family: str = qg_workflow.DEFAULT_REVIEWER_FAMILY,
    canary_artifacts: Mapping[str, Path] | None = None,
    max_cost_usd: float | None = None,
    max_llm_calls: int = 3,
    layerb_dry_run: bool = False,
    max_judge_calls: int | None = None,
    judge_command: str | None = None,
    judge_family: str | None = None,
    judge_model: str | None = None,
    judge_model_version: str | None = None,
    provider_account_lane: str | None = None,
    judge_attestation: Path | None = None,
    labels: Path | None = None,
    corpus_manifests: Sequence[Path] = (),
    fixture_manifests: Sequence[Path] = (),
) -> ShadowRunResult:
    """Run one fresh capture and persist only advisory shadow outcomes."""

    if layerb_shadow.DEFAULT_TAU != 0.75:
        raise RuntimeError("production shadow requires the pinned tau=0.75")
    lineage = _require_writer_lineage(target, author_family)
    effective_reviewer = reviewer or _approved_live_reviewer
    record = qg_workflow.review_module(
        target,
        options=qg_workflow.WorkflowOptions(
            reviewer_model_id=reviewer_model_id,
            reviewer_family=reviewer_family,
            live_reviewer=live_reviewer,
            author_family=lineage.family,
            canary_artifacts=canary_artifacts,
            enable_llm=True,
            max_cost_usd=max_cost_usd,
            max_llm_calls=max_llm_calls,
            use_llm_cache=False,
            persist_llm_qg=False,
            record_live_outcomes=False,
            record_daily_spend=False,
            capture_tier2=True,
        ),
        reviewer=effective_reviewer,
    )
    tier2 = _tier2(record)
    artifact = _artifact_for_capture(target=target, record=record, tier2=tier2, lineage=lineage)
    tier2_run_id = str(tier2["tier2_run_id"])
    run_dir = audit_dir / f"{target.level}-{target.slug}-{tier2_run_id.rsplit('-', 1)[-1]}"
    artifact_dir = run_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=False)
    artifact_path = artifact_dir / "qg-shadow-run.json"
    artifact_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    layerb_exit_code, layerb_report_path, layerb_report = _run_layerb(
        artifact_dir=artifact_dir,
        layerb_dir=run_dir / "layerb",
        layerb_dry_run=layerb_dry_run,
        max_judge_calls=max_judge_calls,
        judge_command=judge_command,
        judge_family=judge_family,
        judge_model=judge_model,
        judge_model_version=judge_model_version,
        provider_account_lane=provider_account_lane,
        judge_attestation=judge_attestation,
        labels=labels,
        corpus_manifests=corpus_manifests,
        fixture_manifests=fixture_manifests,
    )
    markdown_path = run_dir / "shadow-evidence.md"
    _write_markdown(
        markdown_path,
        target=target,
        artifact_path=artifact_path,
        report_path=layerb_report_path,
        report=layerb_report,
    )
    artifact_sha256 = _sha256(artifact_path)
    shadow_run_id = llm_qg_shadow_store.record_shadow_run(
        tier2_run_id=tier2_run_id,
        level=target.level,
        slug=target.slug,
        content_sha=str(record.get("content_sha") or ""),
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        layerb_report_path=layerb_report_path,
        writer_family=str(lineage.family),
        qg_reviewer_family=str(tier2.get("reviewer_family") or ""),
        tau=layerb_shadow.DEFAULT_TAU,
        summary=layerb_report.get("summary") if isinstance(layerb_report.get("summary"), Mapping) else {},
        findings=[row for row in layerb_report.get("records", []) if isinstance(row, Mapping)],
        path=shadow_db,
    )
    return ShadowRunResult(
        tier2_run_id=tier2_run_id,
        shadow_run_id=shadow_run_id,
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        layerb_report_path=layerb_report_path,
        markdown_path=markdown_path,
        layerb_exit_code=layerb_exit_code,
    )


def verify_artifact_survival(result: ShadowRunResult) -> list[str]:
    """Re-verify the replay-grade evidence still matches what the DB recorded.

    The first live shadow run's artifact tree vanished within ~2 minutes of a
    clean exit while the DB row kept pointing at it (#5195).  This probe runs
    at the last possible moment before the process exits so any deletion or
    split-universe path resolution (#5171 class) becomes a loud non-zero exit
    instead of a silently dangling DB row.
    """

    failures: list[str] = []
    for label, path in (
        ("shadow artifact", result.artifact_path),
        ("layer-b report", result.layerb_report_path),
        ("evidence markdown", result.markdown_path),
    ):
        if not path.is_file():
            failures.append(f"{label} missing at exit: {path}")
    # Hash-read under try: the whole point of this probe is that evidence can
    # vanish at ANY moment, including between the is_file() check and the read
    # (review finding: an uncaught OSError here would crash with rc=1 instead
    # of reporting the loss).
    if result.artifact_path.is_file():
        try:
            recomputed = _sha256(result.artifact_path)
        except OSError as exc:
            failures.append(f"shadow artifact unreadable at exit: {result.artifact_path} ({exc})")
        else:
            if recomputed != result.artifact_sha256:
                failures.append(f"shadow artifact content drifted between DB record and exit: {result.artifact_path}")
    return failures


def _canary_artifacts(values: Sequence[str]) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for value in values:
        level, separator, raw_path = value.partition("=")
        if not separator or not level or not raw_path:
            raise argparse.ArgumentTypeError("--canary-artifact must use LEVEL=PATH")
        artifacts[level.strip().lower()] = Path(raw_path)
    return artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-dir", type=Path, required=True)
    parser.add_argument("--level", required=True)
    parser.add_argument("--slug")
    parser.add_argument("--author-family")
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--shadow-db", type=Path, default=llm_qg_shadow_store.DEFAULT_DB_PATH)
    parser.add_argument("--canary-artifact", action="append", default=[], metavar="LEVEL=PATH")
    parser.add_argument("--max-cost-usd", type=float, required=True)
    parser.add_argument("--max-llm-calls", type=int, default=3)
    parser.add_argument("--layerb-dry-run", action="store_true", help="Capture Tier-2 but do not dispatch the judge.")
    parser.add_argument("--max-judge-calls", type=int)
    parser.add_argument("--judge-command")
    parser.add_argument("--judge-family")
    parser.add_argument("--judge-model")
    parser.add_argument("--judge-model-version")
    parser.add_argument("--provider-account-lane")
    parser.add_argument("--judge-attestation", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--corpus-manifest", action="append", default=[], type=Path)
    parser.add_argument("--fixture-manifest", action="append", default=[], type=Path)
    return parser


def _anchor_to_repo_root(path: Path) -> Path:
    """Resolve a relative operator path against the PRIMARY checkout root.

    The shadow DB default is already primary-root-anchored; resolving
    ``--audit-dir``/``--shadow-db`` against the process cwd instead lets one
    run split its evidence across two universes (DB row in the primary,
    artifact tree wherever cwd happened to be — the #5171 class, suspected in
    the #5195 vanished-artifact incident).  Absolute paths pass through
    untouched, so operators can still target anywhere explicitly.
    """

    if path.is_absolute():
        return path
    return resolve_repo_root(Path(__file__), 2) / path


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.audit_dir = _anchor_to_repo_root(args.audit_dir)
    args.shadow_db = _anchor_to_repo_root(args.shadow_db)
    target = qg_workflow.ReviewTarget(
        level=args.level,
        slug=args.slug or args.module_dir.name,
        module_dir=args.module_dir,
    )
    try:
        result = run_shadow_module(
            target,
            audit_dir=args.audit_dir,
            shadow_db=args.shadow_db,
            author_family=args.author_family,
            canary_artifacts=_canary_artifacts(args.canary_artifact),
            max_cost_usd=args.max_cost_usd,
            max_llm_calls=args.max_llm_calls,
            layerb_dry_run=args.layerb_dry_run,
            max_judge_calls=args.max_judge_calls,
            judge_command=args.judge_command,
            judge_family=args.judge_family,
            judge_model=args.judge_model,
            judge_model_version=args.judge_model_version,
            provider_account_lane=args.provider_account_lane,
            judge_attestation=args.judge_attestation,
            labels=args.labels,
            corpus_manifests=args.corpus_manifest,
            fixture_manifests=args.fixture_manifest,
        )
    except (OSError, ValueError, RuntimeError, argparse.ArgumentTypeError) as exc:
        print(f"qg shadow error: {exc}", file=sys.stderr)
        return 2
    print(f"Shadow artifact: {result.artifact_path}")
    print(f"Layer-B report: {result.layerb_report_path}")
    print(f"Local evidence: {result.markdown_path}")
    survival_failures = verify_artifact_survival(result)
    if survival_failures:
        for failure in survival_failures:
            print(f"qg shadow evidence lost: {failure}", file=sys.stderr)
        # rc=4, NOT 3: layerb_shadow already uses 3 for a partial (capped)
        # run, which propagates through layerb_exit_code — an orchestrator
        # must be able to tell "partial but healthy" from "evidence lost".
        return 4
    return result.layerb_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
