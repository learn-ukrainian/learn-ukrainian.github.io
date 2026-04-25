# ADR-008 — Draft — UK-Native Track Destination & Naming

> **Status:** DRAFT — awaiting Krisztian decision 2026-04-21
> **Date:** 2026-04-21
> **Deciders:** Krisztian, Claude, Codex
> **Related:** EPIC #1365, `docs/session-state/2026-04-21-evening-strategic-audit.md`, `docs/plans/jiggly-soaring-forest.md`
> **Context:** EPIC #1365 A.11/A.12 Ukrainian-canonical pilot hit the
> problem that built UK A1/A2 lessons overwrote the English-track
> destination (`starlight/src/content/docs/a1/`) when published.
> This ADR pins where UK-native content lives, how it's named, and
> how the pipeline enforces non-overlap with English track.

## The honest framing

**Primary purpose:** corpus-enrichment artifact. The UK A1/A2 modules
are Phase 2 of the corpus-bootstrap plan — they exist to become
retrievable Ukrainian-native source material that later Phase-G
English-speaker modules draw from. The agents need this content to
produce rich English modules; that's the build reason.

**Secondary purpose:** useful for human Ukrainian-native learners /
teachers as a by-product. Because the content is real lessons (not
just a retrieval corpus), it's shareable. the native reviewer reviews it partly to
verify corpus quality and partly because it's potentially useful for
her students.

The public framing and naming should reflect this honesty, not pretend
this is a polished native-speaker curriculum line competing with
published Ukrainian school textbooks.

## The question

Where do **Ukrainian-canonical A1/A2 modules** (primarily corpus
artifacts, secondarily human-readable content) live — filesystem,
URL, public name — so that:

1. the native reviewer can access them via Starlight-rendered URL during review
2. They NEVER overwrite the English-track at `docs/a1/*.mdx`
3. They stay addressable during Phases 2-3 (corpus enrichment) and
   beyond if we choose to publish them publicly
4. The pipeline mechanically refuses to write UK output to English
   paths and vice versa

## Options considered

### Option 1: Separate Starlight collection

| | Value |
|---|---|
| Filesystem | `starlight/src/content/docs-native/{a1,a2}/*.mdx` |
| URL | `/native/a1/sounds-letters-and-hello` |
| Collection config | New in `starlight/src/content/config.ts` |
| Sidebar config | New `docs-native` sidebar in astro config |
| Public name (UK) | Українська як рідна |
| Public name (EN) | Ukrainian, Native Edition |

**Pros:** Clean separation at framework layer. the native reviewer gets full rendered experience (tabs, widgets). Search can be scoped per collection. Future-proofs for public launch as its own product. URL is honest about the audience.

**Cons:** One-time Astro config work (~1hr). Duplicates some nav infrastructure.

### Option 2: Same collection, subdir tag

| | Value |
|---|---|
| Filesystem | `starlight/src/content/docs/native-a1/*.mdx` |
| URL | `/native-a1/sounds-letters-and-hello` |

**Pros:** No new collection config, just a subdir.
**Cons:** Search across collections mixes native + English content; sidebar logic needs rules; `docs/native-a1/` is clunky; harder to enforce "pipeline never writes UK to English subdir" via paths alone.

### Option 3: Sidecar site

Separate Astro project entirely (`starlight-native/`).
**Pros:** Total isolation.
**Cons:** 2× infrastructure (CI, deploy, dependency updates); the native reviewer navigates two URLs; no real benefit over Option 1.

### Option 4: Markdown-only, no render

Raw `.md` in `review-packets/uk-a1/`.
**Pros:** Minimal infrastructure.
**Cons:** the native reviewer doesn't see activity widgets, dialogue rendering, stress marks as styled — she'd review prose, not "what learners would see". Today's whole problem was that raw prose wasn't enough.

## Recommendation: Option 1

**Reasoning:**
- Option 4 is out — user said the point is the native reviewer sees what Starlight renders
- Option 3 is 2× ops cost for zero gain
- Option 2 is cheaper in setup but uses filesystem conventions to enforce a track boundary, which is brittle — someone running the wrong command still clobbers
- Option 1 is the only one where Starlight's own collection boundary gives us hard separation — a UK-pipeline output CANNOT land in the English collection without explicit code changes

**Configuration cost:** ~1 hour of Astro config work once. Then the pipeline's `step_publish` takes a `--collection docs-native` flag (or reads `V6_PHASE_SUITE=uk` → infers `docs-native`), writes only to that tree, and the English-collection publish path is structurally unreachable from a UK run.

## Naming convention

### Filesystem layout
```
starlight/src/content/
  docs/                    ← English-speaker track (existing, unchanged)
    a1/<slug>.mdx
    a2/<slug>.mdx
  docs-native/             ← Ukrainian-native track (NEW)
    a1/<slug>.mdx
    a2/<slug>.mdx
```

