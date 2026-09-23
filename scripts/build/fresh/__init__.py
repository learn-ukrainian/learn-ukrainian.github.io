"""The create-path build engine for the fresh lesson-based build (#8397 child 6, writer contract #8431 r3).

Part E1: the lesson-draft schema (generated per level from
``schemas/templates/lesson-draft-v1.template.json`` by :mod:`gen_draft_schemas`) and its
validator (:mod:`draft_schema`), plus level-schema additions and style cards under
``docs/style-cards/``.

Part E2: immersion payload (:mod:`immersion`), prompt templates and rendered-prompt check
(:mod:`prompt`), evidence preflight with gap report (:mod:`preflight`), and writer call
dispatch with schema validation (:mod:`writer`), exposed through CLI (:mod:`cli`).

Part E3: assembler, check runner, and module build are the final slice of the brief (#8397 comment 5773128681).
"""
