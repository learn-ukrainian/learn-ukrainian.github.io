"""Build status and track health computations for the state API.

Handles build progress tracking, ETA calculation, and track health
aggregation. All functions are sync and designed for asyncio.to_thread().
"""

import json
from datetime import UTC, datetime

from .config import CURRICULUM_ROOT, LEVELS
from .state_compute import _compute_shippable, _get_review_score
from .state_helpers import (
    PLANS_ROOT,
    V5_PHASE_ORDER,
    detect_pipeline_version,
    get_audit_status,
    get_final_review_info,
    get_plan_slugs,
    read_v2_state,
    read_v3_state,
)

try:
    from scripts.build.v6_build import PHASES as V6_PHASE_ORDER
except ImportError:
    V6_PHASE_ORDER = [
        "check", "research", "skeleton", "pre-verify", "write",
        "exercises", "activities", "repair", "verify-exercises",
        "annotate", "vocab", "enrich", "verify", "review", "stress",
        "publish", "audit",
    ]


def compute_build_status_track(track_id: str, level_cfg: dict) -> dict:
    """Compute build progress for a single track."""
    plan_slugs = get_plan_slugs(track_id)
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    total = len(plan_slugs)

    building_now = []
    done = queued = failed = 0
    recent_completions = []

    for num, slug in plan_slugs:
        orch_dir = track_dir / "orchestration" / slug
        version = detect_pipeline_version(orch_dir)
        furthest, running_phase, latest_ts, audit_status = scan_module_phases(orch_dir, version)

        if audit_status == "complete":
            done += 1
            audit_result = get_audit_status(track_dir, slug)
            recent_completions.append({
                "num": num, "slug": slug, "phase": furthest or "audit",
                "audit": audit_result.get("status", "unknown"),
                "words": f"{audit_result.get('word_count', 0)}/{audit_result.get('word_target', 0)}",
                "ts": latest_ts,
            })
        elif running_phase:
            building_now.append({"num": num, "slug": slug, "phase": running_phase, "prev": furthest})
        elif audit_status == "failed":
            failed += 1
        elif furthest:
            building_now.append({"num": num, "slug": slug, "phase": f"queued-after-{furthest}", "prev": furthest})
        else:
            queued += 1

    recent_completions.sort(key=lambda x: x.get("ts") or "", reverse=True)

    return {
        "track": track_id, "total": total, "done": done,
        "building": len(building_now), "queued": queued, "failed": failed,
        "progress": f"{done}/{total} ({round(done/total*100) if total else 0}%)",
        "currently_building": building_now[:5],
        "recent_completions": recent_completions[:5],
        "generated_at": datetime.now(UTC).isoformat(),
    }

def scan_module_phases(orch_dir, version):
    """Scan pipeline phases for a module. Returns (furthest, running, latest_ts, audit_status)."""
    furthest = running_phase = latest_ts = audit_status = None

    if version == "v6":
        phases = read_v2_state(orch_dir).get("phases", {})
        phase_names = V6_PHASE_ORDER
        audit_key = "audit"
    elif version == "v5":
        phases = read_v2_state(orch_dir).get("phases", {})
        phase_names = V5_PHASE_ORDER
        audit_key = "validate"
    elif version == "v3":
        # BACKWARD-COMPAT: v3 modules still use old phase naming
        phases = read_v3_state(orch_dir).get("phases", {})
        phase_names = ["v3-A", "v3-B", "v3-C", "v3-audit", "v3-D", "v3-E", "v3-F"]
        audit_key = "v3-audit"
    else:
        phases = {}
        phase_names = []
        audit_key = ""

    for pid in phase_names:
        p = phases.get(pid, {})
        status = p.get("status")
        display = pid
        if pid.startswith("v3-"):
            display = pid.replace("v3-", "")
        if status == "complete":
            furthest = display
            if p.get("ts"):
                latest_ts = p["ts"]
        elif status == "running":
            running_phase = display
        elif status == "failed":
            running_phase = display + "(FAIL)"

    audit_status = phases.get(audit_key, {}).get("status") if audit_key else None
    return furthest, running_phase, latest_ts, audit_status


