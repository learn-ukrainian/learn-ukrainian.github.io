# Shared Reading Catalog Template

Prompt suite component version: 0.1
Last reviewed: 2026-06-22

Use this template during seminar preflight and production when a module needs a
primary/source reading layer. The catalog is a search record and rights decision
log; it is not limited to readings already available in the repo.

## Required Candidate Fields

Each candidate should carry these fields when known:

```yaml
- title: ""
  title_en: ""
  author: ""
  collector: ""
  genre: ""
  track: ""
  module_slug: ""
  source_type: primary
  source_family: ""
  source_edition: ""
  source_url: ""
  source_id: ""
  text_identity_verified: false
  license: ""
  copyright_status: unknown
  hosting_decision: reading-needed
  reading_slug: ""
  excerpt_allowed: false
  quote_status: do-not-quote
  verification_notes: ""
  learner_task: ""
  blocker: true
```

## Hosting Decisions

Use exactly one `hosting_decision` per candidate:

- `hosted`: public-domain or otherwise clearly hostable; create or update the
  hosted reading file and keep provenance in frontmatter.
- `linked-only`: stable learner-safe source URL exists, but hosting is not
  allowed or rights are uncertain.
- `excerpt-only`: a short compliant excerpt may be quoted, but full hosting is
  not allowed.
- `omit`: source is unreliable, unsafe, duplicate, or pedagogically unsuitable;
  keep the search note so the omission is reviewable.
- `reading-needed`: the module needs this source, but no verified usable text or
  rights decision exists yet. Treat unresolved `reading-needed` items as
  blockers for production unless the stage is explicitly preflight-only.

## Verification Rules

- `source_type` for catalog candidates must be `primary`. Secondary scholarship
  belongs in references, not in the reading catalog.
- `text_identity_verified: true` means the title, author or collector, edition,
  and text are matched to a specific source. Do not set it from memory.
- `quote_status` should be one of `verified`, `paraphrase-only`, or
  `do-not-quote`.
- `reading_slug` is required only for `hosted` readings.
- `learner_task` should describe what the student does with the text, not just
  where the text came from.

## Preflight Summary Format

```text
Reading coverage:
- hosted: <count>
- linked-only: <count>
- excerpt-only: <count>
- omit: <count>
- reading-needed: <count>
Primary source families checked: <list>
Unresolved blockers: <none | source/rights/text-identity issues>
```
