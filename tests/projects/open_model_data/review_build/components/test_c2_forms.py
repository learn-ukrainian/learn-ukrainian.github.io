"""C2 synthetic SQLite fixtures only; no real records or snippets are held here."""

import copy
import json
import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import bindings
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.components import ComponentContext, load_components
from scripts.projects.open_model_data.review_build.components import c2_forms as c2
from scripts.projects.open_model_data.review_build.contract import digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.test_table_layout import POLICY


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(c2, "POLICY", POLICY)
    db = tmp_path / "SYNTHETIC-sources.db"
    vd = tmp_path / "SYNTHETIC-vesum.db"
    with sqlite3.connect(db) as conn:
        conn.executescript("""
        CREATE TABLE ulif_dictua_entries(id INTEGER PRIMARY KEY,normalized_query TEXT, canonical_headword TEXT,
          sense_gloss TEXT,status TEXT,retrieved_at TEXT,raw_response_ref TEXT,response_sha256 TEXT);
        CREATE TABLE ulif_forms(id INTEGER PRIMARY KEY,entry_id INTEGER,form_unstressed TEXT,form_stressed TEXT,
          grammatical_tags TEXT,variant_order INTEGER,marked_asterisk INTEGER,preposition TEXT,unmapped_labels TEXT,
          is_lemma INTEGER,dual_stress_flag INTEGER);
        CREATE TABLE ulif_dictua_sections(id INTEGER PRIMARY KEY,entry_id INTEGER,kind TEXT,source_order INTEGER,payload_json TEXT);
        CREATE TABLE ulif_forms_failures(id INTEGER PRIMARY KEY,entry_id INTEGER,reason TEXT);
        """)
        conn.execute(
            "INSERT INTO ulif_dictua_entries VALUES (1,?,?,?,?,?,?,?)",
            ("synthetic", "synthetic", "", "ok", "SYNTHETIC-date", "SYNTHETIC-ref", digest(b"SYNTHETIC")),
        )
        html = "<table><tr><td>case</td><td>singular</td></tr><tr><td>genitive</td><td>synthetic-a, synthetic-b</td></tr></table>"
        p = {"raw_html": html, "rows": [["case", "singular"], ["genitive", "synthetic-a, synthetic-b"]]}
        conn.execute("INSERT INTO ulif_dictua_sections VALUES (1,1,?,1,?)", ("paradigm", json.dumps(p)))
        for i, text in enumerate(("synthetic-a", "synthetic-b"), 1):
            conn.execute(
                "INSERT INTO ulif_forms VALUES (?,1,?,?,?, ?,0,?,?,0,0)", (i, text, text, '["gen", "s"]', i, "", "[]")
            )
    with sqlite3.connect(vd) as conn:
        conn.executescript(
            "CREATE TABLE forms_all(id INTEGER PRIMARY KEY,word_form TEXT,lemma TEXT,tags TEXT); CREATE TABLE vesum_build_metadata(key TEXT PRIMARY KEY,value TEXT);"
        )
        for i, text in enumerate(("synthetic-a", "synthetic-b"), 1):
            conn.execute("INSERT INTO forms_all VALUES (?,?,?,?)", (i, text, "synthetic", "noun:gen:s"))
        conn.execute("INSERT INTO vesum_build_metadata VALUES (?,?)", ("canonical_jsonl_sha256", digest(b"SYNTHETIC")))
    lock = {
        "schema_version": "vesum-source-lock-v1",
        "release_asset": {"version": "SYNTHETIC-1"},
        "expected": {"canonical_jsonl_sha256": digest(b"SYNTHETIC")},
    }
    lp = tmp_path / c2.LOCK
    lp.parent.mkdir(parents=True)
    lp.write_text(json.dumps(lock))
    spec = copy.deepcopy(c2.SPEC)
    op = spec["operation_specs"]["agreed_form"]
    op["frozen_count"] = 1
    for rule in op["binding"]["rules"]:
        if rule["op"] == "table_binding":
            rule["policy"] = POLICY
        if rule["op"] == "form_agreement":
            rule["tag_projection"] = {
                "vocabulary": ["gen", "s", "p", "m", "f"],
                "separator": ":",
                "ignore_when": {"noun": ["m", "f"]},
            }
        if rule["op"] == "set_query_equal":
            # Keep production query in the separate SQL projection equivalence test.
            rule["queries"][1]["query"]["sql"] = 'SELECT word_form FROM forms_all WHERE lemma=? AND tags="noun:gen:s"'
            rule["queries"][1]["parameters"] = [c2.VESUM_LEMMA]
    monkeypatch.setattr(c2, "projected_tags", lambda tags: set(tags.split(":")) & {"gen", "s", "p"})
    return {"db": db, "vd": vd, "root": tmp_path, "spec": spec}


