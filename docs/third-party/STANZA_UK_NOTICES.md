# Third-party notices: Ukrainian Stanza inference

## Stanza 1.13.0 code

- **Work:** Stanza, Stanford NLP Group.
- **Citation:** Qi, Zhang, Zhang, Bolton and Manning (2020),
  *Stanza: A Python Natural Language Processing Toolkit for Many Human Languages*,
  ACL System Demonstrations. [Paper](https://aclanthology.org/2020.acl-demos.14/).
- **Source:** [stanfordnlp/stanza](https://github.com/stanfordnlp/stanza).
- **License:** Apache License 2.0;
  [versioned license](https://github.com/stanfordnlp/stanza/blob/v1.13.0/LICENSE).

## Ukrainian-IU models and training data

- **Work:** Stanza Ukrainian-IU language models; UD Ukrainian-IU treebank,
  Institute for Ukrainian.
- **Treebank attribution:** Natalia Kotsyba, Bohdan Moskalevskyi and
  Mykhailo Romanenko, with the additional annotators acknowledged in the
  [treebank documentation](https://universaldependencies.org/treebanks/uk_iu/index.html).
- **Source repository:** [stanfordnlp/stanza-uk](https://huggingface.co/stanfordnlp/stanza-uk).
- **Exact model revision:**
  [`3d394b0c66e58c32f43f4a9460452a08dedbffcd`](https://huggingface.co/stanfordnlp/stanza-uk/tree/3d394b0c66e58c32f43f4a9460452a08dedbffcd),
  the upstream model release for Stanza 1.13.0.
- **Training-data terms retained for the Ukrainian-IU models:**
  [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/),
  as stated in the [treebank license](https://github.com/UniversalDependencies/UD_Ukrainian-IU/blob/master/LICENSE.txt).
  The Hugging Face model card additionally identifies Apache 2.0; that label
  does not remove the treebank attribution and non-commercial terms retained here.
- **Byte inventory:** `scripts/verification/stanza_uk_manifest.json` records
  each tokenizer, MWT, POS, lemma, dependency, pretrain and character model's
  path, length and SHA-256.

This repository does not distribute model weights or treebank data. The
installer downloads the exact upstream bytes without modifying them. Inference
runs locally and supplies structural hypotheses to deterministic VESUM checks;
it does not create authoritative grammatical evidence. No endorsement by
Stanford NLP or the treebank creators is implied. Retain attribution and
applicable licenses when reusing or redistributing upstream materials.
