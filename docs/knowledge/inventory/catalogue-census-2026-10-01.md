# Document and data catalogue census — 2026-10-01

Reviewed census for #9412 AC-01. Every tracked path under `docs/`, `registry/` and
`curriculum/l2-uk-en/evidence/` resolves to exactly one family in
[`catalogue.yaml`](../catalogue.yaml), and every name in the local `data/` directory is
claimed by a logical data-store entry. Inputs: five read-only inventories (tasks
inv-9412-a…e), re-checked against the files, and two design advisories.

## Denominator and reconciliation

Base commit `2476814b25` plus the three files this change adds under `docs/knowledge/`.

| Command (run from the worktree root) | Result |
| --- | ---: |
| `git ls-files -- docs \| wc -l` | 2,120 |
| `git ls-files -- registry \| wc -l` | 1,095 |
| `git ls-files -- curriculum/l2-uk-en/evidence \| wc -l` | 55 |
| Tracked denominator | **3,270** |
| `.venv/bin/python -m scripts.docs.catalogue check --json` → `covered` | 3,270 |
| … `uncovered` / `errors` / ambiguous matches | 0 / 0 / 0 |
| … families / data-store entries / residual paths | 118 / 26 / 31 |
| `check --data-root <primary checkout>/data` → names checked / unmatched | 59 / 0 |

The 2,120 `docs/` files are 2,116 counted by the inventories at `f0c144c5b1`
(949 + 750 + 387 + 30), one decision record merged since
(`docs/decisions/2026-10-01-layerb-entailment-gate-shelved.md`), and this change's
catalogue, schema and census. The 59 local names are the 39 top-level entries of
`data/` (SQLite `-shm`/`-wal` sidecars belong to their database) plus the children
of `data/lexicon/` and `data/projects/`, which are claimed one by one.

### Effective lifecycle by root

| Root | active | archive | superseded | draft | residual | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `docs` | 1,132 | 877 | 61 | 19 | 31 | 2,120 |
| `registry` | 1,044 | 39 | 0 | 12 | 0 | 1,095 |
| `curriculum/l2-uk-en/evidence` | 55 | 0 | 0 | 0 | 0 | 55 |
| **Total** | **2,231** | **916** | **61** | **31** | **31** | **3,270** |

Effective lifecycle is the family default unless a per-path override or a residual entry
applies. 7 paths (`docs/session-state/**`) are catalogued with `content_searchable: false`.
The validator enforces this by ownership: a family that owns any path under a component the
docs inventory excludes (`EXCLUDED_PARTS` in `scripts/docs/docs_inventory.py`) must not be
content-searchable, whatever its glob text says.

## Status vocabulary

The issue's words map onto the existing lifecycle contract
([docs-authority-lifecycle.md](../../architecture/docs-authority-lifecycle.md)); no new
vocabulary is introduced, and "unknown" is never a lifecycle value.

| Issue word | Lifecycle | Rule |
| --- | --- | --- |
| current | `active` | Default for live families. |
| historical | `archive` | Kept for history; no replacement is named. |
| superseded | `superseded` | Requires `superseded_by` (tracked path or `id:<entry>`); the chain must end at `active` or `archive`. |
| — | `draft` | Used only where a file's own header says draft or proposed. |
| unknown | residual list | Path stays in its family for discovery, with an owner and a reason. |

## Families

Files per family sum to the denominator (3,270). Owners are stream keys from
`scripts/config/issue_streams.yaml`. Per-path overrides carry their evidence in the catalogue.

