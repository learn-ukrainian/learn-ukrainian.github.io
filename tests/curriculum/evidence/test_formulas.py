"""Synthetic formula matrix; fixture attestations assert no linguistic facts."""

import copy
import json
import sqlite3

import pytest
import yaml

from scripts.build.fresh import assemble, runner
from scripts.curriculum.evidence import formulas, lock, registry, sources, verify, words
from scripts.curriculum.evidence import sense_bindings as bindings
from scripts.curriculum.resolver import inputs, narrow

LEXICAL = [
    {"id": "W-001", "lemma": "привіт", "pos": "noun", "entry": {"source": "vesum", "entry_id": 101}},
    {"id": "W-002", "lemma": "добрий", "pos": "adj", "entry": {"source": "vesum", "entry_id": 102}},
    {"id": "W-003", "lemma": "день", "pos": "noun", "entry": {"source": "vesum", "entry_id": 103}},
]


def formula(single=False, aliases=True):
    record = {
        "id": "W-004",
        "kind": "formula",
        "text": "Привіт!" if single else "Добрий день!",
        "parts": [{"word": "W-001", "form": "Привіт"}]
        if single
        else [{"word": "W-002", "form": "Добрий"}, {"word": "W-003", "form": "день"}],
        "entry": {"source": "formula"},
    }
    if not single and aliases:
        record["aliases"] = ["добридень"]
    record["definition_sha256"] = formulas.definition_digest(record)
    return record


@pytest.fixture
def api(synthetic_sources, synthetic_vesum, monkeypatch):
    monkeypatch.setattr(assemble, "atlas_href_for", lambda *a, **kw: None)
    with sqlite3.connect(synthetic_vesum) as db:
        for index, word in enumerate(LEXICAL, 101):
            db.execute(
                "INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)",
                (index, index, word["lemma"], word["lemma"], word["pos"], word["pos"] + ":v_naz", "", "fixture"),
            )
        db.execute("INSERT INTO forms_all VALUES (104,104,'добридень','добридень','intj','intj','','fixture')")
    with sqlite3.connect(synthetic_sources) as db:
        db.executemany(
            "INSERT INTO dmklinger_uk_en VALUES (?,?,?,?,?,?)",
            [
                (101, "приві́т", "particle", json.dumps(["hello (greeting)", "hi"]), "", "fixture"),
                (
                    102,
                    "добри́день",
                    "phrase",
                    json.dumps(["good day (greeting between sunrise and sunset)"]),
                    "",
                    "fixture",
                ),
                (103, "добри́день", "particle", json.dumps(["hello"]), "", "fixture"),
            ],
        )
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as value:
        yield value


def records(word):
    return {w["id"]: w for w in [*LEXICAL, word]}


def bind(word, api, tmp_path):
    pool = bindings.candidate_list(word, api.formula_rows(word).raw)
    chosen = pool[0]
    b = bindings.formula_binding(word, pool, chosen)
    context = bindings.Context("a1", {word["id"]: b}, [])
    selected = context.select(word, api.formula_rows(word).raw, None)
    return (
        {
            **word,
            "gloss_en": selected.gloss,
            "gloss_source": selected.source,
            "gloss_ref": selected.ref,
            "gloss_basis": selected.basis,
        },
        context,
        pool,
    )


@pytest.mark.parametrize("single,printed", [(True, "Привіт! (hello)"), (False, "Добрий день! (good day)")])
def test_A1_A3_formula_render_no_part_teaching(api, tmp_path, single, printed):
    word = formula(single)
    formulas.validate(word, records(word), api)
    word, context, pool = bind(word, api, tmp_path)
    assert [p["id"] for p in pool] == ([101, 101] if single else [102, 103])
    assert all(set(p) >= {"table", "id", "row_sha256", "span_index", "span", "atom_index"} for p in pool)
    store = {"words": [*LEXICAL, word]}
    assert assemble.render_unit_piece("{{gloss:W-004}}", assemble.gloss_replacer(store)) == printed
    plan = {"inventory": {"vocabulary": {"core": [{"evidence": "W-004"}], "incidental": ["W-004"]}}}
    entries = assemble.build_slovnyk_entries(plan, store)
    assert [wid for wid, _ in entries] == ["W-004"]
    assert entries[0][1]["lemma"] == word["text"]
    assert not any(w.get("first_introduced") for w in LEXICAL)
    assert not narrow.FormIndex(inputs.Allowlist.from_records([word])).usable
    assert not verify.verify_plan_glosses(plan, store, "a1/fixture", api, binding_context=context)


