# TOMBSTONE: `decolonization/seeds` is quarantined

**Status:** SEALED. Do not train, package, evaluate with or upload anything in this directory or its
`data/projects/open_model_data/decolonization/seeds/` counterpart.
**Sealed:** 2026-10-03 by #9607 (plan v3.4.3, gate PA1). **Parent epic:** #6321. **Set:** `decolonization-gold-seeds`.

**Reason:** Gold seeds of the v1 decolonization pipeline (150 DPO pairs, 150 trajectories) in the templated reasoning format that #8338 measured as harmful; plan principle P1 forbids written reasoning text.

Every file here and in the ignored counterpart is listed with its SHA-256 in
`registry/projects/open_model_data/quarantine/inventory_v1.json`. The files are kept, not deleted.
Loaders refuse this path through `refuse_quarantined` in `scripts/projects/open_model_data/paths.py`;
this file is itself the seal the guard reads.
