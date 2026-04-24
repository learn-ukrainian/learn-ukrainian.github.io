# ADR-002: Model tiering — per-phase model selection

**Status**: Accepted
**Date**: 2026-04-01 (first implemented) / 2026-04-11 (recorded)
**Related**: `scripts/build/batch_gemini_config.py`, `scripts/build/dispatch.py`, `dec-005` (decision journal entry on Gemini model choice)

## Context

Using one model for every phase wastes money on cheap tasks and underpowers hard ones. During early v6 runs we noticed:

- The `check` phase (plan validation) is a pattern-matching task that Flash handles as well as Pro at 1/10 the cost.
- The `write` phase requires the full reasoning budget — downgrading to Flash dropped review scores by 1-2 points per module.
- The `activities` phase is structurally deterministic (generate fill-in + quiz items) and benefits more from schema compliance than raw reasoning. Pro and Flash perform identically here.
- The `review` phase needs to catch subtle errors and must be a DIFFERENT agent from the writer (ADR-001). Pro-class models are required here because the review quality is the quality ceiling of the whole pipeline.

Billing data from the first 200 A1/A2 builds confirmed: a single-Pro configuration was 3-4x more expensive than a tiered configuration at comparable output quality.

## Decision

Each v6 phase gets its own default model, configurable via `scripts/build/batch_gemini_config.py`. Overrides at invocation time are supported via `--writer` / `--reviewer` flags.

**Current defaults** (as of 2026-04):

| Phase             | Default model                 | Rationale                                    |
|-------------------|-------------------------------|----------------------------------------------|
| `check`           | gemini-3-flash                | Pattern matching, no creative work            |
| `research`        | gemini-3.1-pro-preview        | Source synthesis + factual accuracy           |
| `skeleton`        | gemini-3-flash                | Structure generation, deterministic          |
| `pre-verify`      | gemini-3-flash                | Sanity checks on skeleton                     |
| `write`           | gemini-3.1-pro-preview        | Long-form reasoning, style, immersion         |
| `exercises`       | gemini-3-flash                | Template filling from the activity schema     |
| `activities`      | gemini-3-flash                | Schema-compliant generation                   |
| `verify`          | gemini-3-flash                | Pattern matching + word count                 |
| `review`          | claude-opus-4-6               | Adversarial review (different agent from writer) |

The Pro → Flash fallback cascade is automatic: if Pro rate-limits, the runtime tries Flash, then Flash-Lite. The fallback chain is defined in `batch_gemini_config.get_fallback_chain()`.

Codex (`gpt-5.5`) is NOT in the writer rotation; it's used for code review and infrastructure tasks via `scripts/ai_agent_bridge/ask-codex` and `scripts/delegate.py`, never for content.

## Alternatives considered

- **Single model everywhere (all Pro)** → rejected: 3-4x more expensive at no measurable quality gain on cheap phases.
- **Single model everywhere (all Flash)** → rejected: write and review quality dropped 1-2 review points, unacceptable for shipped content.
- **Dynamic model selection by prompt complexity** → rejected: would require a classifier + benchmark, overkill for 17 well-understood phases.
- **Pro for write, Pro for review** (single-model cross-agent) → rejected: same-agent writer+reviewer violates ADR-001's cross-agent rule. Cross-agent means Gemini + Claude, not Gemini + Gemini.

## Consequences

**Positive**:
- ~70% cost reduction on a full pipeline run vs. single-Pro baseline, measured on A1 M01-M10 batch.
- Cheap phases are fast (Flash is ~3x faster than Pro on equal prompts), so the whole pipeline wall-clock time dropped ~30%.
- The explicit tier table makes it easy to experiment with model upgrades — we can swap one phase to a new model and A/B test without touching the pipeline logic.

**Negative / risks**:
- Phase-specific models mean phase-specific failure modes. We hit this once when Flash couldn't parse the activity schema reliably on C1 modules; fix was to promote that phase to Pro. Acceptable — the discovery was caught by the audit gate before shipping.
- The Pro → Flash cascade can mask real Pro capacity issues. Mitigated by the usage JSONL at `batch_state/api_usage/usage_*.jsonl` which tracks fallback events separately (see `agent_runtime.usage.has_headroom`).

**Neutral / follow-ups**:
- When models are updated (e.g. Gemini 4 lands), the config table is the single point to change. Update `batch_gemini_config.py` + run the A1 M01-M10 benchmark + document the result in a new ADR (not this one).

## Verification

- Cost per module: tracked via `scripts/ai_agent_bridge/_cli.py codex-usage --window 30d` + the equivalent queries for Gemini via `/api/runtime/usage`.
- Quality regression check: `pytest tests/test_v6_build_events.py` + running the review phase against a known-good A1 module should produce a score ≥ 9.
- Fallback cascade: `tests/test_dispatch.py` has integration coverage for the Pro → Flash cascade path.
