"""Protected v2 review preparation; admission and claims copied from delegate.

Keep the legacy refusal vocabulary and ordering. The worker owns the boundary's
lifetime; receipt files are created by review_mcp's exclusive reservation.
"""

import argparse
import contextlib
import json
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root
from scripts.common.task_scratch import resolve_scratch_root
from scripts.dispatcher import git, store
from scripts.guardrails import worktree_containment
from scripts.orchestration import worktree_claims
from scripts.review.target_resolution import _origin_github_repo

_UKRAINIAN_MODEL_FAMILIES = frozenset({"anthropic", "openai", "google"})
_UKRAINIAN_AGENT_FAMILIES = {"claude": "anthropic", "codex": "openai", "agy": "google", "gemini": "google"}


def _dispatch_is_language_lane(args, *, model=None):
    from scripts.review.language_lane import is_ukrainian_review

    return (is_ukrainian_review(vars(args))
            or str(args.research_track or "").strip().lower().startswith("l2-uk")
            or any(str(path).replace("\\", "/").lstrip("./").startswith(("curriculum/", "scripts/curriculum/"))
                   for path in args.research_owned_path))


_local_repo_root = Path(__file__).resolve().parents[2]
_REPO_ROOT = main_checkout_root(_local_repo_root)
DEFAULT_GIT_TIMEOUT_S = 30


def _sanitized_git_env():
    return {key: value for key, value in git.sanitized_git_env().items()
            if not key.startswith("PRE_COMMIT")} | {"GIT_TERMINAL_PROMPT": "0"}


def _load_worktree_containment():
    return worktree_containment


def _worktree_lock_dir():
    common = git._git(_REPO_ROOT, "rev-parse", "--path-format=absolute", "--git-common-dir", isolate=True)
    return Path(common) / worktree_claims.LOCK_DIR_NAME


def worktree_lock(path):
    return worktree_claims.worktree_lock(path, lock_dir=_worktree_lock_dir())


def _review_attempt_prompt_admission(
    args: argparse.Namespace, early_prompt: str | None, review_id: str, attempt_id: str
) -> tuple[str | None, dict[str, Any] | None]:
    """Admit a ``--review-attempt`` prompt, or say why not: ``(refusal, None)`` or ``(None, review_contract)``.

    Runs before any side effect. The prompt's own attempt block (#8996) must name this dispatch's ids, and the
    prompt must come from a ``--prompt-file`` whose render record matches the code the seat would run (#9163).
    """
    import yaml

    from scripts.agent_runtime.review_mcp import check_review_contract
    from scripts.review.prompts.check import AttemptIdsUnreadableError, check_prompt, parse_attempt_ids
    from scripts.review.render_contract import ReviewContractError

    prompt_file = Path(args.prompt_file) if getattr(args, "prompt_file", None) else None
    prompt = early_prompt or ""
    try:
        manifest = yaml.safe_load(Path(args.review_attempt).read_bytes())
        if isinstance(manifest, dict) and any(key in manifest for key in ("manifest_schema", "kind", "inputs")):
            contract = check_review_contract(prompt_file, prompt, review_id=review_id, attempt_id=attempt_id)
            try:
                input_root = worktree_claims.required_review_input_root(contract)
            except ValueError as err:
                return f"❌ review attempt refused: {err}", None
            checked = check_prompt(
                prompt,
                Path(args.review_attempt),
                repo_root=Path(input_root),
                prompts_dir=Path(contract["server_checkout"]) / "scripts/review/prompts",
                recorded_prompts_dir=Path(contract["render_checkout"]) / "scripts/review/prompts",
                files_read=contract["recorded_files_read"],
                template_sha256=contract["recorded_template_sha256"],
                recorded_templates=contract["recorded_templates"],
                review_id=review_id,
                attempt_id=attempt_id,
                review_access=getattr(args, "review_access", "full"),
            )
            if not checked.passed:
                return "❌ review attempt refused: prompt_render_invalid: " + "; ".join(checked.errors), None
            return None, contract
        if prompt_file is None and getattr(args, "prompt", None) == "-":
            # stdin is read only later, and a stdin prompt has no render record: refused as review_render_record_missing
            return None, check_review_contract(None, "")
        prompt_review_id, prompt_attempt_id = parse_attempt_ids(prompt, custom=True)
    except AttemptIdsUnreadableError as err:
        return f"❌ review attempt refused: prompt_attempt_ids_unreadable: {err} (#8996)", None
    except ReviewContractError as err:
        return f"❌ {err}", None
    except (OSError, ValueError, yaml.YAMLError) as err:
        return f"❌ review attempt refused: prompt_render_invalid: {type(err).__name__}", None
    if prompt_review_id is None or prompt_attempt_id is None:
        # A seat whose prompt names no ids can only guess them, and a guessed id never matches the
        # ledger this dispatch prepares — the failure #8996 was filed for.
        return (
            "❌ review attempt refused: prompt_attempt_ids_missing: a --review-attempt prompt must print "
            "the review_id and attempt_id its seat echoes (render it with --review-id/--attempt-id) (#8996)"
        ), None
    id_mismatches = [
        f"{name} prompt={found!r} dispatch={expected!r}"
        for name, found, expected in (
            ("review_id", prompt_review_id, review_id),
            ("attempt_id", prompt_attempt_id, attempt_id),
        )
        if found != expected
    ]
    if id_mismatches:
        return (
            "❌ review attempt refused: prompt_attempt_ids_mismatch: the prompt's attempt block ids differ "
            f"from --review-id/--attempt-id ({'; '.join(id_mismatches)}) (#8996)"
        ), None
    # The seat's sources server launches from the primary checkout; the prompt may have been rendered anywhere.
    try:
        return None, check_review_contract(prompt_file, prompt, review_id=review_id, attempt_id=attempt_id)
    except ReviewContractError as err:
        return f"❌ {err}", None
    except (OSError, ValueError) as err:
        return f"❌ review attempt refused: prompt_render_invalid: {type(err).__name__}", None




