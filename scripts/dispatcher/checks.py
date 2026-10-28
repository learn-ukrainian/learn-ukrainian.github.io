"""Dispatch input, review independence and resource admission checks."""

import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote

import yaml

from scripts.agent_runtime import bounded_advisory as advisory
from scripts.dispatcher import git, store
from scripts.dispatcher.types import TaskSpec
from scripts.review.model_catalog import advisory_role_policy, canonical_model_id

CATALOG = Path(__file__).resolve().parents[1] / "config" / "model_catalog.yaml"


def advisory_binding(args, prompt: bytes) -> tuple[dict, str, str]:
    """Bind every dispatch input except attribution, parser plumbing and envelope reference."""
    excluded = {"command", "initiator", "advisory_task", "print_advisory_binding"}
    bound = {key: value for key, value in vars(args).items() if key not in excluded}
    prompt_sha = store.digest(prompt)
    return bound, prompt_sha, advisory.binding_digest(advisory.canonical_sha256(bound), prompt_sha)


def check_bounded_advisory(args, model: str, repo: Path, prompt: bytes) -> dict:
    """Apply the legacy bounded-worker policy before creating a worktree or starting a provider."""
    try:
        alias = model.strip().casefold().split("[", 1)[0]
        if args.agent == "claude" and alias in {"haiku", "opus", "sonnet", "fable"}:
            from scripts.agent_runtime.model_pause import _newest_claude

            model = _newest_claude(alias)
            if model is None:
                raise ValueError("cannot resolve native Claude model alias for bounded admission")
        model = canonical_model_id(model)
        requirement = advisory.bounded_requirement(
            model, mode=args.mode, task_family=args.research_task_family, review_profile=args.review_profile,
            owned_paths=[*args.owned_path, *args.research_owned_path], repo_root=repo,
        )
        task = args.advisory_task
        if task is not None and (not task.strip() or task.strip() == args.task_id or requirement is None):
            raise advisory.AdvisoryRefused(advisory.FLAG_CONFLICT, "--advisory-task must name another task for a bounded worker")
        if requirement is None:
            return {}
        bound, prompt_sha, binding = advisory_binding(args, prompt)
        if task is None:
            if model in advisory.driver_brief_models() and args.research_task_family in {
                "bounded_implementation", "readonly_recon", "mechanical_classification",
            }:
                owned = advisory.validate_driver_brief(bound, repo_root=repo, brief_sha256=prompt_sha, model_id=model)
                return {"driver_brief": dict(advisory_args=bound, prompt_sha256=prompt_sha,
                                             dispatch_args_sha256=binding, owned_paths=owned)}
            raise advisory.AdvisoryRefused(advisory.ENVELOPE_REQUIRED, f"{requirement}; use --advisory-task TASK_ID")
        if args.prompt == "-" or args.prompt_file == "-":
            raise advisory.AdvisoryRefused(advisory.FLAG_CONFLICT, "bounded dispatch requires --prompt or --prompt-file, not stdin")
        path = store.record_path(task.strip())
        path = store.locate_task_record(path.parent, task.strip()) or path
        envelope = advisory.load_envelope(task.strip(), state_path=path, binding_sha256=binding, repo_root=repo)
        advisory.require_owned_paths_match(envelope.owned_paths, args.owned_path)
        return {"advisory_envelope": envelope.state_record(
            requirement, args=bound, prompt_sha256=prompt_sha, repo_root=repo, execution=None,
        )}
    except advisory.AdvisoryRefused as exc:
        raise ValueError(str(exc)) from None


def check_advisory_role(args, model: str) -> dict:
    """Record a read-only advisory decision's catalog role and the digest it binds.

    The worker seals the result at finish (``worker.py``). The consumer of the
    decision, not dispatch, checks that the model is the non-author advisor.
    """
    role, binding = args.advisory_role, args.advisory_binding
    if role is None and binding is None:
        return {}
    if role is None or binding is None:
        raise ValueError("--advisory-role and --advisory-binding are required together")
    try:
        policy = advisory_role_policy(role)
    except KeyError:
        raise ValueError(f"--advisory-role {role!r} is not a catalog advisory_roles entry") from None
    if args.mode != "read-only":
        raise ValueError("--advisory-role runs read-only")
    if canonical_model_id(model) not in policy.advisor_models:
        raise ValueError(f"--advisory-role {role} runs on a designated advisor: {sorted(policy.advisor_models)}")
    if not re.fullmatch(r"[0-9a-f]{64}", binding):
        raise ValueError("--advisory-binding must be a lowercase sha256 hex digest")
    return {"advisory_role": role, "advisory_route": policy.route, "advisory_binding_sha256": binding}


def _handle_private_input(spec: TaskSpec, message: str) -> None:
    if spec.agent == "muse":
        spec.options["contributor_mode"] = "off"
    else:
        raise ValueError(message)


def check_private_input(spec: TaskSpec, repo_key: str) -> None:
    if spec.agent not in {"muse", "opencode", "hermes"}:
        return
    repos = yaml.safe_load(git.CONFIG.read_text())["repos"]
    private = {
        key: item for key, item in repos.items() if item.get("private", False) or "private" in item.get("role", "")
    }
    roots = [git.resolve_repo(key)[0] for key in private]
    if git.resolve_repo(repo_key)[0] in roots:
        return _handle_private_input(spec, "private input is not permitted for this agent")
    origin = spec.options.get("prompt_file")
    if origin and origin != "-" and any(Path(origin).resolve().is_relative_to(root) for root in roots):
        return _handle_private_input(spec, "private prompt file is not permitted for this agent")
    # The content contract is lexical: decode once, then compare without changing provider input.
    text = unquote(spec.prompt_file.read_text()).casefold()
    identifiers = [str(root) for root in roots]
    identifiers.extend(item.get(field, "") for item in private.values() for field in ("local_name", "github"))
    if any(identifier.casefold() in text for identifier in identifiers if identifier):
        _handle_private_input(spec, "private path input is not permitted for this agent")


