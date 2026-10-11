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
(
  set -euo pipefail
  git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git \
    /absolute/path/to/clean/learn-ukrainian
  cd /absolute/path/to/clean/learn-ukrainian || exit 1
  git switch main
  git pull --ff-only

  PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.12.14
  pyenv local 3.12.14
  uv venv --python 3.12.14 .venv
  .venv/bin/python -m pip install --upgrade pip
  uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt
)
```

If `pyenv install` reports that 3.12.14 already exists, retain that interpreter;
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
(
  set -euo pipefail
  cd /absolute/path/to/clean/learn-ukrainian || exit 1
  nvmrc="$(tr -d '[:space:]' < .nvmrc)"
  engines="$(node -p 'require("./package.json").engines.node')"
  node_version="$(node --version)"
  npm_version="$(npm --version)"
  node_bin="$(readlink -f -- "$(command -v node)")"
  npm_bin="$(readlink -f -- "$(command -v npm)")"
  node_prefix="$(dirname "$(dirname "$node_bin")")"
  case "$npm_bin/" in
    "$node_prefix"/*) ;;
    *)
      printf 'npm is not the npm that ships with this Node.\n' >&2
      exit 1
      ;;
  esac
  case "$node_version" in
    v"$nvmrc"|v"$nvmrc".*) ;;
    *)
      printf 'Node %s does not match .nvmrc (%s).\n' "$node_version" "$nvmrc" >&2
      exit 1
      ;;
  esac
  case "$engines" in
    *.x)
      major="${engines%.x}"
      case "$node_version" in
        v"$major".*) ;;
        *)
          printf 'Node %s does not satisfy engines.node (%s).\n' \
            "$node_version" "$engines" >&2
          exit 1
          ;;
      esac
      ;;
    *)
      printf 'Unsupported engines.node range (%s).\n' "$engines" >&2
      exit 1
      ;;
  esac
  printf 'nvmrc=%s engines=%s node=%s npm=%s\n' \
    "$nvmrc" "$engines" "$node_version" "$npm_version"
  npm ci
  npm run agents:deploy
)
```

Do not restore old `.agent/`, `.codex/`, lock, wake, cache, or session-state
directories wholesale. Deploy from the checked-out sources, then re-trust any
project hooks through the relevant local tool interface.

## 4. Restore Git identity and prove readiness

Set the identity deliberately for this clone; use the email address associated
with the account that will sign and push commits. Do not copy another person's
identity or any credential file.

