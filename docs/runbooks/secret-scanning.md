# Secret scanning (local TruffleHog)

TruffleHog is installed locally and is on every agent's `PATH` as
`trufflehog`. CI already scans every pushed range (see
[`ci-gate.md`](ci-gate.md)); this runbook covers the local scan an agent runs
itself, through one wrapper that keeps it offline. Scans and summary commands
print closed-set names and counts. `locate` is the explicit private-console
exception for validated current-tree locations. Issue #9416.

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
.venv/bin/python scripts/audit/secret_scan_local.py show-keys "$REPORT"
.venv/bin/python scripts/audit/secret_scan_local.py count "$REPORT" --path uv.lock --path tests/fixtures/
.venv/bin/python scripts/audit/secret_scan_local.py --repo "$REPO" locate "$REPORT"
.venv/bin/python scripts/audit/secret_scan_local.py --help
```

From a dispatch worktree, use the primary checkout's interpreter (see
[`worktree-cleanup.md`](worktree-cleanup.md) § Shared Python environment).

| Mode | Scans | How |
| --- | --- | --- |
| `tree` | Tracked and untracked-not-ignored files of the work tree | `trufflehog filesystem` over that file list (batched). Never `.git`, `.venv`, `node_modules`, `.worktrees` or database files under `data/`; symlinks and files beneath a symlinked directory are skipped. |
| `history` | Every commit on every ref of the configured public remote (default `origin`) | Clones a full bare mirror into a new temporary directory under the temp directory, scans it with `trufflehog git file://<mirror> --bare`, then removes the directory, also on SIGINT, SIGTERM or SIGHUP. A failed removal is exit 2. |
| `show-keys REPORT` | An existing report | Prints only the report's top-level key names and the count of findings per detector. Runs nothing. |
| `count REPORT [--path P]... [--detector NAME]` | An existing report | Prints only how many findings (of one detector, if given) lie in the given paths, outside them, and without a file location. A path ending in `/` is a directory. The paths and the name are never printed. Runs nothing. |
| `locate REPORT --repo REPO` | An existing tree report and an explicit repository boundary | Private console only. Validates the entire report before printing `path<TAB>line<TAB>detector` on stdout. Prints fixed summary counts on stderr. Uses the current tree, never commit lookup or history objects. Runs no scanner. |

Why a mirror: agent checkouts are blobless partial clones. `trufflehog git`
cannot fetch the missing objects from a partial clone, and a `file://` URL to a
bare repository only works with `--bare`. The mirror clone is the full public
history, so it needs disk room for a complete clone; point `TMPDIR` at a
directory on a larger disk (outside the repository) if needed. Only a plain
`https://` remote without credentials is mirrored; git may use no other
transport, and the clone runs with no credential helper and no terminal prompt.

## Threat model

The operator's agents run the wrapper as the operator's own user. Hostile data
comes from the scanned content, the fields of each finding, the configured
remote and the command-line options. Other processes of the same user racing to
move directories, hardlink files or bind-mount are out of scope: they could
write the files directly.

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
  `RawV2`, `Redacted`, `ExtraData` and others). The wrapper writes it, and
  TruffleHog's own log beside it as `<report>.log`, as new owner-only (0600)
  files in a new owner-only (0700) `secret-scan-*` directory under the temp
  directory: the first set of `TMPDIR`, `TEMP` and `TMP`, else `/tmp`, with
  symlinks resolved. The modes are set explicitly, whatever the umask. There is
  no option to choose another location. The temp directory is decided from the
  path alone, so the run is refused before anything at all is written when it is
  inside the repository or its primary checkout.
- Scans and summary commands never show finding paths, commits, lines or
  values. They show the report's generated file name, the number of files
  scanned (`tree`), the total, and a count per detector. Detector names come
  from TruffleHog's own detector list compiled into the wrapper; any other name
  is counted as `other`. Every error is a fixed message.
