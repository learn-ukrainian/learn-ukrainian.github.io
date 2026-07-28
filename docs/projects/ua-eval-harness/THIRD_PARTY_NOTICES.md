# Third-party notices

## UA-GEC 2.0

The public evaluation data and source-derived saved-response artifacts include
material from:

- **Work:** UA-GEC, Ukrainian Grammatical Error Corpus, version 2.0
- **Creators/citation:** Syvokon, Nahorna, Kuchmiichuk, and Osidach.
  *UA-GEC*. UNLP 2023.
- **Source repository:**
  [grammarly/ua-gec](https://github.com/grammarly/ua-gec)
- **Exact source revision:**
  [`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`](https://github.com/grammarly/ua-gec/tree/4757f72f192c4a41e4c8fb1d9690a948f87cf6d6)
- **License:** [Creative Commons Attribution 4.0 International
  (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Pinned license evidence:**
  [upstream `LICENSE`](https://github.com/grammarly/ua-gec/blob/4757f72f192c4a41e4c8fb1d9690a948f87cf6d6/LICENSE)

Changes made for this evaluation:

- selected `gec-fluency/test` sentences deterministically when at least one
  annotation has tag `F/Calque` or prefix `G/`;
- created one target per annotator by applying only those in-scope edits while
  leaving all other upstream edits unchanged;
- preserved upstream document/author metadata, annotator indices, original
  tags, source locators, and cryptographic receipts;
- retained hash-only exclusion receipts for test sentences without an
  in-scope edit;
- generated source-only request packets, model responses, and aggregate score
  reports for the frozen task.

No endorsement by the UA-GEC creators or Grammarly is implied. Reusers of the
UA-GEC-derived data must retain this attribution, link the CC BY 4.0 license,
and indicate their own changes.

## dict_uk / VESUM v6.8.0

The benchmark-disposition evidence receipts were derived from:

- **Work:** `dict_uk` / VESUM morphological dictionary, release `v6.8.0`
- **Source repository:**
  [brown-uk/dict_uk](https://github.com/brown-uk/dict_uk)
- **Exact source revision:**
  [`bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824`](https://github.com/brown-uk/dict_uk/tree/bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824)
- **Pinned release asset:**
  [`dict_corp_vis.txt.bz2`](https://github.com/brown-uk/dict_uk/releases/download/v6.8.0/dict_corp_vis.txt.bz2),
  SHA-256
  `e33803783ac138e6f3af2cf0e9428ba146c0ecfda7f5c41fe83ae00c7af24be9`
- **License:** [Creative Commons Attribution-NonCommercial-ShareAlike 4.0
  International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

The release does not redistribute the dictionary asset. It preserves bounded
derived receipts for exact surface-form attestation, analysis counts,
style-marker evidence, and receipt hashes. Those signals identify candidates;
they do not automatically adjudicate contextual calque status.

## Repository software

The extractor, scorer, validators, runner, and smoke-test software are
licensed under the repository's [MIT license](../../../LICENSE). The
UA-GEC-derived data remains under CC BY 4.0, and VESUM-derived evidence remains
under CC BY-NC-SA 4.0. The MIT license does not replace or narrow those terms.