```bash
(
  set -euo pipefail
  cd /absolute/path/to/clean/learn-ukrainian || exit 1
  git config user.name "Your name"
  git config user.email "your-verified-email@example.invalid"
  git config --get user.name
  git config --get user.email
  git status --short --branch
  .venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"
)
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

## Restoring the shared node_modules

Use this when the primary checkout is still present and its shared
`node_modules` install was emptied. Dispatch worktrees symlink that directory,
so every command below runs in the primary checkout only. Never run them from
a dispatch worktree.

`.nvmrc` pins Node 22 and `package.json` `engines.node` is `22.x`. The block
exits unless `node` matches `.nvmrc` and satisfies `engines.node`, and unless
`npm` resolves inside that Node's prefix (the npm that ships with it). A
failed `cd` exits before `npm ci`.

```bash
(
  set -euo pipefail
  cd /absolute/path/to/primary/learn-ukrainian || exit 1
  nvmrc="$(tr -d '[:space:]' < .nvmrc)"
  engines="$(node -p 'require("./package.json").engines.node')"
  node_version="$(node --version)"
  npm_version="$(npm --version)"
  node_bin="$(readlink -f -- "$(command -v node)")"
  npm_bin="$(readlink -f -- "$(command -v npm)")"
  node_prefix="$(dirname "$(dirname "$node_bin")")"
  case "$npm_bin/" in
    "$node_prefix"/*) ;;
    *)
      printf 'npm is not the npm that ships with this Node.\n' >&2
      exit 1
      ;;
  esac
  case "$node_version" in
    v"$nvmrc"|v"$nvmrc".*) ;;
    *)
      printf 'Node %s does not match .nvmrc (%s).\n' "$node_version" "$nvmrc" >&2
      exit 1
      ;;
  esac
  case "$engines" in
    *.x)
      major="${engines%.x}"
      case "$node_version" in
        v"$major".*) ;;
        *)
          printf 'Node %s does not satisfy engines.node (%s).\n' \
            "$node_version" "$engines" >&2
          exit 1
          ;;
      esac
      ;;
    *)
      printf 'Unsupported engines.node range (%s).\n' "$engines" >&2
      exit 1
      ;;
  esac
  printf 'nvmrc=%s engines=%s node=%s npm=%s\n' \
    "$nvmrc" "$engines" "$node_version" "$npm_version"
  npm ci
)
```

`npm ci` removes `node_modules` before it reinstalls. A failed run leaves the
directory nearly empty. Retry that block until `npm ci` exits 0. Do not leave
a partial install in place.

Puppeteer's postinstall fails when the per-browser installation directory
already exists and the executable inside it is missing. The message names
that directory and the executable, for example a folder
`<cache>/chrome/linux-<buildId>` whose executable
`<cache>/chrome/linux-<buildId>/chrome-linux64/chrome` is absent. That folder
is not the cache root. The cache root stays non-empty while the installation
directory exists, so removing an empty cache root does not clear the failure.

Set `install_dir` and `executable` to the two paths from the message. The
default cache is `$HOME/.cache/puppeteer` unless `PUPPETEER_CACHE_DIR` is set.
Repeating `npm ci` alone does not clear a directory that is already there.

The block resolves the cache and the installation directory with a sentinel
after `readlink -f`, then removes that sentinel, so a trailing newline stays
part of the path. It refuses unless that directory is a real directory
(not a symlink), resolves strictly inside the cache, is not the cache itself,
and the named executable is inside it and absent. An empty directory is
removed with `rmdir`. A directory that still has entries is renamed, contents
unchanged, to a new sibling under the same cache:
`<name>.quarantine.<utc-stamp>.<pid>.<random>`. The block never uses `rm -rf`.
A failed check exits before `rmdir` or `mv`. A failed `cd` exits before either
command and before `npm ci`.

A scratch cache showed that behavior: `rmdir` removes an empty
`chrome/linux-<buildId>` directory and leaves the cache root; a directory
that still contains `chrome-linux64/` is moved aside and its files stay in
the quarantine sibling; the cache root and a directory outside the cache are
left in place. Selecting a missing primary directory exits before `npm ci`.

```bash
(
  set -euo pipefail
  cd /absolute/path/to/primary/learn-ukrainian || exit 1
  nvmrc="$(tr -d '[:space:]' < .nvmrc)"
  engines="$(node -p 'require("./package.json").engines.node')"
  node_version="$(node --version)"
  npm_version="$(npm --version)"
  node_bin="$(readlink -f -- "$(command -v node)")"
  npm_bin="$(readlink -f -- "$(command -v npm)")"
  node_prefix="$(dirname "$(dirname "$node_bin")")"
  case "$npm_bin/" in
    "$node_prefix"/*) ;;
    *)
      printf 'npm is not the npm that ships with this Node.\n' >&2
      exit 1
      ;;
  esac
  case "$node_version" in
    v"$nvmrc"|v"$nvmrc".*) ;;
    *)
      printf 'Node %s does not match .nvmrc (%s).\n' "$node_version" "$nvmrc" >&2
      exit 1
      ;;
  esac
  case "$engines" in
    *.x)
      major="${engines%.x}"
      case "$node_version" in
        v"$major".*) ;;
        *)
          printf 'Node %s does not satisfy engines.node (%s).\n' \
            "$node_version" "$engines" >&2
          exit 1
          ;;
      esac
      ;;
    *)
      printf 'Unsupported engines.node range (%s).\n' "$engines" >&2
      exit 1
      ;;
  esac
  printf 'nvmrc=%s engines=%s node=%s npm=%s\n' \
    "$nvmrc" "$engines" "$node_version" "$npm_version"
  cache="${PUPPETEER_CACHE_DIR:-$HOME/.cache/puppeteer}"
  install_dir="<browser folder from the puppeteer error>"
  executable="<executable path from the puppeteer error>"
  # $(...) strips every trailing newline. A sentinel keeps one that belongs to the path.
  _capture_canonical() {
    local captured
    if ! captured=$(readlink -f -- "$2" 2>/dev/null && printf x); then
      return 1
    fi
    captured=${captured%x}
    captured=${captured%$'\n'}
    printf -v "$1" '%s' "$captured"
  }
  if ! _capture_canonical cache_real "$cache"; then
    printf 'Refusing to remove a browser folder whose cache does not resolve.\n' >&2
    exit 1
  fi
  if ! _capture_canonical install_real "$install_dir"; then
    printf 'Refusing to remove a browser folder that does not resolve.\n' >&2
    exit 1
  fi
  if [ -z "$cache_real" ] || [ -z "$install_real" ]; then
    printf 'Refusing to remove a browser folder whose path is empty.\n' >&2
    exit 1
  fi
  if [ "$install_real" = "$cache_real" ]; then
    printf 'Refusing to remove the browser cache root.\n' >&2
    exit 1
  fi
  case "$install_real/" in
    "$cache_real"/*) ;;
    *)
      printf 'Refusing to remove a browser folder outside the cache.\n' >&2
      exit 1
      ;;
  esac
  case "$executable" in
    "$install_dir"/*) ;;
    *)
      printf 'Refusing to remove a browser folder whose executable is outside it.\n' >&2
      exit 1
      ;;
  esac
  if [ -e "$executable" ] || [ -L "$executable" ]; then
    printf 'Refusing to remove a browser folder that still has its executable.\n' >&2
    exit 1
  fi
  if [ -L "$install_dir" ] || [ ! -d "$install_dir" ] || [ -L "$install_real" ] || [ ! -d "$install_real" ]; then
    printf 'Refusing to remove a browser folder that is not a directory.\n' >&2
    exit 1
  fi
  if ! named_id=$(stat -c '%d:%i' -- "$install_dir" && printf x); then
    printf 'Refusing to remove a browser folder that cannot be identified.\n' >&2
    exit 1
  fi
  named_id=${named_id%x}
  named_id=${named_id%$'\n'}
  if ! real_id=$(stat -c '%d:%i' -- "$install_real" && printf x); then
    printf 'Refusing to remove a browser folder that cannot be identified.\n' >&2
    exit 1
  fi
  real_id=${real_id%x}
  real_id=${real_id%$'\n'}
  if [ "$named_id" != "$real_id" ]; then
    printf 'Refusing to remove a browser folder that does not match its resolved path.\n' >&2
    exit 1
  fi
  if ! listed=$(find "$install_real" -mindepth 1 -print -quit && printf x); then
    printf 'Refusing to remove a browser folder that cannot be listed.\n' >&2
    exit 1
  fi
  listed=${listed%x}
  if [ -z "$listed" ]; then
    rmdir -- "$install_real"
  else
    install_parent="${install_real%/*}"
    install_base="${install_real##*/}"
    if [ -z "$install_parent" ] || [ -z "$install_base" ] || [ "$install_base" = "." ] || [ "$install_base" = ".." ]; then
      printf 'Refusing to quarantine an unsafe browser folder name.\n' >&2
      exit 1
    fi
    if ! stamp=$(date -u +%Y%m%dT%H%M%SZ && printf x); then
      printf 'Refusing to quarantine without a unique name.\n' >&2
      exit 1
    fi
    stamp=${stamp%x}
    stamp=${stamp%$'\n'}
    if [ -z "$stamp" ]; then
      printf 'Refusing to quarantine without a unique name.\n' >&2
      exit 1
    fi
    quarantine="${install_parent}/${install_base}.quarantine.${stamp}.$$.$RANDOM"
    case "$quarantine/" in
      "$cache_real"/*) ;;
      *)
        printf 'Refusing to quarantine outside the cache.\n' >&2
        exit 1
        ;;
    esac
    if [ "$quarantine" = "$cache_real" ] || [ "$quarantine" = "$install_real" ]; then
      printf 'Refusing to quarantine onto the cache or the browser folder.\n' >&2
      exit 1
    fi
    if [ -e "$quarantine" ] || [ -L "$quarantine" ]; then
      printf 'Refusing to quarantine over an existing path.\n' >&2
      exit 1
    fi
    mv -T -- "$install_real" "$quarantine"
  fi
  npm ci
)
```

Confirm the restored install:

```bash
.venv/bin/python scripts/audit/check_node_modules_integrity.py
```
