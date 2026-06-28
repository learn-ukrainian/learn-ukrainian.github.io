# Shared Reading Section Rules

Prompt suite component version: 0.2
Last reviewed: 2026-06-21

The global reading reference is the seminar equivalent of a lexicon: modules should connect learners to original texts, either hosted on-site when copyright allows or linked externally when hosting is not allowed.

## Required Reading Coverage

- A seminar module's reading layer is a **researched primary-text catalog**, not a single token reading. Before writing, survey the corpus and source registries for **every distinct, verifiable primary text** that belongs to the module's topic (each song, duma, poem, chronicle passage, or other primary artifact appropriate to the track) — then surface as many as the corpus genuinely supports.
- **Per-track minimum (corpus-bound).** Each seminar track sets a primary-text floor. **FOLK targets ≥4 distinct primary readings per module when the gate-safe corpus holds ≥4 distinct verified fragments** (`docs/folk-epic/EXEMPLAR-STANDARD.md` §3). A module may surface fewer **only** when the corpus genuinely lacks that many distinct verified texts — e.g. `zamovliannia` / `narodni-viruvannia`, whose gate-safe corpus carries the genre only as encyclopedia-embedded formulas, not standalone primary rows (record `reading-needed`). **Availability is a verified number, never an assumption:** the preflight audit (#3696) found the koliadky corpus holds 6 distinct carols (not the 2 an earlier note guessed), so its floor is ≥4 — survey the corpus before concluding a topic is genuinely low.
- **Never backfill to the floor.** Do not pad the catalog to hit a number with from-memory text, paraphrase, reconstructed fragments, or scholarly-quoted snippets. Under-coverage relative to corpus availability is recorded as a `reading-needed` finding — never hidden, never faked.
- If no usable reading is present yet, record it as a blocker or explicit `reading-needed` task; do not silently omit readings.
- A reading can be a full original text, an excerpt, a chronicle/source passage, a literary work, a folk text, or another primary artifact appropriate to the track.

## Primary Text vs Scholarship

The reading catalog holds **primary texts only** — the works learners read in the original. **Secondary/scholarly works are not readings**, even when a plan lists them under `references:`:

- Scholarly monographs, surveys, and analyses (e.g. Костомаров «Слов'янська міфологія», Чижевський «Історія української літератури», Попович «Нарис історії культури України», Грушевський used as analysis) are `type: scholarly` references — **never `type: primary`, and never counted toward the reading floor**.
- A primary text embedded inside a scholar's analytical prose (reconstructed or quoted by the author) is **not** a clean hostable reading; source the standalone text from a primary-text corpus instead.
- When auditing or building, flag any reference tagged `type: primary` that is actually a secondary work and re-tag it `type: scholarly`. The reading floor counts only standalone primary texts.

## Current Repo Surfaces

Inspect these before acting because the reading system is still evolving:

- `site/src/content.config.ts`, `readings` collection schema
- `site/src/content/readings/*.mdx`
- `site/src/pages/readings/[...slug].astro`
- `site/src/components/PrimaryReading.tsx`
- `scripts/generate_mdx/reading_links.py`
- `scripts/readings/generate_readings.py`
- `tests/test_reading_links.py`

Current hosted readings require explicit `public_domain: true` in frontmatter. Do not host copyrighted full text unless the current schema and license policy explicitly permit it.

## Plan And Resource Fields

Use `docs/prompts/orchestrators/shared/reading-catalog-template.md` for the
preflight search record and rights decision log. When the current track plan
supports a `readings:` block, include for each candidate:

- `title`
- `title_en` when useful
- `genre`
- `source`
- `source_url`
- `license`
- `hosting`
- `reading_slug` when hosted on-site

When the module has `resources.yaml`, include one or more `role: reading` entries with a learner-facing task in `notes`.

## Copyright Decision

Every reading candidate must carry a decision:

- `hosted`: public-domain or otherwise clearly hostable; create/update `site/src/content/readings/<slug>.mdx`.
- `linked-only`: not hostable or uncertain, but a stable public teaching/source URL exists; add `role: reading` link and learner task.
- `excerpt-only`: only a short compliant excerpt may be quoted; link to the original when possible.
- `omit`: no reliable, learner-safe, or pedagogically usable source exists after search; record the search and reason.
- `reading-needed`: the module needs the source, but no verified usable text or rights decision exists yet; record it as a blocker.

Start with obvious public teaching/library sources such as Osvita when relevant, but verify the exact current domain, URL, license/copyright posture, and text identity. Do not invent `osvita` links or assume that a teaching site automatically grants republication rights.

## Hosted Reading Requirements

Hosted reading files under `site/src/content/readings/` must include valid frontmatter for the current schema:

- `title`
- `genre`
- `tracks`
- `taught_in`
- `excerpt`
- `source`
- `public_domain: true`
- optional `title_en`, `author`, `collector`, `year`, `period`, `order`

The body should render the text with `PrimaryReading` and include source/copyright notes. If generated by `scripts/readings/generate_readings.py`, preserve the generator marker and do not hand-edit generated content without a reason.

## Lesson Linking

- Use `:::primary-reading` blocks for verbatim source work inside FOLK lesson sources.
- The generator links `PrimaryReading` boxes to `/readings/<slug>/` only when the reading file exists; missing files must not create broken links.
- For link-only or excerpt-only readings, add a student-facing `role: reading` resource and mention the reading task in the lesson without pretending the full text is hosted.

- Hosted reading pages are public learner pages when `published` and `canonical` are not false. They may name the public source and show the public URL, but must not expose the build workflow: no `chunk_id`, `source_chunk`, corpus/service IDs, `source hammer`, `hosted reading`, `public reading`, `learner-facing`, or validation-tool language. Unpublished or noncanonical retained readings may carry maintenance notes only while they remain unroutable.

## Validation

For FOLK hosted readings, run:

```bash
.venv/bin/python scripts/readings/generate_readings.py <module-dir> --dry-run --json
.venv/bin/python -m scripts.build.verify_shippable folk <slug>
```

When site dependencies are available, add the relevant Astro/site build or CI check. Always run `git diff --check` and forbidden-artifact guards before commit.
