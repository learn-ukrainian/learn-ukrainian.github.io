"""Opencode transport for ai_agent_bridge — the multi-provider router.

``opencode run`` is a ROUTER that fronts many providers/models, so "opencode"
is NOT itself a fleet member — you must name the model. Two bridge verbs ride
this transport:

- ``ask-opencode`` — generic escape hatch to ANY opencode-reachable model
  (e.g. ``openrouter/qwen/qwen3.7-max``) for one-off cross-model reviews.
- ``ask-pool`` — the first-class **poolside.ai** fleet member. Default model
  ``poolside/poolside/laguna-s-2.1`` (Laguna **S 2.1**, gen-2 strongest). Also
  ship gen-2 light ``laguna-xs-2.1`` and gen-1 fallback ``laguna-m.1`` (not
  "laguna-s2" / not M 2.x). Clean cross-family CODE + web-verify specialist.
  Rides opencode with ``--variant`` effort + NDJSON; browses via lightpanda MCP
  in ``~/.config/opencode/opencode.jsonc``. See ``ask_pool`` below.
- ``ask-glm`` — the first-class **Zhipu GLM** fleet member (model
  ``zai-coding-plan/glm-5.2``): strong code authoring + review (its top axis)
  and live web fact-checking, its own (China-lab) family. ⚠️ China-hosted →
  prompt data EGRESSES TO CHINA → LOCAL-ONLY; ``ask_glm`` refuses to run under
  CI as a backstop. See ``ask_glm`` below.

Invocation:
    ab ask-opencode <content> --task-id T --model openrouter/qwen/qwen3.7-max
    ab ask-pool     <content> --task-id T [--variant high|max|minimal] [--data FILE]
    ab ask-glm      <content> --task-id T [--data FILE]   # LOCAL-ONLY, no CI

Under the hood: opencode run --model PROVIDER/MODEL [--variant V]
    --format {default|json} [--file FILE --] "CONTENT"

For glm/pool (reasoning lanes), the bridge also injects
OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX (sourced from AB_* envs or
per-model defaults of 128K+) into the subprocess to raise the output
budget beyond the ~32k cap that produced step_finish reason=length.
See _get_max_output_tokens and GLM/POOL_DEFAULT_MAX_OUTPUT_TOKENS.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._ask_contract import (
    requested_effort,
    resolve_model_selection,
    response_provenance,
)
from ._ask_lifecycle import (
    ask_attachment,
    ask_sender_model,
    ask_target_model,
    fetch_ask_message,
    launch_background_ask,
    record_ask_failure,
    record_ask_reply,
    register_ask,
)
from ._config import REPO_ROOT
from ._messaging import acknowledge, send_message
from ._reply_sidecar import write_reply_sidecar
from ._review_safety import (
    ReviewSafetyError,
    assert_formal_review_ask_payload,
    warn_missing_review_target,
)

# Default was qwen3.7-max (EXPENSIVE) until 2026-07-05 — a silent money trap
# for every ask-opencode call without --model. Since 2026-07-07 (user order:
# "we will use the free gemma for some time"; OR balance is a deliberate ~$2
# buffer until things stabilize) the default is Gemma via Google AI Studio
# DIRECT — $0 (Gemma has no paid SKU on the Gemini API; opencode reports
# cost:0). The OR paid `-it` endpoint stays reachable via explicit --model.
OPENCODE_DEFAULT_MODEL = "google-ais/gemma-4-31b-it"
OPENCODE_DEFAULT_TIMEOUT_S = 900

# poolside.ai fleet member. Use the NATIVE poolside provider path — it browses
# via the lightpanda MCP; the ``openrouter/poolside/*`` path CANNOT browse.
# Runs on the poolside subscription ("free" lane) — watch weekly limits on
# parallel bursts.
#
# Laguna family (exact IDs — vendor spelling uses hyphen + minor "m.1"):
#   poolside/laguna-s-2.1   — gen-2 strongest (DEFAULT formal/volume pin)
#   poolside/laguna-xs-2.1  — gen-2 light/fast
#   poolside/laguna-m.1     — gen-1 prior (fallback only; not "m2")
# opencode route form is often poolside/poolside/<id>.
# If the local opencode catalog lags, override --model (e.g. opencode/laguna-s-2.1-free).
POOL_MODEL = "poolside/poolside/laguna-s-2.1"
POOL_MODEL_S = POOL_MODEL  # alias: Laguna S 2.1
POOL_MODEL_XS = "poolside/poolside/laguna-xs-2.1"
POOL_MODEL_M1_LEGACY = "poolside/poolside/laguna-m.1"
POOL_DEFAULT_VARIANT = "high"  # reasoning effort: minimal | high | max
POOL_DEFAULT_TIMEOUT_S = 1800  # browsing + high-effort reasoning runs long
POOL_VARIANTS = frozenset({"minimal", "high", "max"})
_EFFORT_TO_VARIANT = {
    "low": "minimal",
    "medium": "high",
    "high": "high",
    "xhigh": "max",
    "max": "max",
}

# Zhipu GLM fleet member (model glm-5.2), reached via the Z.AI Coding Plan
# provider under opencode (also reachable as openrouter/z-ai/glm-5.2). Strong
# code + review + browsing; a distinct (China-lab) family → valid cross-family
# reviewer.
#
# ⚠️ HARD DATA-GOVERNANCE CONSTRAINT: GLM is China-hosted (Zhipu/z.ai) → prompt
# data EGRESSES TO CHINA. LOCAL-ONLY — never call it from CI / automated
# pipelines or with sensitive data; prefer a Western-lab reviewer for
# top-stakes work. ``ask_glm`` refuses to run under CI as a runtime backstop.
GLM_MODEL = "zai-coding-plan/glm-5.2"
GLM_DEFAULT_TIMEOUT_S = 1800
# Env vars whose presence indicates an automated/CI context where the
# China-egress constraint forbids invoking GLM.
_CI_ENV_VARS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL")

# Max output token budget for opencode-routed reasoning-heavy lanes (glm/pool)
# to give headroom for hidden reasoning before a `step_finish` with reason="length".
# Observed death: ~32k reasoning + 5 output on glm-5.2 (input ~31k). Target:
# reasoning + final output headroom >= 64K (or the provider-advertised max).
#
# Control:
# - Sane default per model (131072 for glm-5.2 which advertises ~131K output).
# - Per-model env overrides: AB_GLM_MAX_OUTPUT_TOKENS, AB_POOL_MAX_OUTPUT_TOKENS
# - Global: AB_OPENCODE_MAX_OUTPUT_TOKENS
# - Falls back to setting OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX for the
#   subprocess (the known lever to lift opencode's internal ~32k cap on some
#   paths / custom providers; see anomalyco/opencode#29363 and related).
# If the provider plan or opencode build still caps it server-side, the
# experimental env is still passed (no placebo; callers can observe via
# raw NDJSON step_finish + tokens).
#
# NOTE: this is *output* (incl. reasoning for these models). Context is separate.
GLM_DEFAULT_MAX_OUTPUT_TOKENS = 131072
POOL_DEFAULT_MAX_OUTPUT_TOKENS = 131072
AB_OPENCODE_MAX_OUTPUT_TOKENS_ENV = "AB_OPENCODE_MAX_OUTPUT_TOKENS"
AB_GLM_MAX_OUTPUT_TOKENS_ENV = "AB_GLM_MAX_OUTPUT_TOKENS"
AB_POOL_MAX_OUTPUT_TOKENS_ENV = "AB_POOL_MAX_OUTPUT_TOKENS"

# Google Gemma 4 fleet member (Apr 2026, Apache-2.0). Default pin since
# 2026-07-07 = Google AI Studio DIRECT (`google-ais` opencode provider, user
# key at ~/.secret/google-ais.key; user order: "we will use the free gemma
# for some time"). Western-hosted + permissively licensed → NO egress guard
# (unlike GLM).
#
# COST — $0, triple-verified 2026-07-07:
#   1. ai.google.dev pricing: Gemma 4 free tier "Free of charge", paid tier
#      "Not available" — there IS no paid SKU, no key tier can bill it.
#   2. opencode per-run accounting reports ``cost: 0``.
#   3. The `google-ais` provider block declares ONLY gemma models, and
#      routing_guard refuses `google-ais/` non-gemma ids (the underlying
#      Cloud project is postpay — Gemini models through this key WOULD bill).
# The PAID OpenRouter ``-it`` endpoint (~$0.12/$0.35 per M tok) stays
# reachable via explicit ``--model`` as a fallback — note the spend. The OR
# ``:free`` route is pool-starved (2×300s dead-air, 2026-07-07) — avoid.
# MUST run toolless (agent="chat"): gemma is not a tool-calling model.
#
# ROLE (user probes 2026-07-05, docs/projects/qg-quality-gate/model-evidence.md):
# a cheap Google-family lane to OFFLOAD from the metered lanes (Claude / Codex).
# Ukrainian is fluent + surface-clean (VESUM-valid, 0 russicisms). USE IT FOR:
#   • cheap SURFACE review — reliably flags russicisms / calques, Latin-letter
#     leakage, and imperial / decolonization framing problems;
#   • SOURCE-CONSTRAINED wiki drafting — given a full source packet it produced
#     concise markdown + YAML with NO invented sources and every factual
#     sentence cited.
# DO NOT USE IT AS:
#   • a SOLE seminar writer — it adds unsupported details / inferences beyond
#     the supplied source packet (fluent but over-generates);
#   • a SOLE factual reviewer — not trustworthy on factual accuracy yet.
# For seminar / factual content, gate it behind a NON-Gemma source/factual check.
# Google-family → not a clean cross-family reviewer of agy / Gemini work.
GEMMA_MODEL = "google-ais/gemma-4-31b-it"
GEMMA_DEFAULT_TIMEOUT_S = 900  # chat model (no browsing); MoE variants can be slow


def _resolve_opencode_effort(
    *, lane: str, effort: str | None, variant: str | None = None
) -> tuple[str | None, str | None]:
    """Map the uniform contract to opencode's three native variants visibly."""
    requested_variant = (variant or "").strip().lower() or None
    if requested_variant and requested_variant not in POOL_VARIANTS:
        raise SystemExit(f"{lane}: invalid --variant {variant!r} (choose one of {sorted(POOL_VARIANTS)})")
    if not effort:
        return requested_variant, None
    applied = _EFFORT_TO_VARIANT[effort]
    if requested_variant and requested_variant != applied:
        raise ValueError(
            f"{lane}: --effort {effort} maps to opencode --variant {applied}, "
            f"which conflicts with --variant {requested_variant}"
        )
    reason = None
    if applied != effort:
        reason = f"opencode exposes variants minimal/high/max; requested {effort} maps to {applied}"
        print(f"NOTE: {lane} {reason}")
    return applied, reason