- `locate` is the one explicit private-console location exception. It requires
  `--repo`, before or after `locate`, with no default. Set `REPO` to the tree
  that produced the report. Each output path must exactly match a canonical
  `tree_candidates` member of that tree. Paths are never normalized into a
  match. Absolute paths, traversal, symlinks, tabs, controls, format and bidi
  characters, and multiline injection are refused. Lines must be integers,
  excluding booleans, between 1 and the current file's line count. Detector
  names use the same closed set, with unknown strings mapped to `other`.
  Only `Filesystem` sources are supported. Every `Git` record is a counted
  history refusal, without reading commits. Other sources are counted source
  refusals. Duplicate JSON keys and ambiguous sources are malformed reports.
- For structurally valid reports, `locate` prints `findings`, `located`,
  `refused history`, `refused source`, `refused path`, and `refused line` counts
  on stderr. Located plus the refusal counts equals the `show-keys` total.
  A refusal withholds **all** location stdout and ends with
  `location view refused; no locations emitted`. Here `located` counts valid
  locations withheld from output too. Malformed or unreadable reports produce
  a fixed diagnostic without claiming a complete summary. Success ends with
  `location view complete`, meaning every finding has a validated location,
  not that a candidate is a credential, a false positive, or remediated.
- Never paste the report, the log, any field of a finding or a screenshot of
  them into a PR, issue, comment, commit, chat or transcript. Public text
  quotes only counts and outcomes.
- Delete the report directory when triage is finished.

Exit codes: `0` no findings (`show-keys`, `count`: report summarized;
`locate`: every finding located, including an empty report), `1`
findings, `2` refusal, missing binary, git or TruffleHog error, timeout,
unexpected report structure, any `locate` refusal, or mirror removal failure, `129`/`143` terminated
by SIGHUP/SIGTERM (any temporary mirror is removed first). A missing binary
prints a typed message pointing here.

## Triage

Agents read a report **only** through the wrapper's `show-keys`, `count` and
`locate` subcommands. `show-keys` and `count` print fixed text, closed-set names
and integers. `locate` adds only the private-console location exception above.
It does not authorize ad-hoc source-line or raw-report reads. Never run
`jq`, `cat`, `grep`, `head`, `less`, a Python one-liner or any other ad-hoc
command over a report or its log: a finding can carry a secret in any field,
including a key name or a field of an unexpected type, and an agent's console is
a transcript. If a triage question needs a view these subcommands lack, add a
closed-output subcommand to the wrapper, with tests, in a reviewed PR.

1. Locate the report without printing its directory, and see its shape:

   ```bash
   REPORT=$(find "${TMPDIR:-/tmp}" -maxdepth 2 -name 'secret-scan-tree-0123456789abcdef.jsonl')
   .venv/bin/python scripts/audit/secret_scan_local.py show-keys "$REPORT"
   ```

2. Test false-positive hypotheses by counting. Paths are repository-relative, as
   scanned (`tree`) or as committed (`history`); a path ending in `/` covers a
   directory:

   ```bash
   .venv/bin/python scripts/audit/secret_scan_local.py count "$REPORT" --path uv.lock
   .venv/bin/python scripts/audit/secret_scan_local.py count "$REPORT" --path tests/fixtures/ --path uv.lock
   .venv/bin/python scripts/audit/secret_scan_local.py count "$REPORT" --path tests/fixtures/ --detector PrivateKey
   ```

   "outside the given paths: 0" and "without a file location: 0" settle the
   hypothesis that every finding (of that detector) is in paths you believe are
   noise.

3. False positive in a file that should never be scanned (lockfiles, generated
   hashes): propose a `.trufflehogignore` entry in a reviewed PR. For a single
   line, an inline `trufflehog:ignore` comment is the narrower fix. Never widen
   the exclusions to silence a real credential.
   If counts do not identify the current-tree locations needed for triage,
   use the explicit private-console view:

   ```bash
   .venv/bin/python scripts/audit/secret_scan_local.py --repo "$REPO" locate "$REPORT"
   ```

   Expect only tab-separated path, line and detector fields on stdout. A
   refusal exits 2 with no location stdout. Return the fixed counts and refusal
   class for a reviewed correction. There is no ad-hoc reader fallback.
