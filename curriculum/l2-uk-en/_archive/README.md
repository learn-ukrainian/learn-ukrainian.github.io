# L2-UK-EN Archive

Directories that are no longer part of the live curriculum but are kept for
historical reference. Nothing in here is built, shipped, or read by the
live pipeline.

## Contents

### `lit-crimea/` (archived 2026-04-14, #1228)

Early literary sub-track that was merged into other `lit-*` tracks. Holds 5
`orchestration/` skeletons and 12 `discovery/` research artifacts. No
content `.md` files — the track never shipped modules. Not referenced in
`curriculum/l2-uk-en/curriculum.yaml`.

### `lit-doc/` (archived 2026-04-14, #1228)

Orphaned literary sub-track. Holds 9 `orchestration/` skeletons and 13
`discovery/` research artifacts. No content `.md` files — never shipped.
Not referenced in the curriculum manifest.

### `a1-backup-2026-04-08/` (archived 2026-04-14, #1228)

Full A1 snapshot taken as a recovery point after the 2026-04-08 batch
deletion incident (`--step all --resume` destroyed orchestration + content
for a2-bridge and 40+ other files; see `memory/MEMORY.md` "BATCH COMMANDS"
entry). A1 on `main` is now healthy at 54/55 modules on v6, so the backup
has served its purpose. Kept here for one release cycle as insurance.

## Restoration

To restore any directory to live status:
```bash
git mv curriculum/l2-uk-en/_archive/<dir> curriculum/l2-uk-en/<dir>
# Re-add the track to curriculum/l2-uk-en/curriculum.yaml if needed.
```