| Family | Kind | Default lifecycle | Owner | Files | Overrides |
| --- | --- | --- | --- | ---: | ---: |
| `docs-entry-map` | doc_family | active | docs-knowledge | 1 | 0 |
| `docs-knowledge-system` | doc_family | active | docs-knowledge | 7 | 0 |
| `corpus-inventory` | doc_family | active | corpus-channels | 1 | 0 |
| `top-level-references` | doc_family | active | infra-harness | 9 | 0 |
| `monitor-api-docs` | doc_family | active | monitor | 3 | 0 |
| `core-lesson-contracts` | doc_family | active | curriculum-upgrade | 5 | 2 |
| `top-level-point-in-time-audits` | evidence | archive | infra-harness | 9 | 0 |
| `top-level-historical-notes` | doc_family | archive | infra-harness | 10 | 1 |
| `architecture-adr` | doc_family | active | infra-harness | 17 | 1 |
| `architecture-research` | evidence | archive | infra-harness | 2 | 0 |
| `architecture-specs` | doc_family | active | infra-harness | 42 | 11 |
| `decisions-journal` | registry | active | infra-harness | 60 | 5 |
| `decisions-pending-and-drafts` | doc_family | active | infra-harness | 2 | 1 |
| `design-docs` | doc_family | active | infra-harness | 9 | 2 |
| `proposals` | doc_family | archive | curriculum-upgrade | 11 | 1 |
| `strategy` | doc_family | active | open-model-data | 2 | 1 |
| `gemma-finetuning-guides` | doc_family | archive | open-model-data | 3 | 1 |
| `best-practices` | doc_family | active | infra-harness | 63 | 3 |
| `runbooks` | doc_family | active | infra-harness | 41 | 0 |
| `runbooks-atlas` | doc_family | active | atlas-practice | 14 | 0 |
| `runbooks-data-foundry` | doc_family | active | open-model-data | 8 | 1 |
| `templates` | doc_family | active | infra-harness | 7 | 0 |
| `bug-autopsies` | doc_family | active | infra-harness | 41 | 0 |
| `small-harness-docs` | doc_family | active | infra-harness | 8 | 0 |
| `legacy-agent-docs` | doc_family | archive | infra-harness | 7 | 2 |
| `ocr-setup-note` | doc_family | archive | infra-harness | 1 | 0 |
| `agent-channels` | registry | active | infra-harness | 5 | 0 |
| `session-state-routers` | doc_family | active | infra-harness | 7 | 0 |
| `handoffs-march-2026` | doc_family | archive | infra-harness | 12 | 0 |
| `token-usage-reports` | generated | archive | infra-harness | 2 | 0 |
| `dispatch-briefs` | doc_family | archive | infra-harness | 302 | 0 |
| `dispatch-briefs-reusable` | doc_family | active | infra-harness | 4 | 0 |
| `dispatch-briefs-upgrade-pilot` | doc_family | superseded | curriculum-upgrade | 3 | 0 |
| `plans` | doc_family | active | infra-harness | 5 | 1 |
| `plans-plan-mode-files` | doc_family | archive | curriculum-upgrade | 26 | 0 |
| `plans-state-standard-gap-analyses` | evidence | archive | curriculum-upgrade | 4 | 0 |
| `plans-atlas-practice` | doc_family | active | atlas-practice | 7 | 1 |
| `ci-program` | doc_family | active | devops | 2 | 0 |
| `hramatka-docs` | doc_family | draft | hramatka | 2 | 0 |
| `epics-fresh-build` | doc_family | active | curriculum-upgrade | 9 | 1 |
| `epics-upgrade-abandoned` | doc_family | superseded | curriculum-upgrade | 6 | 2 |
| `epics-other` | doc_family | active | curriculum-upgrade | 1 | 0 |
| `research-bio-dossiers` | doc_family | active | seminars-bio | 410 | 0 |
| `research-folk-dossiers` | doc_family | active | seminars-folk | 43 | 0 |
| `research-dataset-notes` | doc_family | active | open-model-data | 11 | 2 |
| `research-atlas-session-reports` | evidence | archive | atlas-practice | 8 | 0 |
| `research-retrieval-bakeoff` | evidence | active | infra-harness | 4 | 0 |
| `references-reading-notes` | doc_family | active | infra-harness | 4 | 2 |
| `research-registry` | registry | active | infra-harness | 5 | 0 |
| `references-dobra-forma` | resource_catalogue | active | curriculum-upgrade | 91 | 0 |
| `references-textbook-urls` | registry | active | corpus-channels | 1 | 0 |
| `references-external` | resource_catalogue | archive | infra-harness | 1 | 0 |
| `experiments-and-reboot-references` | evidence | archive | curriculum-upgrade | 8 | 0 |
| `archive` | doc_family | archive | docs-knowledge | 85 | 0 |
| `audits-core` | evidence | archive | core-quality | 34 | 0 |
| `audits-bio` | evidence | archive | seminars-bio | 9 | 2 |
| `audits-bio-lit-cross-reference` | generated | active | seminars-bio | 2 | 0 |
| `audits-folk` | evidence | archive | seminars-folk | 2 | 0 |
| `audits-tooling` | evidence | archive | infra-harness | 4 | 0 |
| `audits-open-model-data` | evidence | active | open-model-data | 1 | 0 |
| `reports-analyses` | evidence | archive | infra-harness | 9 | 0 |
| `reports-oneshot-scripts-and-drafts` | generated | archive | curriculum-upgrade | 18 | 0 |
| `reports-a1-reviews` | evidence | archive | core-quality | 39 | 0 |
| `issues-reports` | evidence | archive | core-quality | 46 | 0 |
| `dev-notes` | doc_family | archive | curriculum-upgrade | 59 | 0 |
| `status-snapshots` | generated | archive | curriculum-upgrade | 23 | 0 |
| `prompts-legacy-orchestrators` | doc_family | superseded | curriculum-upgrade | 39 | 0 |
| `prompts-templates` | doc_family | active | curriculum-upgrade | 5 | 1 |
| `l2en-templates` | doc_family | active | curriculum-upgrade | 34 | 0 |
| `l2en-archive` | doc_family | archive | curriculum-upgrade | 14 | 0 |
| `l2en-live-config` | registry | active | curriculum-upgrade | 4 | 0 |
| `state-standard-2024` | resource_catalogue | active | curriculum-upgrade | 2 | 0 |
| `l2en-generated-plan-snapshots` | generated | archive | curriculum-upgrade | 16 | 0 |
| `l2en-authoring-guidelines` | doc_family | archive | curriculum-upgrade | 12 | 1 |
| `l2en-dobra-forma-and-media` | doc_family | archive | curriculum-upgrade | 7 | 0 |
| `l2en-level-plans-and-proposals` | doc_family | archive | curriculum-upgrade | 49 | 0 |
| `l2-uk-direct-plans` | doc_family | archive | curriculum-upgrade | 8 | 0 |
| `textbook-catalog` | registry | active | corpus-channels | 3 | 0 |
| `textbook-reading-notes` | evidence | archive | atlas-practice | 7 | 0 |
| `style-cards` | registry | active | curriculum-upgrade | 6 | 0 |
| `build-rule-data` | registry | active | curriculum-upgrade | 3 | 0 |
| `pedagogy` | doc_family | active | curriculum-upgrade | 5 | 1 |
| `human-and-exam-eval` | doc_family | active | core-quality | 3 | 0 |
| `content-review-reports` | evidence | archive | core-quality | 2 | 0 |
| `folk-epic-specs` | doc_family | active | seminars-folk | 12 | 0 |
| `bio-epic-queues` | doc_family | active | seminars-bio | 3 | 0 |
| `resources-external-links` | resource_catalogue | active | curriculum-upgrade | 4 | 3 |
| `resources-curated-link-maps` | resource_catalogue | active | curriculum-upgrade | 6 | 0 |
| `resources-scraped-catalogs` | resource_catalogue | active | curriculum-upgrade | 14 | 0 |
| `resources-mapping-reports` | evidence | archive | curriculum-upgrade | 13 | 0 |
| `atlas-word-cards` | doc_family | active | atlas-practice | 21 | 0 |
| `atlas-evidence` | evidence | active | atlas-practice | 5 | 0 |
| `practice-specs` | doc_family | active | atlas-practice | 11 | 0 |
| `practice-residual-evidence` | evidence | active | atlas-practice | 6 | 0 |
| `lexicon-sum11-audit` | evidence | active | atlas-practice | 4 | 0 |
| `poc-designs` | doc_family | active | atlas-practice | 14 | 1 |
| `sources-permissions-register` | registry | active | atlas-practice | 2 | 0 |
| `projects-open-model-data` | doc_family | active | open-model-data | 25 | 9 |
| `projects-foundry-evidence` | evidence | active | open-model-data | 23 | 0 |
| `projects-eval-packages` | doc_family | active | open-model-data | 15 | 0 |
| `projects-qg-quality-gate` | doc_family | active | core-quality | 20 | 1 |
| `projects-fleet-design-memos` | doc_family | active | infra-harness | 5 | 0 |
| `projects-folk-remediation` | doc_family | active | seminars-folk | 1 | 0 |
| `registry-reference-inputs` | registry | active | corpus-channels | 13 | 0 |
| `registry-artifacts` | registry | active | infra-harness | 31 | 0 |
| `registry-storage-migration-notes` | evidence | archive | infra-harness | 6 | 0 |
| `registry-corpus-audit` | evidence | active | corpus-channels | 3 | 0 |
| `registry-corpus-audit-draft-tickets` | doc_family | draft | corpus-channels | 12 | 0 |
| `registry-corpus-channels` | registry | active | corpus-channels | 2 | 0 |
| `registry-lexicon-curation` | registry | active | atlas-practice | 24 | 0 |
| `registry-lexicon-source-inventory` | registry | active | atlas-practice | 259 | 0 |
| `registry-practice` | registry | active | atlas-practice | 12 | 0 |
| `registry-miyklas` | registry | active | curriculum-upgrade | 1 | 0 |
| `registry-open-model-data` | registry | active | open-model-data | 697 | 0 |
| `registry-open-model-data-archive` | registry | archive | open-model-data | 16 | 0 |
| `registry-translations` | registry | archive | curriculum-upgrade | 17 | 0 |
| `registry-ua-gec-gold` | registry | active | core-quality | 2 | 0 |
| `curriculum-evidence-a1` | evidence | active | curriculum-upgrade | 55 | 0 |

