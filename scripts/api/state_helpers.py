"""Helper functions for the state API router.

Pipeline state detection, audit status parsing, research scoring, review analysis,
and sync computation functions used by state endpoints.

Pipeline version note (#1186, 2026-04-11):
    This module used to import PHASES/PHASE_LABELS from the retired
    ``pipeline_v5`` module. The current pipeline is v6 at
    ``scripts/build/v6_build.py``, which now exports the canonical
    phase list as public symbols. V5 constants are kept for backwards
    compatibility when reading old state files (``V5_PHASE_ORDER`` /
    ``parse_v5_phase_status``) but new code should use
    ``V6_PHASE_ORDER``.
"""

import contextlib
import json
import re
import sqlite3
import sys
from pathlib import Path

import yaml

from .config import CURRICULUM_ROOT, MESSAGE_DB

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.state import is_complete as _phase_complete
from pipeline.state import load_state as _load_pipeline_state
from research_quality import assess_research_compat, find_research_path

# Canonical phase list for the CURRENT pipeline (v6). Imported from
# the build module so the API and the pipeline can never drift out of
# sync. If the import fails (e.g. tests running without the build
# module on PYTHONPATH), we fall back to a frozen snapshot rather
# than an empty list — an empty phase list silently breaks coverage
# endpoints.
try:
    from build.v6_build import PHASE_LABELS as _V6_PHASE_LABELS
    from build.v6_build import PHASES as _V6_PHASES
except ImportError:
    _V6_PHASES = [
        "check", "research", "skeleton", "pre-verify", "write",
        "exercises", "activities", "repair", "verify-exercises",
        "annotate", "vocab", "enrich", "verify", "review", "stress",
        "publish", "audit",
    ]
    _V6_PHASE_LABELS: dict[str, str] = {}

# Legacy v5 phase list — frozen snapshot. DO NOT use for new work;
# only for reading state files from builds completed before v6
# landed. We keep the list inline instead of importing from
# ``pipeline_v5`` so this module has one less dependency on the
# retired pipeline module.
_V5_PHASES = ["research", "discover", "content", "validate", "activities", "review", "mdx"]
_V5_PHASE_LABELS: dict[str, str] = {}

# Back-compat aliases for callers that still read these names. New
# code should prefer ``_V6_PHASES`` / ``_V6_PHASE_LABELS`` (or the
# public ``V6_PHASE_ORDER`` below).
_PIPELINE_PHASES = _V6_PHASES
_PIPELINE_PHASE_LABELS = _V6_PHASE_LABELS


# ==================== CONSTANTS ====================

CURRICULUM_YAML = CURRICULUM_ROOT / "curriculum.yaml"
PLANS_ROOT = CURRICULUM_ROOT / "plans"

# Track → profile mapping. ``b2-pro`` / ``c1-pro`` were deleted
# 2026-04-10 (STEM will eventually replace the pro tracks; that work
# is not in this issue). The entries are intentionally absent — do
# not re-add them without a curriculum decision.
PROFILE_MAP = {
    "a1": "core", "a2": "core", "b1": "core", "b2": "core",
    "c1": "core", "c2": "core",
    "hist": "seminar", "istorio": "seminar", "bio": "seminar",
    "lit": "seminar", "lit-essay": "seminar", "lit-hist-fic": "seminar",
    "lit-fantastika": "seminar", "lit-war": "seminar",
    "lit-humor": "seminar", "lit-youth": "seminar",
    "lit-doc": "seminar", "lit-drama": "seminar",
    "lit-crimea": "seminar",
    "oes": "seminar", "ruth": "seminar",
}

# Legacy phase orders kept for parsing historical state files only.
# Prefer ``V6_PHASE_ORDER`` for any new code.
V4_PHASE_ORDER = ["research", "discover", "content", "activities", "validate", "review", "mdx"]
V5_PHASE_ORDER = _V5_PHASES
V6_PHASE_ORDER = _V6_PHASES


# ==================== TTL CACHE ====================

_ttl_cache: dict[str, tuple[float, object]] = {}


import time


def cache_get(key: str, ttl: float) -> object | None:
    """Return cached value if still within TTL, else None."""
    entry = _ttl_cache.get(key)
    if entry and (time.time() - entry[0]) < ttl:
        return entry[1]
    return None


def cache_set(key: str, value: object) -> None:
    """Store a value in the TTL cache."""
    _ttl_cache[key] = (time.time(), value)


