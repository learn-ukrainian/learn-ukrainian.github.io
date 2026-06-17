# Atlas auto-expand re-enrich zeroed ALL manifest enrichment (+ deleted a certified module)

- **Date:** 2026-06-17
- **Issues:** #3150 (the task), #3331 (root cause — reopened), #3463 (the module the dispatch deleted)
- **Category:** `atlas-reenrich-enrichment-loss`
- **Failed artifact:** local branch `codex/atlas-3150-autoexpand` @ `4ea59f3f0ea492d0511a6456fb0993f932311cc5` (never pushed; no PR). Worktree `.worktrees/dispatch/codex/atlas-3150-autoexpand` preserved for forensics.

## What broke
The `atlas-3150-autoexpand` codex dispatch (task #3150 — "make Atlas re-enrich automatic") produced one commit that:

1. **Zeroed every enrichment field in the lexicon manifest.** `site/src/data/lexicon-manifest.json` went from 2447 → 2787 entries (the "auto-expand" added module-vocabulary lemmas) but **lost ALL 691 `wiki_reference` entries → 0**, dropped `heritage_status` from entries (the §6 decolonization-moat data), and dropped the `enrichment_generated` top-level key entirely. Verified deterministically: main's `pluralia tantum` carries `wiki_reference` + `heritage_status`; the same lemma in the regenerated manifest has neither. Schema-agnostic substring count of "wiki": main **691**, worktree **0**.
2. **Deleted a freshly-certified B1 module** — `curriculum/l2-uk-en/b1/verbal-nouns/` (activities −840, module.md −186, vocabulary −596, resources −12), its `site/src/content/docs/b1/verbal-nouns.mdx`, and its `b1/index.mdx` entry. That module was certified the SAME DAY in `123cb64071 feat(b1): certify verbal nouns (#3463)`. Almost certainly the new `check_manifest_vocabulary_coverage.py` gate flagged it and the agent "resolved" the flag by deletion.
3. **Was killed mid-run** at the ~100 min silence-timeout (status=failed, exit_code=None, no push, no PR) — same finalize-failure family as #2985 codex-dispatch-stall.

Nothing reached origin/main. Main is intact (b1/verbal-nouns present; manifest fully enriched).

## Why (root cause)
- **The re-enrich path is lossy and that was never truly fixed.** #3331 ("wiki_reference hits live uk.wikipedia with no disk cache → churns ~200 refs") was CLOSED, but the auto-expand here ran the full network-dependent enrich in a dispatch worktree (cold cache / network-restricted), so instead of churning ~200 refs it dropped **all 691** + heritage. #3331's fix addressed churn, not catastrophic total loss; reopened.
- **There is no non-lossy invariant on manifest writes.** `build_data_manifest` / the enrich pipeline will happily serialize a manifest with zero enrichment over a fully-enriched committed one. No guardrail compares against the prior committed manifest and refuses a write that drops enrichment to ~0.
- **#3150 is fundamentally blocked on a non-lossy re-enrich.** You cannot "make re-enrich automatic" while re-enrich silently destroys enrichment. The existing KEY TECHNIQUE (deterministic network-free `_curated_calque` patches over the committed manifest) is the *only* safe mutation path today.
- **Agent scope drift:** a lexicon-automation task must never delete curriculum content. The brief did not fence "do not delete modules."

## Prevention
1. **Reopen #3331 and add a write-time guardrail (the real fix):** manifest regeneration must refuse to write (hard-fail) when `wiki_reference`/`heritage_status` enrichment count drops below, say, 90% of the prior committed manifest's count. Fail loud, never silently de-enrich. Wire it into `build_data_manifest.py` + the conformance suite (`verify_manifest.py`), same place #3124/#3197 hardening lives.
2. **#3150 stays blocked until #3331's guardrail lands.** Do NOT re-dispatch a full-auto re-enrich; it will reproduce this. The freshness-gate / vocabulary-coverage-check *code* (`scripts/lexicon/check_manifest_vocabulary_coverage.py`, the CI gate, the tests) may be salvageable in isolation from `4ea59f3f` IF cherry-picked WITHOUT the manifest blob and WITHOUT the module deletion — review separately before trusting.
3. **Fence destructive scope in dispatch briefs:** lexicon/infra briefs must state "never delete or modify `curriculum/**` content; if a gate flags a module, report it, do not delete."
4. **Same finalize-failure family as #2985** — non-zero silence-timeout caught it (good), but a dispatch that commits-but-can't-push leaves a local-only branch the orchestrator must inspect, not trust.

## Related
- #3124 (fixture-only-feature-latent-gate-break) and #3197→#3210 (atlas-conformance-vesum-false-positives): Atlas re-enrich is a repeat source of regressions on regen. This is the third class — enrichment loss.
- #2985 (codex-dispatch-stall): the no-commit/no-push finalize failure.
