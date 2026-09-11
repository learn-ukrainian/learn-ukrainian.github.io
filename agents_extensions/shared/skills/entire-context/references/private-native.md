## Product prompt workflow and private native Entire mode

For product-style prompts, use `search` for relevant past-work locators. Add
`explain-change` only when an exact provenance path matters, and `handoff` only
when participants need a verified capsule. These are conditional follow-ups,
not a requirement to load every linked record. Use the `.venv/bin/python`
commands above for the canonical body-free recall path.

The operator-authorized private mode in `.entire/private-recall.json` permits
the accountable root to use native Entire search, explain, recap, dispatch,
and private handoff when those tools materially help the task. Before first
use, run `.venv/bin/python -m scripts.entire.private_mode_preflight` and require
its body-free receipt to report `"ready": true`. It verifies routing, private
checkpoint visibility, public-ref absence, authentication, exact private
Entire ACLs on both mirrors, mirror readiness, and the exact 0.8.42 pin without
printing command output or local paths. Use only these shapes:

```bash
entire search "<query>" --json --limit <1-10> \
  --repo learn-ukrainian/learn-ukrainian.github.io
entire checkpoint explain <checkpoint-id-or-sha> --json
entire checkpoint explain <checkpoint-id-or-sha> --full --no-pager
entire recap --static <--day|--week|--month|--90>
entire dispatch --local --all-branches --since <window>
```

`dispatch` is also the native private handoff surface. The accountable root may
consume search and explain results inside its private task context. Never place
prompt-bearing output in a distributed capsule, a public issue/PR, or
formal-review evidence; external disclosure requires operator review. Full
explain requires a task that needs exact continuity and must not be fanned out
to workers. `--all-repos`, `--code`, `--generate`, `--force`,
`--raw-transcript`, and `--transcript` remain forbidden. Full explain is
allowed without a second operator prompt when exact continuity is relevant.
Recap/dispatch and worktree-mutating resume/rewind still require a present
operator request. Entire review is supplemental and never satisfies the sealed
Fleet formal-review gate. Provider failure, an empty search index, or a rate
limit must be reported truthfully and never changes the canonical workflow
outcome.

Current official product references:

- [Entire Skills](https://docs.entire.io/learn/skills)
- [Review and recap agent work](https://docs.entire.io/learn/review-and-recap-agent-work)
- [Search past agent work](https://docs.entire.io/learn/search-past-agent-work)
- [Investigate why code exists](https://docs.entire.io/learn/investigate-why-code-exists)