def update(source, sql, parameters=(), store="db"):
    with sqlite3.connect(source[store]) as conn:
        conn.execute(sql, parameters)


def reader(source):
    return SnapshotReader({c2.STORE: source["db"], c2.VESUM: source["vd"]}, repository_root=source["root"])


def extract(source, r):
    return list(c2.COMPONENT.iter_candidates(ComponentContext(r, {})))


def check(source, r, candidates=None):
    candidate = extract(source, r)[0] if candidates is None else candidates[0]
    bindings.check(candidate, source["spec"]["operation_specs"]["agreed_form"]["binding"], r, {})
    return candidate


def test_accept_all_variants_and_closed_registry(source):
    with reader(source) as r:
        c = check(source, r)
        assert c.outcome == "accepted"
        assert c.unit_id == "1;1"
        assert [v.text for v in c.response] == ["synthetic-a", "synthetic-b"]
        assert all(
            len(v.citations) == 2 and [p.source_id for p in v.citations] == ["ulif", "vesum"] for v in c.response
        )
        assert r.units(c2.UNIT_QUERY) == ["1;1"]
        assert load_components(["C2"])["C2"] is c2.COMPONENT
        assert json.loads(Catalog.rendered_slots(c, source["spec"]["slot_serializers"])["slot"]) == [
            [],
            "genitive",
            ["singular"],
        ]


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("asterisk", "marked_asterisk"),
        ("preposition", "preposition_bound"),
        ("unmapped", "unmapped_labels"),
        ("failed", "failed_entry"),
        ("parse", "parse_error"),
        ("header", "header_unauthenticated"),
        ("lemma", "header_unauthenticated"),
        ("canonical", "lemma_unauthenticated"),
        ("ordering", "source_order_unavailable"),
        ("vesum_missing", "form_set_disagreement"),
        ("vesum_extra", "form_set_disagreement"),
        ("homonym", "homonym_unbridgeable"),
        ("parse_homonym", "parse_error"),
        ("sense", "sense_not_discriminating"),
    ],
)
def test_component_omission_fixtures(source, mutation, reason):
    sql = {
        "asterisk": "UPDATE ulif_forms SET marked_asterisk=1 WHERE id=2",
        "preposition": "UPDATE ulif_forms SET preposition='SYNTHETIC-preposition' WHERE id=2",
        "unmapped": """UPDATE ulif_forms SET unmapped_labels='["SYNTHETIC-unmapped"]' WHERE id=2""",
        "failed": "INSERT INTO ulif_forms_failures VALUES (1,1,'SYNTHETIC-failure')",
        "parse": "UPDATE ulif_dictua_entries SET status='parse_error'",
        "header": "UPDATE ulif_dictua_sections SET payload_json='{}'",
        "lemma": "UPDATE ulif_forms SET is_lemma=1 WHERE id=1",
        "canonical": "UPDATE ulif_dictua_entries SET canonical_headword='SYNTHETIC-other'",
        "ordering": "UPDATE ulif_forms SET variant_order=0 WHERE id=2",
        "vesum_missing": "DELETE FROM forms_all WHERE id=2",
        "vesum_extra": "INSERT INTO forms_all VALUES (3,'synthetic-extra','synthetic','noun:gen:s')",
    }
    if mutation in sql:
        update(source, sql[mutation], store="vd" if mutation.startswith("vesum_") else "db")
    else:
        update(source, "INSERT INTO ulif_dictua_entries VALUES (2,'synthetic','synthetic','','ok','SYNTHETIC','','')")
        if mutation == "parse_homonym":
            update(source, "UPDATE ulif_dictua_entries SET status='parse_error' WHERE id=2")
        elif mutation == "sense":
            update(source, "UPDATE ulif_dictua_entries SET sense_gloss='SYNTHETIC-sense'")
            update(
                source,
                "INSERT INTO ulif_forms SELECT id+2,2,form_unstressed,form_stressed,grammatical_tags,variant_order,marked_asterisk,preposition,unmapped_labels,is_lemma,dual_stress_flag FROM ulif_forms WHERE entry_id=1",
            )
    with reader(source) as r:
        c = extract(source, r)[0]
        assert c.outcome == "withheld" and c.reason == reason
        assert c.evidence


