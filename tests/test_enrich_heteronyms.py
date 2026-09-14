"""Unit tests for Word Atlas heteronym disambiguation (scripts/lexicon/enrich_heteronyms.py)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.lexicon import enrich_heteronyms


def test_curated_heteronyms_structure():
    """Curated heteronyms must include all required fields for Word Atlas."""
    for lemma, items in enrich_heteronyms.CURATED_HETERONYMS.items():
        assert len(items) >= 2, f"Expected at least 2 heteronyms for {lemma}"
        heads = [item["headword"] for item in items]
        assert len(set(heads)) == len(heads), f"Duplicate headwords found for {lemma}"
        for item in items:
            assert "headword" in item
            assert "gloss" in item
            assert "short_label" in item
            assert "heritage_status" in item
            assert "distinction_note" in item
            assert "morphology" in item
            assert "pronunciation" in item
            assert "stress" in item


def test_gorod_disambiguation():
    """Verify город vegetable garden is distinguished from archaic город city."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("город")
    assert items is not None
    assert len(items) == 2

    garden, city = items[0], items[1]

    # Sense 0: vegetable garden (A2, modern standard)
    assert garden["headword"] == "горо́д"
    assert garden["cefr"] == "A2"
    assert garden["heritage_status"]["classification"] == "standard"
    assert garden["pronunciation"]["ipa"] == "[ɦɔˈrɔd]"
    assert garden["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "горо́ду"
    assert garden["morphology"]["paradigm"]["cases"]["місцевий"]["singular"] == "на горо́ді / горо́ду"
    assert "місто" not in garden["sections"]["synonyms"]["items"]
    assert "грядка" in garden["sections"]["synonyms"]["items"]

    # Sense 1: archaic city
    assert city["headword"] == "го́род"
    assert city["heritage_status"]["classification"] == "authentic-archaism"
    assert city["heritage_status"]["warning_severity"] == "treasured"
    assert city["pronunciation"]["ipa"] == "[ˈɦɔrɔd]"
    assert "місто" in city["sections"]["synonyms"]["items"]


def test_zamok_disambiguation():
    """Verify замок castle vs lock disambiguation."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("замок")
    assert items is not None
    assert len(items) == 2

    castle, lock = items[0], items[1]

    assert castle["headword"] == "за́мок"
    assert castle["pronunciation"]["ipa"] == "[ˈzamɔk]"
    assert castle["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "за́мку"
    assert "фортеця" in castle["sections"]["synonyms"]["items"]

    assert lock["headword"] == "замо́к"
    assert lock["pronunciation"]["ipa"] == "[zɐˈmɔk]"
    assert lock["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "замка́"
    assert "колодка" in lock["sections"]["synonyms"]["items"]


def test_atlas_disambiguation():
    """Verify атлас maps collection vs satin fabric disambiguation."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("атлас")
    assert items is not None
    assert len(items) == 2

    maps, satin = items[0], items[1]

    assert maps["headword"] == "а́тлас"
    assert maps["pronunciation"]["ipa"] == "[ˈatɫɐs]"
    assert maps["short_label"] == "збірник карт"
    assert "збірник карт" in maps["sections"]["synonyms"]["items"]

    assert satin["headword"] == "атла́с"
    assert satin["pronunciation"]["ipa"] == "[ɐtˈɫas]"
    assert satin["short_label"] == "тканина"
    assert "шовк" in satin["sections"]["synonyms"]["items"]


def test_sum11_parsing():
    """Verify regex extraction of heteronyms from multi-headword СУМ-11 text."""
    sample_text = (
        "А́ТЛАС, у, ч. Укладений за певною системою збірник карт.\n"
        "АТЛА́С, у, ч. Шовкова або напівшовкова тканина, блискуча з лиця."
    )
    parsed = enrich_heteronyms.parse_sum11_heteronyms("атлас", sample_text)
    assert len(parsed) == 2
    assert parsed[0]["head"] == "А́ТЛАС"
    assert "збірник карт" in parsed[0]["body"]
    assert parsed[1]["head"] == "АТЛА́С"
    assert "Шовкова" in parsed[1]["body"]


def test_apply_heteronyms_to_db(tmp_path: Path):
    """Verify apply_heteronyms updates SQLite database properly for all heteronym lemmas."""
    db_path = tmp_path / "test_atlas.db"
    dummy_manifest = tmp_path / "empty_manifest.json"
    dummy_manifest.write_text("{}", encoding="utf-8")

    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE article_payloads (
            slug TEXT PRIMARY KEY,
            route_order INTEGER,
            payload_json TEXT NOT NULL,
            is_public_route INTEGER NOT NULL DEFAULT 1
        )"""
    )
    conn.execute(
        """CREATE TABLE articles (
            slug TEXT PRIMARY KEY,
            display_head TEXT NOT NULL,
            pos TEXT,
            gloss TEXT,
            heritage_classification TEXT
        )"""
    )

    initial_records = [
        ("город", "город", "vegetable garden", "authentic-archaism", {"items": ["місто"]}),
        ("замок", "замок", "castle / lock", "standard", {"items": ["палац"]}),
        ("атлас", "атлас", "atlas / satin", "standard", None),
    ]
    for slug, head, gloss, heritage, syns in initial_records:
        sec = {"synonyms": syns} if syns else {}
        p = {"lemma": slug, "url_slug": slug, "gloss": gloss, "heritage_status": {"classification": heritage}, "sections": sec}
        conn.execute("INSERT INTO article_payloads VALUES (?, 1, ?, 1)", (slug, json.dumps(p)))
        conn.execute("INSERT INTO articles VALUES (?, ?, 'noun', ?, ?)", (slug, head, gloss, heritage))
    conn.commit()
    conn.close()

    counts = enrich_heteronyms.apply_heteronyms(
        db_path=db_path, manifest_path=dummy_manifest, lemmas=["город", "замок", "атлас"]
    )
    assert counts["db_payloads"] == 3
    assert counts["db_articles"] == 3

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Verify город
    g_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'город'").fetchone()
    assert g_row is not None
    g_payload = json.loads(g_row[0])
    assert len(g_payload["heteronyms"]) == 2
    assert g_payload["heteronyms"][0]["headword"] == "горо́д"
    assert g_payload["display_head"] == "горо́д"
    assert g_payload["heritage_status"]["classification"] == "standard"
    assert g_payload["sections"]["synonyms"]["items"] == ["грядка", "городчик"]

    # Verify замок
    z_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'замок'").fetchone()
    assert z_row is not None
    z_payload = json.loads(z_row[0])
    assert len(z_payload["heteronyms"]) == 2
    assert z_payload["display_head"] == "за́мок"
    assert "фортеця" in z_payload["sections"]["synonyms"]["items"]
    z_art = cur.execute("SELECT display_head, gloss FROM articles WHERE slug = 'замок'").fetchone()
    assert z_art == ("за́мок", "castle, fortress, palace")

    # Verify атлас
    a_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'атлас'").fetchone()
    assert a_row is not None
    a_payload = json.loads(a_row[0])
    assert len(a_payload["heteronyms"]) == 2
    assert a_payload["display_head"] == "а́тлас"
    assert "збірник карт" in a_payload["sections"]["synonyms"]["items"]
    a_art = cur.execute("SELECT display_head, gloss FROM articles WHERE slug = 'атлас'").fetchone()
    assert a_art == ("а́тлас", "atlas (bound collection of maps)")

    conn.close()


def test_apply_heteronyms_to_manifest(tmp_path: Path):
    """Verify apply_heteronyms updates JSON manifest properly for all heteronyms."""
    manifest_path = tmp_path / "lexicon-manifest.json"
    data = {
        "entries": [
            {
                "lemma": "город",
                "url_slug": "город",
                "gloss": "vegetable garden",
                "heritage_status": {"classification": "authentic-archaism"},
            },
            {
                "lemma": "замок",
                "url_slug": "замок",
                "gloss": "castle / lock",
                "heritage_status": {"classification": "standard"},
            },
            {
                "lemma": "атлас",
                "url_slug": "атлас",
                "gloss": "atlas / satin",
                "heritage_status": {"classification": "standard"},
            },
        ]
    }
    manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    dummy_db = tmp_path / "empty.db"
    counts = enrich_heteronyms.apply_heteronyms(
        db_path=dummy_db, manifest_path=manifest_path, lemmas=["город", "замок", "атлас"]
    )
    assert counts["manifest_entries"] == 3

    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {e["lemma"]: e for e in updated["entries"]}

    assert entries["город"]["display_head"] == "горо́д"
    assert entries["город"]["sections"]["synonyms"]["items"] == ["грядка", "городчик"]

    assert entries["замок"]["display_head"] == "за́мок"
    assert "фортеця" in entries["замок"]["sections"]["synonyms"]["items"]

    assert entries["атлас"]["display_head"] == "а́тлас"
    assert "збірник карт" in entries["атлас"]["sections"]["synonyms"]["items"]


def test_curated_heteronyms_ts_parity():
    """Verify site/src/lib/lexicon/curated-heteronyms.ts exactly matches enrich_heteronyms.CURATED_HETERONYMS."""
    ts_file = Path(__file__).resolve().parents[1] / "site" / "src" / "lib" / "lexicon" / "curated-heteronyms.ts"
    assert ts_file.is_file(), f"Expected {ts_file} to exist"
    content = ts_file.read_text(encoding="utf-8")

    prefix = "export const CURATED_HETERONYMS: Record<string, LexiconEntry[]> = "
    start_idx = content.find(prefix)
    assert start_idx != -1, f"Could not find CURATED_HETERONYMS assignment in {ts_file}"
    start_idx += len(prefix)
    end_idx = content.find(";\n\nexport function getEffectiveHeteronyms", start_idx)
    assert end_idx != -1, f"Could not find end of CURATED_HETERONYMS object in {ts_file}"
    json_literal = content[start_idx:end_idx].strip()
    ts_data = json.loads(json_literal)

    assert set(ts_data.keys()) == set(enrich_heteronyms.CURATED_HETERONYMS.keys())

    for lemma, py_items in enrich_heteronyms.CURATED_HETERONYMS.items():
        ts_items = ts_data[lemma]
        assert len(ts_items) == len(py_items)
        for i, py_item in enumerate(py_items):
            ts_item = ts_items[i]
            assert ts_item["lemma"] == lemma
            assert ts_item["url_slug"] == lemma
            ts_item_clean = {k: v for k, v in ts_item.items() if k not in ("lemma", "url_slug")}
            assert ts_item_clean == py_item, f"Drift detected for {lemma} entry #{i} ({py_item['headword']})"


def test_obid_disambiguation():
    """Verify обід wheel rim vs lunch/dinner disambiguation (#8039)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("обід")
    assert items is not None
    assert len(items) == 2

    rim, lunch = items[0], items[1]
    assert rim["headword"] == "о́бід"
    assert rim["short_label"] == "у колеса"
    assert rim["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "о́бода"
    assert rim["pronunciation"]["ipa"] == "[ˈɔbʲid]"

    assert lunch["headword"] == "обі́д"
    assert lunch["short_label"] == "споживання їжі (A1)"
    assert lunch["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "обі́ду"
    assert lunch["pronunciation"]["ipa"] == "[oˈbʲid]"


def test_organ_disambiguation():
    """Verify орган body/state organ vs musical pipe organ disambiguation (#8039)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("орган")
    assert items is not None
    assert len(items) == 2

    body_organ, pipe_organ = items[0], items[1]
    assert body_organ["headword"] == "о́рган"
    assert body_organ["cefr"] == "A1"
    assert body_organ["pronunciation"]["ipa"] == "[ˈɔrɦɐn]"

    assert pipe_organ["headword"] == "орга́н"
    assert pipe_organ["cefr"] == "B1"
    assert pipe_organ["pronunciation"]["ipa"] == "[ɔrˈɦan]"


def test_muzyka_disambiguation():
    """Verify музика music art vs musician disambiguation (#8039)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("музика")
    assert items is not None
    assert len(items) == 2

    music_art, musician = items[0], items[1]
    assert music_art["headword"] == "му́зика"
    assert music_art["short_label"] == "вид мистецтва (A1)"
    assert music_art["morphology"]["paradigm"]["cases"]["родовий"]["plural"] == "му́зик"

    assert musician["headword"] == "музи́ка"
    assert musician["short_label"] == "музикант, виконавець (B1)"
    assert musician["morphology"]["paradigm"]["cases"]["знахідний"]["plural"] == "музи́к"


def test_batch_expansion_count():
    """Verify batch heteronym expansion admits 136 curated lemmas with exact scan residual.

    Batch 1 (#8039, PR #8043): 40 curated. Batch 2 (#8039 continuation): +32
    lemmas selected from the atlas.db-approved, A1/A2/B1 tier residual, each
    with a genuinely distinct SUM-11 stress position. Batch 3 (#8039
    continuation): +32 lemmas selected from the live Atlas manifest, after
    correcting the `--scan` denominator: 45 candidate pairs share an
    identical stress across both SUM-11 headwords (homonyms, not
    heteronyms, e.g. ВІДВО́ЗИТИ/ВІ́ХА/ДЕРЖА́ВА), so the true denominator is
    422, not the pre-fix 467. Batch 4 (#8039 continuation): +32 lemmas
    selected from the remaining 318 residual candidates, expanding SSOT to 136.
    """
    total_curated = len(enrich_heteronyms.CURATED_HETERONYMS)
    assert total_curated == 136
    # Corrected denominator is 422 true two-way-stress candidates;
    # residual is 422 - 136 = 286
    assert 422 - total_curated == 286


def test_kredyt_disambiguation():
    """Verify кредит accounting-ledger term vs loan/credit disambiguation (batch 2)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("кредит")
    assert items is not None
    assert len(items) == 2

    ledger, loan = items[0], items[1]
    assert ledger["headword"] == "кре́дит"
    assert ledger["pronunciation"]["ipa"] == "[ˈkrɛdɪt]"
    assert ledger["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "кре́диту"

    assert loan["headword"] == "креди́т"
    assert loan["cefr"] == "A2"
    assert loan["pronunciation"]["ipa"] == "[krɛˈdɪt]"


def test_rodovyi_perednii_style_directional_verb_aspect_pairs():
    """Verify обходити/обходитися directional-verb aspect pairs (batch 2)."""
    obhodyty = enrich_heteronyms.build_heteronyms_for_lemma("обходити")
    assert obhodyty is not None
    assert len(obhodyty) == 2
    assert obhodyty[0]["headword"] == "обхо́дити"
    assert obhodyty[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert obhodyty[1]["headword"] == "обходи́ти"
    assert obhodyty[1]["morphology"]["paradigm"]["aspect"] == "доконаний"


def test_pidlitok_disambiguation():
    """Verify підліток teenager vs fledgling-bird disambiguation (batch 2).

    SUM-11 marks the rare "fledgling" sense with a double-accent notation
    (пі́длі́ток); the attested alternate stress (підлі́ток) is used as its
    headword so the pair is a genuine two-way stress contrast.
    """
    items = enrich_heteronyms.build_heteronyms_for_lemma("підліток")
    assert items is not None
    assert len(items) == 2

    teenager, fledgling = items[0], items[1]
    assert teenager["headword"] == "пі́дліток"
    assert teenager["cefr"] == "B1"
    assert fledgling["headword"] == "підлі́ток"
    assert fledgling["cefr"] is None


def test_pered_preposition_vs_noun():
    """Verify перед preposition vs пере́д front-part noun disambiguation (batch 2)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("перед")
    assert items is not None
    assert len(items) == 2

    prep, noun = items[0], items[1]
    assert prep["headword"] == "пе́ред"
    assert prep["pos"] == "preposition"
    assert prep["morphology"]["paradigm"]["kind"] == "preposition"

    assert noun["headword"] == "пере́д"
    assert noun["pos"] == "noun"
    assert noun["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "пе́реду"


def test_gospodarskyi_disambiguation():
    """Verify господарський household/domestic vs economic/farming disambiguation (batch 3)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("господарський")
    assert items is not None
    assert len(items) == 2

    domestic, economic = items[0], items[1]
    assert domestic["headword"] == "госпо́дарський"
    assert domestic["pronunciation"]["ipa"] == "[ɦɔˈspɔdɐrsʲkɪj]"
    assert economic["headword"] == "господа́рський"
    assert economic["pronunciation"]["ipa"] == "[ɦɔspɔˈdarsʲkɪj]"


def test_zamkovyi_disambiguation():
    """Verify замковий castle-related vs lock-related disambiguation (batch 3)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("замковий")
    assert items is not None
    assert len(items) == 2

    castle, lock = items[0], items[1]
    assert castle["headword"] == "за́мковий"
    assert castle["cefr"] == "B1"
    assert lock["headword"] == "замкови́й"
    assert lock["cefr"] == "B1"


def test_kopaty_disambiguation():
    """Verify копати kick vs dig disambiguation (batch 3)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("копати")
    assert items is not None
    assert len(items) == 2

    kick, dig = items[0], items[1]
    assert kick["headword"] == "ко́пати"
    assert kick["gloss"].startswith("to kick")
    assert dig["headword"] == "копа́ти"
    assert dig["gloss"].startswith("to dig")
    assert kick["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert dig["morphology"]["paradigm"]["aspect"] == "недоконаний"


def test_kolon_disambiguation_matches_vesum_not_sum11_order():
    """Verify колон stress follows VESUM's current assignment, not raw СУМ-11 headword order (batch 3).

    СУМ-11's 1970s headword order lists КОЛО́Н (metrics term) before
    КО́ЛОН (colonus/peasant); VESUM's `forms_all` source_comment attests the
    reverse stress-to-sense mapping for the modern standard, which is what
    this curated entry follows.
    """
    items = enrich_heteronyms.build_heteronyms_for_lemma("колон")
    assert items is not None
    assert len(items) == 2

    metrics, colonus = items[0], items[1]
    assert metrics["headword"] == "ко́лон"
    assert "verse" in metrics["gloss"] or "colon" in metrics["gloss"]
    assert colonus["headword"] == "коло́н"
    assert "colonus" in colonus["gloss"]


def test_vyhidnyi_disambiguation():
    """Verify вигідний profitable vs comfortable disambiguation (batch 3, replaces дихання)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("вигідний")
    assert items is not None
    assert len(items) == 2

    profitable, comfortable = items[0], items[1]
    assert profitable["headword"] == "ви́гідний"
    assert profitable["gloss"].startswith("profitable")
    assert comfortable["headword"] == "вигі́дний"
    assert comfortable["gloss"].startswith("comfortable")


def test_batch3_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 3's 32 lemmas are net-new (варення and бубон were dropped as dupes)."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3

    assert len(CURATED_HETERONYMS_BATCH_3) == 32
    earlier = set(CURATED_HETERONYMS_BATCH) | set(CURATED_HETERONYMS_BATCH_2)
    assert earlier & set(CURATED_HETERONYMS_BATCH_3) == set()
    assert "варення" not in CURATED_HETERONYMS_BATCH_3
    assert "бубон" not in CURATED_HETERONYMS_BATCH_3
    assert "копати" in CURATED_HETERONYMS_BATCH_3
    assert "коханий" in CURATED_HETERONYMS_BATCH_3


def test_likarskyi_disambiguation():
    """Verify лікарський doctor's vs medicinal disambiguation (batch 4)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("лікарський")
    assert items is not None
    assert len(items) == 2

    doctors, medicinal = items[0], items[1]
    assert doctors["headword"] == "лі́карський"
    assert "doctor" in doctors["gloss"] or "physician" in doctors["gloss"]
    assert medicinal["headword"] == "ліка́рський"
    assert "medicinal" in medicinal["gloss"] or "curative" in medicinal["gloss"]


def test_lynuti_disambiguation():
    """Verify линути soar/fly (impf) vs splash/pour once (pf) disambiguation (batch 4)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("линути")
    assert items is not None
    assert len(items) == 2

    soar, splash = items[0], items[1]
    assert soar["headword"] == "ли́нути"
    assert soar["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert "soar" in soar["gloss"] or "fly" in soar["gloss"]
    assert splash["headword"] == "лину́ти"
    assert splash["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert "pour once" in splash["gloss"] or "splash" in splash["gloss"]



def test_parnyi_disambiguation():
    """Verify парний paired/even vs warm/fresh-milked disambiguation (batch 4)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("парний")
    assert items is not None
    assert len(items) == 2

    paired, warm = items[0], items[1]
    assert paired["headword"] == "па́рний"
    assert "paired" in paired["gloss"] or "even" in paired["gloss"]
    assert warm["headword"] == "парни́й"
    assert "fresh-milked" in warm["gloss"] or "steamy" in warm["gloss"]


def test_natsinka_disambiguation():
    """Verify націнка markup sum/amount vs price increase action disambiguation (batch 4)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("націнка")
    assert items is not None
    assert len(items) == 2

    markup_sum, price_hike = items[0], items[1]
    assert markup_sum["headword"] == "на́цінка"
    assert "markup" in markup_sum["gloss"]
    assert price_hike["headword"] == "наці́нка"
    assert "raising" in price_hike["gloss"] or "increase" in price_hike["gloss"]



def test_batch4_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 4's 32 lemmas are net-new and mutually disjoint with batches 1-3."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4

    assert len(CURATED_HETERONYMS_BATCH_4) == 32
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_4) == set()
    assert "лікарський" in CURATED_HETERONYMS_BATCH_4
    assert "парний" in CURATED_HETERONYMS_BATCH_4