4. Anything the counts do not settle is a possible real credential: stop. Do
   not try it, do not verify it, do not remove it in a quick commit (history
   keeps it). Tell the operator through the private channel that a report needs
   inspection and where it is on the host; the operator opens it with their own
   tools and decides on rotation or revocation. Agents never rotate, revoke or
   rewrite history.
5. Public issue text records only the count and the outcome ("N candidates, all
   false positives" or "handed to the operator"), never the value, its location
   or where a credential is used.

## Relation to the other secret gates

| Gate | When | Scope |
| --- | --- | --- |
| gitleaks (`.pre-commit-config.yaml`, `.gitleaks.toml`) | Every commit, staged files | Stops a secret before it is committed. |
| TruffleHog in CI (`.github/workflows/ci.yml`, `scripts/ci/secret_scan_scope.py`) | Every PR, merge-queue and scheduled run | The event's range. The nightly schedule is an ancestry window, not a commit-date window (below). Verified mode, `--results=verified,unknown`. Required. |
| OPSEC linter (`scripts/audit/lint_opsec_leaks.py`) | CI Secret scan job | Infrastructure identifiers (addresses, key headers) that are not credentials. |
| This wrapper | On demand, as above | Offline; whole work tree or whole public history. |

The nightly schedule scans `base..HEAD` for a fixed first-parent depth
(`SCHEDULE_FIRST_PARENT_STEPS` in `scripts/ci/secret_scan_scope.py`, 400 as of
the 2026-10-16 measurement). That range includes every commit reachable from
HEAD and not from the base, merges and side branches included, with no commit
date involved. 400 is more than twice the measured peak of 156 first-parent
commits in any 48 hours (`git rev-list --count --first-parent --since=...` was
73 for the 48 hours ending 2026-10-16 18:05 UTC). History shorter than 400
steps scans the whole branch, including the root. A git failure fails the job
instead of narrowing the window.

After a successful scheduled scan or explicit default-branch full-history
audit, CI uploads the scanned head outside Git history as the 90-day artifact
`secret-scan-covered-head-v1`. The next schedule reads GitHub artifact
metadata for the latest eligible default-branch CI run. It uses that run's
immutable head SHA, without downloading or extracting any archive. Artifacts
from PRs, forks, other branches and other workflows are ignored. The lookup
checks at most the latest 100 matching artifacts and fails if no eligible
record remains. If that head predates the normal window, the scan widens to `last-scanned-head..HEAD`. A failed, cancelled
or timed-out scan never advances the record. Concurrent runs can read
an older record and repeat work safely; a record ahead of the checkout
fails visibly. PR, queue and bounded manual scans never advance coverage.

Missing, expired, corrupt, shallow or unrelated coverage fails the scheduled
job visibly. To initialize coverage, or recover after such a failure, run
CI on the default branch with `secret_scan_mode=full-history-audit`.
Only a successful audit establishes coverage; findings must be resolved
before retrying. The audit has a 60-minute budget. The normal scheduled
and bounded manual budgets stay at five minutes; a recovery timeout keeps
the previous record, so an explicit audit can recover the missed range.

Manual dispatch defaults to `bounded`: a branch scans from its merge-base
with the default branch to the dispatched SHA; a default-branch or already
merged head scans the ancestry window at that SHA. Resolution errors fail.
Only the exact `full-history-audit` input selects full history, including
the root. An audit on another branch does not establish scheduled coverage.

The action SHA pins the workflow script only. Both TruffleHog steps set the
action input `version` to one exact release (`3.99.0` as of #10056). Omitting
it pulls `:latest`. Bump both steps together to the newest
`trufflesecurity/trufflehog` release, never to an older tag to clear a finding,
then re-run `scripts/audit/secret_scan_local.py tree`.
`tests/ci/test_trufflehog_scanner_pin.py` rejects a missing pin and `latest`.
