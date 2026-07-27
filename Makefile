PYTHON ?= .venv/bin/python

ALONA_V5_INPUT ?= .claude/atlas-epic/plans/alona-truth/v5-curated-with-provenance.jsonl
ALONA_V5_DIR ?= data/lexicon
ALONA_V5_PUBLIC_SEED := $(ALONA_V5_DIR)/alona-v5-atlas-admission-seed.json
ALONA_V5_CANDIDATES := $(ALONA_V5_DIR)/grow_candidates.json
ALONA_V5_PRACTICE_SEED := $(ALONA_V5_DIR)/alona-v5-practice-seed.json
ALONA_V5_REPORT := $(ALONA_V5_DIR)/alona-v5-atlas-admission-report.json

.PHONY: alona-v5-admit atlas atlas-publish practice-deck practice-deck-publish open-dataset open-dataset-publish
alona-v5-admit:
	@test -f "$(ALONA_V5_INPUT)" || { echo "missing private Alona v5 input: $(ALONA_V5_INPUT)" >&2; exit 2; }
	$(PYTHON) -m scripts.lexicon.alona_v5_atlas_admission --input "$(ALONA_V5_INPUT)" --public-seed-out "$(ALONA_V5_PUBLIC_SEED)" --manifest site/src/data/lexicon-manifest.json --candidates-out "$(ALONA_V5_CANDIDATES)"
	$(PYTHON) -m scripts.lexicon.promote_grow_candidates --candidates "$(ALONA_V5_CANDIDATES)" --write
	$(PYTHON) scripts/lexicon/enrich_manifest.py --write
	$(PYTHON) -m scripts.lexicon.alona_v5_atlas_admission --input "$(ALONA_V5_PUBLIC_SEED)" --manifest site/src/data/lexicon-manifest.json --practice-seed-out "$(ALONA_V5_PRACTICE_SEED)" --report-out "$(ALONA_V5_REPORT)"
	npm --prefix site run atlas:build-db
	$(PYTHON) scripts/audit/generate_practice_deck.py --practice-seed "$(ALONA_V5_PRACTICE_SEED)"

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