def _lock_review_input_root(
    contract: dict[str, Any],
    locks: contextlib.ExitStack,
    *,
    locked_worktree: Path | None = None,
    inputs: Sequence[Path] = (),
) -> None:
    """Protect input preparation until the task's persisted record takes over (#9485, #9597).

    Lock the containing registered checkout of the input root and of every other
    attempt input (``_review_attempt_input_paths``), rather than an input
    subdirectory's lock. The dispatch stack releases them on every early return
    or exception, and the kernel releases them on process exit; no git lock leaks.
    """
    input_root = Path(worktree_claims.required_review_input_root(contract)).resolve()
    if not input_root.is_dir():
        raise ValueError("review input root disappeared before preparation")
    paths = [input_root]
    for path in inputs:
        resolved = path.resolve()
        if not resolved.exists():
            raise ValueError("review attempt input disappeared before preparation")
        paths.append(resolved)
    # Reuse eligibility excludes ACP runtime checkouts. Reading one still
    # requires its removal lock, so consult registration directly here: the
    # primary's, exactly as the removal guard does, never a repository
    # discovered from an input path.
    wc = _load_worktree_containment()
    try:
        main_root, registered = worktree_claims.repository_registration(_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"review input {exc}") from exc
    selected = {
        tree
        for path in paths
        if (tree := worktree_claims.review_input_worktree(path, main_root=main_root, registered=registered)) is not None
    }
    for tree in sorted(selected):
        if locked_worktree is None or tree != locked_worktree.resolve():
            locks.enter_context(worktree_lock(tree))
    current = wc.registered_worktrees(main_root)
    if any(not path.exists() for path in paths) or any(tree not in current for tree in selected):
        raise ValueError("review input worktree disappeared while dispatch waited for its lock")




def _review_attempt_input_paths(manifest: str) -> list[Path]:
    """Paths a formal attempt reads after its id is reserved, besides its input root (#9597).

    The worker re-reads the manifest (``attempt_boundary``) at the canonical path
    dispatch froze at admission, and runs this checkout's code and its lazy
    imports for the whole attempt. A formal attempt takes no output schema
    (``attempt_output_schema_unsupported``). The receipts, the sources server and
    its interpreter live in the primary checkout or this one; the runtime tmp root
    is refused inside a removable checkout (``_refuse_review_scratch_in_worktree``).
    """
    return list(dict.fromkeys([Path(manifest).resolve(), _local_repo_root]))




