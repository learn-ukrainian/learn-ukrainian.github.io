"""Execute one bound formal review attempt (#12114).

Admission (``admit``) runs in the dispatch command before anything is created: the
prompt must be the exact render of the attempt's manifest with this dispatch's ids
(``check_review_contract`` and ``check_prompt``), its Sources tool requirements must be
granted, and every pinned input must equal the dispatch commit's bytes, so a refused
tree leaves the attempt id unspent.

Execution (``run``) runs in the task's supervisor once its record exists: the actual
checkout is verified again, the attempt id is claimed (the exclusive empty ledger),
the per-attempt Sources server, sidecar and scoped home are prepared on that claim,
and the seat runs through the agent runtime's attempt boundary
(``agent_runtime.runner.invoke`` with ``review_attempt_tool_config``) with the
rendered prompt's exact bytes. The runtime owns the OS boundary, egress proxy and
Sources socket; there is no fallback to an ordinary launch. The recorder
(``scripts.review.record``) later binds the saved result to this record.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scripts.dispatcher import store


def admit(args: Any, prompt: bytes, binding: dict, repo: Path, sha: str) -> dict:
    """Refuse a bound launch whose prompt, tools or pinned inputs do not match; return its review contract."""
    from scripts.agent_runtime.review_mcp import check_review_contract, check_review_tool_requirements
    from scripts.orchestration.worktree_claims import required_review_input_root
    from scripts.review.prompts.check import check_prompt
    from scripts.review.render_contract import ReviewContractError

    access = args.review_access or "isolated"
    if access == "full" and not args.full_checkout:
        raise ValueError("review_attempt_full_checkout_required: full review access needs --full-checkout")
    if args.output_schema is not None:
        raise ValueError("attempt_output_schema_unsupported: a bound attempt returns its review document")
    if args.codex_account not in (None, "sub"):
        # The runtime boundary stages only the default Codex login; another account is refused, never substituted.
        raise ValueError(f"review_attempt_account_unsupported: codex account {args.codex_account!r}")
    if args.prompt_file in (None, "-"):
        raise ValueError("review_attempt_prompt_file_required: a bound attempt's prompt is a rendered --prompt-file")
    text = prompt.decode("utf-8")
    ids = dict(review_id=binding["review_id"], attempt_id=binding["attempt_id"])
    try:
        contract = check_review_contract(Path(args.prompt_file), text, **ids)
        checked = check_prompt(
            text,
            Path(args.review_attempt),
            repo_root=Path(required_review_input_root(contract)),
            prompts_dir=Path(contract["server_checkout"]) / "scripts/review/prompts",
            recorded_prompts_dir=Path(contract["render_checkout"]) / "scripts/review/prompts",
            files_read=contract["recorded_files_read"],
            template_sha256=contract["recorded_template_sha256"],
            recorded_templates=contract["recorded_templates"],
            review_access=access,
            **ids,
        )
    except ReviewContractError as exc:
        raise ValueError(str(exc)) from None
    if not checked.passed:
        raise ValueError("prompt_render_invalid: " + "; ".join(checked.errors))
    manifest = yaml.safe_load(Path(args.review_attempt).read_bytes())
    if manifest.get("kind") == "lexical" and (
        args.review_profile != "ukrainian" or not args.review_author_model or args.effort != "high"
    ):
        raise ValueError("lexical_review_identity_required: use Ukrainian profile, author model and high effort")
    check_review_tool_requirements(text, access)
    _check_pins_at_commit(repo, sha, Path(args.review_attempt))
    return contract


def _check_pins_at_commit(repo: Path, sha: str, manifest_path: Path) -> None:
    """Every manifest pin must hold the dispatch commit's bytes, before a worktree or record exists."""
    from scripts.build.fresh.manifest import pinned_entries

    for _, entry in pinned_entries(yaml.safe_load(manifest_path.read_bytes())):
        shown = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "blob", f"{sha}:{entry['path']}"],
            capture_output=True, timeout=60, check=False,
        )
        if shown.returncode or hashlib.sha256(shown.stdout).hexdigest() != entry["sha256"]:
            raise ValueError(f"full_review_tree_mismatch: {entry['path']} at {sha} is not the manifest's pinned input")


@dataclass
class Outcome:
    status: str
    error: str | None
    text: str | None
    sources_calls: int | None
    identity: dict
    trace: list = field(default_factory=list)


