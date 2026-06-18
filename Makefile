PYTHON ?= .venv/bin/python

.PHONY: atlas
atlas:
	$(PYTHON) -m scripts.lexicon.build_data_manifest
	$(PYTHON) scripts/lexicon/enrich_manifest.py
	$(PYTHON) scripts/lexicon/export_open_dataset.py
	$(PYTHON) scripts/lexicon/verify_manifest.py
