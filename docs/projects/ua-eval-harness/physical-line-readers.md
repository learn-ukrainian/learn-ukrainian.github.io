# Physical line framing and frozen releases

The active readers preserve U+0085, U+2028, and U+2029 inside JSON strings
and M2 source and annotation text. CR, LF, and CRLF delimit physical records.
JSONL blank-record rules and the saved-response schema remain unchanged.

The active scorer is `ua_eval_exact_token_edits.v2`. The saved-response runner
ID remains `ua_eval_saved_response_runner.v1` for byte-compatible imports.
The provider-neutral batch runner is `ua_eval_provider_neutral_batch_runner.v1.4`.
Scoring and request schemas, edit alignment, metrics, and baseline inputs are
unchanged. Completed batch states remain bound to their recorded runner version;
version 1.4 refuses version 1.3 states rather than rewriting them.

Release `0.1.0` and `0.1.1` manifests and saved reports keep their original
bytes. `release_sources.py` resolves the frozen extractor, evaluator, batch
runner, and `0.1.1` smoke source to exact copies under
`data/projects/ua_eval_harness/releases/v0.1.1/`. Their hashes match the
existing release receipts. Missing or changed copies fail release verification.
These copies record historical source identity; active commands use the
corrected readers under `scripts/`.

The public smoke commands verify the historical freezes, then re-score all
saved baselines with the active scorer. They require identical report fields
except for the scorer ID and implementation hash, which must identify the
active scorer. They do not rewrite historical reports.

The standalone Gemma probe collector uses the same physical boundaries without
an import from the repository. Its current source pin changes; the original
authorization and both earlier runner identities remain accepted for historical
receipt verification. No provider job or authorization is created by this change.
