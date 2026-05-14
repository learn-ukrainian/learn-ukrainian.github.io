---
date: 2026-05-14
session: "Long full-day session — corpus completion arc CLOSED end-to-end. Five major corpus PRs landed (Pohribnyi, Antonenko full book, school-textbook orphan backfill, ESUM vols 2-6, ESUM parser generalization). One follow-up issue filed (#1991, since closed by the parser fix). User direction at session close: build a public etymology feature (static A+B), available from the beginning of the curriculum, not gated by level."
status: ok
main_sha: dc4050c2b8
main_green: true
open_prs: [1873]  # stale dependabot starlight bump, blocked on Frontend
active_dispatches: 0
agents: [claude, codex, gemini]
worktrees_open: 4  # main + codex-interactive (detached) + 3 unmerged-WIP from earlier sessions (bakeoff, writer-prompt-tune, codex pass2)
ci_notes: "All 6 corpus PRs this session passed blocking checks. Advisory `review / review` (Gemini Dispatch) failed on each — non-blocking per #M-0.5. Main fast-forwarded cleanly through 5 corpus commits + this handoff."
filed_today: [1991]
merged_today: [1986, 1987, 1988, 1989, 1990, 1992]  # plus #1985 from earlier session-final-handoff
closed_today: [1991]  # auto-closed by #1992 (parser fix delivered)
next_p0: |
  Design + implement the public etymology feature per the new user
  direction. Two shapes, both required, both ready from the start of
  the curriculum:

    A — per-word static reference pages at /etymology/<lemma-slug>
        (~29k pages, one per ESUM lemma).
    B — interactive cognate-tree explorer (single-page client-side
        tool with a shipped JSON dataset).

  HARD CONSTRAINT: the public site is github.io static hosting. NO MCP
  at runtime; NO server-side API calls. EVERYTHING that consumes ESUM
  data must run at BUILD time and emit static artifacts.

  Next session = plan + implement. Brief below has data shapes, stack
  notes, design questions, and the explicit user direction so the
  planner can hit the ground running.
---

# Brief — 2026-05-14 — etymology feature handoff (corpus arc closed; UI arc begins)

> Predecessor chain (this calendar day, in order):
> - `2026-05-14-corpus-completion-night-brief.md` (overnight)
> - `2026-05-14-content-indexing-audit-brief.md`
> - `2026-05-14-corpus-day-session-final-brief.md`
> - `2026-05-14-c4-pohribnyi-shipped-brief.md`
> - **THIS brief** — closes the corpus arc, opens the public-UI arc

## TL;DR — what shipped today, and what's next

**Today (6 PRs + 1 issue):**

| PR | What | Result |
|---|---|---|
| #1986 | Pohribnyi 1992 28-page pronunciation book OCR + ingest | textbooks +28 |
| #1987 | C4 Pohribnyi handoff doc | docs |
| #1988 | Antonenko-Davydovych «Як ми говоримо» full book (169 pp.) | textbooks +169 |
| #1989 | 280 school-textbook front-matter orphan backfill | textbook_sections +242, 0 orphans system-wide |
| #1990 | ESUM vols 2-6 fetched from archive.org + parsed + loaded | esum_etymology +1,105 (5,517 total) |
| #1992 | ESUM parser generalized: alphabet, body-start, page-running-header look-ahead, first-word lemma | **esum_etymology now 29,171 entries** (5.3× the original) |
| #1991 | Filed for parser undercount, closed by #1992 | — |

**Corpus state at handoff (canonical `data/sources.db`):**

```
textbooks                25,714
textbooks_fts            25,714   (in sync ✓)
textbook_sections         7,250   (0 orphans across ANY source_file ✓)
ukrainian_wiki           22,385
wikipedia                 1,026
literary_texts          137,688
external_articles         1,205
esum_etymology           29,171   (was 4,412 at session start)
esum_etymology_meta      29,171
9 dictionaries           ~600,000 total rows
VESUM (separate DB)    6,691,276 forms
```

GDrive `learn-ukrainian-data/sources.db` re-synced post-ESUM-parser-fix
(1.65 GB, byte-identical to local). All JSONLs synced.

## User direction at session close (load-bearing for next session)

User question: *"or we could turn it into a web content maybe? i like ethymology"*

Orchestrator opinion: yes, both per-word static pages (A) and
interactive explorer (B). User response:

> *"but you have to remember we cannot call mcp on github.io, so we
> will have to build a static content. Unless you have better idea.
> lets do both A and B and lets have it available from the begining.
> When ppl come back to refresh maybe it will not be a cognotivie load
> anymore, talking from my own experinece. Lets do a session hanfoff
> and in the next sesssion you can plan and implement it."*

