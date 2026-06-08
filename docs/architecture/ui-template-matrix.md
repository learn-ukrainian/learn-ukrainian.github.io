# UI Template Matrix

This matrix is the foundation for issue `#2823`. The learner-facing site should
be implemented as a small set of named templates and primitives, not as a
generic documentation shell around generated MDX.

The POC files are design intent, not source to copy:

- `docs/poc/poc-site-design.html`
- `docs/poc/poc-lesson-design.html`
- `docs/poc/poc-word-atlas-design.html`
- `docs/poc/poc-folk-lesson-design.html`
- `docs/poc/poc-lit-lesson-design.html`

The post-foundation state contract is `docs/architecture/ui-template-state-spec.md`.
Use it as the source of truth for required versus intentionally deferred states
before opening the next UI implementation PR.

## Global Rules

- Support light and dark modes for every page class.
- Provide skip link, header, nav, breadcrumbs, mobile nav, footer, 404, and
  hidden-route behavior.
- Use constrained reading width for lessons and reference prose.
- Use app-width surfaces for landing pages, search, inventories, and atlas
  indexes.
- Public copy must say A1 is beta/release focus, A2 is next, Folk is the
  seminar test track, and BIO/HIST are planned seminar work.
- Do not mention stale STEM or C1 Pro promises.
- Self-study is allowed, but trained native Ukrainian teachers are best.
- Promote Ukrainian Lessons / ULP and thank Anna Ohoiko for pedagogy and
  methodology inspiration only. Do not imply copied content or endorsement.

## Template Coverage

| Template | Tracks or Pages | POC Source | Required State |
| --- | --- | --- | --- |
| Global shell | All pages | Site POC | Foundation implemented |
| Main landing | `/` | Site POC | Foundation implemented |
| Core track landing | A1-C2 | Site POC | Foundation implemented |
| Seminar track landing | Folk, BIO, HIST, ISTORIO, LIT, OES, RUTH | Site POC + seminar POCs | Foundation implemented |
| Future track landing | Planned or unavailable tracks | Site POC | Foundation implemented |
| Core lesson | A1-C2 modules | Lesson POC | A1 implemented; A2-C2 use unavailable/future track states |
| Folk seminar lesson | Folk modules | Folk lesson POC | Implemented for currently shipped Folk MDX |
| BIO/HIST/ISTORIO lesson | Source-heavy seminar modules | Folk lesson POC | Landing template implemented; module content follow-up |
| LIT lesson | LIT variants | Lit lesson POC | Landing template implemented; module content follow-up |
| OES/RUTH lesson | Historical-language seminar modules | Folk/Lit POCs | Landing template implemented; module content follow-up |
| Word Atlas index | `/lexicon/` | Word Atlas POC | Foundation implemented with filter/no-results |
| Word Atlas detail | `/lexicon/{lemma}/` | Word Atlas POC | Foundation implemented |
| Etymology index | `/etymology/` | Word Atlas POC | Foundation implemented with featured filter/no-results |
| Etymology detail | `/etymology/{slug}/` | Word Atlas POC | Foundation implemented when full ESUM route build is enabled |
| Search | Search form, results, no-results, error | Site POC | Foundation implemented |
| Error states | 404, hidden route, unavailable, empty record | Site POC | Foundation implemented |
| Activity primitives | Tabs, tables, dialogues, quizzes, cards, callouts | Lesson POC | Foundation implemented; deeper component polish follow-up |

## Track Families

### Core A1-C2

Core tracks need course progress, module inventory, next-module call to action,
level status, and a Ukrainian-first lesson page. Generated A1 MDX must render
without bespoke per-module fixes, including tables, dialogue blocks, tabs,
inline activities, and workbook/activity separation.

### Seminar Tracks

Seminar tracks need a source-first landing and a source-heavy lesson pattern.
Folk emphasizes motif, context, performance, and source notes. BIO, HIST, and
ISTORIO need chronology, source trail, and decolonization notes where relevant.
LIT variants need literary framing and excerpt/reference affordances without
copying protected text. OES and RUTH need a dense seminar reading pattern for
historical-language evidence.

### Reference Tracks

Word Atlas and etymology pages are static. They must work without a backend.
Indexes need search/filter affordances, alphabet grouping, and empty states.
Detail pages need definitions, examples, morphology, etymology/reference links,
related entries, course usage, and back navigation.

## Primitive Inventory

- `CourseLayout`: global shell, hero variants, breadcrumbs, footer.
- Track overview: status panel, primary/secondary CTA, learning support cards.
- Lesson content: reading width, Ukrainian-first prose, headings, tables.
- Tabs: generated MDX compatibility and hash-safe tab switching.
- Dialogue: speaker lines, translation/support table, source notes.
- Rule/callout: grammar rule, cultural note, warning, source note.
- Activity: inline quiz, card grid, workbook section, feedback states.
- Search: input, filters, result row, no-results, loading, error.
- Error: 404, unavailable route, hidden route, missing record.

## First PR Gate

The first #2823 PR may remain a foundation PR, but it is not complete until:

- This matrix exists in the branch.
- Every implemented template class has desktop/mobile and light/dark QA.
- Hidden routes, 404, unavailable, and empty states are checked.
- A representative page from every implemented template class is browser-tested.
- Independent Gemini/Agy UI review is clean.

If the implementation cannot cover all template families under the repository
file-count rule, keep #2823 as the umbrella and split follow-up PRs by template
family.

## Foundation PR Split

The current foundation PR stays under the repository file-count rule by
extending the existing Astro catch-all route instead of adding one route file
per state. It delivers the custom learner shell, main landing, core/seminar
track landings, A1/Folk lesson rendering, static search, reference filters, and
explicit state templates.

Follow-up PRs should remain scoped by template family:

- Deeper hidden-route recovery and analytics around unpublished draft paths.
- Seminar module pages for BIO/HIST/ISTORIO/LIT/OES/RUTH once source-backed
  content exists.
- Rich Word Atlas and ESUM search bundles instead of foundation filters.
- Component-level polish for activity feedback, source notes, glossary panels,
  and workbook separation after the route shell is accepted.
- Legacy Starlight-era MDX landings and React landing components remain in the
  tree because repository rules forbid deleting existing files without explicit
  scope; the foundation docs collection only loads the active A1 and Folk
  lesson families so stale B2-PRO/C1-PRO promises are not generated in the
  learner UI.
