# Ukrainian Corpus Training-Usability Decision

> **Decision:** CONTINUE
> **Date:** 2026-08-02
> **Owner:** [#6171](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6171)
> **Machine receipt:**
> [`corpus_training_usability_decision_v1.json`](../../data/projects/open_model_data/inventory/corpus_training_usability_decision_v1.json)

## Plain answer

The corpus is usable for the project's goal. An LLM can learn from these
textbooks, literature, articles, and Wikipedia after the text is divided into
the correct learning strata and damaged or non-target spans are kept out of
modern-Ukrainian loss.

The corpus is sufficient to:

1. build and validate the corpus-portable clean-Ukrainian tool;
2. prepare a high-value Ukrainian adaptation mixture for an existing open
   model; and
3. give downstream teams deterministic model-ready views, evaluation controls,
   cost arithmetic, and a reproducible training recipe.

It is not large enough to train a competitive general foundation model from
scratch. It also cannot automatically turn every detector candidate into a
corrected gold example. Neither limitation invalidates the project.

## What was wrong with the earlier conclusion

The 2026-07-31 recovery audit correctly counted the corpus but treated missing
database fields and a fail-closed publication-oriented contract as evidence
that most sources were unresolved. That interpretation was too broad.

The raw Google Drive files establish materially better lineage:

- all **137,723 / 137,723 literary rows** have a source locator;
- all 137,723 have work, author, year, genre, and language-period metadata;
- the 229 literary files divide into 170 Litopys/Izbornyk files, 55 UKRLIB
  files, two Ukrainian Wikisource files, and two retained Hrushevsky volumes;
- the database retains `source_url` on only 11,064 rows because the ingestion
  path dropped locators from most records; this is a database-lineage defect,
  not absence of raw provenance; and
- the textbook acquisition is represented by retained PDFs, extracted chunks,
  a selection ledger, a downloader, and a page-URL map for the public textbook
  download site.

Therefore, “zero records admitted by the old gate” meant that the gate had not
issued its most permissive combined training-and-redistribution disposition.
It did not mean “the corpus is fake,” “the corpus has no sources,” or “an LLM
cannot learn from it.”

## Evidence measured from the retained assets

| Evidence | Result | Meaning |
| --- | ---: | --- |
| Public/external human-authored corpus | 189,150 records / 50,298,925 lexical words | Useful-scale curated adaptation and diagnostic corpus |
| Modern stratum | 42,261,796 lexical words | Main starting pool for modern-Ukrainian learning |
| Middle Ukrainian | 5,435,144 lexical words | Protected historical/heritage lane, not unmarked modern loss |
| Old East Slavic | 2,601,985 lexical words | Protected historical lane |
| VESUM-attested tokens | 41,006,903 | Strong morphology-supported base |
| VESUM-unknown tokens | 9,292,022 | Investigation pool, not “nine million errors” |
| Contextual detector candidates | 739,564 | Routing evidence for quotes, interference, history, OCR, names, and uncertainty |
| Literary raw lineage | 229 files / 137,723 rows / 100% with locator | Source families and row provenance are recoverable |
| Textbook raw assets | 158 chunk files / 48,996 chunks / 170 PDFs | Broad grades 1–11 educational Ukrainian |
| Exact chunk-to-PDF stem matches | 141 | Most raw chunk families directly match a retained PDF stem |
| Textbook page-URL mappings | 93; 89 exact current chunk-stem matches | Acquisition pages are substantially retained; remaining names need reconciliation |
| Textbook extraction marked clean | 48,220 / 48,996 rows | Most extraction passes the existing mechanical gate |
| Textbook OCR/encoding warning | 1,214 rows in 48 files contain mojibake markers | Existing `is_clean` is insufficient; damaged spans must be filtered or repaired |

The database's 49,193-row public-textbook count includes 197 public lexicon
rows in addition to the 48,996 raw textbook chunks. The two counts therefore
describe different retained units rather than a lost-text discrepancy.

## Decision by intended use

| Intended use | Decision | Conditions |
| --- | --- | --- |
| Run the clean-Ukrainian detector and evidence tool | **Use now** | Preserve uncertainty; VESUM absence alone is never an error verdict |
| Continue training an existing open model downstream | **Use after preprocessing** | Deduplicate, stratify, filter/mask damage, preserve lineage, and isolate evaluation |
| Prepare a reproducible training recipe for another Ukrainian team | **Use now** | Emit manifests and receipts without embedding private paths or republishing source files |
| Train a general foundation model from scratch | **Do not use as the only corpus** | The roughly 139-million-token planning scale is far below foundation-model scale |
| Create automatic correction/preference gold | **Not from raw detector output** | Use evidence-graded silver; call it gold only after adequate validation |
| Publish raw books or textbook PDFs | **Separate decision** | Not required for downstream learning, derived receipts, tool publication, or the recipe |
| Publish weights or an adapter | **Separate decision** | Evaluate capability, regressions, memorization, obligations, and release terms first |

The operator has approved the retained human-authored source corpus for
downstream research and model-learning work toward the project goal. This
decision does
not claim a blanket right to rehost the raw source books, publish a dataset, or
release weights. Those are separate capabilities and must not be used to block
an otherwise approved downstream model-learning view.

## Required learning mixture

The corpus must not be flattened into one undifferentiated text file.

1. **Modern learning lane:** clean educational, reference, article, and modern
   literary spans suitable for contemporary Ukrainian loss.
2. **Faithful literature lane:** source-faithful modern literature, including
   marked quotations and authorial usage, with a separate mixture weight.
3. **Historical and heritage lane:** Middle Ukrainian, Old East Slavic,
   archaisms, dialectal forms, and historically authentic contact forms.
4. **Protected non-target lane:** quoted Russian, other languages, titles,
   names, citations, and metalinguistic examples; retain for context but mask
   or exclude from modern-Ukrainian target loss.
5. **Technical-repair lane:** OCR and encoding damage; repair with evidence or
   exclude from language-model loss.
6. **Evaluation firewall:** frozen benchmark records and their derivatives
   never enter a training view.

Synthetic A1–B2 modules, FOLK/BIO experiments, and KubeDojo translations stay
separate. They remain useful for error discovery and quality-filter research,
but they are not silently promoted into the human-authored source corpus.

## What this means for the ultimate goal

The goal is not to preserve one Gemma checkpoint. It is to ship the means by
which an open-model team can teach a current or future base model to prefer
clean, grammatical, context-appropriate Ukrainian without erasing legitimate
historical, regional, literary, or quoted language.

The retained corpus is valuable precisely because it combines grades 1–11
textbooks, modern literature, historical material, broad school subjects,
articles, Wikipedia, dictionaries, VESUM morphology, and observed
Russian-contact failures. Larger Ukrainian corpora already provide scale. Our
contribution is the source-aware treatment, language-contact routing, protected
variation, model-ready views, evaluation firewall, and reproducible recipe.

This direction also survives model turnover: domain-adaptive continued
pretraining has repeatedly improved existing pretrained models, including in
multilingual and resource-constrained settings. See
[Gururangan et al. (2020)](https://aclanthology.org/2020.acl-main.740/),
[Liu et al. (2021)](https://aclanthology.org/2021.findings-emnlp.290/), and
[Midu et al. (2025)](https://aclanthology.org/2025.latechclfl-1.22/).

## Execution order from this decision

1. Correct the current admission/export contract so downstream model-learning
   eligibility, raw-source redistribution, dataset publication, and weight
   publication are independent capabilities.
2. Restore raw literary locators into generated source records and reconcile
   the remaining textbook filename variations against retained PDFs and URLs.
3. Produce modern-learning and faithful-source views with OCR, historical, and
   quoted-language masks; keep source text immutable.
4. Measure exact tokenizer counts and run the complete no-accelerator recipe.
5. Hand the validated artifacts, cost method, and limitations to downstream
   teams that have their own compute; the Foundry project stops before model
   download, accelerator rental, or optimizer execution.

No new broad corpus acquisition is required before steps 1–4. No paid training
is required to finish the tool and recipe.

## Reproduction

The machine receipt is rebuilt from metadata and aggregate receipts; it emits
no source text and no personal filesystem path:

```bash
.venv/bin/python -m scripts.projects.open_model_data.audit_corpus_training_usability \
  --gdrive-root "$LU_GDRIVE_DATA" \
  --output data/projects/open_model_data/inventory/corpus_training_usability_decision_v1.json
```

The result must be `project_verdict: continue`. Any future change to the
verdict requires a new versioned decision receipt rather than silently
rewriting this evidence.
