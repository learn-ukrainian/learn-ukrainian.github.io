# Boundary: #2156 harness vs the lang-uk Ukrainian LLM leaderboard (#4289)

- status: agreed boundary (documents the #2156 scoping decision; no new leaderboard is built here)
- decided: 2026-07-05 (elevated from follow-up #4289, user directive 2026-07-05)
- leaderboard: <https://huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard>

## The one-sentence boundary

**lang-uk ranks how capable a model is in Ukrainian; #2156 measures whether specific generated Ukrainian is
contaminated (calques, contact-grammar errors, register defects) with span-level, gold-anchored evidence.**
Neither substitutes for the other, and this repo will not build a general-capability leaderboard.

## What #2156 evaluates that lang-uk does not

| #2156 axis | shape | anchor |
|---|---|---|
| Calque / Russianism contamination | span-level findings (`excerpt` must be an exact substring) | UA-GEC F/Calque gold (CC-BY-4.0) + Антоненко-Давидович + VESUM/heritage merge |
| Contact grammar (G/Case, G/Gender, …) | span-level findings | UA-GEC G/* gold |
| Naturalness / register / level fit | curriculum-facing judgments, CEFR-aware | reviewer prompt profiles + deterministic surface gates |
| Seminar factual grounding | tool-verified claim audit (CONFIRMED/REFUTED_BY_CONTRADICTION/UNATTESTED_AFTER_SEARCH/CONTESTED/UNVERIFIED_INSUFFICIENT_SEARCH) | sources MCP (wiki/literary/heritage/ЕСУМ/Грінченко/GRAC) — design brief v2, 2026-07-05 |
| Compact module evidence | `ua_contact_quality_evidence.v1` records (schema.md) with content hash, source_lang, scorer provenance | `scripts/audit/qg_schema.py` |

Empirical demonstration of why capability ranking is not contamination measurement: gemma-4-26b is **#1 on
the lang-uk leaderboard**, and gemma-4-31b scored deterministically perfect on our surface gates — yet
fabricated folk-culture specifics in seminar content that only tool-grounded fact-checking caught
(`model-evidence.md`, 2026-07-04/05). Capability-high ≠ contamination-free.

## What is delegated to lang-uk (never duplicated here)

- General Ukrainian LLM capability measurement (translation, reasoning, QA, IFEval) and its maintenance.
- Broad all-model benchmark ranking, including UA-fine-tuned open weights (Lapa, MamayLM).
- Public leaderboard infrastructure and submission workflow.

When a #2156 conversation drifts toward "which model is best at Ukrainian overall" → the answer lives at
lang-uk; we may *cite* it (as the model-evidence doc does) but never re-measure it.

## Metadata bridge (small, interop-only)

To make #2156 findings comparable against lang-uk rows without copying their scope, each harness run
records — all already present in `ua_contact_quality_evidence.v1` or the run store:

1. **Exact model identity** — `reviewer_model_id` (run store `llm_qg_runs`) / writer model slug,
   provider-qualified (e.g. `openrouter/google/gemma-4-31b-it`) — joinable to a lang-uk leaderboard row
   when one exists.
2. **Schema + gate version** — the schema identity (`ua_contact_quality_evidence.v1`) and the workflow
   `gate_version` (`qg_workflow.v1` today; v2 lands with the reviewer-tooling PRs) — so cross-citations pin
   the harness contract they were measured under.
3. **`content_sha` + `source_lang`** (schema record fields) — reproducibility anchors lang-uk doesn't need
   but any joint analysis does.

That is the whole bridge. No shared scoring, no synced releases, no scraped leaderboard data.

## Non-goals (restating #4289's)

- No general-purpose Ukrainian LLM leaderboard in this repo.
- No all-model capability ranking under #2156 (the step-3 bakeoff ranks *reviewer configurations* on ~3-4
  seminars — a harness-calibration exercise, not a capability leaderboard).
- No broad capability claims from curriculum QG scores alone — a model that reviews seminars well is not
  thereby "good at Ukrainian", and vice versa (the gemma result cuts both ways).
