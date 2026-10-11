# Claude through the AGY review route

The adapter accepts `claude-sonnet-5-5-high` and `claude-opus-5-5-high`.
The display strings `Claude Sonnet 5.5 (High)` and `Claude Opus 5.5 (High)`
resolve to those same slugs. Bare, low, medium and unknown Claude names remain
unsupported. Retired Claude 4.6 Thinking labels retain the retirement refusal.

These pins require the existing AGY review route. That route denies
`command(*)` and `write_file(*)` in its scoped permission settings and passes
`--sandbox`. Non-review routes pass `--dangerously-skip-permissions`, including
ordinary read-only dispatches, so the adapter refuses these Claude pins there
before writing permissions or probing the CLI. The error starts with
`agy_claude_requires_review_route`, includes the original model argument and
says `rejected`. The delegate substitution probe recognizes this refusal and
cannot silently replace the request with Gemini or native Claude.

The catalog records an AGY transport and wire id for each model. It adds no
reviewer candidate, seat route, ladder entry or substitution rule. Existing
role, risk and independence gates still apply. Anthropic-family models cannot
review Anthropic-authored work, regardless of transport. Do not pass `--effort`;
the adapter uses the explicit high slug and leaves effort unwired.

The `agy` endpoint has the `agy` accounting bucket. Models have no separate
bucket field. No Claude/GPT quota pool is claimed here. Adapter admission does
not prove provider availability, model-list presence or qualification.

## Driver qualification procedure

The accountable driver runs qualification after independent exact-head review.
The implementation worker runs no provider generation.

1. For each variant, bracket one bounded generation on the permission-denied
   review route with aggregate allowance readings and UTC timestamps. Keep the
   prompt, route, adapter revision and success criterion fixed. Record only
   privacy-safe evidence and the before/after pool delta. Unavailable readings
   remain unknown; a delta alone does not establish a shared quota pool.
2. Capture the provider's NDJSON `init` model identity event. Require its model
   to equal the requested resolved slug and require the specified semantic
   response. A mismatch fails with `agy_model_event_mismatch`. An absent model
   remains unknown on the parse result and does not qualify the variant.
   Tool turns such as `PLANNER_RESPONSE` are not identity evidence.
3. Run a no-substitution control for both explicit slugs using the real delegate
   adapter probe and substitution resolver with the non-review shape. Require
   the typed route refusal before any subprocess and no Gemini or native Claude
   substitution. Keep the review command/write denials in place.

Stop on a refusal, identity mismatch, missing identity, semantic failure or
unexpected substitution. Record each variant separately; do not infer the
other variant's qualification or silently retry through another transport.
