"""Deterministic pre-promote quality gate for enrolled seminar tracks."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.audit.wiki_completeness_gate import SEMINAR_LEVELS
from scripts.common.thresholds import seminar_promote_floors_for

ROOT = Path(__file__).resolve().parents[2]
CURRICULUM = ROOT / "curriculum" / "l2-uk-en"

KNOWN_FAMILIES = {
    "anthropic",
    "openai",
    "google",
    "deepseek",
    "xai",
    "cursor",
    "mistral",
}
CONTENT_HASH_ALGORITHM = "sha256"
CONTENT_HASH_BASIS = "lesson_sources_v2"

# Plan bookkeeping/positional fields excluded from the quality content hash. Changing a module's
# position in the track (resequence/renumber via `module:`/`sequence:`), its cross-links
# (`connects_to:`/`prerequisites:`), its slug/level, or a version bump must NOT invalidate a
# recorded quality score — none of those affect lesson quality. Mirrors
# check_plan_immutability.METADATA_ONLY_FIELDS (+ `version`). (v1→v2: 2026-06-25, folk reset
# resequence — a mid-track cut renumbered every later plan and falsely staled passing scores.)
_PLAN_HASH_EXCLUDED_FIELDS = frozenset(
    {"module", "sequence", "slug", "slug_intentional", "level", "connects_to", "prerequisites", "version"}
)
SCHEMA_VERSION = 1


def _level_key(level: str | None) -> str:
    return str(level or "").strip().casefold()


def _default_module_dir(level: str, slug: str, repo_root: Path) -> Path:
    return repo_root / "curriculum" / "l2-uk-en" / _level_key(level) / slug


def _plan_path(level: str, slug: str, repo_root: Path) -> Path:
    return repo_root / "curriculum" / "l2-uk-en" / "plans" / _level_key(level) / f"{slug}.yaml"


def _module_dir_path(
    level: str,
    slug: str,
    *,
    module_dir: Path | None,
    repo_root: Path,
) -> Path:
    return Path(module_dir) if module_dir is not None else _default_module_dir(level, slug, repo_root)


def _repo_rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def lesson_source_paths(
    level: str,
    slug: str,
    *,
    module_dir: Path | None = None,
    repo_root: Path = ROOT,
) -> tuple[Path, ...]:
    """Return the fixed-order source list for the promote content hash."""
    resolved_module_dir = _module_dir_path(
        level,
        slug,
        module_dir=module_dir,
        repo_root=repo_root,
    )
    return (
        _plan_path(level, slug, repo_root),
        resolved_module_dir / "module.md",
        resolved_module_dir / "activities.yaml",
        resolved_module_dir / "vocabulary.yaml",
        resolved_module_dir / "resources.yaml",
    )


def _is_plan_path(path: Path) -> bool:
    return "plans" in path.parts and path.suffix in {".yaml", ".yml"}


def _canonical_plan_bytes(path: Path) -> bytes:
    """Plan bytes for hashing with bookkeeping/positional fields stripped, canonically dumped.

    A resequence (`module:`/`sequence:`), a cross-link edit (`connects_to:`/`prerequisites:`),
    a slug/level change, or a version bump does not change lesson quality, so it must not stale a
    recorded score. Falls back to raw bytes if the plan cannot be parsed as a YAML mapping.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        return path.read_bytes()
    if not isinstance(data, dict):
        return path.read_bytes()
    filtered = {k: v for k, v in data.items() if k not in _PLAN_HASH_EXCLUDED_FIELDS}
    return yaml.safe_dump(filtered, allow_unicode=True, sort_keys=True).encode("utf-8")


def _hash_bytes_for(path: Path) -> bytes:
    """Raw bytes for content files; canonical metadata-stripped bytes for plan files."""
    return _canonical_plan_bytes(path) if _is_plan_path(path) else path.read_bytes()


def content_digest(files: Iterable[Path], *, repo_root: Path = ROOT) -> dict[str, Any]:
    """Compute the stable lesson_sources_v2 digest and per-file sha list.

    Plan files contribute a canonical hash with positional/bookkeeping fields stripped
    (see ``_PLAN_HASH_EXCLUDED_FIELDS``); all other lesson sources hash their raw bytes.
    """
    digest = hashlib.sha256()
    file_rows: list[dict[str, str]] = []
    for path in files:
        if not path.exists():
            continue
        data = _hash_bytes_for(path)
        file_sha = hashlib.sha256(data)
        rel = _repo_rel(path, repo_root)
        digest.update(rel.encode("utf-8") + b"\0" + file_sha.digest() + b"\0")
        file_rows.append({"path": rel, "sha256": file_sha.hexdigest()})
    return {
        "algorithm": CONTENT_HASH_ALGORITHM,
        "basis": CONTENT_HASH_BASIS,
        "digest": digest.hexdigest(),
        "files": file_rows,
    }


