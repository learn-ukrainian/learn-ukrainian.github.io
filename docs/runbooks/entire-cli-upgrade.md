# Entire CLI 0.11.5 install and rollback

Issue: [#10846](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10846).
Decision: [ADR-018 § Amendment: Entire 0.11.5](../architecture/adr/adr-018-entire-acp-context-layer.md#amendment-entire-0115-2026-10-16).

Run this after the PR that pins 0.11.5 has merged, from the primary checkout on
`main` at the merged commit. Do not install earlier: until the merge, the
repository code pins 0.8.42 and its preflight fails closed against a 0.11.5
binary. Install promptly after the merge: from then on every Entire entry point
runs through `scripts/entire/capture_guard.sh`, which refuses capture on a
0.8.42 binary. Each hook prints one
`[entire] capture refused (cli_version_not_accepted)` line, and commits and
pushes are not affected. A failed step in **Verify** means **Rollback**, not a
fix in place.

Never run `entire enable --force`, `entire agent add`, `entire doctor --force`,
`entire clean` or `entire disable --uninstall` as part of this procedure. They
rewrite the repository-managed hook configuration or delete session state and
legacy shadow branches.

## Install

1. Record the live binary and keep a rollback copy beside it.

   ```bash
   entire_bin="$(command -v entire)"
   entire_dir="$(dirname "$entire_bin")"
   "$entire_bin" version | head -n 1      # expect: Entire CLI 0.8.42
   sha256sum "$entire_bin"
   cp -p "$entire_bin" "$entire_bin.0.8.42"
   ```

2. Download the release into a new empty directory and verify it. The vendor
   publishes `checksums.txt` but no signature, so the digests the #10846 canary
   verified are pinned here. This is the Linux x86-64 archive; another
   architecture needs its own archive and its digest from the same
   `checksums.txt`.

   ```bash
   dl="$(mktemp -d)"
   base=https://github.com/entireio/cli/releases/download/v0.11.5
   curl -fsSL -o "$dl/checksums.txt" "$base/checksums.txt"
   curl -fsSL -o "$dl/entire_linux_amd64.tar.gz" "$base/entire_linux_amd64.tar.gz"
   echo "d3dce3e819f7e8d679eab9e12845fe3bf7d3fa711b3d8a18866624b7bdf143b6  $dl/checksums.txt" | sha256sum -c -
   echo "c20476c4ba9689b1800fe8d590601792e2b6f3c89d03a95280d88484029d7eba  $dl/entire_linux_amd64.tar.gz" | sha256sum -c -
   (cd "$dl" && grep " entire_linux_amd64.tar.gz$" checksums.txt | sha256sum -c -)
   tar -xzf "$dl/entire_linux_amd64.tar.gz" -C "$dl" entire git-remote-entire
   ```

3. Replace the binary by rename, so a hook that is running keeps the old file,
   and add the `git-remote-entire` helper that 0.11.5 ships.

   ```bash
   install -m 0755 "$dl/entire" "$entire_dir/.entire.new"
   mv -f "$entire_dir/.entire.new" "$entire_bin"
   install -m 0755 "$dl/git-remote-entire" "$entire_dir/.git-remote-entire.new"
   mv -f "$entire_dir/.git-remote-entire.new" "$entire_dir/git-remote-entire"
   rm -rf "$dl"
   ```

4. Deploy the merged agent configuration, which carries the 0.11.5 hook
   timeouts (Stop and post-task 120 s) and the guarded hook commands:
   `npm run agents:deploy`.
5. Rerun the hook installer. It routes each Entire git hook wrapper's
   `entire hooks git` call through the capture guard: `scripts/install_git_hooks.sh`.
   It refuses, and changes nothing, when the hooks directory or a hook file is a
   symlink; replace the link with a regular file and rerun it. Rerun it after
   anything rewrites Entire's wrappers, for example an `entire enable` an
   operator runs outside this procedure.

## Verify

Every line must hold.

```bash
entire version | head -n 1
# exactly: Entire CLI 0.11.5
entire status --json | .venv/bin/python -c 'import json, sys; s = json.load(sys.stdin); print(s.get("checkpoint_sync_remote_source"), s.get("checkpoint_sync_remote"), s.get("checkpoint_remote_ignored"))'
# exactly: dedicated learn-ukrainian/entire-checkpoints-private None
entire doctor </dev/null
# read-only without a terminal; it must not report a git-hook or metadata-branch failure
.venv/bin/python scripts/entire/private_mode_preflight.py --repo-root .
# "ready": true
.venv/bin/python -m scripts.entire_context refresh-provider-status
# "available": true, "version": "0.11.5"
scripts/install_git_hooks.sh --check
# every declared stage ok; no UNGUARDED or UNSAFE line
scripts/entire/capture_guard.sh --budget 20 version
# exactly: Entire CLI 0.11.5 (and its Go line), with no "[entire] capture refused" line
git ls-remote --heads origin 'entire/*'
# no output
```

Expected `entire doctor` warnings that are not failures: Claude Code and
OpenCode hook configuration "OUT OF DATE". The repository manages those files
and keeps its own matchers; see the ADR amendment residuals.

Then prove the outcome on real work:

1. After the next interactive agent turn, `.entire/logs/entire.log` shows
   `turn-start` followed by the `TurnStart` phase line and `turn-end` followed by
   the checkpoint line and the `TurnEnd` phase line for that session. A missing
   phase line is a failure, not a pass. The start gap should be about two
   seconds, not the 6–27 s seen on 0.8.42.
2. After the next agent-made commit is pushed, the commit carries an
   `Entire-Checkpoint:` trailer, `git ls-remote --heads origin 'entire/*'` is
   still empty, and
   `git ls-remote --heads https://github.com/learn-ukrainian/entire-checkpoints-private.git entire/checkpoints/v1`
   shows a new tip.
3. Authenticated search, which the canary did not run because it used no
   credentials:
   `entire search "<non-sensitive canary term>" --json --limit 1 --repo learn-ukrainian/learn-ukrainian.github.io`
   returns JSON with a `counts` object, and
   `.venv/bin/python -m scripts.entire_context refresh-provider-capabilities --query "<same term>"`
   reports `private_boundary.ready: true`.

## Rollback

```bash
entire_bin="$(command -v entire)"
entire_dir="$(dirname "$entire_bin")"
install -m 0755 "$entire_bin.0.8.42" "$entire_dir/.entire.new"
mv -f "$entire_dir/.entire.new" "$entire_bin"
rm -f "$entire_dir/git-remote-entire"
entire version | head -n 1
# exactly: Entire CLI 0.8.42
```

Then revert the 0.11.5 PR through a normal reviewed PR
(`git revert <merged-commit-sha>` on a new branch). Until that revert lands, the
merged code pins 0.11.5: the preflight and the capture guard both fail closed
against 0.8.42, so native recall and capture stay off (commits and pushes are
unaffected) until the revert lands.

Downgrading discards pending, uncommitted agent session state (Entire 0.11.5
release notes). Legacy shadow branches that 0.8.42 wrote are not removed
automatically by either version; leave them, since removing them is a separate,
operator-approved cleanup. The #10846 canary ran 0.8.42 after 0.11.5 in the
same clone: it captured a turn, pushed its checkpoint only to the private
repository, and read a checkpoint that 0.11.5 had written.
