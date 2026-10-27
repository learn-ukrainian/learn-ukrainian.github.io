"""V2 wiring for the shared bounded-advisory contract, without the legacy launcher."""

import dataclasses
import re
from pathlib import Path

from scripts.agent_runtime import bounded_advisory as contract
from scripts.dispatcher import store
from scripts.review.model_catalog import canonical_model_id


def binding(args, prompt: bytes) -> tuple[dict, str, str]:
    excluded = {"command", "initiator", "advisory_task", "print_advisory_binding"}
    bound = {key: value for key, value in vars(args).items() if key not in excluded}
    prompt_sha = store.digest(prompt)
    return bound, prompt_sha, contract.binding_digest(contract.canonical_sha256(bound), prompt_sha)


def model_id(agent: str, model: str) -> str | None:
    alias = model.strip().casefold().split("[", 1)[0]
    if agent == "claude" and alias in {"haiku", "opus", "sonnet", "fable"}:
        from scripts.agent_runtime.model_pause import _newest_claude

        model = _newest_claude(alias)
        if model is None:
            raise ValueError("cannot resolve native Claude model alias for bounded admission")
    return canonical_model_id(model)


def state_path(task: str) -> Path:
    path = store.record_path(task)
    return (store.locate_task_record(path.parent, task) or path) if store.locate_task_record else path


def flag_refusal(args) -> str | None:
    """Mechanical port of delegate.py:16936, preserving refusal order and text."""
    task, role, digest = args.advisory_task, args.advisory_role, args.advisory_binding
    conflict = contract.FLAG_CONFLICT
    if task is not None and not str(task).strip():
        return f"{conflict}: --advisory-task must name a task"
    if task is not None and role is not None:
        return f"{conflict}: --advisory-task (bounded worker) and --advisory-role (advisor) are exclusive"
    if task is not None and str(task).strip() == str(args.task_id):
        return f"{conflict}: --advisory-task must name another task, not this one"
    if (role is None) != (digest is None):
        return f"{conflict}: --advisory-role and --advisory-binding are required together"
    if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
        return f"{conflict}: --advisory-binding must be a lowercase sha256 hex digest"
    if role is not None and args.mode != "read-only":
        return f"{contract.ADVISOR_ROUTE_REFUSED}: the advisor runs read-only, not {args.mode}"
    return None


def admit(args, model: str, repo: Path, prompt: bytes) -> dict:
    """Port of delegate.py:17049 admission, using the shared seal and policy checks."""
    try:
        if refusal := flag_refusal(args):
            raise ValueError(refusal)
        model = model_id(args.agent, model)
        policy = contract.bounded_execution_policy()
        # CLI aliases select the same provider; record the effective provider below.
        from scripts.dispatcher.cli import ALIASES

        agent = ALIASES.get(args.agent, args.agent)
        if args.advisory_role is not None:
            if model != policy.advisor_model_id:
                raise contract.AdvisoryRefused(
                    contract.ADVISOR_ROUTE_REFUSED,
                    f"--advisory-role runs on the advisor {policy.advisor_model_id}; the admitted route launches "
                    f"{agent} {args.model or model!r}",
                )
            return dict(advisory_role=policy.advisor_role, advisory_route=contract.ADVISOR_ROUTE,
                        advisory_binding_sha256=args.advisory_binding)
        classified = [*args.owned_path, *args.research_owned_path]
        requirement = contract.bounded_requirement(
            model, mode=args.mode, task_family=args.research_task_family, review_profile=args.review_profile,
            owned_paths=classified, repo_root=repo, policy=policy,
        )
        task = args.advisory_task
        if requirement is None:
            if task is not None:
                raise contract.AdvisoryRefused(
                    contract.FLAG_CONFLICT,
                    f"--advisory-task applies only to a bounded-worker dispatch; the admitted route launches "
                    f"{agent} {args.model or model!r}",
                )
            if model == policy.bounded_fallback_model_id:
                return {"advisory_exemption": dict(model_id=model, task_family=args.research_task_family,
                                                  review_profile=args.review_profile, mode=args.mode,
                                                  classified_paths=classified)}
            return {}
        bound, prompt_sha, digest = binding(args, prompt)
        if task is None:
            if model in contract.driver_brief_models() and args.research_task_family in {
                "bounded_implementation", "readonly_recon", "mechanical_classification",
            }:
                owned = contract.validate_driver_brief(bound, repo_root=repo, brief_sha256=prompt_sha, model_id=model)
                return {"driver_brief": dict(advisory_args=bound, advisory_args_sha256=contract.canonical_sha256(bound),
                                             prompt_sha256=prompt_sha, dispatch_args_sha256=digest, owned_paths=owned,
                                             repo_root=str(repo), driver=dict(identity=args.initiator, source="explicit" if args.initiator else "unknown"))}
            raise contract.AdvisoryRefused(
                contract.ENVELOPE_REQUIRED,
                f"{requirement}; dispatch it with --advisory-task <task-id> naming a finished "
                f"{policy.advisor_model_id} advisory task (operator decision 2026-09-30, #9275)",
            )
        if args.prompt == "-" or args.prompt_file == "-":
            raise contract.AdvisoryRefused(
                contract.FLAG_CONFLICT,
                "a bounded dispatch binds its prompt text; pass --prompt or --prompt-file, not stdin",
            )
        envelope = contract.load_envelope(task.strip(), state_path=state_path(task.strip()),
                                          binding_sha256=digest, repo_root=repo, policy=policy)
        contract.require_owned_paths_match(envelope.owned_paths, args.owned_path)
        return {"advisory_envelope": envelope.state_record(
            requirement, args=bound, prompt_sha256=prompt_sha, repo_root=repo, execution=None,
        )}
    except contract.AdvisoryRefused as exc:
        raise ValueError(str(exc)) from None


