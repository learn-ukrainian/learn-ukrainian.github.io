# Ukrainian minimal-edit correction benchmark

This package evaluates systems that make minimal corrections to Ukrainian
calques and grammar. It contains a deterministic 677-sentence evaluation set,
a source-only request format, saved baseline responses, an exact-edit scorer,
and cryptographic receipts for independent verification.

The package is intended for research and system evaluation. It is not a
leaderboard, a training corpus, a general measure of Ukrainian-language
quality, or an assessment of any person.

## Release status

Release `0.1.0` is the current immutable freeze. Release `0.1.1` is a
corrective packaging release in preparation: it preserves the dataset, task,
scorer, and `0.1.0` results while improving the public documentation,
provenance, and model-response workflow. See
[RELEASE_NOTES.md](RELEASE_NOTES.md) for the exact boundary.

## Start here

The six authoritative English documents are:

- [README.md](README.md): package map and quick start;
- [DATA_CARD.en.md](DATA_CARD.en.md): dataset, metrics, limitations, and
  baseline interpretation;
- [REPRODUCING.md](REPRODUCING.md): complete verification and evaluation
  commands;
- [contamination-policy.md](contamination-policy.md): freeze and prohibited
  reuse policy;
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md): source, license, and
  attribution evidence;
- [RELEASE_NOTES.md](RELEASE_NOTES.md): versioned changes and compatibility.

Files required to verify or score the benchmark are under:

- `data/projects/ua_eval_harness/`: frozen data, task contracts, saved
  responses, score reports, and release manifests;
- `scripts/projects/ua_eval_harness/`: extraction, validation, scoring, and
  smoke-test commands.

Most repository content is unrelated to this benchmark and can be ignored.
In particular, development notes, archived translations, website code,
curriculum material, and quality-gate documentation are not part of the
research package or its frozen release.

## Quick verification

Requirements are Git, `uv`, and CPython 3.12.8. Verification does not require a
model-provider account or credential.

```bash
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
uv venv --python 3.12.8
.venv/bin/python scripts/projects/ua_eval_harness/smoke_public_v0.py
```

The smoke test validates the release manifest and re-scores every saved
baseline response. The expected `0.1.0` result is:

```text
identity: 677 responses, edit F0.5=0.0000, headline calque R=0.0000, exact=0.0000
deterministic fixture rules: 677 responses, edit F0.5=0.0000, headline calque R=0.0000, exact=0.0000
gpt-5.6-terra saved run: 677 responses, edit F0.5=0.2439, headline calque R=0.1410, exact=0.1610
public v0 smoke passed: frozen scoring reproduced without provider credentials
```

For individual verification commands, upstream rebuild instructions, and the
model-response contract, see [REPRODUCING.md](REPRODUCING.md).

## Task contract

Each request contains only:

- a stable item ID;
- the original Ukrainian sentence;
- the SHA-256 digest of that sentence;
- the SHA-256 digest of the frozen instruction.

The model returns the complete corrected sentence without explanation. Gold
targets, annotator references, edit spans, and scores are never included in
generation requests. Responses are saved before scoring so that a run can be
re-evaluated without contacting its provider.

The instruction requests the smallest changes needed to correct calques and
grammar. It excludes unrelated spelling, punctuation, style, and fluency
changes unless a grammatical correction requires them.

## Dataset and split

The evaluation set is derived deterministically from
[UA-GEC 2.0](https://github.com/grammarly/ua-gec) at commit
[`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`](https://github.com/grammarly/ua-gec/tree/4757f72f192c4a41e4c8fb1d9690a948f87cf6d6).
It retains every sentence in the `gec-fluency/test` partition with at least
one `F/Calque` or `G/*` annotation.

| Measure | Count |
| --- | ---: |
| Included sentences | 677 |
| Excluded test sentences | 2,013 |
| Total test sentences accounted for | 2,690 |
| Acceptable annotator references | 918 |
| In-scope annotations | 1,608 |
| Test documents | 166 |
| Test authors | 76 |

The upstream training and test partitions have zero author overlap and zero
document overlap. A separate set of 52 training-derived examples is used only
by a diagnostic literal-rule baseline and never contributes to held-out
results.

## Metrics

Overall edit precision, recall, and F0.5 use exact source-token spans and exact
replacement text. When a sentence has several annotator references, the
scorer selects the reference that maximizes the prediction's F0.5 with a
deterministic tie-break. Exact corrected-sentence accuracy is also reported.

Calque-specific claims use headline calque recall. The source corpus contains
354 retained `F/Calque` annotations; 338 are admitted to headline scoring after
a separate evidence-backed disposition. Sixteen register, heritage, or
contextually unresolved annotations remain outside that headline metric.

Calque precision is not reported because model-produced edits do not carry
reliable error-type labels. Overall exact-edit precision still covers every
predicted edit. The [English data card](DATA_CARD.en.md) defines the metrics
and their limitations in detail.

## Saved `0.1.0` baselines

| Saved run | Edit P | Edit R | Edit F0.5 | Headline calque R | Exact sentence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Identity v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Train-fixture literal rules v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `gpt-5.6-terra` | 0.3110 | 0.1309 | 0.2439 | 0.1410 | 0.1610 |

These controls demonstrate the scorer and saved-response workflow. They do not
establish a general ranking of model quality. Live regeneration is not
expected to be byte-identical when a provider does not expose deterministic
decoding controls; the saved responses and scoring results are reproducible.

## Evaluate another system

Prepare a source-only packet:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py prepare \
  --output /tmp/ua-eval-requests.jsonl
```

Generate one response for each request, then import and score it. The
provider-neutral batch runner can call an arbitrary executable through a
shell-free argument or standard-input interface, retain resumable receipts,
and write import-ready metadata. See
[REPRODUCING.md](REPRODUCING.md#evaluate-another-model) for its configuration
contract and complete command.

```bash
.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py import \
  --requests /tmp/ua-eval-requests.jsonl \
  --model-output /tmp/model-output.jsonl \
  --metadata /tmp/model-metadata.json \
  --output /tmp/saved-responses.jsonl

.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py score \
  --responses /tmp/saved-responses.jsonl \
  --output /tmp/score-report.json
```

The importer fails on incomplete coverage, duplicate IDs, receipt drift,
tampered responses, or fields resembling hidden gold data. The response file
and metadata contract are documented in
[REPRODUCING.md](REPRODUCING.md#evaluate-another-model).

## Provenance, licensing, and reuse

UA-GEC-derived data is licensed under CC BY 4.0. Bounded evidence derived from
dict_uk/VESUM is licensed under CC BY-NC-SA 4.0. Repository software is
licensed under MIT; that software license does not replace the licenses
applying to data and evidence.

Read [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistribution or
commercial use. Read
[contamination-policy.md](contamination-policy.md) before evaluating a model
that may have trained on public benchmark material. Held-out content and
derived rules must not be used for training, fine-tuning, synthetic data,
preference data, learner exercises, or regression corpora.

## Citation

When reporting results, identify the repository, semantic release version,
saved-response metadata, and freeze-manifest digest. Cite UA-GEC and
dict_uk/VESUM as specified in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Report enough decoding and
provider metadata to distinguish the evaluated system without including
credentials or hidden benchmark fields.