def test_A2_no_alias_candidates_pending_and_pack_gate(api):
    word = formula(aliases=False)
    formulas.validate(word, records(word), api)
    assert api.formula_rows(word).raw == []
    context = bindings.Context("a1", {}, [])
    assert context.select(word, [], None).reason == "formula_binding_missing"
    assert "formula_binding_missing" in " ".join(
        verify.verify_plan_glosses(
            {"inventory": {"vocabulary": {"core": [{"evidence": "W-004"}]}}},
            {"words": [*LEXICAL, word]},
            "a1/fixture",
            api,
            binding_context=context,
        )
    )


@pytest.mark.parametrize(
    "mutation", ["aliases", "text", "parts", "digest", "candidates", "hash", "span_index", "atom_index", "span"]
)
def test_A4_binding_mutations_withheld(api, tmp_path, mutation):
    word, context, _ = bind(formula(), api, tmp_path)
    if mutation == "aliases":
        word["aliases"] = []
    elif mutation == "text":
        word["text"] = "Добрий день."
    elif mutation == "parts":
        word["parts"] = list(reversed(word["parts"]))
    elif mutation == "digest":
        word["definition_sha256"] = "0" * 64
    elif mutation == "candidates":
        context.entries["W-004"]["candidates_sha256"] = "0" * 64
    elif mutation == "hash":
        context.entries["W-004"]["row_sha256"] = "0" * 64
    elif mutation == "span_index":
        context.entries["W-004"]["span_index"] = 9
    elif mutation == "atom_index":
        context.entries["W-004"]["atom_index"] = 9
    else:
        context.entries["W-004"]["span"] = "invented"
    assert context.select(word, api.formula_rows(word).raw, None).reason == "formula_binding_invalid"


def test_A5_deduplicate_formula_and_taught_lexical(api, tmp_path):
    word, _, _ = bind(formula(), api, tmp_path)
    noun = {
        **LEXICAL[2],
        "forms": [{"form": "день", "tags": "noun:v_naz", "stressed": "день", "stress_source": "none", "learner": True}],
    }
    plan = {
        "inventory": {
            "vocabulary": {
                "core": [{"evidence": "W-004"}, {"evidence": "W-003", "forms": ["noun:v_naz"]}],
                "incidental": ["W-004", "W-003", "W-004"],
            }
        }
    }
    entries = assemble.build_slovnyk_entries(plan, {"words": [noun, word]})
    assert [wid for wid, _ in entries] == ["W-004", "W-003"]
    assert entries[1][1]["forms"] == ["день"]
    assert list(narrow.FormIndex(inputs.Allowlist.from_records([noun, word])).usable) == ["день"]


def test_A6_count_rendered_gloss_identically(api, tmp_path):
    word, _, _ = bind(formula(), api, tmp_path)
    expanded = {"units": [{"tab": "urok", "role": "gloss_ref", "text": "{{gloss:W-004}}"}]}
    counted = runner.check_6_count(expanded, 0, {"words": [word]})["details"]
    lexical = {**LEXICAL[0], "id": "W-004", "gloss_en": "good day"}
    lexical_count = runner.check_6_count(expanded, 0, {"words": [lexical]})["details"]
    assert counted["ukrainian_tokens"] == 2
    assert counted["urok_tokens"] - 2 == lexical_count["urok_tokens"] - 1 == 2
    assert (
        assemble.render_unit_piece("{{gloss:W-004}}", assemble.gloss_replacer({"words": [word]}))
        == "Добрий день! (good day)"
    )


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("order", "formula_token_parts_mismatch"),
        ("insert", "formula_token_parts_mismatch"),
        ("delete", "formula_token_parts_mismatch"),
        ("form", "formula_part_form_invalid"),
        ("pin", "formula_part_entry_invalid"),
        ("missing", "formula_part_missing_or_retired"),
        ("retired", "formula_part_missing_or_retired"),
        ("nested", "formula_part_non_lexical"),
        ("cycle", "formula_part_cycle"),
        ("punctuation", "formula_punctuation_invalid"),
        ("alias", "formula_alias_unattested"),
        ("unavailable", "formula_vesum_unavailable"),
    ],
)
def test_token_part_mutations(api, monkeypatch, mutation, reason):
    word = formula()
    store = copy.deepcopy(records(word))
    if mutation == "order":
        word["parts"].reverse()
    elif mutation == "insert":
        word["text"] = "Добрий добрий день!"
    elif mutation == "delete":
        word["text"] = "Добрий!"
    elif mutation == "form":
        store["W-002"]["lemma"] = "день"
        store["W-002"]["pos"] = "noun"
        store["W-002"]["entry"] = {"source": "vesum", "entry_id": 103}
    elif mutation == "pin":
        store["W-002"]["entry"]["entry_id"] = 999
    elif mutation == "missing":
        store.pop("W-002")
    elif mutation == "retired":
        store["W-002"]["retired"] = True
    elif mutation == "nested":
        store["W-002"]["kind"] = "formula"
    elif mutation == "cycle":
        word["parts"][0]["word"] = word["id"]
    elif mutation == "punctuation":
        word["text"] = "Добрий, день!"
    elif mutation == "alias":
        word["aliases"] = ["невідоме"]
    else:
        monkeypatch.setattr(
            api, "inspect_lemma_forms", lambda *a: (_ for _ in ()).throw(ValueError("source_unavailable"))
        )
    with pytest.raises(ValueError, match=reason):
        formulas.validate(word, store, api)


