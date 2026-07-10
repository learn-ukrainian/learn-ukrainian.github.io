"""Research detail and legacy compatibility functions for state API endpoints.

Contains research detail computation, module detail deep-dive,
pipeline version phase resolution, and legacy research/content checks.
"""

import contextlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.thresholds import REVIEW_PASS_FLOOR
from research_quality import (
    DIMENSION_SHORT_LABELS,
    assess_research_compat,
    find_research_path,
    get_dimensions,
    get_rubric,
)

from scripts.audit.llm_qg_store import (
    current_payload_for_module,
    llm_qg_file_is_current_for_module,
)

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from .config import CURRICULUM_ROOT
from .state_helpers import (
    PLANS_ROOT,
    V5_PHASE_ORDER,
    detect_pipeline_version,
    find_content_file,
    get_audit_status,
    get_broker_messages_for_slug,
    get_final_review_info,
    get_plan_slugs,
    get_research_score,
    get_word_target_from_plan,
    has_research_file,
    # BACKWARD-COMPAT: v3/v2 parsers needed for modules not yet rebuilt on v6
    parse_v3_phase_status,
    parse_v5_phase_status,
    plan_has_revision_log,
    read_v2_state,
    read_v3_state,
)


def severity_key(m: dict) -> int:
    """Sort key for weak-points severity ranking."""
    score = 0
    for issue in m["issues"]:
        if "audit_fail" in issue:
            score += 100
        elif "research_score" in issue:
            score += 50
        elif "low_words" in issue:
            score += 10
    return -score



