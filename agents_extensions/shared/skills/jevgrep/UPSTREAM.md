# Upstream provenance — jevgrep skill

| Field | Value |
| --- | --- |
| Source | https://github.com/dzhng/jevgrep |
| npm package | `@dzhng/jevgrep` (bin `jg`), https://www.npmjs.com/package/@dzhng/jevgrep |
| Upstream skill | `dist/skills/jevgrep/SKILL.md` inside the installed package |
| License | MIT |
| Adopted | 2026-09-28 (#9134) |

## Version policy: track npm `latest`

Operator decision 2026-09-28: track npm `latest`, because jevgrep is in rapid
development. There is no exact pin and no vendored upstream body in this repo.

- The tracked `SKILL.md` holds only our frontmatter, the Project Overlay and a
  short Usage section.
- `scripts/tools/jevgrep_update.py`, run every 6 hours by
  `learn-ukrainian-jevgrep-update.timer`, holds an exclusive lock on
  `~/.local/state/learn-ukrainian/jevgrep-update.lock` for the whole run. A run
  that finds the lock held reports `action: locked`, changes nothing and exits 0.
- It reads `https://registry.npmjs.org/` and resolves `latest` to an exact
  version. It installs that version only when the release has npm provenance
  attestations, has no `preinstall`/`install`/`postinstall` script, declares
  `bin.jg`, declares only plain semver ranges in `dependencies`,
  `optionalDependencies` and `peerDependencies` (npm installs URL, git, host
  shorthand, `file:`, `link:` and `npm:` alias specs from wherever they point,
  whatever `--registry` says), bundles nothing, and names a `registry.npmjs.org`
  tarball with a sha512 `dist.integrity`. A dependency violation is labelled
  `dependency_source_refused`. Metadata and tarball requests follow no redirects, must end
  on `registry.npmjs.org` over HTTPS, and are capped at 8 MiB and 64 MiB.
- It checks the tarball against `dist.integrity` and installs the local file
  with `--ignore-scripts --no-package-lock --registry=https://registry.npmjs.org/`
  into its own prefix under `~/.local/share/learn-ukrainian/jevgrep/`. npm runs
  without any inherited `npm_config_*` variable, and its user and global config
  files are an empty temp file, so no host setting (scoped registries included)
  can route a dependency elsewhere. Before anything staged runs, every package
  in the prefix except jevgrep itself (installed from the verified tarball) must
  appear in the staged `node_modules/.package-lock.json` with a `resolved` URL
  under `https://registry.npmjs.org/` and an `integrity`; otherwise the prefix is
  deleted with `dependency_source_refused`. npm 7+ writes that hidden lockfile on
  every non-global install (`--no-package-lock` only stops `package-lock.json`)
  and no longer writes `_resolved` into installed `package.json` files.
  The staged `jg --version` must match and the
  staged `jg doctor` must pass. The staged package's upstream skill file must
  also exist. Only then does it switch the `~/.local/bin/jg` symlink atomically.
  If the switched `jg` fails its checks or a skill write fails, the previous
  link and skill files come back without a download, and `jg --version` and
  `jg doctor` are checked again. After a switch, pruning re-reads the link and
  keeps the active and previous prefixes. The first run treats the older
  `npm -g` install in `~/.local/lib/node_modules/@dzhng/jevgrep` as the previous
  version and leaves it in place.
- Every run except `--dry-run` first rewrites `~/.claude/skills/jevgrep/SKILL.md`
  and `~/.agents/skills/jevgrep/SKILL.md` from the package that `~/.local/bin/jg`
  resolves to: the tracked `SKILL.md` plus that package's upstream skill body.
  The overlay wins over the appended text. A successful update then writes the
  new version's text.
- **Residual:** if a skill write fails and restoring the old text also fails,
  the run exits 1 with `skill_restore_failed`, and one skill copy can describe a
  different version from the active CLI. The next run heals this with its first
  step, so the mismatch lasts at most one timer interval (6 hours) unless the
  driver runs the updater by hand sooner.
- Each run appends one JSON line to
  `~/.local/state/learn-ukrainian/jevgrep-update.jsonl` (versions, action,
  result, child exit codes, fixed failure classifications, sha256 of the
  upstream skill file). Output from npm and `jg` is never recorded.

## Host setup

1. **Operator only:** authenticate once per host (agents never do this):
   `jg auth --provider typesafe --stdin < ~/.secrets/typesafe-ai.key`
2. **Driver host maintenance (no approval gate):** preview the updater from the
   primary checkout with
   `.venv/bin/python scripts/tools/jevgrep_update.py --dry-run --json`, then
   install and enable the reviewed user unit as described in
   `packaging/systemd/README.md` § jevgrep auto-update.

## Holding a version

If a release breaks, pin temporarily by setting `JEVGREP_HOLD_VERSION=<x.y.z>`
in the service environment (`systemctl --user edit
learn-ukrainian-jevgrep-update.service`, add `Environment=JEVGREP_HOLD_VERSION=0.4.4`
under `[Service]`), then run the service once. The updater installs that exact
version under the same guards. Remove the override to return to `latest`.

## Host history

On 2026-09-28 the driver installed `@dzhng/jevgrep@0.4.4` (then `latest`) and
copied the upstream skill verbatim (sha256 `04d4d7b5…3e44`) to
`~/.claude/skills/jevgrep/` and `~/.agents/skills/jevgrep/`. The updater's
first run replaces those copies with overlay + upstream.
