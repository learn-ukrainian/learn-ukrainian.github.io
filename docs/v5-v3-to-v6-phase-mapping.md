# v5/v3 to v6 Phase Mapping

This document records the metadata-only migration used by
[`scripts/tools/migrate_legacy_state_to_v6.py`](../scripts/tools/migrate_legacy_state_to_v6.py).

The migration rewrites orchestration state files to the v6 schema only. It does
not touch lesson prose, plans, activities, vocabulary, research, or wiki files.

## Discovery Snapshot

Repository snapshot checked on `2026-04-14`:

- `936` legacy `state.json` files with `mode: "v5"`
- `564` legacy `state-v3.json` files total
- `54` standalone v3 directories with no `state.json`
- `510` directories that contain both `state.json` (`mode: "v5"`) and `state-v3.json`

Observed legacy phase names in the live corpus:

- v5: `research`, `discover`
- v3: `v3-A`

Historical legacy phase names still referenced in code/docs but not observed in
the live corpus scan:

- v5: `content`, `validate`, `activities`, `review`, `mdx`
- v3: `v3-B`, `v3-C`, `v3-audit`, `v3-D`, `v3-E`, `v3-F`

## v5 Mapping

| Legacy phase | v6 phase | Basis |
|---|---|---|
| `research` | `research` | Same responsibility in both pipelines. |
| `discover` | `research` | v5 explicitly merged discover into research; state notes already say `merged-into-research`. |
| `content` | `write` | v5 content generated the prose; v6 split planning from writing, and `write` is the durable equivalent. |
| `validate` | `verify` | v5 validate was the prose-only audit/screen/fix gate; `verify` is the closest v6 quality gate. |
| `activities` | `activities` | Same sidecar-generation phase in both pipelines. |
| `review` | `review` | Same adversarial review step in both pipelines. |
| `mdx` | `publish` | v5 MDX generation corresponds to the final v6 publish/render step. |

## v3 Mapping

The repo no longer carries the old v3 pipeline implementation, so these mappings
come from the surviving API/dashboard labels plus the live `phase-A-prompt.md`
artifacts that define Phase A as research.

| Legacy phase | v6 phase | Basis |
|---|---|---|
| `v3-A` | `research` | Historical dashboards labeled A as Research; live Phase A prompts are explicitly research + meta. |
| `v3-B` | `write` | Historical dashboards labeled B as Content. |
| `v3-C` | `activities` | Historical dashboards labeled C as Activities. |
| `v3-audit` | `verify` | v3 audit ran before review/repair/final, so it aligns better with the v6 verification gate than with terminal v6 audit. |
| `v3-D` | `review` | Historical dashboards labeled D as Review. |
| `v3-E` | `repair` | Historical dashboards labeled E as Repair. |
| `v3-F` | `publish` | Historical dashboards labeled F as Final; the closest surviving v6 terminal artifact phase is publish. |

## Ambiguities

No observed live phase names required `__preserved_as_legacy__`.

Migration fallback for any unseen custom legacy phase name:

| Legacy phase | v6 phase | Basis |
|---|---|---|
| any unrecognized name | `__preserved_as_legacy__` | The script warns and keeps the full original JSON under `legacy_state`, but does not invent a v6 phase. |

## Mixed Directories

When an orchestration directory contains both v5 and v3 state files:

- `migrated_from` is set to `v5`
- mapped v5 phases win conflicts over v3 phases
- the full v5 and v3 payloads are both preserved under `legacy_state`
- `state-v3.json` is backed up to `state-v3.json.pre-migration.bak` on `--apply`

This keeps the newer v5 state authoritative while still retaining the older v3
metadata for auditability.
