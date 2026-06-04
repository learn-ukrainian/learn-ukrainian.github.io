# Bug Autopsy: Stanza model md5 flake wedged required CI

## Symptom

On 2026-06-04 the required `Test (pytest)` check went red across `main` and a
large fan of open PRs (the whole A1 stack #2613–#2668, plus #2675, #2601, and
others). The failing job died in `Prewarm Stanza resources` **before pytest
even started**, with an md5 mismatch on the downloaded Ukrainian model file
`uk/tokenize/iu.pt`; pytest then cascaded into dozens of
`pipeline.stress_annotator.annotate_stress` / heteronym failures all rooted in
the same corrupt model load.

It was expensive and confusing because:
- `Test (pytest)` is the **only required** status check, so a model-download
  flake blocked **every** PR's mergeability, not just stress-related ones.
- The failure was intermittent (md5 sometimes matched), so it read like a
  content/test bug on each individual PR rather than one shared infra fault.
- It was patched **three times in a single day** before being root-fixed,
  because each patch addressed a symptom layer.

## Root cause

Required CI depended on a **live external network artifact**. The
`ukrainian-word-stress` / Stanza stack downloads the Ukrainian model at test
time; the `Prewarm Stanza resources` CI step fetched it on every run. That
download is integrity-fragile — a partial/throttled fetch or a racy parallel
download (pytest `-n auto`) yields a corrupt `.pt` whose md5 fails verification.

The deeper design flaw: a **branch-protection-blocking** check was coupled to a
flaky, non-hermetic network dependency. Any hiccup at the model host could wedge
the entire PR queue. The model code itself (`scripts/pipeline/stress_annotator.py`
and callers in `generate_mdx/generate_ipa.py`, vocab enrichment, stress
verification) is legitimate pipeline code — the bug was running its live-model
tests *inside the required gate*.

## Fix

Three layers landed the same day; only the third is the real root-fix:

- **#2681** (`e276f1924f`) — serialize the Stanza model download behind a lock
  (kills the parallel-download race).
- **#2615** (`a447043f33`) — CI prewarm catches the md5 `ValueError`, deletes
  `$RUNNER_TEMP/stanza_resources`, recreates, and retries once.
- **#2691** (`codex/2682-stanza-ci-recovery`, merged 2026-06-04 15:46Z) — the
  root-fix: mark the Stanza/HF model-backed stress tests `slow` and exclude them
  from required CI via `-k "not slow and not website"`, and remove the prewarm
  step. The required path is now **hermetic** — it never downloads a model, so
  the flake can no longer break a required check. Deterministic stress helper /
  lock tests stay in required CI.

This PR (`claude/ci-hardening-2026-06-04`) confirms the invariant holds, anchors
a comment in `ci.yml` explaining why the exclusion is load-bearing, and records
this autopsy. Out of scope: vendoring/pinning the model with an integrity check
for the `slow`/local path (follow-up).

## Prevention

- **Required CI must be hermetic** — no live model/network downloads in the
  required path. Model-backed tests stay `slow` and out of the required gate.
- The completed python/frontend paths-filter split (this PR) keeps pure
  content/MDX PRs out of pytest entirely, shrinking the blast radius further.
- This autopsy + the `.github/workflows/README.md` note document the invariant
  so a future edit does not re-add a `Prewarm Stanza` step or drop the
  `not slow` selector.
- Follow-up candidate: a tiny CI guard asserting the required pytest selection
  contains `not slow` (turns the operating rule into an enforced invariant).

## Links

- Issue: #2682 (PR-queue recovery controller surfaced the incident)
- Fix: `e276f1924f` (#2681), `a447043f33` (#2615), `#2691` (root-fix)
- PR: `claude/ci-hardening-2026-06-04` (this confirmation + autopsy)