def _refuse_review_scratch_in_worktree() -> None:
    """Refuse an attempt whose runtime scratch would sit in a removable checkout (#9597).

    The worker's tmp lease lives under the fleet scratch root for the whole
    attempt and no task record claims it, so a scratch root whose real path is
    inside a registered linked checkout is refused before the attempt id is
    reserved. The registration is the primary's, the removal guard's source;
    discovering a repository from the scratch path would let a nested one mask
    the checkout around it.
    """
    scratch = resolve_scratch_root().resolve()
    try:
        main_root, registered = worktree_claims.repository_registration(_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"review_scratch_root_unverifiable: {exc}") from exc
    tree = worktree_claims.review_input_worktree(scratch, main_root=main_root, registered=registered)
    if tree is not None:
        raise ValueError(
            f"review_scratch_root_in_worktree: the fleet scratch root {scratch} lies in removable "
            f"checkout {tree}; set LU_SCRATCH_ROOT outside every linked checkout"
        )


_REVIEW_ATTEMPT_NO_REUSE_MARKER = "lu-review-attempt-no-reuse"


def _review_attempt_marker_path(worktree_path: Path) -> Path:
    try:
        proc = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "--absolute-git-dir"],
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"could not resolve git admin directory for {worktree_path}: {exc}") from exc
    git_dir = Path(proc.stdout.strip())
    if proc.returncode != 0 or not git_dir.is_absolute():
        raise RuntimeError(f"could not resolve git admin directory for {worktree_path}")
    return git_dir / _REVIEW_ATTEMPT_NO_REUSE_MARKER


def _refuse_review_attempt_worktree_reuse(worktree_path: Path) -> None:
    # A real linked worktree has a .git pointer. Test stubs may model only the
    # directory; the existing validation still handles those paths.
    if not (worktree_path / ".git").exists():
        return
    marker = _review_attempt_marker_path(worktree_path)
    if marker.is_file():
        try:
            task_id = marker.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"could not read review attempt marker in {worktree_path}: {exc}") from exc
        raise ValueError(f"worktree {worktree_path} belongs to review attempt task {task_id!r}; reuse refused (#8517)")


def _mark_review_attempt_worktree(worktree_path: Path, task_id: str) -> None:
    marker = _review_attempt_marker_path(worktree_path)
    marker.write_text(f"{task_id}\n", encoding="utf-8")



def _origin_base_ref(base_branch: str) -> str:
    """Return the remote ref used for ahead-count checks."""
    if base_branch.startswith("origin/"):
        return base_branch
    return f"origin/{_base_branch_name(base_branch)}"

def _base_branch_name(base_branch: str) -> str:
    """Return a PR base branch name without the remote prefix.

    ``origin/main`` and ``github/main`` both name the canonical ``main`` —
    the dispatch fetch lands every base into ``refs/remotes/origin/<name>``
    regardless of which remote served it (#7522).
    """
    stripped = base_branch.removeprefix("origin/")
    return stripped.removeprefix("github/")

def _require_ukrainian_model_family(args: argparse.Namespace, model: str | None, *, resolved: bool = False) -> None:
    """Fail closed for Ukrainian content using the declared language lane.

    An omitted model on an allowed seat waits for resolution. A resolved
    model that is still missing is a refusal.
    """
    from scripts.review.reviewer_resolver import resolve_family

    family = str(getattr(args, "research_task_family", None) or "").strip().casefold()
    content_task = family in {"data", "text", "word cards", "word-cards", "word_cards", "dataset", "reviews"}
    language_lane = getattr(args, "language_lane", None)
    if content_task and not language_lane:
        raise ValueError(
            "UKRAINIAN_MODEL_REFUSED: content task language is missing or unknown; use --language-lane"
        )
    if not (content_task or _dispatch_is_language_lane(args, model=model)):
        return
    if model is None and not resolved:
        agent = str(getattr(args, "agent", "") or "").strip().lower()
        if _UKRAINIAN_AGENT_FAMILIES.get(agent) in _UKRAINIAN_MODEL_FAMILIES:
            return
    if not model or resolve_family(model) not in _UKRAINIAN_MODEL_FAMILIES:
        raise ValueError(
            "UKRAINIAN_MODEL_REFUSED: Ukrainian jobs require a known GPT, Gemini or Claude model"
        )