## Local data stores

Logical identities and tracked producers only; no host path is recorded. Producer paths are
checked against Git's index. `git ls-files -- data | wc -l` returns 64: the two Hramatka
datasets, the six ESUM volumes, the UA eval payloads and two placeholder files. Those three
stores are marked `local_only: false`, and the validator checks every store's `local_only`
flag against the index; all other stores exist only in the local `data/` directory.

| Store entry | Logical store | Default lifecycle | Owner | Producer |
| --- | --- | --- | --- | --- |
| `data-sources-db` | `data/sources.db` | active | corpus-channels | `scripts/wiki/build_sources_db.py`, `scripts/lexicon/runner/fetch_ulif_homonyms.py` |
| `data-vesum-db` | `data/vesum.db`, `data/vesum.db.bak`, `data/vesum.db.bak.*`, `data/vesum_shadow_v680.db` | active | corpus-channels | `scripts/rag/activate_vesum_db.py`, `scripts/rag/build_vesum_shadow.py` |
| `data-atlas-db` | `data/atlas.db` | active | atlas-practice | `scripts/atlas/atlas_db.py` |
| `data-ulif-dumps` | `data/ulif_dump.db`, `data/ulif_scrape.log` (legacy `data/ulif_dump_all.db` retired #8798) | active | atlas-practice | `scripts/lexicon/tools/dump_ulif.py` (`ulif_dump.db` only; `ulif_dump_all.db` retired) |
| `data-wiki-cache` | `data/wiki_cache.db`, `data/wiki_sources.db` | active | corpus-channels | `scripts/rag/wiki_cache.py` (`wiki_cache.db` only; nothing in `scripts/` names `wiki_sources.db`) |
| `data-empty-comms-placeholders` | `data/comms_plane.db`, `data/fleet_comms.db` | archive | infra-harness | Zero-byte files with no writer in scripts/; the Fleet Comms plane keeps its durable store elsewhere. |
| `data-lexicon-ulif-cache` | `data/lexicon/cache/` | active | atlas-practice | `scripts/lexicon/runner/fetch_ulif_homonyms.py`, `scripts/lexicon/ulif_raw_cache.py`, `scripts/lexicon/enrich_manifest.py` |
| `data-lexicon-slovnyk-cache` | `data/lexicon/slovnyk_cache/` | active | atlas-practice | `scripts/lexicon/enrich_manifest.py`, `scripts/lexicon/migrate_slovnyk_cache_v3.py`, `scripts/lexicon/migrate_slovnyk_cache_v4.py` |
| `data-lexicon-source-inventory` | `data/lexicon/source-inventory/`, `data/lexicon/textbook-end-dictionaries/` | active | atlas-practice | `scripts/practice_deck/end_dictionaries.py` (`textbook-end-dictionaries/` only; no writer of `source-inventory/` in `scripts/`) |
| `data-lexicon-working` | `data/lexicon/intake/`, `data/lexicon/parked/`, `data/lexicon/recovery-audit/`, `data/lexicon/runner_work/`, `data/lexicon/side/`, `data/lexicon/*.json` | active | atlas-practice | `scripts/lexicon/reconcile_calque_clusters.py`, `scripts/lexicon/enrich_manifest.py`, `scripts/lexicon/park_thin_entries.py`, `scripts/lexicon/promote_teacher_lesson_intake.py`, `scripts/lexicon/ohoiko_paired_headword_split.py` |
| `data-open-model-data-payloads` | `data/projects/open_model_data/` | active | open-model-data | `scripts/projects/open_model_data/build_decolonization_cases.py` |
| `data-eval-payloads` | `data/projects/ua_eval_harness/`, `data/projects/ua_open_weight_eval/` | active | open-model-data | `scripts/projects/ua_eval_harness/build_heldout_manifest.py`, `scripts/projects/ua_open_weight_eval/suite_cli.py` |
| `data-textbook-chunks` | `data/textbook_chunks/` | active | corpus-channels | `scripts/rag/extract_text.py` |
| `data-ua-gec` | `data/ua-gec/` | active | corpus-channels | Clone of the upstream UA-GEC project; scripts/audit/ingest_ua_gec_gold.py reads it. |
| `data-artifact-store` | `data/.artifact-store/` | active | infra-harness | `scripts/storage/artifacts.py` |
| `data-backups` | `data/backups/` | active | infra-harness | No writer in `scripts/`: hand-made pre-migration copies and leftover rehearsal sidecars; the Monitor admin router lists and deletes them. |
| `data-backups-staging` | `data/.backup-staging/` | active | infra-harness | `scripts/backup-data.sh` |
| `data-corpus-audit` | `data/corpus_audit/` | active | corpus-channels | `scripts/navsi200_asr_bakeoff.py`, `scripts/navsi200_captions.py` |
| `data-datasets` | `data/datasets/` | active | open-model-data | `scripts/dataset/export_ukrainian_pedagogy_dataset.py`, `scripts/dataset/audit_literary_poltava_candidate.py` |
| `data-processed-esum` | `data/processed/` | active | corpus-channels | `scripts/ingest/esum_abbyy_parser.py` |
| `data-raw-sources` | `data/raw/` | active | corpus-channels | `scripts/etymology/bulk_ocr_gemini.py` (ESUM OCR under `raw/esum/`); the Pravopys 2019 HTML is an artifact group read by `scripts/build/module_memory.py`. |
| `data-references` | `data/references/` | active | corpus-channels | Classified as A-class data by scripts/storage/build_classification_table.py; no writer or reader found in scripts/. |
| `data-ubertext-freq` | `data/ubertext-freq/` | active | corpus-channels | `scripts/rag/convert_phase2.py` |
| `data-youtube-discovery` | `data/youtube_discovery/` | active | corpus-channels | `scripts/crawl/discover_yt_by_pattern.py` |
| `data-native-reviewer-lessons` | `data/native-reviewer-lessons/` | active | atlas-practice | `scripts/navsi200_captions.py` (raw captions); the lesson documents are human-supplied. |
| `data-telemetry` | `data/telemetry/` | active | infra-harness | `scripts/api/telemetry_router.py`, `scripts/audit/check_primary_integrity.py` |

## Residual (lifecycle not yet classified)

| Path | Owner | Why the lifecycle is not classified |
| --- | --- | --- |
| `docs/research/INVESTIGATION_9_VS_10_SCORE_REQUIREMENTS.md` | core-quality | Dated 2026-07-23, no banner; whether the review gate it discusses still applies is unverified. |
| `docs/dispatch-briefs/luna-max-closeout-contract.md` | infra-harness | Reusable brief fragment; whether the Luna closeout contract still matches current routing is unverified. |
| `docs/dispatch-briefs/qg-bakeoff-claude-1x17-sweep.md` | core-quality | Bake-off sweep runbook tied to PRs #4762/#4763; current harness fit unverified. |
| `docs/dispatch-briefs/qg-bakeoff-gemini-1x17-sweep.md` | core-quality | Bake-off sweep runbook tied to PRs #4762/#4763; current harness fit unverified. |
| `docs/dispatch-briefs/qg-bakeoff-gpt-1x17-sweep.md` | core-quality | Bake-off sweep runbook tied to PRs #4762/#4763; current harness fit unverified. |
| `docs/plans/MASTER_ENGINEERING_ROADMAP.md` | infra-harness | July 2026 roadmap with no confirmed status or tracking issue. |
| `docs/plans/GEMMA_FINETUNING_9_PLUS_MASTER_SPECIFICATION.md` | open-model-data | July 2026 spec; its relation to the retired fine-tuning guides is unconfirmed. |
| `docs/plans/primary-text-acquisition-hosting-system.md` | corpus-channels | No status line; whether it is the plan of record for primary-text hosting is unverified. |
| `docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md` | curriculum-upgrade | Own status 'open', tracking issue '#TBD' (April 2026); never confirmed filed. |
| `docs/architecture/ROADMAP-two-track-build-plan.md` | infra-harness | Status 'design agreed, tri-agent confirmation pending' (April 2026); outcome unrecorded. |
| `docs/wiki-rebuild-plan.md` | corpus-channels | Says 'active plan as of 2026-04-18' and scripts/wiki/rebuild.py still reads it; currency unverified. |
| `docs/agent-channels/architecture/context.md` | infra-harness | Bridge code still reads channel contexts while Fleet Comms owns messages; disposition waits on bridge retirement. |
| `docs/agent-channels/content/context.md` | infra-harness | Bridge code still reads channel contexts while Fleet Comms owns messages; disposition waits on bridge retirement. |
| `docs/agent-channels/pipeline/context.md` | infra-harness | Bridge code still reads channel contexts while Fleet Comms owns messages; disposition waits on bridge retirement. |
| `docs/agent-channels/reviews/context.md` | infra-harness | Bridge code still reads channel contexts while Fleet Comms owns messages; disposition waits on bridge retirement. |
| `docs/agent-channels/shared/context.md` | infra-harness | Bridge code still reads channel contexts while Fleet Comms owns messages; disposition waits on bridge retirement. |
| `docs/pedagogy/a1-a2-lesson-construction.md` | curriculum-upgrade | June 2026 standard; overlap with the fresh-build ULP presentation pattern not compared. |
| `docs/pedagogy/a1-a2-core-retrofit-audit.md` | curriculum-upgrade | Retrofit protocol for the old core; relevance to the fresh build not compared. |
| `docs/pedagogy/a1-a2-retrofit-template.md` | curriculum-upgrade | Retrofit template for the old core; relevance to the fresh build not compared. |
| `docs/bio-epic/phase-4-wiki-queue.md` | seminars-bio | Queue says to update status per merged wiki but last changed 2026-06-04; not checked against wiki state. |
| `docs/bio-epic/phase-2-sequence-allocation.yaml` | seminars-bio | No consumer found; whether the allocation is still driven is unverified. |
| `docs/playbooks/anti-hallucination-review-protocol.md` | infra-harness | April 2026 portable protocol; relation to current exact-head review rules unstated. |
| `docs/reference/folk-micro-genres.md` | seminars-folk | Harvested proverbs and riddles are unverified against sources (a sibling audit found fabricated proverbs). |
| `docs/folk-epic/folk-wiki-compile-grounding-register-gap.md` | seminars-folk | Own status 'OPEN finding' (2026-06-12); closure unverified. |
| `docs/folk-epic/phase-folk-queue.md` | seminars-folk | Stage-0 queue (2026-06-06); whether still driven is unverified. |
| `docs/plans/HRAMATKA_APP_PRODUCT_ROADMAP.md` | hramatka | Header calls it the master roadmap (2026-07-24, #5699) but states no draft or accepted status, and no tracked file links to it. |
| `docs/decisions/2026-05-17-clawpatch-adoption.md` | infra-harness | Own status PROPOSED, but commit `25b69074ec` moved it out of `pending/` as signed off. |
| `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` | infra-harness | Own status PROPOSED, but commit `25b69074ec` records its sign-off. |
| `docs/decisions/2026-05-17-unified-evidence-layer-for-judges-ORIGINAL.md` | infra-harness | Own status PROPOSED; moved out of `pending/` as signed off in `25b69074ec`. |
| `docs/decisions/2026-05-17-unified-evidence-layer-for-judges-DECISION.md` | infra-harness | Own status DRAFT awaiting sign-off; added as the signed-off synthesis in `25b69074ec`. |
| `docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md` | core-quality | Own status DRAFT pending review, yet PR #1593 shipped the thresholds in code. |

## Inventory judgements corrected on re-check

At least ten status judgements per inventory were re-read against the files. These changed:

| Inventory claim | Catalogue | Evidence |
| --- | --- | --- |
| `docs/references/dobra-forma/**` historical | active | A CC-licensed textbook copy; having no consumer does not make it historical. |
| `docs/architecture/research/**` replaced by the #9233 bake-off | archive, no successor | Different subject (embedder survey versus retrieval methods). |
| `docs/decisions/*` current throughout | active with 5 overrides | Own SUPERSEDED status lines: two name a successor, three do not (archive). |
| All three `docs/guides/*` superseded | one superseded, two archive | Only the Gemma fine-tuning guide carries a banner and successor. |
| `docs/epics/upgrade-combined-qg-prompt*.md` superseded | archive | No banner and no named successor. |
| `docs/reports/a1_reviews/**` superseded by the review contracts | archive | Old scorecards are evidence; a contract does not replace them. |
| State Standard gap analyses and `docs/dev/**` replaced by fresh-build docs | archive, no successor | The named successors were unconfirmed guesses. |
| `docs/agent-channels/**` superseded | active, all five residual | `scripts/ai_agent_bridge/_channels.py` still reads them. |
| `docs/rules/global-friction.yaml` has no consumer | active | `git grep` finds it in `scripts/pipeline/core.py`. |
| All twelve V5/V6 authoring guidelines superseded | archive; one superseded | Only `ACTIVITY-GUIDELINES.md` is bannered (successor `MODULE-RICHNESS-GUIDELINES-v2.md`). |
| `docs/v5-v3-to-v6-phase-mapping.md` superseded | archive | Shelved by a decision, not replaced by a document. |
| `docs/north-star.md` current | draft | Own header: DRAFT v3.1. Same for `docs/epics/fresh-build-a1-arc.md` (draft r3). |
| `docs/projects/qg-quality-gate/layerb-entailment-gate-design.md` current | archive | Shelved 2026-10-01, after the inventory ran. |
| `docs/pedagogy/**` unknown | active; 1 archive, 3 residual | The commercial-source policy is live; the M1–M7 audit is a dated audit. |
| `docs/agents/AGENT-CAPABILITY-MATRIX.md` and `docs/architecture/ARCHITECTURE.md` historical | superseded | Banners name `agent-activity-matrix.md` and `v7-pipeline.md` as current. |
| `data/raw/pravopys.html` consumer not found | consumer found | `scripts/build/module_memory.py` reads it (artifact group `raw_source`). |
| Slovnyk cache producer "slovnyk fetchers" | named producers | `scripts/lexicon/enrich_manifest.py` and the v3/v4 cache migrations write it; `heritage_classifier.py` only reads it. |

## Draft-marker scan

`.venv/bin/python -m scripts.docs.catalogue draft-scan` reads the first 30 lines of every
content-readable catalogued path from Git's index and looks for draft markers: a heading that starts with
"Draft", an upper-case `DRAFT`, `Status: draft`, `Status: proposed`, `lifecycle: draft`,
"work in progress"/`WIP` and "proposal". `Original status:` lines do not count.

| Measure | Before fixes | After fixes |
| --- | ---: | ---: |
| Paths scanned (one binary file skipped) | 3,269 | 3,269 |
| Paths with a marker | 103 | 103 |
| … resolving to `active` | 52 | 29 |
| … resolving to `draft` / `residual` / `archive` / `superseded` | 12 / 0 / 35 / 4 | 30 / 5 / 35 / 4 |
| `draft` paths with no marker | 2 | 1 |

Both columns predate the scan's privacy gate. The scan now reads only paths that resolve to a
content-searchable family and have no inventory-excluded component; it withholds the 7
session-state router paths unread and reads 3,262 paths (one binary skipped). The marker
counts above are unchanged by the gate (still 103 paths with a marker).

Dispositions of the 23 `active` paths whose marker held:

- **New draft family** `registry-corpus-audit-draft-tickets`: all 12 files under
  `registry/corpus_audit/draft_tickets/` open with `# Draft — Ingest …`.
- **Draft overrides** (own status line): `heritage-attestation-engine.md` and
  `word-atlas-design.md` (front-matter `DRAFT`), `api-ui-improvements-proposal.md`
  (`v1 proposal`), ADR-012 (`Proposed`, also in the ADR index), `SLOVNYK-HUB-LAYERS.md`
  (`proposed implementation standard`), `EXTERNAL_RESOURCES_SCHEMA.md` (`Draft`).
- **Residual**: five decision records whose own status says PROPOSED or DRAFT while their
  history says signed off or shipped (table above).

The remaining 29 `active` hits were each read and are false positives: "proposal" as a data
field or in prose (19, including ten open-model-data contracts, prompts and receipts), "WIP" caps and a
WIP commit (2), an `Original status: DRAFT` line (1), lesson-contract history (1), an ADR
template listing every status (1), and approved, accepted or deferred records that
quote the original proposal (5). The one `draft` path without a marker,
`docs/rules-core-draft-notes.md`, says "draft" in its title and is kept draft. The Hramatka
roadmap, previously draft by family default, has no draft evidence and is now residual; its
family stays draft on the strength of `lesson-document-v1.md` ("Status: DRAFT").

## Store producers re-verified

Each producer script was read for a write to the store it is listed under. Corrections:

| Store entry | Removed (does not write the store) | Added (writes it) |
| --- | --- | --- |
| `data-vesum-db` | — | `scripts/rag/build_vesum_shadow.py` (the shadow database) |
| `data-lexicon-ulif-cache` | `ulif_dictua_store.py` (writes a runner work database through a passed connection) | `scripts/lexicon/ulif_raw_cache.py`, `scripts/lexicon/enrich_manifest.py` |
| `data-lexicon-slovnyk-cache` | `heritage_classifier.py` (reader) | the v3/v4 cache migrations |
| `data-lexicon-source-inventory` | `apply_source_inventory_promotion.py` (reads it, writes the site lexicon manifest) | `scripts/practice_deck/end_dictionaries.py` |
| `data-lexicon-working` | — | `park_thin_entries.py`, `promote_teacher_lesson_intake.py`, `ohoiko_paired_headword_split.py` |
| `data-open-model-data-payloads` | `model_view_exporter.py` (writes only an explicit `--output`) | — |
| `data-textbook-chunks` | `incremental_textbook_ingest.py` (reads the chunks into `sources.db`) | `scripts/rag/extract_text.py` |
| `data-backups-staging` (was one entry with `data/backups/`) | "no current writer" | `scripts/backup-data.sh` stages here; `data/backups/` is now its own active entry, since it holds a pre-migration copy made on 2026-10-01 |
| `data-raw-sources` | — | `scripts/etymology/bulk_ocr_gemini.py` |
| `data-native-reviewer-lessons` | — | `scripts/navsi200_captions.py` |

Partial coverage is stated in `producer_note`: no script writes `ulif_dump_all.db`,
`ulif_scrape.log`, `wiki_sources.db`, `data/lexicon/source-inventory/` or `data/backups/`.
The other 13 store entries were confirmed unchanged.

## Duplicates found

- Exact duplicate blobs in the denominator (`git ls-files -s`, same object id): one pair of
  archived damage reports, and three evidence plan-review manifests stored twice by design
  (content-addressed copy plus the named manifest).
- `docs/resources/external_resources.yaml.backup` and `.truncated` are stray copies of
  `external_resources.yaml` (catalogued as superseded by it).
- Local store copies: `vesum_shadow_v680.db` and the dated VESUM backup beside `vesum.db`;
  the ULIF dumps, `data/lexicon/cache/` and the `sources.db` ULIF tables overlap.
- Planning lives in both `docs/plans/` and `docs/epics/` (the CI plan is in both).
- ADR numbers collide across `docs/architecture/adr/`, `docs/architecture/ADR_0xx_*.md`
  and `docs/decisions/ADR-0xx-*.md`.
- Two evaluation homes (`docs/eval/` and `docs/evaluations/`), and storage topology is
  documented in both `docs/runbooks/` and the rules tree.
- HTML twins duplicate Markdown in `docs/architecture/`, `docs/proposals/` and
  `docs/best-practices/`.

## Gaps found

- **No tool searches inside tracked docs.** The `sources` MCP and `/api/sources/*` cover
  `sources.db` and `vesum.db` only; `/api/knowledge/manifest` is the ADR-011 research
  registry and is disabled by default. The Monitor docs router (`/artifacts/…`) lists and
  serves files but does not search them. Its `docs/resources/podcasts/raw` exclusion matches
  no tracked file, so the ULP episode lists in `raw_lists/` are served but unsearchable.
- **The docs inventory sees part of the denominator.** `scripts/docs/docs_inventory.py`
  reads only `.md/.mdx/.rst/.txt/.adoc` under `docs/` (plus code trees) and skips
  `registry/`, curriculum evidence, session-state and every JSON/YAML resource catalogue
  (765 JSON and 338 YAML files in this denominator).
- **The entry map is incomplete.** `docs/README.md` has zero mentions of `runbooks`,
  `atlas`, `resources`, `style-cards`, `lexicon`, `status`, `folk-epic`, `bio-epic`,
  `epics`, `knowledge`, `research` or `dispatch-briefs`, and still describes the V7 era.
- **No store catalogue existed.** `docs/corpus-inventory.md` covers only `sources.db`
  and its counts (refreshed 2026-07-31) are stale against the live store; `atlas.db`,
  the lexicon caches and the project payloads had no listing and no query surface.
- **Status is mostly implicit.** Of 1,994 tracked Markdown files under `docs/`, 20 have
  front-matter and 9 declare `status` or `lifecycle` in it; elsewhere status lives in prose
  banners or nowhere. The catalogue now records it per family; in-place banners for the
  superseded set are PR 2 scope.
- **Misleading names.** `docs/issues/` holds reports, not GitHub issues;
  `docs/dispatch-queue/` is a frozen May 2026 snapshot; `docs/rules/` is build data, not
  binding rules; `docs/MASTER-PLAN.md` is a March 2026 snapshot.
- **Not yet enforced.** The catalogue check runs report-only in this change; the blocking
  CI test and a scan that maps `data/*.db` literals in `scripts/` to store entries
  arrive with PR 2. The `data/` reconciliation runs only where `data/` exists (not in CI).

## Method and limits

- Coverage, counts and lifecycle distribution come from the validator over Git's index, so
  they are sparse-checkout safe and reproducible from a fresh clone.
- The store-name scan (`store_literals` in `scripts/docs/catalogue.py`, enforced by the
  catalogue check) reads every file Git's index lists under `scripts/`, whatever its
  extension, as the index blob behind the privacy gate. Binary blobs are skipped; an
  unreadable or privacy-withheld file fails the check. A name is
  `data/<segments>.db|.sqlite|.sqlite3|.duckdb`; segments may hold any characters except
  whitespace, controls, quotes, `<>|`, `;&()`, `{}$*?[]` and `\`, plus a backslash-escaped
  space in a shell word and inner spaces inside a single-line quoted span. Comments count.
  Python path joins are read from the AST. Limits: names assembled at run time (f-string
  fields, concatenation, variables, shell expansion, globs) are not literals and rely on the
  producers each store entry declares; a spaced name split across lines or inside
  mismatched quotes can be missed. Re-run on 2026-10-01 over 2,084 text files: 18 store
  names, the same set the Python-only scan found; no new store.
- Store entries record names and producers. Store sizes, row counts and file dates come from
  inventory d and were not re-measured; this census opened no database.
- Lifecycle defaults are family-level judgements; per-file overrides exist only where a file
  states its own status or a successor is named. Paths without evidence are residual.
- Globs use one dialect, shared by the schema (`$defs/glob`, `$defs/storeName`) and the
  validator: literals, `*` and `?` within a segment, and `**` as a whole segment. Character
  classes, braces, empty, `.` and `..` segments are schema errors. A glob whose first segment
  below its tracked root is not literal is a catch-all error. Every brace glob was rewritten as
  an explicit list. The brace-to-list rewrite on its own changed zero path-to-family
  assignments; separately, 12 paths intentionally moved to the new
  `registry-corpus-audit-draft-tickets` family (see the draft-marker scan below).
