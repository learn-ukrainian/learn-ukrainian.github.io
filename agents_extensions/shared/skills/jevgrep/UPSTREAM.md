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
  `learn-ukrainian-jevgrep-update.timer`, resolves `latest` to an exact version
  and installs it only when the release has npm provenance attestations, has no
  `preinstall`/`install`/`postinstall` script, and declares `bin.jg`. It installs
  that exact version with `--ignore-scripts`, then requires `jg --version` to
  match and `jg doctor` to pass; otherwise it reinstalls the previous version.
- On every run it rewrites `~/.claude/skills/jevgrep/SKILL.md` and
  `~/.agents/skills/jevgrep/SKILL.md` as the tracked `SKILL.md` plus the
  installed package's upstream skill body, so agents read upstream text that
  matches the installed CLI. The overlay wins over the appended text.
- Each run appends one JSON line to
  `~/.local/state/learn-ukrainian/jevgrep-update.jsonl` (versions, action,
  result, sha256 of the upstream skill file).

## Host setup (operator only)

1. Authenticate once per host (agents never do this):
   `jg auth --provider typesafe --stdin < ~/.secrets/typesafe-ai.key`
2. Preview the updater from the primary checkout:
   `.venv/bin/python scripts/tools/jevgrep_update.py --dry-run --json`
3. Install and enable the timer as described in `packaging/systemd/README.md`
   § jevgrep auto-update.

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
