# Data card: Ukrainian calque and grammar evaluation v0

## At a glance

| Field | Value |
| --- | --- |
| Release | `ua-gec-calque-grammar-public-v0` |
| Semantic version | `0.1.0` |
| Task | Minimal-edit correction of Ukrainian calques and grammar |
| Evaluation items | 677 held-out UA-GEC sentences |
| Acceptable references | 918 annotator references |
| In-scope annotations | 1,608 `F/Calque` or `G/*` annotations |
| Source | UA-GEC 2.0, `gec-fluency/test` |

The `v0` suffix is part of the release name; `0.1.0` is the semantic version
of this frozen release.

This release is for researchers and practitioners evaluating systems that make
minimal corrections to Ukrainian sentences. It provides a public evaluation
set, a source-only model interface, saved baseline responses, an exact-edit
scorer, and reproducibility receipts.

It is not a general measure of Ukrainian-language quality, a leaderboard, a
training corpus, or an evaluation of a person's language competence.

## What the model receives and returns

Each request contains only:

- a stable item ID;
- the original Ukrainian sentence;
- the SHA-256 digest of that sentence;
- the SHA-256 digest of the frozen task instruction.

The instruction asks the model to return the complete sentence with only the
smallest changes needed to correct calques and grammar. It tells the model not
to rewrite otherwise correct wording and not to correct spelling, punctuation,
style, or fluency unless a grammatical correction requires it. The model
returns the corrected sentence without an explanation.

Gold targets, annotator references, edit spans, and scores are never included
in the generation input. Responses are saved before they are scored, so a
saved run can be evaluated again without contacting the model provider.

## What the metrics mean

The release reports two deliberately different views of performance.

### Overall exact-edit metrics

Overall edit precision, recall, and F0.5 cover all selected UA-GEC
standardization and grammar labels. A predicted edit is a true positive only
when both its source-token span and its replacement text exactly match a gold
edit.

There may be more than one acceptable annotator reference for a sentence. The
scorer selects the reference that gives the prediction its best F0.5, using a
deterministic tie-break. This policy recognizes valid alternative corrections,
but it can produce a higher score than strict single-reference evaluation.
Exact corrected-sentence accuracy is reported as a companion metric.

### Headline calque recall

Claims specifically about calque correction use a separate, heritage-aware
headline recall. The original UA-GEC `F/Calque` label is preserved for
provenance, but the label alone does not make an edit eligible for this
headline result. Eligibility is determined by the separate scoring
disposition described below.

The denominator depends on two stages:

1. UA-GEC contains 354 `F/Calque` annotations in the retained references.
2. The release admits 338 of them to headline calque scoring.
3. A scored run uses the admitted annotations found in the reference selected
   for each sentence, so its denominator can be smaller than 338.
4. For the saved `gpt-5.6-terra` run, the selected references contain 234
   admitted annotations; 33 exact matches give recall
   `33 / 234 = 0.1410`.

Calque precision is not reported. Model-produced edits do not carry error-type
labels, so an edit that appears only in the hypothesis cannot be assigned
reliably to the calque category. Reporting those false positives as calque
errors would create a misleading precision value. Overall exact-edit precision
remains available and includes every predicted edit.

Reports also provide per-tag recall and support, the rate of unchanged and
over-edited sentences, Wilson intervals for per-tag recall, and deterministic
sentence-bootstrap intervals for overall edit F0.5 and exact-sentence
accuracy.

## Source and construction

