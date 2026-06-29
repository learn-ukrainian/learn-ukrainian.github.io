# B2 Source Readiness Audit

Date: 2026-06-29

Branch: `codex/b2-source-readiness-audit`

Base: `c3750d49021369a421edbb72fa9c40c8699874ca`

Stage: PR 3, source/plan/wiki/research readiness before any B2 rebuild.

## Verdict

Do not start the B2 golden pilot rebuild yet.

The manifest and basic plan coverage are coherent, but the stricter source
readiness gates fail. The current B2 source layer still has plan-quality
failures, empty discovery evidence, malformed or unresolved wiki source
registry entries, and one tracked stale backup file. These are source-layer
blockers, not module-content repair tasks.

No B2 module content was modified or rebuilt for this audit.

## Scope Checked

- `curriculum/l2-uk-en/curriculum.yaml`, B2 manifest section.
- `curriculum/l2-uk-en/plans/b2/*.yaml`.
- `curriculum/l2-uk-en/b2/discovery/*.yaml`.
- `wiki/grammar/b2/*.md`.
- `wiki/grammar/b2/*.sources.yaml`.
- Existing B2 rebuild/readiness decision and prompt docs.
- Source DB resolution through the main checkout `data/sources.db`, linked into
  the worktree only for local validation.

## Passing Checks

| Check | Result |
| --- | --- |
| B2 manifest count | 93 unique modules |
| Plan file coverage | 93 plans, no missing or extra slugs |
| Discovery file coverage | 93 files, no missing or extra slugs |
| Wiki article coverage | 93 articles, no missing or extra slugs |
| Wiki source registry coverage | 93 source registries, no missing or extra slugs |
| Manifest order alignment | 0 `sequence`, `slug`, or `b2-###` mismatches |
| Basic plan validator | `scripts/validate_plans.py b2` passed, 0 errors, 0 warnings |
| Live wiki/discovery unresolved markers | no `VERIFY`, `TODO`, `FIXME`, `TBD`, or placeholder markers found |

## Blockers

### 1. Deterministic plan quality gate fails

Command:

```bash
.venv/bin/python scripts/audit/check_plan.py b2 --failing-only
```

Result after linking the main checkout `data/sources.db` for local validation:

| Status | Count |
| --- | ---: |
| Fail | 72 |
| Warn only | 5 |
| Pass | 16 |

Issue distribution:

| Issue | Count | Scope |
| --- | ---: | --- |
| Missing `vocabulary_hints` | 68 | plan field required by `check_plan.py` |
| Missing `phase` | 21 | plan field required by `check_plan.py` |
| Unknown textbook reference | 3 | `pobut-shchodenne`, `sport-i-dozvillia`, `kharchuvannia-i-kukhnia` reference `Заболотний, 7 клас (2015)` |
| Possible Russicism | 1 | `checkpoint-communication` has `самий + adjective` superlative warning promoted to error |
| Unknown prerequisite slug warnings | 6 | `passive-voice-system`, `dim-zhytlo`, `genitive-advanced`, `dative-advanced`, `instrumental-advanced`, `questions-deliberative-rhetorical` |

This is a hard blocker because the accepted rebuild contract says to stop when
source, wiki, or research readiness is missing.

### 2. Discovery files are present but not substantive

All 93 B2 discovery files parse and have query keywords, but all have empty
retrieval evidence:

| Field | Total |
| --- | ---: |
| `rag_chunks` | 0 |
| `rag_literary` | 0 |

Discovery files therefore cannot serve as authoritative research packets. They
can only be treated as query-keyword hints unless a later remediation fills or
explicitly supersedes them with wiki/source registries.

### 3. B2 wiki quality gate fails

Command:

```bash
.venv/bin/python scripts/wiki/quality_gate.py --track b2
```

Result:

```text
B2: 1 issues
grammar/b2/register-public-discourse.md:
  MALFORMED_SOURCES_YAML (register-public-discourse.sources.yaml: 'file')
```

The failing source is `S10` in
`wiki/grammar/b2/register-public-discourse.sources.yaml`. It is cited inline,
has `type: official`, and lacks the required `file` field. The source schema
does not list `official` as an allowed type, so fixing only the missing field
may still leave a schema issue.

### 4. Cited source registry entries do not all resolve

A batched read-only source check loaded B2 `.sources.yaml` registries through
`scripts/wiki.sources_schema.load_sources_registry`, then checked source keys
against the current main-checkout `data/sources.db`.

Most textbook entries resolve:

| Source shape | Count |
| --- | ---: |
| Exact `textbooks.chunk_id` | 349 |
| `textbook_sections.section_id` plus source file | 398 |

