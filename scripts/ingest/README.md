# Ingest Scripts

- `esum_ingest.py`: parse the deployed ЕСУМ DjVu plain-text OCR (`data/raw/esum/vol*.txt`).
- `esum_abbyy_parser.py`: parse Internet Archive ABBYY FineReader XML for ЕСУМ vols. 1, 2, 3, and 6 (`data/raw/esum/ia-abbyy-xml/vol*-abbyy.xml` or `.gz`).
- `verify_stem_coverage.py`: read-only live SQLite census for #4593. Reports all-grade STEM source/chunk counts, each source's grade, observed grade 5–11 absences, and both corpus-wide and STEM grade 5–11 FTS hits. Run from a dispatch worktree with the shared interpreter and an explicit live database:

  ```bash
  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.ingest.verify_stem_coverage --db /home/ops/learn-ukrainian/data/sources.db
  ```

  Exit 0 means the census was read, including any gaps; it does not certify curriculum completeness, current editions, or extraction quality. Interpret absent cells against `data/textbook_curriculum_denominator.yaml` (including integrated alternatives and subject start grades). Use `incremental_textbook_ingest.py` with verified retained chunks for ingestion, then rerun this census. A selected book or retained PDF is not evidence of live SQLite ingestion.
