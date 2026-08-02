PYTHON ?= .venv/bin/python

CURATED_SEED_INPUT ?= .claude/atlas-epic/plans/curated-seed/v5-curated-with-provenance.jsonl
CURATED_SEED_DIR ?= data/lexicon
CURATED_SEED_PRACTICE_SEED := $(CURATED_SEED_DIR)/curated-v5-practice-seed.json
CURATED_SEED_REPORT := $(CURATED_SEED_DIR)/curated-v5-admission-report.json
CURATED_SEED_LOCAL_SMOKE_OUT ?= batch_state/curated-v5-local-practice
CURATED_SEED_LOCAL_SMOKE_TARGET ?= 700
CURATED_SEED_GOLD_TARGET ?= 40
CURATED_SEED_GOLD_OUT ?= site/public/lexicon
CURATED_SEED_GOLD_VESUM_DB ?= data/vesum.db
CURATED_MEMBERSHIP ?= site/src/data/lexicon-teacher-curated-membership.json
CURATED_MEMBERSHIP_HOMEWORK ?= .claude/atlas-epic/plans/curated-seed/curated-seed.jsonl
CURATED_MEMBERSHIP_TEACHER ?= site/src/data/lexicon-teacher-cloze.json

.PHONY: atlas-practice-api-hydrate atlas-export-runtime atlas-local-practice-refresh curated-membership practice-admit-curated-seed practice-gold-curated-seed atlas atlas-publish practice-deck practice-deck-publish open-dataset open-dataset-publish

# Refresh practice JSON API copies + /atlas runtime for local/dev word-page CTA.
atlas-practice-api-hydrate:
	cd site && node --experimental-strip-types ./scripts/hydrate-lexicon-api-shards.ts

atlas-export-runtime:
	$(PYTHON) -m scripts.atlas.export_runtime_shards \
	  --db data/atlas.db \
	  --out-dir site/public \
	  --base-path atlas \
	  --deck-dir site/public/lexicon \
	  --verify

atlas-local-practice-refresh: atlas-practice-api-hydrate atlas-export-runtime

# A lemma-only public membership overlay: A is resolved with the existing
# VESUM-attested admission logic, and B contributes exact legacy identifiers
# only. This target never reads or writes teacher sentence bodies.
curated-membership:
	@test -f "$(CURATED_MEMBERSHIP_HOMEWORK)" || { echo "missing private curated homework input" >&2; exit 2; }
	$(PYTHON) -m scripts.lexicon.curated_membership --homework-seed "$(CURATED_MEMBERSHIP_HOMEWORK)" --teacher-inventory "$(CURATED_MEMBERSHIP_TEACHER)" --manifest site/src/data/lexicon-manifest.json --out "$(CURATED_MEMBERSHIP)"

practice-admit-curated-seed:
	@test -f "$(CURATED_SEED_INPUT)" || { echo "missing private curated seed input" >&2; exit 2; }
	$(PYTHON) -m scripts.lexicon.curated_seed_atlas_admission --input "$(CURATED_SEED_INPUT)" --manifest site/src/data/lexicon-manifest.json --practice-seed-out "$(CURATED_SEED_PRACTICE_SEED)" --report-out "$(CURATED_SEED_REPORT)" --allow-missing-routes
	$(PYTHON) scripts/audit/generate_practice_deck.py --manifest site/src/data/lexicon-manifest.json --local-practice-seed "$(CURATED_SEED_PRACTICE_SEED)" --out-dir "$(CURATED_SEED_LOCAL_SMOKE_OUT)" --target "$(CURATED_SEED_LOCAL_SMOKE_TARGET)"

# Local-only vertical slice: these ignored static shards temporarily replace
# hydrated practice shards so the existing /lexicon browser path can smoke them.
# Restore the published local deck afterwards with `npm --prefix site run hydrate:practice`.
practice-gold-curated-seed:
	@test -f "$(CURATED_SEED_INPUT)" || { echo "missing private curated seed input" >&2; exit 2; }
	@test "$(CURATED_SEED_GOLD_TARGET)" -ge 32 && test "$(CURATED_SEED_GOLD_TARGET)" -le 50 || { echo "gold target must be between 32 and 50" >&2; exit 2; }
	@test -f "$(CURATED_SEED_GOLD_VESUM_DB)" || { echo "missing explicit VESUM database for gold slice" >&2; exit 2; }
	$(PYTHON) -m scripts.lexicon.curated_seed_atlas_admission --input "$(CURATED_SEED_INPUT)" --manifest site/src/data/lexicon-manifest.json --practice-seed-out "$(CURATED_SEED_PRACTICE_SEED)" --report-out "$(CURATED_SEED_REPORT)" --allow-missing-routes
	$(PYTHON) scripts/audit/generate_practice_deck.py --manifest site/src/data/lexicon-manifest.json --local-practice-seed "$(CURATED_SEED_PRACTICE_SEED)" --out-dir "$(CURATED_SEED_GOLD_OUT)" --target "$(CURATED_SEED_GOLD_TARGET)" --seed-selection representative --disable-cloze --vesum-db "$(CURATED_SEED_GOLD_VESUM_DB)"

atlas:
	$(PYTHON) -m scripts.lexicon.build_data_manifest --write
	$(PYTHON) scripts/lexicon/enrich_manifest.py --write
	$(PYTHON) -m scripts.audit.generate_search_index
	$(PYTHON) scripts/lexicon/export_open_dataset.py
	$(PYTHON) -m scripts.audit.generate_daily_pool
	$(PYTHON) scripts/lexicon/verify_manifest.py

atlas-publish: atlas
	$(PYTHON) -m scripts.lexicon.publish_manifest

practice-deck:
	$(PYTHON) scripts/audit/generate_practice_deck.py --curated-membership "$(CURATED_MEMBERSHIP)"

practice-deck-publish: practice-deck
	$(PYTHON) scripts/practice_deck/publish.py --curated-membership "$(CURATED_MEMBERSHIP)"

open-dataset:
	$(PYTHON) scripts/lexicon/export_open_dataset.py

open-dataset-publish: open-dataset
	$(PYTHON) scripts/open_dataset/publish.py
