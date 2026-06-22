# Primary-Text Acquisition & Hosting System (demand-driven, multi-source, all tracks)

## Context

Students must read **original Ukrainian texts** inside lessons — exactly as the Ukrainian school
textbooks do: a pedagogue selects *the* important passage of a work and embeds it where kids read and
process it with a teacher. We must do this across **all of Ukrainian culture we cover** (1,270
literature + seminar modules), hosting **only the texts a module actually teaches** — not bulk-scraping
whole Wikisource categories (the mistake the earlier folk-думи approach was drifting into).

This plan replaces that one-off, folk-only, bulk-ingest direction with a general, demand-driven system.

### What we already have (verified this session via 3 Explore passes)
- **Demand signal already exists, machine-readable:** every lit + seminar plan carries a `references:`
  block, and entries tagged **`type: primary`** mark the original works the module teaches —
  **2,116 primary refs across 1,270 modules, 100% adoption** (`curriculum/l2-uk-en/plans/<track>/<slug>.yaml`).
  The hand-built folk coverage map was just re-deriving this by hand.
- **The hosting engine already exists:** `scripts/readings/generate_readings.py` resolves a module's
  declared primary texts → matches the corpus → **PD gate** (`is_public_domain`, fail-closed) →
  **quote-verify gate** (every line must appear in the source) → renders a reading `.mdx` → linked at
  render time by `scripts/generate_mdx/reading_links.py` (file-existence gated). It is just **folk-only**
  and **`sources.db`-only** today.
- **The curated source you pointed at:** the ingested **literature textbooks** (`textbook_sections` +
  `textbooks` in `data/sources.db`, Avramenko/Mishchenko grades 9–11). `textbook_sections.section_title`
  cleanly names **author → work → the lesson excerpt**, with grade + page range + interleaved pedagogy.
  ⚠️ **The textbook text is often ABRIDGED (`скорочено`) and OCR-noisy** — so it is the **curation /
  selection signal (which work, which passage, what grade, how framed)**, NOT the verbatim text-of-record.
- **Clean full text** lives in `literary_texts` (137k chunks: chronicles, Драгоманов folk, OES, etc.) and,
  as PD fallback, on Wikisource (`scripts/rag/scrape_wikisource.py`, built+merged this session) / ukrlib.
- **Build-time gate:** Astro enforces `public_domain: z.literal(true)` on every reading
  (`site/src/content.config.ts`). There is **no** CI gate that re-checks reading text against `sources.db`.

### Decisions locked
- **Rights (user choice = "Excerpt + link"; verified against Ukraine's Law No. 2811-IX — full detail in
  "Rights law" below):** PD works → **host the full clean original**. In-copyright works → **host a brief
  analytical excerpt + a link**, grounded in Ukraine's **quotation right** (criticism / scholarship /
  education) — lawful because our use is **non-commercial**, **attributed**, and **limited to the extent the
  lesson's analysis justifies**.
- **Textbook = selection, not text-of-record (user):** never host the textbook's shortened/OCR text as
  the original. Use the textbook to pick the work + passage + grade; source the clean verbatim text
  separately. For PD works prefer the **full** clean original over the textbook's abridged cut.

## Rights law (verified 2026-06 — Ukraine Law No. 2811-IX, in force 2023-01-01, EU-aligned)

Applied to our exact posture: **non-commercial, free, open-source, public `github.io` site, attribution
always, goal = popularize Ukrainian literature.** (Not legal advice — for scaled in-copyright hosting,
confirm with Ukrainian IP counsel.)

