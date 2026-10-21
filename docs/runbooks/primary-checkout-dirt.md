# Primary-checkout dirt: audit and self-cleanup (#11253)

Write-capable dispatch refuses to start while the protected primary checkout
has tracked changes or untracked, non-ignored files (`PRIMARY_DIRTY`,
`scripts/delegate.py::_resolve_dirty_primary_checkout_error`). The command-text
guard `guard-primary-checkout-write.py` blocks the writes it can read in a
shell command, but not what a launched script does: a script that `cd`s into
the primary checkout and then redirects to a relative path writes there unseen.

## The audit hook

`agents_extensions/shared/hooks/audit-primary-checkout-dirt.py` wraps every
shell call:

- **Before the call** (PreToolUse) it records the `git status
  --porcelain=v1 -z --untracked-files=all` entries of each protected primary
  checkout that owns the call's cwd or the project directory.
- **After the call** (PostToolUse; on Claude also PostToolUseFailure, where a
  non-zero exit goes) it compares again. A path that is dirty now and was not
  dirty before is attributed to the call. The hook writes an attribution
  record and exits 2, so the agent sees the new paths, the command, the
  record id and the exact cleanup command.

What it does not do:

- It blocks nothing. The call has already run, and a failing snapshot never
  stalls a session. An internal error after the call exits 1, which the
  harness shows as a hook error. When the pre-call snapshot is missing, a
  dirty primary is reported as "not audited" rather than attributed.
- Paths that were already dirty before the call are never attributed to it.
- Git-ignored paths never appear, because `git status` omits them.
- The probe sets `GIT_OPTIONAL_LOCKS=0`, so it never rewrites the primary
  index.

Wiring:

- Claude: `agents_extensions/shared/settings.json`, `Bash` matcher on
  PreToolUse, PostToolUse and PostToolUseFailure. These hooks are fail-open
  (no `onFailure`).
- Codex: `scripts/agent_runtime/codex_hook_policy.py` takes the snapshot
  only after every PreToolUse guard has allowed the call.
  `scripts/agent_runtime/codex_hook_entry.sh post-tool-use` runs the
  comparison for `Bash`. Codex runs PostToolUse after non-zero exits too, and
  its exit 2 replaces the tool result with the report.
- Dispatched Claude workers are not wired: their settings carry PreToolUse
  guards only, and they write in their own worktree.

## Cost

Each shell call runs two status probes. On the full repository (about 33,000
tracked files, clean tree), one probe measured 0.13–0.15 s and about 16 MB
RSS. The whole hook, interpreter start-up included, measured a median of
274 ms (max 329 ms) before the call and 198 ms (max 235 ms) after it, over 20
calls at load average 10 on 16 CPUs. On Claude the pre-call phase runs in
parallel with the PreToolUse guards. Each git probe has a 3 s deadline. A status listing more than 20,000
entries makes the call unauditable rather than slow. Only new untracked files
are fingerprinted: at most 200 per call, and files are hashed only up to
8 MiB.

## Removing your own files

The report prints the command. Run the dry run first, then apply:

```bash
.venv/bin/python -m scripts.hygiene.primary_dirt_cleanup --session '<session>' --record '<record>'
.venv/bin/python -m scripts.hygiene.primary_dirt_cleanup --session '<session>' --record '<record>' --apply
```

The command removes a file only when all of these hold:

- the session's record exists and names a root that is still a protected
  primary checkout;
- the file was untracked when recorded and is untracked now;
- its path is relative, contains no `..` or `.git` component and passes
  through no symlink (`O_NOFOLLOW` at every step);
- it is a regular file whose device, inode, size, mtime and SHA-256 match the
  record;
- no other session's record claims the same file.

Everything else is refused and reported in the JSON output:

| Outcome | Meaning |
| --- | --- |
| `refused:tracked_entry` | a tracked change, which this command never touches |
| `refused:tracked` | the file became tracked after it was recorded |
| `refused:modified_since_attribution` | the file changed after it was recorded |
| `refused:claimed_by_other_session` | another session's record claims the file |
| `refused:symlink`, `refused:symlink_or_non_directory_in_path` | a symlink on the path |
| `refused:invalid_path`, `refused:primary_root_invalid` | a forged or out-of-root record |
| `refused:not_untracked`, `refused:not_a_fingerprinted_regular_file` | not plain untracked file content |

Exit codes: 0 means every entry was removable, removed or already absent; 1
means there is no matching record and nothing was done; 2 means at least one
entry was refused.

With `--apply`, the command appends one receipt per entry to `cleanup.jsonl`.
It never removes directories: Git does not report empty directories, so they
do not dirty the checkout.

Tracked changes need a deliberate restore, for example `git checkout --
<path>`; the primary-checkout guard allows that rescue form. Make sure nobody
else made the change first. Anything the command refuses still needs the
operator, as before.

## State

Records, snapshots, the `audit.jsonl` log and `cleanup.jsonl` receipts live in
`$XDG_STATE_HOME/learn-ukrainian/primary-dirt-audit/` (default
`~/.local/state/...`), outside the repository. Directories are mode `0700` and
files `0600`. Snapshots whose post phase never ran (denied or cancelled calls)
are deleted after 6 hours. Records are kept as the audit trail.

## Threat model

This is a safety net for honest-agent mistakes, plus attribution. A process
running as the same user can bypass it. It can skip the hooks, write between
two snapshots, or edit the state directory. Session binding is by knowledge of
the session id printed only to that session. It is not authentication.
Attribution is temporal: a path that appears while two calls overlap is
recorded for both, so the cleanup command refuses a file that another
session's record also claims.