STANDING_TOOLLESS_NOTICE = "answer from the attached content; shell/tools are unavailable in this mode"


def _ensure_toolless_prompt_notice(prompt: str) -> str:
    if STANDING_TOOLLESS_NOTICE in prompt:
        return prompt
    return f"{prompt.rstrip()}\n\n[{STANDING_TOOLLESS_NOTICE}]"


@dataclass(frozen=True, slots=True)
class OpencodeTurnStatus:
    outcome: str  # "completed" | "aborted" | "permission_rejected" | "errored" | "trace_unavailable"
    reason: str
    cancellation_category: str | None = None
    session_id: str | None = None


class OpencodeTurnError(RuntimeError):
    """Raised when an opencode turn is not completed cleanly."""

    def __init__(self, status: OpencodeTurnStatus, partial_text: str):
        super().__init__(f"opencode turn aborted: {status.outcome}/{status.reason}")
        self.status = status
        self.partial_text = partial_text


def read_opencode_turn_status(
    stdout: str,
    *,
    cwd: Path | None = None,
    opencode_db_path: Path | None = None,
) -> OpencodeTurnStatus:
    """Classify an opencode turn: completed vs aborted/permission-rejected/errored.

    Reads opencode's session/trace state from:
      1. NDJSON stdout stream (events/parts/errors)
      2. opencode.db SQLite database (if present)

    Exit code 0 is PROVEN meaningless — turn state must be verified empirically.
    If session trace state is missing or unreadable and stream has no trace proof,
    fails closed as trace_unavailable.
    """
    session_id: str | None = None
    stream_has_error = False
    stream_error_name: str | None = None
    stream_error_msg: str | None = None
    stream_stop = False
    stream_finish_reason: str | None = None
    permission_cancelled = False
    tool_error_detail: str | None = None
    has_text = False

    raw_stdout = (stdout or "").strip()
    if raw_stdout and not raw_stdout.startswith("{"):
        has_text = True

    for raw_line in raw_stdout.splitlines():
        line = raw_line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        if (
            event.get("type") is None
            and not isinstance(event.get("part"), dict)
            and not (event.get("sessionID") or event.get("session_id"))
            and event.get("error") is None
        ):
            # A JSON object carrying none of the opencode event signature keys
            # (type/part/session/error) is model CONTENT — e.g. an ask that
            # replies with a bare JSON verdict — not a trace event. Without
            # this, a legitimate pure-JSON reply classifies as
            # trace_unavailable and a good ask is killed (REACH regression).
            has_text = True
            continue

        sid = event.get("sessionID") or event.get("session_id")
        if isinstance(sid, str) and sid:
            session_id = sid
        part = event.get("part")
        if isinstance(part, dict):
            sid_part = part.get("sessionID") or part.get("session_id")
            if isinstance(sid_part, str) and sid_part:
                session_id = sid_part

        event_type = event.get("type")
        if event_type == "text":
            has_text = True
            part_obj = event.get("part")
            if isinstance(part_obj, dict) and isinstance(part_obj.get("text"), str):
                has_text = True
        elif isinstance(part, dict) and part.get("type") == "text":
            has_text = True

        # `error: null` is a benign key on normal events — only a NON-NULL
        # error payload marks the turn errored (a null here previously blocked
        # the has_text completion fallback and killed good turns).
        if event.get("type") == "error" or event.get("error") is not None:
            stream_has_error = True
            err = event.get("error")
            if isinstance(err, dict):
                stream_error_name = str(err.get("name") or err.get("type") or "error")
                err_data = err.get("data")
                if isinstance(err_data, dict):
                    stream_error_msg = str(err_data.get("message") or "")
                elif isinstance(err_data, str):
                    stream_error_msg = err_data
            elif isinstance(err, str):
                stream_error_name = err

        if event_type in ("step_finish", "step-finish") or (
            isinstance(part, dict) and part.get("type") in ("step_finish", "step-finish")
        ):
            reason = (part.get("reason") if isinstance(part, dict) else None) or event.get("reason")
            if isinstance(reason, str):
                stream_finish_reason = reason
                if reason in ("stop", "completed"):
                    stream_stop = True
                elif reason in ("abort", "cancelled", "permission_denied", "permission_rejected", "error", "length"):
                    stream_has_error = True

        if event_type in ("tool", "tool_use") or (isinstance(part, dict) and part.get("type") in ("tool", "tool_use")):
            st = None
            if isinstance(part, dict):
                state = part.get("state")
                st = state.get("status") if isinstance(state, dict) else part.get("status")
            if st is None:
                st = event.get("status")

            if isinstance(st, str) and st in ("rejected", "cancelled", "permission_denied", "permission_rejected"):
                permission_cancelled = True
                tool = part.get("tool") if isinstance(part, dict) else None
                tool_error_detail = f"tool call {tool or 'unknown'} permission cancelled ({st})"

    db_path = opencode_db_path
    if db_path is None:
        raw_db_env = os.environ.get("OPENCODE_DB_PATH")
        if raw_db_env:
            db_path = Path(raw_db_env)
        else:
            data_home = Path(
                os.environ.get("OPENCODE_HOME")
                or os.environ.get("XDG_DATA_HOME")
                or (Path.home() / ".local" / "share")
            )
            db_path = data_home / "opencode" / "opencode.db"

    db_error_name: str | None = None
    db_error_msg: str | None = None
    db_finish_reason: str | None = None
    db_permission_cancelled = False

    if db_path and db_path.exists():
        try:
            import sqlite3

            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            try:
                cur = conn.cursor()
                target_sid = session_id
                if not target_sid and cwd is not None:
                    cur.execute(
                        "SELECT id FROM session WHERE directory = ? ORDER BY time_updated DESC LIMIT 1",
                        (str(cwd.resolve()),),
                    )
                    row = cur.fetchone()
                    if row:
                        target_sid = row[0]

                if target_sid:
                    session_id = target_sid
                    cur.execute(
                        "SELECT data FROM message WHERE session_id = ? AND json_extract(data, '$.role') = 'assistant' ORDER BY time_created DESC LIMIT 1",
                        (target_sid,),
                    )
                    msg_row = cur.fetchone()
                    if msg_row and msg_row[0]:
                        try:
                            msg_data = json.loads(msg_row[0])
                            if isinstance(msg_data, dict):
                                err = msg_data.get("error")
                                if isinstance(err, dict):
                                    db_error_name = str(err.get("name") or "error")
                                    err_d = err.get("data")
                                    if isinstance(err_d, dict):
                                        db_error_msg = str(err_d.get("message") or "")
                                db_finish_reason = msg_data.get("finish")
                        except json.JSONDecodeError:
                            pass

                    cur.execute(
                        "SELECT data FROM part WHERE session_id = ? ORDER BY time_created DESC",
                        (target_sid,),
                    )
                    for part_row in cur.fetchall():
                        if not part_row or not part_row[0]:
                            continue
                        try:
                            pdata = json.loads(part_row[0])
                            if isinstance(pdata, dict):
                                ptype = pdata.get("type")
                                if ptype in ("step-finish", "step_finish"):
                                    r = pdata.get("reason")
                                    if isinstance(r, str) and not db_finish_reason:
                                        db_finish_reason = r
                                elif ptype in ("tool", "tool_use"):
                                    st = (
                                        pdata.get("state", {}).get("status")
                                        if isinstance(pdata.get("state"), dict)
                                        else pdata.get("status")
                                    )
                                    if isinstance(st, str) and st in (
                                        "rejected",
                                        "cancelled",
                                        "permission_denied",
                                        "permission_rejected",
                                    ):
                                        db_permission_cancelled = True
                        except json.JSONDecodeError:
                            pass
            finally:
                conn.close()
        except Exception:
            pass

    if permission_cancelled or db_permission_cancelled:
        return OpencodeTurnStatus(
            outcome="permission_rejected",
            reason=tool_error_detail or "tool call permission cancelled by policy",
            cancellation_category="permission_rejected",
            session_id=session_id,
        )

    err_name = db_error_name or stream_error_name
    err_msg = db_error_msg or stream_error_msg
    if err_name:
        err_lower = (err_name + " " + (err_msg or "")).lower()
        if "permission" in err_lower or "denied" in err_lower:
            return OpencodeTurnStatus(
                outcome="permission_rejected",
                reason=err_msg or err_name,
                cancellation_category="permission_rejected",
                session_id=session_id,
            )
        if "abort" in err_lower or "cancel" in err_lower:
            return OpencodeTurnStatus(
                outcome="aborted",
                reason=err_msg or err_name,
                cancellation_category="aborted",
                session_id=session_id,
            )
        return OpencodeTurnStatus(
            outcome="errored",
            reason=err_msg or err_name,
            cancellation_category="error",
            session_id=session_id,
        )

    finish_reason = db_finish_reason or stream_finish_reason
    if finish_reason:
        if finish_reason in ("stop", "completed"):
            return OpencodeTurnStatus(
                outcome="completed",
                reason="stop",
                session_id=session_id,
            )
        if finish_reason in ("abort", "cancelled"):
            return OpencodeTurnStatus(
                outcome="aborted",
                reason=f"finish reason {finish_reason}",
                cancellation_category="aborted",
                session_id=session_id,
            )
        if finish_reason in ("permission_denied", "permission_rejected"):
            return OpencodeTurnStatus(
                outcome="permission_rejected",
                reason=f"finish reason {finish_reason}",
                cancellation_category="permission_rejected",
                session_id=session_id,
            )
        if finish_reason in ("length", "error", "unknown"):
            cat = "length" if finish_reason == "length" else "error"
            return OpencodeTurnStatus(
                outcome="errored",
                reason=f"finish reason {finish_reason}",
                cancellation_category=cat,
                session_id=session_id,
            )

    if not stream_has_error and (stream_stop or has_text):
        return OpencodeTurnStatus(
            outcome="completed",
            reason="stop",
            session_id=session_id,
        )

    return OpencodeTurnStatus(
        outcome="trace_unavailable",
        reason="missing or unreadable session state",
        cancellation_category="trace_unavailable",
        session_id=session_id,
    )


