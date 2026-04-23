# Alignment Contract Autopsies

Systemic bugs surfaced by the 2026-04-23 alignment-pipeline audit.
Origin: [`docs/architecture/2026-04-23-alignment-pipeline-audit.md`](../architecture/2026-04-23-alignment-pipeline-audit.md).

---

## 1. Sidecar cache reuse without freshness proof

**What broke.** `scripts/build/v6_build.py:3207` reloads `contract.yaml` and `wiki-excerpts.yaml` from disk if they exist — no hash check against the current plan, wiki packet, prompt templates, canonical-anchor registry, or tokenizer version. A build can be "consistent" against artifacts generated before any of those upstream inputs changed.

**Why.** The pipeline grew sidecars as a performance optimization for re-runs, without adding a freshness contract. The assumption was that editing a plan implicitly invalidates its contract — which is only true if the contract was on the same commit. It was never enforced structurally.

**Prevention.**
- Phase 1 EPIC: `alignment_manifest.json` composed from plan hash, sources hash, template hashes, anchor-registry hash, tokenizer version, threshold snapshot, active decisions subset. Stamp on every sidecar.
- Consumer-side invariant: refuse to reuse a sidecar whose stamped hash ≠ current manifest hash.
- CI test that artificially mutates a template, runs a build, and asserts the cached sidecar was rebuilt.

---

## 2. `module_memory` silent-update on corpus change

**What broke.** `scripts/build/module_memory.py:293-316` invalidates learned constraints only on `plan_hash` mismatch. `sources_hash` and `plan_version` update silently in the same code path. Corpus, rule, or tokenizer changes land — but old writer constraints ("avoid term X, use term Y") persist as if nothing changed.

**Why.** Invalidation logic was added for plan changes when the memory feature shipped. Corpus changes were out of scope at that time; `sources_hash` was recorded as telemetry, not as an invalidation key. The distinction was never revisited when the RAG corpus started being rebuilt regularly.

**Prevention.**
- Phase 1 EPIC: add `sources_hash` to the invalidation predicate in `module_memory.py`.
- Generalize: the full `alignment_manifest` hash should be the invalidation key, not any single component.
- Test: change `sources.db` contents, confirm a module's learned constraints clear on next build.

---

## 3. Rule-after-incident governance pattern

**What broke.** Several recent incidents (#1403 auto-merge, #1431 contract asymmetry, #1448 tokenizer й/ї mangling, ISTORIO 3500-vs-4000 word-target drift) followed the same sequence: production bug → human corrects → rule added to `claude_extensions/rules/` or `memory/MEMORY.md` → hope agents read the rule next time. The rules are advisory documentation, not CI-enforced gates.

**Why.** `docs/decisions/` has `scripts/check_decisions.py` as an advisory checker, not a pre-commit or CI hook. Rules in `claude_extensions/` are rendered as agent-context only. Nothing in the build pipeline fails on contradiction between a decision and the code.

Concrete example caught by the audit: the "reviewer-as-fixer, no rewrite" decision (`docs/decisions/decisions.yaml:19-24`) is contradicted by live `section_rewrite` / `full_rewrite` / `writer_swap` strategies in `scripts/build/convergence_loop.py:595-607`. Both have been true simultaneously for ≥1 month.

**Prevention.**
- Phase 2-C EPIC: decide which side of the rewrite contradiction is correct; enforce the chosen side as a parsed-decision CI invariant.
- Phase 4-E EPIC: `diff claude_extensions/rules/ .claude/rules/` runs in CI; any non-empty diff fails the build.
- Phase 4 generally: convert the MEMORY/rules lessons into executable invariants where possible (citation resolution, Unicode round-trip, plan immutability, post-processor mutation class).
- Meta: when an incident adds a rule, the same PR should add a test that would have failed BEFORE the fix. Rules without tests are ceremonial.

---

## See also

- Audit: [`../architecture/2026-04-23-alignment-pipeline-audit.md`](../architecture/2026-04-23-alignment-pipeline-audit.md)
- EPIC: [`../epics/2026-04-23-alignment-pipeline-runtime-contracts.md`](../epics/2026-04-23-alignment-pipeline-runtime-contracts.md)
