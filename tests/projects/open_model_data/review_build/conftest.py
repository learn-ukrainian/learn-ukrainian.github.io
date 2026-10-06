"""Synthetic-only fixtures. Never open the project's source databases."""

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.contract import Candidate, Citation, Value, digest
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader

STARTS = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima"]


def write_db(path: Path, rows: list[dict], table: str = "units") -> None:
    columns = {
        "id": "INTEGER PRIMARY KEY",
        "source_field": "TEXT",
        "target_field": "TEXT",
        "entry_id": "INTEGER",
        "group_id": "TEXT",
        "source_file": "TEXT",
        "grade": "INTEGER",
        "is_sensitive": "INTEGER",
        "split": "TEXT",
        "document": "TEXT",
        "author": "TEXT",
        "layer": "TEXT",
        "edits": "TEXT",
        "sovietization_risk": "INTEGER",
        "sovietization_keywords": "TEXT",
        "form_key": "TEXT",
        "tags": "TEXT",
        "sol": "TEXT",
        "opus": "TEXT",
        "pair": "TEXT",
    }
    with sqlite3.connect(path) as conn:
        conn.execute(f"CREATE TABLE {table} ({','.join(k + ' ' + v for k, v in columns.items())})")
        for row in rows:
            conn.execute(
                f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", list(row.values())
            )


def selector(area="slots", slot="sentence", **extra):
    return {"area": area, "slot": slot, **extra}


def citation(row: dict, field="source_field", source="synthetic", table="units") -> Citation:
    return Citation(
        source, "sources.db", table, f"id={row['id']}", field, f"SYNTHETIC row {row['id']}", digest(row[field].encode())
    )


def catalog_data(component="C1", operation="sentence_correction") -> dict:
    return {
        "schema_version": "instruction-catalog.v1",
        "version": "1.0.0",
        "status": "reviewed_rb1",
        "components": {
            component: {
                "instructions": [
                    {
                        "id": f"{component}.{operation}.{i:02}",
                        "operation": operation,
                        "template": start + " SYNTHETIC: {sentence}",
                        "slots": ["sentence"],
                    }
                    for i, start in enumerate(STARTS)
                ]
            }
        },
        "prefix_metric": {
            "id": "instruction-prefix.v1-draft",
            "prefix_lengths": [1, 4],
            "top1_max": 0.15,
            "top5_max": 0.6,
        },
        "repetition_metric": {
            "id": "instruction-repetition.v1-draft",
            "ngram_length": 8,
            "whole_template_top1_max": 0.15,
            "whole_template_top5_max": 0.6,
            "suffix_top1_max": 0.6,
            "ngram_record_share_max": 0.6,
        },
    }


def register_data(form="SYNTHETIC source edition 1", sources=("synthetic",)) -> dict:
    return {
        "sources": [
            {"id": source, "citation": {"form": form}, "terms": {"licence": {"name": "SYNTHETIC licence"}}}
            for source in sources
        ]
    }


@pytest.fixture
def bundle(tmp_path):
    rows = [
        {
            "id": i,
            "source_field": f"SYNTHETIC sentence {i}",
            "target_field": f"SYNTHETIC target {i}",
            "entry_id": i,
            "group_id": "SYNTHETIC group",
            "source_file": "SYNTHETIC book",
            "grade": 1,
            "is_sensitive": 0,
            "split": "train",
            "document": f"SYNTHETIC doc {i}",
            "author": f"SYNTHETIC author {i}",
            "layer": "gec-only",
            "edits": '["F/Calque"]',
            "sovietization_risk": 1,
            "sovietization_keywords": "[]",
            "form_key": f"SYNTHETIC target {i}",
            "tags": "SYNTHETIC tags",
        }
        for i in range(1, 13)
    ]
    db = tmp_path / "synthetic.db"
    write_db(db, rows)
    candidates = [
        Candidate(
            "C1",
            str(row["id"]),
            "accepted",
            "ok",
            (),
            "sentence_correction",
            (Value("sentence", row["source_field"], (citation(row),), None, "verbatim"),),
            (),
            (Value("target", row["target_field"], (citation(row, "target_field"),), None, "verbatim"),),
            (),
        )
        for row in rows
    ]
    spec = {
        "unit_id": {
            "primary": [{"selector": selector(), "store": "sources.db", "table": "units", "key": "id"}],
            "separator": ";",
        },
        "unit_query": {"kind": "sql", "store": "sources.db", "sql": "SELECT id FROM units"},
        "frozen_count": 12,
        "unit_grain": "SYNTHETIC unit",
        "annotation_layer": "SYNTHETIC layer",
        "reference_multiplicity": "SYNTHETIC one",
        "reasons": {
            "accepted": ["ok"],
            "rejected": ["synthetic_error"],
            "withheld": ["attribution_unresolved", "locator_unavailable", "catalog_inapplicable", "synthetic_missing"],
            "excluded": ["synthetic_excluded"],
        },
        "operations": ["sentence_correction"],
        "binding": {
            "schema": "binding-spec.v1",
            "rules": [{"op": "same_row", "values": [selector(), selector("response", "target")]}],
        },
    }
    spec["compatibility"] = [
        {
            "store": "sources.db",
            "table": "units",
            "source_id": "synthetic",
            "role": "modern",
            "source_column": "source_file",
            "source_values": ["SYNTHETIC book"],
        }
    ]
    config = {
        "schema": "omd-review-request.v2",
        "databases": {"sources.db": str(db)},
        "ua_gec": {"root": str(tmp_path / "synthetic-ua-gec")},
        "catalog": "catalog.yaml",
        "register": "register.yaml",
        "synthetic_sources": ["synthetic"],
    }
    result = {
        "rows": rows,
        "db": db,
        "candidates": candidates,
        "spec": spec,
        "specs": {"C1": spec},
        "config": config,
        "catalog": catalog_data(),
        "register": register_data(),
        "root": tmp_path,
    }
    save_bundle(result)
    return result


def save_bundle(bundle):
    root = bundle["root"]
    (root / "request.json").write_text(json.dumps(bundle["config"]))
    (root / "catalog.yaml").write_text(yaml.safe_dump(bundle["catalog"]))
    (root / "register.yaml").write_text(yaml.safe_dump(bundle["register"]))


def run_gate(bundle, candidates=None):
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        resolver = Resolver(bundle["register"], {s["id"]: SyntheticAdapter() for s in bundle["register"]["sources"]})
        return Gate(
            reader,
            Catalog(bundle["catalog"]),
            resolver,
            bundle["specs"],
        ).run(bundle["candidates"] if candidates is None else candidates)


def synthetic_components(bundle):
    """Reviewed synthetic specs and streams are supplied in code, never request JSON."""
    return {
        component: SimpleNamespace(
            spec=spec,
            adapters={},
            files={},
            iter_candidates=lambda ctx, component=component: iter(
                c for c in bundle["candidates"] if c.component == component
            ),
        )
        for component, spec in bundle["specs"].items()
    }