def content_hash(
    level: str,
    slug: str,
    *,
    module_dir: Path | None = None,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Compute the content hash for a lesson module and its source plan."""
    return content_digest(
        lesson_source_paths(level, slug, module_dir=module_dir, repo_root=repo_root),
        repo_root=repo_root,
    )


def _sidecar_path(level: str, slug: str, *, module_dir: Path | None, repo_root: Path) -> Path:
    return _module_dir_path(level, slug, module_dir=module_dir, repo_root=repo_root) / "promote_quality.json"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_family(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _family_from(sidecar: Mapping[str, Any], key: str) -> str | None:
    agent = sidecar.get(key)
    if not isinstance(agent, Mapping):
        return None
    return _normalized_family(agent.get("family"))


def _score_value(scores: Mapping[str, Any], dim: str) -> float | None:
    try:
        raw = scores[dim]
    except KeyError:
        return None
    if isinstance(raw, bool):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _content_staleness_failures(sidecar_hash: Mapping[str, Any], current_hash: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if sidecar_hash.get("algorithm") != CONTENT_HASH_ALGORITHM:
        failures.append("content_hash algorithm is not sha256")
    if sidecar_hash.get("basis") != CONTENT_HASH_BASIS:
        failures.append(f"content_hash basis is not {CONTENT_HASH_BASIS}")

    sidecar_digest = sidecar_hash.get("digest")
    if not isinstance(sidecar_digest, str):
        failures.append("content_hash digest missing or invalid")
        return failures

    if sidecar_digest == current_hash["digest"]:
        return failures

    recorded_rows = sidecar_hash.get("files")
    if not isinstance(recorded_rows, list):
        failures.append("content_hash files missing or invalid")
        return failures

    recorded: dict[str, str | None] = {}
    for row in recorded_rows:
        if not isinstance(row, Mapping):
            failures.append("content_hash files contain a non-object row")
            continue
        path = row.get("path")
        sha = row.get("sha256")
        if not isinstance(path, str) or not isinstance(sha, str):
            failures.append("content_hash files contain an invalid row")
            continue
        recorded[path] = sha

    current = {row["path"]: row["sha256"] for row in current_hash["files"]}
    for rel_path in sorted(recorded.keys() | current.keys()):
        if recorded.get(rel_path) != current.get(rel_path):
            failures.append(f"stale: {rel_path} changed since scoring")

    if not failures:
        failures.append("stale: content_hash digest changed since scoring")
    return failures


def _family_failures(sidecar: Mapping[str, Any], level: str) -> list[str]:
    failures: list[str] = []
    writer_family = _family_from(sidecar, "writer")
    reviewer_family = _family_from(sidecar, "reviewer")

    if writer_family not in KNOWN_FAMILIES:
        failures.append(f"unknown writer family: {writer_family or '<missing>'}")
    if reviewer_family not in KNOWN_FAMILIES:
        failures.append(f"unknown reviewer family: {reviewer_family or '<missing>'}")
    if writer_family in KNOWN_FAMILIES and reviewer_family in KNOWN_FAMILIES:
        if writer_family == reviewer_family:
            failures.append(f"reviewer family must differ from writer family: {reviewer_family}")
        if _level_key(level) == "folk" and reviewer_family == "deepseek":
            failures.append("folk reviewer family deepseek is barred for promote quality scoring")
    return failures


def _floor_failures(
    sidecar_floors: Any,
    current_floors: Mapping[str, float],
) -> list[str]:
    if sidecar_floors is None:
        return []
    if not isinstance(sidecar_floors, Mapping):
        return ["recorded floors are not an object"]

    failures: list[str] = []
    for dim, floor in current_floors.items():
        recorded = sidecar_floors.get(dim)
        if recorded is None:
            failures.append(f"recorded floor missing: {dim}")
            continue
        try:
            recorded_float = float(recorded)
        except (TypeError, ValueError):
            failures.append(f"recorded floor invalid: {dim}")
            continue
        if recorded_float != float(floor):
            failures.append(f"recorded floor stale: {dim} recorded {recorded_float:g}, current {float(floor):g}")

    extra = sorted(set(sidecar_floors) - set(current_floors))
    for dim in extra:
        failures.append(f"recorded floor unexpected: {dim}")
    return failures


def verify(
    level: str,
    slug: str,
    *,
    module_dir: Path | None = None,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Verify that an enrolled seminar module has a fresh passing sidecar."""
    floors = seminar_promote_floors_for(level)
    if floors is None:
        return {
            "applicable": False,
            "passed": True,
            "reason": "level not enrolled in pre-promote gate",
            "per_dim": [],
            "failures": [],
        }

    sidecar_file = _sidecar_path(level, slug, module_dir=module_dir, repo_root=repo_root)
    failures: list[str] = []
    per_dim: list[dict[str, Any]] = []

    if not sidecar_file.exists():
        failures.append(f"missing sidecar: {_repo_rel(sidecar_file, repo_root)}")
        return {
            "applicable": True,
            "passed": False,
            "reason": "; ".join(failures),
            "per_dim": per_dim,
            "failures": failures,
        }

    try:
        sidecar = json.loads(sidecar_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"sidecar JSON parse failed: {exc.msg}")
        return {
            "applicable": True,
            "passed": False,
            "reason": "; ".join(failures),
            "per_dim": per_dim,
            "failures": failures,
        }

    if not isinstance(sidecar, Mapping):
        failures.append("sidecar root is not an object")
        sidecar = {}

    if sidecar.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"unsupported schema_version: {sidecar.get('schema_version')!r}")

    sidecar_hash = sidecar.get("content_hash")
    if not isinstance(sidecar_hash, Mapping):
        failures.append("content_hash missing or invalid")
    else:
        current_hash = content_hash(level, slug, module_dir=module_dir, repo_root=repo_root)
        failures.extend(_content_staleness_failures(sidecar_hash, current_hash))

    failures.extend(_family_failures(sidecar, level))

    scores = sidecar.get("scores")
    if not isinstance(scores, Mapping):
        failures.append("scores missing or invalid")
        scores = {}

    for dim, floor in floors.items():
        score = _score_value(scores, dim)
        ok = score is not None and score >= float(floor)
        per_dim.append({"dim": dim, "score": score, "floor": float(floor), "ok": ok})
        if score is None:
            failures.append(f"missing or invalid score: {dim}")
        elif not ok:
            failures.append(f"score below floor: {dim} {score:g} < {float(floor):g}")

    failures.extend(_floor_failures(sidecar.get("floors"), floors))

    passed = not failures
    return {
        "applicable": True,
        "passed": passed,
        "reason": "all promote quality floors satisfied" if passed else "; ".join(failures),
        "per_dim": per_dim,
        "failures": failures,
    }


