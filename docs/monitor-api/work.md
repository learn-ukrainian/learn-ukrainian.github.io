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

Multivalue filters are bounded by finite per-key raw cardinality (domain size for health/kind/lifecycle/source_id; singleton for orphan and `repository_id`) **before** canonicalization, then deduplicated + sorted so duplicate/reordered forms within the bound share one permanent warm-cache key and one `filters_applied` object. Excess raw repetitions reject with `400 invalid_saved_view`.

`repository_id` accepts only the closed public repository singleton (`learn-ukrainian/learn-ukrainian.github.io`); it is not overridable by environment. `source_id` is enum-backed (`public-monitor` | `private-local-adapter`) both as a query key and inside the closed `filters_applied` object. The authoritative schema enforces matching `maxItems`, `uniqueItems`, lifecycle enum, and repository `const` on `filters_applied`.

Every projection-builder entry point (`build_projection`, `build_public_projection`, cache-key minting, HTTP) re-enters the shared saved-view admission gate; unknown keys and foreign repository IDs cannot bypass via direct calls.

Formal-review rows are admitted only for that exact public repository (no suffix matching; missing/foreign repositories are dropped at collection and normalization).

Delegate class-4 rows are admitted only when they carry an exact canonical public claim on the authoritative attribution fields `repository` or `repository_id` (both must agree when present). Missing, ambiguous, path/branch/task_id-inferred, and foreign rows are omitted **before** public totals/truncation/normalization, so private volume cannot inflate public counts or attach same-number private task IDs to public issues/PRs. The production loaders receive the already-admitted public singleton and apply that exact repository predicate on task state **before** sort/limit/total (Work still re-admits defense-in-depth). The public HTTP `/api/delegate/*` routes remain unscoped for other Monitor consumers and do not expose a free-form repository selector. Bodies and result files are never read.

Unknown keys, free text, private endpoints, overlong values, and oversized repeated filter values are rejected (`400 invalid_saved_view`).

Schema provenance: `GET /api/work/v1/capabilities` returns live `schema_digest_sha256` over `scripts/work/schema/work_projection.v1.json` (private adapters pin that digest + public commit). Any change to the closed `filters_applied` contract (including maxItems/uniqueItems/enums/const) changes that digest.

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