def run(spec: Any, record: dict, prompt: str, deadlines: tuple[float, int, int]) -> Outcome:
    """Claim, prepare and run the bound attempt of ``record``; never falls back to an unbounded launch."""
    # runner.py imports the top-level ``ai_llm`` package (``scripts/ai_llm``), and the supervisor runs as
    # ``python -m`` from the repository root, which does not put ``scripts/`` on ``sys.path``.
    scripts_dir = str(Path(__file__).resolve().parents[1])
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from scripts.agent_runtime import runner
    from scripts.agent_runtime.attempt_boundary import verify_full_review_tree
    from scripts.agent_runtime.errors import (
        AgentRuntimeError,
        AgentStalledError,
        AgentTimeoutError,
        RateLimitedError,
    )
    from scripts.agent_runtime.review_mcp import prepare_review_attempt, review_attempt_tool_config
    from scripts.review.isolation import ReviewIsolationError
    from scripts.review.receipts import ledger

    binding, access = record["review_attempt"], record.get("review_access") or "isolated"
    manifest = Path(record["options"]["review_attempt"])
    workspace = Path(record["worktree_path"])
    unknown = dict(resolved_model="unknown", resolved_model_known=False, resolved_model_source="unobserved")
    from scripts.review.language_lane import is_ukrainian_review

    ukrainian = is_ukrainian_review(record)
    if ukrainian:
        record.setdefault("claims_total", 0)
        record.setdefault("claims_unsupported", 0)
        record.setdefault("unknown_items", 0)
        record.setdefault("dropped_claims", [])
    try:
        if access == "full":
            verify_full_review_tree(manifest, workspace)
        store.check_review_attempt(binding, claim=True, owner=record["task_id"])
        plan = prepare_review_attempt(
            binding["review_id"], binding["attempt_id"], manifest, spec.agent,
            receipts_root=store.receipts_root(), review_contract=record.get("review_contract"),
            review_access=access, checkout_root=workspace, claimed=True,
        )
        if plan.manifest_sha256 != binding["manifest_sha256"]:
            raise ValueError("attempt_manifest_hash_mismatch: the manifest changed after admission")
        tool_config = review_attempt_tool_config(
            plan, manifest_path=manifest, input_root=record["review_contract"]["input_root"], cwd=workspace,
            task_id=record["task_id"], model=spec.model, effort=spec.effort, review_access=access,
            review_profile=record.get("review_profile") or "code",
            base_tool_config=_route(spec, record),
        )
    except (OSError, ValueError, ReviewIsolationError) as exc:
        return Outcome("failed", f"review_attempt_refused: {exc}"[:500], None, None, unknown)
    hard, silence, initial = deadlines
    try:
        result = runner.invoke(
            spec.agent, prompt, mode="read-only", cwd=workspace, model=spec.model, task_id=record["task_id"],
            tool_config=dict(tool_config), entrypoint="dispatch", hard_timeout=int(hard) if hard else 86400,
            stdout_silence_timeout=silence or None, initial_response_timeout=initial or None, effort=spec.effort,
            allow_runner_failover=False,
        )
    except (AgentTimeoutError, AgentStalledError) as exc:
        return Outcome("timeout", str(exc)[:500], None, _ledger_count(ledger, plan.ledger_path), unknown)
    except RateLimitedError as exc:
        return Outcome("rate_limited", str(exc)[:500], None, _ledger_count(ledger, plan.ledger_path), unknown)
    except AgentRuntimeError as exc:
        return Outcome("failed", str(exc)[:500], None, _ledger_count(ledger, plan.ledger_path), unknown)
    # Only an identity the runtime observed from the provider is attested; a requested model never is.
    known = result.identity_state == "observed"
    identity = dict(
        resolved_model=result.observed_model if known else "unknown",
        resolved_model_known=known,
        resolved_model_source=result.observed_model_source if known else "unobserved",
    )
    ok = result.ok and bool(result.response.strip())
    error = None if ok else (result.failure_code or result.stderr_excerpt or "provider returned no successful response")
    response_text = result.response if ok else None
    if ukrainian and ok and response_text:
        import yaml

        from scripts.review.review_contract import (
            _fenced,
            reply_has_item_judgments,
            validate_item_claims,
        )

        if reply_has_item_judgments(response_text):
            bodies = _fenced(response_text, "ukrainian-item-judgments")
            if len(bodies) == 1:
                try:
                    try:
                        payload = json.loads(bodies[0])
                    except Exception:
                        payload = yaml.safe_load(bodies[0])
                    if isinstance(payload, dict):
                        sanitized, val_res = validate_item_claims(
                            payload,
                            ledger_path=plan.ledger_path,
                            binding=binding,
                        )
                        record["claims_total"] = val_res.claims_total
                        record["claims_unsupported"] = val_res.claims_unsupported
                        record["unknown_items"] = val_res.unknown_items
                        record["dropped_claims"] = [dict(c) for c in val_res.dropped_claims]
                        clean_block = (
                            "```ukrainian-item-judgments\n"
                            + json.dumps(sanitized, indent=2, ensure_ascii=False)
                            + "\n```"
                        )
                        pattern = r"^```ukrainian-item-judgments[ \t]*\n.*?\n```[ \t]*$"
                        response_text = re.sub(
                            pattern,
                            lambda _: clean_block,
                            response_text,
                            count=1,
                            flags=re.M | re.S,
                        )
                except Exception:
                    pass
        else:
            yaml_bodies = _fenced(response_text, "yaml") or _fenced(response_text, "yml")
            fence_tag = "yaml" if _fenced(response_text, "yaml") else "yml"
            if len(yaml_bodies) == 1:
                try:
                    payload = yaml.safe_load(yaml_bodies[0])
                    if isinstance(payload, dict):
                        sanitized, val_res = validate_item_claims(
                            payload,
                            ledger_path=plan.ledger_path,
                            binding=binding,
                        )
                        record["claims_total"] = val_res.claims_total
                        record["claims_unsupported"] = val_res.claims_unsupported
                        record["unknown_items"] = val_res.unknown_items
                        record["dropped_claims"] = [dict(c) for c in val_res.dropped_claims]
                        clean_block = (
                            f"```{fence_tag}\n"
                            + yaml.safe_dump(sanitized, allow_unicode=True, sort_keys=False)
                            + "```"
                        )
                        pattern = rf"^```{fence_tag}[ \t]*\n.*?\n```(?:{fence_tag})?[ \t]*$"
                        response_text = re.sub(
                            pattern,
                            lambda _: clean_block,
                            response_text,
                            count=1,
                            flags=re.M | re.S,
                        )
                except Exception:
                    pass
            else:
                try:
                    payload = yaml.safe_load(response_text)
                    if isinstance(payload, dict):
                        sanitized, val_res = validate_item_claims(
                            payload,
                            ledger_path=plan.ledger_path,
                            binding=binding,
                        )
                        record["claims_total"] = val_res.claims_total
                        record["claims_unsupported"] = val_res.claims_unsupported
                        record["unknown_items"] = val_res.unknown_items
                        record["dropped_claims"] = [dict(c) for c in val_res.dropped_claims]
                        response_text = yaml.safe_dump(sanitized, allow_unicode=True, sort_keys=False)
                except Exception:
                    pass
    # Which tools the seat called with which arguments (no outputs): the evidence of its context reads.
    calls = getattr(result, "tool_calls", None) or ()
    trace = [_redacted(json.loads(json.dumps({key: call.get(key) for key in ("name", "arguments", "timestamp")},
                                             default=str)))
             for call in calls]
    return Outcome("done" if ok else "failed", error, response_text if ok else None,
                   _ledger_count(ledger, plan.ledger_path), identity, trace)