def test_registry_formula_append_only_and_schema(api):
    word = formula()
    ledger_records = []
    for w in LEXICAL:
        assert (
            registry.allocate(
                ledger_records, lemma=w["lemma"], pos=w["pos"], entry=w["entry"], allocated_at_build="frozen"
            )
            == w["id"]
        )
    before = lock.yaml_bytes(ledger_records)
    assert registry.allocate(ledger_records, formula=word, allocated_at_build="frozen") == "W-004"
    assert lock.yaml_bytes(ledger_records[:3]) == before
    registry.check_store(ledger_records, [*LEXICAL, word])
    with pytest.raises(ValueError, match="registry_mismatch"):
        registry.allocate(ledger_records, formula=word, allocated_at_build="frozen")
    with pytest.raises(ValueError, match="registry_mismatch"):
        registry.check_store(ledger_records, [*LEXICAL, {**word, "text": "Добрий день."}])
    registry.retire(ledger_records, "W-004")
    assert (
        registry.allocate(ledger_records, formula={**word, "text": "Добрий день."}, allocated_at_build="frozen")
        == "W-005"
    )
    words.validate_request_data(
        {
            "request_schema": 1,
            "level": "a1",
            "words": [
                {
                    "kind": "formula",
                    "text": word["text"],
                    "parts": [{"lemma": "добрий", "pos": "adj"}, {"lemma": "день", "pos": "noun"}],
                    "want": "new",
                }
            ],
        }
    )


def lexical_request():
    return [{k: w[k] for k in ["lemma", "pos", "entry"]} | {"want": "new"} for w in LEXICAL]


def build(api, root, request, monkeypatch):
    path = root / "request.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump({"request_schema": 1, "level": "a1", "words": request}, allow_unicode=True))
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda form, **kw: {"status": "not_found", "matches": [], "source": {"digest": "a" * 64}},
    )
    return words.build_words("a1", path, evidence_dir=root, sources_instance=api, mcp_commit="f" * 40, stamp=False)


def test_A8_frozen_lexical_baseline_and_formula_build(api, tmp_path, monkeypatch):
    old = build(api, tmp_path / "old", lexical_request(), monkeypatch)
    new = build(api, tmp_path / "new", lexical_request(), monkeypatch)
    assert lock.yaml_bytes(old["store"]) == lock.yaml_bytes(new["store"])
    assert (tmp_path / "old/_words.registry.yaml").read_bytes() == (tmp_path / "new/_words.registry.yaml").read_bytes()
    req = {
        "kind": "formula",
        "text": "Добрий день!",
        "parts": [{"lemma": "добрий", "pos": "adj"}, {"lemma": "день", "pos": "noun"}],
        "aliases": ["добридень"],
        "want": "new",
    }
    added = build(api, tmp_path / "new", [req], monkeypatch)
    lexical = [w for w in added["store"]["words"] if w.get("kind") != "formula"]
    assert lock.yaml_bytes(lexical) == lock.yaml_bytes(old["store"]["words"])
    ledger = registry.load(tmp_path / "new/_words.registry.yaml")
    lexical_ledger = [w for w in ledger if w.get("kind") != "formula"]
    assert lock.yaml_bytes(lexical_ledger) == (tmp_path / "old/_words.registry.yaml").read_bytes()
    assert added["store"]["words"][-1]["gloss_en"] == "good day"
    again = build(api, tmp_path / "new", [req], monkeypatch)
    assert again["store"]["words"] == added["store"]["words"]
    assert len(registry.load(tmp_path / "new/_words.registry.yaml")) == 4
    current = copy.deepcopy(req)
    current["want"] = "W-004"
    current["text"] = "Добрий день."
    with pytest.raises(ValueError, match="formula_identity_changed"):
        build(api, tmp_path / "new", [current], monkeypatch)


