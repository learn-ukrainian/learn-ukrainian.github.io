# ACCEPTED — Public Ukrainian evaluation ownership and data boundaries

**Status:** ACCEPTED

**Decided on:** 2026-07-28

**Scope:** Public Ukrainian calque + grammar evaluation, internal quality
machinery, Hramatka feedback, Atlas evidence, and Daily Practice data
boundaries.

## Decision

GitHub epic #2156 owns the public UA-GEC-derived calque + grammar evaluation:
public gold, standard scoring, baselines, freeze/versioning, documentation,
and release.

GitHub epic #4913 remains the internal product-quality machinery lane. It owns
QG schemas, finding envelopes, reusable validators, internal quality gates,
product adapters, and private calibration. Internal findings never
automatically become public benchmark gold.

Hramatka remains under #4542, with private quality calibration under #5254.
Teachers are product users. Their accept/edit/reject actions are organic
feedback, not unpaid annotation, approval, or automatic research gold.

Atlas (#4387) supplies provenance-aware lexical and heritage evidence. Daily
Practice (#4700) uses independently rights-cleared learner material. Neither
product automatically supplies public benchmark gold.

The stable registry key `benchmark-2156` is retained for consumer
compatibility, but its epic mapping moves from the retired factuality
[epic #4639](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4639)
to canonical public-evaluation
[epic #2156](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2156).

## Shared infrastructure

The lanes may share only thin, versioned infrastructure:

- stable finding/event schemas and upstream tag vocabulary;
- span normalization;
- scorer interfaces;
- validator/configuration versions;
- VESUM and heritage evidence semantics;
- provenance conventions.

They do not share data inventories by default.

## Data separation

The following remain separate:

- frozen public benchmark gold;
- private Hramatka regression cases;
- teacher feedback and lesson payloads;
- Atlas source sentences;
- Daily Practice exercise inventory;
- model responses and results;
- any future training data.

Public benchmark cases must not enter Daily Practice or training. Atlas
evidence may cause abstention or a contested heritage/regional warning, but it
must not silently override upstream UA-GEC gold or become a boolean
"Russianism truth" layer.

## Current capability correction

The current 52 rows are train-derived development fixtures, not public
held-out gold. The evaluator is mock-only and the metrics are custom rather
than standard GEC scoring. Historical issue #5608 and PRs #5610/#5633 remain
prototype receipts; they do not satisfy #2156 completion.

## Exclusions

This decision excludes:

- BIO, factuality, and cultural/tool-grounded fact checking;
- synthetic corruption;
- DPO, fine-tuning, and training;
- broad curriculum evidence backfill;
- a general Ukrainian leaderboard;
- teacher/community annotation dependencies;
- automatic transfer of Hramatka, Atlas, or Practice data into public gold.

## Consequences

The ordered public queue is #5966 → #5967 → #5636 → #4626 → #4541. Final
dataset size is determined by the frozen upstream eligibility predicate, not
an arbitrary quota. Public release requires attribution, limitations,
contamination policy, clean-clone proof, and separation from all private or
product data.

This decision supersedes
`2026-07-07-benchmark-public-release-parked.md` only for public calque +
grammar evaluation ownership. The retired factuality/BIO release program
remains excluded and closed as not planned.