# ==================== CURRICULUM LOADING ====================

_curriculum_cache: dict | None = None
_curriculum_mtime: float = 0.0


def load_curriculum() -> dict:
    """Load curriculum.yaml, cached with mtime check for auto-refresh."""
    global _curriculum_cache, _curriculum_mtime
    if CURRICULUM_YAML.exists():
        current_mtime = CURRICULUM_YAML.stat().st_mtime
        if _curriculum_cache is None or current_mtime != _curriculum_mtime:
            _curriculum_cache = yaml.safe_load(CURRICULUM_YAML.read_text()) or {}
            _curriculum_mtime = current_mtime
    else:
        _curriculum_cache = {}
    return _curriculum_cache


def to_bare_slug(entry: str) -> str:
    """Strip numeric prefix if present (e.g. '01-the-cyrillic-code-i' -> 'the-cyrillic-code-i')."""
    if not entry:
        return entry
    entry = entry.split("#")[0].strip()
    match = re.match(r"^\d+-(.+)$", entry)
    return match.group(1) if match else entry


def get_plan_slugs(track_id: str) -> list[tuple[int, str]]:
    """Return [(num, slug)] for a track, sorted by position.

    Primary: curriculum.yaml ordering.
    Fallback: scan PLANS_ROOT / track_id / *.yaml, sorted alphabetically.
    """
    data = load_curriculum()
    modules = data.get("levels", {}).get(track_id, {}).get("modules", [])
    if modules:
        result = []
        for i, entry in enumerate(modules):
            slug = to_bare_slug(str(entry))
            if slug:
                result.append((i + 1, slug))
        return result

    plan_dir = PLANS_ROOT / track_id
    if plan_dir.is_dir():
        plan_files = sorted(plan_dir.glob("*.yaml"))
        return [(i + 1, f.stem) for i, f in enumerate(plan_files)]

    return []


# ==================== PIPELINE STATE ====================

class StateCtx:
    """Lightweight context for pipeline.state.load_state (needs .track, .slug, .orch_dir)."""
    __slots__ = ("orch_dir", "slug", "track")

    def __init__(self, track: str, slug: str, orch_dir: Path):
        self.track = track
        self.slug = slug
        self.orch_dir = orch_dir


def load_module_state(track: str, slug: str, orch_dir: Path) -> dict:
    """Load unified pipeline state for a module.

    Handles V6 state directly (mode='v6'), delegates V5/V4/V3 to pipeline.state.
    """
    # V6 state: read directly (pipeline.state only knows v5)
    state_file = orch_dir / "state.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
            if data.get("mode") == "v6":
                return data
        except Exception:
            pass

    ctx = StateCtx(track, slug, orch_dir)
    try:
        return _load_pipeline_state(ctx)
    except Exception:
        return {"track": track, "slug": slug, "mode": "v5", "phases": {}}


def detect_pipeline_version(orch_dir: Path) -> str:
    """Detect pipeline version for a module.

    Priority: state.json mode=v6/v5 > state-v4.json > state-v3.json > state.json['mode'] > 'unbuilt'.
    """
    state_file = orch_dir / "state.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
            if data.get("mode") == "v6":
                return "v6"
            if data.get("mode") == "v5":
                return "v5"
        except Exception:
            pass
    if (orch_dir / "state-v4.json").exists():
        return "v4"
    if (orch_dir / "state-v3.json").exists():
        return "v3"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
            if data.get("mode") == "v4":
                return "v4"
            if data:
                return "v3"
        except Exception:
            pass
    return "unbuilt"


# ==================== BACKWARD-COMPAT STATE READERS ====================

def read_v4_state(orch_dir: Path) -> dict:
    """Read state-v4.json, return {} if missing or invalid."""
    state_file = orch_dir / "state-v4.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text()) or {}
    except Exception:
        return {}


def read_v3_state(orch_dir: Path) -> dict:
    """Read state-v3.json, return {} if missing or invalid."""
    state_file = orch_dir / "state-v3.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text()) or {}
    except Exception:
        return {}


def read_v2_state(orch_dir: Path) -> dict:
    """Read state.json (v2 pipeline), return {} if missing or invalid."""
    state_file = orch_dir / "state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text()) or {}
    except Exception:
        return {}


# ==================== PHASE STATUS PARSING ====================

