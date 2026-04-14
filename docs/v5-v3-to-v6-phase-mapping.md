# v5/v3 to v6 Phase Mapping

> **STATUS — SHELVED (2026-04-14).** This migration was superseded by
> the "archive research-only seminar tracks" decision (#1229 closed).
> Every track the migration would have touched had zero shipped
> `.md` lesson content, so the metadata port was busywork; the tracks
> were moved to `curriculum/l2-uk-en/_archive/` instead.
>
> The script is kept for potential future one-off use. Before running
> `--apply`, the two Gemini conditions below must be addressed.

This document records the metadata-only migration used by
[`scripts/tools/migrate_legacy_state_to_v6.py`](../scripts/tools/migrate_legacy_state_to_v6.py).

The migration rewrites orchestration state files to the v6 schema only. It does
not touch lesson prose, plans, activities, vocabulary, research, or wiki files.

## Gemini review (#1229, thread `fd490a47a3674d72`) — APPROVE WITH CONDITIONS

Both blocking conditions are implemented in the script:

1. **Status coercion** — `_select_status()` maps legacy status strings
   (`"PASS@8.5"`, `"success"`, `"reject…"`, `"revise…"`, `"degraded"`, …)
   onto the v6 vocabulary `{"complete", "skipped", "failed"}` that the
   v6 runtime (`scripts/build/v6_build.py::_PHASE_SATISFIED_STATUSES`)
   and the track-health dashboard accept.
2. **API round-trip diff** — `_verify_dry_run()` calls
   `GET /api/state/module/{track}/{num}` before and after applying the
   migrated state to a temp location, then diffs `shippable`,
   `audit_status`, and `review`. Mismatches raise `AssertionError`.

Gaps a future `--apply` campaign should tighten:

* `_verify_dry_run` derives module number via
  `int(slug.split("-")[0])` and silently no-ops on non-numeric-prefix
  slugs (which is most of them). Replace with a curriculum-manifest
  lookup before any non-trivial run.
* The diff currently checks `shippable`, `audit_status`, `review`.
  Gemini also asked for `phases.*.status` parity — add it.

Other review checks were clean: precedence logic correct,
`migrated_from` key safe under the v6 parser, `__preserved_as_legacy__`
is only a warning string and is never silently inserted as a phase,
atomic write via `os.replace` is POSIX-safe.

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
