### `AWAITING_PRODUCTION_QG_ARMING`

Production QG is never self-armed. Supply one current qualification artifact
from outside the repository to `qg-decision-card`. The card shows the proposed
reviewer family/model/route/lineage, qualification identity, canary, budget,
circuit, resume contract, and deterministic approval id. A human creates a
separate `production-qg-human-arming.v1` artifact with that exact approval id.
Record both with `record-qg-authorization`. The route must be outside every
author family and pass the track's reviewer policy.