def test_builder_strips_stale_formula_gloss(api, tmp_path, monkeypatch):
    root = tmp_path / "build"
    build(api, root, lexical_request(), monkeypatch)
    word, context, _ = bind(formula(), api, tmp_path)
    bindings.write(root / bindings.BINDINGS, "a1", context.entries)
    req = {
        "kind": "formula",
        "text": word["text"],
        "parts": [{"lemma": "добрий", "pos": "adj"}, {"lemma": "день", "pos": "noun"}],
        "aliases": ["добридень"],
        "want": "new",
    }
    valid = build(api, root, [req], monkeypatch)
    assert valid["store"]["words"][-1]["gloss_en"] == "good day"
    req["aliases"] = []
    invalid = build(api, root, [req], monkeypatch)
    assert not any(k.startswith("gloss") for k in invalid["store"]["words"][-1])
    assert next(r for r in invalid["unglossed"] if r["word_id"] == "W-004")["reason"] == "formula_binding_invalid"


def test_A7_formula_binding_preserved_and_checked(api, tmp_path, monkeypatch, capsys):
    from scripts.curriculum.evidence import sense_cli
    from scripts.curriculum.validate import a1_reference

    word, context, _ = bind(formula(single=True), api, tmp_path)
    bindings.write(tmp_path / bindings.BINDINGS, "a1", context.entries)
    before = (tmp_path / bindings.BINDINGS).read_bytes()
    write_locked_fixture(tmp_path, word)
    inventory = tmp_path / "inventory.yaml"
    inventory.write_text("sources: []\n")
    monkeypatch.setattr(a1_reference, "INVENTORY_PATH", inventory)
    monkeypatch.setattr(sources, "Sources", lambda **kw: api)
    monkeypatch.setattr(sense_cli, "tasks_dir", lambda: tmp_path / "tasks")
    monkeypatch.setattr(bindings, "git", lambda repo, *args: b"" if args[0] == "status" else b"a" * 40)
    monkeypatch.setattr(
        sense_cli,
        "leak_scan",
        lambda *a, **k: {"status": "checked", "pr_text": "unverified", "scope": {"kind": "diff"}},
    )
    private = tmp_path / "private.jsonl"
    private.write_text("")
    key = tmp_path / "key"
    key.write_bytes(b"k" * 32)
    args = [
        "a1",
        "--evidence-dir",
        str(tmp_path),
        "--private-input",
        str(private),
        "--key-file",
        str(key),
        "--key-id",
        "fixture",
    ]
    assert sense_cli.main([*args, "--write"]) == 0
    assert (tmp_path / bindings.BINDINGS).read_bytes() == before
    assert sense_cli.main([*args, "--check", "--receipt", str(tmp_path / "receipt")]) == 0
    assert bindings.load(tmp_path / bindings.BINDINGS, "a1") == context.entries
    assert (
        sense_cli.main(["a1", "--evidence-dir", str(tmp_path), "--word", "W-004", "--candidates"], command="bind") == 0
    )
    assert "definition_sha256" in capsys.readouterr().out
    assert (
        sense_cli.main(
            [
                "a1",
                "--evidence-dir",
                str(tmp_path),
                "--word",
                "W-004",
                "--row-id",
                "101",
                "--span-index",
                "0",
            ],
            command="bind",
        )
        == 0
    )
    assert bindings.load(tmp_path / bindings.BINDINGS, "a1") == context.entries


def test_formula_selection_carries_its_basis_and_local_proof(api, tmp_path):
    word, context, _ = bind(formula(), api, tmp_path)
    selected = context.select(word, api.formula_rows(word).raw, None)
    assert selected.basis == {"method": formulas.METHOD, "binding": f"{bindings.BINDINGS}#{word['id']}"}
    binding = context.entries[word["id"]]
    # A coordinate-only formula needs no receipt; one committed to the book does.
    assert bindings.local_proof(binding) is None
    committed = {**binding, "inventory": bindings.INVENTORY, "locator": "p1#1", "commitment": "0" * 64, "key_id": "k"}
    assert bindings.local_proof(committed) == "private_commitment"
    assert bindings.local_proof({"method": bindings.BOOK_METHOD}) == "private_commitment"
    assert bindings.local_proof({"method": "reviewed.v1"}) == "review_provenance"
    assert bindings.local_proof({}) is None


