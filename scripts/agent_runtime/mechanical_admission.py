"""Catalog mechanical-only seats have narrow, explicitly typed task authority (#9996)."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.agent_runtime.kimi_admission import CYRILLIC, ContentTree, content_problem, worktree_trees
from scripts.review.model_catalog import canonical_model_id, load_model_catalog
from scripts.review.security_paths import is_security_sensitive_change

MECHANICAL_FAMILIES = frozenset({"routine_mechanical", "mechanical_classification", "readonly_recon"})
MECHANICAL_ROLES = MECHANICAL_FAMILIES | {"mechanical_only"}


class MechanicalAdmissionRefused(ValueError):
    """A mechanical-only model was requested outside its catalog authority."""


def refuse_mechanical_task(
    models: Iterable[str | None], *, mode: str, task_family: str | None = None,
    task_role: str | None = None, paths: Iterable[str] = (), review: bool = False,
    language_lane: bool = False, research_track: str | None = None,
    prompt_file: str | None = None,
    task_prompt: str | None = None,
    trees: Sequence[ContentTree] | Callable[[], Sequence[ContentTree]] = (),
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
    constrained = [catalog["models"][identity] for pin in pins
                   if (identity := canonical_model_id(pin, catalog))
                   and "mechanical_only" in catalog["models"][identity]["roles"]]
    if not constrained:
        return

    def refuse(reason: str) -> None:
        raise MechanicalAdmissionRefused(f"MECHANICAL_TASK_REFUSED: {reason} (#9996)")

    if review:
        refuse("mechanical-only seats never perform review, critique or approval")
    if task_family not in MECHANICAL_FAMILIES or any(task_family not in model["roles"] for model in constrained):
        refuse("declare a catalog-eligible --research-task-family: routine_mechanical, mechanical_classification or readonly_recon")
    if task_role not in {None, "implementation", "recon", "classification", "triage"}:
        refuse("driver, design, advisory, approval and content roles are excluded")
    if mode not in {"read-only", "workspace-write"} or (task_family != "routine_mechanical" and mode != "read-only"):
        refuse("only routine mechanical work may write; classification and recon must be read-only")
    owned = tuple(paths)
    if not owned:
        refuse("declare narrow owned paths for the mechanical task")
    if any(PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts or "\\" in path for path in owned):
        refuse("owned paths must be repository-relative without traversal")
    if is_security_sensitive_change((), owned):
        refuse("security-sensitive owned paths are excluded")
    if language_lane or (research_track or "").casefold().startswith("l2-uk"):
        refuse("Ukrainian authoring, review and content are excluded")
    if any(CYRILLIC.search(path) or set(PurePosixPath(path).parts) & {"curriculum", "wiki"} for path in owned):
        refuse("Ukrainian content paths are excluded")
    try:
        if task_prompt:
            from scripts.lib.rules_core import core_block

            # The canonical core contains Ukrainian normative examples and is
            # carried by every seat. Exempt only its exact canonical bytes.
            task_text = task_prompt.replace(core_block("core"), "")
            if content_problem(task_text.encode("utf-8")):
                refuse("task prompt must be plain UTF-8 without Cyrillic")
        if prompt_file and content_problem(Path(prompt_file).read_bytes()):
            refuse("task input must be plain UTF-8 without Cyrillic")
        resolved = trees() if callable(trees) else trees
        if not resolved:
            refuse("owned content must be available for admission")
        for tree in resolved:
            for path in owned:
                _, files = tree.owned_files(path)
                for name, data in files.items():
                    if is_security_sensitive_change((name,)) or set(PurePosixPath(name).parts) & {"curriculum", "wiki"}:
                        refuse("owned scope contains security-sensitive or Ukrainian content paths")
                    if CYRILLIC.search(name) or content_problem(data):
                        refuse("owned content must be plain UTF-8 without Cyrillic")
    except MechanicalAdmissionRefused:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        refuse(f"task input unavailable ({type(exc).__name__})")


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
