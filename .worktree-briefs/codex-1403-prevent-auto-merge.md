# #1403 — Prevent danger-mode agents from auto-merging PRs

Read `gh issue view 1403` for the full incident. Two merges happened
unauthorized on 2026-04-22 evening because brief text ("user will
merge") is advisory — `--mode danger` agents follow technical
affordance, not prose prohibition.

## Fix

The delegate / bridge wrapper must make `gh pr merge` (and equivalent
API calls) **technically unavailable** to `--mode danger` agents unless
the dispatch explicitly opts in.

Three layers, implement all three:

### 1. Command-level deny list

In `scripts/delegate.py` and/or `scripts/agent_runtime/runner.py`,
when a subprocess is spawned with `--mode danger`, set an environment
variable `AGENT_NO_MERGE=1` and wrap the PATH so that a shim version of
`gh` intercepts any argv containing `pr merge` / `pr review --approve`
and exits non-zero with a clear error:

```
error: agent invoked with AGENT_NO_MERGE=1 cannot merge or approve PRs.
       User reviews and merges. See INCIDENT #1403.
```

The shim can live at `scripts/agent_runtime/shims/gh` (chmod +x) and
delegate to the real `gh` for all other subcommands.

### 2. Denylist at the git level

Also intercept direct `git push` when the target ref is `main`:
agents can push their feature branch, not `main`. Shim `git` similarly
to catch `git push origin main`, `git push --force origin main`, any
`refs/heads/main` argument. Error message references #1403.

### 3. Dispatch-brief opt-in flag

Add `--allow-merge` flag to `delegate.py dispatch`. When NOT passed,
`AGENT_NO_MERGE=1` is set. When passed, merge is permitted (rare; user
explicitly granting authority). Default off. Document in `--help`.

## Tests

- Unit: subprocess invoked without `--allow-merge` rejects `gh pr merge 1234`
- Unit: same subprocess with `--allow-merge` accepts the call
- Unit: `git push origin main` rejected without opt-in
- Integration: a full delegate dispatch in `read-only` mode never has
  access to merge (unchanged behavior)

## Worktree

```
git worktree add -b codex/1403-prevent-auto-merge .worktrees/codex-1403-prevent-auto-merge
cd .worktrees/codex-1403-prevent-auto-merge
# work, commit, push, PR
```

Do NOT auto-merge THIS PR either — if your shim works, you can't
anyway. User merges.

## Hard timeout

3600s (1h). Small scoped fix.