def test_formula_public_verifier_checks_coordinates_without_review(api, tmp_path, monkeypatch):
    build(api, tmp_path, lexical_request(), monkeypatch)
    word, context, _ = bind(formula(), api, tmp_path)
    bindings.write(tmp_path / bindings.BINDINGS, "a1", context.entries)
    req = {
        "kind": "formula",
        "text": word["text"],
        "parts": [{"lemma": "добрий", "pos": "adj"}, {"lemma": "день", "pos": "noun"}],
        "aliases": ["добридень"],
        "want": "new",
    }
    build(api, tmp_path, [req], monkeypatch)
    result = verify.verify_words_store("a1", evidence_dir=tmp_path, plans_dir=tmp_path, sources_instance=api)
    assert not result["errors"], result
    assert not any(w == "W-004: " + bindings.CI_NOTICE for w in result["warnings"])
    assert "W-004:review_provenance" not in result["not_checked"]
    store = yaml.safe_load((tmp_path / "_words.yaml").read_text())
    store["words"][-1]["gloss_en"] = "invented"
    lock.write(tmp_path / "_words.yaml", lock.yaml_bytes(store))
    result = verify.verify_words_store("a1", evidence_dir=tmp_path, plans_dir=tmp_path, sources_instance=api)
    assert any("formula_binding_invalid" in e for e in result["errors"])


