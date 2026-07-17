"""In-worker chunk enrichment using sealed CEFR/relations + side DBs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import canonical_json
from scripts.lexicon.runner.side_db import KaikkiSideDb


def enrich_chunk_payload(payload: dict[str, Any]) -> dict[str, str]:
    """Enrich lemma entries from payload paths; return lemma_id → content hash.

    Imports enrich_manifest lazily after the caller has applied memory limits.
    """
    from scripts.lexicon import enrich_manifest as em
    from scripts.lexicon.runner.phase_cefr import (
        apply_sealed_cefr_to_engine_cache,
        load_sealed_cefr_map,
    )
    from scripts.lexicon.runner.phase_relations import load_closed_relations_by_headword
    from scripts.lexicon.runner.side_db import BallaReverseSideDb, DmklingerSideDb

    entries_path = Path(str(payload["entries_path"]))
    entries = json.loads(entries_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("entries_path must contain a JSON list")

    sources_path = Path(str(payload["sources_db"]))
    conn = sqlite3.connect(f"file:{sources_path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        has_sum11_flags = em._sum11_has_flag_columns(conn)
        sealed_cefr = load_sealed_cefr_map(Path(str(payload["cefr_seal_db"])))
        apply_sealed_cefr_to_engine_cache(sealed_cefr, em._CEFR_ESTIMATE_LEVEL_BY_KEY)

        rel_db = Path(str(payload["relations_seal_db"]))
        pointer_syn = load_closed_relations_by_headword(rel_db, kind="synonym")
        pointer_ant = load_closed_relations_by_headword(rel_db, kind="antonym")
        pointer_hom = load_closed_relations_by_headword(rel_db, kind="homonym")
        pointer_par = load_closed_relations_by_headword(rel_db, kind="paronym")

        # Install side-DB lookups for this process (no whole-table Python indexes).
        balla_path = payload.get("balla_side_db")
        dmk_path = payload.get("dmklinger_side_db")
        kaikki_path = payload.get("kaikki_side_db")
        if balla_path:
            balla = BallaReverseSideDb(Path(str(balla_path)))
            em._install_balla_side_db(balla)
        if dmk_path:
            dmk = DmklingerSideDb(Path(str(dmk_path)))
            em._install_dmklinger_side_db(dmk)
        kaikki = (
            KaikkiSideDb(Path(str(kaikki_path))).as_mapping_proxy()
            if kaikki_path
            else em._load_kaikki_lookup()
        )

        out_dir = Path(str(payload["artifact_dir"]))
        out_dir.mkdir(parents=True, exist_ok=True)
        artifacts: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            lemma = str(entry.get("lemma") or "")
            entry_key = em._canonical_synonym_term(lemma) or ""
            em.enrich_entry(
                entry,
                conn,
                kaikki,
                has_sum11_flags=has_sum11_flags,
                pointer_synonym_relations=pointer_syn.get(entry_key, []),
                pointer_antonym_relations=pointer_ant.get(entry_key, []),
                pointer_homonym_relations=pointer_hom.get(entry_key, []),
                pointer_paronym_relations=pointer_par.get(entry_key, []),
            )
            lemma_id = str(entry.get("url_slug") or lemma)
            digest = hashlib.sha256(canonical_json(entry).encode("utf-8")).hexdigest()
            (out_dir / f"{lemma_id}.json").write_text(
                json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            artifacts[lemma_id] = digest
        return artifacts
    finally:
        conn.close()
