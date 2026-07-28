# Launcher-estate consolidation — design (Sol memo, 2026-07-28)

> **Status: OPERATOR APPROVED (2026-07-28).** Tracking issue: #5935. This document records
> the advisor design memo (gpt-5.6-sol, xhigh; bridge task `launcher-consolidation-sol`,
> reply 5683, 2026-07-28), including the operator's D1–D3 overrides.
>
> Sequencing prerequisite (per the memo §6): #5931 (glmcc launcher) and the Kimi
> shared-route work (#5937, merged) land first; #5932 stays separate.

---

Verdict: collapse by stable model family, not harness and not transient SKU. Harnesses and model versions become flags; driver capability remains certification-gated.

### Target public launchers

Ship these ten files now:

- `start-claude.sh`
- `start-claude-driver.sh`
- `start-codex.sh`
- `start-codex-driver.sh`
- `start-gemini.sh`
- `start-gemini-driver.sh`
- `start-grok.sh`
- `start-grok-driver.sh`
- `start-kimi.sh`
- `start-glm.sh`

Add `start-kimi-driver.sh` and `start-glm-driver.sh` only when their T4 certification is machine-recorded.

Remove the retired harness-specific public wrappers and the prior `-drive`
wrapper family. The atomic cutover contract test owns the exact absence list so
this design remains forward-looking rather than preserving obsolete commands.

### Verdicts

1. Harness collapse: yes.

   - `start-codex.sh --harness codex|claude-code`; default `codex`. This absorbs Claudex.
   - `start-kimi.sh --harness kimi-code|claude-code`; default native `kimi-code`. This absorbs KimiCC.
   - `start-glm.sh --harness claude-code`; reject unsupported `native` plainly.
   - Harness-specific names may remain internally; they should not be operator-facing files.

2. Driver naming: hard rename to `-driver`; remove `-drive`.

   Fold Sonnet/Fable into `start-claude-driver.sh --model claude-sonnet-5|claude-fable-5`.
   Operator decision D1 pins Fable as the default; Sonnet remains an explicit
   routine alternate. Reject Opus as a driver because current policy says it is
   not an orchestrator seat. Per-SKU scripts would recreate the same explosion
   on every model rotation.

3. Shared core: use one lifecycle core, not one auth monolith.

   Exact internal boundary:

   - `scripts/lib/launcher_core.sh`
   - `scripts/launchers/{claude,codex,gemini,grok,kimi,glm}.sh`
   - `scripts/lib/codex_cc_route.sh`
   - Existing in-flight `scripts/lib/kimicc_route.sh`
   - New `scripts/lib/glmcc_route.sh`

   Public scripts can then be roughly 6–10 declarative lines.

   `launcher_core.sh` owns argument grammar, root/session resolution, dry-run, model/harness dispatch, driver certification check, epic validation, lease sequencing, redacted diagnostics, and adapter hooks.

   Provider adapters—not the core—must own endpoint allowlists, credential selection, profile resolution, OAuth/config isolation, binary invocation, and provider-specific canaries. Combining those in the core would make cross-provider credential leakage substantially easier.

4. Trail gating: both file-presence and runtime gate.

   Do not ship stub Kimi/GLM driver files. Their presence falsely advertises capability and adds clutter. Even certified driver scripts must revalidate certification at launch so revocation fails closed. Interactive launchers must reject `--epic`; only `-driver` entrypoints may claim leases and inject `drive-epic`.

5. Security invariants:

   - Never reuse ambient `ANTHROPIC_AUTH_TOKEN` for Kimi or GLM by default.
   - If an exception is approved, require a named opt-in, exact default endpoint allowlist, explicit credential source, and reject simultaneous base-URL override.
   - Separate `SESSION_ROOT` from `DURABLE_HELPER_ROOT`: sessions/catalog resolution stay on the invoked worktree revision; only Kimi's OAuth helper may point to a durable main-root path.
   - Dry-run must validate credential availability while printing only the credential source, never its value.

6. Migration: hard cutover, no alias release.

   Land #5931 and the Kimi shared-route work first; keep #5932 separate. Then one public cutover updates every reference, adds the new names, and removes old files atomically. Contract tests should assert:

   - Exact root launcher allowlist
   - Old files and tracked references absent
   - Interactive launchers reject driver flags
   - Drivers require a certified model and valid epic
   - Ambient foreign credentials never cross providers
   - Catalog/session/OAuth-helper roots remain distinct
   - Dry-run output is redacted
   - Lease, canary, and `drive-epic` binding occur in the required order

### Explicit operator choices required

- Resolved by operator decision D1: the Claude driver defaults to Fable; Sonnet
  remains an explicit supported model.
- Resolved by operator decision D2: ambient `ANTHROPIC_AUTH_TOKEN` is denied for Kimi;
  require explicit Kimi credentials or OAuth.
- Resolved by operator decision D3: ship one atomic PR with a recorded size-rule
  exception. The reference sweep is part of that single cutover.