def test_same_homonym_forms_distinct_sense_and_dual_stress(source):
    update(source, "UPDATE ulif_dictua_entries SET sense_gloss='SYNTHETIC-sense-one'")
    update(
        source,
        "INSERT INTO ulif_dictua_entries VALUES (2,'synthetic','synthetic','SYNTHETIC-sense-two','ok','SYNTHETIC','','')",
    )
    update(
        source,
        "INSERT INTO ulif_forms SELECT id+2,2,form_unstressed,form_stressed,grammatical_tags,variant_order,marked_asterisk,preposition,unmapped_labels,is_lemma,dual_stress_flag FROM ulif_forms WHERE entry_id=1",
    )
    update(source, "UPDATE ulif_forms SET dual_stress_flag=1 WHERE id=1")
    with reader(source) as r:
        c = check(source, r)
        assert c.outcome == "accepted" and c.flags == ("dual_stress",)
        assert c.slots[1].text == "SYNTHETIC-sense-one"


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("omit", "binding_set"),
        ("extra", "binding_set"),
        ("order", "binding_set"),
        ("support", "binding_agreement"),
        ("header", "binding_selector"),
        ("wrong_slot", "binding_group"),
    ],
)
def test_independent_bindings_refuse_candidate_mutations(source, mutation, code):
    if mutation == "wrong_slot":
        update(
            source,
            'INSERT INTO ulif_forms SELECT 3,entry_id,form_unstressed,form_stressed,\'["gen","p"]\',variant_order,marked_asterisk,preposition,unmapped_labels,is_lemma,dual_stress_flag FROM ulif_forms WHERE id=2',
        )
    with reader(source) as r:
        c = extract(source, r)[0]
        if mutation == "omit":
            c = replace(c, response=c.response[:1])
        elif mutation == "extra":
            c = replace(c, response=(*c.response, c.response[0]))
        elif mutation == "order":
            c = replace(c, response=c.response[::-1])
        elif mutation == "support":
            c = replace(
                c,
                response=(
                    c.response[0],
                    replace(c.response[1], citations=(c.response[1].citations[0], c.response[0].citations[1])),
                ),
            )
        elif mutation == "header":
            c = replace(c, slots=tuple(replace(v, slot="section_0") if v.slot == "column_0" else v for v in c.slots))
        else:
            # The snapshot is pinned: mutate the citation to a different row's tags instead.
            c = replace(
                c,
                response=(
                    c.response[0],
                    replace(
                        c.response[1],
                        citations=(replace(c.response[1].citations[0], row_key="id=3"), c.response[1].citations[1]),
                    ),
                ),
            )
            code = "binding_group"
        with pytest.raises(BuildError, match=code):
            check(source, r, [c])


