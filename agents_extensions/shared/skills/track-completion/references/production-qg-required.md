### `PRODUCTION_QG_REQUIRED`

Run only the qualified, human-armed live production route and record its strict
`production-qg` artifact. A current PASS satisfies goal `certify`; goal
`deploy` advances to `DEPLOYMENT_REQUIRED`. A material learner finding routes
to `REPAIR_REQUIRED`; malformed/provenance failures route to
`AUDIT_TOOLING_REQUIRED`. Any repair changes identity and therefore requires
fresh PBR, independent review, integration, production QG, and downstream
evidence.
