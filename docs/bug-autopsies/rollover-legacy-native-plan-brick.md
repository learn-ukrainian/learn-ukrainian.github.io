# Rollover legacy native-plan brick (PR #5320)

**Date:** 2026-07-16 · **Category:** schema-migration / legacy-state-reconciliation
**Fixed by:** PR #5320 (`1c6bfe26e9`) · **Introduced by the interaction of:** #5233 (old prepare) × #5301/#5307 (identity envelope + registry)

## Symptom

Every thread-rollover packet prepared before the task-identity envelope landed was
un-claimable: the replacement session's `thread_handoff.py resume` failed with
*"native-created replacement must be registered before resume"*, and the demanded
`register-created` path was impossible to satisfy. All four live pending packets
fleet-wide were bricked — `claude-infra`, `claude`, and both `codex` packets. Discovered
when the claude-infra lane's own cold-start rollover claim hit the wall.

## Root cause

Three individually-reasonable changes composed into a fail-closed dead end:

1. **Old `prepare` (#5233 era)** wrote a `native_lifecycle` block into *every* lease,
   regardless of harness capability.
2. **New `resume` (#5301)** treats the *presence* of that block as proof the replacement
   must be native-created, and gates on `native_lifecycle.replacement_thread_id` — which
   only `register-created` (a native-adapter path) can bind.
3. **Legacy identity migration** assigns the harness slug `<harness>-legacy`, which is
   never in `NATIVE_TITLE_HARNESSES` — even `codex-app-legacy` — so the migrated
   transition denies native support. The honest `bind-replacement` fallback then records
   correctly but never clears the orphaned block, and `repair-native-intent` explicitly
   refuses same-rollover receipts. No sanctioned path could unbrick the lease.

The bug class: **a schema evolution changed what a state's *presence* means without
reconciling legacy state that predates the meaning.** Presence of `native_lifecycle`
became a capability claim ("this harness will native-create"), but a whole generation of
leases carried it as unconditional boilerplate.

## Fix (at the migration layer)

`normalize_identity_state` now retires a *pristine* legacy native plan
(`awaiting_native_create`, never bound) whenever the validated transition says the
harness has no native adapter — converging the lease to exactly the shape current
`prepare` emits for non-native harnesses. The block is preserved verbatim under
`native_lifecycle_retired` (reason + timestamp); no receipt is edited or deleted.
Touched plans (bound / failed / `supersession_pending`) and native-capable packets are
never retired, so the fail-closed gate for genuine native packets is intact.

Cross-family review (deepseek-v4-flash) caught two follow-on defects, both applied:
the registry projection told operators a retired/non-native lease was
`AWAITING_NATIVE_CREATE` (now projected from the identity binding:
`PREPARED`/`REPLACEMENT_CREATED`), and `repair-native-intent` dropped the
migration-changed flag (retirement computed but not persisted, plus a misleading error).

## Prevention

- **Migration must converge, not just translate.** When a schema changes the *meaning*
  of existing state (here: presence ⇒ capability), the deterministic migration is the
  place to reconcile every legacy shape into a shape the new invariants can drive —
  before any gate reads it.
- **Gate on validated capability, not on artifact presence,** when legacy data can carry
  the artifact without the capability.
- **Sweep the fleet when one lane bricks.** One `detect` failure on one lane was a probe
  of a fleet-wide class: a 10-line scan of all `*/lease.json` found 3 more bricked
  packets and proved (via `codex-app-legacy`) that even the "native" lane was affected.
- **Pin the production shape in a regression test.** The lease already half-migrated by
  pre-fix code (identity bound, orphan block intact) is a distinct shape from the
  pristine legacy lease; both are tested.

## Verification trail

- 5 new lifecycle tests + 2 registry-projection tests + 1 repair-persistence CLI test;
  full targeted sweep 134 + 201 green.
- Zero-write in-memory probe of the pure state functions against the live bricked lease
  before merge (`changed=True`, retired, `resume_state → resumed`).
- Real claim completed post-merge: resume → strict recall 10/10 → challenge proof PASS →
  `confirm-started` (`replacement_status=started`, `identity_lifecycle=confirmed`,
  `title_confirmation_state=fallback_recorded`).
