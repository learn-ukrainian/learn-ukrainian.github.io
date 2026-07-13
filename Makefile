PYTHON ?= .venv/bin/python

.PHONY: atlas atlas-publish practice-deck practice-deck-publish open-dataset open-dataset-publish
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
