# TypeScript Scripts Archive

This directory contains archived TypeScript scripts that have been replaced by Python implementations.

## Retirement Date
2025-12-22

## Reason
Complete migration to Python-based tooling for better maintainability and consistency with the primary pipeline (generate_mdx.py, generate_json.py, audit_module.py, etc.).

## Archived Scripts

### Active Scripts (Replaced)
- `vocab-init.ts` → `scripts/vocab_init.py`

### Legacy Scripts (Unused)
- `generate-mdx.ts` - Replaced by `generate_mdx.py`
- `enrich-activities.ts` - Legacy activity scaffolding
- `generate-exercises.ts` - Legacy exercise templates
- `ci.ts`, `merge-levels.ts`, `migrate-modules.ts`, `preflight.ts`, `scope-validator.ts`

### Library Code
- `lib/` - TypeScript library code (parsers, types, utils)

## Note
These files are kept for historical reference only. All active development uses Python.