def _dispatch_review_changed_paths(args: argparse.Namespace) -> tuple[str, ...]:
    """Resolve a review's exact scope before route selection, pinning branch heads.

    Branch refs use the existing remote-tracking objects; a missing object
    refuses and must be refreshed before retrying. PR resolution uses its
    actual base. Attempt records supply their frozen target.changed_paths.
    """
    from scripts.review.security_paths import git_changed_paths
    from scripts.review.target_resolution import (
        TargetResolutionError,
        resolve_branch_target,
        resolve_pr_target,
        resolve_review_repository,
    )

    attempt = getattr(args, "review_attempt", None)
    paths: tuple[str, ...] | None = None
    if attempt:
        import yaml

        try:
            record = yaml.safe_load(Path(attempt).read_bytes())
        except (OSError, ValueError, yaml.YAMLError) as exc:
            raise TargetResolutionError("review attempt target unreadable") from exc
        target_record = record.get("target") if isinstance(record, dict) else None
        changed = target_record.get("changed_paths") if isinstance(target_record, dict) else None
        if not isinstance(changed, list) or not all(isinstance(path, str) and path for path in changed):
            raise TargetResolutionError("review attempt target.changed_paths missing or invalid")
        paths = tuple(changed)

    branch = getattr(args, "branch", None)
    pr = getattr(args, "pr", None)
    pinned = getattr(args, "pinned_head", None)
    if pinned and not (branch or pr):
        raise TargetResolutionError("--pinned-head requires --branch or --pr")
    repo_key = getattr(args, "repo", None)
    anchor = _REPO_ROOT if repo_key else _local_repo_root
    if pr is not None:
        resolution_mode, resolution_branch, resolution_base = "pr", None, None
    elif branch:
        resolution_mode = "branch"
        resolution_branch = pinned or _origin_base_ref(branch)
        resolution_base = _origin_base_ref(getattr(args, "base", None) or "main")
    else:
        resolution_mode, resolution_branch, resolution_base = None, None, None
    repo_root = resolve_review_repository(
        anchor,
        repo_key,
        mode=resolution_mode,
        branch=resolution_branch,
        base=resolution_base,
    )
    args._review_repo_root = repo_root
    if pr is not None:
        target = resolve_pr_target(repo_root, int(pr))
        if pinned and pinned.lower() != target.head_sha:
            raise TargetResolutionError("pinned head differs from PR head")
        args._review_admission_head = target.head_sha
    elif branch:
        if pinned and not re.fullmatch(r"[0-9a-fA-F]{40}", pinned):
            raise TargetResolutionError("pinned head must be a full commit SHA")
        target = resolve_branch_target(repo_root, resolution_branch, resolution_base)
        args.pinned_head = target.head_sha
    elif paths is not None:
        return paths
    else:
        raise TargetResolutionError("review target required: supply --branch, --pr or a resolved --review-attempt")
    literal = git_changed_paths(repo_root, target.base_sha, target.head_sha)
    # The frozen endpoints the complete-authorship facts are read from (#9739).
    args._review_target = target
    return tuple(dict.fromkeys((*literal, *(paths or ()))))

