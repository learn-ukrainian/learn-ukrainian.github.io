# Atlas build silently renders STALE data: `hydrate-manifest.mjs` clobbers a locally-regenerated manifest

**Date:** 2026-06-26
**Issue:** #3852
**Category:** atlas-build / hydrate-clobber-on-stale-pointer
**Tool:** `site/scripts/hydrate-manifest.mjs`, `scripts/lexicon/publish_manifest.py`, `scripts/lexicon/enrich_manifest.py`
**Impact:** During the СУМ-11 decolonization purge (#3852), the Atlas manifest was regenerated
locally to drop Soviet СУМ-11 data, but `npm run build` silently **overwrote the regen with the
old Release-asset manifest** and rendered the OLD (СУМ-11-containing) data. Caught only by an
explicit render-verify; cost a full second re-regen (~5–10 min warm / ~40 min cold). Recurring
class — this is the "stale-manifest trap" that has bitten multiple sessions (#3124, #3416, PR1a
of the practice-hub epic, and the warning-severity gradient #3759).

## Symptom

After regenerating `site/src/data/lexicon-manifest.json` locally (СУМ-11 removed, VTS/СУМ-20
added) and verifying 0 СУМ-11 traces in the file, running `npm run build` produced pages that
**still showed СУМ-11 source cards**. The on-disk manifest was correct; the rendered output was
stale. Re-reading the file after the build showed it had been **reverted** to the pre-regen
content.

## Root cause

The Atlas manifest is a ~41 MB derived artifact. Since #3659 it is **not committed to git** — it
is published as a GitHub Release asset (`atlas-manifest`, the gzipped `lexicon-manifest.json.gz`)
and hydrated at build time. Three files form a consistency triangle:

| File | Carries | Committed? |
|------|---------|-----------|
| `lexicon-manifest.json` | the actual 41 MB data | **gitignored** (hydrated at build) |
| `lexicon-manifest.pointer.json` | `asset_url`, `gz_sha256`, `json_sha256`, `manifest_fingerprint` | committed |
| `lexicon-manifest.fingerprint.json` | sha256 of `scripts/lexicon/*.py` (the generator code) | committed |

`npm run build` runs `site/scripts/hydrate-manifest.mjs` **before** astro build. Hydrate's logic:

> If the local `lexicon-manifest.json` sha256 ≠ the committed pointer's `json_sha256`,
> the local copy is assumed STALE → **download the Release asset and overwrite the local file.**

That heuristic is correct for a fresh checkout (no local manifest → fetch the published one). But
it is exactly **wrong** mid-regen: a freshly regenerated manifest *intentionally* differs from the
still-old pointer, so hydrate reads "different sha → stale" and clobbers the new data with the old
asset. The regen and the pointer move in lockstep on the published path (`make atlas-publish`),
but a **local regen without re-stamping the pointer** leaves them divergent, and hydrate resolves
the divergence in favor of the *published* (old) bytes — silently, with no error.

### Why it is silent

Hydrate treats "local differs from pointer" as the normal cold-checkout case and just downloads.
There is no "local is newer than the asset" branch — it cannot tell an intentional regen apart
from a stale leftover, because the only freshness signal it trusts is the committed pointer, which
the local regen did not update.

## The deeper coupling (why any lexicon code edit is entangled)

`hydrate-manifest.mjs::assertPointerFresh` also throws if
`pointer.manifest_fingerprint !== fingerprint.fingerprint`, where `fingerprint` is the committed
sidecar = `sha256(scripts/lexicon/*.py)`. `enrich()` embeds that same code fingerprint into the
manifest, and `publish_manifest.py` re-validates the chain on upload. Net effect:

- **Editing any `scripts/lexicon/*.py` file** (even output-neutral dead-code removal) changes the
  sidecar fingerprint → the pre-commit hook regenerates the sidecar → it no longer matches the
  committed pointer → `assertPointerFresh` throws at the astro build → Frontend CI red **until the
  manifest is re-stamped and the Release asset republished**.

This coupling is *intentional and load-bearing*: it guarantees the published manifest was produced
by the current generator code, which CI cannot otherwise verify (the dictionary DBs are not
available in CI). The cost is that a generator-code change and an asset republish are inseparable —
you cannot land a `scripts/lexicon/*.py` edit without republishing what it generates (or proving it
unchanged, which CI cannot do). **Do not weaken the gate to dodge this** — it would silently
de-couple the manifest from its generator. Instead, pay the republish cost when it is already being
paid (bundle output-neutral code changes into a PR that regenerates the manifest for a data reason).

## Prevention

1. **Write the pointer LOCALLY first, then build.** After a local regen, before `npm run build`/
   `astro build`, write the pointer to match the new manifest (no upload):

   ```python
   from scripts.lexicon import publish_manifest as pm
   # Do not call gzip_manifest/build_pointer_payload/write_pointer directly:
   # every canonical pointer write must first pass the shared richness gate.
   # Use publish_manifest (or reenrich_thin_manifest_entries.py --write), which
   # records the gate decision and then packages the pointer.
   ```

   Now `local manifest sha == pointer.json_sha256` → hydrate is a **no-op** → the build renders the
   regenerated data. Upload the asset (`publish_manifest.py`, which DOES `gh release upload`) only
   at merge time.

2. **Re-read the manifest after `npm run build`** and re-assert the property you regenerated for
   (here: 0 СУМ-11 traces). The on-disk file before the build is NOT evidence the build used it —
   hydrate runs in between. This is the #M-4a "verify the real artifact end-to-end" rule applied to
   the build step.

3. **Publish atomicity at merge:** `gh release upload --clobber` overwrites the single shared asset,
   so main's old pointer breaks until the PR merges. Verify locally first, then upload → push →
   CI-green → **merge fast** (window ≈ CI duration); the live site is static and unaffected.

4. **Bundle output-neutral `scripts/lexicon/*.py` edits** (dead-code removal, behavior-preserving
   refactors) into a PR that already regenerates + republishes the manifest for a data reason —
   never as a standalone PR, which would force a gratuitous asset republish + main-CI-red window for
   cosmetic gain.

## Links

- Issue: #3852 (СУМ-11 purge — the session this trap was hit)
- Related: #3796 (deck → Release-asset migration), #3675 (Atlas auto-grow), #3659 (manifest →
  Release asset, the change that introduced hydrate-on-build)
- Commit: `b718d95cae` (feat(lexicon): purge СУМ-11; fill with VTS/СУМ-20 — #3852)
- Decision: `docs/decisions/2026-06-25-lexicon-update-mechanics.md` (the 3-layer update model)
- Recipe: `scripts/lexicon/publish_manifest.py` (`gzip_manifest` / `build_pointer_payload` /
  `write_pointer` vs the upload path)
