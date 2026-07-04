# PR1 Plan: Curriculum Ukrainian Quality-Gate Harness

Issue: [#2156](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2156)

## Context

The original #2156 project is a broader UA-GEC / UNLP 2027 evaluation harness.
The 2026-07-04 issue update narrows PR1 to the curriculum-facing production
spine: deterministic checks first, B1-27 calibration, compact evidence, and a
coverage report that prevents an expensive all-module LLM pass before evidence
inventory is understood.

## Fleet Inputs

- L1 AGY architecture review noted the older academic `russianism_eval` path,
  but local inspection shows PR1 should extend the existing curriculum QG stack:
  `scripts/audit/content_surface_gates.py`,
  `scripts/audit/llm_qg_canaries.py`,
  `scripts/audit/llm_qg_store.py`, and
  `scripts/audit/module_quality_audit.py`.
- L2 AGY deterministic review recommended gold B1-27 fixtures for
  `застосунок має бути відкритий`, `Застереження каже: ...`,
  `радить не робити певної поведінки`,
  `дія має дати конкретний результат чи описати процес?`,
  `доконаний вид дає результат із вікном`, and `У кухні`.
- L3 AGY evidence review recommended bounded excerpts/spans, checker version
  and config hashes, source metadata, level policy, and score-null tolerance for
  levels where numeric scores are not yet available.
- Cursor planning was rate-limited. Claude Opus dispatch failed because the
  runtime's native Claude binary is not installed; this PR will use AGY for
  required non-Codex lanes and final prompt/checker review.

## PR1 Scope

1. Add a fixture runner for curriculum QG calibration, not a standalone
   academic leaderboard.
2. Add gold fixtures for B1-27 bad text plus small A1, A2, B1+, and seminar
   calibration cases.
3. Emit compact deterministic harness evidence with module id, level policy,
   checker config/version/hash, content hash, per-dimension scores/findings,
   exact bounded spans/excerpts, checker-source metadata, and reproducibility
   metadata.
4. Keep LLM review as a residual-judgment adapter: PR1 validates prompt/checker
   behavior through canary-shaped labeled fixtures and existing LLM-QG prompt
   rules, without bulk-running modules or committing raw LLM transcripts.
5. Extend the corpus audit so git-tracked compact `qg_evidence.json` counts as
   current file evidence. Current B1-27 must no longer appear as missing QG
   evidence solely because the local SQLite DB is absent.

## Non-Goals

- No all-module LLM review.
- No leaderboard or retrospective scoring.
- No UA-GEC data import or large corpus extraction in this PR.
- No raw prompts, raw responses, `llm_qg.json`, telemetry DBs, status JSONs, or
  audit/review generated artifacts in git.
- No migration of existing `llm_qg_evidence.v1` records to a new schema.

## Target Files

- New fixture harness under `scripts/audit/`.
- New labeled fixture data under `tests/fixtures/`.
- Focused tests under `tests/audit/`.
- Small extension to `scripts/audit/module_quality_audit.py` and its tests so
  compact file evidence is counted.
- This plan and a runbook update documenting the calibration command.

## Verification

- Run the fixture harness against labeled fixtures.
- Run current B1-27 calibration and confirm PASS.
- Run `module_quality_audit.py --level b1 --format summary` and confirm B1-27
  is counted as current file evidence.
- Run targeted pytest for the new harness, module-quality audit, surface gates,
  and LLM-QG store.
- Run `git diff --check`, forbidden-file checks, and agent-trailer lint before
  opening a PR.
