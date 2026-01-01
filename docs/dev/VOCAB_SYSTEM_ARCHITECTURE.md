# Vocabulary System Architecture (v2: YAML-Based)

## Overview

This document defines the architecture for the "Gold Standard" vocabulary system, utilizing a **YAML-first** approach for data storage.

## Core Hierarchy

1.  **Narrative (`.md`)**: Pure educational content.
2.  **Data (`vocabulary/*.yaml`)**: Structured lexical data.
3.  **Configuration (`meta/*.yaml`)**: Module routing and metadata.

## Workflow Status (Phase 1 Complete)

- **Schema**: Defined in [`docs/dev/VOCAB_YAML_SCHEMA.md`](VOCAB_YAML_SCHEMA.md).
- **Migration**: `scripts/migrate_vocab_to_yaml.py` exists to split MD files.
- **Validation**: `scripts/validate_vocab_yaml.py` exists to enforce the schema.

## Next Steps (Phase 2)

- **Pilot Migration**: Convert A1 modules to this new structure.
- **Pipeline Update**: Update `generate_mdx.py` to consume the new YAML files.

(See Issue #340 and #342 for full details).