- **No US-style "fair use" — a CLOSED, exhaustive list of exceptions.** We may rely only on the specific
  enumerated free-use grounds, each requiring **attribution to author + source**.
  ([Lexology](https://www.lexology.com/library/detail.aspx?g=6b75c750-5fcd-4b73-989c-4b17bb26a250),
  [ICLG 2026](https://iclg.com/practice-areas/copyright-laws-and-regulations/ukraine/))
- **Quotation right (цитата)** = the primary basis for in-copyright text: brief excerpts of lawfully
  published works for **criticism / polemic / scholarship / education**, **to the extent justified by the
  purpose**, attributed, boundaries clearly marked. Our lessons *analyze* the works, so quoting excerpts for
  that analysis fits squarely. No access-control condition attaches to quotation.
- **Teaching-illustration / distance-learning exceptions** also exist BUT the distance-learning one
  requires materials be **"protected from unauthorized access"** — an **open public `github.io` site does
  NOT meet that**, so we **do not** rely on it. We lean on the **quotation right** instead.
- **Term:** life + 70. **Repressed-then-rehabilitated authors = rehabilitation + 70** → most Executed
  Renaissance writers are STILL protected. **Moral rights are perpetual** → attribute even PD works.
  ([Wikimedia Commons](https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_territory/Ukraine))
- **State e-textbooks are not openly licensed** — Ukraine's free e-textbooks (IMZO / National Educational
  Electronic Platform) are free to *access* but carry no open licence, so they are **not reusable** as
  source content. We take clean PD text from PD editions / our corpus, never from them.
  ([School Education Platform](https://school-education.ec.europa.eu/en/discover/news/online-educational-resources-ukrainian-schooling-ukraine-under-adverse-conditions))

**Net posture — maximize access, never gatekeep Ukrainian literature.** PD works (Shevchenko, Franko,
Lesya, Kotsiubynsky, Stefanyk — everyone pre-1956 — plus folk/medieval) → **host the full text on-site,
freely, attributed.** In-copyright works (Stus, Kostenko, the Executed Renaissance under rehab+70, living
authors) → host the brief analytical excerpt **AND link straight to the free full text** on reputable
public sources (`ukrlib.com.ua`, Wikisource, `litopys.org.ua`, `chtyvo.org.ua`, diasporiana) so the reader
reaches the complete work in **one click**. The reader is never denied a work — they read it in full here,
or one click away. The legal `/legal/` page is a light backstop; the goal is the widest possible reach.

## Design — 5 components (each a reusable layer, not a folk one-off)

### 1. Demand manifest — `scripts/readings/primary_text_demand.py` (NEW)
Scan **all** plans' `references: type: primary` → emit a machine-readable registry of **distinct
(work, author)** → the list of modules that teach it (+ grade/track hints). Deduplicates shared works
(e.g. *Кобзар* referenced by many bio/lit/hist modules). This is the automated, all-track generalization
of the hand-audited folk coverage map, and the single input that drives hosting. Output: a JSON build
artifact (e.g. `data/primary_text_demand.json`).

### 2. Textbook curation lookup (NEW resolver step)
Query `textbook_sections` by `section_title`/author for each demanded work → return the **curated
presentation**: grade, the excerpt the textbook teaches, page range, and that it's the curriculum-approved
selection. Used to (a) confirm a work is in the school canon + at what level, and (b) define the
**excerpt boundary** for in-copyright works. **Not** used as the verbatim text (abridged/OCR).

### 3. Multi-source clean-text resolver + rights classifier (extend the engine's resolve+gate)
For each demanded work:
- **Rights classify (law-grounded, fail-safe = conservative):** PD if folk / anonymous / pre-modern
  (OES, Ruthenian, baroque) **or** a named author who **died ≥71 years ago** (life + 70) — **UNLESS** the
  author was **repressed and posthumously rehabilitated**, in which case the term runs **rehabilitation +
  70** (so most Executed Renaissance authors are STILL in copyright). **Default to in-copyright** whenever
  the author's death/rehabilitation date is unknown or borderline — hosting an excerpt instead of the full
  work is cheap; hosting a still-protected work in full is legal exposure. Extend `is_public_domain`
  (today `≤1928` / `ukrlib-narod`) with an **author-death table + a repressed/rehabilitated flag + rehab year**.
- **Resolve clean verbatim text** in priority order: `literary_texts` corpus → Wikisource per-work fetch
  (`scrape_wikisource.py`, used as a **single-work fetcher**, not a category dump) → ukrlib. `verify_quote`-gated.
- **Free-full-text link resolver (the anti-gatekeeping mechanism):** for EVERY in-copyright work, locate
  and record a **direct link to the free full text** on reputable public sources (`ukrlib.com.ua`,
  Wikisource, `litopys.org.ua`, `chtyvo.org.ua`, diasporiana). This is mandatory, not optional — an
  in-copyright reading without a working free-full-text link is incomplete.
- **Emit:** PD → full clean work (host on-site). In-copyright → the brief analytical excerpt
  (clean-sourced) **+ a prominent "read the full work" link** to the free public source above.

### 4. Generalized hosting engine — extend `generate_readings.py` + rendering across tracks
- Drive `generate_readings.py` from the **demand manifest** across **all tracks** (not just folk module
  dirs, not just `:::primary-reading` blocks). Reuse its PD gate, quote-verify gate, `render_reading`,
  and the `taught_in`/dedup logic.
- Generalize rendering: `scripts/generate_mdx/converters.py::convert_folk_content_blocks` is folk-specific
  → add a **general primary-reading converter** so any track's module embeds + links its reading.
- **Demand-driven:** only works referenced by ≥1 module are hosted.

### 5. Legal / compliance — rights metadata + a dedicated compliance subpage
- Each reading's frontmatter records its **rights class** (`public_domain` = host full / `quotation` =
  excerpt only) + **attribution** (author + source). Astro already enforces `public_domain: true`; extend
  so in-copyright readings carry the source link + an "excerpt quoted for educational analysis under
  Ukraine's quotation right" marker. A reading must never host more than its class allows.
- A dedicated **`/legal/` compliance subpage** (NOT the homepage; linked from the footer) stating the
  project's compliance with **Ukrainian copyright law**: PD works hosted in full with attribution;
  in-copyright works used only as brief attributed quotation-excerpts for educational analysis;
  non-commercial; perpetual moral-rights attribution; and a contact / takedown path.

## Phased rollout (1,270 modules = a fleet program; ship incrementally)
- **Phase 0 — manifest** (read-only, all tracks). Cheap, high-value; gives the real coverage picture.
- **Phase 1 — resolver** (textbook lookup + rights classifier + clean-text resolution). Prove on a
  handful of works (1 folk PD, 1 lit PD = Shevchenko/Kotliarevsky, 1 in-copyright = Stus).
- **Phase 2 — generalize the engine + rendering**; host a first **real batch** end-to-end: the PD
  school-canon works a few lit modules teach (clean from corpus/Wikisource, textbook-curated selection).
- **Phase 3 — scale track-by-track**, fleet-driven (folk is the in-flight pilot), coordinated with the
  main orchestrator.

## Role / boundary
This system spans all tracks — beyond the folk lane. **I build the reusable engine + manifest + prove it
on folk and a small PD lit slice (my buildable scope, via PRs).** The full cross-track hosting rollout
across 1,270 modules is a **fleet program this design enables**, coordinated with the main orchestrator —
not unilateral. No commits to `main`; everything via PRs.

## Files
**Reuse:** `scripts/readings/generate_readings.py` (engine + gates), `scripts/generate_mdx/reading_links.py`
(linking), `scripts/generate_mdx/converters.py` + `core.py` (rendering), `scripts/rag/scrape_wikisource.py`
(per-work PD fetch), `site/src/content.config.ts` (readings schema), `data/sources.db`
(`textbook_sections` + `literary_texts`).
**New:** `scripts/readings/primary_text_demand.py` (manifest); textbook-curation lookup + author-death PD
table + clean-text multi-source resolver (in/around `generate_readings.py`); a general primary-reading
MDX converter.

## Verification
- **Manifest:** run on all plans → JSON with N distinct works + per-work module coverage; spot-check a
  few entries against their plans.
- **Resolver:** for 3–5 demanded works (folk PD, lit PD, in-copyright) show textbook-curation hit +
  clean-text source + rights class + `verify_quote` raw result.
- **Hosting:** generate the reading(s) for **one lit module** end-to-end, run the astro build, eyeball
  the rendered `/readings/{slug}/` page + the in-lesson link (REAL artifact, not gate-green).
- **Tests:** unit tests for the manifest scan, the rights classifier (author-death edge cases:
  Franko 1916 PD vs Stus 1985 in-copyright), and the resolver's source-priority + excerpt boundary.
