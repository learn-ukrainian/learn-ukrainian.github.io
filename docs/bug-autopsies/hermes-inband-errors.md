# Hermes in-band provider errors parsed as success (PR #4580)

**Date**: 2026-07-06 · **Category**: silent-error-as-content · **Fix**: PR #4580

## What broke

Two faults in the hermes-lane runtime path (deepseek, grok, qwen adapters):

1. **In-band HTTP errors**: hermes surfaces provider API failures as the
   FINAL assistant message on stdout with returncode 0 — e.g.
   `HTTP 401: Authentication Fails, Your api key: ****robe is invalid`
   (hermes-agent `run_agent.py` `_describe_api_error` formats
   `HTTP {status}: {message}` / `HTTP {status} — {title} — Ray {id}`).
   `build_hermes_parse_fields` used `ok = returncode == 0 and bool(response)`,
   so the error line parsed as a SUCCESSFUL response: dispatches recorded
   `outcome=ok` with the error string as their deliverable, and the #4501
   runner failover classifier — which only runs on `not parse.ok` — never
   fired.
2. **Dead-credential startup failures**: `hermes -z: agent failed: Provider
   'X' is set in config.yaml but no API key was found...` (rc != 0, so
   parse correctly failed) matched NO trigger class in
   `classify_failover_trigger` — credential rotation, a headline #4497
   use-case, never engaged.

## Why

The parse layer equated "process exited 0 with output" with "invocation
succeeded". CLIs that virtualize provider errors into the conversation
channel (hermes renders them as the assistant's final message) break that
assumption. The failover classifier was then grounded in *transport-level*
error phrasing (401/unauthorized/timeouts) and had no coverage for the
CLI's own *startup* phrasing for missing credentials.

Neither gap was visible in unit tests because fixtures modeled errors as
nonzero-rc + stderr — the shapes a well-behaved CLI produces. Only a live
forced-failure probe (isolated HERMES_HOME, deliberately dead credential)
exposed the real shapes.

## Prevention

- **Fix at the chokepoint**: `_inband_provider_error()` in
  `hermes_common.py` — a single-line, ≤600-char, `^HTTP [45]\d{2}`-anchored
  stdout parses `ok=False` with the error in `stderr_excerpt` (429 also
  sets `rate_limited`). All three hermes lanes inherit it. Conservative
  shape so multi-line content discussing HTTP statuses is untouched.
- **Classifier grounded in live-captured strings**: credential-absence
  phrasings added to `_AUTH_RE`; the exact captured strings are pinned in
  `tests/agent_runtime/test_runner_failover.py`.
- **Probe methodology is the regression harness**: any new chain or parse
  change re-runs `scripts/agent_runtime/probe_fallback.py` with a forced
  failure — validate the REAL fault shape, not the imagined one. (Same
  lesson as the 2026-07-05 hermes `fallback_providers` probe that
  prevented shipping imaginary resilience.)
- **Category rule**: when wrapping ANY agent CLI, test what it emits on
  provider failure by *forcing one live* — rc conventions and error
  channels differ per CLI and per failure class (in-band vs startup vs
  stderr), and a wrong assumption converts outages into silent garbage
  deliverables.
- **Retro sweep**: #4583 AC2 sweeps historical usage records for
  ok-outcome rows matching the in-band error shape.
