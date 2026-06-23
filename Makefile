PYTHON ?= .venv/bin/python

.PHONY: atlas atlas-publish
atlas:
	$(PYTHON) -m scripts.lexicon.build_data_manifest
	$(PYTHON) scripts/lexicon/enrich_manifest.py
	$(PYTHON) -m scripts.audit.generate_search_index
	$(PYTHON) scripts/lexicon/export_open_dataset.py
	$(PYTHON) scripts/audit/generate_daily_pool.py
	$(PYTHON) scripts/lexicon/verify_manifest.py

atlas-publish: atlas
	$(PYTHON) scripts/lexicon/publish_manifest.py
