# Baseline receipts v1

These are complete saved-response runs for the 677-item
`ua-gec-calque-grammar-heldout-v1` manifest. Scoring is reproducible without
provider credentials.

| Run | Overall edit P | Overall edit R | Overall edit F0.5 | Headline calque R | Exact sentence | Unchanged | Over-edited |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Identity v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 677 | 0 |
| Train-fixture literal rules v1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 673 | 4 |
| `gpt-5.6-terra` | 0.3110 | 0.1309 | 0.2439 | 0.1410 | 0.1610 | 310 | 258 |

The Terra run produced 144 exact edit true positives, 319 false positives, and
956 false negatives. Its deterministic 1,000-sample sentence-bootstrap 95%
interval is 0.2073–0.2780 for edit F0.5 and 0.1344–0.1891 for exact-sentence
accuracy.

Overall edit metrics retain every selected UA-GEC standardization and grammar
label and use the best-F0.5 upstream annotator per sentence with a deterministic
tie-break. They must not be compared directly with a strict single-reference
shared-task result.

`F/Calque` is preserved as an upstream standardization label. The separate
benchmark disposition admits 338 of 354 annotator-level calque annotations and
fails closed on 16 register/heritage/contested annotations. Terra corrects 33
of 234 admitted annotations in its selected references, for headline calque
recall 0.1410. Calque precision is not reported because hypothesis-only edits
are untyped; overall edit precision remains the standard precision measure.

## Files

| File | SHA-256 |
| --- | --- |
| `generation_requests.jsonl` | `ec7d5b4e4216d484d3d2243f4a09c4cf82aab423ec918acb424fcf76f2ebdf83` |
| `identity.responses.jsonl` | `eb9414fb71b6a520f9bd3d3d7e709840c908ee2c8c85de30a005f2b3f223a7c6` |
| `identity.report.json` | `b278dd289783c027162c80ec48b6857db968b2834c50d6fe1fbae30022205142` |
| `fixture-rules.responses.jsonl` | `cc22f750fcfd889f1054a7d48d010efe7add9a610ffc9ba2e2f139236cf29321` |
| `fixture-rules.report.json` | `0759ba0c49c6a834acede64e0faa62c7197a6b3d5b53f4761e4eef2d479055c5` |
| `gpt-5.6-terra.responses.jsonl` | `e966913bd151f6a54170bc91442388cb68688965c9951c2d76088199c0ebe63b` |
| `gpt-5.6-terra.report.json` | `2567fb9e96c94c3a165e24607907e98edb7fc86e25634c9d788fdc10e9f19952` |

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