def test_real_query_tag_projection_equivalence_on_synthetic_rows(tmp_path):
    db = tmp_path / "SYNTHETIC.db"
    tags = [
        "noun:m:v_rod:s",
        "noun:f:v_rod:s:arch",
        "noun:m:v_rod:p",
        "adj:m:v_rod:s",
        "verb:perf:past:m:s",
        "verb:imperf:past:m:s",
        "adjp:pasv:m:v_rod:s",
    ]
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE forms_all(id INTEGER PRIMARY KEY,lemma TEXT,tags TEXT,word_form TEXT)")
        for i, tag in enumerate(tags):
            c.execute("INSERT INTO forms_all VALUES (?,?,?,?)", (i, "synthetic", tag, f"synthetic-{i}"))
        for slot in (["v_rod", "s"], ["m", "v_rod", "s"], ["past", "m", "s"], ["adjp", "pasv", "m", "v_rod", "s"]):
            raw = json.dumps(slot)
            actual = {
                r[0]
                for r in c.execute("SELECT word_form FROM forms_all v WHERE " + c2.VESUM_MATCH, ("synthetic", raw, raw))
            }
            expected = {f"synthetic-{i}" for i, tag in enumerate(tags) if c2.projected_tags(tag) == set(slot)}
            assert actual == expected


def test_attribution_resolves_held_metadata_and_refuses_placeholder(source):
    with reader(source) as r:
        c = extract(source, r)[0]
        primary = c.response[0].citations[0]
        support = c.response[0].citations[1]
        a = c2.ULIF_ADAPTER.resolve(c2.ULIF_FORM, primary, r.row(primary), r)
        assert "SYNTHETIC-date" in a.bibliography and "(entry reference" not in a.bibliography
        a = c2.VESUM_ADAPTER.resolve(c2.VESUM_FORM, support, r.row(support), r)
        assert "SYNTHETIC-1" in a.bibliography and "<used version>" not in a.bibliography
        assert c2.LOCK in r.repository_config_hashes()
        for adapter, citation in ((c2.ULIF_ADAPTER, primary), (c2.VESUM_ADAPTER, support)):
            with pytest.raises(BuildError, match="attribution_unresolved"):
                adapter.resolve("SYNTHETIC insert bibliography <placeholder>", citation, r.row(citation), r)
    update(source, "UPDATE vesum_build_metadata SET value='SYNTHETIC-wrong'", store="vd")
    with reader(source) as r:
        support = extract(source, r)[0].response[0].citations[1]
        with pytest.raises(BuildError, match="attribution_unresolved"):
            c2.VESUM_ADAPTER.resolve(c2.VESUM_FORM, support, r.row(support), r)


def synthetic_gate(source, r):
    from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
    from scripts.projects.open_model_data.review_build.catalog import Catalog
    from scripts.projects.open_model_data.review_build.gate import Gate
    from tests.projects.open_model_data.review_build.conftest import catalog_data

    cat = catalog_data("C2", "agreed_form")
    for line in cat["components"]["C2"]["instructions"]:
        line["template"] = line["template"].replace("{sentence}", "{lemma} {slot}")
        line["slots"] = ["lemma", "slot"]
        line["sense_variant"] = "without_sense"
    for i in range(12):
        original = cat["components"]["C2"]["instructions"][i]
        cat["components"]["C2"]["instructions"].append(
            {
                **original,
                "id": original["id"] + ".sense",
                "sense_variant": "with_sense",
                "template": original["template"] + " {sense}",
                "slots": ["lemma", "slot", "sense"],
            }
        )
    compat = [
        {
            "store": c2.STORE,
            "table": table,
            "source_id": "ulif",
            "role": "modern",
            "source_column": column,
            "source_values": [text],
        }
        for table, column, text in [
            ("ulif_forms", "preposition", ""),
            ("ulif_dictua_entries", "status", "ok"),
            ("ulif_dictua_sections", "kind", "paradigm"),
        ]
    ]
    compat.append(
        {
            "store": c2.VESUM,
            "table": "forms_all",
            "source_id": "vesum",
            "role": "modern",
            "source_column": "tags",
            "source_values": ["noun:gen:s"],
        }
    )
    register = {
        "sources": [
            {
                "id": s,
                "citation": {"form": "SYNTHETIC bibliography"},
                "terms": {"licence": {"name": "SYNTHETIC licence"}},
            }
            for s in ("ulif", "vesum")
        ]
    }
    resolver = Resolver(register, {s: SyntheticAdapter() for s in ("ulif", "vesum")})
    return Gate(r, Catalog(cat), resolver, {"C2": source["spec"]}, compat)


