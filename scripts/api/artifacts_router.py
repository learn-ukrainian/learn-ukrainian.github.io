"""Artifacts API router — content-delivery-to-production gate check.

Mounted at /api/artifacts in main.py.

Endpoints:
    GET /api/artifacts/{track}/{slug}   Single-module gate snapshot
    GET /api/artifacts/ship-ready       Aggregate ship-ready list

Why this exists (GH #1309): before this router, the only way to ask
"which modules are ready to ship" was to scrape seven different endpoints
and cross-reference them. The artifact layer answers that question in
one call, with the EXACT set of gates defined as a tuple of booleans so
clients never guess at which combination means "ship-ready".

Boundary: this router is about the INTERNAL artifact state. The public
site (is it up, was the latest build deployed, does the canonical URL
404) lives in ``site_router.py`` — see that file for the public-facing
checks. Codex flagged that mixing these would muddy the contract.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import CURRICULUM_ROOT, LEVELS, PROJECT_ROOT
from .state_compute import _compute_shippable, _get_review_score
from .state_helpers import (
    find_content_file,
    get_audit_status,
    get_final_review_info,
    get_plan_slugs,
    get_word_target_from_plan,
)

router = APIRouter(tags=["artifacts"])

PLANS_ROOT = PROJECT_ROOT / "plans"


# ---------------------------------------------------------------------
# Gate checks — each returns a bool so ``ship_ready`` is (all gates true).
# ---------------------------------------------------------------------


def _has_frontmatter(content_path: Path) -> bool:
    """True if the MDX/MD file starts with a YAML frontmatter block.

    We only check the shape, not the schema — schema checks live in the
    audit layer and will have already run by the time anything reaches
    ship-ready. This gate catches the worst failure mode: the content
    file exists but is empty / half-written.
    """
    if not content_path.is_file():
        return False
    try:
        head = content_path.read_text(encoding="utf-8", errors="replace")[:512]
    except OSError:
        return False
    return bool(re.match(r"^---\s*\n.*?\n---\s*\n", head, re.DOTALL))


def _plan_not_changed_after_build(
    plan_path: Path, content_path: Path
) -> bool:
    """True if the plan is not newer than the content file.

    If the plan has been edited since the last build, the module needs
    a rebuild before shipping. Missing either side → False (something
    is incomplete).
    """
    if not plan_path.is_file() or not content_path.is_file():
        return False
    try:
        return plan_path.stat().st_mtime <= content_path.stat().st_mtime
    except OSError:
        return False


def _final_review_approved(final_review: dict | None) -> bool:
    if not final_review or not final_review.get("exists"):
        return False
    verdict = str(final_review.get("verdict") or "").upper()
    return verdict == "PASS"


def _word_target_met(audit: dict, word_target: int) -> bool:
    """True if the module meets its required word count.

    Explicitly returns ``False`` when ``word_target == 0`` — per
    project rule "word targets are MINIMUMS" (see
    ``claude_extensions/rules/non-negotiable-rules.md``), a module
    with no resolvable target is a plan bug, not a pass. Shipping
    it would hide that the plan is incomplete. Reviewer CONCERN
    Gemini-B / #1309: this is intentional; the plan-review step
    is where a missing ``word_target`` gets caught, not here.
    """
    wc = int(audit.get("word_count") or 0)
    return bool(word_target) and wc >= word_target


# ---------------------------------------------------------------------
# Per-module snapshot
# ---------------------------------------------------------------------


def _level_cfg(track: str) -> dict | None:
    return next((cfg for cfg in LEVELS if cfg["id"] == track), None)


def _compute_artifact_snapshot(track: str, slug: str) -> dict[str, Any]:
    """Return the full gate-by-gate snapshot for one module.

    Shape::
        {
          "track": "a1", "slug": "...",
          "gates": {
              "content_exists":    bool,
              "frontmatter_valid": bool,
              "word_target_met":   bool,
              "audit_pass":        bool,
              "final_review_pass": bool,
              "plan_fresh":        bool,
          },
          "ship_ready": bool,   # every gate green
          "audit":       {...},
          "review":      {...},
          "final_review": {...} | null,
          "word_count": int, "word_target": int,
          "content_path": "curriculum/l2-uk-en/a1/...md" | null,
          "plan_path":    "plans/a1/...yaml" | null,
        }
    """
    cfg = _level_cfg(track)
    if not cfg:
        return {"error": f"unknown track: {track}"}

    track_dir: Path = CURRICULUM_ROOT / cfg["path"]
    content_path = find_content_file(track_dir, slug)
    plan_path = PLANS_ROOT / track / f"{slug}.yaml"

    # If neither the content file nor the plan exists, the slug is
    # unknown on this track. Return an error sentinel so the HTTP
    # wrapper can 404 — otherwise a typo looks like "all gates
    # false" which is indistinguishable from a known module that's
    # legitimately unshippable (reviewer CONCERN Codex-1 / #1309).
    if not (content_path and content_path.is_file()) and not plan_path.is_file():
        return {"error": f"unknown module: {track}/{slug}"}

    audit = get_audit_status(track_dir, slug)
    review = _get_review_score(track_dir, slug)
    final_review = get_final_review_info(track_dir, slug)

    word_target = int(audit.get("word_target") or 0)
    if word_target == 0:
        word_target = int(get_word_target_from_plan(track, slug) or 0)

    gates = {
        "content_exists": bool(content_path and content_path.is_file()),
        "frontmatter_valid": bool(content_path) and _has_frontmatter(content_path),
        "word_target_met": _word_target_met(audit, word_target),
        "audit_pass": str(audit.get("status") or "").lower() == "pass",
        "final_review_pass": _final_review_approved(final_review),
        "plan_fresh": bool(content_path) and _plan_not_changed_after_build(plan_path, content_path),
    }

    # ``_compute_shippable`` is the legacy audit+review definition and
    # does NOT include plan_fresh / frontmatter / final_review. We keep
    # it in the response for back-compat with existing dashboards, but
    # ``ship_ready`` is the strict new definition.
    legacy_shippable = _compute_shippable(audit.get("status", ""), review.get("score"))

    return {
        "track": track,
        "slug": slug,
        "gates": gates,
        "ship_ready": all(gates.values()),
        "legacy_shippable": legacy_shippable,
        "audit": {
            "status": audit.get("status"),
            "word_count": int(audit.get("word_count") or 0),
            "word_target": word_target,
            "blocking_issues": audit.get("blocking_issues", []),
        },
        "review": review,
        "final_review": final_review,
        "content_path": (
            str(content_path.relative_to(PROJECT_ROOT)) if content_path else None
        ),
        "plan_path": (
            str(plan_path.relative_to(PROJECT_ROOT)) if plan_path.exists() else None
        ),
    }


@router.get("/{track}/{slug}")
async def module_artifact(track: str, slug: str):
    """Single-module artifact snapshot."""
    result = await asyncio.to_thread(_compute_artifact_snapshot, track, slug)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result


# ---------------------------------------------------------------------
# Aggregate ship-ready list
# ---------------------------------------------------------------------


def _list_ship_ready(track_filter: str | None) -> dict[str, Any]:
    """Walk every plan and return the modules whose every gate is green.

    ``track_filter`` narrows the scan to one level. Empty tracks or
    missing plan dirs are silently skipped — the response reports what
    was inspected.
    """
    ship_ready: list[dict[str, Any]] = []
    inspected = 0
    tracks_scanned: list[str] = []

    for cfg in LEVELS:
        if track_filter and cfg["id"] != track_filter:
            continue
        tracks_scanned.append(cfg["id"])
        for _, slug in get_plan_slugs(cfg["id"]):
            inspected += 1
            snap = _compute_artifact_snapshot(cfg["id"], slug)
            if snap.get("ship_ready"):
                ship_ready.append({
                    "track": cfg["id"],
                    "slug": slug,
                    "review_score": snap.get("review", {}).get("score"),
                    "word_count": snap.get("audit", {}).get("word_count"),
                    "word_target": snap.get("audit", {}).get("word_target"),
                })

    return {
        "tracks_scanned": tracks_scanned,
        "modules_inspected": inspected,
        "ship_ready_count": len(ship_ready),
        "ship_ready": ship_ready,
    }


# ---------------------------------------------------------------------
# Force-preview — dry run for v6_build.py --force (#1313 / Codex-9)
# ---------------------------------------------------------------------


def _enumerate_force_deletions(track: str, slug: str) -> list[dict[str, Any]]:
    """Mirror ``v6_build._force_reset_module`` — enumerate what would go.

    MUST stay in sync with ``scripts/build/v6_build.py`` helpers
    ``_clean_build_artifacts`` (lines ~797-858) and
    ``_force_reset_module`` (lines ~860-880). A separate helper
    — not a direct import of v6_build — is deliberate: importing
    v6_build here would pull the whole pipeline module (gemini SDK,
    broker, runtime) into every API startup, which is too heavy for
    a read-only preview.

    Drift risk: if ``_clean_build_artifacts`` changes, this preview
    diverges. The test pins the exact set of paths so a v6_build
    change that adds or removes a target will flip a test red.
    """
    cfg = _level_cfg(track)
    if not cfg:
        return []

    base: Path = CURRICULUM_ROOT / cfg["path"]
    orch = base / "orchestration" / slug
    targets: list[dict[str, Any]] = []

    def _add(path: Path, category: str, reason: str) -> None:
        if path.exists():
            targets.append({
                "path": str(path.relative_to(PROJECT_ROOT)),
                "category": category,
                "is_dir": path.is_dir(),
                "size_bytes": (
                    sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
                    if path.is_dir()
                    else path.stat().st_size
                ),
                "reason": reason,
            })

    # Content + activities + vocab (see _clean_build_artifacts:812-819).
    _add(base / f"{slug}.md", "content", "module markdown")
    _add(base / "activities" / f"{slug}.yaml", "activities", "activity YAML")
    _add(base / "vocabulary" / f"{slug}.yaml", "vocabulary", "vocabulary YAML")

    # Review files (see _clean_build_artifacts:822-826).
    review_dir = base / "review"
    if review_dir.is_dir():
        for f in sorted(review_dir.glob(f"{slug}-review*")):
            _add(f, "review", "review output")

    # Audit + status (see _clean_build_artifacts:829-835).
    _add(base / "audit" / f"{slug}-audit.md", "audit", "audit report")
    _add(base / "status" / f"{slug}.json", "status", "status cache")

    # Research (see _clean_build_artifacts:838-841).
    _add(base / "research" / f"{slug}-knowledge-packet.md", "research", "knowledge packet")

    # Orchestration artifacts — everything except index.md + friction.yaml
    # (see _clean_build_artifacts:844-854).
    if orch.is_dir():
        keep = {"index.md", "friction.yaml"}
        for f in sorted(orch.iterdir()):
            if f.name in keep:
                continue
            _add(f, "orchestration", "pipeline state / prompts / dispatch")

    # Published MDX (see _force_reset_module:877-879).
    mdx = PROJECT_ROOT / "starlight" / "src" / "content" / "docs" / track / f"{slug}.mdx"
    _add(mdx, "published", "starlight MDX output")

    return targets


@router.get("/{track}/{slug}/force-preview")
async def force_preview(track: str, slug: str):
    """Dry-run preview for ``v6_build.py --force {track} {num}``.

    Returns the EXACT list of files ``--force`` would delete, without
    touching anything. Classified by category so a reviewer can spot
    anomalies (e.g. a 50 MB orchestration dir, or a stray published
    MDX that shouldn't exist). Reviewer Codex-9 / #1313.

    Shape::
        {
          "track": "a1", "slug": "...",
          "count": 12,
          "total_bytes": 234567,
          "would_remove": [
            {"path": "curriculum/l2-uk-en/a1/hello.md",
             "category": "content", "is_dir": false,
             "size_bytes": 8432, "reason": "module markdown"},
            ...
          ],
          "preserved": ["plans/a1/hello.yaml", "orchestration/hello/index.md",
                        "orchestration/hello/friction.yaml"]
        }

    **Never** deletes anything. This is a read-only endpoint.
    """
    cfg = _level_cfg(track)
    if not cfg:
        return JSONResponse(
            status_code=404,
            content={"error": f"unknown track: {track}"},
        )

    targets = await asyncio.to_thread(_enumerate_force_deletions, track, slug)

    base = CURRICULUM_ROOT / cfg["path"]
    preserved: list[str] = []
    plan = PLANS_ROOT / track / f"{slug}.yaml"
    if plan.is_file():
        preserved.append(str(plan.relative_to(PROJECT_ROOT)))
    for keep_name in ("index.md", "friction.yaml"):
        keep = base / "orchestration" / slug / keep_name
        if keep.is_file():
            preserved.append(str(keep.relative_to(PROJECT_ROOT)))

    return {
        "track": track,
        "slug": slug,
        "count": len(targets),
        "total_bytes": sum(t.get("size_bytes", 0) for t in targets),
        "would_remove": targets,
        "preserved": preserved,
    }


# ---------------------------------------------------------------------
# ship-ready (aggregate)
# ---------------------------------------------------------------------


@router.get("/ship-ready")
async def ship_ready(
    track: str | None = Query(
        None,
        description="Narrow the scan to one track id (e.g. 'a1'). Omit to scan all.",
    ),
):
    """Modules that pass EVERY artifact gate — safe to deploy.

    Unknown ``track`` → 404 (consistent with
    ``/api/artifacts/{track}/{slug}``, which also 404s on unknown
    tracks — reviewer CONCERN Codex-2 / #1309).
    """
    if track is not None and _level_cfg(track) is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"unknown track: {track}"},
        )
    return await asyncio.to_thread(_list_ship_ready, track)


# ---------------------------------------------------------------------
# Classified file manifest (#1313 / Codex-2)
# ---------------------------------------------------------------------


_ARTIFACT_CATEGORIES: tuple[tuple[str, str], ...] = (
    # (category, reason-for-classification)
    ("source_of_truth", "editable by humans, never regenerated by the pipeline"),
    ("generated", "pipeline output — regenerable from source of truth"),
    ("published", "live on the starlight site"),
    ("stale", "artifact from a prior build + source has since changed"),
)


def _classify_module_files(track: str, slug: str) -> dict[str, Any]:
    """Walk every file tied to one module and tag its lifecycle role.

    Reviewer Codex-2 / #1313: "would make --force work and cleanup
    reasoning much safer". Pipeline:
    - ``plans/{track}/{slug}.yaml`` + ``orchestration/{slug}/friction.yaml``
      + ``orchestration/{slug}/index.md`` → source of truth (never
      regenerated).
    - Everything else under the module's track directory → generated.
    - ``starlight/src/content/docs/{track}/{slug}.mdx`` → published.
    - A generated artifact is ``stale`` if the plan YAML mtime is
      newer than its own mtime — the source has moved on.
    """
    cfg = _level_cfg(track)
    if not cfg:
        return {"error": f"unknown track: {track}"}

    base: Path = CURRICULUM_ROOT / cfg["path"]
    orch = base / "orchestration" / slug
    plan_path = PLANS_ROOT / track / f"{slug}.yaml"
    mdx_path = (
        PROJECT_ROOT / "starlight" / "src" / "content" / "docs" / track / f"{slug}.mdx"
    )

    plan_mtime = plan_path.stat().st_mtime if plan_path.is_file() else None

    buckets: dict[str, list[dict[str, Any]]] = {
        "source_of_truth": [],
        "generated": [],
        "published": [],
        "stale": [],
    }

    def _record(path: Path, bucket: str) -> None:
        if not path.exists():
            return
        is_dir = path.is_dir()
        size = (
            sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
            if is_dir else path.stat().st_size
        )
        mtime = path.stat().st_mtime if not is_dir else max(
            (p.stat().st_mtime for p in path.rglob("*") if p.is_file()),
            default=path.stat().st_mtime,
        )
        entry = {
            "path": str(path.relative_to(PROJECT_ROOT)),
            "is_dir": is_dir,
            "size_bytes": size,
            "mtime": mtime,
        }
        # Stale check: pipeline output older than the plan is suspect.
        if bucket == "generated" and plan_mtime is not None and mtime < plan_mtime:
            entry["reason"] = "older than plan.yaml — rebuild recommended"
            buckets["stale"].append(entry)
            return
        buckets[bucket].append(entry)

    # Source of truth
    if plan_path.is_file():
        _record(plan_path, "source_of_truth")
    for keep in ("index.md", "friction.yaml"):
        _record(orch / keep, "source_of_truth")

    # Generated — the same paths that --force would delete, minus the
    # published MDX which has its own bucket.
    _record(base / f"{slug}.md", "generated")
    _record(base / "activities" / f"{slug}.yaml", "generated")
    _record(base / "vocabulary" / f"{slug}.yaml", "generated")
    review_dir = base / "review"
    if review_dir.is_dir():
        for f in sorted(review_dir.glob(f"{slug}-review*")):
            _record(f, "generated")
    _record(base / "audit" / f"{slug}-audit.md", "generated")
    _record(base / "status" / f"{slug}.json", "generated")
    _record(base / "research" / f"{slug}-knowledge-packet.md", "generated")
    if orch.is_dir():
        keep = {"index.md", "friction.yaml"}
        for f in sorted(orch.iterdir()):
            if f.name in keep:
                continue
            _record(f, "generated")

    # Published
    _record(mdx_path, "published")

    return {
        "track": track,
        "slug": slug,
        "counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
        "categories": [
            {"name": name, "reason": reason} for name, reason in _ARTIFACT_CATEGORIES
        ],
    }


@router.get("/{track}/{slug}/files")
async def module_files(track: str, slug: str):
    """Classified file manifest for one module (#1313 / Codex-2)."""
    result = await asyncio.to_thread(_classify_module_files, track, slug)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result


# ---------------------------------------------------------------------
# Review snapshot (#1313 / Codex-3)
# ---------------------------------------------------------------------


def _read_review_file(path: Path) -> dict[str, Any] | None:
    """Parse one review file. Extract score, verdict, findings count.

    "Empty findings with high score" is the reviewer-gaming pattern
    Codex wants flagged — ``empty_findings_flag`` captures it.
    """
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    from .review_parsing import (
        count_review_issues,
        extract_review_score,
        extract_review_verdict,
    )

    score = extract_review_score(text)
    verdict = extract_review_verdict(text)
    findings = count_review_issues(text)

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "score": score,
        "verdict": verdict,
        "findings_count": findings,
        "empty_findings_flag": (
            findings == 0 and score is not None and score >= 8.5
        ),
    }


def _review_snapshot(track: str, slug: str) -> dict[str, Any]:
    cfg = _level_cfg(track)
    if not cfg:
        return {"error": f"unknown track: {track}"}

    base: Path = CURRICULUM_ROOT / cfg["path"]
    review_dir = base / "review"

    # Main review — the canonical per-module review file. Pipeline
    # writes several naming variants over time; pick the newest match.
    main_candidates: list[Path] = []
    if review_dir.is_dir():
        for pattern in (f"{slug}-review*.md", f"{slug}-final-review*.md"):
            main_candidates.extend(review_dir.glob(pattern))
    main_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    main_review = (
        _read_review_file(main_candidates[0]) if main_candidates else None
    )

    # Style review — separate file, same directory. Empty if absent.
    style_candidates = (
        sorted(review_dir.glob(f"{slug}-style-review*.md"))
        if review_dir.is_dir() else []
    )
    style_review = (
        _read_review_file(style_candidates[-1]) if style_candidates else None
    )

    return {
        "track": track,
        "slug": slug,
        "main_review": main_review,
        "style_review": style_review,
        "any_empty_findings_flag": bool(
            (main_review and main_review.get("empty_findings_flag"))
            or (style_review and style_review.get("empty_findings_flag"))
        ),
    }


@router.get("/{track}/{slug}/review-snapshot")
async def review_snapshot(track: str, slug: str):
    """Latest main + style review result with empty-findings flag.

    Flags the reviewer-gaming pattern where a high score is reported
    with zero actionable findings (#1313 / Codex-3). Deterministic
    detection so bad-review cases don't slip through.
    """
    result = await asyncio.to_thread(_review_snapshot, track, slug)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result


# ---------------------------------------------------------------------
# Drift check (#1313 / Codex-8)
# ---------------------------------------------------------------------


def _state_drift_check(track: str, slug: str) -> dict[str, Any]:
    """Cross-check state.json vs audit vs review vs published MDX.

    Catches the recurring pipeline failure where one system says
    "done" and another says "missing". Reports each disagreement as
    a named ``drift`` entry so callers can decide which side to
    trust (#1313 / Codex-8).
    """
    cfg = _level_cfg(track)
    if not cfg:
        return {"error": f"unknown track: {track}"}

    base: Path = CURRICULUM_ROOT / cfg["path"]
    orch = base / "orchestration" / slug
    content_path = find_content_file(base, slug)
    state_path = orch / "state.json"
    audit = get_audit_status(base, slug)
    final_review = get_final_review_info(base, slug)
    mdx = (
        PROJECT_ROOT / "starlight" / "src" / "content" / "docs" / track / f"{slug}.mdx"
    )

    drifts: list[dict[str, str]] = []

    state_phases: dict[str, Any] = {}
    if state_path.is_file():
        try:
            import json
            state_phases = (json.loads(state_path.read_text("utf-8")) or {}).get("phases") or {}
        except Exception:
            drifts.append({
                "kind": "state_unreadable",
                "detail": f"{state_path} exists but failed to parse",
            })

    publish_phase = state_phases.get("publish") if isinstance(state_phases, dict) else None

    # state says publish complete, but no MDX on disk
    if (
        isinstance(publish_phase, dict)
        and publish_phase.get("status") == "complete"
        and not mdx.is_file()
    ):
        drifts.append({
            "kind": "publish_mdx_missing",
            "detail": "state.json says publish complete but starlight MDX missing",
        })

    # mdx exists but state disagrees
    if mdx.is_file() and not (
        isinstance(publish_phase, dict) and publish_phase.get("status") == "complete"
    ):
        drifts.append({
            "kind": "mdx_without_state",
            "detail": "published MDX on disk but state.json has no publish=complete",
        })

    # audit says pass but content file missing
    if str(audit.get("status") or "").lower() == "pass" and not (
        content_path and content_path.is_file()
    ):
        drifts.append({
            "kind": "audit_passes_without_content",
            "detail": "status.json pass but no content .md on disk",
        })

    # final-review APPROVED but content file missing
    if final_review and final_review.get("verdict", "").upper() == "PASS" and not (
        content_path and content_path.is_file()
    ):
        drifts.append({
            "kind": "final_review_without_content",
            "detail": "final review PASS but no content .md on disk",
        })

    # content exists but audit never ran
    if content_path and content_path.is_file() and str(audit.get("status") or "") == "not_run":
        drifts.append({
            "kind": "content_without_audit",
            "detail": "content .md exists but audit/status cache missing",
        })

    return {
        "track": track,
        "slug": slug,
        "in_sync": not drifts,
        "drift": drifts,
        "snapshot": {
            "state_phases": {
                name: data.get("status") for name, data in state_phases.items()
                if isinstance(data, dict)
            },
            "audit_status": audit.get("status"),
            "final_review_verdict": (
                final_review.get("verdict") if isinstance(final_review, dict) else None
            ),
            "content_on_disk": bool(content_path and content_path.is_file()),
            "mdx_on_disk": mdx.is_file(),
        },
    }


@router.get("/{track}/{slug}/drift")
async def drift_check(track: str, slug: str):
    """Cross-check module state across state.json, audit, review, disk."""
    result = await asyncio.to_thread(_state_drift_check, track, slug)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result
