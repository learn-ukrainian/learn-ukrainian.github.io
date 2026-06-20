# Хрестоматія (primary-source readings) — authoritative design spec

**Status: IMPLEMENTED for real (not a mockup).** This was prototyped as standalone HTML,
then — per the "it must match the main site exactly, or we adjust everything" requirement —
built as **real astro pages** that reuse the site's own layout/CSS, so there is zero drift.
This file is the binding spec; the live pages are the reference.

**Live routes (dev server):**
- Section landing: `/folk/readings/`
- Reading page: `/folk/readings/dumy-nevilnytski-lytsarski/` («Дума про Марусю Богуславку», full PD text)

## What the Хрестоматія is
A **parallel, per-track "primary-sources" section** (anthology), course-looking but **NOT**
part of the numbered module ladder. Holds the **full original texts** the lessons teach from
in excerpts. Lives under each seminar: `/folk/readings/`, later `/lit/readings/`, etc.

## Binding rules
1. **Not numbered modules.** Readings live at `<track>/readings/**`, are excluded from the module
   sidebar bucket, carry a "Хрестоматія" eyebrow (never "Module NN"), and a sidebar counter
   "N текстів" (never "Урок N з M"). (Root-cause fix for readings appearing as a phantom "module 50".)
2. **Excerpt ↔ full-text contract.** Lesson keeps `<PrimaryReading>` excerpts ("📜 Читаємо
   першоджерело") + a "прочитати повністю →" link; the complete text lives in the Хрестоматія.
3. **Verse formatting.** Full text goes inside `<PrimaryReading>` as clean Markdown blockquotes;
   verse renders as lines via the merged verse-CSS (#3663) — **no `<br/>`**.
4. **Source/attribution.** Every reading ends with provenance, a public-domain statement, and
   "подано дослівно за записом — архаїчні й діалектні форми збережено."
5. **Hosting.** Host on-site every text we teach from (verified PD corpus). Verified-external links
   only for supplementary breadth, behind the URL-resolve gate. Never an unchecked link.
6. **Huge works** (Eneida-scale): one page per part/canto.

## Generalizes to ALL seminar tracks (esp. LIT)
The engine is track-agnostic — it keys on `<track>/readings/`, so **lit, hist, bio, istorio, oes,
ruth** get the identical section behaviour. To enable another track's readings:
1. Author `site/src/content/docs/<track>/readings/index.mdx` + `*.mdx`.
2. Ensure the content-collection glob in `site/src/content.config.ts` includes `<track>/readings/**`
   (folk is already globbed via `folk/**`; other seminars currently load only `index` — add a
   `<track>/readings/**` pattern when their readings land).
3. Add `<track>` to `publicLessonPrefixes` in `[...slug].astro::getStaticPaths` (currently a1/a2/b1/folk).

## Implementation (this PR)
- `site/src/pages/[...slug].astro` — readings bucket split + Хрестоматія sidebar + eyebrow (reuses
  the existing `CourseLayout` sidebar prop → zero new layout code → exact site match).
- `site/src/content/docs/folk/readings/{index,dumy-nevilnytski-lytsarski}.mdx` — landing + first reading.
- `scripts/audit/check_mdx_source_parity.py` — exempt `<track>/readings/**` (hand-authored, no module
  source) from the MDX↔source parity gate (+2 regression tests).

## Reference text
«Дума про Марусю Богуславку» — full text, public domain (запис за М. Драгомановим); the worked
exemplar for the невільницькі-думи module. Same text as parked PR #3660, which folds into this section.
