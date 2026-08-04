# Ukrainian Data Foundry: North Star

> **Status:** Operator-confirmed strategic direction; evidence snapshot
> **Approval receipt:** Operator issued **GO REALIGN** for the stream and issue
> realignment on 2026-07-30; recorded in
> [PR #6060](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/6060).
> Operator approved the Ukrainian Data Foundry architecture, replacement issue
> chain, and first implementation on 2026-07-31, then issued **GO REALIGN AND
> EXECUTE PHASE 2–4** on 2026-08-01. On the same date, the operator recorded
> that this is a solo project with neither budget nor access to a three-person
> Ukrainian review panel and directed the Foundry to remove that unavailable
> labour from the critical path. On 2026-08-02, the operator directed the
> Foundry to ship the clean-Ukrainian preparation tool and consumer training
> recipe without project-funded or project-operated model training. Training
> belongs to downstream teams that choose to use the released artifacts. On
> 2026-08-03, after the only project-owned Gemma 4 run was reclassified as an
> invalid runtime-failure receipt, the operator clarified that community-useful
> prepared data is the goal and adoption is only a possible side effect. The
> completed Foundry engine therefore remains a foundation for successor epic
> #6321 rather than the end of the prepared-data program.
> **Recorded:** 2026-07-30; Foundry direction and existing-asset baseline
> refreshed 2026-08-03
> **Applies to:** Ukrainian model evaluation, dataset work, training-data
> preparation, and UNLP ecosystem monitoring
> **Does not authorize:** model training, mixing evaluation gold into training
> data, model-weight publication, external researcher contact, provider
> inference, or paid compute

## North star

Our ultimate goal is to help AI produce measurably better, authentically
Ukrainian language.

We will pursue that goal through evidence-bearing prepared Ukrainian data
products built on an open Ukrainian Data Foundry. Ukrainian and open-weight
model teams must be able to run the infrastructure on our corpus, their
corpora, or other licensed collections. The program provides:

- trusted and well-documented data;
- morphology-aware coverage and diagnostics;
- narrow, credible evaluations of important failure modes;
- reproducible preparation and training recipes; and
- evidence that distinguishes standardization errors from legitimate
  historical, regional, dialectal, and register variation.

Community linguistic usefulness is the success criterion. External adoption
is welcome evidence that the products are usable, but it is not the product and
not a completion gate. Each shipped artifact must name one concrete consumer
decision or use case it enables, without requiring outreach or external use.

We are not trying to win by training and maintaining our own general-purpose
model weights. Base models can leapfrog a local fine-tune in one release.
Curated data, provenance, evaluation, and tooling transfer to every new model
generation.

This direction prioritizes transferable data, grammar, lexical naturalness,
and evidence over owning or producing model weights. Foundry implementation
completion stops before model download, accelerator rental, optimizer
execution, adapter production, or weight upload. The later #6273 Gemma 4
Hugging Face Jobs attempt completed structurally but failed source-aware output
integrity and is retained only as an invalid runtime-failure receipt. It does
not authorize a rerun or training. The accepted boundary between public
evaluation gold, private product data, and training data remains intact.

## Solo-operator execution model

The Foundry must be executable by one operator. It cannot make paid or donated
review labour or accelerator access a prerequisite for useful source
preparation, model-ready data, or a complete release.

The production evidence lanes are therefore distinct:

- **Admitted human-authored text** supports continued pretraining after source,
  rights, privacy, origin, destination, and contamination gates pass. It does
  not require new linguistic annotation.
- **Evidence-backed silver** combines preserved context with deterministic
  lexical, morphological, corpus, source, and bounded dictionary evidence.
  Cross-family model proposals may add alternatives and surface disagreement,
  but model agreement is never linguistic authority. Every record retains its
  evidence grade, uncertainty, and protected or unresolved disposition.
- **Hramatka feedback** may add consented teacher observations over time. It is
  useful product evidence, but its arrival rate, selection effects, and privacy
  constraints make it an optional upgrade rather than a critical-path gate.
- **Qualified-human gold** remains a supported optional upgrade. The existing
  blinded two-reviewer plus distinct-resolver contract applies only when the
  project later chooses to claim qualified-human gold; no current milestone or
  release requires that claim.

A future evidence-backed silver product may be used in an explicitly silver,
provenance-complete downstream experiment only after its destination admission
passes. The current 739,503 protected or unresolved records are not admitted
correction data. Silver must never be reported as human gold, native-speaker
acceptance, reviewer reliability, or proof that every proposed correction is
correct.

The Foundry engine can credibly promise reusable preparation, diagnostics,
evidence, model-ready interfaces, evaluation isolation, and reproducible
consumer recipes. It cannot promise that a downstream treatment will make an
LLM fluent. The successor program must now turn those interfaces into useful,
rights-classified data products. Consumer training results remain external
evidence and are never a prerequisite for completing an internal data product.

## GitHub execution homes

- [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
  owns the active evidence-bearing prepared-data program. Its ordered path is
  receipt audit, deterministic evidence and canaries, rights-gated corpus
  complements, an evidence-graded clean-Ukrainian correction/protection pack,
  and only then optional downstream ablation under separate authorization. The
  governing decision is the
  [UNLP prepared-data product decision](../research/UNLP_PREPARED_DATA_PRODUCT_DECISION.md).
- [#6322](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6322)
  owns the completed Phase 0 receipt audit. It explained the three empty
  correction-family lanes and froze product truth without weakening a
  disposition.
- [#6324](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6324)
  owns completed Evidence and Canaries v0: a deterministic, text-free signal
  manifest over all 189,150 public/external human-authored records.
- [#6327](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6327)
  owns completed Phase 2: capability decisions, source-stratified complement
  planning, resolvability keys, and the evidence-resolution worklist. It does
  not authorize source publication, training, or a local-hydration bypass for
  unresolved learning rights. Its complete production build covers all 189,150
  Phase 1 records, binds 42,302 text-free source/work locators, and creates
  3,511 exact evidence-resolution tasks. This is a capability map and plan, not
  a corpus publication or a Ukrainian-quality judgment.
- [#6333](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6333)
  owns active Phase 3: an evidence-graded clean-Ukrainian correction/protection
  pack. It must distinguish Russian interference, bad morphology, contextual
  calques, and government errors from quotation, phonetic Russian, Surzhyk,
  historical or archaic Ukrainian, dialect, regional language, folklore, and
  unresolved contact-language cases. Evidence channels, rather than pack
  labels, are authoritative; without qualified-human adjudication, no label is
  gold or authoritative.

- Closed [#6164](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6164)
  owns the completed Foundry-engine Phase 2–4 implementation: real corpus
  admission, production contextual language-contact detection, evidence-backed
  silver with an optional qualified-human upgrade, model-ready interfaces and
  bounded CPT receipts, a model-neutral clean-Ukrainian tool, reproducible
  consumer training recipe, and no-training release candidate. It closed after
  PRs #6266, #6268, and #6271.
  Closed
  [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
  owns the completed interfaces, profiler, exporters, recipes, and synthetic
  reference build on which this production program depends.
- Closed [#6273](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6273)
  owns the public evaluation release and invalid Gemma 4 runtime-failure
  correction. The frozen suite remains valid; the saved model output is not
  scoreable and proves neither Gemma ability nor adoption. No rerun is
  authorized.
- [#6057](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6057)
  is closed as not planned under the solo-operator model while preserving the
  completed v0.2 error analysis and frozen design. Its reviewer-intensive
  acquisition is parked; the existing v0.1.1 and licensed external evaluations
  remain the current measurement surfaces.
- [#4913](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4913)
  owns internal Ukrainian validators, quality gates, product adapters, and
  private calibration.
- [#4542](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4542)
  owns Hramatka teacher-product behavior and production-path qualification.
- [#2156](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2156)
  remains closed with the immutable public v0.1.1 evaluation freeze.

## Why the size of Ukrainian matters

The operator's current working estimate is about 254,000 modern Ukrainian
lemmas before historical vocabulary and other extensions. This estimate must
receive a citable source and a precise definition before external use.

Current local project documentation reports approximately 409,000 VESUM lemma
records and 6.7 million generated forms. These figures depend on the VESUM
version and on what is counted as a distinct lemma or form. The upstream VESUM
project describes a dictionary of words, paradigms, part-of-speech tags, style
markers, and generated word forms. It includes markers such as rare, archaic,
slang, and discouraged usage. Its data are CC BY-NC-SA 4.0, which constrains
redistribution and commercial training uses.

Millions of possible forms do **not** mean that a model must memorize every
form. A subword model can learn productive declension, conjugation, agreement,
and word formation. Proper Ukrainian preparation must nevertheless expose
enough balanced, contextual evidence for the model to learn those rules rather
than merely imitate the most frequent web forms.

This changes the data problem:

- a lemma list is not a training corpus;
- a generated form without context does not teach sense, government,
  collocation, register, stress, or discourse use;
- raw frequency alone underrepresents rare paradigm cells and productive
  patterns;
- indiscriminate oversampling can make archaic, dialectal, or rare forms look
  falsely ordinary; and
- filtering Russian influence must not erase legitimate cognates, heritage
  forms, regional Ukrainian, or code-switching research data.

The useful unit is therefore a **provenanced contextual example with linguistic
attributes**, not an isolated word form.

## What the Ukrainian NLP community already has

This is an orientation map, not an exhaustive catalog. The weekly Ukrainian
NLP ecosystem watch remains the mechanism for keeping it current.

| Layer | Important existing assets | What they already solve |
| --- | --- | --- |
| Morphology and lexical tooling | [VESUM / `dict_uk`](https://github.com/brown-uk/dict_uk) | Large inflectional lexicon, generated paradigms, POS tags, and usage markers |
| Large native-text corpora | [Kobza](https://aclanthology.org/2025.unlp-1.14/), UberText and other `lang-uk` corpora | Pretraining-scale Ukrainian text; Kobza reports nearly 60B tokens and deduplication |
| Human correction data | [UA-GEC](https://github.com/grammarly/ua-gec) | Professionally annotated Ukrainian grammar and fluency corrections with metadata |
| Silver correction data | [OmniGEC](https://aclanthology.org/2025.unlp-1.17/) | Larger automatically corrected Ukrainian and multilingual GEC data |
| Open model adaptation | [Lapa](https://aclanthology.org/2026.unlp-1.14/) | Reproducible Gemma 3 adaptation: tokenizer surgery, quality filtering, instruction-data construction, models, data, and code |
| Language proficiency evaluation | [UNLP gold-standard benchmark](https://aclanthology.org/2026.unlp-1.12/) and the [`lang-uk` Ukrainian LLM leaderboard](https://huggingface.co/datasets/lang-uk/ukrainian-llm-leaderboard-results) | Broad grammar, vocabulary, orthography, and model comparison |
| Minimal-edit GEC evaluation | [UNLP prompting study](https://aclanthology.org/2026.unlp-1.13/) and the UNLP 2023 UA-GEC shared task | Standard GEC scoring, strong fine-tuned baselines, and detailed prompt baselines |
| Specialized datasets and benchmarks | [ZNO-Vision](https://aclanthology.org/2025.unlp-1.2/), [lexical stress and phonemization](https://aclanthology.org/2025.unlp-1.11/), [native paraphrases](https://aclanthology.org/2026.unlp-1.17/), UD treebanks, NER, sentiment, manipulation, idiom, translation, RAG, ASR, and dialect resources | Strong coverage of many bounded Ukrainian tasks and modalities |

The conclusion is important: **the community does not lack datasets in
general**. A new contribution must identify the exact uncovered phenomenon,
consumer, license, and evaluation question.

Before Phase 3 calls a phenomenon uncovered, it must measure the proposed cases
against the current [LanguageTool Ukrainian rule module](https://github.com/languagetool-org/languagetool/tree/master/languagetool-language-modules/uk)
and related `nlp_uk`/R2U-community tooling. This comparison verifies a measured
delta; it does not assume exact present coverage by those tools.

## Gaps that remain valuable

### 1. Contextual lexical naturalness and language-contact errors

Generic GEC is already well served. There is still room for expert-grounded
data about:

- semantic calques and sense transfer;
- collocations and case government;
- bureaucratic and translation-like constructions;
- minimal pairs that separate acceptable Ukrainian from contextually wrong
  usage; and
- corrections with more than one acceptable Ukrainian realization.

This is where the current public calque-and-grammar evaluation is relevant, but
its 677 error-containing sentences are only a first instrument.

### 2. Protection against linguistic erasure

A decolonizing dataset cannot be a blacklist of forms that resemble Russian.
It needs hard positive examples for:

- authentic cognates;
- historical and heritage forms;
- regional and dialectal Ukrainian;
- conversational and marked registers; and
- contested cases that should remain unresolved rather than be normalized
  automatically.

Each decision needs a source, scope, confidence, and disposition. This is an
area where our Atlas evidence model and conservative VESUM use can be unusually
helpful.

### 3. Morphology-aware coverage rather than word-count scale

Training and evaluation packages need diagnostics by:

- lemma frequency band;
- part of speech and paradigm cell;
- agreement and syntactic dependency;
- seen versus unseen lemma;
- rare but productive inflection;
- tokenizer fertility and fragmentation; and
- modern, historical, regional, and register strata.

VESUM can verify forms and organize coverage. Its licensing and dictionary
semantics mean we must not simply convert it into unrestricted training text.

### 4. Provenance-rich, rights-clear, quality-scored source data

Large corpora exist, but their scale does not eliminate source-quality,
rights, duplication, machine-translation, Russian-influence, domain-balance,
or historical-balance questions. Open model teams benefit from:

- per-document provenance and stable source identifiers;
- explicit license and redistribution status;
- time, domain, genre, region, and register metadata;
- deduplication and contamination receipts;
- language and translation-origin confidence; and
- quality-filter labels with auditable examples.

### 5. Clean, contamination-resistant evaluation

The current public release contains only sentences with at least one in-scope
error. Future releases need:

- no-change controls;
- hard positives that must not be "corrected";
- more expert references for legitimate alternatives;
- sequestered or regularly renewed test material;
- category-balanced reporting; and
- uncertainty estimates and frozen run metadata.

Benchmark cases must remain outside training data.

### 6. Model-ready interfaces

Researchers should not have to reverse-engineer a corpus to use it. The same
reviewed source records should support separate, reproducible exports for:

- continued pretraining;
- supervised correction or instruction tuning;
- preference data;
- quality-filter training; and
- held-out evaluation.

Those exports must stay distinct and carry lineage back to the source record.

## What this project can credibly contribute

### Existing-asset baseline

The [existing-corpus recovery audit](../research/EXISTING_CORPUS_ASSET_RECOVERY_AND_LINEAGE_AUDIT.md)
now establishes a deterministic baseline before any acquisition. The
public/external inventory-classified `human_authored_source` view contains
189,150 database rows and 50,298,925 lexical words; the separate private-
reference view contains 5,786 rows and 681,925 words. Google Drive retains 229
literary JSONL source files,
which reconcile by filename stem to all 229 literary database source groups.
The repository also retains 12,347 tracked archive files and six historical
FOLK package versions with Git recovery locators.

This inventory preceded the current capability-specific decision. Its zero
source-record admissions and zero redistribution-cleared assets described the
old combined gate, not corpus authenticity or downstream training fitness. It
keeps
human-authored, machine-generated direct Ukrainian, machine-translated,
private-reference, evaluation-only, and unknown-origin material mechanically
separate. The invalid 5,000-record export may locate an underlying work but
cannot establish source, edition, rights, acquisition lineage, or contamination
status.

The subsequent
[training-usability audit](../research/UKRAINIAN_CORPUS_TRAINING_USABILITY_DECISION.md)
found source locators and core metadata on all 137,723 raw literary rows and
reconciled the textbook family to retained chunks, PDFs, acquisition code,
selection metadata, and page URLs. The operator approved these retained human-
authored sources for downstream research and continued model learning.
Raw-source
redistribution, dataset publication, and model publication remain independent
later decisions. The project verdict is **CONTINUE**.

### Already available

- Public Ukrainian calque-and-grammar evaluation release `0.1.1`: 677 held-out
  UA-GEC sentences, 918 acceptable references, 1,608 in-scope annotations,
  exact-edit scoring, reproducibility receipts, and saved closed- and
  open-weight baselines.
- A working provenance and evidence architecture for heritage-sensitive
  language judgments.
- A weekly Ukrainian NLP ecosystem watch.
- A 5,000-record literary export retained only as a locator for independently
  reconstructing original-source evidence; it is not provenance authority or a
  candidate training collection.

### Completed Foundry engine and evaluation release

The production corpus audit, admission baseline, full-corpus detector,
evidence-grade silver/protection factory, separate model views, tokenizer
diagnostics, and reference build completed under #6166–#6169. PR #6248 supplied
the corpus-usability decision. #6171 and PR #6266 then completed capability-
specific admission, restored locators, the consumer JSONL and public CLI,
contextual non-erasure routes, evidence surfaces, disjoint views, receipts, and
clean reproduction. PR #6268 added the frozen 4,000-case, fourteen-track open-
weight evaluation; PR #6271 added the Lapa and lang-uk adapters.

Issue #6273 later published the frozen evaluation package. Its attempted Gemma
4 execution completed at the provider and transport level but failed the
source-aware semantic integrity replay on every row. The saved bytes are an
invalid runtime-failure receipt, not a baseline, model result, or adoption
receipt. Issue #6273 is closed and authorizes no rerun.

The 4,000 cases are not 4,000 independent human judgments. The suite contains
1,000 UA Eval 0.1.1 human-gold error anchors, 1,000 deterministic controls
derived from accepted targets, and 2,000 evidence-graded protected or unresolved
silver cases. Closed #6170 remains historical preregistration only. The
reviewer-intensive v0.2 acquisition remains closed as not planned. Public
evaluation data remains mechanically isolated from every model-learning or
derived-rule view.

### Completed Foundry v1 reference build

The #6119–#6123 implementation chain now has an executable reference build. It
reproduces the complete 189,150-record / 50,298,925-word morphology profile,
joins source and language-span lineage through the five consumer-view
interfaces, and re-scores the frozen 677-item saved baseline without a model
call or gold leakage. Its real data output is narrower than those interfaces:
1,028 admitted Wikipedia rows populate each continued-pretraining view, while
correction, preference, and quality-filter views contain zero eligible rows.
The 739,503 silver records remain protected or unresolved.

The integration fixture is the observed `звучит` → `звучить` failure. It uses
VESUM, Russian morphology, `r2u`, ULIF, a heritage source, per-dictionary
`slovnyk.me` provenance, and Ukrainian corpus context. It remains synthetic:
fixture reviewers are not qualified-human evidence and all four fixture rows
remain training-ineligible. Separately, the older combined gate admitted 1,029
real Ukrainian Wikipedia records / 2,865,506 lexical words for the declared
continued-pretraining destination. The later usability decision approves the
retained human-authored corpus for downstream research and model learning after
required preprocessing; it does not authorize raw-source, dataset, adapter, or
weight publication.

The reference build is proof that teams can run the Foundry interfaces and
obtain reproducible evidence. It is not a released dataset, a trained model,
or a claim that the 677-item benchmark measures general Ukrainian fluency.

### Prepared-data product program

Successor epic #6321 turns the engine into data products that can be compared
with or consumed alongside Lapa, `lang-uk`, UA-GEC, and other open-weight
Ukrainian work through:

- a machine-readable disposition table and runnable consumer-corpus filtering
  recipe;
- a non-erasure benchmark/harness with protected legitimate variation; and
- stand-off annotations over revision-pinned locators for non-redistributable
  source families.

These direct-use forms preserve model-lane proposal provenance, per-family
datasheets, stable locators, and contamination-aware versioning with held-back
evaluation material. Provenance/capability metadata and recipes are supporting
infrastructure, not corpus-scale claims.

External feedback may prioritize later evidence adapters or acquisition, but
it is not required to prove deterministic receipts, source lineage, rights
decisions, or contamination controls. No external adoption is currently
claimed: an adapter, fixture, internal CI run, or failed project-run output is
not adoption evidence. Hramatka teacher feedback follows the same optional-
evidence rule.

## Downstream validation policy

The Foundry project does not run training experiments and has no active
project-owned evaluation run. The #6273 Gemma 4 attempt is invalid and cannot
be retried under its historical authorization. The project still ships frozen
artifacts that downstream teams can reproduce independently without a
closed-model judge.

A downstream result is useful evidence only when it answers a named question,
such as:

- Does a new open-weight generation remove a specific failure category?
- Does a tokenizer change improve Ukrainian fertility and downstream quality?
- Does a training-data slice improve held-out morphology without increasing
  overcorrection?
- Does a detailed Ukrainian prompt expose a capability that a generic prompt
  hides?

Open-weight consumers are the primary integration target because researchers
can inspect, reproduce, and adapt their work. Closed models remain useful to
consumers as comparison ceilings, candidate annotators, or prompt-sensitivity
probes. A closed-model score is not itself a durable community contribution.

Do not compare scores across different benchmarks as if they measured the same
thing. For example, the UNLP 2026 prompting result for Gemini 3.1 Pro is a
minimal-edit UA-GEC result under a specialized prompt. It does not establish
that the same model is best on broad Ukrainian proficiency, lexical
naturalness, or our narrower evaluation.

## Anti-distraction test

Before beginning work, answer all six questions:

1. Which documented Ukrainian failure or ecosystem gap does this address?
2. Who in the open-weight Ukrainian community can use the output?
3. Why do existing data, tools, or benchmarks not already solve it?
4. What artifact remains useful after the next base model release?
5. How will we measure improvement without contaminating the evaluation?
6. What is the cheapest observation that would make us stop before further
   spending?

If those answers are missing, the work is not ready.

## Evidence and uncertainty

Primary references used for this snapshot:

- [UNLP 2025 proceedings](https://aclanthology.org/volumes/2025.unlp-1/)
- [UNLP 2026 proceedings](https://aclanthology.org/volumes/2026.unlp-1/)
- [VESUM / `dict_uk`](https://github.com/brown-uk/dict_uk)
- [UA-GEC](https://github.com/grammarly/ua-gec)
- [Kobza and Modern-LiBERTa](https://aclanthology.org/2025.unlp-1.14/)
- [Lapa adaptation](https://aclanthology.org/2026.unlp-1.14/)
- [OmniGEC](https://aclanthology.org/2025.unlp-1.17/)
- [UNLP gold-standard proficiency benchmark](https://aclanthology.org/2026.unlp-1.12/)
- [Minimal-edit Ukrainian GEC prompting study](https://aclanthology.org/2026.unlp-1.13/)

Claims that Gemma 4 currently leads a particular Ukrainian leaderboard must be
tied to a frozen leaderboard snapshot and its exact task aggregate before
external publication. The operator's observation is strategically useful, but
the rank and benchmark definition must remain reproducible.

Gemma 4 may outperform a Gemma 3 adaptation on an aggregate leaderboard without
having solved clean Ukrainian. The public
[`lang-uk` methodology](https://huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard/blob/main/README.md)
aggregates translation, summarization, QA, reasoning/knowledge, mathematics,
and instruction following; it does not comprehensively measure surzhyk,
semantic calques, Russian morphology, government, or unwanted normalization of
heritage Ukrainian. Google's Gemma 4 card does not disclose a Ukrainian-
specific pretraining share. A top aggregate rank therefore cannot substitute
for the Foundry's targeted clean-Ukrainian diagnostics.

Lapa's public training assets predate the 2026-04-02 Gemma 4 launch. Its later
v0.1.3 release is described as an alignment and pipeline maintenance update;
no public Lapa Gemma-4 port or team-intent statement was located as of
2026-08-03. Gemma 4 does provide pretrained weights, but Lapa's Gemma-3 token
identifiers, embedding transfer, and training configurations are not a
drop-in Gemma 4 recipe. See the
[prepared-data product decision](../research/UNLP_PREPARED_DATA_PRODUCT_DECISION.md)
for the facts, bounded inference, and unknowns.
