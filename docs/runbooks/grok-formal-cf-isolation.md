# Grok code and infra review routing

Native Grok dispatch and the former sealed formal CF path are retired.
Grok 4.7 code and infra reviews run through the Cursor seat at `grok-4.7-high`.
The catalog and reviewer resolver determine eligibility at every risk, including critical.

## Dispatch

Use the resolver-selected invocation. The explicit Grok dispatch route is:

```bash
.venv/bin/python scripts/dispatch.py dispatch --agent cursor --model grok-4.7-high \
  --mode read-only --task-id <task-id> --prompt-file <brief>
```

Dispatch v2 maps `--agent grok` to Cursor.
That alias does not launch the native Grok CLI. Native TUI and bridge callers
outside detached dispatch retain their own interfaces and do not establish
eligibility for resolver-selected review.

## Review requirements

- Pin `grok-4.7-high` and require Cursor's runtime model attestation.
- Exclude xAI-authored work and the reviewer's own subject seat.
- Supply the diff and CI evidence. Grok reviewers read tracked files and do not
  run shell commands, tests or scripts. Use Opus 5.5 or Sol 6.1 for reviews that
  require execution.
- Record the exact reviewed head and concrete model, family and transport.
  Follow `review-loop` and the same-head CI gate before landing.
- Cursor Grok stays off Ukrainian language seats. Security final sign-off stays
  with Opus 5.5 or Sol 6.1.

The retired sealed path supplies no current isolation or review receipt guarantee.
See [model assignment](../../agents_extensions/shared/rules/model-assignment.md)
and [the activity matrix](../best-practices/agent-activity-matrix.md).

Parent: #5557 · stream #4707 · product #5512.
