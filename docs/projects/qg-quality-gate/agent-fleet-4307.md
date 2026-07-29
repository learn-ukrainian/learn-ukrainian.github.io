# Agent Fleet Evidence for #4307

Date: 2026-07-04

Issue: [#4307](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4307)

This note records the concrete fleet lanes used for the source-language-agnostic
schema slice. Raw task JSON/result files live under `batch_state/tasks/` and
are local operational state, not committed artifacts.

## Summary

| Lane | Task id | Mode | Model | Duration | Prompt chars | Response chars | Result |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| Cursor review | `4307-cursor-schema-review` | read-only | `auto` | 66.399s | 2518 | 14849 | Completed. Strongest schema-blocker analysis. |
| AGY review | `4307-agy-schema-review` | read-only | `Gemini 3.1 Pro (High)` | 95.123s | 2287 | 7644 | Completed. Good linguistic and false-positive blockers. |
| DeepSeek review | `4307-deepseek-schema-review` | read-only | `deepseek-v4-pro` | 181.517s | 2522 | 0 | Timed out at initial response. |
| Qwen review | `4307-qwen-schema-review` | read-only | `qwen/qwen3.6-plus` | 180.914s | 2514 | 0 | Timed out; not a desired #2156 lane going forward. |
| Cursor implementation | `4307-cursor-schema-impl` | danger | `auto` | 59.495s | 2802 | 1683 | Produced schema/test patch and auto-finalized PR #4318. |

The dispatch runtime exposes these delegate agents for this repo:
`codex`, `gemini`, `claude`, `grok`, `grok-build` (alias), `grok-hermes`, `deepseek`, `qwen`, `agy`,
and `cursor`. It does not expose a literal `glm` delegate target in
`scripts/delegate.py` or `scripts/agent_runtime/registry.py` as of this run.
Older bakeoff docs mention GLM as a model-family participant, but there is no
callable GLM lane to dispatch here yet.

Routing update after this run: do not assign Qwen to #2156 work unless the user
explicitly re-enables it. DeepSeek is still an expected review lane; its timeout
in this repo should be treated as a learn-ukrainian runtime/config mismatch to
debug against the working kubedojo DeepSeek setup, not as evidence that
DeepSeek itself is unavailable.

## Findings by Lane

### Cursor Review

Strengths:

- Found the real blocker: existing deterministic evidence and LLM compact
  evidence use different envelopes and dimension names.
- Correctly separated `contact_source_lang` from learner-track L1.
- Identified issue-id fragmentation between curriculum phrase rules,
  russicism gates, UA-GEC lookup, and #912 semantic false friends.
- Produced concrete field, mapping, and false-positive-control proposals.

Weaknesses:

- The recommendation still required integrator decisions on version naming and
  projection policy.
- It did not solve downstream adapter wiring; it scoped that correctly as
  #4308 work.

Observed fit:

Cursor was the strongest fast architecture reviewer for this code-adjacent
schema task.

### AGY Review

Strengths:

- Independently confirmed "no blocker for schema PR" while flagging blockers
  before scorer adapters.
- Emphasized teaching-example masking, heritage/dialect guards, and rigid
  CC-BY-4.0 attribution as adapter prerequisites.
- Gave a useful #912 model: semantic false friends need sense context and must
  not be blanket-failed.

Weaknesses:

- Less specific than Cursor on existing dual-envelope compatibility.
- Suggested stricter UA-GEC severities in places where the existing repo keeps
  bulk lookup as `info`; the integrator kept the repo's current safer default.

Observed fit:

AGY is useful for language taxonomy, false-positive risk, and prompt/reviewer
calibration, especially as a non-Codex independent reviewer.

### DeepSeek Review

Observed failure:

- Timed out after 181.517s at the initial-response gate.
- `response_chars` was `0`; no schema judgment was available.
- Worktree was clean on exit.

Observed fit:

DeepSeek remains the desired cheap review lane for this project. This run shows
that the learn-ukrainian dispatch path did not respond, while the user's
kubedojo setup is known to work. Before relying on DeepSeek for #4308 or PR
review, compare this repo's Hermes/delegate configuration and environment with
kubedojo and rerun a tiny smoke prompt.

### Qwen Review

Observed failure:

- Timed out after 180.914s at the initial-response gate.
- `response_chars` was `0`; no schema judgment was available.
- Worktree was clean on exit.

Observed fit:

Qwen is not a desired lane for #2156 work. The timeout is recorded for honesty
because the lane was dispatched, but it should not be part of the follow-up
reliability target unless the routing policy changes.

### Cursor Implementation

Strengths:

- Produced a focused two-file implementation with schema helpers and tests in
  under one minute.
- Covered stable finding ids, UA-GEC tag mapping, source-language validation,
  #912 semantic false friends, and legacy-schema non-overwrite checks.

Weaknesses:

- The delegate runtime auto-finalized the dirty worktree into draft PR #4318
  even though the worker brief said not to commit or push. That is an
  operational hazard for danger-mode lanes.
- The worker implementation used a finding-only schema version
  (`ua_qg_finding.v1`) rather than the record-level
  `ua_contact_quality_evidence.v1` contract accepted by the integrator.
- The worker defaulted some contact grammar mappings to `unknown`; the
  accepted contract defaults prioritized UA-GEC F/G tags to Russian unless a
  source row or rule metadata says otherwise.

Observed fit:

Cursor is a strong bounded implementation lane, but danger-mode dispatch needs
explicit auto-finalization expectations. For future implementation lanes, use
read-only design first, then either accept that delegate may open a draft PR or
disable auto-finalization if the runtime supports it.

## Decisions Applied

- The accepted contract is record-level `ua_contact_quality_evidence.v1`, not a
  finding-only schema.
- Existing `curriculum_ua_qg_evidence.v1` and `llm_qg_evidence.v1` stay as
  compatible projection versions; no migration is required for #4307.
- `contact_source_lang` is canonical; `source_lang` is retained as a
  compatibility alias for issue text and future adapters.
- UA-GEC bulk lookup remains `info` by default.
- `F/Style` is not a deterministic-adapter input for #4308.
- #912 emits `SEMANTIC_FALSE_FRIEND` with `sense_context` and
  `contact_source_lang: ru`.

## Operational Follow-Ups

Tracked in
[#4321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4321).

- Wire or document a real GLM dispatch lane before promising GLM participation
  in future fleet tasks.
- Restore DeepSeek by checking learn-ukrainian runtime/config parity against
  kubedojo, where DeepSeek is known to work.
- Do not use Qwen for #2156 work unless the user explicitly re-enables it.
- Treat Cursor danger-mode auto-finalization as expected behavior unless
  delegate runtime configuration proves otherwise.
