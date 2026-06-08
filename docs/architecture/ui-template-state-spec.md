# Post-Foundation Learner UI State Spec

This is the source of truth for the next learner-UI implementation PR after
`#2823` / PR `#2840`. It converts the POC intent and the merged
`docs/architecture/ui-template-matrix.md` into a required/deferred state
contract so missing templates are not invented silently during implementation.

The POC files remain design intent, not source to copy:

- `docs/poc/poc-site-design.html`
- `docs/poc/poc-lesson-design.html`
- `docs/poc/poc-word-atlas-design.html`
- `docs/poc/poc-folk-lesson-design.html`
- `docs/poc/poc-lit-lesson-design.html`

## Visual System Baseline

Use the merged lightweight learner shell and namespaced `lu-*`/lesson styles as
the implementation surface. Do not reintroduce the legacy Starlight docs shell
as the primary learner experience.

Required baseline:

- Header, mobile navigation, footer, breadcrumbs, skip link, 404, hidden-route,
  missing-content, and unavailable states stay visually consistent.
- Light and dark themes are first-class. The next UI PR must add a visible
  theme toggle rather than relying only on `?theme=` and system preference.
- Core tracks use the blue/yellow course vocabulary from the site and lesson
  POCs.
- Seminar tracks use source-first variants from the site, seminar lesson, Folk,
  and Lit POCs. Color is a track accent, not a separate design system.
- Reference pages use the Word Atlas teal/yellow vocabulary with provenance and
  editorial-warning surfaces.
- Cards remain for repeated items, resources, definitions, and individual
  activities. Do not nest UI cards inside other cards.

## Next Shippable UI PR

The next shippable UI PR must cover these states before it is marked ready:

- Future/unavailable track pages for both core and seminar tracks.
- Search loading, error, no-results, and dense results layouts on mobile and
  desktop.
- Word Atlas and etymology/reference empty states plus detail variants for
  rich, partial, and missing records.
- Activity primitive polish for feedback, workbook separation, glossary support,
  callouts, source notes, and prev/next.
- Accessibility polish: visible theme toggle, roving keyboard focus for tabs,
  visible focus rings, and reduced-motion handling.

Seminar module pages for BIO/HIST/ISTORIO/LIT/OES/RUTH may ship in the same PR
only if source-backed content and QA stay under the repo file-count rule.
Otherwise, this spec must still define their templates and mark implementation
as deferred.

## Track State Requirements

### Core Future and Unavailable

Required:

- A2 is a `next` state, not a generic unavailable state. It should say A2 is the
  next core target after A1 without promising live lessons.
- B1, B2, C1, and C2 are `future/unavailable` states. They may show curriculum
  scope and module counts, but they must not imply current learner readiness.
- Every future core page needs a primary return path to A1 and a secondary
  reference/search path when useful.
- Module inventories may appear locked, but locked rows must not be clickable
  dead ends.
- Copy must avoid stale STEM, C1 Pro, or complete-course promises.

Deferred:

- Full progress persistence, account state, and learner completion analytics.
- Rich per-unit future-roadmap editorial copy for B1-C2.

### Seminar Future and Unavailable

Required:

- Folk remains the seminar test track and can link to available Folk lessons.
- BIO, HIST, ISTORIO, LIT, OES, and RUTH are planned seminar pages unless their
  modules are actually published in the learner UI.
- Planned seminar pages should show prerequisite level, source-heavy pattern,
  and what makes the track different.
- Planned pages must route learners to Folk for the live seminar pattern, or to
  Word Atlas/etymology when the track is reference-heavy.
- Seminar pages must not show fake module readiness. Planned inventories are
  allowed only as disabled/planned rows.

Deferred:

- Track-specific published inventories for seminar families that do not yet have
  learner-ready content.
- Per-track onboarding quizzes or diagnostics.

## Seminar Module Variants

All seminar modules keep the shared tab shape from the lesson POC:

- Lesson
- Vocabulary
- Workbook
- Resources

The lesson tab is source-first. It should put sources, interpretation, and
context near the top instead of burying them under generic prose.

### Shared Source-Heavy Seminar

Required for BIO/HIST/ISTORIO/OES/RUTH when a module page ships:

- A source note card with source title, type, date/period when available, and
  provenance status.
- A bibliography/resource card list in the Resources tab, grouped by source
  type when there are at least three sources.
- A decolonization/context callout where the plan or source material involves
  imperial framing, Soviet framing, contested terminology, or historical bias.
- Source evaluation workbook state using author, context, evidence, bias, and
  usefulness criteria.
- Reading/comparison prompts that require learners to cite the displayed source
  or resource trail.
- Glossary support for dense terms, names, historical forms, and abbreviations.

Deferred:

- Full citation export and downloadable bibliographies.
- Multi-source side-by-side annotation tools beyond static comparison tables.

### BIO

Required:

- Chronology strip or compact timeline.
- Role/context summary that avoids hero worship.
- Source-conflict or legacy-framing note when sources disagree.
- Resource cards for primary source, scholarly biography, and reference overview
  when available.

Deferred:

- Interactive prosopography maps and network graphs.

### HIST

Required:

- Era/chronology grouping from the site POC.
- Primary-source card and decolonization note where applicable.
- Source comparison and debate workbook prompts.
- Explicit distinction between event narrative and historiographic
  interpretation.

Deferred:

- Map/timeline animation and multi-era filters.

### ISTORIO

Required:

- Method note explaining what kind of historical writing is being examined.
- Bias/checklist callout for author position, audience, and archive/source base.
- Comparative table for competing interpretations.

Deferred:

- Large historiography network views.

### LIT

Required:

