# Secret scanning (local TruffleHog)

TruffleHog is installed locally and is on every agent's `PATH` as
`trufflehog`. CI already scans every pushed range (see
[`ci-gate.md`](ci-gate.md)); this runbook covers the local scan an agent runs
itself, through one wrapper that keeps it offline and keeps secret values off the
console. Issue #9416.

## When to run it

- Before opening a PR that changes credential, identity, transport or hook code
  (launchers, auth helpers, network clients, git or agent hooks): `tree`.
- After any suspected leak (a secret pasted into a file, commit, log, issue, PR or
  transcript): `tree`, then `history`.
- When a driver needs a baseline of the whole public history: `history`.

It does not replace CI or the pre-commit hook, and it is not needed for ordinary
changes.

## How to run it

```bash
.venv/bin/python scripts/audit/secret_scan_local.py tree
.venv/bin/python scripts/audit/secret_scan_local.py history
.venv/bin/python scripts/audit/secret_scan_local.py --help
```

From a dispatch worktree, use the primary checkout's interpreter (see
[`worktree-cleanup.md`](worktree-cleanup.md) § Shared Python environment).

| Mode | Scans | How |
| --- | --- | --- |
| `tree` | Tracked and untracked-not-ignored files of the work tree | `trufflehog filesystem` over that file list (batched). Never `.git`, `.venv`, `node_modules`, `.worktrees` or database files under `data/`; symlinks are skipped. |
| `history` | Every commit on every ref of the configured public remote (default `origin`) | Clones a full bare mirror into a new temporary directory outside the repository, scans it with `trufflehog git file://<mirror> --bare`, then removes the directory. |

Why a mirror: agent checkouts are blobless partial clones. `trufflehog git`
cannot fetch the missing objects from a partial clone, and a `file://` URL to a
bare repository only works with `--bare`. The mirror clone is the full public
history, so it needs disk room for a complete clone; use `--mirror-parent` to put
it on a larger disk (it is refused inside the repository). The clone runs with no
credential helper and no terminal prompt: the remote is public.

## Fixed flags and parity with CI

The wrapper passes these flags on every call and accepts no TruffleHog
pass-through options:

| Flag | Why |
| --- | --- |
| `--no-verification` | Offline. Nothing is sent to any provider. |
| `--no-update` | No update check over the network. |
| `--results=unverified` | Offline, every candidate is "unverified". CI runs verified mode and keeps `--results=verified,unknown`; offline that filter would hide everything, so the local scan reports the full unverified superset. Expect more false positives than CI. |
| `--exclude-detectors=Lob` | Same as CI (#6575). |
| `--exclude-paths=.trufflehogignore` | Same as CI's Secret scan job, when the file exists. |
| `--fail-on-scan-errors` | A scan error is a tool error (exit 2), not a clean result. |
| `--json` | The report format the wrapper parses. |

## Verified mode is not allowed

Verified mode sends each candidate secret to the provider's API to test it.
That discloses the candidate to a third party and contacts external services
from the host. The wrapper refuses any verification-style option (`--verify`,
`--verifier`, `--results`, `--no-no-verification`, and similar) with exit 2.
Running TruffleHog in verified mode by hand, by any route, needs an explicit
operator decision first.

## Output handling

- The full JSON Lines report contains the **raw secret values** (`Raw`,
  `RawV2`, `Redacted`, `ExtraData` and others). It is written to a new file with
  owner-only permissions (0600) outside the repository: by default a fresh
  `secret-scan-<mode>-*.jsonl` in the system temp directory, or `--output PATH`,
  which must not exist and is refused inside the repository or its primary
  checkout. TruffleHog's own log goes beside it as `<report>.log`, also 0600.
- The console shows only the count per detector and one row per finding:
  detector, file, short commit (history) and line. Author emails are not shown.
- Never paste the report, the log, a `Raw`/`Redacted` value or a screenshot of
  them into a PR, issue, comment, commit, chat or transcript. Public text quotes
  detector, file, short commit and line, or just the count.
- Delete the report and log when triage is finished.

Exit codes: `0` no findings, `1` findings, `2` refusal, missing binary, git or
TruffleHog error, or timeout. A missing binary prints a typed message pointing
here.

## Triage

1. Read the rows. For each, open the file at that line (or `git show
   <commit>:<file>` for history) locally and decide: test fixture, public
   identifier, hash or other false positive; or a possible real credential.
2. False positive in a file that should never be scanned (lockfiles, generated
   hashes): propose a `.trufflehogignore` entry in a reviewed PR. For a single
   line, an inline `trufflehog:ignore` comment is the narrower fix. Never widen
   the exclusions to silence a real credential.
3. Possible real credential: stop. Do not try it, do not verify it, do not
   remove it in a quick commit (history keeps it). Report to the operator
   through the private channel with detector, file, short commit and line only.
   The operator decides on rotation or revocation; agents never rotate, revoke
   or rewrite history.
4. Public issue text records only the count and the outcome ("N candidates, all
   false positives" or "handed to the operator"), never the value or where a
   credential is used.

## Relation to the other secret gates

| Gate | When | Scope |
| --- | --- | --- |
| gitleaks (`.pre-commit-config.yaml`, `.gitleaks.toml`) | Every commit, staged files | Stops a secret before it is committed. |
| TruffleHog in CI (`.github/workflows/ci.yml`, `scripts/ci/secret_scan_scope.py`) | Every PR and merge-queue run | The pushed range, verified mode, `--results=verified,unknown`. Required. |
| OPSEC linter (`scripts/audit/lint_opsec_leaks.py`) | CI Secret scan job | Infrastructure identifiers (addresses, key headers) that are not credentials. |
| This wrapper | On demand, as above | Offline; whole work tree or whole public history. |