The evaluation is a deterministic derivative of
[UA-GEC 2.0](https://github.com/grammarly/ua-gec) at commit
[`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`](https://github.com/grammarly/ua-gec/tree/4757f72f192c4a41e4c8fb1d9690a948f87cf6d6).
It uses the `gec-fluency/test` partition.

The selection rule has no arbitrary item quota: it retains every tokenized
test sentence with at least one `F/Calque` annotation or an annotation whose
tag begins with `G/`. For each annotator reference, only these in-scope edits
are applied; other UA-GEC edits remain unchanged.

The extraction manifest accounts for every sentence in the upstream test
partition:

| Disposition | Sentences |
| --- | ---: |
| Included | 677 |
| Excluded because there is no in-scope edit | 2,013 |
| Total | 2,690 |

The upstream test partition contains 166 documents by 76 authors. The upstream
training partitions contain 752 authors. The frozen split receipt confirms
that neither authors nor documents overlap between train and test.

Of the 677 included sentences, UA-GEC marks 505 as native and 172 as
non-native. The source-language metadata is 502 `null`, 114 `en`, 58 `ru`,
and 3 `pl`. None of the included records has upstream
`is_sensitive=true`.

An older set of 52 train-derived examples remains available only as
development fixtures. It is excluded from held-out results and is used only
by the deliberately weak deterministic literal-rule baseline.

## Annotation coverage

| UA-GEC tag | Annotations |
| --- | ---: |
| `F/Calque` | 354 |
| `G/Case` | 391 |
| `G/UngrammaticalStructure` | 270 |
| `G/Prep` | 143 |
| `G/Number` | 85 |
| `G/Tense` | 77 |
| `G/Gender` | 76 |
| Other `G/*` tags | 212 |
| **Total** | **1,608** |

In per-tag reports, `support` counts all eligible annotations across the
retained references. `selected_reference_support` is the denominator produced
by the scorer's reference choices for one saved run and may therefore differ
between runs.

## Heritage, register, regional, and dialect-sensitive cases

UA-GEC was annotated to normalize text toward standard Ukrainian. The release
therefore preserves all 354 upstream `F/Calque` annotations as source
provenance without treating every annotation as an independent finding that a
form is a calque.

A separate disposition covers every `F/Calque` annotation:

| Scoring disposition | Annotations |
| --- | ---: |
| Admitted to headline calque recall | 338 |
| Excluded as register or conversational standardization | 3 |
| Excluded because of a heritage conflict | 2 |
| Excluded as contested or contextually unresolved | 11 |
| Excluded as regional standardization | 0 |
| **Total** | **354** |

The disposition uses bounded evidence derived from the pinned dict_uk/VESUM
v6.8.0 release. An exact surface-form probe found 49 unique spans with style
markers: 34 `bad`, 10 `slang`, 3 `arch`, and 2 `rare`. These markers and
morphological attestations identify cases for review; they do not determine
the correct interpretation in context.

The pinned dictionary source has no dedicated `dial` tag. Its documentation
allows `arch` to cover obsolete, archaic, and sometimes dialectal use, and the
parser can also preserve comment-level dialect evidence. The release therefore
does not claim that the dataset has no dialect conflicts. It makes no automatic
regional exclusion, and any unresolved register, heritage, regional, or
dialect-sensitive case stays outside headline calque scoring. Broader
contextual activation of dictionary markers remains tracked in
[issue #5092](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5092).

This conservative boundary affects only the headline calque claim. Overall
exact-edit metrics continue to report performance over all selected UA-GEC
standardization and grammar labels.

## Baseline results

| Saved run | Overall edit P | Overall edit R | Overall edit F0.5 | Headline calque R | Exact sentence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Identity v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Train-fixture literal rules v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `gpt-5.6-terra` | 0.3110 | 0.1309 | 0.2439 | 0.1410 | 0.1610 |

For the `gpt-5.6-terra` run, the 95% sentence-bootstrap interval is
0.2073–0.2780 for overall edit F0.5 and 0.1344–0.1891 for exact-sentence
accuracy. These intervals describe uncertainty for this dataset and run; they
do not turn the release into a general comparison of model quality.

All 677 responses from each saved run are retained. Re-scoring those responses
is deterministic. Live regeneration of the `gpt-5.6-terra` responses is not
byte-reproducible because the provider did not expose temperature, top-p, or a
seed. The saved run records its model, provider, prompt, decoding metadata,
runner, responses, and report through versioned metadata and cryptographic
receipts.

The zero-scoring identity and literal-rule baselines are diagnostic controls,
not evidence that the task is impossible or that one model is generally
better than another. The release is not a maintained leaderboard.

## Appropriate uses

The release is suitable for:

- reproducible evaluation of systems that make minimal Ukrainian calque and
  grammar corrections;
- analysis of exact-edit precision, recall, F0.5, over-editing, and per-tag
  recall;
- offline scoring or re-scoring of saved model responses;
- controlled comparison of systems under the same frozen task contract.

It is not suitable for:

- measuring general Ukrainian-language quality, factual accuracy, style,
  cultural appropriateness, or human language competence;
- drawing conclusions about individual authors or source-language groups;
- grading learners, hiring, or other high-stakes decisions;
- training, fine-tuning, synthetic corruption, preference data, or DPO;
- serving as content for Daily Practice, Hramatka, teacher-feedback
  inventories, Atlas, private regression sets, or private canaries.

## Limitations

- The gold references inherit UA-GEC annotation decisions and possible noise.
  UA-GEC's `F/Calque` tag is a standardization label; the release's scoring
  disposition is a separate decision about headline calque evaluation.
- Dictionary attestation and style markers do not resolve meaning or
  acceptability in context. The release excludes unresolved cases from its
  headline claim rather than assuming that a marker is decisive.
- The dataset covers only retained `F/Calque` and `G/*` edits in one pinned
  UA-GEC test partition. It cannot establish performance on other correction
  types, domains, or Ukrainian varieties.
- Selecting the best annotator reference can raise scores relative to
  single-reference evaluation.
- Exact token-span matching is intentionally strict. Ambiguous token
  alignments and valid corrections not represented in the references may be
  scored as errors.
- The source is tokenized M2 text and retains upstream spacing. The evaluation
  does not measure the naturalness of detokenized output.
- Tags with low support have wide uncertainty intervals.
- Public gold enables independent verification but also creates contamination
  risk for future model evaluations.

These limitations mean that the release can establish performance on this
specific frozen minimal-edit task. It cannot establish overall Ukrainian
proficiency, cultural or dialectal correctness, factual reliability, or
suitability for deployment.

## Licensing and provenance

UA-GEC and the text derived from it are distributed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reusers must retain
attribution, link the license, and describe their changes. The bounded
dict_uk/VESUM evidence is distributed under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
The evaluator and packaging scripts use the repository's MIT license.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the complete
citations, pinned revisions, license evidence, and modification notices. The
MIT license for repository software does not replace the licenses that apply
to UA-GEC-derived data or VESUM-derived evidence.

## Privacy, safety, and contamination

The release preserves upstream pseudonymous document and author IDs. It does
not support re-identification. The included subset has no records marked
sensitive by UA-GEC, and no provider credentials are stored. Aggregate reports
exclude item text, IDs, edits, raw responses, and content hashes.

Public held-out source text, gold targets, IDs, hashes, and derived rules must
not enter training or fine-tuning data, synthetic-data or preference-data
pipelines, Daily Practice, Hramatka, teacher-feedback inventories, Atlas,
private product data, regression sets, or canaries. A discovered leak is a
contamination incident: the affected release requires a recorded incident, a
new version, a new extraction, new baselines, and a new freeze.

The complete restrictions and disclosures are in the
[contamination policy](contamination-policy.md).

## Reproduction and evaluating another model

[REPRODUCING.md](REPRODUCING.md) explains how to verify the frozen release,
reproduce the saved baseline scores without provider credentials, rebuild the
evaluation data from the pinned upstream sources, and score another model's
saved responses.

Release `0.1.0` is immutable. A documentation-only correction may be released
as a patch without changing the dataset, task, scorer, or baseline results;
any frozen-byte change requires a new semantic version and a separate freeze.
