# Ukrainian Data Foundry: Clean-Ukrainian Tool and Training Recipe

> **Owner:** [#6171](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6171)
> under [Foundry Phase 2–4 #6164](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6164)
> **Status:** Release contract; paid training is optional and is not on the
> critical path
> **Does not authorize:** model download, accelerator rental, training, upload,
> dataset publication, or automatic rewriting of source text

## What we are shipping

The primary product is a corpus-portable preparation tool and recipe that help
an open-weight team teach a current or future base model cleaner Ukrainian. It
does not depend on Gemma 4 and remains useful when a stronger model appears.

The tool must let a consumer:

1. inventory and destination-admit its own Ukrainian sources;
2. find Russian interference, mixed or surzhyk candidates, phonetic Russian,
   valid-word calques, grammar/government problems, and morphology gaps;
3. keep quoted Russian, historical language, regional or dialectal Ukrainian,
   heritage forms, proper names, and uncertain cases out of an automatic
   deletion path;
4. build separate modern-learning, faithful-source, correction, preference,
   quality-filter, and held-out-evaluation views; and
5. produce exact tokenizer, contamination, runtime, and cost receipts before
   anyone rents hardware.

This delivery addresses the Foundry's calque, grammar/agreement, and morphology
requirements and incorporates Oleksiy's recorded recommendation to use the
ULIF synonym tab. Heritage evidence prevents de-Russification from erasing
real Ukrainian. The current evidence stack includes VESUM, Russian morphology,
R2U, Ukrainian corpus context, local Грінченко/ЕСУМ/СУМ-11 evidence, and
bounded ULIF or per-dictionary `slovnyk.me` evidence. No single source is a
verdict.

## What our corpus is

The recovered public/external corpus is inventory-classified human-authored
Ukrainian source material:

| Source family | Records | Lexical words |
| --- | ---: | ---: |
| Literature | 137,723 | 36,031,758 |
| School textbooks, grades 1–11 | 49,193 | 9,564,143 |
| External articles | 1,205 | 1,837,518 |
| Ukrainian Wikipedia | 1,029 | 2,865,506 |
| **Total** | **189,150** | **50,298,925** |

This is recovered Ukrainian source data, mechanically distinct from the
project's synthetic and translated collections. The
[training-usability decision](../research/UKRAINIAN_CORPUS_TRAINING_USABILITY_DECISION.md)
verified all 137,723 raw literary rows against retained source locators and
core metadata, and verified the textbook family against 158 chunk files, 170
PDFs, the selection ledger, downloader, and page-URL map. The operator has
approved these retained human-authored families for local research and model
learning toward the project goal.

Local model learning, raw-source redistribution, public dataset release, and
public weight or adapter release are independent capabilities. The last three
remain separately gated; they do not block preparation or local continued
training. The existing exporter still implements the older combined gate and
must be corrected before it can emit the newly approved local-training view.

Historical and literary text must not be flattened into contemporary standard
Ukrainian. A training consumer receives explicit strata and chooses the mixture:

- contemporary modern-learning text;
- faithful modern-literary text;
- historical or heritage text;
- regional, dialectal, and marked-register text;
- quoted Russian or other-language passages;
- suspected modern interference or mixed-language passages; and
- protected or unresolved evidence.

The tool preserves source text and emits views; it does not silently “clean”
the only copy.

## End-to-end recipe

### 1. Admit sources for the intended capability

Validate source identity, provenance, privacy, human or synthetic origin,
contamination, and the exact destination. Record permissions separately for
local model training, raw-source redistribution, dataset publication, and
model publication; an unknown redistribution status must not be converted into
a denial of an independently approved local-training use. Keep machine-
generated lessons, translations, and synthetic research evidence in separate
origins. Do not promote benchmark text or its derivatives into a training
view.

### 2. Route language-contact evidence

Run the contextual detector over every record. Ordinary Ukrainian with no
positive signal remains source text rather than becoming invented “gold.”
Candidates retain exact offsets, discourse role, source period, evidence, and
one of the explicit dispositions: suspected modern interference, mixed or
phonetic Russian, quoted Russian, historical or marked language, protected
Ukrainian, proper name, OCR/encoding, other language, or unresolved.

The production CLI is:

```bash
.venv/bin/python -m scripts.projects.open_model_data.language_contact_detector \
  --config data/projects/open_model_data/detector/language_contact_config_v1.json \
  --input-root /absolute/path/to/learn-ukrainian \
  --summary-output batch_state/foundry/language-contact-receipt.json \
  --candidates-output batch_state/foundry/language-contact-candidates.jsonl
```

The release candidate must add a documented adapter for a consumer-owned
JSONL corpus so that a team does not need this project's private database.

### 3. Attach evidence without inventing gold

The silver factory validates the detector artifact, rejects evaluation
contamination, performs cache-only evidence enrichment, and retains uncertainty:

```bash
.venv/bin/python -m scripts.projects.open_model_data.silver_evidence_factory \
  --candidates batch_state/foundry/language-contact-candidates.jsonl \
  --detector-receipt batch_state/foundry/language-contact-receipt.json \
  --output batch_state/foundry/language-contact-silver.jsonl \
  --receipt-output batch_state/foundry/language-contact-silver-receipt.json
```

Model proposals may suggest alternatives or expose disagreement. They remain
model-only or silver evidence; they do not certify their own Ukrainian.

### 4. Build disjoint model views

Export source text and labeled data through different manifests:

- `continued_pretraining`: admitted human-authored text only;
- `correction_instruction`: an observed source and supported target;
- `preference`: explicit chosen/rejected alternatives;
- `quality_filter`: text-free or rights-safe quality decisions;
- `heldout_evaluation`: evaluation only, never training.

Every row reconstructs to its source, admission, evidence, derivation, and
destination. A missing eligible lane stays empty; it is never backfilled with
fixtures or evaluation data.

### 5. Measure the exact tokenizer

Pin the base-model revision and tokenizer bytes, then measure token count,
lexical fertility, byte fallback, word and paradigm fragmentation, record
length, and character-to-token mask projection. Tokenizer replacement or
surgery is optional: perform it only when a frozen comparison shows a useful
efficiency or morphology benefit that outweighs embedding disruption and
compatibility cost.

### 6. Freeze a model-neutral training manifest

For each view, record the objective, immutable model and tokenizer revisions,
framework and dependency lock, rendering template, loss policy, split
namespace, sequence length, packing, precision, seed, optimizer settings,
epochs, and an explicit `training_authorized: false` state. The existing
`training_recipe_config_v1` and `training_recipe_manifest_v1` contracts are
preparation contracts; generating them does not start training.

If a separately authorized model experiment occurs, keep these roles separate:

1. continued pretraining on destination-admitted human-authored text;
2. optional correction/instruction or preference tuning on eligible,
   evidence-graded records; and
3. evaluation on mechanically isolated grammar, calque, interference,
   morphology, no-change, and protected-variation inventories.

Do not combine these roles in an authorized run: otherwise a result cannot
identify which data treatment helped or caused harm.

### 7. Reproduce without an accelerator

From a fresh checkout or clean environment, rebuild schemas, receipts,
admissions, detector regression cases, silver evidence, views, recipe
manifests, tokenizer diagnostics where tokenizer files are locally available,
and evaluation-firewall checks. This no-training reproduction is the required
release gate. A trained adapter is an optional later artifact.

## How long and how much would training take?

The recipe makes the cost measurable; it does not make one unmeasured price
honest. For a particular checkpoint and hardware configuration:

```text
wall-clock hours = train tokens × epochs / measured aggregate tokens per second / 3600
compute cost = wall-clock hours × accelerator count × provider price per hour
```

Add storage, data transfer, evaluation inference, taxes, and a declared failed-
run allowance separately. Measure aggregate throughput with the exact model,
sequence length, precision, optimizer, and adapter/full-parameter policy before
approving the full run.

The pinned Gemma 4 IT tokenizer produced 7,696,734 non-special tokens from
2,778,111 lexical words in the 1,028-record, deduplicated training-eligible
Wikipedia view: 2.7705 total text tokens per lexical word. The admitted source
family has 1,029 records / 2,865,506 lexical words; the view exporter excludes
one long near-duplicate, as recorded in the
[model-view runbook](ukrainian-data-foundry-model-views.md). Applying the
post-dedup observed ratio to the pre-dedup 50,298,925-word corpus inventory
gives a rough **planning extrapolation of about 139.35 million tokens for one
pass**. It is not a current training artifact: the exact local-training views
have not yet been exported, their deduplication and masking will change the
denominator, and literary/historical genres may tokenize differently.

Using Hugging Face Jobs list prices retrieved on 2026-08-02 of USD 2.50/hour
for one A100 80 GB and USD 1.80/hour for one L40S 48 GB, a one-GPU, one-epoch
sensitivity table is:

| Measured throughput | Wall time | A100 list compute | L40S list compute |
| ---: | ---: | ---: | ---: |
| 50 tokens/s | 774 hours | USD 1,935 | USD 1,394 |
| 100 tokens/s | 387 hours | USD 968 | USD 697 |
| 200 tokens/s | 194 hours | USD 484 | USD 348 |

These rows are arithmetic scenarios, not a promise that Gemma 4 training fits
or reaches those speeds on either device. Three epochs triple the time and
compute. Multiple accelerators reduce wall time only to the extent scaling is
efficient; their hourly costs multiply. Full-parameter continued pretraining
has a very different memory and compute envelope from QLoRA. The exact clean
microbenchmark and model revision must replace this table before any spending
decision.

## Could the proof run on an unused M1?

Yes, if the proof uses a Gemma 4 size that matches the machine's unified memory
and uses an Apple-Silicon training stack. It does not mean the current Gemma 4
31B CUDA treatment can be copied to the Mac.

Google's current
[Gemma 4 memory table](https://ai.google.dev/gemma/docs/core#parameter-sizes-and-quantization)
gives approximate Q4 inference loads of 2.9 GB for E2B, 4.5 GB for E4B,
6.7 GB for 12B, 14.4 GB for 26B A4B, and 17.5 GB for 31B. Context and
fine-tuning add memory beyond those values. Record the exact M1 variant,
unified memory, free storage, and macOS version before selecting anything.

| M1 unified memory | First candidate | What it can establish |
| ---: | --- | --- |
| 8 GB | Gemma 4 E2B Q4 | Whether the complete local pipeline can execute at all |
| 16 GB | Gemma 4 E4B Q4; E2B fallback | A real small-model Ukrainian before/after proof; not 31B compatibility |
| 32 GB | Gemma 4 12B Q4; E4B fallback | A stronger local proof if peak memory and reload pass |
| 64 GB or more | Benchmark 12B first; consider 31B second | 31B remains conditional on measured training memory and speed |

Apple's [MLX-LM](https://github.com/ml-explore/mlx-lm) supports LoRA and QLoRA
on Apple silicon. Release `v0.31.2` added Gemma 4 support, while the
[MLX-LM LoRA guide](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md)
documents quantized-model training and memory controls. The existing #6170
runner is not portable: it pins CUDA, an NVIDIA L40S, BitsAndBytes NF4, and a
31B checkpoint. Preserve that runner and create a separately pinned MLX path
only after the exact Mac and checkpoint are approved.

A useful local proof has five measured steps:

1. capture machine, model, tokenizer, framework, quantization, and storage
   receipts;
2. run the frozen baseline evaluation and protected-variation probes;
3. perform a synthetic one-step update, save, restart, reload, and re-evaluate
   only as a hardware preflight;
4. train on a real, stratified Foundry slice and compare the reloaded adapter
   with the untouched checkpoint on exactly the same held-out evidence; and
5. run a full-corpus pass only if the measured throughput, peak memory, and
   preliminary Ukrainian result justify its wall time.

The fourth step is the minimum linguistic proof. A successful synthetic update
alone proves only that MLX can write and reload an adapter.

Gemma 4 is the first candidate because the project already has its tokenizer,
baseline, and treatment contracts. Another Western open-weight model is a
fallback only if the same frozen Ukrainian baseline, tokenizer diagnostics,
memory preflight, and license check make it a more credible proof target. A
fallback result validates the Foundry path for that model; it does not prove a
Gemma 4 treatment.

For scale, Lapa reports about 30 billion filtered pretraining tokens and a
56-H100 training setup for its Gemma 3 adaptation. Our 139-million-token
one-pass extrapolation is roughly 1/215 of that token volume. Our collection is
valuable for its curated textbooks, literature, historical strata, provenance,
and failure evidence; it is not by itself a replacement for a tens-of-billions-
of-tokens language corpus.

## Why Gemma 4 can lead and still make bad Ukrainian

Gemma 4 can improve an aggregate Ukrainian leaderboard because it is a newer
general model with stronger reasoning, instruction following, architecture,
and broad multilingual transfer. That does not prove that it received a
better clean-Ukrainian training mixture; Google does not publish a Ukrainian-
specific pretraining share.

The `lang-uk` leaderboard aggregates translation, summarization, question
answering, reasoning and knowledge, mathematics, and instruction following.
Its own roadmap still lists tokenizer efficiency separately. It does not
comprehensively measure whether free generation is free of surzhyk, semantic
calques, Russian morphology, bad government, or unwanted normalization of
heritage Ukrainian. A model can therefore rank first overall and still produce
errors such as Russian `звучит` inside an otherwise Ukrainian answer.

This is why the Foundry should not race one model generation. The detector,
protected-variation evidence, data views, tokenizer census, and training recipe
can be rerun for Gemma 4, Gemma 5, or another open model. A local adapter ages
quickly; the means to prepare and measure Ukrainian transfer forward.

## Decision rule

Ship the tool, contracts, recipes, clean-run receipt, limitations, and consumer
guide first. Do not wait for paid training. Consider a model run only when a
specific team or operator needs compatibility evidence for an exact current
checkpoint, the admitted data are large enough for the named question, a
microbenchmark supplies the real cost, and present-tense authorization covers
that exact spend. A newer model release changes the checkpoint, not this plan.

## Primary references

- [Lapa: Data-Efficient Adaptation of Multilingual LLMs to Ukrainian](https://aclanthology.org/2026.unlp-1.14/)
- [Gemma 4 model card](https://huggingface.co/google/gemma-4-31B-it)
- [`lang-uk` Ukrainian LLM leaderboard methodology](https://huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard/blob/main/README.md)
- [Hugging Face Jobs pricing](https://huggingface.co/docs/hub/jobs-pricing)
- [VESUM / `dict_uk`](https://github.com/brown-uk/dict_uk)
