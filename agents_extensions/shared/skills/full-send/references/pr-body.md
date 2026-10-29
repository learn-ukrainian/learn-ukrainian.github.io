# PR title and body

Used by `full-send` and `full-stop` when they create or update a PR. Publishing goes through the
typed publisher (`docs/dev/agent-public-text.md`), which scans every field before it is sent.

`"$PY"` is the primary checkout's interpreter ([delivery](delivery.md#interpreter)).

## Before creating

- Check whether a PR already exists for the branch: `gh pr list --head "$BRANCH" --state all`.
  Update it with `pr-edit` instead of opening a second one.
- Read the diff against the base and confirm it matches the outcome and nothing else.
- Follow the repository title style from recent merged PRs (`type(scope): what changes`). Say
  what the change achieves, not which functions moved.

## Body

1. **Problem first**, in one or two plain sentences: what was wrong or missing for whom.
2. **What changes**, briefly. No file-by-file inventory.
3. **Proof**, one line: the check or reproduction that shows it works, with the run id.
4. The public-safe subset of the hand-off record ([delivery](delivery.md#hand-off-record)):
   acceptance ids and their proof, catalog risk and budget tier, and the finding ledger.
5. A size justification when the PR is above the small-batch guide (`workflow.md` § Merge
   policy).
6. `Refs #N` or `Fixes #N` for the issue. `Fixes` closes the whole issue, so use it only when
   every acceptance criterion is delivered (`workflow.md` § Work intake).
7. **Credit**: original contributors (after `takeover`), and the model and harness that wrote
   the change, as the harness reports them. Never guess a model name.

Never put host paths, server or deployment details, private task metadata, private transcripts
or the operator's words in a title or body (rules core P8).

## Commands

```bash
"$PY" -m scripts.publish pr-create --title "$TITLE" --body-file "$BODY" \
  --base main --head "$BRANCH"
"$PY" -m scripts.publish pr-edit --number "$PR" --body-file "$BODY"
```

`pr-create` takes no labels. Open a non-draft PR so PR CI and review bots run, unless the
skill you run says otherwise (`full-stop` opens with a `[hold]` title).