def _validate_family(family: str, field: str) -> str:
    normalized = _normalized_family(family)
    if normalized not in KNOWN_FAMILIES:
        raise ValueError(f"unknown {field} family: {family}")
    return normalized


def _review_artifact_record(path: Path, repo_root: Path) -> dict[str, str]:
    return {"path": _repo_rel(path, repo_root), "sha256": _sha256_file(path)}


def record(
    level: str,
    slug: str,
    *,
    module_dir: Path | None,
    repo_root: Path = ROOT,
    writer_family: str,
    writer_agent: str,
    writer_model: str,
    reviewer_family: str,
    reviewer_agent: str,
    reviewer_model: str,
    scores: Mapping[str, float],
    evidence: Mapping[str, str] | None,
    scored_at: str,
    assembled_mdx_path: Path | None = None,
    review_artifact: Path | None = None,
) -> dict[str, Any]:
    """Record a promote-quality sidecar by hashing the local source files."""
    floors = seminar_promote_floors_for(level)
    if floors is None:
        track = _level_key(level)
        scope = "seminar level" if track in SEMINAR_LEVELS else "level"
        raise ValueError(f"{scope} not enrolled in pre-promote gate: {level}")

    writer_family_key = _validate_family(writer_family, "writer")
    reviewer_family_key = _validate_family(reviewer_family, "reviewer")
    resolved_module_dir = _module_dir_path(
        level,
        slug,
        module_dir=module_dir,
        repo_root=repo_root,
    )
    resolved_module_dir.mkdir(parents=True, exist_ok=True)

    score_rows = {dim: float(score) for dim, score in scores.items()}
    per_dim = [
        score_rows.get(dim) is not None and score_rows[dim] >= float(floor)
        for dim, floor in floors.items()
    ]
    sidecar = {
        "schema_version": SCHEMA_VERSION,
        "track": _level_key(level),
        "slug": slug,
        "profile": f"{_level_key(level)}_promote_v1",
        "content_hash": content_hash(
            level,
            slug,
            module_dir=resolved_module_dir,
            repo_root=repo_root,
        ),
        "assembled_mdx_sha256": _sha256_file(assembled_mdx_path) if assembled_mdx_path else None,
        "writer": {
            "agent": writer_agent,
            "model": writer_model,
            "family": writer_family_key,
        },
        "reviewer": {
            "agent": reviewer_agent,
            "model": reviewer_model,
            "family": reviewer_family_key,
        },
        "scores": score_rows,
        "floors": {dim: float(floor) for dim, floor in floors.items()},
        "evidence": dict(evidence or {}),
        "verdict": "PASS" if all(per_dim) else "FAIL",
        "scored_at": scored_at,
        "review_artifact": _review_artifact_record(review_artifact, repo_root) if review_artifact else None,
    }

    sidecar_file = resolved_module_dir / "promote_quality.json"
    sidecar_file.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": sidecar_file, "sidecar": sidecar}


