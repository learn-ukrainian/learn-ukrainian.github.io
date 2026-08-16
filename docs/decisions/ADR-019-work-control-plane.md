# ADR-019: Work control plane (public foundation)

**Status**: Accepted (public foundation P1)
**Date**: 2026-08-16
**Deciders**: Operator brief v3 + design inspection GO; implementation on public issue #5921
**Completion vocabulary**: `FOUNDATION_COMPLETE` (never product `COMPLETE`)

## Context

Operators need a single local Work surface that answers what needs attention across the public Learn Ukrainian repository (and later a private infrastructure repository) without creating a second planning authority. GitHub Issues/PRs remain the source of truth. Existing Monitor projections remain authoritative for their domains. Private bodies must never enter the public tree, API, or shareable URLs.

## Decision

1. **Public owns the schema.** Authoritative contract: `scripts/work/schema/work_projection.v1.json` (`schema_version: work-projection.v1`). The future private adapter pins this file by public commit + SHA-256 (`schema_digest_sha256` from `/api/work/v1/capabilities`) and must not fork fields. `filters_applied` is a closed object that includes enum-backed `source_id` alongside health/kind/lifecycle/orphan/repository_id, with finite `maxItems`/`uniqueItems` (and repository `const`) aligned to the saved-view parser's raw cardinality bounds.
2. **Public Monitor serves a read-only projection** at `GET /api/work/v1/projection` (plus `/v1/capabilities`, `/v1/health`) and a UI at `/work.html`.
3. **Canonical identity** is `(source_id, repository_id, resource_kind, remote_id)` serialized as `wp1:{source_id}:{repository_id}:{resource_kind}:{remote_id}`.
4. **Warm refresh denominator (public)**:
   - open public issues (one GH list enumeration, cap 1000, `truncated=true` if incomplete)
   - open public PRs (one GH list enumeration, same cap)
   - complete public `/api/issues/streams` projection (never raw cache private keys)
   - class-4 summaries only: `GET /api/delegate/active`, `GET /api/delegate/tasks?status=all&limit<=500`, `GET /api/fleet/reviews` (Work's production collectors pass the admitted public repository into internal delegate/fleet loaders so filtering precedes pagination/counting; HTTP surfaces stay unscoped except fleet's exact `repository` query)
5. **No mutations** in the foundation. FX-10 mutation preview/idempotency remains design-only.
6. **Private source seam**: public server never fetches, proxies, persists, or renders private-repository data. Capability object reports `available: false` / `not_configured` until a browser-local private adapter exists (P2).
7. **Health** is rule-derived (`ON_TRACK` / `AT_RISK` / `OFF_TRACK` / `UNKNOWN`). Activity volume is never health evidence.
8. **UI direction**: Evidence rail — Monitor paper tokens, dense attention list, lifecycle/evidence rail, authority/freshness, keyboard-first, reduced motion, ~390px usable layout.

## Consequences

- P1 ships and CI-passes with no private checkout.
- P2 (private repo) adds a local loopback adapter outside Hramatka production routes and pins the public schema digest.
- Adding or removing class-4 endpoints is a counted residual requiring plan re-review.
- Foundation completion is reported as `FOUNDATION_COMPLETE`, not product complete.

## Alternatives considered

- Server-side merge of private adapter into public Monitor (rejected: SSRF + privacy boundary).
- Reusing `/api/orient` as the Work denominator (rejected: incomplete GH limits, fat aggregate).
- Dark ops console UI (rejected: fights Monitor paper language).