def parse_v4_phase_status(v4_state: dict, phase_name: str) -> dict:
    """Extract status info for a v4 phase (e.g. 'research', 'content')."""
    phase = v4_state.get("phases", {}).get(f"v4-{phase_name}", {})
    if not phase:
        return {"status": "pending"}
    return {"status": phase.get("status", "pending"), "ts": phase.get("ts")}


def parse_v5_phase_status(v5_state: dict, phase_name: str) -> dict:
    """Extract status info for a v5 phase. V5 uses plain keys (no prefix)."""
    phase = v5_state.get("phases", {}).get(phase_name, {})
    if not phase:
        return {"status": "pending"}
    result = {"status": phase.get("status", "pending"), "ts": phase.get("ts")}
    # Executor provenance (new structured format)
    if phase.get("executor"):
        result["executor"] = phase["executor"]
    # Backward compat: migrate legacy ad-hoc agent/model to executor
    elif phase.get("agent") or phase.get("model"):
        result["executor"] = {
            "type": "llm",
            "agent": phase.get("agent", "unknown"),
            "model": phase.get("model", "unknown"),
        }
    return result


def parse_v3_phase_status(v3_state: dict, phase_key: str) -> dict:
    """Extract status info for a v3 phase key (e.g. 'v3-A')."""
    phase = v3_state.get("phases", {}).get(phase_key, {})
    if not phase:
        return {"status": "pending"}
    return {
        "status": phase.get("status", "pending"),
        "mode": phase.get("mode"),
        "ts": phase.get("ts"),
        "attempts": phase.get("attempts"),
    }


def parse_phase_status_from_state(state: dict, phase_name: str) -> dict:
    """Extract status info for a phase from unified v5 state."""
    phase = state.get("phases", {}).get(phase_name, {})
    if not phase:
        return {"status": "pending"}
    result = {"status": phase.get("status", "pending")}
    if phase.get("ts"):
        result["ts"] = phase["ts"]
    if phase.get("mode"):
        result["mode"] = phase["mode"]
    if phase.get("attempts"):
        result["attempts"] = phase["attempts"]
    return result


# ==================== RESEARCH & CONTENT HELPERS ====================

def has_research_file(track_dir: Path, slug: str) -> bool:
    """Return True if a research file exists for this module (V5 or V6 format)."""
    research_dir = track_dir / "research"
    return (
        (research_dir / f"{slug}-research.md").exists()
        or (research_dir / f"{slug}-knowledge-packet.md").exists()
    )


def is_research_done(state: dict, track_dir: Path | None = None, slug: str | None = None) -> bool:
    """Research done if pipeline state has research phase complete, or research file exists."""
    if _phase_complete(state, "research"):
        return True
    return bool(track_dir is not None and slug is not None and has_research_file(track_dir, slug))


def is_content_done(state: dict) -> bool:
    """Content done if pipeline state has content phase complete.

    V6 uses 'write' phase instead of 'content', both with status='complete'.
    """
    if _phase_complete(state, "content"):
        return True
    return _phase_complete(state, "write")


