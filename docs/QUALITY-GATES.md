# Quality Gates

CI enforces these gates on every push to `scripts/` or `tests/`.

## Code Complexity (radon CC)

**Gate**: No F-grade functions (CC > 40) in `scripts/`.

```bash
# Check locally
.venv/bin/python -m radon cc scripts/ -n F -s
```

**Known exceptions** (legacy, tracked for decomposition):
- `scripts/pipeline_lib.py:phase_2_content` CC=48

## Maintainability Index (radon MI)

**Gate**: No MI=C files (MI < 10) in `scripts/`.

```bash
# Check locally
.venv/bin/python -m radon mi scripts/ -s | grep " - C "
```

**Known exceptions** (legacy, tracked for decomposition):
- `scripts/pipeline_v5.py` MI=C
- `scripts/pipeline_lib.py` MI=C
- `scripts/yaml_activities.py` MI=C

## Linting (ruff)

**Gate**: Zero ruff violations in `scripts/`.

```bash
.venv/bin/python -m ruff check scripts/
```

## Tests (pytest)

**Gate**: All tests pass (excluding known failures).

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/test_docusaurus_links.py --ignore=tests/test_rag.py
```

**Known exceptions**:
- `test_docusaurus_links.py` — tests Docusaurus paths but we use Starlight
- `test_rag.py` — requires running Qdrant + RAG server

## Current Thresholds

| Metric | Target | Current |
|--------|--------|---------|
| F-grade functions | 0 (excl. legacy) | 1 legacy |
| MI=C files | 0 (excl. legacy) | 3 legacy |
| Test count | 3600+ | 3673 |
| Test coverage | 40% | 40% |
| Ruff violations | 0 | 0 |
