import contextlib
import json
import logging
import subprocess
import uuid

import yaml
from fastapi import APIRouter, HTTPException

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/module/{level}/{slug}")
def get_module_state(level: str, slug: str):
    try:
        track_dir = safe_join(PROJECT_ROOT, "curriculum", "l2-uk-en", level)
        plan_path = safe_join(track_dir, "plans", f"{slug}.yaml")
        orchestration_dir = safe_join(track_dir, "orchestration", slug)
        content_path = safe_join(track_dir, f"{slug}.md")
        state_file = safe_join(orchestration_dir, "state.json")
        status_file = safe_join(track_dir, "status", f"{slug}.json")
    except ValueError:
        return {"error": "Invalid level/slug"}

    state_data = {}
    if state_file.exists():
        with contextlib.suppress(Exception):
            state_data = json.loads(state_file.read_text("utf-8"))

    status_data = {}
    if status_file.exists():
        with contextlib.suppress(Exception):
            status_data = json.loads(status_file.read_text("utf-8"))

    return {
        "level": level,
        "slug": slug,
        "phase_state": state_data.get("phases", {}),
        "audit_status": status_data.get("overall", {}).get("status", "unknown"),
        "key_paths": {
            "plan": str(plan_path.relative_to(PROJECT_ROOT)) if plan_path.exists() else None,
            "orchestration_dir": str(safe_join(track_dir, "orchestration", slug).relative_to(PROJECT_ROOT)),
            "content": str(content_path.relative_to(PROJECT_ROOT))
            if content_path.exists()
            else None,
        },
    }


@router.get("/orchestration/{level}/{slug}")
def get_orchestration(level: str, slug: str):
    try:
        track_dir = safe_join(PROJECT_ROOT, "curriculum", "l2-uk-en", level)
        orch_dir = safe_join(track_dir, "orchestration", slug)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid level/slug") from None
    if not orch_dir.exists():
        raise HTTPException(status_code=404, detail="Orchestration dir not found")

    prompts = [p.name for p in orch_dir.glob("*-prompt.md")]

    review_rounds = []
    for f in orch_dir.glob("review-structured-r*.yaml"):
        review_rounds.append(f.name)

    dispatch_dir = orch_dir / "dispatch"
    dispatch_logs = []
    if dispatch_dir.exists():
        dispatch_logs = [f.name for f in dispatch_dir.glob("*.json")]

    terminal = None
    for candidate in ("plan_revision_request.yaml", "budget_exhausted.yaml"):
        if (orch_dir / candidate).exists():
            terminal = candidate.removesuffix(".yaml")
            break

    return {
        "latest_prompts": sorted(prompts),
        "review_rounds": sorted(review_rounds),
        "dispatch_logs": sorted(dispatch_logs)[-5:],
        "terminal": terminal,
    }


@router.get("/prompt-summary/{level}/{slug}")
def get_prompt_summary(level: str, slug: str):
    try:
        track_dir = safe_join(PROJECT_ROOT, "curriculum", "l2-uk-en", level)
        orch_dir = safe_join(track_dir, "orchestration", slug)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid level/slug") from None
    if not orch_dir.exists():
        raise HTTPException(status_code=404, detail="Orchestration dir not found")

    manifests = {}
    for f in orch_dir.glob("*-prompt-manifest.yaml"):
        try:
            with open(f, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
                manifests[f.name] = {
                    "metrics": data.get("metrics", {}) if isinstance(data, dict) else {},
                    "audit": data.get("audit", {}) if isinstance(data, dict) else {},
                }
        except Exception:
            error_id = uuid.uuid4().hex
            logger.error(f"Failed to load manifest {f.name} [{error_id}]", exc_info=True)
            manifests[f.name] = {"error": "internal error", "error_id": error_id}

    return {"manifests": manifests}


@router.get("/runtime")
def get_runtime():
    proc = subprocess.run(["ps", "-x", "-o", "pid,state,command"], capture_output=True, text=True)
    processes = []
    repo_name = PROJECT_ROOT.name
    for line in proc.stdout.splitlines()[1:]:
        parts = line.strip().split(maxsplit=2)
        if len(parts) < 3:
            continue
        pid, state, cmd = parts

        is_relevant = False
        if (
            repo_name in cmd
            or (".venv/bin/python" in cmd and "scripts/" in cmd)
            or "@anthropic-ai/claude-code" in cmd
            or ("gemini" in cmd and "bridge" in cmd)
        ):
            is_relevant = True

        if is_relevant and "grep" not in cmd and "ps " not in cmd:
            processes.append({"pid": int(pid), "state": state, "command": cmd})

    return {"active_processes": processes}


@router.get("/worktree")
def get_worktree():
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True, text=True)

    source_code = []
    artifacts = []

    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]

        is_artifact = False
        if (
            (
                path.startswith("curriculum/l2-uk-en/")
                and ("/orchestration/" in path or "/status/" in path or path.endswith("-audit.md"))
            )
            or path.startswith("wiki/")
            or path.startswith("batch_state/")
            or path.startswith("logs/")
        ):
            is_artifact = True

        entry = {"status": status, "path": path}
        if is_artifact:
            artifacts.append(entry)
        else:
            source_code.append(entry)

    return {
        "source_code_changes": source_code,
        "generated_artifacts": artifacts,
        "total_changes": len(source_code) + len(artifacts),
    }
