"""Catalog mechanical-only seats have narrow, explicitly typed task authority (#9996)."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.agent_runtime.kimi_admission import CYRILLIC, ContentTree, content_problem, worktree_trees
from scripts.review.model_catalog import (
    MECHANICAL_FAMILIES,
    bounded_execution_policy,
    canonical_model_id,
    load_model_catalog,
)
from scripts.review.model_catalog import (
    MECHANICAL_ROLES as MECHANICAL_ROLES,
)
from scripts.review.security_paths import is_security_sensitive_change


class MechanicalAdmissionRefused(ValueError):
    """A mechanical-only model was requested outside its catalog authority."""


def refuse_mechanical_task(
    models: Iterable[str | None], *, mode: str, task_family: str | None = None,
    task_role: str | None = None, paths: Iterable[str] = (), review: bool = False,
    language_lane: bool = False, research_track: str | None = None,
    prompt_file: str | None = None,
    task_prompt: str | None = None,
    driver_brief: bool = False,
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
    preferred = bounded_execution_policy(catalog).bounded_worker_model_id
    identities = {canonical_model_id(pin, catalog) for pin in pins}
    constrained = [catalog["models"][identity] for identity in identities if identity and (
        "mechanical_only" in catalog["models"][identity]["roles"]
        or (identity == preferred and (driver_brief or task_family == "bounded_implementation"))
    )]
    # Explicit-envelope research roles are free-form. Keep their historical
    # vocabulary while refusing excluded activities and their class siblings.
    excluded_roles = {"driver", "orchestrator", "orchestration", "design", "architecture",
                      "approval", "advisory", "advisor", "adviser", "advice", "consult", "consultation",
                      "review", "reviewer", "critique", "security", "ukrainian", "content", "language"}
    if preferred in identities and excluded_roles.intersection(re.split(r"[\W_]+", (task_role or "").casefold())):
        raise MechanicalAdmissionRefused("MECHANICAL_TASK_REFUSED: bounded workers cannot take driver, design, advisory or review roles")
    if not constrained:
        return

    def refuse(reason: str) -> None:
        raise MechanicalAdmissionRefused(f"MECHANICAL_TASK_REFUSED: {reason} (#9996)")

    if review:
        refuse("mechanical-only seats never perform review, critique or approval")
    families = MECHANICAL_FAMILIES | {"bounded_implementation"}
    if task_family not in families or any(task_family not in model["roles"] for model in constrained):
        refuse("declare a catalog-eligible --research-task-family: routine_mechanical, mechanical_classification, readonly_recon or bounded_implementation")
    typed_role = driver_brief or any("mechanical_only" in model["roles"] for model in constrained)
    if typed_role and task_role not in {None, "implementation", "recon", "classification", "triage"}:
        refuse("driver, design, advisory, approval and content roles are excluded")
    bounded = task_family == "bounded_implementation"
    if typed_role and bounded and task_role != "implementation":
        refuse("bounded implementation requires the implementation role")
    allowed_modes = {"workspace-write", "danger"} if bounded else {"read-only", "workspace-write"}
    if bounded and not typed_role:
        allowed_modes.add("read-only")  # Existing Luna envelopes retain their read-only launch mode.
    if mode not in allowed_modes or (
        task_family not in {"routine_mechanical", "bounded_implementation"} and mode != "read-only"
    ):
        refuse("only routine mechanical or bounded implementation work may write; classification and recon must be read-only")
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
    stage = "task prompt"
    try:
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
        stage = "owned content"
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
