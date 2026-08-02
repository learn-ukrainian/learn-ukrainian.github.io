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
> Foundry to ship the clean-Ukrainian preparation tool and training recipe
> before considering optional paid model validation.
> **Recorded:** 2026-07-30; Foundry direction and existing-asset baseline
> refreshed 2026-08-02
> **Applies to:** Ukrainian model evaluation, dataset work, training-data
> preparation, and UNLP ecosystem monitoring
> **Does not authorize:** model training, dataset publication, or mixing
> evaluation gold into training data

## North star

Our ultimate goal is to help AI produce measurably better, authentically
Ukrainian language.

We will pursue that goal through an open Ukrainian Data Foundry: reusable
infrastructure that Ukrainian and open-weight model teams can run on our
corpus, their corpora, or other licensed collections. The Foundry provides:

- trusted and well-documented data;
- morphology-aware coverage and diagnostics;
- narrow, credible evaluations of important failure modes;
- reproducible preparation and training recipes; and
- evidence that distinguishes standardization errors from legitimate
  historical, regional, dialectal, and register variation.

We are not trying to win by training and maintaining our own general-purpose
model weights. Base models can leapfrog a local fine-tune in one release.
Curated data, provenance, evaluation, and tooling transfer to every new model
generation.

This direction prioritizes transferable data, grammar, lexical naturalness,
and evidence over owning model weights. A bounded model treatment is permitted
only to test whether those artifacts help. The accepted boundary between public
evaluation gold, private product data, and training data remains intact.

## Solo-operator execution model

The Foundry must be executable by one operator. It cannot make paid or donated
review labour a prerequisite for useful source preparation, model-ready data,
or a bounded causal experiment.

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

Evidence-backed silver may be used in an explicitly silver, provenance-complete
experiment. It must never be reported as human gold, native-speaker acceptance,
reviewer reliability, or proof that every proposed correction is correct.

The Foundry can credibly promise reusable preparation, diagnostics, evidence,
and a controlled test of whether those artifacts help. It cannot promise in
advance that a treatment will make an LLM fluent. The cheapest falsifying check
always precedes a more expensive run, and a failed prerequisite or null result
is reported immediately rather than converted into more work.

## GitHub execution homes

