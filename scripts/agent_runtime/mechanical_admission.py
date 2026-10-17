"""Catalog mechanical-only seats have narrow, explicitly typed task authority (#9996)."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.agent_runtime.bounded_advisory import AdvisoryRefused
from scripts.agent_runtime.kimi_admission import BRIDGE_MODE, CYRILLIC, ContentTree, content_problem, worktree_trees
from scripts.review.model_catalog import (
    MECHANICAL_FAMILIES,
    canonical_model_id,
    load_model_catalog,
)
from scripts.review.model_catalog import (
    MECHANICAL_ROLES as MECHANICAL_ROLES,
)
from scripts.review.security_paths import is_security_sensitive_change

TRIAL_LABEL = "haiku-luna-coding-trial"
TRIAL_FAMILY = "bounded_implementation"
DEEPSEEK_MODEL = next(
    model_id for model_id, entry in load_model_catalog()["models"].items()
    if entry["family"] == "deepseek" and entry.get("bounded_implementation_trial") == TRIAL_LABEL
)


def sensitive_data_path(path: str) -> bool:
    """Reject credential, environment and secret filenames, including glob scopes."""
    parts = PurePosixPath(path.casefold().strip("`\"'(),:;[]{}<>")).parts
    return any(
        part in {".ssh", ".aws", ".config", ".netrc", ".npmrc", ".pypirc"}
        or part.startswith((".env", "env.", "credentials", "credential.", "secret"))
        or part.endswith((".pem", ".key", ".p12", ".pfx"))
        for part in parts
    )


def is_trial_model(model: str | None) -> bool:
    """Resolve trial membership from the catalog, including model aliases."""
    catalog = load_model_catalog()
    identity = canonical_model_id(model, catalog) if model else None
    return bool(identity and catalog["models"][identity].get("bounded_implementation_trial") == TRIAL_LABEL)


class MechanicalAdmissionRefused(ValueError):
    """A mechanical-only model was requested outside its catalog authority."""


def refuse_mechanical_task(
    models: Iterable[str | None], *, mode: str, task_family: str | None = None,
    task_role: str | None = None, paths: Iterable[str] = (), review: bool = False,
    language_lane: bool = False, research_track: str | None = None,
    prompt_file: str | None = None,
    task_prompt: str | None = None,
    trees: Sequence[ContentTree] | Callable[[], Sequence[ContentTree]] = (),
    repo: str | None = None,
) -> None:
    """Refuse original and resolved mechanical-only pins before routing or launch effects.

    Unclassified work is refused. Classification and recon are read-only; routine
    mechanical writes require narrow ownership. Content is conservatively limited
    to plain UTF-8 without Cyrillic, including every descendant of a declared scope.
    Identity and eligible task families come from catalog roles, never model ids.
    """
    pins = tuple(model for model in models if model)
    if not pins:
        return
    catalog = load_model_catalog()
    deepseek = any(
        (identity := canonical_model_id(pin, catalog)) and catalog["models"][identity]["family"] == "deepseek"
        for pin in pins
    )
    if deepseek and mode == BRIDGE_MODE and not review:
        if language_lane or task_role in {"design", "approval", "advisor"}:
            raise MechanicalAdmissionRefused("DEEPSEEK_TASK_REFUSED: no Ukrainian content, design or approval")
        return  # Ordinary non-language consultation retains its existing bridge gates.
    if deepseek and (task_family != TRIAL_FAMILY or any(
        canonical_model_id(pin, catalog) != DEEPSEEK_MODEL for pin in pins
        if catalog["models"].get(canonical_model_id(pin, catalog), {}).get("family") == "deepseek"
    )):
        raise MechanicalAdmissionRefused("DEEPSEEK_TASK_REFUSED: bounded_implementation trial only")
    if deepseek and repo != "public-monorepo":
        raise MechanicalAdmissionRefused("DEEPSEEK_TASK_REFUSED: public-repository worktrees only")
    trial = task_family == TRIAL_FAMILY and any(is_trial_model(pin) for pin in pins)
    constrained = [catalog["models"][identity] for pin in pins
                   if (identity := canonical_model_id(pin, catalog))
                   and ("mechanical_only" in catalog["models"][identity]["roles"]
                        or (trial and is_trial_model(pin)))]
    if not constrained:
        return

    def refuse(reason: str) -> None:
        raise MechanicalAdmissionRefused(f"MECHANICAL_TASK_REFUSED: {reason} (#9996)")

    if review:
        refuse("mechanical-only seats never perform review, critique or approval")
    if (task_family not in MECHANICAL_FAMILIES and not trial) or any(task_family not in model["roles"] for model in constrained):
        refuse("declare a catalog-eligible --research-task-family: routine_mechanical, mechanical_classification or readonly_recon")
    if task_role not in {None, "implementation", "recon", "classification", "triage"}:
        refuse("driver, design, advisory, approval and content roles are excluded")
    if not trial and (mode not in {"read-only", "workspace-write"} or (task_family != "routine_mechanical" and mode != "read-only")):
        refuse("only routine mechanical work may write; classification and recon must be read-only")
    if trial and mode not in {"read-only", "workspace-write", "danger"}:
        refuse("bounded implementation requires a supported execution mode")
    owned = tuple(paths)
    if not owned:
        refuse("declare narrow owned paths for the mechanical task")
    if deepseek and any(sensitive_data_path(path) for path in owned):
        refuse("credential, env and secret files are excluded")
    if deepseek and any(set(path) & set("*?[") or path.endswith("/") for path in owned):
        refuse("data fence requires explicit file paths, excluding credential, env and secret files")
    if any(PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts or "\\" in path for path in owned):
        refuse("owned paths must be repository-relative without traversal")
    if is_security_sensitive_change((), owned):
        refuse("security-sensitive owned paths are excluded")
    if language_lane or (research_track or "").casefold().startswith("l2-uk"):
        refuse("Ukrainian authoring, review and content are excluded")
    if any(CYRILLIC.search(path) or set(PurePosixPath(path).parts) & {"curriculum", "wiki"} for path in owned):
        refuse("Ukrainian content paths are excluded")
    stage = "task prompt"
    try:
        brief = ""
        if trial:
            stage = "prompt file" if prompt_file else "task prompt"
            brief = Path(prompt_file).read_text(encoding="utf-8") if prompt_file else task_prompt or ""
        if deepseek:
            from scripts.lib.rules_core import core_block

            if any(sensitive_data_path(word) for word in brief.replace(core_block("core"), "").split()):
                refuse("credential, env and secret files in prompts are excluded")
        if task_prompt:
            from scripts.lib.rules_core import core_block

            # The canonical core contains Ukrainian normative examples and is
            # carried by every seat. Exempt only its exact canonical bytes.
            task_text = task_prompt.replace(core_block("core"), "")
            if content_problem(task_text.encode("utf-8")):
                refuse("task prompt must be plain UTF-8 without Cyrillic")
        stage = "prompt file"
        if prompt_file and content_problem(Path(prompt_file).read_bytes()):
            refuse("task input must be plain UTF-8 without Cyrillic")
        stage = "tree resolution"
        resolved = trees() if callable(trees) else trees
        if not resolved:
            refuse("owned content must be available for admission")
        if trial:
            from scripts.agent_runtime.bounded_advisory import parse_envelope, require_owned_paths_match

            packet = parse_envelope(brief, repo_root=getattr(resolved[0], "root", Path.cwd()), driver_packet=True)
            require_owned_paths_match(packet["owned_paths"], owned)
        stage = "owned content"
        for tree in resolved:
            for path in owned:
                if trial and (root := getattr(tree, "root", None)) is not None:
                    from scripts.agent_runtime.bounded_advisory import validate_owned_path
                    validate_owned_path(path, root)
                    target = root / path
                    if deepseek and target.is_dir():
                        refuse("data fence requires explicit file paths")
                    if any(part.is_symlink() for part in (target, *target.parents) if part != root):
                        refuse("symlink owned paths are excluded")
                _, files = tree.owned_files(path)
                for name, data in files.items():
                    if trial and (root := getattr(tree, "root", None)) is not None and (root / name).is_symlink():
                        refuse("symlink owned content is excluded")
                    if is_security_sensitive_change((name,)) or set(PurePosixPath(name).parts) & {"curriculum", "wiki"}:
                        refuse("owned scope contains security-sensitive or Ukrainian content paths")
                    if deepseek and sensitive_data_path(name):
                        refuse("owned scope contains credential, env or secret files")
                    if CYRILLIC.search(name) or content_problem(data):
                        refuse("owned content must be plain UTF-8 without Cyrillic")
    except MechanicalAdmissionRefused:
        raise
    except AdvisoryRefused as exc:
        refuse(str(exc))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        refuse(f"task input unavailable at {stage} ({type(exc).__name__})")


def refuse_mechanical_execution(
    model: str | None, *, mode: str, cwd: Path, tool_config: Mapping[str, Any] | None,
    prompt: str | None = None,
) -> None:
    """Recheck persisted task typing and the execution tree at the Claude adapter."""
    config = tool_config or {}
    task = config.get("mechanical_task") or {}
    refuse_mechanical_task(
        (model,), mode=mode, task_family=task.get("family"), task_role=task.get("role"),
        paths=task.get("paths") or (), research_track=task.get("track"),
        task_prompt=prompt,
        language_lane=bool(task.get("language_lane") or config.get("language_lane") or config.get("review_profile") == "ukrainian"),
        # reviewer_tools is also the ordinary read-only permissions profile;
        # it does not type an activity as review. Use actual review markers.
        review=bool(task.get("review")) or any(config.get(key) for key in (
            "review_isolation", "review_profile", "review_manifest", "review_attempt"
        )),
        trees=lambda: worktree_trees(cwd),
    )