def compute_build_status_all() -> dict:
    """Compute build progress across all tracks."""
    tracks = {}
    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(track_id)
        if not plan_slugs:
            continue
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        total = len(plan_slugs)
        done = building = failed = 0

        for _num, slug in plan_slugs:
            orch_dir = track_dir / "orchestration" / slug
            version = detect_pipeline_version(orch_dir)
            _furthest, running_phase, _latest_ts, audit_status = scan_module_phases(orch_dir, version)
            if audit_status == "complete":
                done += 1
            elif audit_status == "failed":
                failed += 1
            elif running_phase:
                building += 1

        tracks[track_id] = {
            "total": total, "done": done, "building": building, "failed": failed,
            "progress": f"{done}/{total} ({round(done/total*100) if total else 0}%)",
        }

    return {"generated_at": datetime.now(UTC).isoformat(), "tracks": tracks}


def compute_track_health(track_id: str, level_cfg: dict) -> dict:
    """Compute track health summary."""
    plan_slugs = get_plan_slugs(track_id)
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    plan_dir = PLANS_ROOT / track_id
    total = len(plan_slugs)

    built = audit_pass = audit_fail = enriched = final_reviewed = final_approved = shippable = 0
    word_ratios = []
    attention = []
    completion_times = []

    for num, slug in plan_slugs:
        b, ct = _check_build_phase(track_dir / "orchestration" / slug)
        built += b
        if ct:
            completion_times.append(ct)

        audit = get_audit_status(track_dir, slug)
        ap, af, att = _check_audit_health(audit, num, slug)
        audit_pass += ap
        audit_fail += af
        if att:
            attention.append(att)

        wc, wt = audit.get("word_count", 0), audit.get("word_target", 0)
        if wt > 0 and wc > 0:
            word_ratios.append(wc / wt)

        # Shippable = audit PASS + review >= 8.0 (#971)
        review_data = _get_review_score(track_dir, slug)
        if _compute_shippable(audit["status"], review_data["score"]):
            shippable += 1

        if (plan_dir / f"{slug}.yaml.bak").exists():
            enriched += 1

        fr_r, fr_a, fr_att = _check_final_review_health(track_dir, num, slug)
        final_reviewed += fr_r
        final_approved += fr_a
        if fr_att:
            attention.append(fr_att)

    remaining = total - built
    eta_minutes = compute_eta(completion_times, remaining)
    avg_word_ratio = round(sum(word_ratios) / len(word_ratios), 2) if word_ratios else None
    attention.sort(key=lambda x: 0 if "fail" in x["reason"] else 1)

    return {
        "track": track_id, "total": total,
        "build": {"done": built, "pct": round(built / total * 100) if total else 0},
        "audit": {"passing": audit_pass, "failing": audit_fail, "pct": round(audit_pass / total * 100) if total else 0},
        "shippable": {"count": shippable, "pct": round(shippable / total * 100) if total else 0},
        "enrichment": {"done": enriched, "pct": round(enriched / total * 100) if total else 0},
        "final_review": {
            "reviewed": final_reviewed, "approved": final_approved,
            "approval_rate": f"{round(final_approved / final_reviewed * 100)}%" if final_reviewed else "N/A",
        },
        "words": {"avg_ratio": f"{avg_word_ratio}x" if avg_word_ratio else "N/A"},
        "eta": {
            "remaining": remaining, "minutes": eta_minutes,
            "display": f"~{eta_minutes}min ({eta_minutes//60}h{eta_minutes%60:02d}m)" if eta_minutes else "N/A",
        },
        "attention": attention[:10],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _check_build_phase(orch_dir):
    """Check if content phase is complete. Returns (built_count, timestamp_or_none)."""
    version = detect_pipeline_version(orch_dir)
    if version == "v6":
        phases = read_v2_state(orch_dir).get("phases", {})
        content_phase = phases.get("write", {})
    elif version == "v5":
        phases = read_v2_state(orch_dir).get("phases", {})
        content_phase = phases.get("content", {})
    elif version == "v3":
        # BACKWARD-COMPAT: v3 content phase was "v3-B"
        phases = read_v3_state(orch_dir).get("phases", {})
        content_phase = phases.get("v3-B", {})
    else:
        content_phase = {}
    if content_phase.get("status") == "complete":
        return 1, content_phase.get("ts")
    return 0, None


def _check_audit_health(audit, num, slug):
    """Check audit status for health. Returns (pass_count, fail_count, attention_or_none)."""
    if audit["status"] == "pass":
        return 1, 0, None
    if audit["status"] == "fail":
        detail = (audit.get("blocking_issues", [{}])[0].get("gate", "")
                  if audit.get("blocking_issues") else "")
        return 0, 1, {"num": num, "slug": slug, "reason": "audit_fail", "detail": detail}
    return 0, 0, None


def _check_final_review_health(track_dir, num, slug):
    """Check final review for health. Returns (reviewed_count, approved_count, attention_or_none)."""
    fr = get_final_review_info(track_dir, slug)
    if not fr:
        return 0, 0, None
    if fr["verdict"] == "APPROVE":
        return 1, 1, None
    return 1, 0, {
        "num": num, "slug": slug,
        "reason": f"final_review_{fr['verdict']}",
        "detail": f"{fr['issue_count']} issues",
    }


def compute_eta(completion_times: list, remaining: int) -> int | None:
    """Compute ETA in minutes from completion timestamps."""
    if len(completion_times) < 3:
        return None
    sorted_ts = sorted(completion_times)
    recent = sorted_ts[-min(10, len(sorted_ts)):]
    if len(recent) < 2:
        return None
    try:
        first = datetime.fromisoformat(recent[0].replace("Z", "+00:00"))
        last = datetime.fromisoformat(recent[-1].replace("Z", "+00:00"))
        elapsed = (last - first).total_seconds()
        if elapsed > 0:
            rate_per_min = (len(recent) - 1) / (elapsed / 60)
            if rate_per_min > 0:
                return round(remaining / rate_per_min)
    except Exception:
        pass
    return None


def compute_enrichment_status(track: str | None) -> dict:
    """Compute enrichment status across tracks."""
    tracks = {}
    level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS
    for level_cfg in level_cfgs:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(track_id)
        if not plan_slugs:
            continue
        plan_dir = PLANS_ROOT / track_id
        enriched = sum(1 for _, slug in plan_slugs if (plan_dir / f"{slug}.yaml.bak").exists())
        not_enriched = [slug for _, slug in plan_slugs if not (plan_dir / f"{slug}.yaml.bak").exists()]
        total = len(plan_slugs)
        tracks[track_id] = {
            "total": total, "enriched": enriched, "pending": total - enriched,
            "pct": round(enriched / total * 100) if total else 0,
            "not_enriched": not_enriched[:10] if len(not_enriched) <= 10 else [*not_enriched[:5], f"...+{len(not_enriched) - 5}"],
        }
    return {"generated_at": datetime.now(UTC).isoformat(), "tracks": tracks}


def compute_build_stats(track: str) -> dict:
    """Parse V6 build-stats.jsonl for a track."""
    stats_path = CURRICULUM_ROOT / track / "build-stats.jsonl"
    if not stats_path.exists():
        return {"track": track, "entries": [], "summary": {}}

    entries = []
    for line in stats_path.read_text().splitlines():
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Compute summary
    total = len(entries)
    successes = sum(1 for e in entries if e.get("success"))
    slugs = set(e.get("slug", "") for e in entries)

    return {
        "track": track,
        "total_attempts": total,
        "successes": successes,
        "unique_modules": len(slugs),
        "success_rate": round(successes / total * 100, 1) if total else 0,
        "entries": entries[-50:],  # Last 50 entries
    }


def compute_build_stats_all() -> dict:
    """Aggregate V6 build stats across all tracks."""
    all_stats = {}
    total_attempts = 0
    total_successes = 0
    total_modules = 0

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        stats = compute_build_stats(track_id)
        if stats.get("total_attempts", 0) > 0:
            all_stats[track_id] = {
                "total_attempts": stats["total_attempts"],
                "successes": stats["successes"],
                "unique_modules": stats["unique_modules"],
                "success_rate": stats["success_rate"],
            }
            total_attempts += stats["total_attempts"]
            total_successes += stats["successes"]
            total_modules += stats["unique_modules"]

    return {
        "total_attempts": total_attempts,
        "total_successes": total_successes,
        "total_modules": total_modules,
        "overall_success_rate": round(total_successes / total_attempts * 100, 1) if total_attempts else 0,
        "tracks": all_stats,
        "generated_at": datetime.now(UTC).isoformat(),
    }