@pytest.mark.parametrize(
    "mutation,code",
    [
        (None, None),
        ("missing", "missing_unit"),
        ("quote", "quote_mismatch"),
        ("span", "quote_span"),
        ("locator", "empty_locator"),
        ("transform", "unknown_transform"),
        ("unit", "unit_id_mismatch"),
        ("sense", "catalog_inapplicable"),
    ],
)
def test_full_gate_synthetic_accounting_and_must_fail(source, mutation, code):
    with reader(source) as r:
        candidates = extract(source, r)
        c = candidates[0]
        if mutation == "missing":
            candidates = []
        elif mutation == "quote":
            candidates = [replace(c, response=(replace(c.response[0], text="SYNTHETIC-absent"), *c.response[1:]))]
        elif mutation == "span":
            candidates = [replace(c, response=(replace(c.response[0], span=(-1, 2)), *c.response[1:]))]
        elif mutation == "locator":
            v = c.response[0]
            candidates = [
                replace(
                    c,
                    response=(
                        replace(v, citations=(replace(v.citations[0], locator=""), v.citations[1])),
                        *c.response[1:],
                    ),
                )
            ]
        elif mutation == "transform":
            candidates = [
                replace(c, response=(replace(c.response[0], transform="SYNTHETIC-paraphrase"), *c.response[1:]))
            ]
        elif mutation == "unit":
            slots = list(c.slots)
            slots[2] = replace(slots[2], citations=(c.response[1].citations[0],))
            candidates = [replace(c, slots=tuple(slots))]
        elif mutation == "sense":
            # Preserve quotation while pretending the empty source sense is visible.
            gate = synthetic_gate(source, r)
            gate.components["C2"]["operation_specs"]["agreed_form"]["applicability"]["without_sense"][1]["expected"] = [
                0
            ]
            with pytest.raises(BuildError, match=code):
                gate.run(candidates)
            return
        gate = synthetic_gate(source, r)
        if mutation:
            with pytest.raises(BuildError, match=code):
                gate.run(candidates)
        else:
            records, report = gate.run(candidates)
            assert report["accounting"]["C2"]["accepted"] == 1
            assert report["accounting"]["C2"]["counted"] == 1
            assert report["metrics"]["C2.agreed_form"]["status"] == "insufficient_evidence"
            assert json.loads(records[0]["response"]) == ["synthetic-a", "synthetic-b"]
            assert gate.unit_id(c) == c.unit_id


def test_different_homonym_stress_is_not_bridged_by_unstressed_agreement(source):
    update(source, "INSERT INTO ulif_dictua_entries VALUES (2,'synthetic','synthetic','','ok','SYNTHETIC','','')")
    update(
        source,
        "INSERT INTO ulif_forms SELECT id+2,2,form_unstressed,form_stressed||char(769),grammatical_tags,variant_order,marked_asterisk,preposition,unmapped_labels,is_lemma,dual_stress_flag FROM ulif_forms WHERE entry_id=1",
    )
    with reader(source) as r:
        assert extract(source, r)[0].reason == "homonym_unbridgeable"


