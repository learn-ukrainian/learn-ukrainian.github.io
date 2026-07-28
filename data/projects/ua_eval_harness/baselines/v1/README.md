# Baseline receipts v1

These are complete saved-response runs for the 677-item
`ua-gec-calque-grammar-heldout-v1` manifest. Scoring is reproducible without
provider credentials.

| Run | Edit P | Edit R | Edit F0.5 | Exact sentence | Unchanged | Over-edited |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Identity v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 677 | 0 |
| Train-fixture literal rules v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 673 | 4 |
| `gpt-5.6-terra` | 0.3110 | 0.1309 | 0.2439 | 0.1610 | 310 | 258 |

The Terra run produced 144 exact edit true positives, 319 false positives, and
956 false negatives. Its deterministic 1,000-sample sentence-bootstrap 95%
interval is 0.2073–0.2780 for edit F0.5 and 0.1344–0.1891 for exact-sentence
accuracy.

Edit metrics use the best-F0.5 upstream annotator per sentence with a
deterministic tie-break. The headline F0.5 is therefore more lenient than a
strict single-reference score and must not be compared directly with a
single-reference shared-task result.

## Files

| File | SHA-256 |
| --- | --- |
| `generation_requests.jsonl` | `ec7d5b4e4216d484d3d2243f4a09c4cf82aab423ec918acb424fcf76f2ebdf83` |
| `identity.responses.jsonl` | `eb9414fb71b6a520f9bd3d3d7e709840c908ee2c8c85de30a005f2b3f223a7c6` |
| `identity.report.json` | `028f2254b82e8c9e3e8d4b7ac5bb2653fa094a24c4eda11b52047f9ab96f69b7` |
| `fixture-rules.responses.jsonl` | `cc22f750fcfd889f1054a7d48d010efe7add9a610ffc9ba2e2f139236cf29321` |
| `fixture-rules.report.json` | `756f5c52a415ef7c69271ab122cda1e8ccd26a724f799bbf01a37bd0f52995e5` |
| `gpt-5.6-terra.responses.jsonl` | `e966913bd151f6a54170bc91442388cb68688965c9951c2d76088199c0ebe63b` |
| `gpt-5.6-terra.report.json` | `761be57af975bcf3797732e7c2fa38b7b861d503e7ec7c31b3105056ad221f7c` |

Each report repeats its saved-response hash and carries the manifest payload
hash, prompt hash, scorer source hash, model/provider/version, decoding
settings, runner version, input field allowlist, and gold-firewall receipt.

The real run used:

- model ID and model version: `gpt-5.6-terra`;
- provider route: OpenAI subscription through `codex-cli 0.145.0`;
- runner source:
  `06453da9cf0750aac5065650c510f4d03e1d7d2ef9ca21be1fefd719c1f1590b`;
- structured-output schema:
  `93fda1b52e570cfc3c6431bb77e55d4e0047bf9cf92c45e4c5107b10e47ba710`;
- prompt:
  `f121546dcbaf602c58c7d85977ad792eb9be402dd1e01a6a556ba966dac2c96a`;
- seven source-only batches, size 100 except the final 77, with three
  parallel workers;
- provider-default temperature/top-p and no exposed seed.

No target, reference, edit span, held-out score, Hramatka payload, teacher
feedback, Atlas/Practice data, synthetic example, or training data entered the
real-model process. The process ran in an empty temporary directory with a
read-only sandbox, a minimal environment allowlist, and repository/user rules
disabled.

The prompt wording received one formatting-only clarification after a two-item
source-only transport smoke: it was made explicit that token spacing and
punctuation must be preserved. No gold target, edit, or score was inspected,
and the committed run used only the final prompt.
