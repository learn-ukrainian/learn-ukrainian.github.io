# ADR-019: Work control plane (unified browser projection)

**Status**: Accepted (public foundation P1 + browser-local unified P3)
**Date**: 2026-08-16
**Deciders**: Operator brief v3 + design inspection GO; implementation on public issue #5921
**Completion vocabulary**:
- Server/schema foundation: `FOUNDATION_COMPLETE` (never product `COMPLETE`)
- Browser dual-source slice: `UNIFIED_COMPLETE` (dual fetch/validate/merge, public-safe
  saved views, independent degradation, docs, deterministic proofs, ready PR,
  exact-head cross-family approval, green checks — not mutation/hosted/proxy)

## Context

Operators need a single local Work surface that answers what needs attention across
the public Learn Ukrainian repository and an optional private infrastructure
repository without creating a second planning authority. GitHub Issues/PRs remain
the source of truth. Existing Monitor projections remain authoritative for their
domains. Private bodies must never enter the public tree, API, shareable URLs, or
browser-rendered error text.

## Decision

1. **Public owns the schema.** Authoritative contract:
   `scripts/work/schema/work_projection.v1.json` (`schema_version: work-projection.v1`).
   The private adapter pins this file by public commit
   `f522c8dba5a68d86fe29d1a36bd8cfeb8c3acb9d` + SHA-256
   `89fb9c1eec41baaa00a328d456340111163c1e3ab899cd7baa15e284fff65bde` and must not
   fork fields. `filters_applied` remains a closed object on the public API.
2. **Public Monitor serves a read-only projection** at
   `GET /api/work/v1/projection` (plus `/v1/capabilities`, `/v1/health`) and a UI
   at `/work.html`.
3. **Canonical identity** is
   `(source_id, repository_id, resource_kind, remote_id)` serialized as
   `wp1:{source_id}:{repository_id}:{resource_kind}:{remote_id}`.
4. **Warm refresh denominator (public)**:
   - open public issues (one GH list enumeration, cap 1000, `truncated=true` if incomplete)
   - open public PRs (one GH list enumeration, same cap)
   - complete public `/api/issues/streams` projection (never raw cache private keys)
   - class-4 summaries only: `GET /api/delegate/active`,
     `GET /api/delegate/tasks?status=all&limit<=500`, `GET /api/fleet/reviews`
5. **No mutations.** FX-10 mutation preview/idempotency remains design-only.
6. **Private source is browser-local only.** The public server never fetches,
   proxies, persists, configures, or logs the private adapter. Only
   `dashboards/work.html` may GET the fixed constant
   `http://127.0.0.1:8766/v1/projection` with a 5s abort budget, CORS-safelisted
   headers, `credentials: omit`, and no query string. The endpoint is not
   configurable and never enters shareable saved-view state.
7. **Independent dual-source settlement.** The browser uses `Promise.allSettled`
   (or equivalent). Either source may fail without blocking the other. Private
   admission is closed-world (exact keys, redacted item shape, digest pin, single
   `private-local-adapter` source). Collisions reject the private payload
   (`identity_collision`) without overwriting public items. Merge replaces the
   public placeholder private source, concatenates items, sums denominators, ANDs
   `streams_complete`, preserves public class-4 authority, installs private
   capability metadata, takes `max(cache_age_s)`, and densifies attention.
8. **Health** is rule-derived (`ON_TRACK` / `AT_RISK` / `OFF_TRACK` / `UNKNOWN`).
   Activity volume is never health evidence.
9. **UI direction**: Evidence rail — Monitor paper tokens, dense attention list,
   lifecycle/evidence rail, authority/freshness, keyboard-first, reduced motion,
   ~390px usable layout without horizontal overflow.
10. **Saved views**: URL query only; stricter shareable allowlist than local
    filters so private repository slugs and `private-local-adapter` never enter
    transferable state.

## Consequences

- P1 ships the public foundation with no private checkout.
- P2 (private repo adapter process) lives outside Hramatka production routes and
  pins the public schema digest; it is not imported by the public server.
- P3 completes browser-local dual-source unification (`UNIFIED_COMPLETE` scope).
- Adding or removing class-4 endpoints is a counted residual requiring plan re-review.
- Foundation completion remains `FOUNDATION_COMPLETE`; unified browser completion
  is reported separately as `UNIFIED_COMPLETE` and is still not product-complete
  for mutation or hosted deployment.

## Alternatives considered

- Server-side merge of private adapter into public Monitor (rejected: SSRF + privacy boundary).
- Configurable private endpoint via query/storage/env (rejected: shareable-state + SSRF footgun).
- Reusing `/api/orient` as the Work denominator (rejected: incomplete GH limits, fat aggregate).
- Dark ops console UI (rejected: fights Monitor paper language).
