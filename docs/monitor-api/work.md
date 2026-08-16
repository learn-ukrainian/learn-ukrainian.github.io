# Work control plane API (public foundation)

Read-only projection of public work for the local Monitor. GitHub Issues/PRs remain the source of truth. Completion vocabulary for this foundation: **`FOUNDATION_COMPLETE`** (not product `COMPLETE`).

Base URL: `http://127.0.0.1:8765` (prefer loopback IP).

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/work/v1/projection` | Normalized attention list, work items, source envelopes, denominator, cache age |
| `GET` | `/api/work/v1/capabilities` | Schema digest, budgets, class-4 endpoint freeze, private-source seam |
| `GET` | `/api/work/v1/health` | Cheap Work surface liveness |

UI: [`/work.html`](../../dashboards/work.html) — Evidence rail attention list (Monitor paper language).

## Denominator (public)

At a query instant the projection represents exactly once (or counts in a typed omission):

1. Open public issues — one `gh issue list` enumeration, cap **1000**, `truncated=true` when incomplete.
2. Open public PRs — one `gh pr list` enumeration, same cap. No per-item detail/comment/check fan-out on refresh.
3. Complete public `GET /api/issues/streams` response (private cache keys stripped).
4. Class-4 summaries only:
   - `GET /api/delegate/active`
   - `GET /api/delegate/tasks?status=all&limit<=500`
   - `GET /api/fleet/reviews`

   Never delegate task detail bodies or sealed review blobs.

## Identity

`work_id = wp1:{source_id}:{repository_id}:{resource_kind}:{remote_id}`

`source_id`: `public-monitor` | `private-local-adapter`

## Budgets

- Warm response target: **≤2s** (warm cache ~30s).
- Optional/failing section → typed degraded/unknown within **≤5s** without hiding healthy sources.
- `cache_age_s` is always present on the projection.

## Saved-view URL filters

Allowed query keys only: `health`, `kind`, `lifecycle`, `orphan`, `repository_id`, `source_id`.

Multivalue filters are canonicalized (deduplicated + sorted) before permanent warm-cache keys and `filters_applied` are formed, so duplicate/reordered query forms share one entry. `repository_id` accepts only the closed public repository singleton (`learn-ukrainian/learn-ukrainian.github.io`); it is not overridable by environment. `source_id` is enum-backed (`public-monitor` | `private-local-adapter`) both as a query key and inside the closed `filters_applied` object.

Formal-review rows are admitted only for that exact public repository (no suffix matching; missing/foreign repositories are dropped at collection and normalization).

Unknown keys, free text, private endpoints, and overlong values are rejected (`400 invalid_saved_view`).

Schema provenance: `GET /api/work/v1/capabilities` returns live `schema_digest_sha256` over `scripts/work/schema/work_projection.v1.json` (private adapters pin that digest + public commit).

## Privacy

- Public server **never** fetches, proxies, persists, or renders private-repository data.
- Private capability seam returns `available: false`, `reason_if_unavailable: not_configured` until a browser-local adapter is configured (private P2).
- Mutation is always `false` in the foundation.

## Example

```bash
curl -sS 'http://127.0.0.1:8765/api/work/v1/capabilities' | .venv/bin/python -m json.tool
curl -sS 'http://127.0.0.1:8765/api/work/v1/projection?health=AT_RISK&kind=issue' | .venv/bin/python -m json.tool | head
```

See also: [ADR-019](../decisions/ADR-019-work-control-plane.md).