def find_content_file(track_dir: Path, slug: str) -> Path | None:
    """Find the module content .md file."""
    for pattern in [f"{slug}.md", f"*-{slug}.md"]:
        matches = list(track_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


# ==================== AUDIT STATUS ====================

def get_audit_status(track_dir: Path, slug: str) -> dict:
    """Read status/{slug}.json. Returns {status, word_count, word_target, blocking_issues}.

    Staleness guard: if the content file is newer than the status cache,
    the audit result is stale.
    """
    status_file = track_dir / "status" / f"{slug}.json"
    if not status_file.exists():
        return {"status": "not_run", "word_count": 0, "word_target": 0, "blocking_issues": []}
    try:
        content_file = find_content_file(track_dir, slug)
        if content_file and content_file.exists():
            content_mtime = content_file.stat().st_mtime
            status_mtime = status_file.stat().st_mtime
            if content_mtime > status_mtime:
                word_count = len(content_file.read_text().split())
                return {
                    "status": "stale",
                    "word_count": word_count,
                    "word_target": 0,
                    "blocking_issues": [],
                    "stale_reason": "content rebuilt after last audit",
                }

        data = json.loads(status_file.read_text())
        overall_status = data.get("overall", {}).get("status", "unknown")

        word_count = 0
        word_target = 0
        lesson_msg = data.get("gates", {}).get("lesson", {}).get("message", "")
        if "/" in str(lesson_msg):
            parts = str(lesson_msg).split("/")
            try:
                word_count = int(parts[0].strip().split()[-1])
            except (ValueError, IndexError):
                for md_candidate in track_dir.glob(f"*{slug}*.md"):
                    if md_candidate.is_file():
                        word_count = len(md_candidate.read_text().split())
                        break
            with contextlib.suppress(ValueError, IndexError):
                word_target = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0

        blocking_issues = []
        for gate_name, gate_info in data.get("gates", {}).items():
            if isinstance(gate_info, dict) and gate_info.get("status") == "fail":
                blocking_issues.append({
                    "gate": gate_name,
                    "message": gate_info.get("message", ""),
                })
        return {
            "status": overall_status,
            "word_count": word_count,
            "word_target": word_target,
            "blocking_issues": blocking_issues,
        }
    except Exception:
        return {"status": "error", "word_count": 0, "word_target": 0, "blocking_issues": []}


# ==================== RESEARCH SCORING ====================

def get_research_score(track_dir: Path, slug: str, track_id: str) -> int | None:
    """Get research quality score for a module (0-10 or None)."""
    rp = find_research_path(track_dir, slug)
    if not rp:
        return None
    result = assess_research_compat(rp, track_id, None)
    if result and result.get("score") is not None:
        return result["score"]
    return None


def get_word_target_from_plan(track_id: str, slug: str) -> int:
    """Try to read word_target from the individual plan YAML file."""
    plan_file = PLANS_ROOT / track_id / f"{slug}.yaml"
    if not plan_file.exists():
        return 0
    try:
        data = yaml.safe_load(plan_file.read_text()) or {}
        return data.get("word_target", 0)
    except Exception:
        return 0


# ==================== REVIEW HELPERS ====================

def extract_content_hash(review_path: Path) -> str | None:
    """Extract content hash from review file header (#618).

    Reviews written by write_review_with_hash() start with:
        <!-- content-hash: abc123def456 -->
    """
    try:
        with open(review_path, encoding="utf-8") as f:
            first_line = f.readline()
        m = re.match(r"<!-- content-hash: ([a-f0-9]+) -->", first_line)
        return m.group(1) if m else None
    except Exception:
        return None


def is_review_stale(review_path: Path, content_path: Path | None) -> bool:
    """Check if a review file is stale relative to its content (#618)."""
    if not review_path.exists():
        return False
    if not content_path or not content_path.exists():
        return False

    import hashlib
    review_hash = extract_content_hash(review_path)
    if review_hash:
        try:
            current_hash = hashlib.md5(content_path.read_bytes(), usedforsecurity=False).hexdigest()[:12]
        except OSError:
            return False
        return review_hash != current_hash

    try:
        content_mtime = content_path.stat().st_mtime
        review_mtime = review_path.stat().st_mtime
    except OSError:
        return False
    return content_mtime > 0 and review_mtime < content_mtime


def get_broker_messages_for_slug(slug: str, limit: int = 20) -> list[dict]:
    """Query broker DB for messages related to a module slug."""
    if not MESSAGE_DB.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{MESSAGE_DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, task_id, from_llm, to_llm, message_type, "
            "substr(content, 1, 200) as preview, timestamp "
            "FROM messages WHERE task_id LIKE ? "
            "ORDER BY id DESC LIMIT ?",
            (f"%{slug}%", limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_final_review_info(track_dir: Path, slug: str) -> dict | None:
    """Parse final review file for verdict and issue count."""
    review_file = track_dir / "review" / f"{slug}-final-review.md"
    if not review_file.exists():
        return None
    try:
        text = review_file.read_text()
        verdict = None
        verdict_match = re.search(r"===VERDICT===\s*(\w+)\s*===END_VERDICT===", text)
        if verdict_match:
            verdict = verdict_match.group(1).strip()

        issue_count = len(re.findall(r"\*\*ISSUE\s+\d+", text, re.IGNORECASE))

        issues = []
        for m in re.finditer(
            r"\*\*ISSUE\s+(\d+)\s*[—–-]\s*([^*]+)\*\*",
            text, re.IGNORECASE,
        ):
            issues.append({
                "num": int(m.group(1)),
                "summary": m.group(2).strip()[:120],
            })

        return {
            "verdict": verdict,
            "issue_count": issue_count,
            "issues": issues,
            "file": str(review_file.relative_to(CURRICULUM_ROOT)),
        }
    except Exception:
        return None