def compute_research_detail(track_id: str, level_cfg: dict, min_score: int) -> dict:
    """Compute per-module research quality for a track."""
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    plan_slugs = get_plan_slugs(track_id)
    rubric_name = get_rubric(track_id)
    dimensions = get_dimensions(rubric_name) if rubric_name else []

    modules = []
    upgrade_queue = []
    quality_counts = {"exemplary": 0, "solid": 0, "adequate": 0, "thin": 0, "stub": 0, "missing": 0}
    scores = []

    for num, slug in plan_slugs:
        mod_entry, quality, score = _assess_module_research(
            track_dir, track_id, num, slug,
            rp_finder=find_research_path, assessor=assess_research_compat,
        )
        modules.append(mod_entry)

        if not mod_entry["exists"]:
            quality_counts["missing"] += 1
            upgrade_queue.append({"num": num, "slug": slug, "score": None, "gaps": ["missing"]})
            continue

        if quality and quality in quality_counts:
            quality_counts[quality] += 1
        if score is not None:
            scores.append(score)
            if score < min_score:
                gaps = mod_entry.get("gaps") or []
                upgrade_queue.append({
                    "num": num, "slug": slug, "score": score,
                    "gaps": [g.split(":")[0] for g in gaps],
                })

    upgrade_queue.sort(key=lambda x: (x["score"] if x["score"] is not None else -1))
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    return {
        "track": track_id, "rubric": rubric_name,
        "dimensions": dimensions,
        "dimension_labels": {d: DIMENSION_SHORT_LABELS.get(d, d[:3]) for d in dimensions} if dimensions else {},
        "total": len(plan_slugs), "researched": len(scores), "avg_score": avg_score,
        "quality_distribution": quality_counts,
        "upgrade_queue": upgrade_queue, "upgrade_count": len(upgrade_queue),
        "min_score_threshold": min_score, "modules": modules,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _assess_module_research(track_dir, track_id, num, slug, *, rp_finder, assessor):
    """Assess research quality for a single module. Returns (entry, quality, score)."""
    rp = rp_finder(track_dir, slug)
    empty = {
        "num": num, "slug": slug, "exists": False,
        "score": None, "quality": None, "dimensions": None, "gaps": None,
    }
    if not rp:
        return empty, None, None

    content_path = find_content_file(track_dir, slug)
    info = assessor(rp, track_id, content_path)
    if not info or not info.get("exists"):
        return empty, None, None

    dims = info.get("dimensions") or {}
    mod_entry = {
        "num": num, "slug": slug, "exists": True,
        "words": info.get("words", 0),
        "score": info.get("score"), "quality": info.get("quality"),
        "dimensions": {
            k: {"score": v["score"], "max": v["max"], "detail": v["detail"]}
            for k, v in dims.items()
        } if dims else None,
        "gaps": info.get("gaps") or [],
        "content_alignment": info.get("content_alignment"),
    }
    return mod_entry, info.get("quality"), info.get("score")


def _get_friction_data(orch_dir: Path) -> dict:
    """Read friction.yaml and return summary. Returns empty dict if no file."""
    friction_path = orch_dir / "friction.yaml"
    if not friction_path.exists():
        return {"active": 0, "resolved": 0, "items": []}
    try:
        data = yaml.safe_load(friction_path.read_text("utf-8"))
        frictions = data.get("frictions", []) if data else []
        active = [f for f in frictions if f.get("status") == "active"]
        resolved = [f for f in frictions if f.get("status") == "resolved"]
        return {
            "active": len(active),
            "resolved": len(resolved),
            "items": [{"id": f.get("id", ""), "type": f.get("type", ""),
                       "description": f.get("description", "").strip()[:200]}
                      for f in active],
        }
    except Exception:
        return {"active": 0, "resolved": 0, "items": []}


def _get_review_score(track_dir: Path, slug: str) -> dict:
    """Parse review file for numeric score and verdict."""
    review_path = track_dir / "review" / f"{slug}-review.md"
    if not review_path.exists():
        return {"exists": False, "score": None, "verdict": None}
    text = review_path.read_text("utf-8")
    score = None
    # Prefer post-fix score estimate (reflects actual quality after fixes)
    m_post = re.search(r"Estimated Post-Fix Score[:\s*]*(\d+(?:\.\d+)?)/10", text)
    if m_post:
        with contextlib.suppress(ValueError):
            score = float(m_post.group(1))
    if score is None:
        m = re.search(r"Overall Score[:\s*]*(\d+(?:\.\d+)?)/10", text)
        if m:
            with contextlib.suppress(ValueError):
                score = float(m.group(1))
    verdict = None
    # Last Status: PASS/FAIL in the file
    for vm in re.finditer(r"\*\*Status:\*\*\s*(PASS|FAIL)", text):
        verdict = vm.group(1)
    return {"exists": True, "score": score, "verdict": verdict}


def _compute_shippable(audit_status: str, review_score: float | None) -> bool:
    """Module is shippable if audit PASS + review >= REVIEW_PASS_FLOOR."""
    if audit_status != "pass":
        return False
    return not (review_score is None or review_score < REVIEW_PASS_FLOOR)


def _get_stress_issues(orch_dir: Path) -> dict:
    """Read stress verification results from screen-result.json."""
    screen_path = orch_dir / "screen-result.json"
    if not screen_path.exists():
        return {"mismatches": 0, "unknown": 0, "details": []}
    try:
        data = json.loads(screen_path.read_text("utf-8"))
        issues = data.get("deterministic_issues", [])
        stress = [i for i in issues if i.get("type", "").startswith("STRESS_")]
        mismatches = [i for i in stress if i["type"] == "STRESS_MISMATCH"]
        unknown = [i for i in stress if i["type"] == "STRESS_UNKNOWN"]
        return {
            "mismatches": len(mismatches),
            "unknown": len(unknown),
            "details": [i.get("text", "")[:120] for i in mismatches[:5]],
        }
    except Exception:
        return {"mismatches": 0, "unknown": 0, "details": []}


def _get_quick_verify(orch_dir: Path) -> dict:
    """Read V6 quick-verify.json results."""
    qv_path = orch_dir / "quick-verify.json"
    if not qv_path.exists():
        return {}
    try:
        return json.loads(qv_path.read_text("utf-8"))
    except Exception:
        return {}


def _read_json_file(path: Path) -> dict | None:
    """Read a JSON object, returning None for absent or unusable artifacts."""
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def read_llm_qg(track_dir: Path, slug: str) -> dict | None:
    """Read a module's LLM quality-gate artifact if present."""
    try:
        module_dir = safe_join(track_dir, slug)
        current = current_payload_for_module(track_dir.name, slug, module_dir)
        if current is not None:
            return current
        path = safe_join(module_dir, "llm_qg.json")
    except ValueError:
        return None
    if not llm_qg_file_is_current_for_module(module_dir, path):
        return None
    return _read_json_file(path)


def read_wiki_gate(track_dir: Path, slug: str) -> dict | None:
    """Read a module's wiki completeness gate artifact if present."""
    try:
        path = safe_join(track_dir, slug, "wiki_completeness_gate.json")
    except ValueError:
        return None
    return _read_json_file(path)


def read_module_status(track_dir: Path, slug: str) -> dict | None:
    """Read a generated module status cache opportunistically if present."""
    try:
        path = safe_join(track_dir, "status", f"{slug}.json")
    except ValueError:
        return None
    return _read_json_file(path)


def _project_llm_qg_dimensions(dimensions: object, *, verbose: bool) -> dict | None:
    if not isinstance(dimensions, dict):
        return None

    projected = {}
    for name, value in dimensions.items():
        if verbose:
            projected[name] = value
            continue
        if isinstance(value, dict):
            projected[name] = value.get("score")
        else:
            projected[name] = value
    return projected


def summarize_llm_qg(llm_qg: dict | None) -> dict | None:
    """Return the compact per-module LLM-QG summary used by API projections."""
    if not isinstance(llm_qg, dict):
        return None

    aggregate = llm_qg.get("aggregate") if isinstance(llm_qg.get("aggregate"), dict) else {}
    return {
        "verdict": aggregate.get("verdict"),
        "min_score": aggregate.get("min_score"),
        "min_dim": aggregate.get("min_dim"),
        "dimensions": _project_llm_qg_dimensions(llm_qg.get("dimensions"), verbose=False),
    }


def compute_llm_qg_track(track_id: str, level_cfg: dict, *, verbose: bool = False) -> dict:
    """Compute per-module LLM quality-gate status from artifacts already on disk."""
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    plan_slugs = get_plan_slugs(track_id)
    modules = []
    min_scores = []
    scored = 0
    passing = 0
    failing = 0

    for num, slug in plan_slugs:
        llm_qg = read_llm_qg(track_dir, slug)
        wiki_gate = read_wiki_gate(track_dir, slug)
        status = read_module_status(track_dir, slug)
        has_llm_qg = llm_qg is not None

        aggregate = (
            llm_qg.get("aggregate")
            if has_llm_qg and isinstance(llm_qg.get("aggregate"), dict)
            else None
        )
        dimensions = _project_llm_qg_dimensions(
            llm_qg.get("dimensions") if has_llm_qg else None,
            verbose=verbose,
        )
        verdict = aggregate.get("verdict") if isinstance(aggregate, dict) else None

        if has_llm_qg:
            scored += 1
            if verdict == "PASS":
                passing += 1
            else:
                failing += 1
            min_score = aggregate.get("min_score") if isinstance(aggregate, dict) else None
            if isinstance(min_score, (int, float)) and not isinstance(min_score, bool):
                min_scores.append(float(min_score))

        modules.append({
            "num": num,
            "slug": slug,
            "has_llm_qg": has_llm_qg,
            "verdict": verdict,
            "aggregate": aggregate,
            "dimensions": dimensions if has_llm_qg else None,
            "wiki_gate": (
                {"verdict": wiki_gate.get("verdict")}
                if isinstance(wiki_gate, dict) and "verdict" in wiki_gate
                else None
            ),
            "status": status,
        })

    return {
        "track": track_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "total": len(plan_slugs),
            "scored": scored,
            "passing": passing,
            "failing": failing,
            "unscored": len(plan_slugs) - scored,
            "min_dim_score": min(min_scores) if min_scores else None,
        },
        "modules": modules,
    }