def execution(spec, hard_timeout: float) -> dict:
    """Actual launch settings; absent v2 budget/PR/harness controls stay disabled."""
    return dict(agent=spec.agent, model_id=model_id(spec.agent, spec.model), mode=spec.mode,
                cwd=str(spec.worktree), effort=spec.effort or None, hard_timeout=hard_timeout,
                silence_timeout=float(spec.options.get("silence_timeout", 0)),
                initial_response_timeout=float(spec.options.get("initial_response_timeout", 0)),
                max_budget_usd=None, provider=spec.provider or None, harness=None, finalize_open_pr=False)


def compose(brief: str, envelope, args: dict) -> str:
    return brief + (contract.worker_prompt_block(envelope) if envelope is not None
                    else contract.driver_brief_prompt_block(args))


class _PromptSnapshot(type(Path())):
    """Provider builders consume the same immutable bytes the worker checks."""

    def read_bytes(self):
        return self.content

    def read_text(self, encoding=None, errors=None):
        return self.content.decode(encoding or "utf-8", errors or "strict")


def snapshot(spec, prompt: bytes):
    path = _PromptSnapshot(spec.prompt_file)
    path.content = prompt
    return dataclasses.replace(spec, prompt_file=path)


def requires_check(record: dict) -> bool:
    """Preserve checks on older records; new ordinary tasks need no advisory runtime."""
    return record.get("advisory_required") is not False or any(
        record.get(key) is not None for key in ("driver_brief", "advisory_envelope", "advisory_exemption", "advisory_role")
    )