Three hard pins from that statement:

1. **Static-only.** No MCP / no API / no server-side query at runtime.
   Everything runs at BUILD time, emits HTML / JSON / static assets.
2. **Both A and B required.** Not "ship A then B later" — both ready
   at first ship.
3. **Available from the beginning of the curriculum, NOT level-gated.**
   User personal UX rationale: *"when ppl come back to refresh maybe
   it will not be a cognitive load anymore, talking from my own
   experience"* — etymology is intrinsically motivating, and seeing it
   day 1 (even before you understand most of it) seeds curiosity. The
   earlier "A1-A2 skip, B1+ optional" tier model the orchestrator
   proposed mid-session is **superseded** — etymology surfaces at every
   level, the user designs UX around it being always-available.

## Design state — A: per-word static pages

**Path:** `/etymology/<slug>` on the public Starlight site.

**Data source:** `esum_etymology` + `esum_etymology_meta` in
`data/sources.db` — 29,171 lemmas, each with:
- `lemma` (TEXT, lowercased canonical headword)
- `vol` (1-6)
- `page` (page number in source)
- `etymology_text` (full body — typically 200-2000 chars of paragraph
  prose containing cognates, Proto-Slavic root, borrowing path, citations)
- `cognates` (JSON array of language abbreviation markers like `псл.`,
  `гр.`, `тур.`, `перс.`)

Cross-link material:
- **Antonenko `style_guide`** (342 entries) — for headwords that the
  reviewer flags as Russianism / calque concerns. Decolonization
  context.
- **Грінченко** (`grinchenko`, 67,275 entries) — pre-Soviet attestation
  for heritage-defense.