def _dispatch_review_facts(args: argparse.Namespace, owned_paths: Sequence[str]) -> Any:
    """Complete authorship and scope of the review target for a trusted code review (#9739).

    A review with a risk reads complete branch facts, including verified app
    bots that have no author model; legacy reviews keep intrinsic eligibility.
    Runs after :func:`_dispatch_review_changed_paths` pinned the
    target. Returns None without a branch or PR target.
    """
    from scripts.review.record_cf_verdict import admitted_unknown_history, collect_branch_review_facts

    target = getattr(args, "_review_target", None)
    if target is None or not (
        (getattr(args, "review_mode", None) or "cross_family") == "red_team" or getattr(args, "risk", None)
    ):
        return None
    repo_root = getattr(args, "_review_repo_root", _local_repo_root)
    repository = _origin_github_repo(repo_root) or ""
    unknown_history = ()
    if (getattr(args, "review_mode", None) or "cross_family") == "red_team":
        branch = getattr(args, "branch", None)
        if not branch and getattr(args, "pr", None):
            from scripts.review.record_cf_verdict import FACTS_TARGET_UNKNOWN, BranchFactsError, RecordError, _run_json

            try:
                pr = _run_json(
                    ["gh", "pr", "view", str(args.pr), "--repo", repository, "--json", "headRefName,headRefOid,isCrossRepository"]
                )
            except RecordError as exc:
                raise BranchFactsError(FACTS_TARGET_UNKNOWN, str(exc)) from exc
            if (
                not isinstance(pr, dict)
                or pr.get("isCrossRepository") is not False
                or not isinstance(pr.get("headRefName"), str)
                or not pr["headRefName"]
                or not isinstance(pr.get("headRefOid"), str)
                or not re.fullmatch(r"[0-9a-fA-F]{40}", pr["headRefOid"])
                or pr["headRefOid"] == "0" * 40
            ):
                raise BranchFactsError(FACTS_TARGET_UNKNOWN, "PR head moved or branch unavailable")
            branch = pr["headRefName"]
            from scripts.review.target_resolution import TargetResolutionError, live_canonical_branch_head

            try:
                live_head = live_canonical_branch_head(repo_root, branch, repository=repository)
            except TargetResolutionError as exc:
                raise BranchFactsError(FACTS_TARGET_UNKNOWN, str(exc)) from exc
            if live_head != target.head_sha:
                raise BranchFactsError(FACTS_TARGET_UNKNOWN, "PR head moved or branch unavailable")
        if branch:
            unknown_history = admitted_unknown_history(
                repository=repository,
                branch=branch,
                head_sha=target.head_sha,
                task_root=store.tasks_dir(),
                repo_root=repo_root,
            )
    facts = collect_branch_review_facts(
        repository=repository,
        repo_root=repo_root,
        base_tip_sha=target.base_sha,
        head_sha=target.head_sha,
        task_root=store.tasks_dir(),
        owned_paths=owned_paths,
        subject_seats=tuple(getattr(args, "subject_seat", None) or ()),
        subject_families=tuple(getattr(args, "subject_family", None) or ()),
        unknown_history=unknown_history,
    )
    # An empty target without a declared author supplies no trusted authorship.
    if (
        (getattr(args, "review_mode", None) or "cross_family") != "red_team"
        and not getattr(args, "review_author_model", None)
        and not facts.existing_families
    ):
        return None
    return facts


