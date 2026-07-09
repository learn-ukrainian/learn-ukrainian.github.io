"""Opencode transport for ai_agent_bridge — the multi-provider router.

``opencode run`` is a ROUTER that fronts many providers/models, so "opencode"
is NOT itself a fleet member — you must name the model. Two bridge verbs ride
this transport:

- ``ask-opencode`` — generic escape hatch to ANY opencode-reachable model
  (e.g. ``openrouter/qwen/qwen3.7-max``) for one-off cross-model reviews.
- ``ask-pool`` — the first-class **poolside.ai** fleet member (model
  ``poolside/poolside/laguna-m.1``): a clean cross-family CODE + web-
  verification specialist. Rides opencode with reasoning-effort control
  (``--variant``) and NDJSON parsing, and fact-checks the live web via the
  lightpanda MCP server wired into ``~/.config/opencode/opencode.jsonc``.
  See ``ask_pool`` below.
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
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ._ask_lifecycle import (
    ask_attachment,
    ask_sender_model,
    ask_target_model,
    fetch_ask_message,
    launch_background_ask,
    record_ask_reply,
    register_ask,
)
from ._messaging import acknowledge, send_message

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
POOL_MODEL = "poolside/poolside/laguna-m.1"
POOL_DEFAULT_VARIANT = "high"  # reasoning effort: minimal | high | max
POOL_DEFAULT_TIMEOUT_S = 1800  # browsing + high-effort reasoning runs long
POOL_VARIANTS = frozenset({"minimal", "high", "max"})

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
# ROLE (user probes 2026-07-05, docs/projects/ua-eval-harness/model-evidence.md):
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


def ask_opencode(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    to_model: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
) -> int:
    """Generic one-shot opencode call to an arbitrary opencode-reachable model.

    Escape hatch for cross-model reviews where the target isn't a named fleet
    member. To reach poolside.ai, prefer :func:`ask_pool` (opencode is a
    router — "opencode" does not identify the model).
    """
    effective_model = model or OPENCODE_DEFAULT_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="opencode",
        from_model=from_model,
        to_model=to_model or effective_model,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(msg_id, "opencode", {"no_timeout": no_timeout})
        return msg_id
    print(f"\n🚀 Invoking opencode ({effective_model}) to process message #{msg_id}...")
    response = _invoke_opencode(content, effective_model, data=data, no_timeout=no_timeout)
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="opencode",
        to_llm=from_llm,
        to_model=from_model,
    )
    acknowledge(msg_id)
    acknowledge(reply_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def ask_pool(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    variant: str | None = None,
    model: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
) -> int:
    """Send a message AND invoke poolside.ai (laguna-m.1) one-shot via opencode.

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
    effective_variant = (variant or POOL_DEFAULT_VARIANT).strip().lower()
    if effective_variant not in POOL_VARIANTS:
        raise SystemExit(f"ask-pool: invalid --variant {variant!r} (choose one of {sorted(POOL_VARIANTS)})")
    effective_model = model or POOL_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="pool",
        from_model=from_model,
        to_model=effective_model,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(
            msg_id,
            "pool",
            {"no_timeout": no_timeout, "variant": effective_variant},
        )
        return msg_id
    print(f"\n🚀 Invoking pool ({effective_model}, variant={effective_variant}) to process message #{msg_id}...")
    response = _invoke_opencode(
        content,
        effective_model,
        variant=effective_variant,
        output_format="json",
        data=data,
        no_timeout=no_timeout,
        default_timeout_s=POOL_DEFAULT_TIMEOUT_S,
    )
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="pool",
        to_llm=from_llm,
        to_model=from_model,
    )
    acknowledge(msg_id)
    acknowledge(reply_id)
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
    from_llm: str = "claude",
    from_model: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
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
    _assert_glm_egress_allowed()
    effective_model = model or GLM_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="glm",
        from_model=from_model,
        to_model=effective_model,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(msg_id, "glm", {"no_timeout": no_timeout})
        return msg_id
    print(
        f"\n🚀 Invoking glm ({effective_model}) to process message #{msg_id}... [LOCAL-ONLY — data egresses to China]"
    )
    response = _invoke_opencode(
        content,
        effective_model,
        output_format="json",
        data=data,
        no_timeout=no_timeout,
        default_timeout_s=GLM_DEFAULT_TIMEOUT_S,
    )
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="glm",
        to_llm=from_llm,
        to_model=from_model,
    )
    acknowledge(msg_id)
    acknowledge(reply_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def ask_gemma(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
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
    effective_model = model or GEMMA_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="gemma",
        from_model=from_model,
        to_model=effective_model,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(msg_id, "gemma", {"no_timeout": no_timeout})
        return msg_id
    print(f"\n🚀 Invoking gemma ({effective_model}) to process message #{msg_id}...")
    response = _strip_gemma_thought(
        _invoke_opencode(
            content,
            effective_model,
            output_format="json",
            data=data,
            no_timeout=no_timeout,
            default_timeout_s=GEMMA_DEFAULT_TIMEOUT_S,
            agent="chat",
        )
    )
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="gemma",
        to_llm=from_llm,
        to_model=from_model,
    )
    acknowledge(msg_id)
    acknowledge(reply_id)
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
    model = ask_target_model(msg)
    if not model:
        raise ValueError(f"ask #{message_id} has no target model")

    kwargs: dict[str, object] = {"data": ask_attachment(msg), "no_timeout": no_timeout}
    if target == "opencode":
        response = _invoke_opencode(msg["content"], model, **kwargs)
    elif target == "pool":
        response = _invoke_opencode(
            msg["content"],
            model,
            variant=variant or POOL_DEFAULT_VARIANT,
            output_format="json",
            default_timeout_s=POOL_DEFAULT_TIMEOUT_S,
            **kwargs,
        )
    elif target == "glm":
        _assert_glm_egress_allowed("process background ask-glm")
        response = _invoke_opencode(
            msg["content"],
            model,
            output_format="json",
            default_timeout_s=GLM_DEFAULT_TIMEOUT_S,
            **kwargs,
        )
    elif target == "gemma":
        response = _strip_gemma_thought(
            _invoke_opencode(
                msg["content"],
                model,
                output_format="json",
                default_timeout_s=GEMMA_DEFAULT_TIMEOUT_S,
                agent="chat",
                **kwargs,
            )
        )
    else:
        raise ValueError(f"unsupported opencode ask target {target!r}")

    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm=target,
        to_llm=msg["from"],
        to_model=ask_sender_model(msg),
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_reply(message_id, reply_id)


def _strip_gemma_thought(text: str) -> str:
    """Drop a leading Gemma ``<thought>...</thought>`` block, never to empty.

    If the model closed the run inside the thought block (observed live
    2026-07-07), stripping would deliver a blank reply — in that case return
    the original text so the content survives, thought scaffolding and all.
    """
    stripped = re.sub(r"^\s*<thought>.*?</thought>\s*", "", text, flags=re.DOTALL)
    return stripped if stripped.strip() else text


@dataclass(frozen=True, slots=True)
class OpencodeStreamParse:
    """One-pass parse of an opencode ``--format json`` (NDJSON) stream.

    ``text`` is the assistant's final answer (same value the thin
    :func:`_parse_opencode_ndjson` wrapper returns). ``tool_events`` is the
    deduped, ordered tuple of MCP/tool invocations the model made during the
    run — the per-run observability the tool-theatre and grounding gates
    (#2156) are built on. Each event is a minimal
    ``{tool, input, status, tool_call_id, output}`` dict.
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

    timeout = None if no_timeout else default_timeout_s
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd is not None else None,
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
    )
    if output_format == "json":
        return _parse_opencode_ndjson(stdout)

    # opencode run (--format default) prints ANSI control codes and a banner
    # before the response; the JSON stream is cleaner to parse. Callers that
    # need reliable text extraction should request output_format="json".
    return stdout.strip()


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
    if output_format == "json":
        return _parse_opencode_stream(stdout)
    return OpencodeStreamParse(text=stdout.strip(), tool_events=())


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
    invocations live in ``type in {"tool", "tool_use"}`` events. Tool events are
    deduped by ``(tool, input-json)`` keeping the FINAL status (opencode may emit
    the same call multiple times as it transitions pending -> completed) while
    preserving first-seen order. Falls back to raw (stripped) stdout for text if
    no text parts parse — robust to opencode format drift.
    """
    chunks: list[str] = []
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
                chunks.append(text)
            continue
        if event_type in ("tool", "tool_use"):
            extracted = _extract_tool_event(event)
            if extracted is not None:
                # Overwrite keeps the FINAL status; dict order keeps first-seen.
                deduped[_tool_event_key(extracted)] = extracted

    parsed = "".join(chunks).strip()
    text = parsed if parsed else stdout.strip()
    return OpencodeStreamParse(text=text, tool_events=tuple(deduped.values()))


def _parse_opencode_ndjson(stdout: str) -> str:
    """Extract the assistant's final text from opencode ``--format json`` output.

    Thin ``.text`` wrapper over :func:`_parse_opencode_stream` — signature kept
    ``-> str`` because ~8 bridge call sites (ask_gemma/ask_pool/ask_glm/...) and
    their tests assume a plain string.
    """
    return _parse_opencode_stream(stdout).text