- **slovnyk.me** — modern definition baseline (preferred over СУМ-11
  for ideologically-loaded terms, see #M-4 sovietization caveat).

**Build-time pipeline (proposed):**

```
scripts/etymology/
    extract_static_pages.py    Reads sources.db; emits one MDX file
                               per lemma into
                               starlight/src/content/docs/etymology/.
                               Wires cognate cross-links if the cognate
                               appears in our corpus.
                               Cites vol + page from esum_etymology_meta.

    extract_index.py           Generates the A-Z browsing index +
                               search-data JSON the explorer consumes.
```

**Open design questions for next-session plan:**

- **Slug strategy.** Diacritics + stress marks complicate URL safety.
  Strip stress (`сéрце` → `serce`) and use ASCII-only slugs? Or keep
  Cyrillic in the URL (Starlight + modern browsers handle this)?
- **Build-time cost.** 29k MDX files at ~1-3 KB each = ~50-90 MB of
  build artifacts. Astro/Starlight handles this fine but the
  `astro build` step will get longer. Verify before merging.
- **Cross-link coverage.** A cognate in ESUM (e.g. "псл. *sьrdьce")
  isn't a headword we can link to; only Ukrainian headwords link to
  their own pages. Decide: link only Ukrainian cognates, OR add a
  "ETYM:cognate" tag that opens the etymology entry where the cognate
  is mentioned.
- **СУМ-11 sovietization opt-out.** Per #M-4, СУМ-11 has 7,152
  Sovietized entries. The etymology page is for ETYMOLOGY, not modern
  definition, so СУМ-11 risk is mostly contained — but if we surface a
  "modern definition" sidebar, route to slovnyk.me + Грінченко first.

## Design state — B: interactive cognate-tree explorer

**Path:** `/etymology/explore` (single page).

**Mechanics:** ship the full ESUM dataset as a static JSON bundle
(probably 5-10 MB compressed). Client-side JS does:
- Search by lemma (typeahead)
- Render cognate tree: Proto-Slavic root in the center, sister-language
  cognates as branches (Russian, Polish, Czech, Slovak, Bulgarian,
  Serbian/Croatian, Slovenian, Belarusian)
- Click a cognate to recenter the tree on that word's own etymology
  (if it's in our corpus)
- "Decolonization context" callouts when the lemma has heritage flags

**Data shape (sketch):**

```json
{
  "lemmas": {
    "серце": {
      "vol": 5, "page": 271,
      "ie_root": "*kerd-",
      "proto_slavic": "*sьrdьce",
      "cognates": {
        "ru": "сердце", "pl": "serce", "cs": "srdce",
        "bg": "сърце", "lt": "širdìs",
        "gr": "καρδία (kardia)", "la": "cor",
        "de": "Herz", "en": "heart"
      },
      "heritage_flags": [],
      "antonenko_note": null
    }
  }
}
```

The above sketch is OPTIMISTIC — extracting cognates as structured
language→form pairs from the OCR text requires parsing more carefully
than the current ingester does. May need an LLM pass (build-time, not
runtime) to extract structured cognate tables from each etymology
paragraph. Decide in plan phase: structured extraction (richer UI,
expensive one-time build) vs raw-text display with a heuristic
cognate-language-marker highlight (cheaper, less polished).

Tech stack candidates:
- `frontend-design` skill (in our tooling) — for the styled component
- `playground` skill — for the interactive explorer shape
- D3.js / Cytoscape.js — for the cognate tree visualization
- Lunr / FlexSearch — for client-side typeahead over 29k lemmas

**Open design questions for B:**

- **Bundle size.** 29k entries × ~500 bytes (raw etymology text) ≈
  15 MB JSON. Gzipped maybe 4-5 MB. That's heavy for a single page.
  Options: lazy-load by first-letter, or pre-compute a compact
  "cognate-summary" view for the explorer and keep the full
  etymology_text for the per-lemma pages only.
- **Tree shape.** Proto-Slavic root → cognates is the natural shape.
  But ESUM also tracks Indo-European parents, borrowing paths, and
  semantic shifts. Decide layer-by-layer rendering vs flat
  language-grid.
- **Mobile UX.** Cognate trees don't fit on mobile naturally. Either
  a vertical timeline rendering or fallback to per-cognate cards.

## Implementation sequencing (recommended)

The user said "do both" — concrete order to make both ship on day 1:

1. **Plan phase (next session, ~30-60 min):**
   - Run a Decision Card or `ab discuss etymology-static-2026-05-15
     --with codex,gemini` on the structured-extraction vs raw-text
     trade-off (it's the load-bearing decision).
   - Pick slug strategy (ASCII or Cyrillic).
   - Pick bundle strategy for B (single-page vs lazy-load).

2. **Phase 1 — static page generator (~2-4 hours):**
   - `scripts/etymology/extract_static_pages.py` — reads sources.db,
     emits MDX. Idempotent on lemma. Cross-link table built in same pass.
   - Run on full 29k corpus, verify Astro build succeeds.
   - Add to public navigation.

3. **Phase 2 — search index + landing page (~1-2 hours):**
   - A-Z browsing page
   - Client-side Lunr/FlexSearch over lemma + first-line-of-etymology
   - Style with `frontend-design` skill if needed

4. **Phase 3 — interactive explorer (~3-6 hours):**
   - Cognate extraction pass (LLM-assisted if going structured; else
     regex on language markers)
   - Bundle build into `/etymology/explore.json`
   - Single HTML page with D3 + search + click-to-recenter
   - Mobile-responsive

5. **Phase 4 — heritage-defense crossover (~1-2 hours):**
   - For each Antonenko `style_guide` entry that has an ESUM match,
     surface a "calques / Russianisms" callout on the etymology page.
   - For Грінченко-only words (pre-Soviet attestation), add a
     "heritage status" badge.

## Where to start the next session

1. Read this brief.
2. Read the relevant existing docs:
   - `claude_extensions/rules/mcp-sources-and-dictionaries.md` —
     the canonical MCP source tools list (which **maps directly** to
     what's queryable at BUILD time even though we won't query at
     runtime).
   - `docs/best-practices/track-architecture.md` — Starlight site
     layout.
   - `starlight/src/content/docs/` — how existing pages are organized.
3. Decide the load-bearing structured-vs-raw extraction question via
   Decision Card or multi-agent discussion.
4. Start Phase 1 (static page generator) — that unblocks every later
   phase.

## Carry-over from this session

- **PR #1873** (dependabot starlight 0.39.2) still open since 2026-05-11,
  blocked on Frontend (build + vitest) failure. Pre-existing; not
  blocking etymology feature work, but related (etymology pages live
  in the same Starlight site).
- **3 unmerged WIP worktrees still on disk** — pending user decision
  from prior session brief:
  - `.worktrees/dispatch/claude/bakeoff-2026-05-12-night`
  - `.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13`
  - `.worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13`
- **MEMORY.md at 150/150 cap** — no new entries this session.
- **6 stale DB backups on disk** — none, just the post-Antonenko one,
  which is the latest and should be kept until the next major DB write.
  Actually: `data/sources.db.bak-20260514-150259-pre-antonenko-full` —
  pre-Antonenko backup. Post-orphan-backfill + post-ESUM-parser-fix
  backups were rolled over. Keep the one we have for one more session.

## Pre-commit backup files (1.5 GB each, ungitignored, untracked)

```
data/sources.db.bak-20260514-150259-pre-antonenko-full
```

Just one remaining. Earlier backups (pre-channel-id-fix, pre-verbs,
pre-section-backfill, pre-orphan-backfill, pre-Pohribnyi) all cleaned.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier
handoffs". MD-only per #M-2 ai→ai.*
