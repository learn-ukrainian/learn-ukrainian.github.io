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
| … families / data-store entries / residual paths | 117 / 25 / 25 |
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
| `docs` | 1,143 | 877 | 61 | 14 | 25 | 2,120 |
| `registry` | 1,056 | 39 | 0 | 0 | 0 | 1,095 |
| `curriculum/l2-uk-en/evidence` | 55 | 0 | 0 | 0 | 0 | 55 |
| **Total** | **2,254** | **916** | **61** | **14** | **25** | **3,270** |

Effective lifecycle is the family default unless a per-path override or a residual entry
applies. 7 paths (`docs/session-state/**`) are catalogued with `content_searchable: false`,
matching the docs inventory's privacy exclusion.

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
| `architecture-adr` | doc_family | active | infra-harness | 17 | 0 |
| `architecture-research` | evidence | archive | infra-harness | 2 | 0 |
| `architecture-specs` | doc_family | active | infra-harness | 42 | 11 |
| `decisions-journal` | registry | active | infra-harness | 60 | 5 |
| `decisions-pending-and-drafts` | doc_family | active | infra-harness | 2 | 1 |
| `design-docs` | doc_family | active | infra-harness | 9 | 2 |
| `proposals` | doc_family | archive | curriculum-upgrade | 11 | 1 |
| `strategy` | doc_family | active | open-model-data | 2 | 1 |
| `gemma-finetuning-guides` | doc_family | archive | open-model-data | 3 | 1 |
| `best-practices` | doc_family | active | infra-harness | 63 | 0 |
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
| `resources-external-links` | resource_catalogue | active | curriculum-upgrade | 4 | 2 |
| `resources-curated-link-maps` | resource_catalogue | active | curriculum-upgrade | 6 | 0 |
| `resources-scraped-catalogs` | resource_catalogue | active | curriculum-upgrade | 14 | 0 |
| `resources-mapping-reports` | evidence | archive | curriculum-upgrade | 13 | 0 |
| `atlas-word-cards` | doc_family | active | atlas-practice | 21 | 0 |
| `atlas-evidence` | evidence | active | atlas-practice | 5 | 0 |
| `practice-specs` | doc_family | active | atlas-practice | 11 | 0 |
| `practice-residual-evidence` | evidence | active | atlas-practice | 6 | 0 |
| `lexicon-sum11-audit` | evidence | active | atlas-practice | 4 | 0 |
| `poc-designs` | doc_family | active | atlas-practice | 14 | 0 |
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
| `registry-corpus-audit` | evidence | active | corpus-channels | 15 | 0 |
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
| `data-vesum-db` | `data/vesum.db`, `data/vesum.db.bak`, `data/vesum.db.bak.*`, `data/vesum_shadow_v680.db` | active | corpus-channels | `scripts/rag/activate_vesum_db.py` |
| `data-atlas-db` | `data/atlas.db` | active | atlas-practice | `scripts/atlas/atlas_db.py` |
| `data-ulif-dumps` | `data/ulif_dump_all.db`, `data/ulif_dump.db`, `data/ulif_scrape.log` | active | atlas-practice | `scripts/lexicon/tools/dump_ulif.py` |
| `data-wiki-cache` | `data/wiki_cache.db`, `data/wiki_sources.db` | active | corpus-channels | `scripts/rag/wiki_cache.py` |
| `data-empty-comms-placeholders` | `data/comms_plane.db`, `data/fleet_comms.db` | archive | infra-harness | Zero-byte files with no writer in scripts/; the Fleet Comms plane keeps its durable store elsewhere. |
| `data-lexicon-ulif-cache` | `data/lexicon/cache/` | active | atlas-practice | `scripts/lexicon/runner/fetch_ulif_homonyms.py`, `scripts/lexicon/runner/ulif_dictua_store.py` |
| `data-lexicon-slovnyk-cache` | `data/lexicon/slovnyk_cache/` | active | atlas-practice | `scripts/lexicon/enrich_manifest.py`, `scripts/lexicon/heritage_classifier.py` |
| `data-lexicon-source-inventory` | `data/lexicon/source-inventory/`, `data/lexicon/textbook-end-dictionaries/` | active | atlas-practice | `scripts/audit/apply_source_inventory_promotion.py` |
| `data-lexicon-working` | `data/lexicon/intake/`, `data/lexicon/parked/`, `data/lexicon/recovery-audit/`, `data/lexicon/runner_work/`, `data/lexicon/side/`, `data/lexicon/*.json` | active | atlas-practice | `scripts/lexicon/reconcile_calque_clusters.py`, `scripts/lexicon/enrich_manifest.py` |
| `data-open-model-data-payloads` | `data/projects/open_model_data/` | active | open-model-data | `scripts/projects/open_model_data/model_view_exporter.py`, `scripts/projects/open_model_data/build_decolonization_cases.py` |
| `data-eval-payloads` | `data/projects/ua_eval_harness/`, `data/projects/ua_open_weight_eval/` | active | open-model-data | `scripts/projects/ua_eval_harness/build_heldout_manifest.py`, `scripts/projects/ua_open_weight_eval/suite_cli.py` |
| `data-textbook-chunks` | `data/textbook_chunks/` | active | corpus-channels | `scripts/ingest/incremental_textbook_ingest.py` |
| `data-ua-gec` | `data/ua-gec/` | active | corpus-channels | Clone of the upstream UA-GEC project; scripts/audit/ingest_ua_gec_gold.py reads it. |
| `data-artifact-store` | `data/.artifact-store/` | active | infra-harness | `scripts/storage/artifacts.py` |
| `data-backups-staging` | `data/backups/`, `data/.backup-staging/` | archive | infra-harness | Orphaned migration-rehearsal sidecars and an empty staging directory; no current writer. |
| `data-corpus-audit` | `data/corpus_audit/` | active | corpus-channels | `scripts/navsi200_asr_bakeoff.py`, `scripts/navsi200_captions.py` |
| `data-datasets` | `data/datasets/` | active | open-model-data | `scripts/dataset/export_ukrainian_pedagogy_dataset.py`, `scripts/dataset/audit_literary_poltava_candidate.py` |
| `data-processed-esum` | `data/processed/` | active | corpus-channels | `scripts/ingest/esum_abbyy_parser.py` |
| `data-raw-sources` | `data/raw/` | active | corpus-channels | Raw Pravopys 2019 HTML published as an artifact group (raw_source manifest); scripts/build/module_memory.py reads it. |
| `data-references` | `data/references/` | active | corpus-channels | Classified as A-class data by scripts/storage/build_classification_table.py; no writer or reader found in scripts/. |
| `data-ubertext-freq` | `data/ubertext-freq/` | active | corpus-channels | `scripts/rag/convert_phase2.py` |
| `data-youtube-discovery` | `data/youtube_discovery/` | active | corpus-channels | `scripts/crawl/discover_yt_by_pattern.py` |
| `data-native-reviewer-lessons` | `data/native-reviewer-lessons/` | active | atlas-practice | Human-supplied private lesson documents. |
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
| Slovnyk cache producer "slovnyk fetchers" | named producers | `scripts/lexicon/enrich_manifest.py`, `scripts/lexicon/heritage_classifier.py`. |

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
- Store entries record names and producers. Store sizes, row counts and file dates come from
  inventory d and were not re-measured; this census opened no database.
- Lifecycle defaults are family-level judgements; per-file overrides exist only where a file
  states its own status or a successor is named. Paths without evidence are residual.
