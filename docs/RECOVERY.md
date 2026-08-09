# Recovery after a local checkout or data loss

This runbook records the 2026-07-29 recovery order. It restores a fresh
checkout and its locally held data without overwriting an active repository,
inventing missing data, or reactivating stale agent state. It does not install
an APFS snapshot LaunchAgent.

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
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
```

If `pyenv install` reports that 3.12.8 already exists, retain that interpreter;
do not substitute another Python version. Add any project dependencies required
by the checked-out revision using its tracked installation instructions.

## 2. Restore data databases from the release

Download the chosen `hramatka-data-releases` release asset into an empty
directory outside the checkout. Verify its published checksum before unpacking.
Then inspect SQLite copies before selectively copying only the verified files
into the fresh checkout.

```bash
RELEASE_STAGE=/absolute/path/to/empty/hramatka-data-release-stage
PROJECT_DIR=/absolute/path/to/clean/learn-ukrainian

mkdir -p "$RELEASE_STAGE"
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
