# Review-contract canary

A change to the review output contract enters the merge queue only after one live read-only review
per required reviewer route settles `done` with a canonical receipt on the PR's exact head, under
the candidate's own dispatcher (#12399). Unit tests with fixtures, and a review that runs on the old
dispatcher, cannot show that a new schema or reply parser still works on a real provider: PR #12372
passed both and then no Codex, Claude or Grok review could settle (#12380, #12394, #12390).

## What is gated

`scripts/review/contract_canary.py` declares the contract paths once (`CONTRACT_PATHS`): the bound
findings schema, the receipt gate, the verdict parser, the recorder, settlement, the dispatcher
worker and output-schema binding, and each reviewer provider's schema and reply handling. The
merge-queue keeper and `scripts.publish pr-merge` read the PR's file list. When it touches one of
those paths, both refuse the head with the typed reason `needs-contract-canary` and one detail:

| Detail | Meaning |
| --- | --- |
| `missing: <routes>` | No receipt at this head for the routes named. |
| `stale: …` | A receipt is bound to other contract or dispatcher bytes. |
| `unverifiable: …` | The route list, the head's tree or a receipt could not be read. |

The required routes are every route of an active formal-review candidate in
`scripts/config/model_catalog.yaml` (today `agy`, `claude`, `codex`, `cursor`, `muse`). Print the
current list with `python -m scripts.review.contract_canary routes`. A route that is down or out of
quota blocks the change; it never shrinks the list.

## Canary evidence is not a review

A canary task is pinned to a head with no `--branch` and no `--pr`, so it spends no review round
and `record_cf_verdict` refuses it ("review was not branch-pinned"). Its receipt is written to
`batch_state/review-contract-canary/<head>/<route>.json` with `eligible_as_review: false`, outside
the PR comments the verdict lookup reads. The review of record still follows `review-loop`, and
the canary does not change who reviews, risk floors or round budgets.

## Recipe

Run from the candidate's own worktree, checked out clean at the pushed PR head. `scripts/dispatch.py`
always runs the primary checkout's dispatcher, so call `cli.main` directly; the supervisor then
runs the worktree's code and records it as `dispatcher_code` in the task record.

```bash
PY="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.venv/bin/python"
HEAD_SHA="$(git rev-parse HEAD)"
# One line per required route: agent and a formal model on it.
for route_model in agy:gemini-3.8-flash-high claude:claude-sonnet-5-5 codex:gpt-6.1-sol \
    cursor:grok-4.7-high muse:muse-wonder-full-1.0; do
  route="${route_model%%:*}"; model="${route_model#*:}"
  "$PY" -c "import sys; from scripts.dispatcher import cli; sys.exit(cli.main(sys.argv[1:]))" dispatch \
    --agent "$route" --model "$model" --effort medium --mode read-only --worktree \
    --task-id "contract-canary-$PR-$route-${HEAD_SHA:0:8}" --prompt-file "$CANARY_BRIEF" \
    --pinned-head "$HEAD_SHA" --review-profile code --require-review-verdict
done
```

`$CANARY_BRIEF` is a short read-only review brief of the PR diff that asks for the reply object in
`schemas/code-review-findings.v1.schema.json`. The verdict does not matter; the receipt does. When
each task settles `done`, record it:

```bash
"$PY" -m scripts.review.contract_canary record --task-id "$TASK" --pr "$PR"
```

`record` refuses a task that did not settle `done`, was not read-only and verdict-bound, was not
run on a worktree that started and settled at one head, was branch- or PR-pinned, was not supervised by a clean dispatcher at
that head, ran on a route or model outside the catalog's formal set, or whose reply is not a
canonical receipt. The receipt is keyed by that head; the gate reads only the PR's live head, so
receipts for an older head admit nothing. Check the head before enqueueing:

```bash
"$PY" -m scripts.review.contract_canary check --head "$HEAD_SHA" $(gh pr diff "$PR" --name-only)
```

Every new head needs new receipts. A task that fails on a route is a finding about the change,
not a reason to skip that route.

## Prior art

Path-triggered required presubmits are the established pattern: Prow's `run_if_changed`
([docs](https://docs.prow.k8s.io/docs/jobs)) and LUCI CQ's `location_filters` on tryjob
verifiers run integration jobs only when matching files change, and make them part of the merge
decision. This canary applies the same rule with live reviewer runs as the integration job.
