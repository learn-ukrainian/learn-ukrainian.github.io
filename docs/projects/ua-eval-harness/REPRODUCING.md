# Reproducing public v0

## Quick check without provider credentials

Requirements: Git, `uv`, and CPython 3.12.8. No provider account, API key,
private repository, product state, or live model call is required.

```bash
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
uv venv --python 3.12.8
.venv/bin/python scripts/projects/ua_eval_harness/smoke_public_v0.py
```

The smoke test first validates the release freeze and the SHA-256 hashes of all
21 frozen artifacts. It then re-scores the identity baseline, the deterministic
fixture-rule baseline, and the saved `gpt-5.6-terra` run. Each newly generated
JSON report must exactly match its committed report.

Expected output:

```text
identity: 677 responses, edit F0.5=0.0000, headline calque R=0.0000, exact=0.0000
deterministic fixture rules: 677 responses, edit F0.5=0.0000, headline calque R=0.0000, exact=0.0000
gpt-5.6-terra saved run: 677 responses, edit F0.5=0.2439, headline calque R=0.1410, exact=0.1610
public v0 smoke passed: frozen scoring reproduced without provider credentials
```

The [English data card](DATA_CARD.en.md) defines overall edit F0.5, headline
calque recall, and why calque precision is not reported. This guide focuses on
the commands and technical verification of those results.

## Individual fail-closed checks

Run the checks separately when diagnosing a failure:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/verify_release_freeze.py

.venv/bin/python scripts/projects/ua_eval_harness/build_scoring_dispositions.py \
  --verify-existing

.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py verify \
  --responses data/projects/ua_eval_harness/baselines/v1/gpt-5.6-terra.responses.jsonl

.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py score \
  --responses data/projects/ua_eval_harness/baselines/v1/gpt-5.6-terra.responses.jsonl \
  --output /tmp/ua-eval-terra-report.json
```

The last command writes a temporary report. It does not modify any frozen
artifact.

## Rebuild the dataset from the pinned upstream source

This check also requires a UA-GEC checkout at the pinned commit:

```bash
git clone https://github.com/grammarly/ua-gec.git /tmp/ua-gec
git -C /tmp/ua-gec checkout 4757f72f192c4a41e4c8fb1d9690a948f87cf6d6

.venv/bin/python scripts/projects/ua_eval_harness/build_heldout_manifest.py \
  --ua-gec-root /tmp/ua-gec \
  --check
```

The extractor verifies the upstream file hashes, license and version evidence,
author and document separation between the training and test partitions, all
2,690 sentence dispositions, and the final payload hash.

## Rebuild the scoring dispositions

To reproduce the heritage and style evidence, download the pinned
dict_uk/VESUM v6.8.0 release asset with SHA-256
`e33803783ac138e6f3af2cf0e9428ba146c0ecfda7f5c41fe83ae00c7af24be9`, then
run:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/build_scoring_dispositions.py \
  --asset /path/to/dict_corp_vis.txt.bz2 \
  --check
```

The asset and the derived evidence are licensed under CC BY-NC-SA 4.0. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the exact download URL,
pinned revision, license, and evidence receipts.

VESUM attestations and style markers identify candidates; they do not decide
contextual calque status automatically. Broader contextual activation is
outside this release. Public v0 excludes unresolved records from headline
scoring.

## Evaluate another model

Create a source-only request packet:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py prepare \
  --output /tmp/ua-eval-requests.jsonl
```

Generate responses outside the scorer using only the request fields. Then
import them with versioned model, provider, and decoding metadata:

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

The importer rejects incomplete coverage, duplicate IDs, drift in source or
prompt hashes, tampered responses, and fields that resemble hidden gold data.
Live generation is optional and remains outside the credential-free
reproduction path.
