# Agent success metrics

`scripts.fleet.agent_success` reports metadata from dispatch-v2 task records and final review results. It makes no network requests and writes no records.

```bash
.venv/bin/python -m scripts.fleet.agent_success
.venv/bin/python -m scripts.fleet.agent_success --window 24h --json
.venv/bin/python -m scripts.fleet.agent_success --since 2026-10-25 --until 2026-10-28 --json
```

`--window` accepts `24h`, `3d` (default), and `14d`. Explicit `--since` overrides the duration. `--until` defaults to the current UTC time. Dates and timestamps without an offset use UTC.

`--tasks-dir` overrides `LU_TASKS_DIR` and the primary checkout's task store. Both the hot directory and its `archive/` are included. JSON output contains no task identifiers, file paths, prompts, result bodies, or raw diagnostics.

## Denominator and coverage

The cohort contains records with integer `schema_version: 2`, a task ID, a run nonce, and `started_at` in the inclusive-start, exclusive-end window. Dry runs are excluded. Legacy records do not enter the v2 denominator.

Each task ID and run nonce identifies one run. A duplicate hot record takes precedence over its archived copy, consistent with the task store's by-ID reader. A repeated task ID with a different nonce counts as another run. Records with invalid JSON or missing identity or timestamps are counted in `coverage`. Such exclusions make `complete` false. A missing or unreadable required directory also makes `available` false. An absent archive is valid.

`success` is done divided by all included runs. `terminal_success` is done divided by done, no_deliverable, failed, timeout, rate_limited, cancelled, and crashed. Running, spawning, needs_finalize, and unknown statuses remain visible outside the terminal denominator. The collector never probes processes or changes a stale status.

`by_agent` and `by_model` each cover the cohort. Concrete labels come from recorded model fields, with positively recorded runtime resolution taking precedence. Cursor display names use the shared model normalizer. Both requested and resolved labels then use explicit catalog aliases, wire IDs, and runtime IDs, so failed runs cannot split from successful runs of the same model. Uncatalogued labels remain visible. A missing catalog makes normalization unavailable instead of guessing. Missing, unsafe, Auto, and default identities become `unknown`. `model_sources` distinguishes requested labels from resolved identities. Requested labels alone do not attest execution. Different roles and task mixes can explain model differences; these counts do not establish a causal ranking.

## Recorded metrics

Each optional metric contains a `value`, an `observed` count, and an `unknown` count. Values aggregate observed evidence only. No observations produce the literal `unknown`, including an empty cohort. Known zero remains zero.

| Metric | Evidence |
| --- | --- |
| Status and failure classes | Recorded status and closed diagnostic classes. Unknown diagnostics stay unknown. |
| No-deliverable reasons | Closed reason labels, including `outside_owned_paths`. Path suffixes are discarded. |
| Median wall seconds | Terminal run `duration_s`, or a nonnegative finished-minus-started span. Coverage is over terminal runs. |
| PRs opened and merged | Explicit `pr_opened` or `pr_merged` booleans on write runs. True also requires a numeric `pr` or `pr_number` and a repository identity. PR identities are deduplicated within each group. Review target PRs, pushed branches, and done statuses prove neither event. |
| Merge-group CI failures | Explicit nonnegative integer `merge_group_ci_failures` per run. Admission CI is not substituted. |
| Cost in USD | Explicit numeric `cost_usd` or `total_cost_usd` on the record or its usage. No pricing estimates or allowance credits. |
| Tokens | Recorded numeric provider fields, normalized to input, output, total, cache read, cache write, and reasoning. No inferred totals. Cache tokens remain separate because provider accounting differs. Raw input counts are not comparable across providers. |

Claude's `input_tokens` excludes cache reads and writes, which have separate fields ([Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)). Codex input includes cached input, consistent with the [OpenAI input usage breakdown](https://developers.openai.com/api/docs/guides/prompt-caching). Muse adapter payloads retain provider-native input and cached fields; the collector does not assume they are disjoint or add them. These accounting differences prevent a direct cross-provider comparison of raw input counts.

Muse tokens come from `usage.models[]` in its adapter records. Entries for the task's model are summed. A different child model's tokens are not attributed to the parent model, and child usage creates no dispatch rows. Missing fields stay unknown. Claude thinking tokens also accept `usage.output_tokens_details.thinking_tokens`; Cursor camelCase usage keys are normalized.

## Reviews

Review runs have explicit review metadata (`require_review_verdict`, `review_profile`, or `review_author_model`). A done review can supply a verdict in its final result, or explicit structured `review_verdict` metadata. The shared verdict parser normalizes APPROVE and REQUEST_CHANGES aliases. Missing, contradictory, unreadable, or nonterminal results stay unknown.

Final results must be adjacent `.result` regular files, without symlinks, under the record's hot or archive directory. Their bytes must match the recorded `result_sha256`. Reads are bounded to 4 MiB. This prevents an archived run from borrowing a later run's verdict.

`rounds_to_approval` reports the median explicit positive integer `review_round` on approved reviews, with missing rounds visible. It does not infer a full review history from a partial window or task-name suffixes. `changes_requested` counts normalized verdicts, not failed dispatches.

Finding counts and severities use structured finding metadata or explicit `F<n>` finding headers with P0 through P3 priorities in brackets, parentheses, or after dashes or periods. Repeated finding IDs count once; conflicting priorities become unknown. Anonymous bracketed priority headers are also supported in review results. Quoted and fenced examples do not count. Free prose cannot establish zero findings. `confirmed_findings` counts explicit boolean `confirmed` flags on recorded findings; no approval or fix is treated as confirmation. `confirmation_rate` uses only findings with explicit confirmation flags. `unobserved_finding_reviews` exposes reviews whose findings were not recorded in a supported form.

## API and exit status

The existing `/api/comms/v1/metrics` and `/api/fleet/facade/metrics` routes accept `include_agent_success=true`. The additive `agent_success` field reports the default three-day cohort from that API context's task store, independently of comms-store availability. Ordinary metrics requests do not scan task records. The async comms route offloads the scan to a thread.

The CLI exits 0 for a complete cohort, 1 for a partial or unavailable ledger, and 2 for invalid arguments. Unknown optional metrics do not make the cohort incomplete.

Fixture proof: `tests/test_agent_success_metrics.py` and `tests/fixtures/fleet/agent_success.json`, tracked under #10468. Public issue evidence uses synthetic fixtures; live ledger receipts are not published there.
