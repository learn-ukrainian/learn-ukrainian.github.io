# ACCEPTED — Grammar + word-choice gate is the priority harness track; model finetuning PARKED

**Status:** ACCEPTED
**Decided on:** 2026-07-10 (user decision, recorded same day)
**Scope:** ua-eval-harness evaluation priorities + any model-training initiative
**Review trigger:** a specific grammar/word-choice quality gap survives TWO model
rotations despite gate-driven routing, OR training hardware becomes available,
OR 2026-10-08 — whichever comes first.

## Decision

1. **Evaluation priority = grammar + lexical naturalness.** The harness's primary
   track is a gate + leaderboard dimension for (a) morphology/orthography
   (VESUM + Правопис — near-total deterministic authority) and (b) word
   choice/collocations — the "Google-translate smell" where grammar is perfect
   but the word is EN-sense-blind (приймати участь vs брати участь;
   відноситися vs ставитися). Observed live by a native speaker on free-tier AI
   output (2026-07-10): translation-quality word selection, not grammar failure.
   These checks are **corpus-independent** — they apply to any sentence any
   model generates, unlike fact-checking.

2. **Fact-checking is scoped honestly to anti-fabrication.** Our corpus is
   closed-world: we can verify "attested in what we have," never world-truth.
   The Layer A/B machinery (#4853/#4860) stays as the trust substrate — it
   stops fabricated evidence in seminar tracks and wraps ANY future LLM judge
   (including grammar-track judges) in provenance/injection contracts. It is
   not, and must not claim to be, a general fact oracle
   (`UNATTESTED_AFTER_SEARCH → AUDIT` stays).

3. **Fine-tuning / retraining (e.g. Gemma 4) is PARKED.** Reasons:
   - No training hardware for fast iteration cycles.
   - Frontier rotation outpaces any finetune we could run (GPT-5.6, Grok 4.5,
     Fable — all within one week of this decision); a finetune depreciates the
     day a better base ships.
   - Our durable asset is **verification data, not weights**: golden sets,
     UA-GEC-calibrated probes, GRAC attestation, labeled error corpora transfer
     to every new model generation for free — and they ARE the training set if
     we ever un-park this. The current path keeps the option open at zero cost.

## Alternatives rejected

| Option | Rejected because |
| --- | --- |
| Finetune Gemma 4 for Ukrainian now | No HW for iteration; depreciates against model rotation; measurement + routing achieves the learner-facing goal without training |
| Fact-checking as the primary harness track | Corpus-bounded (closed-world) — cannot cover arbitrary generated content; grammar/word-choice checks can |
| Treat nativeness/style as a hard gate | Judgment-shaped, not binary — scored/ranked dimension, advisory; only calque/collocation patterns with UA-GEC/Antonenko evidence gate |

## Consequences

- Next design cycle: `grammar-lexical-gate-design` (two deterministic cores:
  VESUM/pravopys morphology; ГРАК + UA-GEC F/Calque+F/Collocation + Antonenko +
  Балла sense-fan lexical naturalness), LLM only for the syntax-level residue
  wrapped in Layer B judge contracts. Panel-reviewed before commit (hard gate).
- New leaderboard dimension: grammar-error rate + collocation/calque error rate
  per 1000 words, deterministically scored per model — the ungameable
  "which model writes native-quality Ukrainian" measurement.
- Layer B Phase 1 continues as queued (substrate, not competitor).