def _handle_opencode_incomplete_turn(
    msg: dict[str, Any],
    message_id: int,
    target: str,
    partial_text: str,
    turn_status: OpencodeTurnStatus,
    *,
    actual_model: str,
    effort: str | None = None,
) -> None:
    """Deliver captured native text only as an explicitly typed failed turn with a sidecar."""
    outcome = turn_status.outcome
    category = turn_status.cancellation_category or outcome
    reason = turn_status.reason
    detail = f"{outcome}/{category}"
    banner = f"[Bridge Error] opencode turn aborted ({reason})"

    sidecar_rel_path: str | None = None
    if partial_text and partial_text.strip():
        try:
            path = write_reply_sidecar(
                partial_text,
                task_id=msg.get("task_id"),
                from_llm=target,
                msg_type="error",
            )
            try:
                sidecar_rel_path = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
            except ValueError:
                sidecar_rel_path = str(path)
        except Exception:
            pass

    provenance_data, _ = response_provenance(
        msg,
        actual_model=actual_model,
        harness="opencode",
        effort_applied=effort,
    )
    try:
        metadata = json.loads(provenance_data)
    except (TypeError, json.JSONDecodeError):
        metadata = {}

    metadata.update(
        {
            "turn_outcome": outcome,
            "cancellation_category": category,
            "reason": reason,
            "partial_response": True,
            "sidecar_path": sidecar_rel_path,
        }
    )

    error_content = banner
    if sidecar_rel_path:
        error_content += f"\n\nPartial narration preserved to sidecar: {sidecar_rel_path}"

    send_message(
        content=error_content,
        task_id=msg.get("task_id", "no-task"),
        msg_type="error",
        from_llm=target,
        to_llm=msg.get("from", "user"),
        data=json.dumps(metadata, sort_keys=True),
        from_model=actual_model,
    )
    acknowledge(message_id)
    record_ask_failure(message_id, f"opencode turn aborted ({detail}: {reason})")


