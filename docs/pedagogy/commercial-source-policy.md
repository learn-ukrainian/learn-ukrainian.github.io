# Commercial Source Policy for Learning Materials

> Scope: how agents may use paid or all-rights-reserved learning materials when
> improving learn-ukrainian pedagogy, prompts, rubrics, or lessons.

## Core Rule

Paid learning materials may be used only as private, read-only benchmarks for
abstract pedagogy. They are not source corpora for this repository.

Agents may learn only high-level principles such as scaffolding style,
cognitive load management, review design, or media support. They must not
ingest proprietary source text into prompts, context windows, RAG, embeddings,
source databases, generated lessons, issue comments, review artifacts, or
preserved notes. Agents must not copy, summarize, extract, store, imitate, or
derive learner-facing content from a commercial resource.

Paid third-party workbooks and courses may be recommended as companion study
resources in learner-facing resource lists when appropriate. They must not be
used as source material to clone.

## Allowed Uses

- Use user-provided abstract observations about pedagogy, without seeing or
  preserving proprietary source text.
- Cite a public product page when recommending or acknowledging a resource.
- Compare project rubrics against broad public claims such as level, audience,
  audio support, review support, or general workbook purpose.
- Write original policy, rubrics, and prompt guidance inspired by broad
  pedagogy, without importing any proprietary content or sequence.

## Forbidden Uses

Do not put any of the following into git, docs, prompts, RAG, embeddings,
source databases, generated lessons, issue comments, or review artifacts:

- PDFs, scans, screenshots, page images, cover crops, or workbook visuals;
- extracted text, OCR, transcripts, audio, answer keys, exercise items, or
  dialogue lines;
- proprietary examples, vocabulary lists, grammar charts, page-level summaries,
  handwriting samples, or image choices;
- local private file paths or notes that identify a user's private copy;
- a commercial workbook's table of contents, lesson order, review cadence,
  exercise sequence, dialogue arc, or distinctive page layout;
- derivative exercises that preserve the same examples, order, answer pattern,
  context, image idea, or wording with superficial substitutions.

## Temporary Analysis

Agents must not temporarily extract, render, OCR, transcribe, paste, or process
paid learning materials, even outside the repository. If a user privately
reviews a paid resource outside the repo, only abstract pedagogy observations
may enter this project.

Never add paid materials to:

- `data/sources.db`;
- `data/external_articles/`;
- `data/references/` or any git-tracked corpus path;
- vector stores, embeddings, or RAG indexes;
- public docs, generated status files, audit files, or review reports.

## Structural Cloning Ban

Direct copying is not the only risk. Structural cloning is also forbidden.

Do not recreate a commercial workbook's:

- grammar order;
- unit grouping;
- review interval;
- exercise-type sequence;
- recurring character/dialogue arc;
- image progression;
- handwriting sample set;
- answer-key pattern;
- page composition.

For learn-ukrainian, lesson order remains controlled by project plans, the
Ukrainian State Standard 2024, and accepted repository decisions. Commercial
materials may influence only abstract scaffolding principles.

## Media and Public Video Rules

Visuals used in lessons must be original, generated for the project,
public-domain, or properly licensed. Record attribution where the schema
requires it.

Audio must be original, properly licensed, or linked lawfully. Public video
platform media may be linked or embedded when appropriate, but agents must not
download, transcribe, remix, cut, or reuse audio/video unless the license or
explicit permission allows it.

Do not use screenshots from public video platforms, paid workbooks, course
platforms, or commercial apps unless the project has permission.

## Agent Checklist

- [ ] I used only public citations or private abstract analysis.
- [ ] I did not copy or preserve any paid source material.
- [ ] I did not add private material to git, RAG, embeddings, or source DBs.
- [ ] I did not recreate a commercial sequence or exercise pattern.
- [ ] I did not temporarily extract, render, OCR, transcribe, paste, or process
      paid source material.
- [ ] The diff contains no local private file path.
- [ ] The work recommends paid resources respectfully as companions, not as
      raw material for this curriculum.
