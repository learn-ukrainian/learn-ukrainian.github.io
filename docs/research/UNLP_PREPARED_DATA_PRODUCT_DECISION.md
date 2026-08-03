# UNLP Prepared Data Product Decision

> **Decision date:** 2026-08-03
> **Owner:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
> **First gate:** [#6322](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6322)
> **Decision:** Continue with evidence-bearing prepared Ukrainian data products;
> do not operate or train a project model

## Decision

The Ukrainian NLP community contribution is the goal. External adoption is a
possible consequence and useful evidence, but it is neither the product nor a
completion gate.

The completed Foundry v1 is an engine and contract foundation. It is not yet
the prepared data contribution described by the North Star. The successor
program must combine the engine with useful, rights-classified data products,
deterministic evidence, protected-variation safeguards, evaluation canaries,
and model-neutral consumer recipes.

The project will not race new base-model releases by training its own weights.
It will make the data and measurement layers reusable when Gemma, Llama, Qwen,
or another open-weight family changes.

## Current product truth

The tracked production receipt establishes the following facts:

- 189,150 human-authored source records and 50,298,925 lexical words are
  inventoried across literature, grade 1–11 textbooks, articles, and Ukrainian
  Wikipedia;
- the current admitted continued-pretraining payload is 1,028 Ukrainian
  Wikipedia records in faithful and loss-masked modern views;
- 739,503 silver records are classified only as `protected` or `unresolved`;
- correction, pairwise-preference, and quality-filter views each have zero
  eligible and zero emitted records;
- 691 held-out rows remain mechanically evaluation-only; and
- the payload receipts are not equivalent to a publicly released training
  dataset or to redistribution permission.

Therefore, the correct status is **engine delivered; prepared-data product
program active**. Calling the whole objective completed would hide the most
important remaining work.

The 50.3 million lexical words are a curated complement, not a scale claim.
[Kobza](https://aclanthology.org/2025.unlp-1.14/) reports nearly 60 billion
tokens, and [Lapa](https://aclanthology.org/2026.unlp-1.14/) reports a roughly
30-billion-token filtered pretraining mixture. Words and tokens are not the
same unit, and our collection must not be presented as a replacement for those
large web-scale corpora.

## What already exists and what remains useful

The community already has large Ukrainian corpora, UA-GEC and OmniGEC
correction resources, VESUM morphology, Lapa adaptation code and datasets,
tokenizer work, quality classifiers, open-weight models, and broad benchmarks.
A duplicate generic corpus, generic document-quality classifier, translated
instruction collection, or Gemma-3 tokenizer port would add little.

The defensible complementary contribution is:

1. **Receipt and evidence truth** — make every product claim reproducible and
   expose empty, blocked, unresolved, local-only, or non-redistributable lanes.
2. **Deterministic document signals and canaries** — provenance, rights,
   period, genre, register, origin, language/script mixture, duplication,
   normalization, and failure-detection evidence that can be inspected without
   a model judge.
3. **Curated continued-pretraining complements** — rights-classified
   textbooks, literature, articles, and historical strata whose provenance and
   balance are more valuable than their raw scale.
4. **Clean-Ukrainian correction and protection data** — narrow, sourced cases
   for contextual calques, government, Russian interference, quotation,
   phonetic Russian, historical language, regional or heritage Ukrainian, and
   contested cases that must remain unresolved.
5. **Contamination-resistant evaluation** — frozen scorers and mutation
   canaries that remain outside every learning view.

Preference data and tokenizer surgery are deferred until a documented consumer
need and a non-duplicative research question exist. Lapa classifier ablation is
conditional on a later operator decision because running those classifiers is
model operation even when it is free.

## Lapa and Gemma 4: facts, inference, and unknowns

### Facts

- Lapa's public tokenizer, quality scorers, pretraining checkpoint, datasets,
  and Gemma-3-specific training templates were materially released in 2025.
- [Google launched Gemma 4 on 2026-04-02](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/).
- The [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4)
  states that official pretrained and instruction-tuned variants are
  available. Gemma 4 is not limited to QAT or GGUF inference artifacts.
- The [Lapa UNLP 2026 paper](https://aclanthology.org/2026.unlp-1.14/)
  documents adaptation of Gemma-3-12B. Its tokenizer surgery preserves
  Gemma-3 token identifiers and transfers Gemma-3 embeddings.
- The public Lapa v0.1.3 card describes alignment and pipeline fixes and says
  the rest of the model is unchanged.
- Gemma 4 changes the architecture and runtime surface: hybrid attention,
  different multimodal variants, dense and mixture-of-experts sizes, and a
  262K vocabulary. A Lapa port requires new tokenizer, embedding-transfer,
  model-config, memory, throughput, and regression validation.

### Bounded inference

The public record shows maintenance of an existing Gemma-3 asset pipeline. It
does **not** show that Lapa evaluated Gemma 4 and rejected it. Their completed
pipeline predates the new base model, while the paper records that completed
work. Porting it would be a new research and training program, not a checkpoint
replacement.

### Unknown

No public Lapa Gemma-4 checkpoint, branch, roadmap, issue, or statement of team
intent was located as of 2026-08-03. Private work may exist. The project must
not invent a motive or claim that no port is planned.

## Execution order

1. Audit current receipts and explain every empty model-ready lane without
   changing any disposition.
2. Freeze Evidence and Canaries v0 with deterministic document signals and
   deliberately planted failures.
3. Establish rights and redistribution decisions per source family and product
   capability.
4. Prepare continued-pretraining complements with exact lineage, strata,
   deduplication, contamination, and limitation receipts.
5. Build correction/protection categories only from authoritative sources and
   Ukrainian-strong linguistic review.
6. Consider Lapa classifier ablation or downstream model validation only when
   it answers a preregistered decision and receives separate authorization.

No step requires project-owned training or paid compute.

## Validation and routing

Deterministic code may establish hashes, schemas, arithmetic, source lineage,
deduplication, contamination boundaries, and canary behavior. It cannot prove
that a proposed Ukrainian correction is linguistically correct.

Use Ukrainian-strong model lanes and authoritative lexical sources for calque,
Russicism, government, orthography, register, historical-language, and
legitimate-variation decisions. Preserve disagreements and unresolved cases.
VESUM proves morphological attestation, not contextual correctness. R2U, ULIF,
Russian morphology, corpus context, heritage dictionaries, and per-dictionary
sources remain distinct evidence; no single lookup or model vote is a verdict.

The first correction/protection release requires:

- authoritative evidence for every category;
- a counter-set of acceptable Ukrainian variation;
- per-category precision and disagreement reporting;
- frozen scorer canaries; and
- a predeclared no-go threshold before any downstream experiment.

## No-go conditions

Stop or redesign a lane if it would:

- promote protected or unresolved silver into correction data by assertion;
- redistribute source bytes without capability-specific permission;
- leak evaluation cases or derivatives into learning views;
- duplicate an incumbent Lapa or UNLP resource without a measurable new
  phenomenon;
- call model agreement human or linguistic gold;
- present 50.3 million words as Kobza-scale data;
- use adoption, outreach, or a trained model as the proof that the preparation
  artifacts are internally correct; or
- spend on model operation before exact compatibility, semantic canaries, and
  a decision-changing research question are approved.

## Decision evidence

This decision combines repository receipts, the public UNLP 2025 and 2026
proceedings, official Lapa artifacts, official Google Gemma 4 release material,
and a two-round Fable/K3 adversarial discussion. The model discussion advised
the architecture; it is not Ukrainian human gold and does not replace formal
exact-head review of implementation.
