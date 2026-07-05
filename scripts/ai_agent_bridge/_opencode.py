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
import shutil
import subprocess
from pathlib import Path

from ._messaging import acknowledge, send_message

OPENCODE_DEFAULT_MODEL = "openrouter/qwen/qwen3.7-max"
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

# Google Gemma 4 fleet member (Apr 2026, Apache-2.0), reached via the OpenRouter
# provider under opencode. Default pin = the 31B dense PAID endpoint.
# Western-hosted + permissively licensed → NO egress guard (unlike GLM).
#
# COST (OpenRouter, verified 2026-07-05): the pinned ``-it`` endpoint is PAID but
# negligible — ~$0.12 / $0.35 per MILLION prompt / completion tokens (a module
# review is fractions of a cent). A genuinely-$0 ``:free`` endpoint also exists
# (``openrouter/google/gemma-4-31b-it:free``) but free-tier endpoints are
# rate-limited (per-min + per-day caps) and less stable → prefer it only via
# ``--model`` for high-volume / non-critical bursts, NOT as the default. (Do not
# call this lane "free" — the default pin costs money, just very little.)
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
GEMMA_MODEL = "openrouter/google/gemma-4-31b-it"
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
) -> int:
    """Send a message AND invoke Google Gemma 4 (31B-it) one-shot via opencode.

    ``gemma`` is a cheap Google-family lane (OpenRouter-hosted, Apache-2.0) to
    OFFLOAD from the metered lanes (Claude / Codex). The pinned ``-it`` endpoint
    is PAID but negligible (~$0.12/$0.35 per M tok); a genuinely-$0 ``:free``
    endpoint exists but is rate-limited / less stable → pass it via ``model``
    only for high-volume bursts. Ukrainian is fluent + surface-clean (VESUM-valid,
    0 russicisms). Cross-family to OpenAI / Anthropic / DeepSeek.

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

    ``model`` overrides the pinned ``GEMMA_MODEL`` — e.g. the 26B-A4B MoE
    (``openrouter/google/gemma-4-26b-a4b-it``, #1 on the lang-uk leaderboard) or
    the free ``openrouter/google/gemma-4-31b-it:free`` endpoint — while tags
    drift (see the "examples not constants" note in model-assignment.md).
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
    print(f"\n🚀 Invoking gemma ({effective_model}) to process message #{msg_id}...")
    response = _invoke_opencode(
        content,
        effective_model,
        output_format="json",
        data=data,
        no_timeout=no_timeout,
        default_timeout_s=GEMMA_DEFAULT_TIMEOUT_S,
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

    return msg_id


def _invoke_opencode(
    content: str,
    model: str,
    *,
    variant: str | None = None,
    output_format: str = "default",
    data: str | None = None,
    no_timeout: bool = False,
    default_timeout_s: int = OPENCODE_DEFAULT_TIMEOUT_S,
) -> str:
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        raise SystemExit("ask-opencode: opencode CLI not found in PATH")

    argv = [opencode_bin, "run", "--model", model, "--format", output_format]
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
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-opencode: opencode timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(f"ask-opencode: opencode exited {result.returncode}\nstderr: {result.stderr[-2000:]}")

    if output_format == "json":
        return _parse_opencode_ndjson(result.stdout)

    # opencode run (--format default) prints ANSI control codes and a banner
    # before the response; the JSON stream is cleaner to parse. Callers that
    # need reliable text extraction should request output_format="json".
    return result.stdout.strip()


def _parse_opencode_ndjson(stdout: str) -> str:
    """Extract the assistant's final text from opencode ``--format json`` output.

    Each stdout line is a JSON event. Assistant text lives in events with a
    top-level ``type == "text"`` (``event["part"]["text"]``). Reasoning, tool,
    step-start/finish and other event types are ignored. Falls back to the raw
    (stripped) stdout if no text parts parse — robust to opencode format drift.
    """
    chunks: list[str] = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "text":
            continue
        part = event.get("part") or {}
        text = part.get("text")
        if isinstance(text, str):
            chunks.append(text)

    parsed = "".join(chunks).strip()
    return parsed if parsed else stdout.strip()
