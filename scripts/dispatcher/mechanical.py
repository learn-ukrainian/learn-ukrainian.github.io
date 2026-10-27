"""Legacy mechanical admission and digested worker scope for v2 dispatches."""

from pathlib import Path

from scripts.agent_runtime.kimi_admission import CommitTree, worktree_trees
from scripts.agent_runtime.mechanical_admission import (
    MECHANICAL_FAMILIES,
    MechanicalAdmissionRefused,
    is_opaque_readonly_recon,
    refuse_mechanical_task,
)
from scripts.agent_runtime.target_admission import mechanical_scope_digest, mechanical_worker_scope
from scripts.dispatcher.advisory import model_id


def admit(args, repo: Path, prompt: bytes) -> dict:
    """Port delegate._mechanical_task_scope and its pre-advisory target gate."""
    model = model_id(args.agent, args.model)
    review = any((args.pr is not None, args.review_attempt, args.require_review_verdict,
                  args.review_profile, args.review_author_model, args.risk))
    opaque = not review and is_opaque_readonly_recon(
        (model,), mode=args.mode, task_family=args.research_task_family, task_role=args.research_role,
    )
    language = bool(args.language_lane or args.review_profile == "ukrainian" or (not opaque and (
        (args.research_track or "").strip().casefold().startswith("l2-uk") or any(
            str(path).replace("\\", "/").lstrip("./").startswith(("curriculum/", "scripts/curriculum/"))
            for path in args.research_owned_path
        )
    )))
    scope = dict(family=args.research_task_family, role=args.research_role, track=args.research_track,
                 language_lane=language, review=bool(review), paths=[*args.owned_path, *args.research_owned_path],
                 mode=args.mode, task_prompt=args.prompt,
                 prompt_file=str(Path(args.prompt_file).resolve()) if args.prompt_file else None,
                 prompt_file_sha256=None)

    def trees():
        from scripts.dispatcher import git

        if args.cwd or args.mode == "read-only":
            return worktree_trees(Path(args.cwd) if args.cwd else repo)
        _, _, sha = git.worktree_plan(
            repo, args.agent, args.task_id, args.pinned_head or args.branch or args.base, args.cwd, args.worktree,
        )
        return [CommitTree(repo, sha)]

    refuse_mechanical_task(
        (args.model, model), mode=args.mode, task_family=scope["family"], task_role=scope["role"],
        paths=scope["paths"], review=scope["review"], language_lane=language,
        research_track=scope["track"], prompt_file=args.prompt_file, task_prompt=args.prompt, trees=trees,
    )
    if scope["family"] not in MECHANICAL_FAMILIES | {"bounded_implementation"}:
        return {}
    from scripts.dispatcher.store import digest

    scope["prompt_file_sha256"] = digest(prompt) if args.prompt_file else None
    scope["sha256"] = mechanical_scope_digest(scope)
    return scope


def verify(spec, record: dict) -> None:
    """Recheck persisted typing and the exact submitted bytes before provider build/spawn."""
    model = model_id(spec.agent, spec.model)
    prompt = spec.prompt_file.read_text(encoding="utf-8")
    scope = mechanical_worker_scope(record, mode=spec.mode, model=model, prompt=prompt)
    # Luna is bounded rather than mechanical-only. Its persisted scope must also
    # reach the common gate; the envelope/brief replay checks run separately.
    admitted = record.get("mechanical_task")
    if not scope and admitted:
        if (not isinstance(admitted, dict) or admitted.get("sha256") != mechanical_scope_digest(admitted)
                or admitted.get("mode") != spec.mode or record.get("mode") != spec.mode):
            raise MechanicalAdmissionRefused(
                "MECHANICAL_TASK_REFUSED: persisted admission inputs changed or are unavailable (#10079)"
            )
        scope = dict(task_family=admitted["family"], task_role=admitted["role"], paths=admitted["paths"],
                     research_track=admitted["track"], language_lane=admitted["language_lane"],
                     review=admitted["review"], task_prompt=prompt)
    scope["review"] = bool(scope.get("review") or any(record.get(key) for key in (
        "review_profile", "review_author_model", "review_risk", "review_attempt", "require_review_verdict", "pr",
    )))
    refuse_mechanical_task(
        (spec.model, model), mode=spec.mode, trees=lambda: worktree_trees(spec.worktree), **scope,
    )
