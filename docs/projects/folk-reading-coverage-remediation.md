# FOLK Reading Coverage Remediation

Status: active blocker
Started: 2026-07-05

## Standard

FOLK seminar modules need learner-visible on-site shortened reading content. External full-text links can supplement the lesson, but they do not satisfy reading coverage by themselves.

Acceptable readings must be:

- verified against a real source text
- rights-safe for a shortened on-site excerpt
- shown in a structured `:::primary-reading{reading="<slug>"}` block
- attributed in the block body
- connected to a source or full-version link when available

Unacceptable substitutes:

- external link-only resources
- orphan `:::primary-reading` snippets without a `reading="<slug>"` source link
- paraphrase presented as primary text
- silently normalized or reconstructed text
- invented sayings, excerpts, captions, or source claims

## Current Audit

The hardened gate confirms this gap on current `origin/main`:

- Already structurally present under the new minimum: M16 `rodynno-pobutovi-pisni`
- Missing on-site structured reading content: M13 and M17-M22
- Bad inline-only format: M23 `sotsialno-pobutovi-kazky`, M24 `narodni-lehendy`
- Missing on-site structured reading content: M25-M36

M1-M12 and M14-M15 still need a stricter reread before they are treated as fully cleared.

## Remediation Order

1. Land the gate hardening so new FOLK production cannot pass with link-only or orphan readings.
2. Fix M13 and M16-M20 as the first content batch, unless the user selects a different order.
3. Fix M21-M24 next, with M23-M24 converted away from inline orphan snippets.
4. Continue in small PR-sized batches through M36.
5. Resume M37/M38 production only after the user clears the reading blocker.

Each content batch must include source verification notes, rights decisions, local gates, and independent review. DeepSeek is not an allowed reviewer for this stream.
