# Bug Autopsy: CI / Caching

### 2026-07-05 — Atlas-manifest cache poisoning + stale-base MDX drift (PR #4386 CI failure)
**What broke:** PR #4386's `MDX Generation Drift` CI job failed 3× while the identical check
passed locally, including under a CI-mimic env (minimal venv, anonymous hydrate).
**Root cause:** three stacked causes —
1. ACTUAL cause: the PR branch was based before #4381's `scripts/generate_mdx/resources.py` and
   examples-dedup changes; CI regenerates on the MERGE ref (new generator) vs committed MDX (old
   generator). Fixed by merging main + regenerating the touched modules.
2. LATENT: two Actions cache entries existed under the SAME `lexicon-manifest-<pointer-hash>`
   key with DIFFERENT sizes — `actions/cache` saves at job end, so a job that mutates the
   manifest after restore poisons the key for all consumers. Fixed: restore → verify-vs-pointer
   (rehydrate) → immediate save.
3. LATENT: `atlas_links._load_index` fail-softs to `{}` on any manifest error — silently
   producing links-less MDX that misreports as content drift. Fixed: loud stderr warning.
**Prevention:** cache content must be verified against its pin after restore (a cache key does
not pin content); silent degradation in generators is forbidden — degrade loudly. When a
drift/parity CI check disagrees with local, FIRST diff the merge ref vs your base
(`git merge origin/main` locally reproduces it), not the environment.
