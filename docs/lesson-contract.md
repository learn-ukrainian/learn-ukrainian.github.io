# Lesson Contract — Curriculum Reboot (#1577 Phase 0 draft)

> **Status:** DRAFT v3 — signed off by Codex + Gemini in `architecture` channel
> thread `6de2be4789394536abdb6356cd5bb006` (round 2, both `[AGREE]`).
> Open questions §7 resolved per panel consensus. Activity matrix in §3.4
> aligned with `docs/best-practices/activity-pedagogy.md` per Codex
> finding. Component count corrected per Codex finding.
>
> v3 corrections from v2:
> - §3.4 activity types fully aligned with `docs/best-practices/activity-pedagogy.md`
>   (was contradicting it on Transcription, EssayResponse, Observe,
>   ReadingActivity, MarkTheWords, Classify, Select)
> - §3 component-count line corrected: 50 `.tsx` + 5 `.astro` overrides
>   = 55 files, minus `utils.tsx` = 54 non-utility components
> - §7 open questions resolved inline as policy
>
> v2 from v1: B1+ immersion is uniform 100 % Ukrainian across every tab
> body, with the **Словник (Tab 2) translation column + idiom/expression
> notes** as the ONLY sanctioned English at B1+. The stale `b1-m01-05`
> band in `scripts/config.py` does not exist in this contract — Phase 2
> config audit cleans up the file. Tab 2 ``VocabCard`` stays slim per
> EPIC #1581 (site-wide dictionary section is separate from per-module
> Словник).
>
> **Purpose.** This document is the single source of truth for the SHAPE of
> a published lesson. The North Star says what we're shipping and why; this
> says what artifacts the pipeline must produce, what tabs the published
> MDX must have, and which Starlight components live in which tab. Phase 3
> formalizes the per-component prop schemas in YAML; this doc defines the
> structural skeleton Phase 3 will fill in.
>
> **Scope.** A1 + A2 + B1 MVP (218 modules). Higher-level
> (B2 / C1 / C2 / seminar / PRO) component support is described where
> relevant but the MVP does not exercise it. The seminar-only / C-only
> components are noted as "out-of-scope-for-MVP."

---

## 1. Source artifacts the writer produces

Every module's authoring output is a small set of files at
`curriculum/l2-uk-en/{level}/{slug}/`:

| File | Purpose | Schema authority |
|---|---|---|
| `module.md` | Theory prose (lesson narrative) — Tab 1 source | Plan section structure + Starlight `:::tip` callouts + `<!-- INJECT_ACTIVITY: {id} -->` placeholders + blockquoted dialogues |
| `activities.yaml` | Typed activity definitions — Tab 3 + inline-Tab-1 | `docs/ACTIVITY-YAML-REFERENCE.md`. Bare list at root, no `activities:` wrapper. Each item has `id`, `type`, `instruction`, type-specific payload |
| `vocabulary.yaml` *(or inline)* | Vocab list — Tab 2 source | Per `docs/best-practices/vocabulary-activity-standards.md`. Each entry: lemma + translation + part-of-speech + example sentence |
| `resources.yaml` *(or inline in `module.md`)* | External citations + media — Tab 4 source | Each entry: title + author + URL + access date + role (textbook/wiki/audio/video) |

Pipeline inputs the writer DOES NOT produce:

- **Plan YAML** — lives at `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` (sacred, pre-existing, immutable mid-build per ADR-007 / non-negotiable rule §7).
- **Wiki packet** — context the writer reads but does not author. Owned by Phase 5+ wiki retrieval.
- **Annotation pass** — stress marks added deterministically AFTER review by `ukrainian-word-stress`, not by the writer.

## 2. Published MDX shape

The pipeline's MDX assembler (today: `scripts/generate_mdx/core.py:267-364`)
produces ONE `.mdx` file at `starlight/src/content/docs/{level}/{slug}.mdx`
with:

- **Frontmatter:** `title`, `description`, `sidebar.order`, `sidebar.label`,
  optional `pipeline`, optional `build_status`, optional `draft`. Schema
  extension declared in `starlight/src/content.config.ts`.
- **Imports block:** every component used in the body, imported from
  `@site/src/components/...`.
- **One `<Tabs syncKey="module-tab">` block** with **exactly four
  `<TabItem>` children** in this order. Tab labels are the Ukrainian
  strings shown to learners; the English labels in the table are the
  canonical English aliases used throughout this contract:

| # | EN label | UK label (in code) | UK label (in handoff text) | What it contains |
|---|---|---|---|---|
| 1 | Lesson | **Урок** | Урок | Theory prose from `module.md` after activity-id substitution and shared transforms |
| 2 | Vocabulary | **Словник** | Словник | Vocabulary cards / flashcard deck / phrase table from `vocabulary.yaml` |
| 3 | Activities | **Вправи** | **Зошит** *(handoff says Зошит — code says Вправи — open Q1 below)* | All activities from `activities.yaml`, rendered as their typed components |
| 4 | Resources | **Ресурси** | Ресурси | External citations, source attribution, embedded video links |

The 4-tab structure is fixed; learners always see all four labels even
if a tab is empty (the empty state is a localized "No vocabulary for
this module" / "Немає словника для цього модуля" message — already
implemented at `core.py:283-302`).

## 3. Component inventory — 1:1 mapping

55 React/Astro component files exist under `starlight/src/components/`
(50 `.tsx` plus 5 `.astro` overrides); excluding `utils.tsx` leaves 54
non-utility component files. The mapping below assigns each
LESSON-SCOPE component to a tab and notes which CEFR level first
introduces it. Site-framing components (5) and utility wrappers (3) are
out of lesson scope.

### 3.1 Out of lesson scope (no MDX usage by writer)

| File | Role |
|---|---|
| `overrides/Footer.astro` | Site footer override |
| `overrides/Head.astro` | `<head>` override (analytics, fonts) |
| `overrides/Header.astro` | Top nav override |
| `overrides/PageTitle.astro` | Title override |
| `overrides/Sidebar.astro` | Sidebar override |
| `Home.tsx` | Site landing page |
| `LevelLanding.tsx` | Per-level overview page (e.g. `/a1/`) |
| `LiveStatus.tsx` | Build-status indicator (admin-facing) |
| `ActivityHelp.tsx` | UX helper rendered inside other activity components |
| `ActivityPlaceholder.tsx` | Stub rendered when an activity id fails to resolve |
| `utils.tsx` | Shared helpers (no JSX export) |

### 3.2 Tab 1 — Урок (Lesson) — narrative + theory

These components appear inside the lesson prose, either authored
directly in `module.md` or substituted in via the
`<!-- INJECT_ACTIVITY: {id} -->` mechanism (which pulls a typed
activity from `activities.yaml` and renders it inline AT that point in
the prose).

Always-prose-only, authored directly in `module.md`:

| Component | Used at | Purpose |
|---|---|---|
| `RuleBox.tsx` | A1+ | Boxed grammar rule with title + body |
| `DialogueBox.tsx` | A1+ | Formatted two-or-more-speaker dialogue with optional translations |
| `YouTubeVideo.tsx` | A1+ | Embedded YouTube link (auto-thumbnail in lesson via `embed_youtube_video_links()`) |

Markdown-native, no component — authored as Starlight `:::tip` /
`:::note` / `:::caution` blocks (heavily used in the testbed reference
module).

Inline-renderable activity types (also appear in Tab 3 — see §3.4):
all of §3.4 components can appear inline in Tab 1 by referencing their
`id` from `activities.yaml`.

Higher-level theory components (out-of-scope for A1+A2+B1 MVP, present
in repo for seminar / B2+ tracks):