def admit(args, prompt: bytes, agent: str) -> dict:
    """Validate before provisioning or spending the pair (delegate:14799)."""
    from scripts.agent_runtime.review_mcp import SUPPORTED_HARNESSES, check_review_tool_requirements
    from scripts.agent_runtime.target_admission import ReviewAdmissionRefused, resolve_and_admit
    from scripts.fleet.claude_account_lane import resolve_route_account
    from scripts.review.target_resolution import TargetResolutionError, repository_target_error

    account = resolve_route_account(args.claude_account, strict=agent == "claude")

    def collect_review_paths():
        try:
            return _dispatch_review_changed_paths(args)
        except (TargetResolutionError, OSError, subprocess.TimeoutExpired) as exc:
            error = repository_target_error(args.repo, exc)
            raise ReviewAdmissionRefused(f"REVIEW_TARGET_UNRESOLVED: {error}") from exc

    def collect_review_facts():
        from scripts.review.record_cf_verdict import BranchFactsError

        try:
            facts = _dispatch_review_facts(args, tuple(args.owned_path))
            if args.review_mode == "red_team" and facts is not None:
                args._red_team_branch_facts = {**facts.receipt(), "author_task_ids": sorted(facts.author_task_ids)}
            return facts
        except (BranchFactsError, OSError, subprocess.TimeoutExpired) as exc:
            raise ReviewAdmissionRefused(f"REVIEW_TARGET_UNRESOLVED: {exc}") from exc

    def initial_snapshot():
        from scripts.fleet.claude_account_lane import select_account
        from scripts.fleet.credit_lane import read_routing_budget

        snapshot = read_routing_budget()
        if snapshot is None:
            raise ReviewAdmissionRefused("RED_TEAM_REFUSED: routing state unavailable")
        return select_account(snapshot, account=account)[0]

    code_review = (args.review_profile or "code") in {"code", "infra"}
    try:
        _require_ukrainian_model_family(args, args.model)
        (target,) = resolve_and_admit(
            (agent,), mode=args.mode, model=args.model, review_dispatch=True, review_attempt=bool(args.review_attempt),
            review_profile=args.review_profile or "code", review_risk=args.risk,
            review_author_model=args.review_author_model, review_owned_paths=tuple(args.owned_path),
            review_subject_seats=frozenset(args.subject_seat), review_subject_families=frozenset(args.subject_family),
            review_changed_paths=collect_review_paths if code_review else (),
            review_facts=collect_review_facts if code_review else None,
            review_mode=args.review_mode or "cross_family", review_task_id=args.task_id,
            review_initial_snapshot=initial_snapshot if args.review_mode == "red_team" else None,
            claude_account=account, review=True,
        )
        if (target.recipient, target.model) != (agent, args.model):
            raise ReviewAdmissionRefused("REVIEW_ROUTE_REFUSED: v2 requires the admitted seat and model")
        _require_ukrainian_model_family(args, target.model, resolved=True)
        if args.review_mode == "red_team" and (target := getattr(args, "_review_target", None)) is not None:
            from scripts.review.record_cf_verdict import RecordError, require_no_branch_outside_rejection

            try:
                require_no_branch_outside_rejection(
                    _origin_github_repo(args._review_repo_root) or "", args.branch, target.head_sha,
                    pr_number=args.pr, task_root=store.tasks_dir(),
                )
            except RecordError as exc:
                raise ReviewAdmissionRefused(str(exc)) from exc
    except ReviewAdmissionRefused as exc:
        raise ValueError(str(exc)) from None
    admitted = {}
    if head := getattr(args, "_review_admission_head", None):
        args.pinned_head = head
    if facts := getattr(args, "_red_team_branch_facts", None):
        admitted["review_branch_facts"] = facts
    if agent == "claude":
        admitted.update(claude_account=account.label, claude_account_source=account.source)
    if not args.review_attempt:
        return admitted
    access = args.review_access or "isolated"
    if access == "full" and not args.full_checkout:
        raise ValueError("full_review_requires_full_checkout: use --full-checkout")
    if args.output_schema:
        raise ValueError("attempt_output_schema_unsupported")
    if agent not in SUPPORTED_HARNESSES:
        raise ValueError(f"review attempt refused for {agent}: unsupported harness {agent!r} (#8517)")
    args.review_attempt = str(Path(args.review_attempt).resolve())
    check_review_tool_requirements(prompt.decode(), access)
    refusal, contract = _review_attempt_prompt_admission(args, prompt.decode(), args.review_id, args.attempt_id)
    if refusal:
        raise ValueError(refusal)
    root = worktree_claims.required_review_input_root(contract)
    _refuse_review_scratch_in_worktree()
    admitted.update(review_contract=contract, review_input_root=root,
                    review_input_paths=[str(p) for p in _review_attempt_input_paths(args.review_attempt)])
    return admitted


@contextlib.contextmanager
def prepare(spec, record, admitted):
    """Hold inputs until worker.start persists their claims (delegate:16129)."""
    from scripts.agent_runtime.attempt_boundary import verify_full_review_tree
    from scripts.agent_runtime.review_mcp import prepare_review_attempt, review_attempt_tool_config
    from scripts.review.isolation import ReviewIsolationError

    try:
        with contextlib.ExitStack() as locks:
            locks.enter_context(worktree_lock(spec.worktree))
            if not spec.worktree.is_dir():
                raise ValueError("review worktree disappeared while dispatch waited for its lock")
            _lock_review_input_root(admitted["review_contract"], locks, locked_worktree=spec.worktree,
                                    inputs=[Path(p) for p in admitted["review_input_paths"]])
            binding = record["review_attempt"]
            manifest = Path(spec.options["review_attempt"])
            if store.digest(manifest.read_bytes()) != binding["manifest_sha256"]:
                raise ValueError("attempt_manifest_hash_mismatch")
            if record["review_access"] == "full":
                verify_full_review_tree(manifest, spec.worktree)
            plan = prepare_review_attempt(
                binding["review_id"], binding["attempt_id"], manifest, spec.agent,
                review_contract=admitted["review_contract"], review_access=record["review_access"],
                checkout_root=spec.worktree,
            )
            config = review_attempt_tool_config(
                plan, manifest_path=manifest, input_root=admitted["review_input_root"], cwd=spec.worktree,
                task_id=spec.task_id, model=spec.model, effort=spec.effort, review_access=record["review_access"],
                review_profile=record.get("review_profile") or "code",
            )
            spec.options["review_tool_config"] = dict(config)
            if label := admitted.get("claude_account") or spec.claude_account:
                from scripts.agent_runtime.attempt_boundary import DEFAULT_CLAUDE_ACCOUNT, load_claude_account_binding

                spec.options["review_tool_config"]["claude_account"] = label
                if label != DEFAULT_CLAUDE_ACCOUNT:
                    account_binding = load_claude_account_binding(label)
                    spec.options["review_tool_config"]["review_claude_config_dir"] = str(account_binding.config_dir)
            record.update(admitted, review_ledger_path=str(plan.ledger_path))
            _mark_review_attempt_worktree(spec.worktree, spec.task_id)
            yield locks.close
    except (ReviewIsolationError, FileExistsError) as exc:
        raise ValueError(str(exc)) from None