def ask_opencode(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    to_model: str | None = None,
    effort: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
) -> int:
    """Generic one-shot opencode call to an arbitrary opencode-reachable model.

    Escape hatch for cross-model reviews where the target isn't a named fleet
    member. To reach poolside.ai, prefer :func:`ask_pool` (opencode is a
    router — "opencode" does not identify the model).
    """
    effective_model = resolve_model_selection(
        lane="ask-opencode", to_model=to_model, model=model, default=OPENCODE_DEFAULT_MODEL
    )
    effective_variant, effort_reason = _resolve_opencode_effort(lane="ask-opencode", effort=effort)
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="opencode",
        from_model=from_model,
        to_model=to_model or effective_model,
        effort=effort,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(msg_id, "opencode", {"no_timeout": no_timeout})
        return msg_id
    print(f"\n🚀 Invoking opencode ({effective_model}) to process message #{msg_id}...")
    try:
        response = _invoke_opencode(
            content, effective_model, variant=effective_variant, data=data, no_timeout=no_timeout
        )
    except OpencodeTurnError as exc:
        msg = fetch_ask_message(msg_id, "opencode") or {
            "task_id": task_id,
            "from": from_llm,
        }
        _handle_opencode_incomplete_turn(
            msg, msg_id, "opencode", exc.partial_text, exc.status, actual_model=effective_model, effort=effort
        )
        raise SystemExit(f"[Bridge Error] opencode turn aborted ({exc.status.reason})") from exc
    provenance_data, actual_model = response_provenance(
        {"data": json.dumps({"to_model": effective_model, "effort": effort})},
        actual_model=effective_model,
        harness="opencode",
        effort_applied=effective_variant,
        effort_reason=effort_reason,
    )
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="opencode",
        to_llm=from_llm,
        data=provenance_data, from_model=actual_model, to_model=from_model,
    )
    acknowledge(msg_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def ask_pool(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    variant: str | None = None,
    model: str | None = None,
    to_model: str | None = None,
    effort: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
    on_message_created: Callable[[int], None] | None = None,
    review_pr_lifecycle: bool = False,
) -> int:
    """Send a message AND invoke poolside.ai (laguna-s-2.1) one-shot via opencode.

    ``pool`` is a cross-family CODE + web-verification reviewer: use it for
    cross-family code review, live web fact-checking (version/pricing/URL/
    citation currency, "is this API still current"), and code authoring /
    bug-fixing. Its own model family, so it's a clean reviewer of work authored
    by OpenAI / Anthropic / Google. Its differentiator is being FREE + high
    volume. It fact-checks the live web via the lightpanda MCP — note this is
    an opencode-harness capability (any opencode-hosted model browses), not a
    pool-only trait.

    Do NOT use it for translation, non-English language work, prose/long-form
    content, or pedagogy — it is a code model, weak on those.

    ``model`` overrides the pinned ``POOL_MODEL`` (model tags drift — see the
    "examples not constants" note in model-assignment.md).
    """
    effective_variant, effort_reason = _resolve_opencode_effort(
        lane="ask-pool", effort=effort, variant=variant
    )
    effective_variant = effective_variant or POOL_DEFAULT_VARIANT
    effective_model = resolve_model_selection(
        lane="ask-pool", to_model=to_model, model=model, default=POOL_MODEL
    )
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="pool",
        from_model=from_model,
        to_model=effective_model,
        effort=effort,
    )
    register_ask(msg_id)
    if on_message_created is not None:
        on_message_created(msg_id)
    if background:
        launch_background_ask(
            msg_id,
            "pool",
            {
                "no_timeout": no_timeout,
                "variant": effective_variant,
                "review_pr_lifecycle": review_pr_lifecycle,
            },
        )
        return msg_id
    print(f"\n🚀 Invoking pool ({effective_model}, variant={effective_variant}) to process message #{msg_id}...")
    try:
        response = _invoke_opencode(
            content,
            effective_model,
            variant=effective_variant,
            output_format="json",
            data=data,
            no_timeout=no_timeout,
            default_timeout_s=POOL_DEFAULT_TIMEOUT_S,
        )
    except OpencodeTurnError as exc:
        msg = fetch_ask_message(msg_id, "pool") or {
            "task_id": task_id,
            "from": from_llm,
        }
        _handle_opencode_incomplete_turn(
            msg, msg_id, "pool", exc.partial_text, exc.status, actual_model=effective_model, effort=effort
        )
        raise SystemExit(f"[Bridge Error] opencode turn aborted ({exc.status.reason})") from exc
    provenance_data, actual_model = response_provenance(
        {"data": json.dumps({"to_model": effective_model, "effort": effort})},
        actual_model=effective_model, harness="opencode", effort_applied=effective_variant,
        effort_reason=effort_reason,
    )
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="pool",
        to_llm=from_llm,
        data=provenance_data, from_model=actual_model, to_model=from_model,
    )
    acknowledge(msg_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def _assert_glm_egress_allowed(verb: str = "ask-glm") -> None:
    """Refuse to run China-hosted GLM in a CI / automated context (data egress).

    GLM (Zhipu/z.ai) sends prompt content to China. The bridge is a local,
    interactive tool; this backstop makes the LOCAL-ONLY policy load-bearing so
    a future pipeline change can't silently egress data to a China-hosted model.
    """
    for var in _CI_ENV_VARS:
        # Presence check, not truthiness: a set-but-empty var (CI="") must STILL
        # refuse — for a China-egress guard, err on the side of not sending data.
        if var in os.environ:
            raise SystemExit(
                f"{verb}: refusing to run under {var}={os.environ[var]!r}. GLM is "
                "China-hosted (Zhipu/z.ai) → prompt data egresses to China; it "
                "is LOCAL-ONLY and must never run in CI / automated pipelines."
            )


def ask_glm(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
    to_model: str | None = None,
    effort: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
    on_message_created: Callable[[int], None] | None = None,
    review_pr_lifecycle: bool = False,
) -> int:
    """Send a message AND invoke Zhipu GLM (glm-5.2) one-shot via opencode.

    ``glm`` is a strong cross-family CODE + review specialist (its top axis —
    deep security/bug review) that also browses for live fact-checks, plus a
    reported edge in large-context / cross-file coherence auditing (finding
    contradictions across many documents at once). Its own China-lab family →
    clean reviewer of OpenAI / Anthropic / Google work.

    ⚠️ China-hosted → prompt data EGRESSES TO CHINA. LOCAL-ONLY: never from CI /
    automated pipelines or with sensitive data; prefer a Western-lab reviewer
    for top-stakes work. Weak at Ukrainian (anglicizes/code-switches) and
    long-form prose / pedagogy — do NOT use it there.

    ``model`` overrides the pinned ``GLM_MODEL`` — needed while the tag drifts
    (``zai-coding-plan`` needs opencode auth; the openrouter fallback is
    ``openrouter/z-ai/glm-5.2``). Any override MUST still be a GLM model — the
    China-egress guard above is unconditional.
    """
    try:
        formal_review = assert_formal_review_ask_payload(
            content,
            msg_type=msg_type,
            task_id=task_id,
            attachment=data,
            has_target=False,
        )
    except ReviewSafetyError as exc:
        raise SystemExit(f"ask-glm: {exc}") from exc
    warn_missing_review_target(formal_review=formal_review, has_target=False)
    _assert_glm_egress_allowed()
    effective_model = resolve_model_selection(
        lane="ask-glm", to_model=to_model, model=model, default=GLM_MODEL
    )
    effective_variant, effort_reason = _resolve_opencode_effort(lane="ask-glm", effort=effort)
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="glm",
        from_model=from_model,
        to_model=effective_model,
        effort=effort,
    )
    register_ask(msg_id)
    if on_message_created is not None:
        on_message_created(msg_id)
    if background:
        launch_background_ask(
            msg_id,
            "glm",
            {
                "no_timeout": no_timeout,
                "review_pr_lifecycle": review_pr_lifecycle,
            },
        )
        return msg_id
    print(
        f"\n🚀 Invoking glm ({effective_model}) to process message #{msg_id}... [LOCAL-ONLY — data egresses to China]"
    )
    try:
        response = _invoke_opencode(
            content,
            effective_model,
            variant=effective_variant,
            output_format="json",
            data=data,
            no_timeout=no_timeout,
            default_timeout_s=GLM_DEFAULT_TIMEOUT_S,
        )
    except OpencodeTurnError as exc:
        msg = fetch_ask_message(msg_id, "glm") or {
            "task_id": task_id,
            "from": from_llm,
        }
        _handle_opencode_incomplete_turn(
            msg, msg_id, "glm", exc.partial_text, exc.status, actual_model=effective_model, effort=effort
        )
        raise SystemExit(f"[Bridge Error] opencode turn aborted ({exc.status.reason})") from exc
    provenance_data, actual_model = response_provenance(
        {"data": json.dumps({"to_model": effective_model, "effort": effort})},
        actual_model=effective_model, harness="opencode", effort_applied=effective_variant,
        effort_reason=effort_reason,
    )
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="glm",
        to_llm=from_llm,
        data=provenance_data, from_model=actual_model, to_model=from_model,
    )
    acknowledge(msg_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def ask_gemma(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
    to_model: str | None = None,
    effort: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
) -> int:
    """Send a message AND invoke Google Gemma 4 (31B-it) one-shot via opencode.

    ``gemma`` is the $0 Google-family lane (Apache-2.0) to OFFLOAD from the
    metered lanes (Claude / Codex). Default = Google AI Studio DIRECT
    (``google-ais/gemma-4-31b-it``, user key minted 2026-07-07): Gemma has NO
    paid SKU on the Gemini API (pricing verified 2026-07-07 — free tier "Free
    of charge", paid tier "Not available"), and opencode's own accounting
    reports ``cost: 0`` per run. Runs TOOLLESS via the ``chat`` opencode agent
    (gemma is not a tool-calling model; the tool bundle made it flail). The
    OpenRouter paid ``-it`` route stays reachable via ``model`` as a fallback
    (~$0.12/$0.35 per M tok — note the spend); OR ``:free`` is pool-starved
    (2×300s dead-air probes 2026-07-07), avoid. Ukrainian is fluent +
    surface-clean (VESUM-valid, 0 russicisms). Cross-family to OpenAI /
    Anthropic / DeepSeek.

    USE IT FOR (user probes 2026-07-05, model-evidence.md):
    - cheap SURFACE review — reliably flags russicisms / calques, Latin-letter
      leakage, imperial / decolonization framing;
    - SOURCE-CONSTRAINED wiki drafting — with a full source packet it cites every
      factual sentence and invents no sources.

    ⚠️ DO NOT use it as a SOLE seminar writer (it adds unsupported details beyond
    the source packet) or a SOLE factual reviewer (not trustworthy on accuracy
    yet). For seminar / factual content, gate it behind a NON-Gemma source /
    factual check. Being Google-family, it is NOT a clean reviewer of agy / Gemini
    work.

    ``model`` overrides the pinned ``GEMMA_MODEL`` (default = AIS-direct
    ``google-ais/gemma-4-31b-it``, $0) — e.g. ``google-ais/gemma-4-26b-a4b-it``
    (also $0; the MoE is #1 on the lang-uk leaderboard) or the PAID
    ``openrouter/google/gemma-4-31b-it`` fallback — while tags drift (see the
    "examples not constants" note in model-assignment.md).
    """
    effective_model = resolve_model_selection(
        lane="ask-gemma", to_model=to_model, model=model, default=GEMMA_MODEL
    )
    effective_variant, effort_reason = _resolve_opencode_effort(lane="ask-gemma", effort=effort)
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="gemma",
        from_model=from_model,
        to_model=effective_model,
        effort=effort,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(msg_id, "gemma", {"no_timeout": no_timeout})
        return msg_id
    print(f"\n🚀 Invoking gemma ({effective_model}) to process message #{msg_id}...")
    try:
        response = _strip_gemma_thought(
            _invoke_opencode(
                content,
                effective_model,
                variant=effective_variant,
                output_format="json",
                data=data,
                no_timeout=no_timeout,
                default_timeout_s=GEMMA_DEFAULT_TIMEOUT_S,
                agent="chat",
            )
        )
    except OpencodeTurnError as exc:
        msg = fetch_ask_message(msg_id, "gemma") or {
            "task_id": task_id,
            "from": from_llm,
        }
        _handle_opencode_incomplete_turn(
            msg, msg_id, "gemma", exc.partial_text, exc.status, actual_model=effective_model, effort=effort
        )
        raise SystemExit(f"[Bridge Error] opencode turn aborted ({exc.status.reason})") from exc
    provenance_data, actual_model = response_provenance(
        {"data": json.dumps({"to_model": effective_model, "effort": effort})},
        actual_model=effective_model, harness="opencode", effort_applied=effective_variant,
        effort_reason=effort_reason,
    )
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="gemma",
        to_llm=from_llm,
        data=provenance_data, from_model=actual_model, to_model=from_model,
    )
    acknowledge(msg_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def process_for_opencode(
    message_id: int,
    *,
    target: str,
    no_timeout: bool = False,
    variant: str | None = None,
) -> None:
    """Process an existing opencode-routed ask for sync and detached paths."""
    msg = fetch_ask_message(message_id, target)
    if not msg:
        return
    from ._ask_lifecycle import assert_ask_content_present

    # #4915: feed the model from the stored message body only (never inherited stdin).
    content = assert_ask_content_present(msg, message_id=message_id, target=target)
    model = ask_target_model(msg)
    if not model:
        raise ValueError(f"ask #{message_id} has no target model")
    effort = requested_effort(msg)
    effective_variant, effort_reason = _resolve_opencode_effort(
        lane=f"ask-{target}", effort=effort, variant=variant
    )

    kwargs: dict[str, object] = {"data": ask_attachment(msg), "no_timeout": no_timeout}
    try:
        if target == "opencode":
            response = _invoke_opencode(content, model, variant=effective_variant, **kwargs)
        elif target == "pool":
            response = _invoke_opencode(
                content,
                model,
                variant=effective_variant or POOL_DEFAULT_VARIANT,
                output_format="json",
                default_timeout_s=POOL_DEFAULT_TIMEOUT_S,
                **kwargs,
            )
        elif target == "glm":
            _assert_glm_egress_allowed("process background ask-glm")
            response = _invoke_opencode(
                content,
                model,
                variant=effective_variant,
                output_format="json",
                default_timeout_s=GLM_DEFAULT_TIMEOUT_S,
                **kwargs,
            )
        elif target == "gemma":
            response = _strip_gemma_thought(
                _invoke_opencode(
                    content,
                    model,
                    variant=effective_variant,
                    output_format="json",
                    default_timeout_s=GEMMA_DEFAULT_TIMEOUT_S,
                    agent="chat",
                    **kwargs,
                )
            )
        else:
            raise ValueError(f"unsupported opencode ask target {target!r}")
    except OpencodeTurnError as exc:
        _handle_opencode_incomplete_turn(
            msg, message_id, target, exc.partial_text, exc.status, actual_model=model, effort=effort
        )
        return

    provenance_data, actual_model = response_provenance(
        msg,
        actual_model=model,
        harness="opencode",
        effort_applied=effective_variant,
        effort_reason=effort_reason,
    )
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm=target,
        to_llm=msg["from"],
        data=provenance_data, from_model=actual_model, to_model=ask_sender_model(msg),
    )
    acknowledge(message_id)
    record_ask_reply(message_id, reply_id)


