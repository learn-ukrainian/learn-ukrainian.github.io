# Відтворення public v0

## Швидка перевірка без credentials

Потрібні Git, `uv` і CPython 3.12.8. Провайдерний обліковий запис не потрібен.

```bash
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
uv venv --python 3.12.8
.venv/bin/python scripts/projects/ua_eval_harness/smoke_public_v0.py
```

Smoke спочатку перевіряє freeze manifest і всі 21 frozen artifact hashes.
Потім заново оцінює identity, deterministic fixture-rule і збережений
`gpt-5.6-terra` run. Усі три нові report objects мають точно збігтися із
закоміченими звітами.

Очікуване завершення:

```text
identity: 677 responses, edit F0.5=0.0000, headline calque R=0.0000, exact=0.0000
deterministic fixture rules: 677 responses, edit F0.5=0.0000, headline calque R=0.0000, exact=0.0000
gpt-5.6-terra saved run: 677 responses, edit F0.5=0.2439, headline calque R=0.1410, exact=0.1610
public v0 smoke passed: frozen scoring reproduced without provider credentials
```

Значення загального F0.5, основної повноти виправлення кальок і відсутньої
влучності для кальок пояснено в
[українському описі даних](DATA_CARD.uk.md). Цей документ зосереджено на
командах і технічній перевірці результатів.

Окремі fail-closed команди:

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

Остання команда записує тимчасовий звіт; вона не змінює frozen artifacts.

## Відтворення dataset із pinned upstream

Ця перевірка додатково потребує clone UA-GEC на точному commit:

```bash
git clone https://github.com/grammarly/ua-gec.git /tmp/ua-gec
git -C /tmp/ua-gec checkout 4757f72f192c4a41e4c8fb1d9690a948f87cf6d6

.venv/bin/python scripts/projects/ua_eval_harness/build_heldout_manifest.py \
  --ua-gec-root /tmp/ua-gec \
  --check
```

Екстрактор перевіряє upstream file hashes, license/version evidence,
writer/document split, усі 2 690 sentence dispositions і точний payload hash.

Для повного відтворення heritage/style disposition завантажте pinned
dict_uk/VESUM v6.8.0 asset, SHA-256
`e33803783ac138e6f3af2cf0e9428ba146c0ecfda7f5c41fe83ae00c7af24be9`, і
запустіть:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/build_scoring_dispositions.py \
  --asset /path/to/dict_corp_vis.txt.bz2 \
  --check
```

Asset та derived evidence мають CC BY-NC-SA 4.0; точний URL, revision і
license receipt наведено в
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). VESUM attestation/style
markers є candidate evidence, не автоматичним contextual adjudication.
Повніша contextual activation залишається залежністю issue #5092; public v0
fail closed виключає unresolved records із headline scoring.

## English quickstart

Requirements: Git, `uv`, and CPython 3.12.8. No provider account, API key,
private repository, product state, or live model call is required.

```bash
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
uv venv --python 3.12.8
.venv/bin/python scripts/projects/ua_eval_harness/smoke_public_v0.py
```

The smoke verifies the immutable release manifest, validates all complete
saved-response runs, re-scores all 677 responses in each run, and requires
byte-equivalent report objects. It reads only the public files committed under
`data/projects/ua_eval_harness` and the public scorer/extractor scripts.

The [English data card](DATA_CARD.en.md) defines overall edit F0.5, headline
calque recall, and why calque precision is not reported. This guide focuses on
the commands and technical verification of those results.

To score a new saved-response file, first create a source-only request packet:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py prepare \
  --output /tmp/ua-eval-requests.jsonl
```

Generate responses outside the scorer using only the request fields, then
import them with versioned model/provider/decoding metadata:

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

The importer rejects incomplete coverage, duplicate IDs, source/prompt drift,
response tampering, and gold-shaped fields. Live generation is optional and
outside the credential-free reproduction path.
