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

### Seminar research-only tracks (archived 2026-04-14, #1229)

Twelve tracks whose v5/v3 orchestration produced only research + discovery
metadata — no shipped lesson content anywhere in the repo. Going forward,
seminar modules are built by the **wiki-to-module pipeline** (#1136), which
reads the wiki article as its knowledge source instead of re-running the
legacy research phase. `folk` stayed live because it was the first
wiki-based build test and has real content.

| Dir | Modules orchestrated | Legacy pipeline |
|---|---|---|
| `bio/` | 180 | v5 |
| `istorio/` | 136 | v5 |
| `lit/` | 232 | v5 |
| `ruth/` | 115 | v5 |
| `oes/` | 102 | v5 |
| `lit-essay/` | 63 | v5 |
| `lit-youth/` | 32 | v5 |
| `lit-war/` | 30 | mixed v5/v3 |
| `lit-hist-fic/` | 23 | v5 |
| `lit-fantastika/` | 27 | v3 |
| `lit-humor/` | 14 | v3 |
| `lit-drama/` | 12 | v3 |

Plans for these tracks (`plans/{track}/*.yaml`) stay live in the top-level
`plans/` tree — they remain the curriculum source-of-truth. When the
wiki-to-module pipeline ships seminar builds, v6 will read those plans and
produce fresh `curriculum/l2-uk-en/{track}/` directories with real content.

The archived research artifacts may still be useful as priors / fact-checks
for the wiki compiler if a track is ever resurrected, which is why we
archive rather than delete.

## Restoration

To restore any directory to live status:
```bash
git mv curriculum/l2-uk-en/_archive/<dir> curriculum/l2-uk-en/<dir>
# Re-add the track to curriculum/l2-uk-en/curriculum.yaml if needed.
```
