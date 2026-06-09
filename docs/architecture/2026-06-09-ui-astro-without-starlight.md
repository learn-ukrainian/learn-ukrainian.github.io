---
title: "Learner UI Architecture — Astro Without Starlight"
status: ACCEPTED
date: 2026-06-09
owner: Claude / orchestrator
scope: "#2823 learner-facing course UI; A1 + Folk first, A2-C2 later"
---

# Learner UI Architecture — Astro Without Starlight (Option A)

Resolves #2823 acceptance criterion *"Choose and document the initial UI
architecture path: Astro-without-Starlight or no-Astro replacement."*

## Decision

**Keep Astro as the static builder; remove Starlight as the learner-facing
layer; build custom components and routes (Option A).** Reject the
no-Astro / smaller-Vite-stack replacement (Option B) for now.

This is the path already in effect on `main` — this record makes the
existing, undocumented decision explicit.

## Why (decided from repo reality, per the #2823 brief)

| Factor | Finding |
|---|---|
| **Content pipeline compatibility** | Lessons are generated MDX (`scripts/generate_mdx/`) consumed via Astro content collections. Astro keeps that pipeline working unchanged; a non-Astro stack would mean re-tooling MDX → HTML. |
| **GitHub Pages deploy** | Astro emits a static `dist/` deployed by `deploy-pages.yml`. No change needed. |
| **Generated lesson format** | Published MDX imports `Tabs/TabItem` + activity components. Kept working via a local `src/starlight-compat/` shim + a Vite alias (`@astrojs/starlight/components` → shim), so existing MDX needs **no rewrite** and no bulk regen. |
| **Search / Word Atlas** | Custom routes (`[...slug].astro`, `lexicon/`) + a build-time search index already replace Starlight's. No Starlight dependency. |
| **Build speed / coupling** | Starlight's docs machinery was overkill for a learner course UI; the custom `CourseLayout` is lighter and gives full control over the lesson shell, hero, sidebar, and dark-mode tokens. |
| **Maintenance cost** | One owned layout (`CourseLayout.astro` + `course.css`) vs. fighting Starlight overrides. Lower long-term cost. |

## What this looks like in the tree (evidence)

- `starlight/astro.config.mjs` no longer registers the `starlight()` integration
  (only `mdx`, `react`, `sitemap`).
- The 5 Starlight override components were deleted (`9cd2e0c557`); zero real
  `@astrojs/starlight` imports remain in source.
- Learner shell is `src/layouts/CourseLayout.astro` (header nav, hero,
  breadcrumbs, lesson sidebar, footer) styled by `src/styles/course.css` with
  theme-aware `--lu-*` tokens.
- `@astrojs/starlight` stays in `package.json` (unused) only because the Vite
  alias resolves published-MDX imports to the local shim; removing the npm dep
  is a separate, lower-priority cleanup.

## Consequences

- **Generated MDX should eventually emit the shim path directly** so the Vite
  alias becomes redundant; until an A1 regen happens, the alias stays.
- The `starlight/` directory name is now historical (it predates the
  de-Starlight move); a rename is cosmetic and deferred.
- Future tracks (A2-C2, seminars) reuse `CourseLayout`; no per-track UI stack.

## Status

Accepted and in effect. Option B (no-Astro) can be revisited only if the MDX
pipeline or Pages deploy constraints change materially.