class Execution:
    """Own the boundary until provider parsing and evidence extraction finish."""

    def __init__(self, spec, record, env):
        from scripts.agent_runtime.attempt_boundary import prepare_attempt_boundary

        self.boundary = None
        self.spec = spec
        self.record = record
        self.cli_digest = None
        self.cli_version = "unknown"
        config = spec.options.get("review_tool_config")
        if record.get("review_attempt"):
            from scripts.review.isolation import ReviewIsolationError
            from scripts.review.runtime_identity import boundary_refusal

            try:
                if config and spec.agent == "claude" and config.get("review_claude_config_dir"):
                    env["CLAUDE_CONFIG_DIR"] = config["review_claude_config_dir"]
                if not config:
                    raise ReviewIsolationError("attempt_boundary_inputs_missing")
                if store.digest(spec.prompt_file.read_bytes()) != record["prompt_sha256"]:
                    raise ReviewIsolationError("review_prompt_changed")
                if store.digest(Path(config["review_manifest"]).read_bytes()) != record["review_attempt"]["manifest_sha256"]:
                    raise ReviewIsolationError("attempt_manifest_hash_mismatch")
                self.boundary = prepare_attempt_boundary(spec.agent, spec.mode, None, config, environ=env)
                spec.options["review_tool_config"] = self.boundary.tool_config
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
                raise ValueError(boundary_refusal(exc, stage="prepare")) from exc

    def wrap(self, invocation):
        from dataclasses import replace

        try:
            if self.spec.agent == "agy":
                import shutil

                binary = Path(shutil.which(invocation.argv[0]) or invocation.argv[0]).resolve(strict=True)
                self.cli_digest = store.digest(binary.read_bytes())
                command, env = [str(binary), "--version"], invocation.env
                if self.boundary:
                    command, env = self.boundary.wrap(command, env)
                version = subprocess.run(command, env=env, capture_output=True, text=True, timeout=5, check=False)
                if version.returncode == 0:
                    self.cli_version = version.stdout.strip()
            if not self.boundary:
                return invocation
            self.boundary.verify_seat(invocation.argv, invocation.env)
            argv, env = self.boundary.wrap(invocation.argv, invocation.env)
            return replace(invocation, argv=argv, env=env)
        except (OSError, ValueError, RuntimeError) as exc:
            if not self.boundary:
                raise
            from scripts.review.runtime_identity import boundary_refusal

            raise ValueError(boundary_refusal(exc, stage="wrap")) from exc

    @property
    def cwd(self):
        return self.boundary.workspace if self.boundary else self.spec.worktree

    def evidence(self, stdout: str):
        """Runtime observations only; no model prose can grant identity or Sources."""
        from scripts.common.jsonl import jsonl_lines

        events, complete = [], True
        for line in jsonl_lines(stdout):
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    events.append(event)
                else:
                    complete = False
            except ValueError:
                complete = False
        calls = []
        for event in events:
            message = event.get("message")
            content = message.get("content", []) if isinstance(message, dict) else []
            calls.extend(block.get("name") for block in content if isinstance(block, dict)
                         and block.get("type") == "tool_use")
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "mcp_tool_call" and event.get("type") == "item.completed":
                calls.append("mcp__" + str(item.get("server")) + "__" + str(item.get("tool")))
        import re

        count = sum(bool(re.fullmatch(r"(?:mcp__sources__|mcp_sources_)[A-Za-z][A-Za-z0-9_]*", name))
                    for name in calls if isinstance(name, str))
        if not complete or any(not isinstance(name, str) or not name.strip() for name in calls):
            count = None
        if self.spec.agent == "agy" and not self.boundary:
            from scripts.agent_runtime.adapters.agy import _invocation_transcript, _parse_transcript_tool_calls

            plan = self.spec.options["review_plan"]
            if _invocation_transcript(plan) is None:
                count = None
            else:
                runtime_calls = _parse_transcript_tool_calls(plan)
                count = sum(bool(re.fullmatch(r"(?:mcp__sources__|mcp_sources_)[A-Za-z][A-Za-z0-9_]*", call["name"]))
                            for call in runtime_calls)
        if self.record.get("review_attempt"):
            from scripts.review.receipts.ledger import records

            rows = records(Path(self.record["review_ledger_path"]))
            binding = self.record["review_attempt"]
            if any(row.get("review_id") != binding["review_id"] or row.get("attempt_id") != binding["attempt_id"]
                   or row.get("manifest_sha256") != binding["manifest_sha256"] for row in rows):
                raise ValueError("attempt_identity_mismatch")
            count = len(rows)
        self.record["sources_mcp_call_count"] = count
        if self.spec.agent == "agy":
            from scripts.agent_runtime.adapters.agy import agy_model_state
            from scripts.review.runtime_identity import observe_agy_identity

            identity = observe_agy_identity(stdout=stdout, plan=self.spec.options["review_plan"],
                task_id=self.spec.task_id, run_nonce=self.record["run_nonce"], invocation_id=self.record["run_nonce"],
                cli_sha256=self.cli_digest, cli_version=self.cli_version)
            state = agy_model_state(agent="agy", model=self.spec.model, identity=identity,
                                    task_id=self.spec.task_id, run_nonce=self.record["run_nonce"])
            self.record.update(state)
            if state and not state["identity_matches_request"]:
                raise ValueError("agy_model_identity_unverified")
        else:
            models = {event.get("model") for event in events if event.get("type") == "system"
                      and event.get("subtype") == "init" and isinstance(event.get("model"), str)}
            if self.spec.agent == "claude":
                from scripts.review.model_catalog import runtime_model_matches_requested

                known = len(models) == 1
                model = next(iter(models)) if known else "unknown"
                self.record.update(resolved_model=model, resolved_model_known=known,
                                   resolved_model_source="provider-init" if known else "unattested-harness")
                if known and not runtime_model_matches_requested(self.spec.model, model):
                    raise ValueError("review_model_mismatch")
        from scripts.review.language_lane import is_ukrainian_review

        if is_ukrainian_review(self.record):
            from scripts.review.record_cf_verdict import _require_sources_mcp_calls

            _require_sources_mcp_calls(self.record)

    def cleanup(self):
        if self.boundary:
            self.boundary.cleanup()
        elif (self.spec.agent == "codex" and (plan := self.spec.options.get("review_plan"))
                and plan.output_file is not None):
            plan.output_file.unlink(missing_ok=True)


