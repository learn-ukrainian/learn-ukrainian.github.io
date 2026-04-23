# Decision Journal Index

One-liner per decision. Full details in `decisions.yaml`.

Staleness check: `.venv/bin/python scripts/check_decisions.py`

| ID | Date | Expires | Scope | Status | Title |
|----|------|---------|-------|--------|-------|
| dec-001 | 2026-03-24 | 2026-06-24 | pipeline | active | V6 uses reviewer-as-fixer, not full rewrite |
| dec-002 | 2026-03-26 | 2026-06-26 | content | active | A1 written by Claude, reviewed by Gemini |
| dec-003 | 2026-04-03 | 2026-07-03 | pipeline | active | Cap review fix rounds at 4 with degradation detection |
| dec-004 | 2026-03-28 | 2026-06-28 | architecture | active | Bare slug filenames, no number prefixes |
| dec-005 | 2026-04-03 | 2026-07-03 | tooling | active | Keep gemini-cli, fix dispatch retry logic |
| dec-007 | 2026-04-24 | 2027-04-23 | pipeline | active | Enforce dec-001 at code level — no LLM regeneration during review (ADR-007) |