def _parse_key_value(raw: str, *, label: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"{label} must be dim=value: {raw}")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"{label} key is empty: {raw}")
    return key, value


def _parse_scores(items: list[str]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for item in items:
        key, value = _parse_key_value(item, label="--score")
        try:
            scores[key] = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"--score value must be numeric: {item}") from exc
    return scores


def _parse_evidence(items: list[str] | None) -> dict[str, str]:
    evidence: dict[str, str] = {}
    for item in items or []:
        key, value = _parse_key_value(item, label="--evidence")
        evidence[key] = value
    return evidence


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _print_verify_report(report: Mapping[str, Any], level: str, slug: str) -> None:
    if report["passed"]:
        if report["applicable"] is False:
            print(f"PASS promote_quality n/a for {level}/{slug}: {report['reason']}")
        else:
            print(f"PASS promote_quality for {level}/{slug}: {report['reason']}")
            for row in report.get("per_dim", []):
                print(f"- {row['dim']}: {row['score']} >= {row['floor']}")
        return

    print(f"FAIL promote_quality for {level}/{slug}: {report['reason']}")
    for failure in report.get("failures", []):
        print(f"- {failure}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="verify a promote-quality sidecar")
    verify_parser.add_argument("level")
    verify_parser.add_argument("slug")
    verify_parser.add_argument("--module-dir", type=Path)
    verify_parser.add_argument("--repo-root", type=Path, default=ROOT)
    verify_parser.add_argument("--json", action="store_true")

    record_parser = subparsers.add_parser("record", help="write a promote-quality sidecar")
    record_parser.add_argument("level")
    record_parser.add_argument("slug")
    record_parser.add_argument("--module-dir", type=Path)
    record_parser.add_argument("--repo-root", type=Path, default=ROOT)
    record_parser.add_argument("--writer-family", required=True)
    record_parser.add_argument("--writer-agent", required=True)
    record_parser.add_argument("--writer-model", required=True)
    record_parser.add_argument("--reviewer-family", required=True)
    record_parser.add_argument("--reviewer-agent", required=True)
    record_parser.add_argument("--reviewer-model", required=True)
    record_parser.add_argument("--score", action="append", default=[], required=True)
    record_parser.add_argument("--evidence", action="append")
    record_parser.add_argument("--scored-at")
    record_parser.add_argument("--assembled-mdx", type=Path)
    record_parser.add_argument("--review-artifact", type=Path)

    args = parser.parse_args(argv)
    if args.command == "verify":
        report = verify(args.level, args.slug, module_dir=args.module_dir, repo_root=args.repo_root)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            _print_verify_report(report, args.level, args.slug)
        return 0 if report["passed"] else 1

    try:
        result = record(
            args.level,
            args.slug,
            module_dir=args.module_dir,
            repo_root=args.repo_root,
            writer_family=args.writer_family,
            writer_agent=args.writer_agent,
            writer_model=args.writer_model,
            reviewer_family=args.reviewer_family,
            reviewer_agent=args.reviewer_agent,
            reviewer_model=args.reviewer_model,
            scores=_parse_scores(args.score),
            evidence=_parse_evidence(args.evidence),
            scored_at=args.scored_at or _utc_now_iso(),
            assembled_mdx_path=args.assembled_mdx,
            review_artifact=args.review_artifact,
        )
    except (argparse.ArgumentTypeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"wrote {result['path']}")
    print(f"verdict: {result['sidecar']['verdict']}")
    print(f"content_hash: {result['sidecar']['content_hash']['digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
