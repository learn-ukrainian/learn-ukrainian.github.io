# Claude orchestrator session handoff — 2026-06-08 (UI / #2823)

Generated near context ceiling (~815K, autocompact OFF). Driving #2823 (lightweight
UI tech + design); folk is owned by another agent (hands-off).

## ⚠️ ACTIVE HAZARD — Codex is working in the SHARED main checkout
A parallel **Codex** process checked out `codex/context-handoff-memory` IN the primary
checkout (against the worktree rule), committed on it, and left a `claude_extensions/ →
agents_extensions/shared/` rename WIP. This caused:
- A branch switch out from under `main` (I restored main; Codex's WIP → `stash@{1}`,
  committed work safe on `origin/codex/context-handoff-memory`).
- Recurring `.git/index.lock` collisions that intermittently break my commits/stashes.
- Untracked `agents_extensions/` (README.md + codex/memory/MEMORY.md) left in tree.
**Recommend:** get Codex onto a worktree; do not let two agents share the main checkout.

## SHIPPED + PUSHED (safe on origin/main, verified in-browser on localhost:4321)
1. `497c51b09a` chore(agents): retarget track-orchestrator default → folk epic (#2849).
2. `1ce28423d3` **fix(ui): dark-mode contrast** — root cause: chromatic/fixed surfaces
   consumed theme-INVERTING tokens. Added fixed on-color tokens (`--lu-on-yellow`,
   `--lu-hero-grad`, `--lu-footer-bg`). Fixed footer (was white-on-white), badges,
   "Start A1" button, hero (now fixed azure), lexicon hero, logo/active-nav, track
   badges, + 3 activity-widget regressions (groupTitle/stepBadge/bucketPlaceholder).
   Contrast audit: home 23→0; A1 lesson regressions resolved. 340 frontend tests pass.
3. `cd4620834a` docs(scripts): canonical local-site workflow via services.sh.
4. `cf1c78fafe` fix(ui): A1 landing secondary CTA was stale "Open M08" → now "Open Word Atlas".

NOTE: origin/main HEAD is `21bc38a89c` (sits ON TOP of my commits — all 4 confirmed
ancestors via merge-base; nothing clobbered). Public Pages deploy NOT triggered (manual
`deploy-pages.yml`); user explicitly wants live site untouched, local-only.

## LOCAL SERVICES
`./services.sh start astro` → http://localhost:4321/ is the canonical local site (NOT
ad-hoc `npm run dev`/`nohup` — that caused 4322 port drift earlier). Currently running.

## IN-FLIGHT / PARKED
### Slice 1 (de-Starlight) — in `stash@{0}`, BLOCKED, needs redo
Attempted: rename 59 published MDX imports `@astrojs/starlight/components` →
`@site/src/starlight-compat`, fix generator `scripts/generate_mdx/core.py:292`, delete 5
dead `src/components/overrides/*`, drop Vite alias. **Build green (144pp), 88 pytest green.**
BUT blocked by the `check-mdx-source-parity` pre-commit gate (forbids hand-editing
published MDX without curriculum source change). **Redo approach:** KEEP the Vite alias
(it's a harmless local shim now), do only the parity-SAFE parts — fix generator for future
MDX + delete dead overrides + delete dead Starlight/Docusaurus/Infima CSS in
`starlight/src/css/custom.css` + drop unused `template` field in `content.config.ts`. Do
NOT bulk-edit published MDX (regenerate via pipeline instead, or leave alias).
`node_modules/@astrojs/starlight` is physically present but UNUSED after override deletion.

### Lexicon "unusable" (user-reported) — DIAGNOSED, decision needed
`/lexicon/<lemma>/` detail pages (e.g. він-вона-воно) are **deliberately thin v1 stubs**
(`src/pages/lexicon/[lemma].astro`, per `word-atlas-design.md §9`). Manifest
`src/data/lexicon-manifest.json` (gen by `scripts/lexicon/build_data_manifest.py`) has only
lemma/gloss/POS/course_usage. Meaning/etymology/morphology are "Дані готуються" placeholders
(enrichment from VESUM/ESUM/SUM-20/heritage deferred + unrun). Also a raw **`plan_required`**
status token leaks into the course-links badge (clear UI bug — map to a human label or hide).
**DECISION for user:** (a) build the lexicon enrichment pipeline (substantial, needs
source-verified content), or (b) **defer Word Atlas from public nav** until populated (the
#2823 AC explicitly allows "explicitly defer a scoped subset"). Quick win regardless: fix
the `plan_required` token leak.

## #2823 slice plan (remaining)
1 cleanup (parked, see above) · 2 shell+home landing · 3 CoreLesson template · 4 seminar
(folk+lit) · 5 Word Atlas · 6 deploy doc + visual design QA. Design-QA already swept 7 page
classes (home/A1-landing/core-lesson/folk/lexicon/404/B1) — all clean in dark mode.

## Follow-ups filed (task list)
#8 activity-widget gamified palette is low-contrast in BOTH themes (pre-existing, not a dark
regression) — needs a deliberate WCAG palette pass.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git stash list            # stash@{0}=my slice-1 WIP, stash@{1}=Codex WIP
./services.sh status      # astro on 4321
git log origin/main --oneline -6
```
