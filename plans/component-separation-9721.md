---
version: 1
issue: 9721
status: design-approved-implementation-pending
original_report_sha256: d17d5ba8cbb24e84d8d20368947ae0962bf344e32fc51dc5153b19342c4e0dda
original_source_sha: 841701f9a1f59b5471e995f6781a97e61c5791d4
approval_result_sha256: acfb12274231d4cf8288c2b66baab0b1022018f139dc552b59703d403087e141
inspected_source_sha: ad17bcc2bf201a4ea019831ec855611814a4e4c1
---

# Component separation plan — #9721, version 1

This records the independently approved six-component design for [#9721](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9721). Implementation is pending. Separate producer preparation, consumer verification and tests within the existing repository first, preserving shared infrastructure, existing stream authority, all correctness assertions and learner behavior. Physical repository separation remains an independently reviewed option; this plan does not select it or introduce a package layout, framework, cache, affected-test selector, frontend route seam or timing target.

The accountable driver is codex-devops through the existing DevOps stream [#5703](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5703). Root retains scope, review judgment, integration, landing, issue status and subsequent implementation. Component authorities retain their streams. This document is the first deliverable, not delivered component separation; it completes neither AC-01 nor the whole issue. The issue remains open until its full acceptance criteria are proven.

## 1. Approval, evidence and denominator

The complete approved input is the revision-2 design result, SHA-256 `d17d5ba8cbb24e84d8d20368947ae0962bf344e32fc51dc5153b19342c4e0dda`, at source `841701f9a1f59b5471e995f6781a97e61c5791d4`. The whole-file digest was recomputed for publication. The report's self-digest `fb729e7bb6af0b757e86c94890374d1ba29bd5b65629848439ee37eff6ff9a2b` covers only part of the report and is not the approval binding.

Assigned design author: `gpt-6.1-sol`, OpenAI family, native Codex, high effort. Design approval: `claude-opus-5-5`, Anthropic/Claude family, native Claude Code, high effort; its result binds the complete-file digest and original source and says **APPROVE**, with no remaining design blockers. The approval describes the author's identity as assigned rather than runtime-attested. Sol authorship plus native Opus approval supplies designated design provenance. It is neither implementation CF nor publication/cutover authorization. Private reports remain outside Git; this plan transfers technical obligations, without operational transcripts or private metadata.

Evidence classes used below:

- **Current inspected source (C):** `ad17bcc2bf201a4ea019831ec855611814a4e4c1`. Source citations give repository-relative paths and bounded line spans inspected for publication; they prove interfaces and source behavior, not successful execution.
- **Approved source snapshot (S):** `841701f9a1f59b5471e995f6781a97e61c5791d4`. The approved report's direct inspections at S remain historical where not rechecked here.
- **Original observations (O):** `51df047088d13929b7063d11468a1fdc37d6fbc9`; **reconnaissance (R):** `12fc3529e6ae3d6be022dc51bbfa4912f81e1e13`. O/R locators below preserve the approved report's historical edge evidence, not present runtime verification or independent approval.
- **Unresolved:** complete inventories, named component-interface authority, publication bindings and behavior proof remain unknown where stated. Sparse absence is missing materialization, not an empty inventory or successful build.

The fixed design denominator is exactly six components, every shared artifact family and producer/consumer/reverse edge in section 3, seven migration steps, six residual groups, and all verification/rollback obligations here. Before implementation, freeze the exact discovered affected test node IDs, assertions, artifact members and learner routes. No current complete inventory or completion percentage is inferred from headings, configured selection counts or digests.

### Current factual grounding

Observation date: 2026-10-05 UTC. Commands were read-only source/issue queries; no hydration, payload enumeration, learner generation, runtime installation, source suites or timing runs were executed for publication.

| Evidence | Bounded source or command/result | Implication |
| --- | --- | --- |
| Source identity | `git rev-parse HEAD` → `ad17bcc2bf201a4ea019831ec855611814a4e4c1` | The inspected publication baseline, not an implementation head |
| Current command coupling | [site/package.json](../site/package.json), C lines 6–32 | `hydrate` still runs the full producer chain; `test:unit` hydrates before Vitest; `build:shell` verifies then performs shared Astro build |
| Existing shell verifier | [verify-consumed-artifacts.mjs](../site/scripts/verify-consumed-artifacts.mjs), C lines 12–23, 61–90 | Checks named Atlas inputs, browse membership, manifest freshness and teacher pointer; this file does not certify stats/arc/landing freshness or the complete runtime inventory |
| Landed stats repair | `gh issue view 9754` → CLOSED; `gh pr list --state merged --search '9754'` → PR #9759 MERGED, merge `a6c4769dc7810d7bc0dec1c74e71866e3a2c2427` | [#9754](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9754) is the landed stats-family dependency; do not duplicate its repair |
| Current stats comparison | [generate_curriculum_stats.py](../scripts/generate_curriculum_stats.py), C lines 28–79, 100–117; [test_generate_curriculum_stats.py](../tests/test_generate_curriculum_stats.py), C lines 73–164 | Non-writing producer comparison and stale/missing/malformed/source-change regressions now exist; no local rerun or current-count audit is claimed here |
| Existing arc comparison | [build_arc_landing.py](../scripts/build/build_arc_landing.py), C lines 136–255, 268–375; [arc loader](../scripts/curriculum/arc/loader.py), C lines 51–84 | Producer-derived outputs, stale/missing/orphan checks and design-source digest rejection already exist; preserve and qualify them |
| Non-arc producer | [build_landing_pages.py](../scripts/build/build_landing_pages.py), C lines 322–375; [compatibility wrapper](../scripts/build_landing_pages.py), C lines 2–15 | The wrapper delegates; the actual producer writes core/specialized/intro pages. Complete dependencies and non-writing comparison remain unqualified |
| Display readers | [slug route](../site/src/pages/[...slug].astro), C lines 13–20, 58–62, 311–319, 657–660; [content.config.ts](../site/src/content.config.ts), C lines 5–32, 38–39 | Stats, arc, docs, readings and Atlas search are shared display inputs; missing arc JSON raises; curriculum display consumes Atlas search |
| Existing selection guard | [frontend_change_scope.py](../scripts/ci/frontend_change_scope.py), C lines 224–240, 290–301; [test_frontend_change_scope.py](../tests/test_frontend_change_scope.py), C lines 377–404 | Hydrate-denominator assertion is enforced by tests including a removal mutation; `main()` does not invoke it. Source evidence is not a test-pass receipt |
| Existing CI surfaces | [ci.yml](../.github/workflows/ci.yml), C lines 225–230, 310–331 | Separate site-toolchain lane; shared tracked-file sharding excluding `atlas_release`, `slow`, `site_toolchain`. Placement weights are not affected-test selection |
| Current stream registration | [WORKSTREAMS.md](../docs/WORKSTREAMS.md), C lines 60–70; [issue_streams.yaml](../scripts/config/issue_streams.yaml), C lines 17–46 | Existing Atlas/practice, Infra, DevOps, open-model and curriculum streams remain; registration is not a new interface-owner agreement |
| Live issue boundaries | `gh issue view` → #9721 OPEN, #9718 OPEN, #8875 OPEN | Separation, build reuse and CI-speed work retain their distinct ownership and proof |

A scoped `git diff --stat S HEAD` of the package, shell verifier, stats producer, arc producer/loader, non-arc producer, selection guard/tests, CI workflow and stream documents showed changes only in the stats producer and the two stream documents. It does not prove whole-repository equivalence. The approved report's absence-of-stats-check finding is historical and repaired by #9754. Arc/landing qualification and broader shell-verifier completeness remain separate obligations. No new owner agreement follows from source drift checks.

Historical prerequisite: [#8510](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8510) and [PR #9749](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9749) were CLOSED/MERGED in the approved evidence; merge S is the landed baseline, not a prerequisite still awaiting landing and not #9721 implementation proof. The only suite-related CI cited by the approved report is run `37299333271` at O: success with Checks, Frontend, Freeze pytest durations, Secret scan, Dependency audit, pytest and pytest report skipped; Reuse check, Queue commit metadata scan and CI Gate succeeded. That is historical reuse/gate evidence, not fresh source-suite proof.

## 2. Six-component map and located commands

`P` means the task-prescribed project Python interpreter, supplied by each implementation brief. npm commands below run in `site/`; Make targets run at repository root with that interpreter supplied through `PYTHON`. These are located existing interfaces, not newly approved independent boundaries or commands executed for this document. Preserve explicit input/output arguments and existing source withholding.

| Component | Located source/build/preparation interface | Located test/verification interface | Boundary and existing authority |
| --- | --- | --- | --- |
| Open-model data/evaluation | [model_view_exporter.py](../scripts/projects/open_model_data/model_view_exporter.py): C 1964–2031 supplies `P -m scripts.projects.open_model_data.model_view_exporter` subcommands `materialize-human-source`, `continued-pretraining`, `correction`, `preference`, `quality-filter`, `evaluation`, `recipe`; [receipt audit](../scripts/projects/open_model_data/audit_model_ready_receipts.py): C 594–611 supplies `P -m scripts.projects.open_model_data.audit_model_ready_receipts --output <receipt>` | `P -m pytest tests/test_open_model_view_exporter.py tests/test_model_ready_receipt_audit.py`; audit `--verify-existing`; shared pytest/data-tier selection | JSONL views, export receipts, recipes and product audit; existing open-model-data stream (#6321), with named component-contract handoff evidence unresolved |
| Atlas data | [site/package.json](../site/package.json): C 6–12, `npm run hydrate:manifest`, `atlas:build-db`, `atlas:build-search`, `atlas:build-daily`; [Makefile](../Makefile): C 61–70, `make atlas` / `atlas-publish` | `P -m pytest tests/test_atlas_db.py`; `npm run atlas:validate-aliases` is validation, not suite proof; shared pytest | Pointer/fingerprint, hydrated manifest, Atlas DB and lexical projections; existing Atlas/practice stream (#4387), named interface evidence unresolved |
| Atlas frontend | Package C 18–20: `npm run build:shell`, `build`, `build:full`; shared Astro. [atlas-static-paths.ts](../site/src/lib/lexicon/atlas-static-paths.ts): O 18–54 describes client-shell and diagnostic static modes | Package C 28–32: `test:atlas-route-parity`, `test:atlas-release-gate`, `test:atlas-client-shell-e2e`, `check:atlas-browser-bundle`; [atlas-runtime-shards.test.ts](../site/tests/unit/atlas-runtime-shards.test.ts); shared built-output tests | Search/browse/daily/runtime assets; diagnostic routes also consume SQLite. Existing Atlas/frontend authority; #9718 owns reuse work, not the whole frontend |
| Practice frontend | Package C 11, 13–14: `npm run hydrate:practice`, `hydrate:teacher`; Makefile C 72–80: `make practice-deck`, `practice-deck-publish`, `teacher-deck-refresh` with declared inputs | `P -m pytest tests/test_practice_deck_io.py tests/test_generate_practice_deck.py tests/test_publish_practice_deck.py`; [LexiconPractice.test.tsx](../site/tests/unit/LexiconPractice.test.tsx), [ZnoPractice.test.tsx](../site/tests/unit/ZnoPractice.test.tsx), [hydrate-practice-deck.test.ts](../site/tests/unit/hydrate-practice-deck.test.ts) via Vitest | Published kind/level shards, teacher/cloze decks, lesson keys and ZNO metadata; existing practice/Atlas authority, named contract boundary unknown |
| Curriculum generation | [generate_arc.py](../scripts/curriculum/arc/generate_arc.py): C 562–622, `P scripts/curriculum/arc/generate_arc.py --level <level> --write` / `--check`; `P -m scripts.build.build_arc_landing <level> --write` / `--check`; `P -m scripts.build.build_landing_pages`; lesson pipelines listed in section 3 | `P -m pytest tests/build/test_build_arc_landing.py tests/build/test_lesson_assembler.py tests/build/test_fresh_assemble.py`; existing validation/parity gates; stats dependency's existing test/check | Arc YAML/JSON, landing/module/lesson MDX, level status, lesson manifests and schema; existing curriculum-upgrade (#7994) and relevant domain authorities, named handoff proof incomplete |
| Curriculum display | [content.config.ts](../site/src/content.config.ts), C 5–32, 38–39; slug route C 13–20, 58–62, 311–319, 657–660; package C 18–25 uses shared Astro build and `npm run test:built-output` | `npm run test:built-output` names [build-renders.test.ts](../site/tests/unit/build-renders.test.ts) and [etymology-handler-built-output.test.ts](../site/tests/unit/etymology-handler-built-output.test.ts); CI `site_toolchain` includes `tests/build/` | Committed stats/arc/MDX/readings plus Atlas search → routes/HTML. Existing frontend/curriculum authorities; independent display composition not proven |

The approved inspection chain located command surfaces for 6/6 components but proved complete independent build/test boundaries for 0/6 and approved named component-contract owner handoffs for 0/6. Those are historical inspection coverage limits, not a present ownership census. Current registration grounds existing stream authority without inventing agreement. No independent-build improvement is claimed by this document.

## 3. Shared artifact families and dependency edges

Every row remains in the migration denominator. O/R spans are historical approved-report locators; current rechecks are marked C. Unknown callee, member, reader or publication evidence must remain unknown until the existing producer/consumer authority qualifies it.

| Producer → artifact → consumer | Binding and remaining evidence |
| --- | --- |
| Storage publication → `registry/artifacts/<group>.manifest.json`, managed members and companions → storage readers/hydration | [artifacts.py](../scripts/storage/artifacts.py), O 251–289, 1151–1166, 1200–1209; [storage paths](../scripts/storage/paths.py), O 105–153, 187–230. Preserve membership, digests and publication consistency. Schema hardening remains separate Infra/storage maintenance |
| Open-model exporter → JSONL view + export receipt → recipe | Exporter O 1146–1193, 1818–1835: schema/kind/count/byte/digest binding; local paired replacement rollback O 1073–1126. Concurrent-reader safety remains unproven |
| Model-ready receipts/contracts → product-audit receipt → verify-existing reader | Receipt audit O 64–86, 132–157, 589–608; C 594–611 verifies expected receipt bytes against inputs. Exact production exporter → named receipt → audit invocation remains incomplete; receipts do not prove payload quality or training success |
| Classification → logical K/A paths → model readers | [open-model paths](../scripts/projects/open_model_data/paths.py), O 240–254, 297–323: K is registry, A is managed data; unclassified paths refuse. Exact receipt/group classification and release binding remain unverified; preserve quarantine |
| Manifest publication → pointer/fingerprint → hydrated manifest | [hydrate-manifest.mjs](../site/scripts/hydrate-manifest.mjs), R 27–29, 260–261; verifier C 80–82. Pointer freshness is not complete runtime readiness |
| Manifest/aliases → Atlas DB → static/data readers | R build step 2; [sqlite-atlas-data-source.ts](../site/src/lib/lexicon/sqlite-atlas-data-source.ts): R 63; [atlasDb.ts](../site/src/lib/lexicon/atlasDb.ts): R 87; static paths O 35–54. Client-shell route skipping does not establish that every import avoids SQLite |
| Atlas DB → search/aliases/search shards/browse metadata, flagged entries, daily pool → frontend and curriculum display | R build steps 3–4; package C 6–11 and display route C 14, 59. Preserve this cross-component search edge |
| Practice generation/publication → pinned pointer/package → practice-kind.level shards → practice readers | [practice_deck/io.py](../scripts/practice_deck/io.py), O 25–35, 128–175; [hydrate-practice-deck.mjs](../site/scripts/hydrate-practice-deck.mjs), O 199–245, 267–282. Make targets are located; complete publication callee boundary is not proven |
| Practice/search → API shard hydration → `site/public/api/lexicon` and `site/public/lexicon/search` → runtime | R build step 7; package C 11. Complete runtime/member inventory remains unproven |
| Teacher publication → teacher pointer → teacher deck/cloze → practice/custom decks | R build step 6/readers; verifier C 83–88. Preserve published-byte/member readiness; pointer verification alone does not close the inventory |
| Teacher cloze → `lexicon-teacher-lesson-keys.json` → custom decks | R build step 8; [custom-decks.ts](../site/src/lib/lexicon/custom-decks.ts): R 15. Named generated-data drift check, not a check of all `src/data` |
| Named ZNO decks → `practice-zno-meta.json` → ZNO practice | R build step 9; [ZnoPractice.tsx](../site/src/components/ZnoPractice.tsx): R 3. Consumer of `practice-zno.residual.json` remains untraced |
| Arc design → `_arc.yaml` → schema/source-digest-validating loader | R curriculum E-01; loader C 51–84. Preserve design-source freshness and schema rejection |
| Arc/plans/scope/state → arc JSON + arc landing/module MDX + level status → display/non-arc generation | Arc producer C 136–255, 268–375; display C 17–20, 657–660. Preserve complete output byte comparison and orphan detection; qualify producer dependencies |
| Canonical curriculum YAML → `curriculum-stats.json` → track/home module counts | Stats producer C 23–79, 100–117; slug route C 13, 58–62. #9754/#9759 supplies the landed repair/check; integrate its evidence, do not duplicate it |
| Level status → non-arc landing MDX, specialized landings and intro → docs/display | R curriculum E-05; actual producer C 322–375, wrapper C 2–15. Complete source/template/config dependencies and compare mode still need owner qualification |
| Lesson assembly → lesson MDX + lesson manifests → display/review promotion | R E-06–10: [v7_build.py](../scripts/build/v7_build.py) 3061–3084; [lesson_assembler.py](../scripts/build/lesson_assembler.py) 383–478; [fresh/assemble.py](../scripts/build/fresh/assemble.py) 3032–3239; [fresh/manifest.py](../scripts/build/fresh/manifest.py) 392–425; [fresh/cli.py](../scripts/build/fresh/cli.py) 520–560. Review-receipt branch remains incomplete |
| React props → transient AST JSON → `docs/lesson-schema.yaml` → curriculum generation gate | R E-11–12 and original driver trace. This is a frontend-source-to-generation reverse edge; bind one producer-owned extraction interface, not display-only data |
| Readings and practice cloze/reviewed-source JSON → display/verifier | Content config C 38–39, display C 311–313, verifier C 21–22. Complete producers/publication contracts remain unknown |

The historical O registry observation was `group=open_model_release_payload`, `schema=1`, `entries=233`, `descriptor_members=233`, `descriptor_companions=17`. It records registry membership, not current payload availability, release eligibility or semantic success. No corpus census is performed by publication.

Preserve [ADR-017](../docs/architecture/adr/adr-017-atlas-schema-and-lifecycle.md)'s source/projection and user-state boundaries, stable identities, compatibility/parity and divergent-fixture rejection, withholding and provenance. Reconcile actual readers/runtime/practice/API edges before claiming compliance. The plan does not grant source admission, promote quarantined candidates or rewrite learner content.

## 4. Preparation, verification and tests

The concrete AC-03 coupling is `test:unit` → full `hydrate` before Vitest (package C 24). Hydration chains manifest hydration, Atlas DB/search/daily generation, practice/teacher hydration, API shards, teacher lesson keys and ZNO metadata (C 11). `build` also hydrates (C 18). `build:shell` already runs `verify:artifacts && astro build` without hydration (C 19), but still performs shared Astro compilation.

Approved responsibility split:

- Producer preparation explicitly creates/publishes the owning artifacts and any producer-derived current-input verification evidence.
- Consumer verification reads the exact required immutable set, refuses missing/incompatible/corrupt/stale inputs and never regenerates or repairs them. Required committed contracts absent/stale on a clean checkout fail with owner/recovery guidance; managed data requires explicit existing preparation; missing runtime members fail readiness.
- Unit tests consume immutable prepared inputs. Mutation tests use private fixture/output roots and preserve existing source withholding; shared-write races block adoption.
- Built-output tests consume the exact fresh build or reuse qualified against current inputs and expected outputs.
- Shared Astro assembly remains integration until the smallest independently reviewed route/import seam proves independent builds for Atlas frontend, practice frontend and curriculum display. No seam is selected here.

Consumers need not execute producers to prove freshness: they may verify explicit preparation evidence bound to complete current inputs and output membership. If source inputs are unavailable, that evidence must cover them, otherwise readiness is unverified. Re-hashing old output never makes its input binding current. All consumers preserve existing refusal, source withholding, quarantine and compatibility behavior.

CI selection stays shared Infra. Current workflow sharding places tracked test files and excludes `atlas_release`, `slow`, `site_toolchain`; the separate site-toolchain job includes `tests/build/`. [data_tier.py](../scripts/ci/data_tier.py), O 326–347 selects audited node IDs; O 580–617 provisions/hydrates whole runs with a distinct subset branch. The hydrate-denominator assertion has source-confirmed test/mutation enforcement (C citations above); preserve it, without inventing a `main()` call or executed test result.

Historical O selection metadata: `tracked_open_model_collector_files=190`, `under_component_test_directory=85`; data-tier `declared_cases=542`, `nodeids=542`, `files=102`, `open_model_nodeids=341`, `open_model_files=48`, `bulk_nodeids=16`. These are collection candidates/configured selections, not executed assertions, complete affected-test coverage, independence or healthy runners. Freeze the actual complete inventory before changing selection; unknown dependencies retain existing coverage.

## 5. Freshness contracts and negative controls

Integrity means bytes match their digest. Freshness means bytes represent the current complete producer inputs. Every enabled display input requires both. Fingerprint producer-consumed inputs, relevant source/schema/tool/config/lockfile identities, output path/member sets and meaningful existence/absence predicates. Same-size changes, source renames/deletions and member changes invalidate the relevant reuse evidence. No new registry, service or approval authority is introduced.

| Family | Producer-derived positive evidence | Required negative controls and qualifications |
| --- | --- | --- |
| Stats | #9754's landed `build_stats`/`stats_drift` and `--check` compare all current manifest-derived level keys, values, total and exact serialized output; existing regression tests are the dependency | Keep old JSON and its matching digest while adding/removing modules or a level: refuse stale. Missing/malformed/wrong-key output refuses. Fresh producer-equivalent counts pass. A YAML change with identical counts may be semantically equivalent but cannot retain a falsely current input fingerprint. Verify integration/current binding rather than build another stats repair |
| Arc JSON | Loader validates schema and design-source digest; producer uses arc fields/order, module plans, lesson titles/numbers, scope sidecars, lesson-page presence, gate files, plan review, module verdict and previous-edition page presence (C 136–255). Preserve expected-byte comparison (C 307–375) | Change an arc field, plan title/lesson list, scope count, gate/review state or relevant file presence while retaining digest-valid old JSON: refuse stale. Change design without regenerating `_arc.yaml`: preserve loader rejection. Source removal invalidates; fresh exact outputs pass |
| Arc landing/module MDX and level status | Same producer owns landing/index bytes and level-status planned value (C 268–317). Use existing `--check`, missing-output and orphan-page semantics; do not build a competing render oracle | Alter position membership/order, title/job or output presence while preserving old MDX/digest: refuse affected stale output. State changes can alter JSON without altering an index page; check the complete set instead of requiring every output to change |
| Non-arc landing MDX | Actual producer consumes level status and emits core/specialized/intro pages; qualify complete source/template/config dependencies and non-writing deterministic comparison through its owner | Change a producer-consumed status field with old digest-valid page retained: producer-derived oracle must refuse stale; fresh matching output passes. This control is unexecuted; no existing `--check` flag is assumed |
| Open-model publication and recipes | Existing schema/kind/count/bytes/digest checks, audit expected-input comparison, classified K/A paths and paired artifacts | Missing, incompatible or corrupt pair/member/input refuses; unclassified paths and quarantined sources remain withheld. Qualify exact exporter→receipt→audit and release/group binding, stale current-input evidence, and concurrent-reader/partial-installation behavior. A receipt is not training or payload quality proof |
| Teacher/practice/runtime/readings/schema/lesson contracts | Producer-qualified complete required members, compatibility and current-input binding, plus owning reader checks | Missing shard/deck/lesson key/reading/schema/member, incompatible versions, corrupt bytes or stale source/tool/config/pointer/member evidence must refuse. Trace unresolved publication/readers first; do not claim the current shell verifier covers everything |

Arc input identity also covers its loader/plan-validation dependencies and local findings-database freshness branch. Arc producer C 184–217 recomputes local verdict problems when that database is available; CI without it trusts committed verdicts. A CI receipt cannot claim it independently recomputed local review truth. Use existing generator checks first; a missing non-writing producer comparison is supplied by the producer authority through normal implementation review.

Historical evidence retained with limits:

- Opus round-1 counterexample at O: 4/22 stats keys differed, `bio` 310→410, `c1` 132→133, `folk` 42→40, `_total` 1833→1932. This is a historical finding, not current committed counts; #9754 has repaired the stats family.
- Author's S in-memory stats probe compiled actual counting statements with synthetic inputs, no payload reads or writes: old expected total/modules 1, changed-source expected total/modules 2; retained digest valid `True`, matches current producer `False`. It falsifies digest-as-freshness, not an implemented checker or learner outcome.
- Original O pure storage probe: manifest v1 ACCEPTED, unsupported version ACCEPTED, missing version ACCEPTED, invalid digest REJECTED (`ValueError`). Opus's inspection corroborated 15 committed schema-1 manifests; neither observation is a current manifest census. Optional schema-validation hardening stays with storage/Infra and is not a seventh migration residual or gate.
- Original O shell probe assumed pointer validators valid: absent runtime practice/API shards still yielded exit 0; missing committed search index yielded exit 1. This limits verifier completeness; it is not a real build or full pointer/runtime proof.
- The driver-reported **4/4 arc probe** is historical pure mechanism proof at its old source snapshot, not a migration outcome. Publication does not re-establish its exact receipt/source binding or rerun it; it cannot certify current freshness or satisfy implementation behavior proof.

## 6. Existing authority and seven-step migration

[WORKSTREAMS.md](../docs/WORKSTREAMS.md) and [issue_streams.yaml](../scripts/config/issue_streams.yaml) ground existing stream membership. They do not establish all named producer/consumer handoffs. Missing named evidence must be recorded and resolved by codex-devops through the existing domain leads, without assigning a new owner. New acknowledgements are required only for actual changes in contract shape/obligations or owner assignments; unchanged established authority is not re-approved. User authorization does not erase cross-stream ownership.

| Contract responsibility | Existing authority retained | Coordination obligation |
| --- | --- | --- |
| Managed membership/publication/digests | `scripts.storage`, shared Infra claude-infra | [#9737](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9737); optional schema hardening stays here |
| Open-model views/receipts/recipes | Existing open-model authority | codex-devops resolves exact interface/publication evidence |
| Atlas projections | Existing Atlas authority | codex-devops coordinates changed contracts |
| Practice/teacher/ZNO packages | Existing practice authority | codex-devops coordinates changed contracts |
| Lesson-schema extraction | Existing frontend extractor and curriculum validator authorities | Bind one producer-owned interface; acknowledge actual changes |
| Consumer compatibility/readiness | Existing consuming component authority | Accept changed obligations/assignments |
| CI selection/shared assembly/integration | Existing Infra claude-infra | [#8875](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8875) and [#9718](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9718) retain their boundaries |

The approved seven-step order is preserved:

1. **Freeze denominator and authority.** Freeze the six-component/artifact/test inventory, existing authorities and corrected design; reconcile ADR-017. Obtain acknowledgements only for changed contracts/assignments. Native Opus's exact-report design challenge is complete; this committed plan still needs independent exact-head publication review and root's held-out comparison.
2. **Consume existing work.** #8510/#9749 are landed prerequisites. Coordinate forthcoming CI changes with #8875's existing Infra owner, including selection, shards, area lanes and merge-queue measurement, before allocating work. Incorporate #9718's accepted build-reuse evidence without duplication; [#9645](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9645) retains delegate/reaper inventory. Consume landed #9754 for stats. None proves separation implementation.
3. **Qualify owning readers and freshness.** Qualify stats/arc/landing and all shared artifact inputs using producer-derived positive/negative controls. Preserve arc checks and current commands; integrate the stats dependency. Optional manifest-schema hardening remains existing storage/Infra maintenance, not a new migration gate.
4. **Separate preparation from tests.** Remove the implicit unrelated-producer execution at the approved component boundary, specifically `test:unit` → full hydrate (AC-03). Preserve every assertion and immutable artifact set; isolate shared-write tests and integrate #9718's race/build-reuse evidence.
5. **Qualify frontend composition.** Review the smallest route/import seam, all three frontend surfaces, actual missing-input behavior and complete shared integration denominator. Until demonstrated, report shared Astro compilation. This plan does not invent the seam.
6. **Shadow selection under Infra coordination.** Under #8875, compare proposed changed-path selection with the unchanged required test/assertion inventory, including shared inputs, renames/deletions and display freshness invalidation. Only then wire approved commands into existing CI on the already-merged #8510 baseline. Do not create competing CI-speed/selector ownership.
7. **Prove and deliver implementation.** Prove clean-checkout behavior, current freshness/invalidation, real component builds, API/UI and learner outcomes. Obtain exact-head independent cross-family implementation approval, same-head required green CI, merge and common cleanup. Publication/production cutover authority remains separate.

No component is complete merely because a command, receipt or plan exists. Material new decisions stay explicit questions for root; they are not silently adopted while filling an inventory gap.

## 7. Rollback, denominator, measurement and independent proof

Rollback restores previous commands/selection together with their matching immutable artifact/contract sets. Retain prior digests and receipts; never regenerate an “old” output with a new tool and describe it as the prior artifact. Exercise schema/version incompatibility and partial installation. Rollback evidence must still refuse stale display inputs; reverting commands cannot make stale inputs current. No bulk deletion, payload movement or reaper redesign is included.

Freeze the complete collected/required/selected/executed test node IDs and assertion denominator for component and shared integration work before selection changes. Preserve every existing correctness assertion and failure detector, including hydrate-denominator mutation checks and integration tests outside component directories. Independently shadow-check required dependencies against actual selection; unchanged test files alone do not prove coverage. Unknown edges retain current coverage. Shared-write race evidence is a separate required control, not inferred from passing a serial run.

Measurement prior art: [local-ci-replay.md](../docs/best-practices/local-ci-replay.md), inspected lines 67–111, supports local replay; [learner-runtime-and-build-split.md](../docs/architecture/learner-runtime-and-build-split.md), lines 3, 43–51, is **draft prior art**, not adopted authority; [task-quality.md](../docs/best-practices/task-quality.md) provides the existing readiness/delivery contract. The approved report's pyperf references support repeated runs, warmup and distributions; this publication claims no new timing research or measurement.

| Stage | Distinct measurement/proof |
| --- | --- |
| Dependency install | Python/npm installation and cache restore, tool/lockfile identity |
| Preparation/hydration | Retrieval, digest/freshness verification, projections and waits |
| Component build | Component production separately from shared Astro assembly |
| Unit tests | Collected/required/selected/executed IDs and assertions; exclude preparation time |
| Built-output tests | Exact fresh/reused output, HTML/runtime assertions and freshness binding |
| Queue latency | Eligibility/enqueue-to-start, scheduling and landing waits, separate from execution |
| Integration | All six component outcomes and shared artifact/route correctness |

Pre-register repetitions and analysis; retain raw failed and successful observations and privacy-safe environment metadata. Interleave matched baseline/candidate cold, warm-unchanged and invalidation runs. Distinguish dependency, artifact and build caches. Unstable or insufficient comparable data is inconclusive, never a claimed speedup. No fixed-time promise or invented timing is adopted.

Invalidation includes current producer inputs; schemas, tools, config and lockfiles; pointers/member sets; source renames/deletions and same-size changes. Explicit display mutations include canonical stats YAML, arc design/`_arc.yaml`/plans/scope/state/page presence and non-arc landing inputs. Frozen dependency obligations determine required tests. #9718 supplies once-per-stage reuse, unit-parallelism and shared-write race evidence; #8875's Infra owner coordinates baselines, shard/area coverage and queue health; codex-devops integrates them without duplicating implementation or asserting new owner acknowledgement.

Independent held-out proof remains distinct from author examples and approval:

- Root compares the frozen approved report against the committed plan for omissions, verifies a source edge/negative freshness contract not selected by this author, and checks privacy and the one-file diff.
- The driver's separately chosen producer-derived held-out control must retain exact input/output/source evidence. Author probes and the historical 4/4 mechanism observation cannot certify the current migration.
- A resolver-selected qualified native reviewer outside the author family performs toolful exact-pushed-head review. Design/proposal approval and prompt criticism do not replace this gate.
- Actual clean-checkout builds and current-input refusal controls must accompany local learner/API/UI proof for Atlas, practice and curriculum on the merged artifacts. Engine, transport, cache, schema or CI success alone does not prove those outcomes.
- Exact-head CF APPROVE comes before opening a PR; then required CI green on that head, root landing, MERGED confirmation and common branch/worktree cleanup. A moved head requires renewed head-bound evidence. Preserve typed acceptance/behavior evidence and issue hygiene; #9721 stays open until every criterion passes.

Production/public cutover, new infrastructure, paid plans and bulk corpus movement require separately authorized scope. This document author task includes no provider calls, implementation, leases, PR opening, merge/enqueue or issue closeout.

## 8. Six residual groups and stopping rule

These are unresolved work groups, not completed checkboxes. Root/codex-devops owns integration and every residual through the existing authority; no new owner assignment is inferred. Native Opus design approval and stats repair update the historical conditions without removing the broader obligations.

| Residual group | Concrete evidence / next condition | Existing accountable owner / stream |
| --- | --- | --- |
| 1. Contract-owner evidence and changed acknowledgements | Verify exact existing handoff/interface authority; record missing evidence; obtain acceptance only for actual changed obligations or assignments | codex-devops (#5703) through existing domain leads/registered streams |
| 2. Open-model publication binding | Establish exact receipt classification/groups and production exporter→receipt→audit invocation, current-input/release binding and preserved quarantine | codex-devops integrating existing open-model-data authority (#6321) |
| 3. Runtime/shared-artifact completeness and display freshness | Trace ADR-017/runtime/practice/API/readings/cloze/reviewed-source/ZNO edges; qualify all arc/landing dependencies and stale-but-digest-valid controls; consume landed #9754's stats comparison/evidence instead of repeating the repair | codex-devops through existing Atlas/practice (#4387), curriculum and artifact authorities |
| 4. Independent frontend composition | Reviewed minimal route/import seam plus real missing-input behavior, independent builds and shared integration proof for Atlas, practice and curriculum display | codex-devops with existing frontend/domain authorities; no seam or named interface assignment invented |
| 5. Test denominator, measurements and CI-speed coordination | Exact node IDs/assertions, independent shadow selection/freshness controls, shared-write race evidence and comparable six-component cold/warm/invalidation timings; consume #9718, coordinate #8875 on landed #8510 baseline | codex-devops integrating existing Infra claude-infra (#6943/#9737) evidence |
| 6. Independent evaluation and delivery | Design approval is recorded; root's report-to-plan/held-out comparison, exact-head publication CF and all implementation CF/CI/learner proof, landing and hygiene remain required | root/codex-devops (#5703) |

There are six retained residual groups. Publication's bounded live query `gh issue list --state open --search 'in:body "Parent: #5703"' --limit 100 --json number --jq length` returned `19`; this is a search count, not a complete registered-stream census. #9721 is OPEN. Optional storage-manifest schema maintenance stays with storage/Infra; unrelated follow-ups do not become a seventh migration group.

Stop affected work on a digest mismatch, scope beyond the owned deliverable, unresolvable authority contradiction or need for a new material decision. Independent permitted corrections continue. Implementation stops on missing/incompatible/corrupt/stale inputs, lost assertions, unverified freshness, shared-write races, unauthorized actions or absent acknowledgement of an actual changed contract/assignment. Unknown proof is never green.

After two review rounds on an artifact, material contract/freshness/coverage/composition or approval findings still block adoption; recurring new failure classes require changing approach, not lowering requirements. Non-blocking observations retain their documented owner. This plan's publication requires document checks, pushed source, root's held-out evaluation and exact-head outside-family review; it claims no completed migration, implementation percentage or timing.