def test_synthetic_build_verify_and_pinned_config_mutation(source, monkeypatch):
    from types import SimpleNamespace

    import yaml

    from scripts.projects.open_model_data.review_build import output
    from scripts.projects.open_model_data.review_build.__main__ import main
    from scripts.projects.open_model_data.review_build.attribution import SyntheticAdapter

    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    with reader(source) as r:
        gate = synthetic_gate(source, r)
        catalog = gate.catalog.data
        register = {
            "sources": [
                {
                    "id": s,
                    "citation": {"form": "SYNTHETIC bibliography"},
                    "terms": {"licence": {"name": "SYNTHETIC licence"}},
                }
                for s in ("ulif", "vesum")
            ]
        }
        compatibility = list(gate.roles.compatibility.values())
    root = source["root"]
    (root / "catalog.yaml").write_text(yaml.safe_dump(catalog))
    (root / "register.yaml").write_text(yaml.safe_dump(register))
    config = {
        "schema": "omd-review-request.v1",
        "catalog": "catalog.yaml",
        "register": "register.yaml",
        "databases": {c2.STORE: str(source["db"]), c2.VESUM: str(source["vd"])},
        "components": {"C2": {}},
        "compatibility": compatibility,
    }
    (root / "request.json").write_text(json.dumps(config))
    component = SimpleNamespace(
        spec=source["spec"],
        adapters={s: SyntheticAdapter() for s in ("ulif", "vesum")},
        iter_candidates=c2.COMPONENT.iter_candidates,
    )
    args = ["--config", str(root / "request.json"), "--out", str(root / "SYNTHETIC-out"), "--components", "C2"]
    assert main(["build", *args], _test_components={"C2": component}) == 0
    assert main(["verify", *args], _test_components={"C2": component}) == 0
    results = json.loads((root / "SYNTHETIC-out/mutation-fixtures/results.json").read_text())
    assert set(results) == {"absent_quote", "wrong_span", "empty_locator", "missing_unit", "swapped_citation"}
    update(source, "UPDATE ulif_forms SET form_stressed='SYNTHETIC-tampered' WHERE id=1")
    assert main(["verify", *args], _test_components={"C2": component}) == 1


def test_printed_lemma_case_is_preserved_and_matches_the_witness(source):
    update(source, "UPDATE ulif_dictua_entries SET canonical_headword='Synthetic'")
    update(source, "UPDATE forms_all SET lemma='Synthetic'", store="vd")
    with reader(source) as r:
        c = check(source, r)
        assert c.outcome == "accepted" and c.slots[0].text == "Synthetic"


@pytest.mark.parametrize(
    "mutation", ["missing_lock", "invalid_lock", "missing_version", "missing_metadata", "entry_metadata"]
)
def test_unmapped_bibliography_withholds_with_closed_reason(source, mutation):
    if mutation == "missing_lock":
        # Synthetic test-only relocation, never a real source deletion.
        (source["root"] / c2.LOCK).rename(source["root"] / "SYNTHETIC-other-lock.json")
    elif mutation == "invalid_lock":
        (source["root"] / c2.LOCK).write_text("SYNTHETIC-invalid-json")
    elif mutation == "missing_version":
        (source["root"] / c2.LOCK).write_text('{"schema_version":"vesum-source-lock-v1"}')
    elif mutation == "missing_metadata":
        update(source, "DELETE FROM vesum_build_metadata", store="vd")
    else:
        update(source, "UPDATE ulif_dictua_entries SET retrieved_at='' ")
    with reader(source) as r:
        c = extract(source, r)[0]
        citation = c.response[0].citations[0 if mutation == "entry_metadata" else 1]
        adapter = c2.ULIF_ADAPTER if mutation == "entry_metadata" else c2.VESUM_ADAPTER
        form = c2.ULIF_FORM if mutation == "entry_metadata" else c2.VESUM_FORM
        with pytest.raises(BuildError, match="attribution_unresolved"):
            adapter.resolve(form, citation, r.row(citation), r)


def test_absent_expected_and_actual_version_digest_cannot_authenticate(source):
    (source["root"] / c2.LOCK).write_text(
        '{"schema_version":"vesum-source-lock-v1","release_asset":{"version":"SYNTHETIC-1"},"expected":{}}'
    )
    update(source, "DELETE FROM vesum_build_metadata", store="vd")
    with reader(source) as r:
        citation = extract(source, r)[0].response[0].citations[1]
        with pytest.raises(BuildError, match="attribution_unresolved"):
            c2.VESUM_ADAPTER.resolve(c2.VESUM_FORM, citation, r.row(citation), r)


def test_whitespace_only_source_sense_uses_senseless_variant(source):
    update(source, "UPDATE ulif_dictua_entries SET sense_gloss=?", ("\t\n\u2003",))
    with reader(source) as r:
        c = extract(source, r)[0]
        assert c.outcome == "accepted"
        gate = synthetic_gate(source, r)
        assert {gate.catalog.lines[name][1]["sense_variant"] for name in gate.applicable(c)} == {"without_sense"}
        assert len(synthetic_gate(source, r).run([c])[0]) == 1