def _model_families() -> dict[str, str | None]:
    models = yaml.safe_load(CATALOG.read_text())["models"]
    families = {}
    for name, item in models.items():
        for identifier in [
            name,
            *item.get("aliases", []),
            *item.get("routing_wire_ids", {}).values(),
            *item.get("runtime_model_ids", []),
        ]:
            families[identifier] = item.get("family")
    return families


def check_review_family(author_model: str | None, reviewer_model: str) -> None:
    if author_model is None:
        return
    families = _model_families()
    author, reviewer = families.get(author_model), families.get(reviewer_model)
    if not author or not reviewer or author == reviewer:
        raise ValueError("review independence requires two known, different model families")


def check_branch_author_families(args, repo: Path, repository: dict, head_sha: str, reviewer_model: str) -> None:
    """Keep a branch review outside every author family committed on the branch (FR-23, C-2902).

    Families are derived from the branch itself, read with the facts the
    verdict recorder accepts, whether or not ``--review-author-model`` is
    given. The range is always the fetched default branch to the head; the
    caller's ``--base`` only chooses where a worktree starts, never authorship
    (F6). An empty range, a range without attributed authors and a commit with
    an unresolvable author are refusals in every review mode (F9). The family
    comes from each commit's ``X-Agent`` trailer, which is author-controlled
    (the git author is not read): a readable catalog trailer is trusted as
    that family. A red-team review differs only in its seat rule, which the
    recorder applies: it may share an author family.
    """
    from scripts.review.record_cf_verdict import (
        RecordError,
        admitted_unknown_history,
        collect_branch_review_facts,
        default_branch_review_base,
        refuse_excluded_only_range,
        require_resolved_branch_authors,
    )

    red_team = (args.review_mode or "").strip().casefold() == "red_team"
    try:
        tip, base = default_branch_review_base(repo, head_sha)
        # Untrailered history is admissible only to a red team, by an existing admission receipt.
        history = (
            admitted_unknown_history(repository=repository["github"], branch=args.branch, head_sha=head_sha,
                                     task_root=store.tasks_dir(), repo_root=repo)
            if red_team and args.branch else ()
        )
        facts = collect_branch_review_facts(
            repository=repository["github"], repo_root=repo, base_tip_sha=base, head_sha=head_sha,
            task_root=store.tasks_dir(), authorship_exclude_sha=tip, unknown_history=history,
        )
        refuse_excluded_only_range(facts, repo_root=repo, exclude_sha=tip)
        require_resolved_branch_authors(facts)
    except (RecordError, OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"review independence: branch author families unavailable ({exc})") from None
    if not facts.existing_families:
        raise ValueError("review independence: the reviewed range has no attributed author commits")
    if red_team:
        return
    reviewer = _model_families().get(reviewer_model)
    if not reviewer or reviewer in facts.excluded_families:
        raise ValueError(
            f"review independence: reviewer family {reviewer or 'unknown'} is not outside the branch's author "
            f"families {sorted(facts.excluded_families)}; choose a reviewer from another family"
        )


def check_review_subjects(agent, model, seats, families, owned_paths, *, review=False):
    from types import SimpleNamespace

    from scripts.review.subject_seat import classify_owned_path, prepare_subject_exclusion, subject_exclusion_reason

    if review:
        for path in owned_paths:
            if classify_owned_path(path).kind == "ambiguous":
                raise ValueError(f"ambiguous review subject path: {path}")
    exclusion = prepare_subject_exclusion(subject_seats=frozenset(seats), subject_families=frozenset(families),
                                          owned_paths=tuple(owned_paths))
    if exclusion.fail_closed_reason:
        raise ValueError(exclusion.fail_closed_reason)
    if not exclusion.seats and not exclusion.families:
        return exclusion
    models = {model}
    if agent == "cursor":
        from scripts.review.model_catalog import (
            CURSOR_APPROVED_WIRE_PINS,
            cursor_pinned_models,
            substitution_default_model,
        )

        if model not in {*cursor_pinned_models(), *CURSOR_APPROVED_WIRE_PINS}:
            models.add(substitution_default_model("cursor"))
    model_families = _model_families()
    for effective_model in models:
        family = model_families.get(effective_model)
        if not family:
            raise ValueError("subject exclusion requires a known effective reviewer model family")
        candidate = SimpleNamespace(name=agent, family=family, concrete_model=effective_model,
                                    route=agent, transport=agent)
        reason = subject_exclusion_reason(candidate, seats=exclusion.seats, families=exclusion.families,
                                          evidence=exclusion.evidence)
        if reason:
            raise ValueError(reason)
    return exclusion


def check_resources(paths) -> None:
    available = next(
        int(line.split()[1]) * 1024
        for line in Path("/proc/meminfo").read_text().splitlines()
        if line.startswith("MemAvailable:")
    )
    if available < 8.5 * 1024**3:
        raise ValueError("insufficient memory: MemAvailable must be at least 8.5 GiB")
    for path in paths:
        path = Path(path)
        while not path.exists():
            path = path.parent
        usage = shutil.disk_usage(path)
        if usage.used / usage.total >= 0.9:
            raise ValueError("insufficient disk: usage must be below 90%")
