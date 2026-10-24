# Decision: Atlas entries use stable anchors on spelling hubs

- ID: dec-017
- Date: 2026-10-24
- Expires: 2027-01-22
- Status: active
- Scope: architecture
- Issue: [#8334](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8334)

## Approval chain

The operator approved one page per spelling, separate entries with stable IDs
and anchors, and preservation of old URLs. Sol 6.1 (`gpt-6.1-sol`) authored the
design. Opus 5.5 (`claude-opus-5-5`) returned `APPROVE_WITH_CHANGES` on
2026-10-24. The CTO's Unit 0 brief authorizes recording that contract with all
five required changes below. This completes designated design approval for
the recorded direction. Implementation review and acceptance remain separate.

The retained design has SHA-256
`f87fea842c7056c788936abb0654c93449fc578b71be46fda0653fcd2218e602`.
The retained Opus result has SHA-256
`17a759112a2152d1d66fb17532135c0331b35ea77788048052943f6190261207`.
These identify the approval inputs, not held-out evaluation or release proof.

## Contract

Reuse the existing identity registry as the sole allocator. Preserve `wc_`
card IDs and `ws_` sense IDs. Cards represent lexemes, MWEs, or proper names.
Descriptive matching keys and display homonym numbers never replace identity.
Corrections do not remint IDs. Keep source-qualified partitions and attach
facts only through evidenced correspondence. Polysemy uses senses. Verified
stress doublets remain variants on one card.

Keep `/lexicon/<unstressed-spelling>/` as the hub with existing slugs and
base-path handling. Every entry uses `#entry-<card_id>`, including singletons.
An independently established second entry preserves the first entry's anchor.
Merge redirects follow lineage. A conflated-card split keeps the old ID and
anchor as a chooser for all successors. Preserve old spelling URLs, form
routes, and frozen fragment aliases. Form routes do not mint lexemes.

The five required changes are part of this contract:

1. The hub key is the lowercased spelling. The descriptive entry key keeps
   case. `За́мок` follows Q12's proper-name exclusion from the general-vocabulary
   pilot. Once correspondence is resolved, `/lexicon/замок/` shows the two
   common nouns, `за́мок` and `замо́к`.
2. A spelling whose source correspondence is unresolved renders exactly as
   today. The design census identifies 3,287 spellings with several ULIF
   candidates and 778 with none. These are candidates, not proven matches.
3. Before Unit 1's acceptance check, the historical 50-disagreement case list
   must be recovered and frozen as the independent held-out set. The CTO owns
   recovery. This record does not establish that recovery is complete.
4. Missing source data stays unresolved and never proves identity. ULIF
   76793 `замо́к` has `forms_state: stale_source_snapshot` and no harvested forms.
   Its missing forms cannot justify a match or merge.
5. Unit 5 starts with a schema/version-bump PR. Per-consumer PRs follow for
   discovery and publishing. All use one cache version and prevent mixed-version
   reads. This documentation change does not bump the runtime schema.

The [identity contract](../atlas/word-cards/identity.md),
[schema Q10](../atlas/word-cards/schema.md), and
[migration sequence](../atlas/word-cards/migration.md) define the details.
Q10 now records hubs with entry anchors, replacing the earlier opaque-route
direction. This decision does not authorize public cutover or certify cards.

## Risks and mitigations

- Language review may become a backlog. Use the pinned pilot and existing
  preview. Hold unresolved correspondence and preserve current public rendering.
- Positional `#1` and `#2` fragments can break after a reorder. Freeze aliases
  first and resolve them after mounting. Ambiguous aliases open the hub chooser.
  New links use stable entry anchors.
- Static hosting has no server redirects. Inventory all old routes and keep
  explicit aliases and the redirect entries in `site/astro.config.mjs`.
  Retain fragments and check direct loads in full SSG and client-shell modes.

## Alternatives and review condition

- Separate opaque-ID entry routes would duplicate spelling-page navigation
  and conflict with the approved hub direction.
- Spelling or homonym numbers as entry IDs would conflate entries or change
  identity after a correction or reorder.

Review this decision by 2027-01-22, or sooner if route-preservation checks
cannot meet the contract. Atlas owns browser comparison and preservation
proof before public switching. Data owns certification and full coverage.
