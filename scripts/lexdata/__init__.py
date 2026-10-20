"""Lexical data layer (lexdata) v1: one derived local store, ``data/lexdata.db``.

Design: lexdata layer v1, r3 (§3 store boundaries, §4 L1 schema, §6 generations,
§8 invariants). Parsers emit typed L1 records (``records``); only
``build_store`` writes a generation; ``verify`` checks it before publication;
``generation`` is the read-side boundary that refuses an unpublished or
digest-mismatched generation.
"""
