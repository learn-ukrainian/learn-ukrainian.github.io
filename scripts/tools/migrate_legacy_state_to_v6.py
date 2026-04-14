#!/usr/bin/env python3
"""Migrate legacy v5/v3 orchestration state files to the v6 schema."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

V6_PHASE_ORDER = [
    "check",
    "research",
    "skeleton",
    "pre-verify",
    "write",
    "exercises",
    "activities",
    "repair",
    "verify-exercises",
    "annotate",
    "vocab",
    "enrich",
    "verify",
    "review",
    "stress",
    "publish",
    "audit",
]


@dataclass(frozen=True)
class PhaseRule:
    """How a legacy phase maps into the v6 state shape."""

    target: str | None
    justification: str
    precedence: int


V5_PHASE_RULES: dict[str, PhaseRule] = {
    "research": PhaseRule(
        target="research",
        justification="v5 research is the direct predecessor of v6 research.",
        precedence=10,
    ),
    "discover": PhaseRule(
        target="research",
        justification="v5 discover was explicitly merged into research in pipeline v5.",
        precedence=30,
    ),
    "content": PhaseRule(
        target="write",
        justification="v5 content is the prose-generation step; v6 split that into skeleton/write and write is the closest durable phase.",
        precedence=20,
    ),
    "validate": PhaseRule(
        target="verify",
        justification="v5 validate was the prose-only audit/screen/fix gate; v6 verify is the nearest quality gate.",
        precedence=20,
    ),
    "activities": PhaseRule(
        target="activities",
        justification="the activities sidecar phase kept the same responsibility in v6.",
        precedence=20,
    ),
    "review": PhaseRule(
        target="review",
        justification="cross-agent review remained a dedicated phase in v6.",
        precedence=20,
    ),
    "mdx": PhaseRule(
        target="publish",
        justification="v5 mdx rendered the final lesson artifact; v6 publish is the equivalent release/render step.",
        precedence=20,
    ),
}

V3_PHASE_RULES: dict[str, PhaseRule] = {
    "v3-A": PhaseRule(
        target="research",
        justification="historical v3 dashboards labeled A as Research; current v3 prompt artifacts also show Phase A is research+meta.",
        precedence=40,
    ),
    "v3-B": PhaseRule(
        target="write",
        justification="historical v3 dashboards labeled B as Content, which maps most closely to v6 write.",
        precedence=40,
    ),
    "v3-C": PhaseRule(
        target="activities",
        justification="historical v3 dashboards labeled C as Activities.",
        precedence=40,
    ),
    "v3-audit": PhaseRule(
        target="verify",
        justification="historical v3 audit happened before review/repair/final, so it aligns better with v6 verify than the terminal v6 audit.",
        precedence=40,
    ),
    "v3-D": PhaseRule(
        target="review",
        justification="historical v3 dashboards labeled D as Review.",
        precedence=40,
    ),
    "v3-E": PhaseRule(
        target="repair",
        justification="historical v3 dashboards labeled E as Repair.",
        precedence=40,
    ),
    "v3-F": PhaseRule(
        target="publish",
        justification="historical v3 dashboards labeled F as Final, which is closest to the published terminal artifact in v6.",
        precedence=40,
    ),
}


@dataclass
class Candidate:
    """One orchestration directory with legacy state to migrate."""

    track: str
    slug: str
    orch_dir: Path
    detected_mode: str
    migrated_from: str
    state_json_path: Path | None
    state_v3_path: Path | None
    v5_state: dict[str, Any] | None
    v3_state: dict[str, Any] | None


@dataclass
class MigrationReport:
    """Materialized migration output for a single candidate."""

    candidate: Candidate
    target_path: Path
    v6_state: dict[str, Any]
    mapped_pairs: list[tuple[str, str]]
    warnings: list[str]
    backups: list[tuple[Path, Path]]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.stem}-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _iter_orchestration_dirs(track: str | None) -> list[Path]:
    track_dirs = [CURRICULUM_ROOT / track] if track else sorted(p for p in CURRICULUM_ROOT.iterdir() if p.is_dir())
    orch_dirs: list[Path] = []
    for track_dir in track_dirs:
        orch_root = track_dir / "orchestration"
        if not orch_root.exists():
            continue
        orch_dirs.extend(sorted(p for p in orch_root.iterdir() if p.is_dir()))
    return orch_dirs


def detect_candidate(orch_dir: Path) -> Candidate | None:
    """Return a migration candidate if the directory has legacy state."""
    track = orch_dir.parent.parent.name
    slug = orch_dir.name
    state_json_path = orch_dir / "state.json"
    state_v3_path = orch_dir / "state-v3.json"

    v5_state: dict[str, Any] | None = None
    v3_state: dict[str, Any] | None = None

    if state_json_path.exists():
        data = _read_json(state_json_path)
        mode = data.get("mode")
        if mode == "v6":
            return Candidate(
                track=track,
                slug=slug,
                orch_dir=orch_dir,
                detected_mode="v6",
                migrated_from="v6",
                state_json_path=state_json_path,
                state_v3_path=state_v3_path if state_v3_path.exists() else None,
                v5_state=None,
                v3_state=_read_json(state_v3_path) if state_v3_path.exists() else None,
            )
        if mode == "v5":
            v5_state = data
        elif mode is not None:
            raise ValueError(f"Unsupported state.json mode for {track}/{slug}: {mode}")
        elif not state_v3_path.exists():
            raise ValueError(f"state.json for {track}/{slug} has no mode and no state-v3.json companion")

    if state_v3_path.exists():
        v3_state = _read_json(state_v3_path)

    if v5_state and v3_state:
        detected_mode = "both"
        migrated_from = "v5"
    elif v5_state:
        detected_mode = "v5"
        migrated_from = "v5"
    elif v3_state:
        detected_mode = "v3"
        migrated_from = "v3"
    else:
        return None

    return Candidate(
        track=track,
        slug=slug,
        orch_dir=orch_dir,
        detected_mode=detected_mode,
        migrated_from=migrated_from,
        state_json_path=state_json_path if state_json_path.exists() else None,
        state_v3_path=state_v3_path if state_v3_path.exists() else None,
        v5_state=v5_state,
        v3_state=v3_state,
    )


def _normalize_legacy_state(candidate: Candidate) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    if candidate.v5_state is not None:
        payloads["v5"] = copy.deepcopy(candidate.v5_state)
    if candidate.v3_state is not None:
        payloads["v3"] = copy.deepcopy(candidate.v3_state)
    if len(payloads) == 1:
        return next(iter(payloads.values()))
    return payloads


def _select_status(legacy_phase: dict[str, Any]) -> str:
    status = legacy_phase.get("status")
    return status if isinstance(status, str) and status else "complete"


def _apply_phase_rules(
    source_label: str,
    source_state: dict[str, Any] | None,
    rules: dict[str, PhaseRule],
    phases_out: dict[str, dict[str, Any]],
    phase_precedence: dict[str, int],
    mapped_pairs: list[tuple[str, str]],
    warnings: list[str],
) -> None:
    if not source_state:
        return

    for source_phase, legacy_phase in (source_state.get("phases") or {}).items():
        rule = rules.get(source_phase)
        if rule is None:
            warnings.append(
                f"{source_label} phase {source_phase!r} has no mapping; preserved only under legacy_state (__preserved_as_legacy__)."
            )
            continue
        if rule.target is None:
            warnings.append(
                f"{source_label} phase {source_phase!r} intentionally preserved as legacy only (__preserved_as_legacy__)."
            )
            continue

        mapped_pairs.append((source_phase, rule.target))
        candidate_payload = copy.deepcopy(legacy_phase)
        candidate_payload["status"] = _select_status(legacy_phase)

        current_precedence = phase_precedence.get(rule.target)
        if current_precedence is None or rule.precedence < current_precedence:
            phases_out[rule.target] = candidate_payload
            phase_precedence[rule.target] = rule.precedence


def build_v6_state(candidate: Candidate, migrated_at: str | None = None) -> MigrationReport:
    """Translate a legacy candidate into a v6 state payload."""
    if candidate.detected_mode == "v6":
        raise ValueError("build_v6_state() must not be called for already-v6 candidates")

    phases_out: dict[str, dict[str, Any]] = {}
    phase_precedence: dict[str, int] = {}
    mapped_pairs: list[tuple[str, str]] = []
    warnings: list[str] = []

    _apply_phase_rules(
        source_label="v5",
        source_state=candidate.v5_state,
        rules=V5_PHASE_RULES,
        phases_out=phases_out,
        phase_precedence=phase_precedence,
        mapped_pairs=mapped_pairs,
        warnings=warnings,
    )
    _apply_phase_rules(
        source_label="v3",
        source_state=candidate.v3_state,
        rules=V3_PHASE_RULES,
        phases_out=phases_out,
        phase_precedence=phase_precedence,
        mapped_pairs=mapped_pairs,
        warnings=warnings,
    )

    ordered_phases = {
        phase: phases_out[phase]
        for phase in V6_PHASE_ORDER
        if phase in phases_out
    }

    v6_state = {
        "mode": "v6",
        "track": candidate.track,
        "slug": candidate.slug,
        "migrated_from": candidate.migrated_from,
        "migrated_at": migrated_at or _now_iso(),
        "phases": ordered_phases,
        "legacy_state": _normalize_legacy_state(candidate),
    }

    return MigrationReport(
        candidate=candidate,
        target_path=candidate.orch_dir / "state.json",
        v6_state=v6_state,
        mapped_pairs=mapped_pairs,
        warnings=warnings,
        backups=[],
    )


def verify_v6_state(track: str, slug: str, orch_dir: Path, expected_state: dict[str, Any]) -> None:
    """Round-trip a v6 state through the API reader."""
    from api.state_helpers import detect_pipeline_version, load_module_state

    version = detect_pipeline_version(orch_dir)
    if version != "v6":
        raise AssertionError(f"Expected v6 for {track}/{slug}, got {version}")

    loaded = load_module_state(track, slug, orch_dir)
    if loaded != expected_state:
        raise AssertionError(f"Round-trip mismatch for {track}/{slug}")


def _backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.pre-migration.bak")


def apply_migration(report: MigrationReport) -> MigrationReport:
    """Write the v6 state and back up legacy v3 state when present."""
    backups: list[tuple[Path, Path]] = []
    candidate = report.candidate

    if candidate.state_v3_path and candidate.state_v3_path.exists():
        backup = _backup_path(candidate.state_v3_path)
        if not backup.exists():
            candidate.state_v3_path.replace(backup)
        else:
            # Preserve explicit idempotency on repeated apply runs in temp tests.
            candidate.state_v3_path.unlink()
        backups.append((candidate.state_v3_path, backup))

    _atomic_write_json(report.target_path, report.v6_state)

    return MigrationReport(
        candidate=report.candidate,
        target_path=report.target_path,
        v6_state=report.v6_state,
        mapped_pairs=report.mapped_pairs,
        warnings=report.warnings,
        backups=backups,
    )


def _verify_dry_run(report: MigrationReport) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        orch_dir = Path(tmpdir) / report.candidate.track / "orchestration" / report.candidate.slug
        orch_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(orch_dir / "state.json", report.v6_state)
        verify_v6_state(report.candidate.track, report.candidate.slug, orch_dir, report.v6_state)


def format_report(report: MigrationReport, dry_run: bool) -> str:
    """Render a concise diff-like summary block."""
    lines = [
        f"{'DRY-RUN' if dry_run else 'APPLY'} {report.candidate.track}/{report.candidate.slug}",
        f"  source: {report.candidate.detected_mode}",
    ]
    if report.candidate.state_json_path and report.candidate.detected_mode in {"v5", "both"}:
        lines.append(f"  from: {report.candidate.state_json_path}")
    if report.candidate.state_v3_path:
        lines.append(f"  legacy-v3: {report.candidate.state_v3_path}")
    lines.extend(
        [
            f"  target: {report.target_path}",
            f"  migrated_from: {report.v6_state['migrated_from']}",
            f"  phases mapped: {len(report.mapped_pairs)}",
        ]
    )
    for source_phase, target_phase in report.mapped_pairs:
        lines.append(f"    - {source_phase} -> {target_phase}")
    if report.backups:
        for old_path, backup_path in report.backups:
            lines.append(f"  backup: {old_path} -> {backup_path}")
    if report.warnings:
        for warning in report.warnings:
            lines.append(f"  warning: {warning}")
    else:
        lines.append("  warning: none")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--track", help="Track id to migrate (e.g. bio, lit-fantastika)")
    scope.add_argument("--all", action="store_true", help="Scan every track under curriculum/l2-uk-en")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview changes without writing (default)")
    mode.add_argument("--apply", action="store_true", help="Write migrated state.json files in place")

    parser.add_argument("--verify", action="store_true", help="Round-trip migrated states through scripts.api.state_helpers")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N matching orchestration directories")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dry_run = not args.apply
    track = None if args.all else args.track

    processed = 0
    errors: list[str] = []

    for orch_dir in _iter_orchestration_dirs(track):
        if args.limit is not None and processed >= args.limit:
            break

        try:
            candidate = detect_candidate(orch_dir)
            if candidate is None:
                continue
            processed += 1

            if candidate.detected_mode == "v6":
                print(f"INFO {candidate.track}/{candidate.slug} already mode=v6; skipping")
                continue

            report = build_v6_state(candidate)

            if dry_run:
                if args.verify:
                    _verify_dry_run(report)
                print(format_report(report, dry_run=True))
                continue

            applied = apply_migration(report)
            if args.verify:
                verify_v6_state(candidate.track, candidate.slug, candidate.orch_dir, applied.v6_state)
            print(format_report(applied, dry_run=False))
        except Exception as exc:
            errors.append(f"{orch_dir}: {exc}")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