Problem entries:

| Article | Source IDs | Problem |
| --- | --- | --- |
| `dative-advanced` | `S8`-`S11` | cited `ukrainian_wiki` passage IDs not found |
| `instrumental-advanced` | `S8`-`S10` | cited `ukrainian_wiki` passage IDs not found |
| `participles-vs-relative-clauses` | `S8`-`S9` | cited `ukrainian_wiki` passage IDs not found |
| `register-public-discourse` | `S10` | cited malformed registry entry |
| `word-formation-place-object-names` | `S8` | cited textbook key shape `S537`, not a resolvable source key |

These are hard blockers because source registries are the audit trail for
wiki-backed claims used by rebuild prompts.

### 5. Tracked stale backup file remains

Tracked file:

```text
curriculum/l2-uk-en/plans/b2/advanced-case-semantics.yaml.bak
```

This was also called out by the earlier June 22 preflight audit. It should be
removed in a focused source cleanup PR, not included in this audit PR.

## Golden Pilot Implications

The golden pilot should not begin until the blockers above are fixed or
explicitly waived in a decision record.

Minimum remediation before PR 4:

1. Make `scripts/audit/check_plan.py b2 --failing-only` pass, or document which
   B2 plan fields are no longer required by that checker and update the checker
   in a separate prompt/source remediation PR.
2. Fix `register-public-discourse.sources.yaml` so the wiki quality gate passes.
3. Fix or replace the cited unresolved source IDs in `dative-advanced`,
   `instrumental-advanced`, `participles-vs-relative-clauses`, and
   `word-formation-place-object-names`.
4. Remove the tracked `.bak` file from the source tree.
5. Decide whether empty discovery YAML is acceptable because wiki articles and
   source registries are authoritative, or backfill discovery evidence before
   golden pilot.

Avoid selecting any module with unresolved cited source IDs as the pilot module.

## Plan Scaffold Risk

The plan layer still looks like a reference-article scaffold unless the rebuild
prompt aggressively overrides it:

| Metric | Result |
| --- | ---: |
| Plans with 5 outline sections | 82 |
| Plans with 6 outline sections | 11 |
| Median outline section budget | 1000 words |
| Outline sections at least 900 words | 315 |
| Plans mentioning inline/workbook split or injection markers | 0 |

This does not require editing module content in PR 3, but PR 4 golden pilot must
prove the hardened production prompt turns these large reference-style outlines
into taught lessons with early learner decisions, inline activities, and compact
rules.

## Wiki Freshness Decision

`scripts/wiki/list_rebuild_targets.py --high-priority` lists all 93 B2 wiki
articles. That means the source mix makes every B2 wiki article a high-priority
candidate under the wiki rebuild-target heuristic.

Before PR 4, decide one of:

1. Accept the current locked B2 wiki articles as the authoritative source layer
   after the source-registry blockers are fixed.
2. Run a separate B2 wiki refresh/readiness pass before golden pilot.

## Validation Log

Commands already run:

```bash
.venv/bin/python --version
.venv/bin/python scripts/validate_plans.py b2
.venv/bin/python scripts/audit/check_plan.py b2 --failing-only
.venv/bin/python scripts/wiki/quality_gate.py --track b2
.venv/bin/python scripts/wiki/list_rebuild_targets.py --high-priority
```

Results:

- Python is `3.12.8`.
- Basic plan validation passed: 93 plans checked, 0 errors, 0 warnings.
- Deterministic plan quality failed: 72 fail, 5 warn-only, 16 pass.
- B2 wiki quality gate failed on `register-public-discourse.sources.yaml`.
- High-priority wiki rebuild target count for B2: 93.

Final PR validation after this report was staged:

```bash
npx --yes markdownlint-cli2 docs/audits/b2-source-readiness-audit-2026-06-29.md
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Results:

- Markdown lint passed on this report.
- `git diff --check` passed.
- Protected artifact/config guard passed; the only changed file is this report.
- `lint_agent_trailer.py` passed before commit with no commits in range.

## Collaboration Metadata

- `swarm_used`: false
- `swarm_label`: none
- `swarm_note`: solo audit run; no routine helper swarm used
- Independent review required before merge: Claude read-only agreement/review.
- Independent review identity: Claude bridge, `claude-opus-4-8`.
- Independent review task: `review-b2-source-readiness-audit`.
- Independent review scope: staged report diff, validation summary, forbidden
  artifact/config check, and blocker-only source-readiness claims.
- Independent review disposition: PASS / AGREE.
- Unresolved independent review findings: 0.
