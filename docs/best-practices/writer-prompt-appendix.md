# Writer prompt appendix

Fetched on demand from `scripts/build/phases/linear-write.md` via @-path reference. Contains heavy reference material that doesn't fit the main writer prompt budget but remains canonical for writer / reviewer escalations.

## Component inventory — 1:1 mapping

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