def compute_module_detail(track_id: str, num: int, level_cfg: dict) -> dict:
    """Compute single module deep-dive data."""
    plan_slugs = get_plan_slugs(track_id)
    match = next(((n, s) for n, s in plan_slugs if n == num), None)
    if not match:
        return {"error": f"Module #{num} not found in track '{track_id}'"}
    _, slug = match
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    orch_dir = safe_join(track_dir / "orchestration", slug)

    version = detect_pipeline_version(orch_dir)
    # Read state once — reuse for phases + consultations (avoids duplicate I/O)
    state_data = read_v2_state(orch_dir) if version in ("v5", "v6") else {}
    phases = get_phases_for_version(orch_dir, version, state_data=state_data)

    audit = get_audit_status(track_dir, slug)
    word_target = audit.get("word_target", 0)
    if word_target == 0:
        word_target = get_word_target_from_plan(track_id, slug)

    plan_file = PLANS_ROOT / track_id / f"{slug}.yaml"

    return {
        "track": track_id, "num": num, "slug": slug,
        "pipeline_version": version, "needs_rebuild": version != "v6",
        "phases": phases,
        "audit": {
            "status": audit["status"], "word_count": audit.get("word_count", 0),
            "word_target": word_target, "blocking_issues": audit.get("blocking_issues", []),
        },
        "research": {
            "exists": has_research_file(track_dir, slug),
            "score": get_research_score(track_dir, slug, track_id),
        },
        "review": _get_review_score(track_dir, slug),
        "friction": _get_friction_data(orch_dir),
        "shippable": _compute_shippable(
            audit["status"], _get_review_score(track_dir, slug)["score"]),
        "stress": _get_stress_issues(orch_dir),
        "prompt_review": (track_dir / "audit" / f"{slug}-prompt-review.md").exists(),
        "content_review": (track_dir / "audit" / f"{slug}-content-review.md").exists(),
        "final_review": get_final_review_info(track_dir, slug),
        "enriched": plan_has_revision_log(plan_file),
        "quick_verify": _get_quick_verify(orch_dir),
        "consultations": state_data.get("consultations", []),
        "comms": get_broker_messages_for_slug(slug, limit=15),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def get_phases_for_version(orch_dir, version, *, state_data: dict | None = None):
    """Get phase status dict appropriate for the pipeline version."""
    if version == "v6":
        from .state_build import V6_PHASE_ORDER  # noqa: PLC0415 — breaks state-build import cycle
        v6 = state_data if state_data is not None else read_v2_state(orch_dir)
        phases = v6.get("phases", {})
        return {
            name: {"status": phases.get(name, {}).get("status", "pending"),
                   "ts": phases.get(name, {}).get("ts")}
            for name in V6_PHASE_ORDER
        }
    elif version == "v5":
        v5 = state_data if state_data is not None else read_v2_state(orch_dir)
        return {name: parse_v5_phase_status(v5, name) for name in V5_PHASE_ORDER}
    else:
        v3 = read_v3_state(orch_dir)
        return {pid: parse_v3_phase_status(v3, f"v3-{pid}") for pid in ["A", "B", "C", "audit", "D", "E", "F"]}