- [#6164](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6164)
  owns Foundry Phase 2–4: real corpus admission, production contextual
  language-contact detection, evidence-backed silver with an optional
  qualified-human upgrade, real model-ready exports, a model-neutral clean-
  Ukrainian tool, reproducible training recipe, and release
  candidate. An open-weight treatment is an optional compatibility check, not
  a completion dependency. Closed
  [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
  owns the completed interfaces, profiler, exporters, recipes, and synthetic
  reference build on which this production program depends.
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
old combined gate, not corpus authenticity or local training fitness. It keeps
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
authored sources for local research and continued model learning. Raw-source
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

### Immediate work

1. Replace the combined admission disposition with capability-specific states:
   local research/model learning, raw-source redistribution, dataset release,
   and model release. Apply the operator-approved local-training decision to
   the retained human-authored corpus while preserving later release gates
   (#6171).
2. Preserve and use the completed production detector's 739,564 contextual
   candidates across Russian quotation, modern interference, phonetic Russian,
   mixed, historical, protected, and uncertain routes (#6167). VESUM absence
   remains one signal rather than a verdict.
3. Produce real evidence-graded silver correction, retention, protection, and
   unresolved records without requiring reviewer labour (#6168). Preserve the
   existing blind human campaign as an optional gold-upgrade path and add an
   optional, privacy-safe Hramatka feedback intake.
4. Restore raw literary locators lost during ingestion, reconcile remaining
   textbook filename variations, and start the approved local source-text
   continued-pretraining view immediately. Add separately manifested silver
   correction, preference, and quality-filter views only when their evidence
   and destination gates pass (#6169). Never fill a view with benchmark or
   fixture data.
5. Package the production detector, evidence factory, model-view exporters,
   tokenizer diagnostics, and evaluation firewall as one corpus-portable
   clean-Ukrainian tool. It must cover the Foundry's calque, grammar, and
   morphology axes, incorporate Oleksiy's recorded ULIF synonym-source
   recommendation, and protect historical, regional, dialectal, and quoted
   material (#6171).
6. Ship a model-neutral, stranger-runnable training recipe with exact
   admission, mixture, tokenizer, split, objective, evaluation, cost, and stop
   controls. Reproduce the complete no-training path in a clean independent
   environment (#6171). The canonical recipe and cost model are documented in
   the [clean-Ukrainian runbook](../runbooks/ukrainian-data-foundry-clean-ukrainian-recipe.md).
7. Keep the preregistered Gemma 4 treatment (#6170) parked as optional,
   present-tense operator-gated compatibility validation. It is not a
   prerequisite for #6171, and neither model download nor accelerator spend is
   authorized. If it is ever activated, first replace planning estimates with
   an exact microbenchmark and report null, mixed, unsafe, or negative results
   as valid terminal outcomes.
8. Use frozen v0.1.1 and compatible licensed external human-authored
   evaluations for recipe validation and any optional future experiment. The
   reviewer-intensive v0.2
   acquisition may resume only if Hramatka or a future collaboration supplies
   suitable consented evidence without becoming a project staffing dependency.
   Public evaluation gold remains mechanically isolated from every training or
   tuning view.

The accountable orchestrator continues through the #6171 no-training release
candidate. A merged implementation PR is progress, not a stopping condition.
Work pauses only at a source-family admission decision or final publication
approval named on #6164. Paid training is outside the critical path and begins
only through a new present-tense model/revision/budget authorization. Choosing
to claim human gold pauses only that optional upgrade lane.

### Completed Foundry v1 reference build

The #6119–#6123 implementation chain now has an executable reference build. It
reproduces the complete 189,150-record / 50,298,925-word morphology profile,
joins source and language-span lineage through correction evidence and five
separate consumer views, and re-scores the frozen 677-item saved baseline
without a model call or gold leakage.

The integration fixture is the observed `звучит` → `звучить` failure. It uses
VESUM, Russian morphology, `r2u`, ULIF, a heritage source, per-dictionary
`slovnyk.me` provenance, and Ukrainian corpus context. It remains synthetic:
fixture reviewers are not qualified-human evidence and all four fixture rows
remain training-ineligible. Separately, the older combined gate admitted 1,029
real Ukrainian Wikipedia records / 2,865,506 lexical words for the declared
continued-pretraining destination. The later usability decision approves the
retained human-authored corpus for local research and model learning after
required preprocessing; it does not authorize raw-source, dataset, adapter, or
weight publication.

The reference build is proof that teams can run the Foundry interfaces and
obtain reproducible evidence. It is not a released dataset, a trained model,
or a claim that the 677-item benchmark measures general Ukrainian fluency.

### Later validation and collaboration

After a usable reference build exists, it may be validated with Lapa,
`lang-uk`, UA-GEC, and other open-weight Ukrainian teams through:

- data slices they can inspect and reproduce;
- diagnostics they can run on any new base model;
- failure-focused evaluation with protected legitimate variation; and
- evidence-backed annotation guidelines.

External feedback may prioritize later adapters, acquisition, or release work.
It is not a prerequisite for building the architecture, full-corpus profiler,
silver correction intake, separate exporters, recipes, experiment, or reference
validation. Hramatka teacher feedback follows the same optional-evidence rule.

## Model-running policy

Model baselines are experiments, not the mission.

Run a model only when the result answers a named question, such as:

- Does a new open-weight generation remove a specific failure category?
- Does a tokenizer change improve Ukrainian fertility and downstream quality?
- Does a training-data slice improve held-out morphology without increasing
  overcorrection?
- Does a detailed Ukrainian prompt expose a capability that a generic prompt
  hides?

Open-weight models are the primary integration target because researchers can
inspect, reproduce, adapt, and redistribute their work. Closed models remain
useful as comparison ceilings, candidate annotators, or prompt-sensitivity
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

Gemma 4 can outperform Gemma 3 adaptations on an aggregate leaderboard because
of stronger general reasoning, instruction following, architecture, and broad
multilingual transfer without having solved clean Ukrainian. The public
[`lang-uk` methodology](https://huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard/blob/main/README.md)
aggregates translation, summarization, QA, reasoning/knowledge, mathematics,
and instruction following; it does not comprehensively measure surzhyk,
semantic calques, Russian morphology, government, or unwanted normalization of
heritage Ukrainian. Google's Gemma 4 card does not disclose a Ukrainian-
specific pretraining share. A top aggregate rank therefore cannot substitute
for the Foundry's targeted clean-Ukrainian diagnostics.