def prepare(spec, record: dict, prompt: bytes, hard_timeout: float):
    """Bind the admitted execution and append the legacy prompt contract before storing."""
    admitted = record.get("driver_brief") or record.get("advisory_envelope")
    if admitted is not None:
        admitted["admitted_execution"] = execution(spec, hard_timeout)
        if record.get("driver_brief") is not None:
            record["attribution_source"] = admitted["driver"]["source"]
            block = contract.driver_brief_prompt_block(admitted["advisory_args"])
            kind = "driver_brief"
        else:
            current = contract.load_envelope(admitted["advisor_task_id"], state_path=state_path(admitted["advisor_task_id"]),
                                              binding_sha256=admitted["dispatch_args_sha256"],
                                              repo_root=Path(admitted["repo_root"]))
            if (current.result_sha256, current.envelope_sha256, current.advisor_run_nonce) != (
                admitted["result_sha256"], admitted["envelope_sha256"], admitted["advisor_run_nonce"],
            ):
                raise contract.AdvisoryRefused(
                    contract.ENVELOPE_CHANGED,
                    f"advisory task {current.advisor_task_id!r} result changed after validation "
                    f"(sha256 {admitted['result_sha256']} → {current.result_sha256})",
                )
            block, kind = contract.worker_prompt_block(current), "advisory_envelope"
        prompt += block.encode("utf-8")
        record["prompt_blocks"] = [kind]
    elif record.get("advisory_role") is not None:
        prompt += contract.advisor_prompt_block(record["advisory_binding_sha256"]).encode("utf-8")
        record["prompt_blocks"] = ["advisory_contract"]
    record["effective_prompt_sha256"] = store.digest(prompt)
    return (snapshot(spec, prompt) if requires_check(record) or record.get("mechanical_task") else spec), prompt


def verify(spec, record: dict, hard_timeout: float) -> str | None:
    if not requires_check(record):
        return None
    actual = execution(spec, hard_timeout)
    admitted = record.get("driver_brief") or record.get("advisory_envelope")
    if admitted is not None and isinstance(admitted.get("admitted_execution"), dict):
        for field in ("agent", "model_id"):
            allowed = admitted["admitted_execution"].get(field)
            if actual[field] != allowed:
                raise contract.AdvisoryRefused(contract.EXECUTION_MISMATCH,
                                                f"{field} {actual[field]!r} is not the admitted {allowed!r}")
    policy = contract.bounded_execution_policy()
    if (admitted is None and actual["model_id"] != policy.bounded_fallback_model_id
            and contract.bounded_requirement(
                actual["model_id"], mode=spec.mode, task_family=record.get("research_task_family"),
                review_profile=record.get("review_profile"), owned_paths=record.get("owned_paths") or [],
                repo_root=spec.worktree, policy=policy,
            ) is None):
        return None
    rest = {key: value for key, value in actual.items() if key not in {"agent", "model_id", "mode", "cwd"}}
    return contract.verify_worker_admission(
        record, agent=spec.agent, model_id=actual["model_id"], mode=spec.mode, cwd=spec.worktree,
        execution=rest, prompt=spec.prompt_file.read_text(encoding="utf-8"), compose_prompt=compose,
        state_path_for=state_path, default_repo_root=spec.worktree,
    )


def handoff(spec, record: dict, options: dict, hard_timeout: float) -> str | None:
    """Reject supervisor-option drift as well as the admitted launch/brief drift."""
    admitted = record.get("driver_brief") or record.get("advisory_envelope")
    if admitted is not None:
        for field, actual in (("agent", spec.agent), ("model", spec.model), ("mode", spec.mode),
                              ("effort", spec.effort), ("provider", spec.provider)):
            if field in options and options[field] != str(actual):
                # agent aliases are parser inputs, not an execution substitution.
                from scripts.dispatcher.cli import ALIASES

                if field == "agent" and ALIASES.get(options[field], options[field]) == actual:
                    continue
                if field == "mode":
                    raise contract.AdvisoryRefused(
                        contract.ADMISSION_INVALID,
                        f"the task record's mode {actual!r} is not {options[field]!r}",
                    )
                raise contract.AdvisoryRefused(contract.EXECUTION_MISMATCH,
                                                f"{field} {options[field]!r} is not the admitted {actual!r}")
    return verify(spec, record, hard_timeout)


def record_refusal(spec, record: dict, prompt: bytes, exc) -> None:
    """Keep the legacy failed record when an admitted envelope changes before spawn (delegate.py:16405)."""
    from scripts.dispatcher import git

    refusal = f"dispatch refused before spawn: {exc}"
    record.update(status="failed", finished_at=store.now(), stderr_excerpt=refusal[:500],
                  returncode=None, exit_code=None, last_error=exc.code, failure_reason=exc.code,
                  returncode_reason="advisory envelope changed before spawn; worker not started")
    record.update(git.snapshot_delivery(spec, record))
    store.create(record, prompt)
