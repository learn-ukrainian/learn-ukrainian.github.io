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
The tracked `SKILL.md` holds only our frontmatter, the Project Overlay and a
short Usage section.

Until the host auto-updater lands (#9146), the infra driver installs each new
release by hand. Agents never install or upgrade `jg` and never run `jg auth`.

## Host setup

1. **Operator only:** authenticate once per host (agents never do this):
   `jg auth --provider typesafe --stdin < ~/.secrets/typesafe-ai.key`
2. **Infra driver: install or bump to a new `latest`.**
   1. Resolve the exact version: `npm view @dzhng/jevgrep version`.
   2. Check provenance before installing:
      `npm view @dzhng/jevgrep@<version> dist.attestations` must print an
      attestation (npm provenance). Do not install a release without one.
   3. Install that exact version without lifecycle scripts:
      `npm install -g --ignore-scripts @dzhng/jevgrep@<version>`.
   4. Verify: `jg --version` prints `<version>` and `jg doctor` passes.
   5. Refresh the user-level skill copies: write the tracked
      `agents_extensions/shared/skills/jevgrep/SKILL.md`, followed by the body
      (text after the frontmatter) of the installed package's
      `dist/skills/jevgrep/SKILL.md`, to both
      `~/.claude/skills/jevgrep/SKILL.md` and `~/.agents/skills/jevgrep/SKILL.md`.
      The overlay wins over the appended upstream text.

If a release breaks, reinstall the previous exact version with the same
command.

## Host history

On 2026-09-28 the driver installed `@dzhng/jevgrep@0.4.4` (then `latest`) and
copied the upstream skill verbatim (sha256 `04d4d7b5…3e44`) to
`~/.claude/skills/jevgrep/` and `~/.agents/skills/jevgrep/`. The next bump
replaces those copies with overlay + upstream (step 2.5 above).