@pytest.mark.parametrize("stale", ["hash", "candidates", "definition", "missing_word", "non_formula"])
def test_select_write_skips_stale_formula_binding(api, tmp_path, monkeypatch, capsys, stale):
    from scripts.curriculum.evidence import sense_cli
    from scripts.curriculum.validate import a1_reference

    valid_word, valid_context, _ = bind(formula(single=True), api, tmp_path)
    stale_word = {**formula(), "id": "W-005"}
    _, stale_context, _ = bind(stale_word, api, tmp_path)
    stale_binding = stale_context.entries["W-005"]
    entries = {**valid_context.entries, **stale_context.entries}
    write_locked_fixture(tmp_path, valid_word)
    if stale == "non_formula":
        entries["W-002"] = {**stale_binding, "word": "W-002"}
        entries.pop("W-005")
        stale_id = "W-002"
    else:
        stale_id = "W-005"
        if stale != "missing_word":
            store = yaml.safe_load((tmp_path / "_words.yaml").read_text())
            store["words"].append(stale_word)
            lock.write(tmp_path / "_words.yaml", lock.yaml_bytes(store))
            allocations = registry.load(tmp_path / "_words.registry.yaml")
            assert registry.allocate(allocations, formula=stale_word, allocated_at_build="fixture") == "W-005"
            registry.write(tmp_path / "_words.registry.yaml", allocations)
            field = {"hash": "row_sha256", "candidates": "candidates_sha256", "definition": "definition_sha256"}[stale]
            stale_binding[field] = "0" * 64
    bindings.write(tmp_path / bindings.BINDINGS, "a1", entries)
    before = (tmp_path / bindings.BINDINGS).read_bytes()
    inventory = tmp_path / "inventory.yaml"
    inventory.write_text("sources: []\n")
    monkeypatch.setattr(a1_reference, "INVENTORY_PATH", inventory)
    monkeypatch.setattr(sources, "Sources", lambda **kw: api)
    private = tmp_path / "private.jsonl"
    private.write_text("")
    key = tmp_path / "key"
    key.write_bytes(b"k" * 32)
    args = [
        "a1", "--evidence-dir", str(tmp_path), "--private-input", str(private),
        "--key-file", str(key), "--key-id", "fixture",
    ]
    # Checking remains strict and cannot certify the stale binding.
    assert sense_cli.main([*args, "--check"]) == 1
    assert (tmp_path / bindings.BINDINGS).read_bytes() == before
    capsys.readouterr()
    assert sense_cli.main([*args, "--write"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert {"word": stale_id, "reason": "formula_binding_invalid"} in report["decisions"]
    assert not any("id" in d for d in report["decisions"] if d["word"] == stale_id)
    assert bindings.load(tmp_path / bindings.BINDINGS, "a1") == valid_context.entries
    assert report["resolved"] == 1


def test_non_learner_atoms_and_undeclared_alias_rows_cannot_bind(api):
    word = formula(aliases=False)
    alias_rows = api.formula_rows(formula()).raw
    assert bindings.candidate_list(word, alias_rows) == []
    bad = {
        "id": 200,
        "word": "до́брий день",
        "pos": "phrase",
        "translations": json.dumps(["a " * 40]),
        "text": "",
        "source": "fixture",
    }
    assert bindings.candidate_list(word, [bad]) == []


def test_formula_request_pins_and_ambiguity():
    request = {
        "text": "Привіт!",
        "parts": [{"lemma": "привіт", "pos": "noun", "entry": {"source": "vesum", "entry_id": 999}}],
    }
    with pytest.raises(ValueError, match="formula_part_entry_invalid"):
        formulas.resolve_request(request, {w["id"]: w for w in LEXICAL})
    request["parts"][0].pop("entry")
    duplicate = {**LEXICAL[0], "id": "W-005"}
    with pytest.raises(ValueError, match="formula_part_ambiguous"):
        formulas.resolve_request(request, {w["id"]: w for w in [*LEXICAL, duplicate]})


def test_indirect_formula_cycle(api):
    first = formula()
    second = {**formula(), "id": "W-005"}
    first["parts"][0]["word"] = second["id"]
    second["parts"][0]["word"] = first["id"]
    with pytest.raises(ValueError, match="formula_part_cycle"):
        formulas.validate(first, {first["id"]: first, second["id"]: second}, api)


@pytest.mark.parametrize("text", ["Добрий день!", "Добрий день.", "Добрий день?", "Добрий день…", "Привіт!"])
def test_original_token_text_and_terminal_punctuation(text):
    assert [t.text for t in formulas.tokens(text)] == (["Привіт"] if text.startswith("Привіт") else ["Добрий", "день"])
    assert formulas.printed_headword(text) == ("привіт" if text.startswith("Привіт") else "добрий день")


def write_locked_fixture(root, word):
    lock.write(root / "_words.yaml", lock.yaml_bytes({"level": "a1", "words": [*LEXICAL, word]}))
    allocations = []
    for part in LEXICAL:
        registry.allocate(
            allocations, lemma=part["lemma"], pos=part["pos"], entry=part["entry"], allocated_at_build="fixture"
        )
    registry.allocate(allocations, formula=word, allocated_at_build="fixture")
    registry.write(root / "_words.registry.yaml", allocations)


def test_exact_candidate_spelling_preserves_internal_apostrophes_and_boundaries():
    word = {**formula(single=True), "text": "Сім’я!"}
    rows = [{"id": 1, "word": "сім'я", "pos": "noun", "translations": '["family"]', "text": "", "source": "fixture"}]
    assert bindings.candidate_list(word, rows) == []
    rows[0]["word"] = "сім’я"
    assert len(bindings.candidate_list(word, rows)) == 1
    word = formula(aliases=False)
    rows[0]["word"] = "добрий-день"
    assert bindings.candidate_list(word, rows) == []
    rows[0]["word"] = "добридень"
    assert bindings.candidate_list(word, rows) == []


def test_formula_uses_actual_form_and_pinned_lemma(api, tmp_path, synthetic_vesum):
    # Independent fixture morphology: the inflected token is not a fabricated phrase lemma.
    with sqlite3.connect(synthetic_vesum) as db:
        db.execute("INSERT INTO forms_all VALUES (105,102,'доброго','добрий','adj','adj:m:v_rod','','fixture')")
        db.execute("INSERT INTO forms_all VALUES (106,103,'дня','день','noun','noun:v_rod','','fixture')")
    word = formula()
    word["text"] = "Доброго дня!"
    word["parts"][0]["form"] = "Доброго"
    word["parts"][1]["form"] = "дня"
    word["definition_sha256"] = formulas.definition_digest(word)
    formulas.validate(word, records(word), api)
    word, context, _ = bind(word, api, tmp_path)
    assert word["gloss_en"] == "good day"
    assert context.entries[word["id"]]["method"] == formulas.METHOD


def test_cli_refuses_changed_part_allocation(api, tmp_path, synthetic_vesum):
    from scripts.curriculum.evidence import sense_cli

    with sqlite3.connect(synthetic_vesum) as db:
        db.execute("INSERT INTO forms_all VALUES (105,105,'добрий','добрий','adj','adj:m:v_naz','','fixture')")
    word = formula()
    write_locked_fixture(tmp_path, word)
    store = yaml.safe_load((tmp_path / "_words.yaml").read_text())
    store["words"][1]["entry"]["entry_id"] = 105
    lock.write(tmp_path / "_words.yaml", lock.yaml_bytes(store))
    with pytest.raises(ValueError, match="formula_part_identity_invalid"):
        sense_cli.validate_formula_record(word, store, tmp_path, api)


def test_ulif_pinned_part_and_invalid_pin(api, synthetic_sources):
    with sqlite3.connect(synthetic_sources) as db:
        db.execute("INSERT INTO ulif_dictua_entries VALUES (101,'привіт',1,'приві́т','noun','',1,'ok','fixture')")
    word = formula(single=True)
    store = copy.deepcopy(records(word))
    store["W-001"]["entry"] = {"source": "ulif", "key": ["приві́т", 1]}
    formulas.validate(word, store, api)
    store["W-001"]["entry"]["key"][1] = 2
    with pytest.raises(ValueError, match="formula_part_entry_invalid"):
        formulas.validate(word, store, api)


@pytest.mark.parametrize(
    "meaning,note,expected,reason",
    [
        ("hi", "hello", "hi", "formula_reference_match"),
        ("unmatched fixture", "hi", "hi", "formula_note_match"),
        (None, "hi", "hi", "formula_note_match"),
        (None, "unmatched fixture", "hello", "formula_first_meaning"),
        (" HELLO! ", "hi", "hello", "formula_reference_match"),
        ("Hi! Hello!", "hi", "hello", "formula_reference_match"),
    ],
)
def test_formula_selection_priority(api, meaning, note, expected, reason):
    word = {**formula(single=True), "note": note}
    inventory = [{"lemma": "привіт!", "stressed": "Привіт!", "locator": "fixture#1"}]
    private = {"fixture#1": {"meaning": meaning}} if meaning else {}
    pool = bindings.candidate_list(word, api.formula_rows(word).raw)
    chosen, decision = bindings.choose_formula(word, pool, inventory, private)
    assert chosen["span"] == expected
    assert decision["reason"] == reason
    assert "meaning" not in decision
    binding, decision = bindings.auto_formula_binding(
        word, api.formula_rows(word).raw, inventory, private, b"k" * 32, "fixture"
    )
    assert "reviewer" not in binding
    context = bindings.Context("a1", {word["id"]: binding}, inventory)
    assert context.select(word, api.formula_rows(word).raw, None).gloss == expected
    if reason == "formula_reference_match":
        assert binding["commitment"] == bindings.keyed(private["fixture#1"], b"k" * 32)
        assert binding["locator"] == "fixture#1"
        binding["locator"] = "unrelated#1"
        assert context.select(word, api.formula_rows(word).raw, None).reason == "formula_binding_invalid"
    else:
        assert "commitment" not in binding


def test_builder_pending_formula_keeps_allocation(api, tmp_path, monkeypatch):
    build(api, tmp_path, lexical_request(), monkeypatch)
    req = {
        "kind": "formula",
        "text": "Добрий день!",
        "parts": [{"lemma": "добрий", "pos": "adj"}, {"lemma": "день", "pos": "noun"}],
        "want": "new",
    }
    result = build(api, tmp_path, [req], monkeypatch)
    pending = result["store"]["words"][-1]
    assert pending["id"] == "W-004"
    assert pending["text"] == req["text"]
    assert pending["definition_sha256"] == formulas.definition_digest(pending)
    assert "gloss_en" not in pending
    assert next(r for r in result["unglossed"] if r["word_id"] == "W-004")["reason"] == "formula_binding_missing"
    assert build(api, tmp_path, [req], monkeypatch)["store"]["words"][-1] == pending


def test_formula_binding_wrong_word_and_nonlearner_rejected(api):
    word = formula(single=True)
    rows = api.formula_rows(word).raw
    pool = bindings.candidate_list(word, rows)
    binding = bindings.formula_binding(word, pool, pool[0])
    context = bindings.Context("a1", {"W-004": binding}, [])
    binding["word"] = "W-003"
    assert context.select(word, rows, None).reason == "formula_binding_invalid"
    with pytest.raises(ValueError, match="formula_binding_invalid"):
        bindings.formula_binding(word, pool, {**pool[0], "span": "a " * 40})
    assert (
        bindings.Context("a1", {"W-001": binding}, []).select(LEXICAL[0], rows, None).reason
        == "reference_binding_invalid"
    )


def test_public_candidate_change_invalidates_formula(api, tmp_path):
    word, context, _ = bind(formula(), api, tmp_path)
    rows = api.formula_rows(word).raw
    changed = {
        "id": 201,
        "word": "добридень",
        "pos": "phrase",
        "translations": '["hi"]',
        "text": "",
        "source": "fixture",
    }
    assert context.select(word, [*rows, changed], None).reason == "formula_binding_invalid"


def test_formula_schema_rejects_review_requirement_and_partial_reference(api, tmp_path):
    word, context, _ = bind(formula(), api, tmp_path)
    binding = context.entries[word["id"]]
    bindings.write(tmp_path / bindings.BINDINGS, "a1", context.entries)
    assert bindings.load(tmp_path / bindings.BINDINGS, "a1") == context.entries
    for extra in ({"reviewer": {}}, {"locator": "fixture#1"}):
        bindings.write(tmp_path / bindings.BINDINGS, "a1", {word["id"]: {**binding, **extra}})
        with pytest.raises(ValueError, match="sense_bindings_invalid"):
            bindings.load(tmp_path / bindings.BINDINGS, "a1")


def test_formula_token_classes_and_terminal_whitespace(api):
    for text in ("", "Hello!", "123!", "При2віт!"):
        with pytest.raises(ValueError, match="formula_tokens_invalid"):
            formulas.tokens(text)
    assert formulas.printed_headword("  Привіт!  ") == "привіт"
    assert len(formulas.tokens("  Привіт!  ")) == 1
    assert (
        len(
            bindings.candidate_list(
                {**formula(single=True), "text": "  Привіт!  "}, api.formula_rows(formula(single=True)).raw
            )
        )
        == 2
    )


def test_builder_private_formula_selection_and_keyed_receipt(api, tmp_path, monkeypatch):
    from scripts.curriculum.evidence import sense_cli

    inventory = [{"lemma": "Привіт!", "stressed": "Привіт!", "locator": "fixture#1"}]
    monkeypatch.setattr(
        bindings.Context,
        "read",
        classmethod(
            lambda cls, level, evidence_dir: bindings.Context(
                level, bindings.load(evidence_dir / bindings.BINDINGS, level), inventory
            )
        ),
    )
    private = tmp_path / "private.jsonl"
    private.write_text(json.dumps({"locator": "fixture#1", "inventory_label": "Привіт!", "meaning": "hi"}) + "\n")
    build(api, tmp_path, lexical_request(), monkeypatch)
    request = tmp_path / "formula-request.yaml"
    request.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "kind": "formula",
                        "text": "Привіт!",
                        "parts": [{"lemma": "привіт", "pos": "noun"}],
                        "want": "new",
                        "note": "hello",
                    }
                ],
            },
            allow_unicode=True,
        )
    )
    kwargs = dict(evidence_dir=tmp_path, sources_instance=api, mcp_commit="f" * 40, private_input=private)
    with pytest.raises(ValueError, match="commitment_key_required"):
        words.build_words("a1", request, **kwargs)
    result = words.build_words("a1", request, **kwargs, key=b"k" * 32, key_id="fixture")
    formula_word = result["store"]["words"][-1]
    assert formula_word["gloss_en"] == "hi"
    binding = bindings.load(tmp_path / bindings.BINDINGS, "a1")[formula_word["id"]]
    assert binding["locator"] == "fixture#1"
    assert "commitment" in binding and "reviewer" not in binding
    verification = verify.verify_words_store("a1", evidence_dir=tmp_path, plans_dir=tmp_path, sources_instance=api)
    assert not verification["errors"], verification
    assert "W-004:private_commitment" in verification["not_checked"]
    selected, decisions = sense_cli.select_store(
        result["store"], inventory, bindings.private_entries(private, inventory), api, b"k" * 32, "fixture"
    )
    assert selected[formula_word["id"]] == binding
    assert decisions[-1]["reason"] == "formula_reference_match"
    monkeypatch.setattr(sources, "Sources", lambda **kw: api)
    monkeypatch.setattr(bindings, "git", lambda repo, *args: b"" if args[0] == "status" else b"a" * 40)
    monkeypatch.setattr(sense_cli, "leak_scan", lambda *a, **k: {"status": "checked", "scope": {"kind": "diff"}})
    key_path = tmp_path / "key"
    key_path.write_bytes(b"k" * 32)
    check_args = [
        "a1",
        "--evidence-dir",
        str(tmp_path),
        "--private-input",
        str(private),
        "--key-file",
        str(key_path),
        "--key-id",
        "fixture",
        "--check",
        "--receipt",
        str(tmp_path / "receipt"),
    ]
    assert sense_cli.main(check_args) == 0
    from scripts.curriculum.evidence import pack

    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    (plans_dir / "formula-fixture.yaml").write_text(yaml.safe_dump({"vocabulary": {"core": ["W-004"]}}))
    pack_request = tmp_path / "pack-request.yaml"
    pack_request.write_text(yaml.safe_dump({"request_schema": 1, "module": "a1/formula-fixture"}))
    pack.build_pack("a1", "formula-fixture", pack_request, evidence_dir=tmp_path, sources_instance=api, offline=True)
    verified_pack = verify.verify_pack(
        "a1", "formula-fixture", evidence_dir=tmp_path, plans_dir=plans_dir, sources_instance=api, offline=True
    )
    assert not verified_pack["errors"], verified_pack
    assert "W-004:private_commitment" in verified_pack["not_checked"]
    assert any(bindings.CI_NOTICE in w for w in verified_pack["warnings"])
    binding["commitment"] = "0" * 64
    bindings.write(tmp_path / bindings.BINDINGS, "a1", {formula_word["id"]: binding})
    assert sense_cli.main(check_args) == 1


@pytest.mark.parametrize("text", ["Привіт!", "Приві́т!"])
def test_formula_render_preserves_printed_text(text):
    word = {**formula(single=True), "text": text, "gloss_en": "hello"}
    store = {"words": [word]}
    assert assemble.render_unit_piece("{{gloss:W-004}}", assemble.gloss_replacer(store)) == text + " (hello)"
    plan = {"inventory": {"vocabulary": {"core": [{"evidence": "W-004"}]}}}
    assert assemble.build_slovnyk_entries(plan, store)[0][1]["lemma"] == text
