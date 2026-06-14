# Fixture-only feature + strict conformance gate = latent break on real regen

**Date:** 2026-06-14 · **Issue:** RED-main after re-enrich · **Fix:** #3124

## What broke
`tests/test_atlas_conformance.py::test_real_lexicon_manifest_conforms_to_atlas_gates`
(a **required** `Test (pytest)` check) went RED on `main` immediately after the
controlled Atlas re-enrich (`4fabcecfc5`) regenerated `site/src/data/lexicon-manifest.json`.
~34 lemmas raised `kaikki_attribution_required`. This blocked **all code-touching
PR merges** (content-only PRs path-skip pytest, so the codex b1 train kept flowing
— which masked the breakage; it looked like only *my* PRs were stuck).

## Why (root cause)
- **#2971** (derivational-base etymology) appends an informative
  `" (etymology of base form X)"` suffix to the etymology `source` when a lemma's
  etymology resolves via its base form, e.g.
  `"kaikki/Wiktionary (CC BY-SA 3.0) (etymology of base form вигляд)"`.
- The conformance gate `_check_kaikki_attribution` required the kaikki etymology
  source to **exactly equal** `KAIKKI_SOURCE`. The suffix tripped it.
- **#2971 shipped with fixture-only tests.** Its dispatch brief *explicitly
  forbade running a full re-enrich* (to avoid hammering slovnyk.me live and
  because the worktree sparse-excludes the warm cache), deferring the single real
  re-enrich to "the orchestrator, after merge." So no test ever ran the *real*
  regenerated manifest through the conformance gate. The fixture tests passed; the
  conformance gate passed (on the **old** manifest, which had no suffix). The two
  were never exercised **together against the new artifact**.

## The trap (the reusable lesson)
A feature whose only validation is fixtures/mocks **+** a conformance gate that
asserts exact equality on a **generated artifact** = a guaranteed latent break the
moment that artifact is regenerated. Both halves were green in isolation; the break
lived in the gap between them and detonated on the first real regen — which, by
design, happened on `main` (orchestrator-run), not in any PR's CI.

## Prevention
1. **Orchestrator regen discipline:** when a dispatch brief defers the real-artifact
   regen to "orchestrator after merge," the orchestrator MUST run the relevant
   **conformance/integration suite against the regenerated artifact BEFORE merging
   dependent work or deploying** — not only a bespoke spot-check. Here the #M-11
   spot-check (`verify_manifest.py`, #3122) checked synonyms/wiki/hazards but NOT
   the conformance gate → it gave a false-clean. **Action:** wire
   `test_atlas_conformance` (or `validate_atlas_conformance.py`) into
   `verify_manifest.py` so the post-re-enrich gate runs the conformance validator,
   not just structural hazards. (Follow-up on #3122.)
2. **Tolerant gates on generated attribution:** a conformance gate over a generated
   attribution string should tolerate documented, licensing-neutral suffixes (fix
   #3124 strips `" (etymology of base form …)"` before the exact compare). Better
   still, features should put non-attribution info in a **separate field**, not
   append it into the attribution string.
3. **Fixture-only is a yellow flag for artifact features:** if a feature mutates a
   generated artifact but its tests are 100% fixtures/mocks, add at least one test
   that runs the real generator (or a small real slice) through every gate the
   artifact must pass.

## Fix
#3124 — `_check_kaikki_attribution` strips the optional base-form suffix before the
exact attribution compare (etymology only; pronunciation stays strict). +2
regression tests. 21/21 conformance tests pass incl. the real-manifest gate.
