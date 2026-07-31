# Ukrainian Open-Model Data Infrastructure: North Star

> **Status:** Operator-confirmed strategic direction; evidence snapshot
> **Approval receipt:** Operator issued **GO REALIGN** for the stream and issue
> realignment on 2026-07-30; recorded in
> [PR #6060](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/6060).
> **Recorded:** 2026-07-30; existing-asset baseline refreshed 2026-07-31
> **Applies to:** Ukrainian model evaluation, dataset work, training-data
> preparation, and UNLP ecosystem monitoring
> **Does not authorize:** model training, dataset publication, or mixing
> evaluation gold into training data

## North star

Our ultimate goal is to help AI produce measurably better, authentically
Ukrainian language.

We will pursue that goal by giving open-weight model teams reusable Ukrainian
language infrastructure:

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

This direction implements the existing accepted decision to prioritize grammar
and lexical naturalness while parking model fine-tuning. It also preserves the
accepted boundary between public evaluation gold, private product data, and
future training data.

## GitHub execution homes

- [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
  owns audited open-model data infrastructure, provenance contracts,
  morphology/tokenizer diagnostics, and consumer-specific exporters.
- [#6057](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6057)
  owns the separately frozen public benchmark v0.2 design and release.
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
public/external human-authored text view contains 189,150 database rows and
50,298,925 lexical words; the separate private-reference view contains 5,786
rows and 681,925 words. Google Drive retains 229 literary JSONL source files,
which reconcile by filename stem to all 229 literary database source groups.
The repository also retains 12,347 tracked archive files and six historical
FOLK package versions with Git recovery locators.

This is an inventory, not an admission decision. The baseline records zero
source-record admissions and zero redistribution-cleared assets. It keeps
human-authored, machine-generated direct Ukrainian, machine-translated,
private-reference, evaluation-only, and unknown-origin material mechanically
separate. The invalid 5,000-record export may locate an underlying work but
cannot establish source, edition, rights, acquisition lineage, or contamination
status.

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

1. Maintain a source-linked UNLP asset and gap map. Record datasets, licenses,
   task coverage, model baselines, and unresolved gaps without claiming that
   our work is unique before comparison.
2. After one real open-weight consumer documents a bounded need, reconstruct a
   one-source-family micro-pilot from an original catalogue, edition, website,
   archive, or retained acquisition artifact already represented in the corpus.
   The 5,000-record export may be used only to locate the underlying work.
3. Analyze errors and model disagreements in the 677-item evaluation. Use them
   to define the next annotation categories rather than merely adding model
   rows to a table.
4. Design the next evaluation slice with no-change controls, heritage and
   dialect hard positives, multiple acceptable references, and category
   coverage targets.
5. Specify one canonical source-record schema and separate exporters for
   training, preference, filtering, and evaluation views.
6. Build morphology and tokenizer coverage reports that open-weight teams can
   run before and after adaptation.

### Collaboration target

After the audits, offer narrow assets to Lapa, `lang-uk`, UA-GEC, and other
open-weight Ukrainian teams:

- data slices they can inspect and reproduce;
- diagnostics they can run on any new base model;
- failure-focused evaluation with protected legitimate variation; and
- evidence-backed annotation guidelines.

The offer should start with their unmet need, not with our desire to publish a
dataset.

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

Before beginning work, answer all five questions:

1. Which documented Ukrainian failure or ecosystem gap does this address?
2. Who in the open-weight Ukrainian community can use the output?
3. Why do existing data, tools, or benchmarks not already solve it?
4. What artifact remains useful after the next base model release?
5. How will we measure improvement without contaminating the evaluation?

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