def _strip_gemma_thought(text: str) -> str:
    """Drop a leading Gemma ``<thought>...</thought>`` block, never to empty.

    If the model closed the run inside the thought block (observed live
    2026-07-07), stripping would deliver a blank reply — in that case return
    the original text so the content survives, thought scaffolding and all.
    """
    stripped = re.sub(r"^\s*<thought>.*?</thought>\s*", "", text, flags=re.DOTALL)
    return stripped if stripped.strip() else text


def _get_max_output_tokens(model: str) -> int | None:
    """Return the output token budget (incl. reasoning) to request for this model.

    Resolution (highest to lowest precedence):
      1. model-specific AB_* env (AB_GLM_MAX_OUTPUT_TOKENS etc.)
      2. global AB_OPENCODE_MAX_OUTPUT_TOKENS
      3. per-model sane default (131072 for glm/pool)
      4. None (do not override; let opencode/provider decide)

    The returned value (if any) is injected as OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX
    into the opencode subprocess env. This is the current mechanism to raise
    beyond opencode's ~32k internal default on some reasoning/custom paths.
    """
    # Model-specific envs take precedence
    if model == GLM_MODEL or "glm" in model.lower() or model.startswith("zai"):
        v = os.environ.get(AB_GLM_MAX_OUTPUT_TOKENS_ENV)
        if v and v.strip():
            try:
                return int(v)
            except ValueError:
                pass
    if model == POOL_MODEL or "poolside" in model.lower() or "pool" in model.lower():
        v = os.environ.get(AB_POOL_MAX_OUTPUT_TOKENS_ENV)
        if v and v.strip():
            try:
                return int(v)
            except ValueError:
                pass

    # Global override
    v = os.environ.get(AB_OPENCODE_MAX_OUTPUT_TOKENS_ENV)
    if v and v.strip():
        try:
            return int(v)
        except ValueError:
            pass

    # Sane defaults for the reasoning lanes that exhibited the length death.
    if model == GLM_MODEL or "glm" in model.lower() or model.startswith("zai"):
        return GLM_DEFAULT_MAX_OUTPUT_TOKENS
    if model == POOL_MODEL or "poolside" in model.lower():
        return POOL_DEFAULT_MAX_OUTPUT_TOKENS

    return None