def build_invocation(spec, env, adapter):
    """Use retained adapter flags rather than approximating the tool contract."""
    from scripts.dispatcher.types import Invocation

    config = dict(spec.options.get("review_tool_config") or {"reviewer_tools": True})
    if spec.options.get("output_schema_path") is not None:
        config.update({key: spec.options[key] for key in ("output_schema_path", "output_schema_sha256")
                       if key in spec.options})
    if spec.agent == "claude":
        config["claude_account"] = spec.claude_account or "a"
    boundary = config.get("review_attempt_boundary")
    cwd = boundary.workspace if boundary else spec.worktree
    plan = adapter.build_invocation(prompt=spec.prompt_file.read_text(), mode=spec.mode, cwd=cwd, model=spec.model,
                                   effort=spec.effort, task_id=spec.task_id, session_id=None, tool_config=config)
    spec.options["review_plan"] = plan
    effective_env = {**env, **plan.env_overrides}
    for name in plan.env_unsets:
        effective_env.pop(name, None)
    # AttemptBoundary owns authentication and HOME; provider overrides carry
    # only the adapter's scoped runtime values, never the inherited HOME.
    if boundary:
        effective_env = dict(plan.env_overrides)
    stdin = plan.stdin_payload.encode() if isinstance(plan.stdin_payload, str) else plan.stdin_payload
    return Invocation(plan.cmd, stdin, effective_env, plan.output_file)
