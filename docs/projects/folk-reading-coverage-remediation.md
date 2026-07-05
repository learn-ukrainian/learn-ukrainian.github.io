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
- substantial enough to function as reading content, not a token quote: at least
  six non-empty passage lines, or at least 40 words across at least two
  non-empty passage lines
- closed with a dash-led source/provenance line in house style, including the
  source title or publication evidence and the rights decision
- connected to a source or full-version link when available

Unacceptable substitutes:

- external link-only resources
- orphan `:::primary-reading` snippets without a `reading="<slug>"` source link
- one-line or otherwise token-sized primary-reading blocks
- paraphrase presented as primary text
- silently normalized or reconstructed text
- invented sayings, excerpts, captions, or source claims

## Current Audit

The first remediation wave added or converted structured on-site readings for
M13 and M17-M36. The reread follow-up found that structure alone is not enough:
many modules still surface token-sized excerpts that are useful as evidence but
not as seminar reading content.

Current `origin/main` plus the M3-M6 reread branch leaves 26 modules failing
the stricter substantial-reading gate:

- missing structured on-site reading: M9 `dumy-nevilnytski-lytsarski`, M7
  `holosinnya`, M11 `kobzarstvo-lirnytstvo`, M14
  `rodynna-obriadovist-zvychai`, M2 `vesilni-pisni`
- still token-sized rather than substantial: M13 `bylyny-kyivskoho-tsyklu`,
  M21 `charivni-kazky`, M30
  `dytiachyi-folklor-kolyskovi`, M25 `istorychni-perekazy`, M22
  `kazky-pro-tvaryn`, M10 `kolomyiky`, M35
  `narodna-vyshyvka-rushnyk-strii`, M29 `narodni-anekdoty`, M19
  `narodni-balady`, M24 `narodni-lehendy`, M32
  `narodni-muzychni-instrumenty`, M26
  `narodni-opovidannia-buvalshchyny-memoraty`, M36
  `narodni-remesla-ta-khudozhni-promysly`, M33 `narodni-tantsi`, M20
  `pisni-literaturnoho-pokhodzhennia`, M27 `prykazky-ta-pryslivia`, M34
  `pysankarstvo`, M23 `sotsialno-pobutovi-kazky`, M31
  `vertep-narodna-drama`, M28 `zahadky`
- mixed structural issue despite at least one substantial passage: M8
  `dumy-sotsialno-pobutovi`, M33 `narodni-tantsi`

M3-M6 are cleared by the current reread branch. M16
`rodynno-pobutovi-pisni` still needs manual quality reread even though it was
previously counted by the older minimum.

## Remediation Order

1. Keep the gate hardening in place so FOLK production cannot pass with
   link-only, orphan, or one-line readings.
2. Land the M3-M6 reread slice that adds explicit attribution and removes the
   short M6 song from the structured reading surface.
3. Continue in small PR-sized slices through the remaining failed list above,
   using substantial source-verified excerpts or explicit blockers.
4. Resume M37/M38 production only after the user clears the reading blocker.

Each content batch must include source verification notes, rights decisions, local gates, and independent review. DeepSeek is not an allowed reviewer for this stream.