- Close-reading annotation state.
- Source/excerpt card that respects protected-text limits.
- Genre and structure framing.
- Lit workbook families from the Lit POC: close reading, prosody, theme trace,
  structure, and dramatic reading where relevant.
- Myth/decolonization callout where a literary myth or imperial framing is part
  of the lesson.

Deferred:

- Full text hosting for protected works.
- Audio staging beyond a static playback/recording affordance.

### OES and RUTH

Required:

- Dense seminar reading layout with glossary support always visible or one tap
  away.
- Paleography/transcription/source-note primitives for historical-language
  evidence.
- Etymology trace and translation-critique workbook patterns when the plan
  includes historical forms.
- Clear language label for old forms versus modern Ukrainian equivalents.

Deferred:

- Manuscript image viewers with zoom/hotspot persistence.
- Full parallel-text alignment tooling.

### Folk

Required if Folk is touched:

- Preserve the Folk experiential additions: audio block, symbolic decode, ritual
  sequencing, variant comparison, motif/formula, and performance.
- Keep Folk additive to the shared seminar source-analysis set; do not replace
  source evaluation with performance-only activities.

Deferred:

- Real recording capture/upload. The UI may show a local/placeholder recording
  affordance only if it does not imply server storage.

## Search States

Search is an app-width surface, not a reading-width lesson page.

Required:

- Loading: stable layout with skeleton/result-row placeholders, no content
  jump, and an `aria-live` status message.
- Error: concise failure state with retry action and a link back to home or the
  current track. It must not look like a 404.
- No results: echo the query, offer spelling/diacritic hints, and provide links
  to A1, Folk, Word Atlas, and search reset.
- Results: dense rows with title, route, type, track/level chip, and a short
  excerpt. Mobile uses a single-column row with wrapped metadata; desktop can
  use denser two-line rows.
- Keyboard: search input receives focus when opened by shortcut or search link;
  result links follow normal tab order.

Deferred:

- Backend search, ranking telemetry, federated external-source search, and
  advanced filters beyond the static foundation data.

## Word Atlas, Etymology, and Reference States

Reference pages use the Word Atlas POC as the design source.

Required index states:

- Default index with search/filter, alphabet or group affordance, and a compact
  list.
- Filtered results.
- Empty filter state with reset.
- Loading/skeleton state if bundles are lazy-loaded.
- Error state if a reference bundle fails to load.

Required detail variants:

- Rich record: hero with lemma, stress, part of speech, status badges,
  definitions, morphology, etymology, literary/source attestations, course
  usage, translation links, and provenance footer.
- Partial record: show available sections only, with a small missing-data note
  near the absent section. Do not render empty headings.
- Editorial warning: support Soviet-definition warnings, calque warnings,
  regionalism notes, and heritage-defense success notes.
- Missing record: use the reference empty-record state, link back to index, and
  offer search. It is not a site-wide 404 unless the route is invalid.
- Full-reference route behavior: generated detail routes should build only for
  records included in the active static bundle. Hidden or omitted records should
  use the missing-record state or the site 404 based on route validity.

Deferred:

- Full ESUM route expansion for every record.
- Citation export, all-attestation browsing, and large external media bundles.

## Activity and Content Primitives

Required:

- Tabs: `Lesson`, `Vocabulary`, `Workbook`, `Resources` tab shape with roving
  keyboard focus, hash-safe activation, visible focus ring, and no layout shift.
- Quiz/card feedback: neutral, selected, correct, incorrect, explanation, retry,
  and disabled states. Feedback must be announced to assistive technology.
- Workbook sections: clear exercise number, type badge, instruction, response
  area, feedback/rubric area, and stable spacing between activities.
- Glossary support: inline glossary term, compact glossary panel/list, and
  missing-glossary empty state.
- Callouts: rule, cultural note, warning, source note, myth/decolonization, and
  editorial/reference warning. Color alone cannot carry meaning.
- Source notes: source title, type, citation/provenance status, and optional
  "why this source matters" note.
- Prev/next behavior: lessons need previous/next module links plus a track
  return link. Unavailable or hidden neighbors must not create dead links.
- Tables/dialogues/cards must retain readable mobile layouts.

Deferred:

- Drag-and-drop-only interactions. If added, they need click/keyboard fallbacks.
- Persistent answer storage, scoring, and teacher dashboards.

## Accessibility and Motion

Required:

- Visible theme toggle in the header or mobile menu. It must update
  `localStorage`, reflect current state, and have a text label or accessible
  name.
- Roving tab focus for custom tablists:
  - `Tab` enters/leaves the tablist.
  - Arrow keys move active/focused tab.
  - `Home` and `End` jump to first/last tab.
  - Hash links continue to open the matching tab.
- Focus rings: all interactive controls use a visible focus outline with at
  least 3:1 contrast against adjacent colors.
- Reduced motion: respect `prefers-reduced-motion`; disable decorative
  waveform/hover movement and shorten transitions.
- Loading/error/no-results messages use `aria-live` when content updates without
  navigation.
- Icon-only buttons need accessible names and visible tooltips or labels where
  meaning is not obvious.

Deferred:

- Full WCAG audit reports for every route family. The next UI PR still needs
  targeted browser QA for representative routes.

## QA Gate For The Next UI PR

Before marking the next UI PR ready:

- Browser-test one desktop and one mobile route for every implemented state
  family.
- Test light and dark themes using the visible theme toggle.
- Test reduced motion with `prefers-reduced-motion`.
- Test keyboard tab navigation through header, search, tabs, activity feedback,
  and prev/next.
- Verify no route shows stale C1 Pro/STEM/publication promises.
- Verify no copy implies Anna Ohoiko book-based content, copied ULP material, or
  endorsement. Use "pedagogy and methodology inspiration" only.
- Keep the PR under the repository file-count rule, or split by template family.
