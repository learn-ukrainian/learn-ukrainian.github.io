# Recovery after a local checkout or data loss

This runbook formalizes the 2026-07-29 incident recovery order
([#6013](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6013),
primary checkout deleted by an unknown actor). It restores a fresh checkout and
its locally held data without overwriting an active repository, inventing
missing data, or reactivating stale agent state. It does not install an APFS
snapshot LaunchAgent; host-level snapshot and backup-rotation policy is an
operator decision tracked outside this runbook.

Related runbooks:

- [Data backup and recovery](data-backup.md) — restic snapshots of
  `batch_state/`, `.agent/`, `.claude/*-epic/`, and `data/`, with the restore
  drill used when a release asset is not the right recovery source.
- [launchd inventory](launchd-inventory.md) — the scheduled jobs to reinstall
  and verify after a full machine-local loss.
- [Worktree cleanup](worktree-cleanup.md) — reaper rescue refs for recovering
  a wrongly reaped dispatch worktree.

## Safety boundary

Stop writers for the affected databases before copying anything. Preserve the
damaged directory as evidence when space permits. Work from a new clone and a
new empty staging directory; never restore an archive directly over a live
checkout, its `data/` directory, the repository root, or a home directory.

The published `hramatka-data-releases` assets are the source for recoverable
database files. Select the asset and database names from the release manifest
or its checksums, not from memory. If an expected asset is absent or a checksum
does not match, stop: a partial release is not a substitute for the missing
database.

## 1. Recreate the checkout and Python environment

```bash
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git \
  /absolute/path/to/clean/learn-ukrainian
cd /absolute/path/to/clean/learn-ukrainian
git switch main
git pull --ff-only

PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.12.8
pyenv local 3.12.8
uv venv --python 3.12.8 .venv
.venv/bin/python -m pip install --upgrade pip
uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt
```

If `pyenv install` reports that 3.12.8 already exists, retain that interpreter;
do not substitute another Python version.

**`pip install -e .` does NOT work on this tree — do not use it.** `pyproject.toml`
declares no `[build-system]`/`[tool.setuptools]` table, so an editable install
falls back to setuptools flat-layout auto-discovery, which refuses to guess a
single top-level package when the repo root holds multiple top-level
directories (`scripts/`, `wiki/`, `docs/`, …) — the install fails outright.
`uv pip install -r requirements.txt` (a plain dependency install, not a
project install) is the working replacement — but it was NOT sufficient on
its own until #6830 closed a manifest-debt gap: `psutil`, `filelock`,
`rapidfuzz`, `lxml`, `pypdf`, `PyMuPDF`, and `ruamel.yaml` were previously
only pulled in transitively, so a from-scratch `requirements.txt`-only
install left `pytest --collect-only` unable to collect 17 test modules (see
`requirements.txt`).

### The `.pth` story

Neither `requirements.txt` nor an editable install puts this repo's own code
on `sys.path` — there is no `scripts` distribution to install. Two internal
import spellings are both live in the tree: `scripts.audit.foo` (repo root on
`sys.path`, what `tests/conftest.py` sets up for pytest) and bare `audit.foo`
(`scripts/` itself on `sys.path`, used by scripts invoked directly and by
tools that shell out to a script's own directory — see the dual-identity
note in `check_node_modules_integrity.py` and #6812). Outside pytest — a
direct venv `python -c "import ..."`, an MCP server subprocess, a cron job —
nothing sets either path up. A `.pth` file in site-packages is the standard
mechanism for adding paths to every interpreter start in a venv:

```bash
cat > .venv/lib/python3.12/site-packages/learn-ukrainian-paths.pth <<'EOF'
/absolute/path/to/clean/learn-ukrainian
/absolute/path/to/clean/learn-ukrainian/scripts
EOF
```

Use the venv's actual `python3.NN` directory name (`ls .venv/lib/`) and the
clone's real absolute path — a `.pth` is not portable across clones or Python
minor versions; regenerate it, don't copy it from another checkout. #6812
tracks retiring the bare `scripts/`-rooted identity, which will let this file
shrink to the repo-root line only.

Add any further project dependencies required by the checked-out revision
using its tracked installation instructions.

## 2. Restore data databases from the release

Download the chosen `hramatka-data-releases` release asset into an empty
directory outside the checkout. Verify its published checksum before unpacking.
Then inspect SQLite copies before selectively copying only the verified files
into the fresh checkout.

```bash
RELEASE_STAGE=/absolute/path/to/empty/hramatka-data-release-stage
PROJECT_DIR=/absolute/path/to/clean/learn-ukrainian

mkdir -p "$RELEASE_STAGE"
mkdir -p "$PROJECT_DIR/data"
# Download the exact reviewed release asset and checksum into $RELEASE_STAGE.
# Verify the checksum before unpacking; do not use rsync --delete.

sqlite3 "$RELEASE_STAGE/sources.db" 'PRAGMA quick_check;'
sqlite3 "$RELEASE_STAGE/vesum.db" 'PRAGMA quick_check;'
cp "$RELEASE_STAGE/sources.db" "$PROJECT_DIR/data/sources.db"
cp "$RELEASE_STAGE/vesum.db" "$PROJECT_DIR/data/vesum.db"
```

The two example names are the expected core databases, not a license to copy
an arbitrary asset set. Copy additional databases only when the selected
release manifest names them and each file passes its own integrity check.
Retain the stage until application checks pass.

## 3. Recreate deployed agent configuration

The tracked agent-extension sources regenerate local ignored deployment files:

```bash
cd /absolute/path/to/clean/learn-ukrainian
npm ci
npm run agents:deploy
```

Do not restore old `.agent/`, `.codex/`, lock, wake, cache, or session-state
directories wholesale. Deploy from the checked-out sources, then re-trust any
project hooks through the relevant local tool interface.

## 4. Restore Git identity and prove readiness

Set the identity deliberately for this clone; use the email address associated
with the account that will sign and push commits. Do not copy another person's
identity or any credential file.

```bash
git config user.name "Your name"
git config user.email "your-verified-email@example.invalid"
git config --get user.name
git config --get user.email
git status --short --branch
.venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Finally run the smallest relevant test or application health check for the
recovered component. Keep the release stage and the damaged copy until that
check passes; only then resume writers.

## 5. Restore services and scheduled jobs

Reinstall the project's LaunchAgents only from the merged primary checkout on
`main`; each plist persists absolute checkout paths, so never install from a
dispatch worktree. The [launchd inventory](launchd-inventory.md) lists every
job, its installer, and its log locations.

```bash
./services.sh status api
./services.sh supervise api install
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py install
.venv/bin/python scripts/orchestration/install_archived_thread_cleanup_launchd.py install \
  --repo-root "$PWD"
```

The backup job (`com.learn-ukrainian.backup`) is host-managed: its plist runs
the private wrapper `~/.local/bin/learn-ukrainian-backup`, which sources the
environment file under `~/.secrets/` before invoking
`scripts/backup-data.sh backup --execute`. Recreate that wrapper and
environment on the host and confirm them with
`./scripts/backup-data.sh doctor` per
[Data backup and recovery](data-backup.md); never commit the environment file
or wrapper.

After reinstalling, verify each service with its installer `status` command
and confirm the first receipts appear at the log and receipt paths listed in
the inventory.
