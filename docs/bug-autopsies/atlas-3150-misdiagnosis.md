# MIS-DIAGNOSIS: a successful atlas-3150 finalize-zombie wrongly condemned as catastrophic enrichment loss

- **Date:** 2026-06-17
- **Issues:** #3150 (the task — actually near-complete), #3331 (wrongly reopened, re-closed), #2985 (the real pattern: finalize-zombie)
- **Category:** `atlas-misdiagnosis`
- **Artifact:** local branch `codex/atlas-3150-autoexpand` @ `4ea59f3f` (sound; hung at push).

> **CORRECTION.** An earlier autopsy (`atlas-reenrich-enrichment-loss.md`, merged in #3466)
> claimed the `atlas-3150-autoexpand` dispatch "zeroed all manifest enrichment (wiki 691→0)" and
> "deleted a certified module." **Both claims were false** — products of two forensics errors by
> the reviewing orchestrator (me). This file documents the mis-diagnosis itself, the real and
> instructive failure.

## Symptom
The reviewing orchestrator broadcast a **false catastrophe**: it told the user that the
`atlas-3150-autoexpand` dispatch had "zeroed all manifest enrichment (wiki 691→0)" and "deleted a
certified module," then acted on that belief — wrote a (now-retracted) autopsy
(`atlas-reenrich-enrichment-loss.md`, merged in #3466), reopened #3331, and blocked #3150. None of
it was real: the dispatch's committed work was sound and gates-passing. The expensive, confusing
part was that every downstream artifact (autopsy, reopened issue, block) was built on a single
measurement taken at the wrong moment against the wrong object.

## What actually happened
The `atlas-3150-autoexpand` dispatch (#3150) **succeeded**. Commit `4ea59f3f` (9 files, zero
curriculum) added a manifest-vocabulary-coverage gate (`check_manifest_vocabulary_coverage.py`),
wired it into CI, updated `build_data_manifest.py` / `promote_module.py`, added tests, and
**expanded the manifest with full enrichment**: entries 2447→2783, `wiki_reference` 657→718,
`heritage_status` 2447→2783 (100%), `enrichment_generated=True`. Verified post-hoc: its own tests
21/21, the new vocab gate clean (2774 lemmas / 160 modules), `test_atlas_conformance` 29/29.

It was marked `status=failed` only because it **hung at the push/PR step** — the known **#2985
finalize-zombie** (work done + locally committed, never finalized). Not a data failure.

## Root cause
The two forensics errors below — not any defect in the dispatch — are the actual bug:

1. **Measured a mid-write transient, not the committed artifact.** I read the worktree's
   *working-tree* `lexicon-manifest.json` and found `wiki_reference=0`. The codex process was
   **still live-writing the file** (it rewrites enrichment in place; I caught the gap between
   clear and refill). The file's mtime later advanced with no action from me — the tell I missed.
   The **committed** blob (`git show HEAD:…`) always had `wiki_reference=718`. #M-11 exists for
   exactly this: verify the COMMITTED artifact, never a working-tree file that may be mid-write.
2. **Read a base-divergence diff as a deletion.** `git diff origin/main..HEAD` showed
   `b1/verbal-nouns/*` as deleted. But the branch forked at `b720a6df59` — *before* #3463
   certified verbal-nouns on main — so `origin/main..HEAD` shows everything main gained since as
   "deleted by HEAD." `git show HEAD --stat` (the commit's own changes) proves it touched no
   curriculum file. Always inspect the COMMIT (`git show`), not a divergent range, to attribute
   changes.

On those two errors I wrote a false autopsy, reopened #3331, blocked #3150, and reported a
catastrophe to the user. The dispatch was fine; the review was not.

## Prevention
- **Attribute changes from `git show <sha>` / `git show <sha> --stat`, never `base..HEAD`** on a
  branch that has diverged from base. The range conflates "what this branch did" with "what base
  did since the fork."
- **Only measure committed artifacts** (`git show HEAD:path`), never a working-tree file a
  background process may still be writing. Check process liveness + file mtime before trusting a
  read of a dispatch worktree.
- **A `status=failed` dispatch is not a failed deliverable** — #2985: codex completes + commits,
  then hangs at finalize. Before condemning, inspect the commit and run its gates. Default to
  "recover the zombie," not "abandon."
- **Don't broadcast a catastrophe (autopsy / reopened issues / blocks) before the committed work
  is verified against its gates.** Verify, then report.

## Status of the work
`4ea59f3f` is a recoverable, gates-passing implementation of #3150 — to be finalized as a proper
PR (rebased onto current main; manifest re-validated for vocab coverage vs current curriculum).

## Related
- #2985 (`codex-dispatch-stall`): the finalize-zombie pattern this dispatch actually hit.
- #3124, #3197: real Atlas re-enrich regressions — distinct from this (which was not a regression).
