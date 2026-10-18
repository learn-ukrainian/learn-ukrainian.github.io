# Russification evidence subset

This separate, opt-in subset supports Russification and russism detection and
classification. It is not for language-model pretraining. Never concatenate its
JSONL into the general corpus or treat the imposed side as a Ukrainian norm.

## Records and source roles

`russification-contrast.v1` records carry `opt_in: true`,
`for_pretraining: false` and one `soviet_colonization_context` pair. Each pair has
a stable `pair_id`, a card `sense_id`, a source-adjudicated `distortion_type`, an
`imposed` quotation and a `norm` correction. Both sides have a `citation` with
`source_id`, `snapshot_id`, `locator` and `attribution`. Quotation boundaries are
the separate `text` fields. The imposed side retains `sovietization_risk` and
`sovietization_keywords`; the norm names its modern `assertion_id`.

СУМ-11 supplies contrastive historical evidence only. Modern citations come from
СУМ-20, ULIF or VTS. A complete pair does not establish that the linguistic
judgment is correct. Production inputs must come from certified word cards and
the two-seat, source-bound adjudication required by
[`WORD_CARDS_DATA_PLAN.md`](https://github.com/learn-ukrainian/learn-ukrainian.github.io/blob/main/docs/projects/open-model-data/WORD_CARDS_DATA_PLAN.md)
and [card schema §14](https://github.com/learn-ukrainian/learn-ukrainian.github.io/blob/main/docs/atlas/word-cards/schema.md#14-russification-exposed-сум-11).
The builder neither invents Ukrainian nor certifies source judgments.

## Building and quarantine

Call `scripts.open_dataset.russification.write_contrastive_subset` with
`opt_in=True` and a private output directory outside every checkout. The
existing RB-1 output guard enforces containment. This writes the JSONL and this
card together. There is no implicit inclusion in the default dataset.

Before release, call `validate_default_split(default_records,
sum11_texts=frozen_quotation_inventory)` with an independently frozen complete
inventory for the projection being audited. The gate rejects nested СУМ-11
provenance, contrast fields and matching quotations, including case and whitespace
changes. Without the inventory it checks provenance only. It cannot establish
the provenance of unlabelled text or detect arbitrary paraphrases. Report the
inventory digest, input denominator and exact reviewed projection with the audit.
The ordinary release packager rejects quarantined provenance and refuses
contrast JSONL even if someone places it beside the default shards. Uploads
require `--sum11-inventory`, a JSON array containing the independently frozen
quotations. A dry run without that option checks provenance only.

Structural tests use synthetic English placeholders. They prove the software
boundary, not the correctness or coverage of Ukrainian pairs. No production
coverage, held-out evaluation, certification or release is claimed by this card.
Those remain the open-model-data driver's obligations under #8989, #8982,
#8988 and #10515. Public release requires current operator authorization.

## Attribution and quotation basis

The [permissions register](https://github.com/learn-ukrainian/learn-ukrainian.github.io/blob/main/docs/sources/permissions-register.yaml) is the
source-use record. Its `sum11` entry permits only red-flagged Russification
evidence paired with the cited modern norm. It records an in-copyright work,
not an open-text licence, and references `law_art22_quotation` for attributed,
bounded quotation and `law_art31_term` for the recorded term basis. The register
requires checking aggregator passages against the official edition before
display. Preserve each modern source's register entry and licence notices too;
this subset grants no new licence over quoted dictionary text.

The registered citation is *Словник української мови: в 11 томах. АН УРСР,
Інститут мовознавства ім. О. О. Потебні. Київ: Наукова думка, 1970–1980*, with
the quoted headword or passage locator. Source corrections and takedown requests
use the project's GitHub issues route recorded in the register.
