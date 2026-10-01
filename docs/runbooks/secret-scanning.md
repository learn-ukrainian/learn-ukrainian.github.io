# Secret scanning (local TruffleHog)

TruffleHog is installed locally and is on every agent's `PATH` as
`trufflehog`. CI already scans every pushed range (see
[`ci-gate.md`](ci-gate.md)); this runbook covers the local scan an agent runs
itself, through one wrapper that keeps it offline and prints nothing taken from a
finding. Issue #9416.

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
.venv/bin/python scripts/audit/secret_scan_local.py --help
```

From a dispatch worktree, use the primary checkout's interpreter (see
[`worktree-cleanup.md`](worktree-cleanup.md) § Shared Python environment).

| Mode | Scans | How |
| --- | --- | --- |
| `tree` | Tracked and untracked-not-ignored files of the work tree | `trufflehog filesystem` over that file list (batched). Never `.git`, `.venv`, `node_modules`, `.worktrees` or database files under `data/`; symlinks and files beneath a symlinked directory are skipped. |
| `history` | Every commit on every ref of the configured public remote (default `origin`) | Clones a full bare mirror into a new temporary directory under the system temp directory, scans it with `trufflehog git file://<mirror> --bare`, then removes the directory. A failed removal is exit 2. |
| `show-keys REPORT` | An existing report | Prints only the report's top-level key names and the count of findings per detector. Runs nothing. |

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
  files in a new owner-only (0700) `secret-scan-*` directory under the system
  temp directory (`TMPDIR`, else `/tmp`). There is no option to choose another
  location. The run is refused before anything is written when the system temp
  directory is inside the repository or its primary checkout.
- The console never shows anything taken from a finding: no path, commit, line
  or value. It shows the report's generated file name, the number of files
  scanned (`tree`), the total, and a count per detector. Detector names come
  from TruffleHog's own detector list compiled into the wrapper; any other name
  is counted as `other`. Every error is a fixed message.
- Never paste the report, the log, any field of a finding or a screenshot of
  them into a PR, issue, comment, commit, chat or transcript. Public text
  quotes only counts and outcomes.
- Delete the report directory when triage is finished.

Exit codes: `0` no findings (`show-keys`: report summarized), `1` findings,
`2` refusal, missing binary, git or TruffleHog error, timeout, unexpected report
structure, or mirror removal failure. A missing binary prints a typed message
pointing here.

## Triage

Triage reads the report with your own tools, and only commands that print key
names or counts. Never print `Raw`, `RawV2`, `Redacted`, `ExtraData`,
`SecretParts` or a location field: an agent's console is a transcript.

1. Locate the report without printing its directory, and see its shape:

   ```bash
   REPORT=$(find "${TMPDIR:-/tmp}" -maxdepth 2 -name 'secret-scan-tree-0123456789abcdef.jsonl')
   .venv/bin/python scripts/audit/secret_scan_local.py show-keys "$REPORT"
   jq -c '.SourceMetadata.Data | map_values(keys)' "$REPORT" | sort -u   # location key names
   ```

2. Test false-positive hypotheses by counting. Each command prints one number
   (use `.SourceMetadata.Data.Git.file` for `history`):

   ```bash
   # Findings in one file you suspect (a lockfile, a test fixture):
   jq -n --arg f uv.lock '[inputs | select(.SourceMetadata.Data.Filesystem.file == $f)] | length' "$REPORT"
   # Findings outside the paths you believe are noise; 0 settles the hypothesis:
   jq -n '[inputs | select(.SourceMetadata.Data.Filesystem.file
       | test("^(tests/fixtures/|uv\\.lock$)") | not)] | length' "$REPORT"
   # Findings of one detector:
   jq -n '[inputs | select(.DetectorName == "PrivateKey")] | length' "$REPORT"
   ```

3. False positive in a file that should never be scanned (lockfiles, generated
   hashes): propose a `.trufflehogignore` entry in a reviewed PR. For a single
   line, an inline `trufflehog:ignore` comment is the narrower fix. Never widen
   the exclusions to silence a real credential.
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
| TruffleHog in CI (`.github/workflows/ci.yml`, `scripts/ci/secret_scan_scope.py`) | Every PR and merge-queue run | The pushed range, verified mode, `--results=verified,unknown`. Required. |
| OPSEC linter (`scripts/audit/lint_opsec_leaks.py`) | CI Secret scan job | Infrastructure identifiers (addresses, key headers) that are not credentials. |
| This wrapper | On demand, as above | Offline; whole work tree or whole public history. |
