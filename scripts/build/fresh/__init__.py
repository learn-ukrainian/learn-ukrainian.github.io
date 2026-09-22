"""The create-path build engine for the fresh lesson-based build (#8397 child 6, writer contract #8431 r3).

Part E1 (this package's first slice): the lesson-draft schema (generated per level from
``schemas/templates/lesson-draft-v1.template.json`` by :mod:`gen_draft_schemas`) and its
validator (:mod:`draft_schema`), plus the level-schema additions and the style cards under
``docs/style-cards/``. Parts E2 (prompt, preflight, writer call) and E3 (assembler, check
runner, module build) are later slices of the same brief (#8397 comment 5773128681).
"""
