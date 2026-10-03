# TOMBSTONE: `components/decolonization` is quarantined

**Status:** SEALED. Do not train, package, evaluate with or upload anything in this directory or its
`data/projects/open_model_data/components/decolonization/` counterpart.
**Sealed:** 2026-10-03 by #9607 (plan v3.4.3, gate PA1). **Parent epic:** #6321. **Set:** `component-decolonization`.

**Reason:** Decolonization component of the withdrawn plan (250 cases, reviews, review sample); plan v3.4.3 PA1 seals it before any component is rebuilt from human sources.

Every file here and in the ignored counterpart is listed with its SHA-256 in
`registry/projects/open_model_data/quarantine/inventory_v1.json`. The files are kept, not deleted.
Loaders refuse this path through `refuse_quarantined` in `scripts/projects/open_model_data/paths.py`;
this file is itself the seal the guard reads.