| Component | First level | Purpose |
|---|---|---|
| `AuthorialIntent.tsx` | C1+ / seminar | Literary analysis prompt |
| `MythBuster.tsx` | B2+ / seminar | Debunks Russian-imperial myth with sourced evidence |
| `ComparativeStudy.tsx` | B2+ / seminar | Ukrainian-vs-other-Slavic comparison |
| `CriticalAnalysis.tsx` | C1+ / seminar | Literary criticism task |
| `DialectComparison.tsx` | B2+ / seminar | Western/Standard/Закарпаття etc. |
| `EtymologyTrace.tsx` | B2+ / seminar | Word-origin chain (note: distinct from EPIC #1581 dictionary etymology — this component is a teaching task) |
| `PaleographyAnalysis.tsx` | C1+ / seminar | Old-script reading (Cyrillic historical) |
| `SourceEvaluation.tsx` | B2+ / seminar | Primary-source criticism |
| `TranslationCritique.tsx` | C1+ / seminar | Translation analysis |

### 3.3 Tab 2 — Словник (Vocabulary)

| Component | Used at | Purpose |
|---|---|---|
| `FlashcardDeck.tsx` | A1+ | Stack of `VocabCard`s with deck-level controls (shuffle, hide translation) |
| `VocabCard.tsx` | A1+ | Single flashcard: Ukrainian + translation + IPA + example sentence + audio (optional) + cross-link to dictionary entry |
| `PhraseTable.tsx` | A1+ | Table of phrase + literal gloss + idiomatic gloss + register tag |

**Tab 2 design principle (per EPIC #1581):** stay slim. Per-module
``VocabCard`` shows translation + pronunciation hint + an example
sentence + an optional ``→ повне визначення`` cross-link to the
site-wide dictionary entry (``/dictionary/{lemma}/``). Etymology,
inflection tables, idiom families, and full definitions live in the
dictionary section, not on the flashcard. This separates LEARNING
(focused, scoped, drillable) from REFERENCE (browse, depth,
exploration).

**Tab 2 source data** comes from `vocabulary.yaml`. Vocabulary entries
that appear in Tab 1 prose (e.g. inline glossing) are NOT separately
listed in Tab 2 unless they're vocabulary the learner is expected to
take away.

**Critical immersion carve-out:** Tab 2 carries English translations
in its translation column, AND English explanation notes for idioms /
expressions where useful. **This is the ONLY sanctioned English at
B1+.** It is a structural feature of the vocab tab (paired-translation
flashcards), not English-in-prose. Python QG must NOT count Tab 2
English content against the B1+ "100 % Ukrainian module body" rule.

### 3.4 Tab 3 — Вправи (Activities)

> **Authority:** [`docs/best-practices/activity-pedagogy.md`](best-practices/activity-pedagogy.md)
> §3 type → level matrix and `scripts/pipeline/config_tables.py`
> `ACTIVITY_CONFIGS` are the single source of truth for which activity
> types are allowed at which level and in which placement
> (inline / workbook / both). This contract DOES NOT redefine the
> matrix — it only enumerates the React components that render the
> matrix's `type` strings. Any conflict with `activity-pedagogy.md` is
> resolved in that doc's favor and this contract is amended.

`activity_repair.py` (`scripts/build/activity_repair.py`) deterministically
drops out-of-allowlist activities and corrects inline/workbook misplacement
based on `INLINE_ONLY_TYPES` and `WORKBOOK_ONLY_TYPES`. The writer never
sees "respect the allowlist" instructions; the prompt ships only the allowed
set and the repair step fixes drift.

#### 3.4.a Activity components in MVP scope (A1 + A2 + B1)

The MVP exercises these 19 active components. Per-level placement
(inline / workbook / both) is governed by `ACTIVITY_CONFIGS` and is
not duplicated here.

| Component | `type` string | A1 | A2 | B1-core | Notes |
|---|---|---|---|---|---|
| `Quiz.tsx` | `quiz` | both | both | both | Backbone comprehension check; all levels |
| `FillIn.tsx` | `fill-in` | both | both | both | Backbone short-answer; all levels |
| `MatchUp.tsx` | `match-up` | both | both | both | Pair items between two columns; survives through C2 (Principle 1) |
| `GroupSort.tsx` | `group-sort` | both | both | both | Multi-bin sort; comprehension, not gamification |
| `TrueFalse.tsx` | `true-false` | both | both | both | Statement → true/false |
| `OddOneOut.tsx` | `odd-one-out` | both | both | workbook | Puzzle-gamification fades by B1 (Principle 1) |
| `Order.tsx` | `order` | both | both | both | Reorder items in correct sequence; ends at B1 |
| `Unjumble.tsx` | `unjumble` | both | both | both | Reorder shuffled words into a correct sentence; ends at B1 |
| `ErrorCorrection.tsx` | `error-correction` | workbook | both | both | Find + fix the error |
| `MarkTheWords.tsx` | `mark-the-words` | — | both | both | Click every word matching a criterion; **starts at A2** (not A1) |
| `Cloze.tsx` | `cloze` | — | workbook | workbook | Multi-blank passage, 14+ gaps; workbook-only |
| `Translate.tsx` | `translate` | — | workbook | workbook | EN↔UK translation; workbook-only; ends at C1 |
| `GrammarIdentify.tsx` | `grammar-identify` | — | — | both | Name the grammatical category; metalinguistic earns in at B1 (Principle 3) |
| `HighlightMorphemes.tsx` | `highlight-morphemes` | — | — | both | Mark prefix / root / suffix / ending; metalinguistic earns in at B1 (Principle 3) |
| `EssayResponse.tsx` | `essay-response` | — | — | workbook | 50–500 word free writing; **B1+ workbook** (Principle 4) |

Phonetics-only components (A1 only — gone forever from A2 onward per
Principle 2):

| Component | `type` string | Placement |
|---|---|---|
| `WatchAndRepeat.tsx` | `watch-and-repeat` | A1 inline only |
| `LetterGrid.tsx` | `letter-grid` | A1 inline only |
| `ImageToLetter.tsx` | `image-to-letter` | A1 inline only |
| `DivideWords.tsx` | `divide-words` | A1 inline + workbook |
| `CountSyllables.tsx` | `count-syllables` | A1 inline + workbook |
| `PickSyllables.tsx` | `pick-syllables` | A1 inline + workbook |
| `Anagram.tsx` | `anagram` | A1 workbook only |
| `Observe.tsx` | `observe` | A1 + A2 only (NOT B1+, despite being a "guided observation" component) |

#### 3.4.b Activity components OUT of MVP scope

Components shipped in the repo for B2+ / seminar / philological tracks.
Writer prompts at A1 / A2 / B1 must NOT emit these `type` strings;
Python QG hard-rejects them per §5.

| Component | `type` string | Allowed at | Notes |
|---|---|---|---|
| `ReadingActivity.tsx` | `reading` | B2+ workbook, all seminars workbook | 200+ word passage + comprehension; **NOT A2** despite the name "ReadingActivity" |
| `Transcription.tsx` | `transcription` | OES, RUTH only | Old-orthography → modern; philological track-gated (Principle 7) |
| `Debate.tsx` | `debate` | C2, LIT only | Multi-turn argumentative exchange |
| `AuthorialIntent.tsx` | `authorial-intent` | C2, BIO, LIT | Why did the author write this way |
| `ComparativeStudy.tsx` | `comparative-study` | C1+, all seminars except early HIST | Multi-text comparison |
| `CriticalAnalysis.tsx` | `critical-analysis` | C1+, all seminars | Argumentative response (Principle 6) |
| `DialectComparison.tsx` | `dialect-comparison` | RUTH only | Cross-dialect form comparison |
| `EtymologyTrace.tsx` | `etymology-trace` | C1, C2, OES, RUTH | Word through historical stages |
| `PaleographyAnalysis.tsx` | `paleography-analysis` | OES, RUTH only | Script / manuscript features |
| `SourceEvaluation.tsx` | `source-evaluation` | HIST, BIO, ISTORIO | Primary source reliability |
| `TranslationCritique.tsx` | `translation-critique` | B2+, LIT | Compare two translations |

`MythBuster.tsx` is NOT in `ACTIVITY_CONFIGS` — it is a Tab 1 prose
component (decolonization theory block), not an activity type. It
belongs in §3.2 (already listed there).

#### 3.4.c Deprecated / forbidden components

| Component | `type` string | Status |
|---|---|---|
| `Classify.tsx` | `classify` | Deprecated; subsumed by `group-sort`. Not in any level's `ACTIVITY_CONFIGS`. Writer must not emit. |
| `Select.tsx` | `select` | Deprecated; subsumed by `mark-the-words`. Listed in every level's `FORBIDDEN_ACTIVITY_TYPES`. Writer must not emit. |

**Tab 3 immersion:** activity instructions, prompts, options, and
feedback strings are **100 % Ukrainian at B1+**. At A1 + A2 they
follow the per-band ramp (English instructions early, Ukrainian
instructions late A2). Python QG enforces this by tokenizing activity
strings and checking Latin-character ratio per `type` instance.

### 3.5 Tab 4 — Ресурси (Resources)

| Component | Purpose |
|---|---|
| `SourceBox.tsx` | Citation block — title + author + page + URL + access date |
| `YouTubeVideo.tsx` | (Re-used from §3.2) Linked thumbnail to a referenced video |

Plain markdown links (e.g. to ULP episodes, Anna Ohoiko, Прометей,
Wikipedia articles) also live here without a component wrapper.

**Tab 4 immersion:** Tab 4 prose (curator's notes, "see also" glosses,
section dividers) is **100 % Ukrainian at B1+**. Citation METADATA
(English source titles, English article URLs, English-language
publisher names) is preserved verbatim — that's factual citation
content, not language-of-instruction. A B1+ Tab 4 with English source
titles + Ukrainian curator's prose is correct; a B1+ Tab 4 with
English curator's prose around Ukrainian source titles is a band
violation.

## 4. Constraints the writer must obey

1. **Tab 3 activities use only the 22 type strings in §3.4** (or the
   B2+ extensions when explicitly authorized by the plan). Unknown
   types fall through to `ActivityPlaceholder` and FAIL Python QG.
2. **`<!-- INJECT_ACTIVITY: {id} -->` ids must resolve** to an entry
   in `activities.yaml`. Unresolved ids fail the build.
3. **Every Tab 4 SourceBox must trace back** to a citation present in
   the plan's `references` field or in the wiki packet. Ghost
   citations (a SourceBox not justified by source data) fail Python
   QG.
4. **Vocabulary in Tab 2** — every lemma is VESUM-verified or
   whitelisted in `PROPER_NAME_WHITELIST`. Translations come from the
   writer with contextual disambiguation (not Балла-direct lookup).
5. **No empty tabs without justification.** The plan should account
   for all four tabs. If a module legitimately has no external
   resources, the plan declares this and the empty state renders.
6. **Immersion is band-strict and tab-aware:**
   - **A1 + A2:** writer hits the per-band ramp from `scripts/config.py`
     IMMERSION_POLICIES across all four tabs.
   - **B1+ (including B2, C1, C2, all seminars):** **Tab 1 / Tab 3 /
     Tab 4 module body is 100 % Ukrainian.** No exceptions, no rescue
     notes, no parenthetical English glosses on grammar terms, no
     English mirror-translations, no English narrative scaffolding.
     Tab 2 (Словник) carries English translations + English
     idiom/expression notes as a structural carve-out — this is
     the ONLY sanctioned English at B1+.
7. **Decolonized framing across all four tabs.** Same standards in
   `docs/north-star.md` § WRONG apply uniformly: no Russianisms, no
   Russian-imperial cultural framing, no Soviet-era euphemisms.

## 5. Constraints the pipeline must enforce

Python QG (deterministic) catches:

- Missing tab content (any of the four tabs entirely empty when the
  plan asserts content for it)
- Unknown activity `type` strings
- Unresolved `INJECT_ACTIVITY` ids
- Vocabulary entries failing VESUM verification (with whitelist)
- SourceBox citations that don't roundtrip against plan / wiki packet
- Word count under `target_words`
- Forbidden lemmas (Russianism / Surzhyk / calque list — to be
  formalized in Phase 3 / Phase 4)
- A1 + A2: immersion ratio outside the band's tolerance per
  `IMMERSION_POLICIES`
- **B1+: Latin-character ratio in Tab 1 / Tab 3 / Tab 4 module body
  exceeds a small allowance for proper-name spellings + ISO codes
  (≤ 1 % default). Tab 2 is exempt from this check.**
- MDX renders cleanly under Starlight (`npm run build` smoke test —
  enforced in CI per Phase 4)

LLM QG (pedagogical, by a non-writer agent) scores:

- Naturalness of the Ukrainian prose
- Pedagogical flow (do sections build on each other; is the rule
  introduced before the practice)
- Decolonization (framing, examples, references)
- Engagement (does the prose hold attention; are dialogues real)
- Tone (peer voice, no AI slop, no robotic interrogations)

The two layers must NOT overlap. LLM does not score word count; Python
does not score tone. (See North Star § HOW.)

## 6. What this contract DOES NOT specify

- Per-component prop schemas (Phase 3 work — `docs/lesson-schema.yaml`)
- Wiki packet schema (Phase 5 work)
- Plan YAML schema (already defined in `curriculum/l2-uk-en/plans/`
  and `scripts/build/contracts/module-contract.md`; this doc accepts
  it as given)
- Per-level word targets (already in `scripts/audit/config.py`)
- Activity-type pedagogy (already in
  `docs/best-practices/activity-pedagogy.md`)
- Site-wide ``/dictionary/`` section design (covered separately by
  EPIC #1581; per-module ``VocabCard`` only cross-links to dictionary
  entries — see §3.3)

## 7. Resolved policy decisions (panel-confirmed 2026-04-25)

3-agent review thread `6de2be4789394536abdb6356cd5bb006` resolved the
following design questions unanimously. Each is now binding policy.

**P1 — Tab 3 canonical Ukrainian label = `Вправи`.**
The running code (`scripts/generate_mdx/core.py:356`) is canonical.
The handoff doc reference to `Зошит` was a drafting error and gets a
one-line correction. Reasoning: `Вправи` accurately translates
"Exercises / Activities" and matches every existing curriculum module;
`Зошит` (notebook) is conceptually closer to the Tab 2 vocabulary
deck and would be misleading. Source: panel consensus.

**P2 — Inline-AND-aggregate activity rendering is intentional.**
An activity referenced via `INJECT_ACTIVITY` in Tab 1 ALSO appears in
the Tab 3 aggregate. The Tab 3 aggregate adds a
`(see lesson, §<section-title>)` cross-reference next to each entry
that was already encountered inline, so the learner knows they are
reviewing an activity they have seen rather than meeting a new one.
Source: panel consensus (intentional reinforcement; explicit
cross-reference required).

**P3 — At least one inline activity per major section is required.**
The writer must place at least one `INJECT_ACTIVITY` marker per
major Tab 1 section. No maximum cap; writer discretion for additional
inline activities and for end-of-section placement. Reasoning: breaks
walls of text, paces cognitive load, prevents writer from frontloading
all activities into Tab 3. Source: panel consensus.

**P4 — At least one Tab 4 (Resources) entry is required per module.**
The plan ALWAYS has `references`, so at minimum the module's plan
references re-list as `SourceBox` entries in Tab 4. Empty Tab 4
fails Python QG. Reasoning: zero-cost enforcement that prevents
citation drift; the empty-state localized message remains in the
codebase only as a fallback for malformed plans. Source: panel
consensus.

**P5 — Out-of-scope MVP components are hard-rejected by Python QG.**
At A1 + A2 + B1, any writer output emitting an out-of-MVP component
type (per §3.4.b list) or a deprecated type (per §3.4.c) fails the
build deterministically. The writer prompt at MVP levels ships only
the in-scope component list as the complete option set. Reasoning:
the writer should never need the out-of-scope set at MVP levels; an
emission is a hallucination. Source: panel consensus, contingent on
the §3.4 matrix alignment with `activity-pedagogy.md` (now done in
v3).

**P6 — B1+ body-English Python QG threshold = ≤ 1 % Latin character
ratio in Tab 1 / Tab 3 / Tab 4 module body, with Tab 2 + citation
metadata excluded.** Token-aware tokenization
(skip URLs, ISO codes like `[uk]`, proper-name transliterations like
`Kyiv` inline next to `Київ`). Tab 2 (Словник) is exempt — the
translation column is structural English, not body English. Citation
metadata in Tab 4 (English source titles, English publisher names,
English-language URL paths) is also exempt. Source: panel consensus
on the ≤ 1 % default with Codex's refinement that enforcement should
be token-aware rather than raw-character-ratio-only.

**P7 — VocabCard cross-link to dictionary section: SUPPRESSED until
EPIC #1581 ships.** Per-module `VocabCard` at MVP levels does NOT
emit a cross-link to `/dictionary/{lemma}/`. Once #1581 lands, this
contract is amended (see §6) and the cross-link prop becomes
required. Reasoning: keep the contract simple now; amend only when
the dictionary destination is real. Source: panel consensus
(option c).

---

**Phase 0 closeout actions** (after this commit):
1. Update `docs/session-state/2026-04-25-evening-reboot-decision.md`
   line 82: `Зошит` → `Вправи` per P1.
2. File `scripts/config.py` IMMERSION_POLICIES B1 cleanup issue
   (Phase 2 sub-issue under EPIC #1577) — delete `b1-m01-05`,
   collapse `b1-core` to 100 % Ukrainian, rewrite rule string to
   match B2+ language, audit pipeline code for any `b1-m01-05` key
   branches.
3. Wire `{NORTH_STAR}` and `{LESSON_CONTRACT}` placeholders into
   `scripts/build/phases/v6-write.md` "Shared Contract" preamble
   section as the AC-3 proof for #1578.
4. Comment on #1578 with the channel thread id and close.
