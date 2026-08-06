"""One-process SessionStart gate.

session-setup.sh historically spawned ~16 short-lived python interpreters in
series (session-record update, venv version probe, primary-on-main assert,
thread-lease claim, rollover detect, plus one `python -c` per JSON field it
needed back). Interpreter + import cost dominated the measured ~950 ms
cold-start (2026-08-06 review, PR #6413). This gate runs every one of those
phases inside a single interpreter and returns one JSON document.

Verdict honesty contract (issue #6411): a phase that CRASHES reports
``status: "crashed"`` — the shell maps that to "could not determine", never to
a business verdict such as a lease conflict. Only a phase that actually ran to
a decision may return a decision.

Phase statuses:
  ok       – ran, no problem
  issue    – ran, produced an ISSUES line (``verdict``)
  stop     – ran, produced a session-stopping HANDOFF context (``context``)
  crashed  – the helper itself failed (``error``); state is UNKNOWN
  skipped  – not applicable for this session (``reason``)

The gate always exits 0 when it produced JSON; a non-zero exit means the gate
itself could not run and the caller must treat every phase as UNKNOWN.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import platform
import sys
import traceback
from pathlib import Path
from typing import Any


def _crash(exc: BaseException) -> dict[str, Any]:
    return {
        "status": "crashed",
        "error": f"{type(exc).__name__}: {exc}",
        "trace_tail": traceback.format_exc(limit=3).splitlines()[-3:],
    }


def _run_cli_inprocess(main_fn: Any, argv: list[str]) -> tuple[int, str, str]:
    """Run an argparse-style ``main(argv)`` in-process, capturing output.

    SystemExit (argparse errors, sys.exit paths) is converted to a return code
    so one phase's exit can never terminate the gate.
    """
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = main_fn(argv)
            code = int(rc) if rc is not None else 0
        except SystemExit as exc:  # argparse error paths
            code = int(exc.code) if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return code, out.getvalue(), err.getvalue()


# --- phases -------------------------------------------------------------------


def phase_session_record(args: argparse.Namespace) -> dict[str, Any]:
    # The official session record is keyed by the hook-supplied session id
    # (context-monitor.sh reads it back by that same id, not by the durable
    # thread-lease/rollover identity, which may differ — CF review on #6414
    # finding 1). Fall back to --session-id only when the caller did not
    # supply a distinct --record-session-id (e.g. direct/test invocations).
    record_session_id = args.record_session_id or args.session_id
    if not record_session_id:
        return {"status": "skipped", "reason": "no session id"}
    try:
        from scripts.lib import session_record
    except Exception as exc:
        return _crash(exc)
    argv = [
        "session_record.py",
        "--state-root",
        args.repo_root,
        "update",
        "--session-id",
        record_session_id,
        "--provenance",
        "SessionStart",
        "--append-env",
    ]
    for flag, value in (
        ("--transcript-path", args.transcript_path),
        ("--source", args.source),
        ("--observed-model", args.observed_model),
        ("--agent-type", args.agent_type),
        ("--profile-id", args.profile_id),
    ):
        if value:
            argv += [flag, value]
    try:
        old_argv = sys.argv
        sys.argv = argv
        try:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    rc = session_record.main()
                except SystemExit as exc:
                    rc = int(exc.code) if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        finally:
            sys.argv = old_argv
    except Exception as exc:
        return _crash(exc)
    if rc != 0:
        return {
            "status": "issue",
            "verdict": "SESSION RECORD FAILED: official SessionStart identity could not be persisted.",
        }
    return {"status": "ok"}


def phase_python_version(args: argparse.Namespace) -> dict[str, Any]:
    """The gate runs ON the canonical venv python — compare in-process."""
    pin_file = Path(args.repo_root) / ".python-version"
    try:
        if not pin_file.is_file():
            return {
                "status": "issue",
                "verdict": f"PYTHON VERSION PIN MISSING: expected .python-version at {pin_file}",
            }
        expected = pin_file.read_text(encoding="utf-8").splitlines()[0].strip()
        actual = platform.python_version()
    except Exception as exc:
        return _crash(exc)
    if not expected or actual != expected:
        return {
            "status": "issue",
            "verdict": f"VENV WRONG PYTHON: Expected Python {expected or '<missing pin>'}, got Python {actual}",
        }
    return {"status": "ok"}


def phase_primary_main(args: argparse.Namespace) -> dict[str, Any]:
    try:
        from scripts.guardrails import assert_primary_on_main
    except Exception as exc:
        return _crash(exc)
    try:
        rc, _out, _err = _run_cli_inprocess(
            assert_primary_on_main.main, ["--cwd", args.project_dir, "--quiet"]
        )
    except Exception as exc:
        return _crash(exc)
    if rc != 0:
        return {
            "status": "issue",
            "verdict": (
                "PRIMARY HEAD is detached or not on main (#4857). Inspect it, then run the "
                "explicit doctor if appropriate: .venv/bin/python "
                "scripts/guardrails/assert_primary_on_main.py --heal."
            ),
        }
    return {"status": "ok"}


def _import_thread_handoff() -> Any:
    from scripts.orchestration import thread_handoff

    return thread_handoff


def phase_thread_lease(args: argparse.Namespace) -> dict[str, Any]:
    if not args.claim_lease:
        return {"status": "skipped", "reason": "not a claude lane"}
    if not args.session_id:
        return {
            "status": "stop",
            "context": (
                "ERROR: Cannot acquire durable thread lease: SessionStart did not provide a "
                "current thread id. Stop; do not drive this queue."
            ),
        }
    try:
        thread_handoff = _import_thread_handoff()
        rc, out, err = _run_cli_inprocess(
            thread_handoff.main,
            [
                "--repo-root",
                args.repo_root,
                "claim-thread-lease",
                "--agent",
                args.agent,
                "--current-thread-id",
                args.session_id,
            ],
        )
    except Exception as exc:
        crash = _crash(exc)
        crash["context"] = (
            "ERROR: LEASE CLAIM HELPER CRASHED — stop; lease state UNKNOWN; do NOT "
            f"force-release.\nError: {crash['error']}"
        )
        return crash
    if rc != 0:
        # The claim ran to a real refusal. Distinguish the exact structured
        # conflict status from every other outcome — a malformed/empty payload
        # OR a structured-but-non-conflict status such as {"status": "error"}
        # is a HELPER FAILURE, not a business conflict (issue #6411 / CF review
        # on #6414 findings 2-3): only status == "conflict" may be labeled
        # DURABLE THREAD LEASE CONFLICT.
        try:
            payload = json.loads(out or "{}")
        except ValueError:
            payload = None
        if isinstance(payload, dict) and payload.get("status") == "conflict":
            return {
                "status": "stop",
                "context": (
                    "ERROR: DURABLE THREAD LEASE CONFLICT — stop; do not cold-start or drive "
                    f"this queue.\nOutput:\n{out.strip() or err.strip()}"
                ),
            }
        status_note = (
            f"status={payload.get('status')!r}" if isinstance(payload, dict) else "unstructured output"
        )
        return {
            "status": "crashed",
            "error": f"claim-thread-lease rc={rc} with {status_note}",
            "context": (
                "ERROR: LEASE CLAIM FAILED WITHOUT A STRUCTURED CONFLICT VERDICT — stop; lease "
                f"state UNKNOWN; do NOT force-release.\nOutput:\n{(out or err).strip()}"
            ),
        }
    # rc == 0 requires PROOF, not just a clean exit: valid JSON with the
    # explicit acquired status. A malformed/empty payload — or any status
    # other than "acquired" — must not fall through to an unconditional ok
    # (CF review on #6414 finding 2).
    try:
        payload = json.loads(out or "{}")
    except ValueError:
        payload = None
    if not isinstance(payload, dict) or payload.get("status") != "acquired":
        status_note = f"status={payload.get('status')!r}" if isinstance(payload, dict) else "unstructured output"
        return {
            "status": "crashed",
            "error": f"claim-thread-lease rc=0 without an acquired verdict ({status_note})",
            "context": (
                "ERROR: LEASE CLAIM RETURNED SUCCESS WITHOUT A STRUCTURED ACQUIRED VERDICT — "
                f"stop; lease state UNKNOWN; do NOT force-release.\nOutput:\n{(out or err).strip()}"
            ),
        }
    generation = str(payload.get("generation") or "")
    banner_parts: list[str] = []
    replaced = payload.get("replaced_owner_thread_id")
    if replaced:
        banner_parts.append(
            f"THREAD LEASE TAKEOVER: this session (generation {payload.get('generation')}) "
            f"replaced owner {replaced} -- reason: {payload.get('takeover_reason', 'unknown')}."
        )
    corrupt = payload.get("recovered_from_corrupt_lease")
    if corrupt:
        banner_parts.append(
            f"THREAD LEASE HEALED: on-disk lease was corrupt and was reset -- {corrupt}."
        )
    return {"status": "ok", "generation": generation, "takeover_banner": "\n".join(banner_parts)}


def phase_rollover_detect(args: argparse.Namespace) -> dict[str, Any]:
    if not args.detect:
        return {"status": "skipped", "reason": "native task continuity"}
    family_args: list[str] = []
    if args.task_family:
        family_args = ["--task-family", args.task_family]
    base = [
        "--repo-root",
        args.repo_root,
        "detect",
        "--agent",
        args.agent,
        "--current-thread-id",
        args.session_id or "",
        *family_args,
    ]
    try:
        thread_handoff = _import_thread_handoff()
        rc, out, err = _run_cli_inprocess(thread_handoff.main, [*base, "--format", "json"])
    except Exception as exc:
        return _crash(exc)

    def _formatted() -> tuple[int, str, str]:
        return _run_cli_inprocess(thread_handoff.main, [*base, "--format", "session-start"])

    if rc != 0:
        error_code = ""
        with contextlib.suppress(ValueError):
            error_code = str(json.loads(out or "{}").get("error_code") or "")
        if error_code == "MULTIPLE_LIVE_PENDING_ROLLOVERS":
            try:
                frc, fout, _ferr = _formatted()
            except Exception as exc:
                return _crash(exc)
            if frc == 0:
                return {"status": "stop", "context": fout}
            return {
                "status": "stop",
                "context": (
                    "ERROR: MULTIPLE live pending rollovers — do not cold-start; bind one exact "
                    f"candidate.\nFormatting lookup failed:\n{fout or 'no output'}\n"
                    f"Detection output:\n{out}"
                ),
            }
        return {
            "status": "crashed",
            "error": f"detect rc={rc}",
            "context": f"ERROR: thread_handoff.py detect failed. Stop.\nOutput:\n{(out or err).strip()}",
        }
    try:
        detect_status = str(json.loads(out or "{}").get("status") or "")
    except ValueError:
        return {
            "status": "crashed",
            "error": "detect output was not valid JSON",
            "context": f"ERROR: thread_handoff.py detect output could not be parsed. Stop.\nOutput:\n{out}",
        }
    if detect_status in {"ambiguous", "pending_start", "resumed"}:
        try:
            frc, fout, ferr = _formatted()
        except Exception as exc:
            return _crash(exc)
        if frc != 0:
            return {
                "status": "crashed",
                "error": f"detect --format session-start rc={frc}",
                "context": (
                    f"ERROR: thread_handoff.py detect failed. Stop.\nOutput:\n{(fout or ferr).strip()}"
                ),
            }
        return {"status": "stop", "context": fout, "detect_status": detect_status}
    if detect_status == "none":
        return {"status": "ok", "detect_status": "none"}
    return {
        "status": "stop",
        "context": f"ERROR: Unexpected detect status: {detect_status}",
        "detect_status": detect_status,
    }


# --- entrypoint ---------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="canonical checkout (state root)")
    parser.add_argument("--project-dir", required=True, help="session checkout (may be a worktree)")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--session-id", default="")
    parser.add_argument(
        "--record-session-id",
        default="",
        help=(
            "Official hook session id for the session-record phase. Distinct from "
            "--session-id (the durable thread-lease/rollover identity) so each "
            "consumer keys its own store by the right id; falls back to "
            "--session-id when omitted."
        ),
    )
    parser.add_argument("--transcript-path", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--observed-model", default="")
    parser.add_argument("--agent-type", default="")
    parser.add_argument("--profile-id", default="")
    parser.add_argument("--task-family", default="")
    parser.add_argument("--claim-lease", action="store_true")
    parser.add_argument("--detect", action="store_true")
    args = parser.parse_args(argv)

    # Imports must resolve against the session checkout, matching the old
    # per-script invocation semantics ($PROJECT_DIR scripts, canonical venv).
    project_dir = str(Path(args.project_dir).resolve())
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    result: dict[str, Any] = {
        "session_record": phase_session_record(args),
        "python_version": phase_python_version(args),
        "primary_main": phase_primary_main(args),
        "thread_lease": phase_thread_lease(args),
    }
    # Preserve the historical ordering guarantee: a lease stop is authoritative
    # and detect must not run (never replace a lease verdict with detect output).
    lease_status = result["thread_lease"]["status"]
    if lease_status in {"stop", "crashed"}:
        result["rollover_detect"] = {"status": "skipped", "reason": "lease verdict is authoritative"}
    else:
        result["rollover_detect"] = phase_rollover_detect(args)

    json.dump(result, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