### Slug convention
**English slugs inside UK paths** (e.g., `docs-native/a1/sounds-letters-and-hello.mdx`):
- Consistent with `curriculum/l2-uk-en/curriculum.yaml` slug keys
- Consistent with `plans/a1/<slug>.yaml` naming
- Easier cross-referencing in build logs and code
- Parallel pair-up between UK lesson and English lesson with the same slug — useful for eventual comparison/QA

**Ukrainian title in MDX frontmatter** (what the native reviewer / learners see):
```yaml
---
title: "Звуки, літери та привіт"
sidebar:
  label: "01. Звуки, літери та привіт"
---
```
Already happening — M01's current frontmatter matches this.

### URL structure
```
https://learn-ukrainian.github.io/a1/sounds-letters-and-hello       ← English
https://learn-ukrainian.github.io/native/a1/sounds-letters-and-hello ← Ukrainian
```

### Public-facing names

Given the honest framing (corpus artifact first, human-readable
second), we shouldn't use polished-product branding like "Native
Edition." Options in decreasing marketing-ness:

**Option A — honest about origin (my recommendation):**

| Context | Name (UK) | Name (EN, for docs) |
|---|---|---|
| Collection | Чернетка «Українська як рідна» | UK-Native Draft |
| Nav label | Рідна мова (чернетка) | Native (draft) |
| Pilot label | Пілот для рецензії | Pilot for review |

Disclaimer banner at top of landing page + top of each lesson:

> **Українською:** Цей матеріал створено насамперед як україномовне
> джерело для майбутніх уроків для англомовних. Ми ділимося ним і з
> україномовними читачами, бо контент виявився корисним сам собою.
> Це чернетка — не офіційний підручник.
>
> **EN:** This material was built first as a Ukrainian-language
> source for future lessons aimed at English speakers. We're sharing
> it with Ukrainian readers because the content turned out useful on
> its own. This is a draft, not an official textbook.

**Option B — standard Ukrainian pedagogy term:**

| Context | Name (UK) | Name (EN) |
|---|---|---|
| Collection | Українська як рідна | Ukrainian as Native |
| Nav label | Рідна мова | Native Edition |

"Українська як рідна" is standard Ukrainian school terminology for
native-speaker Ukrainian classes. Professional but potentially
over-promises since our content isn't at published-textbook polish.

**Option C — even more humble:**

| Context | Name (UK) | Name (EN) |
|---|---|---|
| Collection | Сирі матеріали для курсу | Raw course materials |
| Nav label | Матеріали | Materials |

Too self-deprecating — signals lower quality than the actual content.

## Pipeline enforcement

`scripts/build/v6_build.py::step_publish` must:

1. Read `V6_PHASE_SUITE` env var (or a new `V6_TRACK_DESTINATION=native|english` var if cleaner)
2. If `uk` / `native`: target `starlight/src/content/docs-native/{level}/{slug}.mdx`
3. If unset / `english`: target `starlight/src/content/docs/{level}/{slug}.mdx` (current behavior)
4. **Refuse to write across tracks.** If `V6_PHASE_SUITE=uk` and destination computes to `docs/a1/*`, error loudly.
5. Log the destination before writing (today's publish phase is already verbose, just needs one more log line).

This is the **structural guard** that prevents the bug we hit today.
Without it, any future `--force-publish` on a UK module with a
forgotten env var can clobber English content again.

## Phase-3 corpus integration

The UK A1/A2 modules become retrievable source material (corpus-bootstrap
plan step 3). This ADR only covers their PUBLISH destination. Corpus
retrieval layer reads them from `curriculum/l2-uk-en/a1/*.md` (pre-publish),
not from Starlight MDX, so no impact on retrieval.

## Migration

No migration of existing English modules needed — `docs/` stays as-is.
The UK content currently clobbered into `docs/a1/sounds-letters-and-hello.mdx`
(M01) needs to be:
1. Moved to `docs-native/a1/sounds-letters-and-hello.mdx`
2. The English M01 at `docs/a1/sounds-letters-and-hello.mdx` rebuilt from scratch when we reach Phase G of the corpus-bootstrap plan (not urgent; English track is deferred until corpus is enriched)

## Risks / follow-ups

- **Starlight sidebar index** for `docs-native` needs a separate index page (landing). Reuse English index template, translate.
- **Search scope** — Starlight's Pagefind may index both collections by default; may need exclusion rule depending on whether we want cross-collection search.
- **Public launch decision deferred** — this ADR scopes the PATH only. Whether to go public with the native edition once content quality is the native reviewer-approved is a separate later call.

## Open questions (not blocking this ADR)

- Do we want a language toggle in the Starlight header ("Native Edition" / "English Edition")? Post-pilot decision.
- Do we want the native track to have a separate domain long-term (e.g., `rodna.learn-ukrainian.github.io`)? Deferred to post-pilot.

## Decision requested

**Approve Option 1 with the naming convention above?**

If yes, the pipeline changes are a Codex ticket (likely #1393 when filed), ~2-3 hours of work: Starlight collection config + `step_publish` destination routing + guard tests.

If you prefer a different naming ("рідна мова" vs "як рідна" / slug conventions / URL slug `/uk-native/` vs `/native/`), flag it here and I update before filing.
