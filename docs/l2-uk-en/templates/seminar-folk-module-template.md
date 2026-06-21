# Seminar Folk Module Template

**Purpose:** Reference template for building **seminar FOLK** modules (Ukrainian folklore/oral-tradition
seminar track #2836 — calendar ritual, dumas, beliefs, charms, song genres, etc.).
**Based on:** the production-grade exemplar `curriculum/l2-uk-en/folk/koliadky-shchedrivky/` (PR #3648).
**Read first (the law this template operationalizes):** `docs/folk-epic/EXEMPLAR-STANDARD.md` (folk
production standard + ship checklist) and `scripts/build/phases/linear-write-seminar-folk-rules.md`.
**Track sibling:** `lit-module-template.md` (the LIT seminar uses the same template concept).

<!--
TEMPLATE_METADATA:
  required_sections:
  - Розминка
  - Конфліктна карта
  - Читання
  - Аналіз
  - Дискусія
  - Підсумок
  - Словничок ключових термінів
  - Питання для самоперевірки
  pedagogy: Seminar
  min_word_count: 5000
  required_callouts:
  - primary-reading
  - myth-box
  - high-culture-bridge
  description: Seminar folk modules are long-form full-Ukrainian analytical seminars built ON verbatim, corpus-verified folk primary texts.
-->
---

## ⚠️ Seminar FOLK ≠ C1 Folk-Culture (core)
This is the **seminar** folk track, NOT the core `c1-folk-culture-module-template.md`. Differences:
- **Full Ukrainian immersion** — no English scaffolding, no PPP grammar drills. Graduate-seminar register.
- **Built on primary texts** — the module *teaches from* verbatim folk originals (dumas, колядки, замовляння),
  not from generic descriptive prose about the culture.
- **Decolonial analytical stance** — myths corrected with sourced evidence; honest about dark motifs.
- **Folk experiential text-layer components** (below), not the generic activity mix.

## Quick Reference Checklist (the ship gate — full version in EXEMPLAR-STANDARD.md §6)
- [ ] ≈5,000+ words of grounded Ukrainian seminar prose; the section shape below
- [ ] **≥4 `:::primary-reading` boxes**, each wrapping a verbatim folk original that `verify_quote`s under
      its attributed author (corpus-bound — embed only what the corpus has; never backfill from memory)
- [ ] ≥1 `:::myth-box`, ≥1 `:::high-culture-bridge` where evidence supports
- [ ] Folk activity families (`ritual-sequencing`, `variant-comparison`, `motif-formula`, `performance`)
- [ ] `role: reading` resource → public allowlisted URL + a one-line task (see "How students read", below)
- [ ] Prose + resource titles VESUM-clean (`vesum_verified` green); archaic forms ONLY inside primary-reading
- [ ] `verify_shippable folk <slug>` GREEN (python_qg + assemble_mdx + mdx_render); CI astro build green
- [ ] Corpus-hammer done (human read + independent `verify_quote` of every embedded fragment)
- [ ] Site MDX regenerated via `assemble_mdx` and committed in the same PR

## Section structure (what koliadky-shchedrivky uses)
| # | Section | Does | Rough words |
|---|---|---|---|
| 1 | **Розминка** | Hook on a primary text; pose the module's central question | 250–450 |
| 2 | **Конфліктна карта** | Frame the live scholarly debate as a debate (name / text / rite); teach claim-type separation | 600–900 |
| 3 | **Читання** (1–2) | Guided close-reading of the verbatim primary text(s) with an explicit read-model (name situation → extract action → state conclusion, each tied to a line) | 700–1100 each |
| 4 | **Аналіз** | Poetics + ritual function (the thesis: every device is applied magic, not ornament) | 500–800 |
| 5 | **Дискусія** | "What survived & why" — competing hypotheses side by side; honest treatment of dark motifs (`:::caution`); modern (2022–2025) relevance | 500–800 |
| 6 | **Підсумок** | Return to the opening question; the reader now answers with evidence | 300–500 |
| 7 | **Словничок ключових термінів** | Key terms consolidated (each VESUM-verified) | — |
| 8 | **Питання для самоперевірки** | Source-grounded self-check questions | — |

Optional `## Поглиблення:` deep-dive subsections after Підсумок (koliadky uses Вертеп, the winter-cycle
calendar, genre-in-context). Insert `<!-- INJECT_ACTIVITY: act-N -->` at natural points for inline activities.

## The folk components (custom container directives → MDX islands)
| Directive | Renders as | Use for |
|---|---|---|
| `:::primary-reading` | 📜 "Читаємо першоджерело" box (word-count-excluded) | Every verbatim corpus-verified folk original |
| `:::myth-box` | claim-vs-truth (both sourced) | Decolonial correction of an imperial / Soviet / romantic myth |
| `:::high-culture-bridge` | ≥2 nodes + note | Folk-form → opera / literature / world-circulation connection |
| `:::note` / `:::caution` / `:::info` | Starlight admonitions | Asides, honest cautions, external-resource panels |

`:::primary-reading` wraps a Markdown blockquote + an `— attribution` line. `:::myth-box` /
`:::high-culture-bridge` take a YAML payload. Converter:
`scripts/generate_mdx/converters.py::convert_folk_content_blocks`. Activity placement: inline via
`INJECT_ACTIVITY` markers; every activity WITHOUT a marker is auto-appended as a "Вправи" workbook section
(not dropped) — make the inline/workbook split deliberate.

## Corpus-hammer law (the part that bites — see EXEMPLAR-STANDARD.md §3 for the full rule)
- Box only fragments that `verify_quote` **match under their attributed author**. Folk songs collected by a
  named scholar verify under THAT collector (e.g. dumy under `Драгоманов`/`Костомаров`, Carpathian
  cosmogonic colядка under `Народна творчість`/ukrlib) — attribute honestly to the recorder; do NOT
  relabel a collector-recorded text as anonymous «Народна творчість» if it only verifies under the collector.
- A scholarly secondary quote (e.g. Чижевський on duma poetics) is NOT a folk-primary text — leave it as a
  normal blockquote, do NOT wrap it in `:::primary-reading`.
- **≥4 is corpus-bound:** embed only the verified fragments the corpus has; if fewer than 4, fill the word
  budget with grounded exposition, never by backfilling quotes from memory (not even famous ones).
- The `vesum_verified` gate scans PROSE incl. incipits in «лапки»: archaic forms (`нащада`, …) fail VESUM
  there — keep archaic forms ONLY inside `:::primary-reading`; use modern codified forms in prose.

## How students find & read the originals (student-facing access)
A learner reaches the primary texts two ways — design BOTH:
1. **On-site, inline:** the `:::primary-reading` boxes render the verbatim original **excerpt** directly in
   the lesson ("📜 Читаємо першоджерело"). This is the guaranteed, always-present way the student reads the
   actual text we analyse.
2. **Off-site, full work:** the `role: reading` resource (Resources tab → "📖 Читай першоджерела:") is a
   clickable link to a **public allowlisted** source (`data/primary_text_sources.yaml`:
   `uk.wikisource.org`, `litopys.org.ua`, `ukrlib.com.ua`, `uk.wikipedia.org`) + a one-line task.
   - **Prefer a real full-text page** (`uk.wikisource.org` / `ukrlib.com.ua`) so the student can read the
     COMPLETE work, not just our excerpt. The `uk.wikipedia.org` overview article is only the guaranteed
     FLOOR — use it when no clean full-text URL resolves, but treat that as the weaker case to improve.
   - The internal corpus (`data/sources.db`, e.g. Костомаров/Драгоманов/Грушевський) is **AI-facing only**
     (build-time verification) and is NEVER a student link — internal `wiki/...` paths are rejected by the gate.

## Folk activities (`activities.yaml`)
Prefer `ritual-sequencing` (#42), `variant-comparison` (#43), `motif-formula` (#44), `performance` (#45)
where the corpus supports them, over generic quiz/match-up. Do NOT emit `audio-block`, `symbolic-decode`,
or `aural-genre-id` (deferred). `peer_review_guidelines` MUST be a YAML **list**, never a bare string.

## Common pitfalls (real ones, learned on koliadky/dumy)
- **Mis-attributed variant** — a from-memory opening relabelled as another song's title. (Caught on koliadky.)
- **Stitched excerpt** — jumping across non-contiguous lines and presenting it as one quote. Quote a
  contiguous corpus passage; restore the build-up that makes the payoff land.
- **Spurious `packet_chunk_id`** — scholarly `role: textbook` sources sharing a folk text's chunk id. Each
  textbook resource must carry its OWN plan chunk id (or `notes`), not a copy of the primary text's.
- **Ghost source** — an `[S#]` that fails `verify_quote`. Remove the source AND the sentence relying on it.
- **Reading-task = Wikipedia overview** when a wikisource/ukrlib full text exists — upgrade it.
- **Infra/code defects are NOT yours** — a pipeline/gate/converter bug (e.g. a YAML field rendered wrong)
  goes to the **infra Claude** (root-cause + file/flag), not a self-fix. You drive folk CONTENT.

## Definition of Done & reference
Run `.venv/bin/python -m scripts.build.verify_shippable folk <slug>` (add `--astro-build` for the catch-all),
then corpus-hammer, then `handoff_ready --pr <N>`. **Reference module:** `koliadky-shchedrivky` — read it
alongside this template. Full ship checklist: `docs/folk-epic/EXEMPLAR-STANDARD.md §6`.

> **Generalizing to other seminars:** this template is the folk instance of the seminar template concept.
> The next sibling to author is **`seminar-bio-module-template.md`** (BIO epic #2309), then HIST / ISTORIO /
> OES / RUTH; LIT already has `lit-module-template.md`. Each keeps the seminar shape + corpus-hammer law and
> swaps the domain specifics (BIO: a person's life + works + reception, sourced from the bio dossier).