def _route(spec: Any, record: dict) -> dict:
    """The admitted credential route, carried into the runtime exactly as dispatch recorded it."""
    from scripts.agent_runtime.attempt_boundary import CLAUDE_ACCOUNT_KEY, resolve_claude_account_label
    from scripts.dispatcher import admission

    route: dict = {"run_nonce": record["run_nonce"]}
    if spec.agent == "claude":
        # The boundary authenticates as this label and verifies its binding again at use.
        route[CLAUDE_ACCOUNT_KEY] = resolve_claude_account_label(spec.claude_account)
        budget = admission.claude_budget(spec.claude_account, spec.options.get("max_budget_usd"))
        if budget is not None:
            route["max_budget_usd"] = budget
    return route


def _redacted(value: Any) -> Any:
    """A JSON value with every string redacted, mapping keys included, so that it stays valid JSON."""
    from scripts.secret_redactor import redact_text, redact_value

    if isinstance(value, dict):
        value = redact_value(value)  # also blanks the values of secret-named keys
        return {redact_text(key): _redacted(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redacted(item) for item in value]
    return redact_text(value) if isinstance(value, str) else value


def _ledger_count(ledger: Any, path: Path) -> int | None:
    """The attempt's Sources receipts, read from the ledger the outside server wrote."""
    try:
        return len(ledger.records(path))
    except (OSError, ValueError, ledger.LedgerError):
        return None