@dataclass(frozen=True, slots=True)
class OpencodeStreamParse:
    """One-pass parse of an opencode ``--format json`` (NDJSON) stream.

    ``text`` is the model's *complete final output*: the last assistant
    message (post any tool-using steps / narration) when the opencode agent
    loop emits multiple assistant turns; falls back to the single/only
    message or raw stdout. This is the value the thin
    :func:`_parse_opencode_ndjson` wrapper returns for ask-*-one-shots.
    We deliberately return the LAST assistant message (not the first
    streamed chunk and not a cross-turn concatenation) because the reply
    of record for a one-shot bridge ask (ask-glm, ask-pool, ...) must be
    the model's terminal substantive answer, not preamble narration such
    as "Let me fetch…". See #5091.

    ``tool_events`` is the deduped, ordered tuple of MCP/tool invocations
    the model made during the run — the per-run observability the
    tool-theatre and grounding gates (#2156) are built on. Each event is
    a minimal ``{tool, input, status, tool_call_id, output}`` dict.
    """

    text: str
    tool_events: tuple[dict, ...]


def _run_opencode(
    content: str,
    model: str,
    *,
    variant: str | None = None,
    output_format: str = "default",
    data: str | None = None,
    no_timeout: bool = False,
    default_timeout_s: int = OPENCODE_DEFAULT_TIMEOUT_S,
    cwd: Path | None = None,
    agent: str | None = None,
) -> str:
    """Run one ``opencode run`` subprocess and return its raw stdout.

    Shared subprocess core for both :func:`_invoke_opencode` (text-only) and
    :func:`_invoke_opencode_detailed` (text + tool telemetry) so the argv
    construction, timeout, and error handling live in exactly one place.

    ``cwd`` sets the subprocess working directory. It defaults to ``None``
    (inherit the parent process cwd) so writer/bridge lanes that legitimately
    edit the repo are unaffected. Read-only lanes (the reviewer transport)
    pass an out-of-repo directory so a tool-using model's stray relative
    writes land outside the checkout (#4642 second leak path).
    """
    # Relative import: script-path invocation (python scripts/ai_agent_bridge/
    # __main__.py, the documented form) puts scripts/ on sys.path, so the
    # package is `ai_agent_bridge` — an absolute `scripts.` self-import breaks
    # every opencode-routed lane there (#4473 regression; _hermes.py already
    # uses the relative form).
    from .routing_guard import assert_model_routing_allowed

    assert_model_routing_allowed(model, context="opencode transport (_run_opencode)")
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        raise SystemExit("ask-opencode: opencode CLI not found in PATH")

    argv = [opencode_bin, "run", "--model", model, "--format", output_format]
    if agent:
        # Named opencode agent (e.g. "chat" — the TOOLLESS seat). Chat-only
        # models (gemma) must run toolless: the aggregate tool bundle adds
        # ~30K prompt tokens and non-tool-calling models flail in the loop;
        # Google-native upstreams additionally hard-reject one malformed
        # builtin/lightpanda tool schema (2026-07-07 probes).
        argv.extend(["--agent", agent])
        content = _ensure_toolless_prompt_notice(content)
    if variant:
        argv.extend(["--variant", variant])
    if data:
        data_path = Path(data)
        if not data_path.exists():
            raise SystemExit(f"ask-opencode: --data file does not exist: {data}")
        argv.extend(["--file", str(data_path.resolve())])
    # `--` ends option parsing so a prompt starting with '-' (a diff line, a
    # markdown list, etc.) is passed as the positional prompt, not misparsed by
    # opencode as an unknown flag. Unconditional — content is always positional.
    argv.append("--")
    argv.append(content)

    # Inject per-model (or env-overridable) output token budget for reasoning
    # models. This is passed via the known experimental lever so that glm/pool
    # reasoning does not hit the opencode-internal ~32k cap and die with
    # step_finish reason=length before producing the final message.
    env = os.environ.copy()
    max_tokens = _get_max_output_tokens(model)
    if max_tokens is not None:
        env["OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX"] = str(max_tokens)

    timeout = None if no_timeout else default_timeout_s
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-opencode: opencode timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(f"ask-opencode: opencode exited {result.returncode}\nstderr: {result.stderr[-2000:]}")

    return result.stdout


