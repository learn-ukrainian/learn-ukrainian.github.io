# Site build

The learner site builds from `site/` with Astro: either a shell build from committed Atlas artifacts or a full hydrate+build that pulls the public Atlas manifest release asset, then serves via preview for verification.

## Sub-features

- `verify-artifacts` confirms required committed Atlas pointer/search/browse JSON before build.
- `build-shell` runs `npm run build:shell` (verify + `astro build`) without re-hydrating private DBs.
- `build-full` runs `npm run build` (hydrate + `astro build`) when the public release asset is reachable.
- `preview-ready` serves `dist/` so doctor and Playwright can drive learner routes.

## How to get to it (user POV)

- Contributors run site build commands from `site/` (or root `npm run build:starlight` / `build:starlight:full`).
- Verification uses `bin/launch.sh`, which wraps those same npm scripts.

## Driving it with launch helper

Preconditions:

- Node 22.x on `PATH`; `(cd site && npm ci)` completed.
- For `full`: outbound HTTPS to the GitHub Release asset named by `site/src/data/lexicon-manifest.pointer.json` (public).

- **Shell build + preview.** Run `LU_VERIFY_BUILD_MODE=shell bash .cursor/skills/verify-learn-ukrainian/bin/launch.sh preview`. Observable: launch prints `launch OK` and an `env.sh` path; `doctor.sh` then PASSes.
- **Artifact gate alone.** Run `(cd site && npm run verify:artifacts)`. Exit `0` or a missing-artifact list naming `make atlas-publish` as recovery (product/data issue, not private env).
- **Full build (optional).** Run `LU_VERIFY_BUILD_MODE=full bash .cursor/skills/verify-learn-ukrainian/bin/launch.sh preview`. On download failure, treat as `SKIP` for full-mode proof and fall back to shell — do not invent a local fake manifest.
- **Frontend unit gates (CI Frontend job).** After a successful hydrate-capable environment: `(cd site && npm run test:unit && npm run test:built-output)`. Skip cleanly if hydrate prerequisites are missing.
- **Proof.** Launch log + doctor OK + evidence dir created; cleanup leaves evidence.

## Gotchas

- Root `CONTRIBUTING.md` still mentions `starlight/`; the live package path is `site/`.
- `lexicon-manifest.json` is gitignored hydrate output — absence before first hydrate is normal.
- Do not set `ATLAS_MANIFEST_ALLOW_STALE_POINTER=1` to force a green build; that hides real drift.
- Full build is large (hundreds of MB unzipped); prefer shell mode for lesson-only proof.
