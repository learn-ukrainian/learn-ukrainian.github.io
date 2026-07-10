# Destructive restores — restore tooling silently clobbering newer local work

## 2026-07-10 — hydrate-manifest wiped an in-flight intake promotion

**What broke:** during the #4220 intake arc, the local `lexicon-manifest.json` held 8,706
entries (2,919 freshly promoted + a full 1.5h re-enrich) awaiting `make atlas-publish`.
A concurrently-dispatched worker ran the site build's `npm run hydrate`, which downloaded
the *published* 5,787-entry release asset and overwrote the local file. The promotion and
the enrichment output were destroyed. (Recoverable: atlas.db had already been rebuilt from
the enriched manifest and survived; dictionary-lookup caches made the re-run cheap.)

**Why:** `hydrate-manifest.mjs` treated the published release as unconditionally
authoritative. That assumption is wrong exactly during intake — the window between
`promote --write` and `make atlas-publish` is when the local file is legitimately AHEAD
of the release, and it is also the window when parallel site builds are most likely
(busy fleet). Classic destructive-restore: the tool destroys more data than it restores,
silently, on its happy path.

**Prevention:** (the category rule) any restore/hydrate/sync tool that can overwrite
local state must compare BEFORE writing and refuse when the local artifact is richer
(more entries / newer generation), requiring an explicit force flag for intentional
restores. Fixed for hydrate-manifest in the same PR (`ATLAS_MANIFEST_FORCE_HYDRATE=1`
to force). Audit candidate for the same class: `hydrate-practice-deck.mjs` (confirmed by review —
downloads a release asset and unconditionally overwrites local deck state, no local-work
guard). `hydrate-lexicon-api-shards.ts` is NOT this class: it is a local generator over
already-hydrated data — no download, no pointer, no overwrite-from-remote.
