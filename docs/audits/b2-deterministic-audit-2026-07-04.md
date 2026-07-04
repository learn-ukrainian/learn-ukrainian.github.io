# B2 Deterministic Track Audit

Report version: 0.1
Date: 2026-07-04
Auditor: Codex
Workflow: `scripts/audit/track_deterministic_audit.py`
Scope: B2 M01-M93
Durable report path: `docs/audits/b2-deterministic-audit-2026-07-04.md`

## Summary

The reusable deterministic track audit runner was implemented and run against
B2 as the first target. B2 inventory is complete for the selected deterministic
source/mirror set: 93 modules selected, 93 built, 0 not built.

The run found deterministic remediation work:

- Findings total: 119
- Blocker: 48
- High: 8
- Medium: 0
- Low: 0
- Info: 63
- Modules with findings: 70
- Auto-fixable findings: 0
- Remediation-only findings: 119
- Deterministic failures: 63
- Judgement-required content work: 56
- Skipped checks: 187

Old LLM-QG persistence is explicitly excluded pending issue #2156. This run did
not read old rows, run old workers, write telemetry, or create module-local
LLM-QG evidence.

## Command

```bash
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --format json --output /tmp/b2-deterministic-audit.json --fail-on never
```

Outcome: command completed successfully with JSON output under `/tmp`. The JSON
artifact is not committed.

## Finding Classes

| Category | Count | Severity |
| --- | ---: | --- |
| `internal_leakage` | 48 | blocker |
| `english_internal_leakage` | 8 | high |
| `inventory` | 63 | info |

The blocker `internal_leakage` findings are concentrated in modules with
resource chunk markers surfacing into learner mirrors:

- M11 `active-participles-past`
- M12 `participles-vs-relative-clauses`
- M43 `register-practice-cross-register-rewriting`
- M59 `numeral-declension-compound-numbers`
- M60 `word-formation-person-suffixes`
- M61 `word-formation-abstract-nouns`
- M62 `word-formation-place-object-names`

The high `english_internal_leakage` findings match known B2 surface-leakage
areas:

- M01 `passive-voice-system`: `module.md` lines 200 and 206
- M23 `multi-clause-sentences`: `module.md` line 331
- M31 `checkpoint-syntax-ii`: `module.md` lines 237 and 239
- M80 `professional-email-advanced`: `module.md` lines 221 and 223
- M81 `professional-reports`: `module.md` line 243

The 63 info-level `inventory` findings are optional `resources.yaml` absences.
They are advisory in this workflow, not blockers.

## Skipped Checks

- `llm_qg`: excluded pending #2156.
- `mdx_generation_validate`: skipped by default because `generate_mdx.py`
  rewrites site MDX before validating. Use `--run-mdx-generation-validate` only
  for controlled smoke slices.
- `external_resource_liveness`: skipped by default because live URL checks are
  network-dependent.

An explicit controlled smoke run for M01 completed without leaving site output
in the diff and reported one high `mdx_generation_validate` finding for
generation validation/drift. The workflow flagged it and did not auto-fix it.

## Fleet Input

Three read-only planning/review lanes informed the implementation:

- Native Claude CLI recommended manifest enumeration, explicit structural-only
  scope, stable JSON output, offline deterministic gates, and avoiding B2
  assumptions in the generic runner.
- AGY/Gemini recommended a declarative config, subprocess-style isolation for
  side-effect-prone primitives, strict normalized finding records, range
  slicing, and tests that prove failures are caught.
- Cursor recommended a single folder-layout resolver, avoiding legacy flat-file
  batch runners for B2, treating old LLM-QG coupling as out of scope, keeping
  network checks optional, and testing read-only artifact hygiene.

## Independent Review

Reviewer identity: AGY via `scripts/ai_agent_bridge/__main__.py ask-agy`
Review model: `gemini-3.1-pro-high`
Review task id: `track-deterministic-audit-review`
Review scope: staged diff, validation summary, B2 audit headline counts,
artifact-clean statement, and old LLM-QG exclusion.
Final disposition: blocker-only review returned `UNRESOLVED_FINDINGS=0`.
Unresolved review findings: 0

## Remediation Notes

Do not auto-fix B2 content in this PR. Later remediation should shard by module
range, not by category, to avoid file conflicts. A shared route/index lane may
run separately only when it owns shared site files.

## Artifact Hygiene

No curriculum source, site source, telemetry, generated `status/`, generated
`audit/`, generated `review/`, protected config, root package, or old LLM-QG
artifact is included by this report.