def _invoke_opencode(
    content: str,
    model: str,
    *,
    variant: str | None = None,
    output_format: str = "default",
    data: str | None = None,
    no_timeout: bool = False,
    default_timeout_s: int = OPENCODE_DEFAULT_TIMEOUT_S,
    agent: str | None = None,
    cwd: Path | None = None,
) -> str:
    stdout = _run_opencode(
        content,
        model,
        variant=variant,
        output_format=output_format,
        data=data,
        no_timeout=no_timeout,
        default_timeout_s=default_timeout_s,
        agent=agent,
        cwd=cwd,
    )
    turn_status = read_opencode_turn_status(stdout, cwd=cwd)
    parsed_text = _parse_opencode_ndjson(stdout) if output_format == "json" else stdout.strip()

    if turn_status.outcome != "completed":
        raise OpencodeTurnError(turn_status, parsed_text)

    return parsed_text


def _invoke_opencode_detailed(
    content: str,
    model: str,
    *,
    variant: str | None = None,
    output_format: str = "json",
    data: str | None = None,
    no_timeout: bool = False,
    default_timeout_s: int = OPENCODE_DEFAULT_TIMEOUT_S,
    cwd: Path | None = None,
) -> OpencodeStreamParse:
    """Invoke opencode and return assistant text **plus** tool telemetry.

    Only the audit reviewer-dispatch layer needs this; the bridge verbs keep
    using :func:`_invoke_opencode` (``-> str``). Tool events only exist in the
    NDJSON stream, so this defaults ``output_format="json"``; a ``default``
    format run yields no tool events.

    ``cwd`` is forwarded to :func:`_run_opencode`; the reviewer transport
    passes an out-of-repo directory to firewall stray model writes (#4642).
    """
    stdout = _run_opencode(
        content,
        model,
        variant=variant,
        output_format=output_format,
        data=data,
        no_timeout=no_timeout,
        default_timeout_s=default_timeout_s,
        cwd=cwd,
    )
    turn_status = read_opencode_turn_status(stdout, cwd=cwd)
    parse = (
        _parse_opencode_stream(stdout)
        if output_format == "json"
        else OpencodeStreamParse(text=stdout.strip(), tool_events=())
    )

    if turn_status.outcome != "completed":
        raise OpencodeTurnError(turn_status, parse.text)

    return parse


