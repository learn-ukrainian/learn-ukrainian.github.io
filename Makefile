PYTHON ?= .venv/bin/python

CURATED_SEED_INPUT ?= .claude/atlas-epic/plans/curated-seed/v5-curated-with-provenance.jsonl
CURATED_SEED_DIR ?= data/lexicon
CURATED_SEED_PUBLIC_SEED := $(CURATED_SEED_DIR)/curated-v5-admission-seed.json
CURATED_SEED_CANDIDATES := $(CURATED_SEED_DIR)/curated-v5-grow-candidates.json
CURATED_SEED_PRACTICE_SEED := $(CURATED_SEED_DIR)/curated-v5-practice-seed.json
CURATED_SEED_REPORT := $(CURATED_SEED_DIR)/curated-v5-admission-report.json

.PHONY: atlas-practice-api-hydrate atlas-export-runtime atlas-local-practice-refresh practice-admit-curated-seed atlas atlas-publish practice-deck practice-deck-publish open-dataset open-dataset-publish

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

practice-admit-curated-seed:
	@test -f "$(CURATED_SEED_INPUT)" || { echo "missing private curated seed input" >&2; exit 2; }
	$(PYTHON) -m scripts.lexicon.curated_seed_atlas_admission --input "$(CURATED_SEED_INPUT)" --public-seed-out "$(CURATED_SEED_PUBLIC_SEED)" --manifest site/src/data/lexicon-manifest.json --candidates-out "$(CURATED_SEED_CANDIDATES)"
	$(PYTHON) -m scripts.lexicon.promote_grow_candidates --candidates "$(CURATED_SEED_CANDIDATES)" --allow-preexisting-conformance --write
	$(PYTHON) scripts/lexicon/enrich_manifest.py --write
	$(PYTHON) -m scripts.lexicon.curated_seed_atlas_admission --input "$(CURATED_SEED_PUBLIC_SEED)" --manifest site/src/data/lexicon-manifest.json --practice-seed-out "$(CURATED_SEED_PRACTICE_SEED)" --report-out "$(CURATED_SEED_REPORT)"
	npm --prefix site run atlas:build-db
	$(PYTHON) scripts/audit/generate_practice_deck.py --practice-seed "$(CURATED_SEED_PRACTICE_SEED)"
	$(MAKE) atlas-local-practice-refresh

atlas:
	$(PYTHON) -m scripts.lexicon.build_data_manifest
	$(PYTHON) scripts/lexicon/enrich_manifest.py
	$(PYTHON) -m scripts.audit.generate_search_index
	$(PYTHON) scripts/lexicon/export_open_dataset.py
	$(PYTHON) -m scripts.audit.generate_daily_pool
	$(PYTHON) scripts/lexicon/verify_manifest.py

atlas-publish: atlas
	$(PYTHON) -m scripts.lexicon.publish_manifest

practice-deck:
	$(PYTHON) scripts/audit/generate_practice_deck.py

practice-deck-publish: practice-deck
	$(PYTHON) scripts/practice_deck/publish.py

open-dataset:
	$(PYTHON) scripts/lexicon/export_open_dataset.py

open-dataset-publish: open-dataset
	$(PYTHON) scripts/open_dataset/publish.py