def _extract_tool_event(event: dict) -> dict | None:
    """Normalize one NDJSON tool event to a compact telemetry dict.

    Handles the observed opencode shape (top-level ``type == "tool_use"`` with a
    nested ``part`` whose ``state`` carries ``input``/``status``/``output`` and
    whose ``callID`` is the tool-call id) while tolerating flatter/older shapes.
    Structured outputs are serialized to JSON text; ``None`` is kept only when
    opencode genuinely emitted no output.
    """
    part = event.get("part")
    if not isinstance(part, dict):
        part = {}
    tool = part.get("tool") or part.get("name") or event.get("tool")
    if not isinstance(tool, str) or not tool:
        return None
    state = part.get("state") if isinstance(part.get("state"), dict) else {}
    tool_input = state.get("input", part.get("input"))
    output = state.get("output", part.get("output"))
    if output is None:
        output_text = None
    elif isinstance(output, str):
        output_text = output
    elif isinstance(output, (dict, list)):
        output_text = json.dumps(output, ensure_ascii=False, default=str)
    else:
        output_text = str(output)
    status = state.get("status") or part.get("status") or event.get("status")
    tool_call_id = part.get("callID") or part.get("tool_call_id") or part.get("id") or event.get("callID")
    return {
        "tool": tool,
        "input": tool_input,
        "status": status if isinstance(status, str) else None,
        "tool_call_id": tool_call_id if isinstance(tool_call_id, str) else None,
        "output": output_text,
    }


def _tool_event_key(event: dict) -> str:
    """Stable dedupe key for a tool event.

    ``tool_call_id`` is the PRIMARY key when present: pending->completed
    transitions of one call share an id (collapse), while distinct repeated
    identical calls keep distinct ids (counted — retry/redundancy signal the
    theatre gate needs; codex review of #4401). Falls back to tool name +
    canonical input JSON when the stream carries no id.
    """
    call_id = event.get("tool_call_id")
    if isinstance(call_id, str) and call_id:
        return f"id\0{call_id}"
    try:
        input_json = json.dumps(event.get("input"), sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        input_json = str(event.get("input"))
    return f"{event.get('tool')}\0{input_json}"


def _parse_opencode_stream(stdout: str) -> OpencodeStreamParse:
    """Parse an opencode NDJSON stream ONCE into text + deduped tool events.

    Assistant text lives in ``type == "text"`` events (``part.text``); tool
    invocations live in ``type in {"tool", "tool_use"}`` events.

    Per the opencode stream contract for agent/tool-using runs (pool/glm
    default agent; ask-glm/ask-pool one-shots), a single ``run`` can emit
    multiple assistant generations: an initial "narration" assistant message
    ("Let me fetch…", "I'll read the design…") followed (after tool results)
    by a subsequent final assistant message containing the substantive
    answer. We return only the *last* assistant message's concatenated text
    parts as ``text`` (the model's complete final output), never the first
    streamed chunk. This is the correct capture layer for bridge one-shot
    replies (process-ask path and direct ask-glm/ask-pool). Cross-turn
    gluing is avoided; single-turn streams are unaffected.

    Tool events are deduped by ``(tool, input-json)`` keeping the FINAL
    status (opencode may emit the same call multiple times as it transitions
    pending -> completed) while preserving first-seen order. Falls back to
    raw (stripped) stdout for text if no text parts parse — robust to
    opencode format drift.
    """
    current_turn: list[str] = []
    assistant_messages: list[str] = []
    deduped: dict[str, dict] = {}
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type == "text":
            part = event.get("part") or {}
            text = part.get("text")
            if isinstance(text, str):
                current_turn.append(text)
            continue
        if event_type in ("tool", "tool_use"):
            if current_turn:
                # Commit the just-finished assistant turn (e.g. preamble)
                # before processing the tool that followed it.
                msg = "".join(current_turn).strip()
                if msg:
                    assistant_messages.append(msg)
                current_turn = []
            extracted = _extract_tool_event(event)
            if extracted is not None:
                # Overwrite keeps the FINAL status; dict order keeps first-seen.
                deduped[_tool_event_key(extracted)] = extracted
            continue
        if event_type in ("step_finish", "step_start"):
            if current_turn:
                msg = "".join(current_turn).strip()
                if msg:
                    assistant_messages.append(msg)
                current_turn = []
            continue

    if current_turn:
        msg = "".join(current_turn).strip()
        if msg:
            assistant_messages.append(msg)

    # Reply of record = LAST substantive assistant message (final output),
    # not first streamed chunk. This fixes the one-shot opencode capture
    # for multi-step tasks (ask-glm, ask-pool via process-ask). Refs #5091.
    parsed = next((m for m in reversed(assistant_messages) if m), "") if assistant_messages else ""

    text = parsed if parsed else stdout.strip()
    return OpencodeStreamParse(text=text, tool_events=tuple(deduped.values()))


def _parse_opencode_ndjson(stdout: str) -> str:
    """Extract the model's complete *final* output (last assistant message)
    from opencode ``--format json`` output.

    Thin ``.text`` wrapper over :func:`_parse_opencode_stream` — signature kept
    ``-> str`` because ~8 bridge call sites (ask_gemma/ask_pool/ask_glm/ask-opencode
    and process-ask paths) and their tests assume a plain string.

    The selection of LAST (not first) message is the fix for the capture
    defect in the opencode ask lane. See _parse_opencode_stream and #5091.
    """
    return _parse_opencode_stream(stdout).text
