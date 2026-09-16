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
        variant_keys = [
            (
                item["headword"],
                item.get("morphology", {}).get("paradigm", {}).get("animacy"),
                item.get("short_label"),
            )
            for item in items
        ]
        assert len(set(variant_keys)) == len(variant_keys), f"Duplicate variant entries found for {lemma}"
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
    """Verify batch heteronym expansion admits 232 curated lemmas with exact scan residual.

    Batch 1 (#8039, PR #8043): 40 curated. Batch 2 (#8039 continuation): +32
    lemmas selected from the atlas.db-approved, A1/A2/B1 tier residual, each
    with a genuinely distinct SUM-11 stress position. Batch 3 (#8039
    continuation): +32 lemmas selected from the live Atlas manifest, after
    correcting the `--scan` denominator: 45 candidate pairs share an
    identical stress across both SUM-11 headwords (homonyms, not
    heteronyms, e.g. ВІДВО́ЗИТИ/ВІ́ХА/ДЕРЖА́ВА), so the true denominator is
    422, not the pre-fix 467. Batch 4 (#8039 continuation): +32 lemmas
    selected from the remaining 318 residual candidates, expanding SSOT to 136.
    Batch 5 (#8039 continuation): +32 lemmas verified against decolonized
    СУМ-20 / ВТС authorities with СУМ-11 Soviet colonization context attached,
    expanding SSOT to 168.
    Batch 6 (#8039 continuation): +32 lemmas selected from atlas.db and high-frequency
    residual, verified against modern standard (СУМ-20 / ВТС) and authentic pre-Soviet
    Grinchenko (1907), expanding SSOT to 200.
    Batch 7 (#8039 continuation): +32 lemmas selected from academic authorities and
    Grinchenko (1907) with explicit Tsarist imperial ban citations and Soviet
    colonization context, expanding SSOT to 232 and dropping residual to 190.
    Batch 8 (#8039 continuation): +32 lemmas selected from academic authorities and
    Grinchenko (1907) with explicit pre-Soviet witness citations and Soviet
    colonization context, expanding SSOT to 264 and dropping residual to 158.
    """
    total_curated = len(enrich_heteronyms.CURATED_HETERONYMS)
    assert total_curated == 264
    # Corrected denominator is 422 true two-way-stress candidates;
    # residual is 422 - 264 = 158
    assert 422 - total_curated == 158


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


def test_pokii_disambiguation():
    """Verify покій peace/tranquility vs chamber/room disambiguation (batch 5)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("покій")
    assert items is not None
    assert len(items) == 2

    peace, chamber = items[0], items[1]
    assert peace["headword"] == "по́кій"
    assert "peace" in peace["gloss"].lower() or "tranquility" in peace["gloss"].lower()
    assert chamber["headword"] == "покі́й"
    assert "room" in chamber["gloss"].lower() or "chamber" in chamber["gloss"].lower()
    assert "soviet_colonization_context" in peace
    assert peace["soviet_colonization_context"]["source"] == "СУМ-11 (1970–1980)"


def test_sapaty_disambiguation():
    """Verify сапати wheeze/pant vs hoe/weed disambiguation (batch 5)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("сапати")
    assert items is not None
    assert len(items) == 2

    wheeze, hoe = items[0], items[1]
    assert wheeze["headword"] == "са́пати"
    assert "breathe" in wheeze["gloss"].lower() or "pant" in wheeze["gloss"].lower()
    assert hoe["headword"] == "сапа́ти"
    assert "hoe" in hoe["gloss"].lower() or "weed" in hoe["gloss"].lower()


def test_plavnyi_disambiguation():
    """Verify плавний smooth vs floating/floodplain disambiguation (batch 5)."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("плавний")
    assert items is not None
    assert len(items) == 2

    smooth, floating = items[0], items[1]
    assert smooth["headword"] == "пла́вний"
    assert "smooth" in smooth["gloss"].lower() or "flowing" in smooth["gloss"].lower()
    assert floating["headword"] == "плавни́й"
    assert (
        "floating" in floating["gloss"].lower()
        or "buoyant" in floating["gloss"].lower()
        or "floodplain" in floating["gloss"].lower()
        or "marsh" in floating["gloss"].lower()
    )


def test_batch5_semantic_and_stress_distinctions():
    """Verify Batch 5 stress and semantic distinctions against СУМ-20 / ВТС / Grinchenko."""
    # лучити: лу́чити (aim) vs лучи́ти (unite)
    luch = enrich_heteronyms.build_heteronyms_for_lemma("лучити")
    assert luch is not None and len(luch) == 2
    assert luch[0]["headword"] == "лу́чити"
    assert "aim" in luch[0]["gloss"].lower() or "target" in luch[0]["gloss"].lower()
    assert luch[1]["headword"] == "лучи́ти"
    assert "unite" in luch[1]["gloss"].lower() or "join" in luch[1]["gloss"].lower()

    # опій: о́пій (opium) vs опі́й (equine inflammation)
    opii = enrich_heteronyms.build_heteronyms_for_lemma("опій")
    assert opii is not None and len(opii) == 2
    assert opii[0]["headword"] == "о́пій"
    assert "opium" in opii[0]["gloss"].lower()
    assert opii[1]["headword"] == "опі́й"
    assert "equine" in opii[1]["gloss"].lower() or "inflammation" in opii[1]["gloss"].lower()

    # платина: пла́тина (metal Pt) vs плати́на (kerchief)
    plat = enrich_heteronyms.build_heteronyms_for_lemma("платина")
    assert plat is not None and len(plat) == 2
    assert plat[0]["headword"] == "пла́тина"
    assert "platinum" in plat[0]["gloss"].lower()
    assert plat[1]["headword"] == "плати́на"
    assert "kerchief" in plat[1]["gloss"].lower() or "headscarf" in plat[1]["gloss"].lower()

    # порання: по́рання (chores) vs пора́ння (early morning)
    por = enrich_heteronyms.build_heteronyms_for_lemma("порання")
    assert por is not None and len(por) == 2
    assert por[0]["headword"] == "по́рання"
    assert "chores" in por[0]["gloss"].lower() or "tending" in por[0]["gloss"].lower()
    assert por[1]["headword"] == "пора́ння"
    assert "morning" in por[1]["gloss"].lower() or "dawn" in por[1]["gloss"].lower()

    # похідний: похі́дний (marching) vs похідни́й (derived)
    pokh = enrich_heteronyms.build_heteronyms_for_lemma("похідний")
    assert pokh is not None and len(pokh) == 2
    assert pokh[0]["headword"] == "похі́дний"
    assert "marching" in pokh[0]["gloss"].lower() or "camp" in pokh[0]["gloss"].lower()
    assert pokh[1]["headword"] == "похідни́й"
    assert "derived" in pokh[1]["gloss"].lower() or "derivative" in pokh[1]["gloss"].lower()

    # провід: про́від (leadership / wire) vs прові́д (conducting action)
    prov = enrich_heteronyms.build_heteronyms_for_lemma("провід")
    assert prov is not None and len(prov) == 2
    assert prov[0]["headword"] == "про́від"
    assert "leadership" in prov[0]["gloss"].lower() and "wire" in prov[0]["gloss"].lower()
    assert prov[1]["headword"] == "прові́д"
    assert "conducting" in prov[1]["gloss"].lower() or "conveyance" in prov[1]["gloss"].lower()


def test_batch5_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 5's 32 lemmas are net-new and mutually disjoint with batches 1-4."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5

    assert len(CURATED_HETERONYMS_BATCH_5) == 32
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_5) == set()
    assert "покій" in CURATED_HETERONYMS_BATCH_5
    assert "сапати" in CURATED_HETERONYMS_BATCH_5
    assert "плавний" in CURATED_HETERONYMS_BATCH_5


def test_batch6_semantic_and_stress_distinctions():
    """Verify Batch 6 stress and semantic distinctions against СУМ-20 / ВТС / Grinchenko."""
    # гукнути: гу́кнути (гуркнути, boom / crash / roar) vs гукну́ти (крикнути, shout / call)
    guk = enrich_heteronyms.build_heteronyms_for_lemma("гукнути")
    assert guk is not None and len(guk) == 2
    assert guk[0]["headword"] == "гу́кнути"
    assert "boom" in guk[0]["gloss"].lower() or "crash" in guk[0]["gloss"].lower() or "thud" in guk[0]["gloss"].lower()
    assert guk[1]["headword"] == "гукну́ти"
    assert "shout" in guk[1]["gloss"].lower() or "call" in guk[1]["gloss"].lower()

    # балувати: ба́лувати (pamper / spoil) vs балува́ти (feast / attend balls)
    bal = enrich_heteronyms.build_heteronyms_for_lemma("балувати")
    assert bal is not None and len(bal) == 2
    assert bal[0]["headword"] == "ба́лувати"
    assert "pamper" in bal[0]["gloss"].lower() or "spoil" in bal[0]["gloss"].lower()
    assert bal[1]["headword"] == "балува́ти"
    assert "ball" in bal[1]["gloss"].lower() or "feast" in bal[1]["gloss"].lower()

    # жалоба: жа́лоба (lawsuit / grievance) vs жало́ба (mourning / bereavement)
    zhal = enrich_heteronyms.build_heteronyms_for_lemma("жалоба")
    assert zhal is not None and len(zhal) == 2
    assert zhal[0]["headword"] == "жа́лоба"
    assert "complaint" in zhal[0]["gloss"].lower() or "grievance" in zhal[0]["gloss"].lower()
    assert zhal[1]["headword"] == "жало́ба"
    assert "mourning" in zhal[1]["gloss"].lower() or "grief" in zhal[1]["gloss"].lower()

    # дихання: ди́хання (standard: respiration, gas exchange, breath) vs диха́ння (dialectal variant)
    dykh = enrich_heteronyms.build_heteronyms_for_lemma("дихання")
    assert dykh is not None and len(dykh) == 2
    assert dykh[0]["headword"] == "ди́хання"
    assert "respiration" in dykh[0]["gloss"].lower() or "breathing" in dykh[0]["gloss"].lower()
    assert dykh[1]["headword"] == "диха́ння"
    assert "dialectal" in dykh[1]["gloss"].lower() or "variant" in dykh[1]["gloss"].lower()

    # україна: укра́їна (frontier territory) vs украї́на (native country / homeland)
    ukr = enrich_heteronyms.build_heteronyms_for_lemma("україна")
    assert ukr is not None and len(ukr) == 2
    assert ukr[0]["headword"] == "укра́їна"
    assert "border" in ukr[0]["gloss"].lower() or "frontier" in ukr[0]["gloss"].lower()
    assert ukr[1]["headword"] == "украї́на"
    assert "homeland" in ukr[1]["gloss"].lower() or "native land" in ukr[1]["gloss"].lower()

    # замір: за́мір (intention / plan) vs замі́р (measurement / gauging)
    zam = enrich_heteronyms.build_heteronyms_for_lemma("замір")
    assert zam is not None and len(zam) == 2
    assert zam[0]["headword"] == "за́мір"
    assert "intention" in zam[0]["gloss"].lower() or "plan" in zam[0]["gloss"].lower()
    assert zam[1]["headword"] == "замі́р"
    assert "measurement" in zam[1]["gloss"].lower() or "gauging" in zam[1]["gloss"].lower()

    # підсумковий: підсу́мковий (cartridge pouch) vs підсумко́вий (summary / conclusive)
    pid = enrich_heteronyms.build_heteronyms_for_lemma("підсумковий")
    assert pid is not None and len(pid) == 2
    assert pid[0]["headword"] == "підсу́мковий"
    assert "pouch" in pid[0]["gloss"].lower() or "cartridge" in pid[0]["gloss"].lower()
    assert pid[1]["headword"] == "підсумко́вий"
    assert "summary" in pid[1]["gloss"].lower() or "conclusive" in pid[1]["gloss"].lower()

    # уступ: у́ступ (text passage / paragraph) vs усту́п (ledge / step / terrace)
    ust = enrich_heteronyms.build_heteronyms_for_lemma("уступ")
    assert ust is not None and len(ust) == 2
    assert ust[0]["headword"] == "у́ступ"
    assert "passage" in ust[0]["gloss"].lower() or "paragraph" in ust[0]["gloss"].lower()
    assert ust[1]["headword"] == "усту́п"
    assert "ledge" in ust[1]["gloss"].lower() or "step" in ust[1]["gloss"].lower() or "terrace" in ust[1]["gloss"].lower()

    # твердити: тве́рдити (assert / assure) vs тверди́ти (repeat repeatedly / rehearse)
    tve = enrich_heteronyms.build_heteronyms_for_lemma("твердити")
    assert tve is not None and len(tve) == 2
    assert tve[0]["headword"] == "тве́рдити"
    assert "assert" in tve[0]["gloss"].lower() or "assure" in tve[0]["gloss"].lower()
    assert tve[1]["headword"] == "тверди́ти"
    assert "repeat" in tve[1]["gloss"].lower() or "rehearse" in tve[1]["gloss"].lower()

    # родовий: родо́вий (clan / lineage / genitive) vs родови́й (obstetric / labor)
    rod = enrich_heteronyms.build_heteronyms_for_lemma("родовий")
    assert rod is not None and len(rod) == 2
    assert rod[0]["headword"] == "родо́вий"
    assert "clan" in rod[0]["gloss"].lower() or "genitive" in rod[0]["gloss"].lower()
    assert rod[1]["headword"] == "родови́й"
    assert "childbirth" in rod[1]["gloss"].lower() or "obstetric" in rod[1]["gloss"].lower() or "labor" in rod[1]["gloss"].lower()

    # хрещений: хре́щений (baptized participle) vs хреще́ний (godparent)
    khr = enrich_heteronyms.build_heteronyms_for_lemma("хрещений")
    assert khr is not None and len(khr) == 2
    assert khr[0]["headword"] == "хре́щений"
    assert "baptized" in khr[0]["gloss"].lower() or "christened" in khr[0]["gloss"].lower()
    assert khr[1]["headword"] == "хреще́ний"
    assert "godparent" in khr[1]["gloss"].lower()

    # сполучний: сполу́чний (connective / connecting) vs сполучни́й (combinable)
    spol = enrich_heteronyms.build_heteronyms_for_lemma("сполучний")
    assert spol is not None and len(spol) == 2
    assert spol[0]["headword"] == "сполу́чний"
    assert "connect" in spol[0]["gloss"].lower()
    assert spol[1]["headword"] == "сполучни́й"
    assert "combinable" in spol[1]["gloss"].lower() or "compatible" in spol[1]["gloss"].lower()

    # хлібець: хлі́бець (small loaf / bun) vs хлібе́ць (dear bread / young grain in folklore)
    khl = enrich_heteronyms.build_heteronyms_for_lemma("хлібець")
    assert khl is not None and len(khl) == 2
    assert khl[0]["headword"] == "хлі́бець"
    assert "loaf" in khl[0]["gloss"].lower() or "bun" in khl[0]["gloss"].lower()
    assert khl[1]["headword"] == "хлібе́ць"
    assert "bread" in khl[1]["gloss"].lower() or "grain" in khl[1]["gloss"].lower()

    # байковий: ба́йковий (flannelette / baize fabric) vs байко́вий (fable / fabular)
    bay = enrich_heteronyms.build_heteronyms_for_lemma("байковий")
    assert bay is not None and len(bay) == 2
    assert bay[0]["headword"] == "ба́йковий"
    assert "flannelette" in bay[0]["gloss"].lower() or "baize" in bay[0]["gloss"].lower()
    assert bay[1]["headword"] == "байко́вий"
    assert "fable" in bay[1]["gloss"].lower()

    # брикнути: бри́кнути (tumble / fall down) vs брикну́ти (buck / kick with hoof)
    bryk = enrich_heteronyms.build_heteronyms_for_lemma("брикнути")
    assert bryk is not None and len(bryk) == 2
    assert bryk[0]["headword"] == "бри́кнути"
    assert "tumble" in bryk[0]["gloss"].lower() or "fall" in bryk[0]["gloss"].lower()
    assert bryk[1]["headword"] == "брикну́ти"
    assert "buck" in bryk[1]["gloss"].lower() or "kick" in bryk[1]["gloss"].lower()


def test_batch6_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 6's 32 lemmas are net-new and mutually disjoint with batches 1-5."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6

    assert len(CURATED_HETERONYMS_BATCH_6) == 32
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_6) == set()
    assert "балувати" in CURATED_HETERONYMS_BATCH_6
    assert "жалоба" in CURATED_HETERONYMS_BATCH_6
    assert "україна" in CURATED_HETERONYMS_BATCH_6
    assert "дихання" in CURATED_HETERONYMS_BATCH_6
    assert "гукнути" in CURATED_HETERONYMS_BATCH_6
    assert "ковтнути" in CURATED_HETERONYMS_BATCH_6
    assert "байковий" in CURATED_HETERONYMS_BATCH_6
    assert "брикнути" in CURATED_HETERONYMS_BATCH_6


def test_batch7_semantic_and_stress_distinctions():
    """Verify Batch 7 stress and semantic distinctions against academic authorities and Grinchenko."""
    # банник: ба́нник (bore swab) vs банни́к (bathhouse attendant)
    ban = enrich_heteronyms.build_heteronyms_for_lemma("банник")
    assert ban is not None and len(ban) == 2
    assert ban[0]["headword"] == "ба́нник"
    assert "artillery" in ban[0]["gloss"].lower() or "brush" in ban[0]["gloss"].lower()
    assert ban[1]["headword"] == "банни́к"
    assert "bath" in ban[1]["gloss"].lower() or "bather" in ban[1]["gloss"].lower()

    # бережений: бере́жений (participle of берегти) vs береже́ний (cautious, prudent)
    ber = enrich_heteronyms.build_heteronyms_for_lemma("бережений")
    assert ber is not None and len(ber) == 2
    assert ber[0]["headword"] == "бере́жений"
    assert "guarded" in ber[0]["gloss"].lower() or "kept" in ber[0]["gloss"].lower()
    assert ber[1]["headword"] == "береже́ний"
    assert "cautious" in ber[1]["gloss"].lower() or "wary" in ber[1]["gloss"].lower()

    # буритися: бу́ритися (rage / storm) vs бури́тися (passive of бурити)
    bur = enrich_heteronyms.build_heteronyms_for_lemma("буритися")
    assert bur is not None and len(bur) == 2
    assert bur[0]["headword"] == "бу́ритися"
    assert ("rage" in bur[0]["gloss"].lower() or "agitat" in bur[0]["gloss"].lower() or "storm" in bur[0]["gloss"].lower())
    assert "collapse" not in bur[0]["gloss"].lower()
    assert "crumble" not in bur[0]["gloss"].lower()
    assert bur[1]["headword"] == "бури́тися"
    assert "drilled" in bur[1]["gloss"].lower() or "bored" in bur[1]["gloss"].lower()

    # важниця: ва́жниця (person of importance / animate) vs ва́жниця (important matter / inanimate) vs важни́ця (wagon prop / scales / inanimate)
    vazh = enrich_heteronyms.build_heteronyms_for_lemma("важниця")
    assert vazh is not None and len(vazh) == 3
    assert vazh[0]["headword"] == "ва́жниця"
    assert vazh[0]["morphology"]["paradigm"]["animacy"] == "animate"
    assert "person" in vazh[0]["gloss"].lower() or "importance" in vazh[0]["gloss"].lower()
    assert vazh[1]["headword"] == "ва́жниця"
    assert vazh[1]["morphology"]["paradigm"]["animacy"] == "inanimate"
    assert "matter" in vazh[1]["gloss"].lower() or "affair" in vazh[1]["gloss"].lower()
    assert vazh[2]["headword"] == "важни́ця"
    assert vazh[2]["morphology"]["paradigm"]["animacy"] == "inanimate"
    assert "wagon" in vazh[2]["gloss"].lower() or "prop" in vazh[2]["gloss"].lower() or "scale" in vazh[2]["gloss"].lower()
    assert "station" not in vazh[2]["gloss"].lower()
    assert "вагівниця" not in vazh[2]["soviet_colonization_context"]["definition"]
    assert "вага́ 5" in vazh[2]["soviet_colonization_context"]["definition"]
    assert "ва́жниць" in vazh[0]["distinction_note"]
    assert "важни́ць" not in vazh[0]["distinction_note"]
    assert "ва́жниці" in vazh[1]["distinction_note"]
    assert "важни́ці" not in vazh[1]["distinction_note"]

    # валковий: валко́вий (roller-equipped) vs валкови́й (carter / driver with convoy)
    val = enrich_heteronyms.build_heteronyms_for_lemma("валковий")
    assert val is not None and len(val) == 2
    assert val[0]["headword"] == "валко́вий"
    assert "roller" in val[0]["gloss"].lower()
    assert val[1]["headword"] == "валкови́й"
    assert val[1]["morphology"]["paradigm"]["animacy"] == "animate"
    assert "carter" in val[1]["gloss"].lower() or "driver" in val[1]["gloss"].lower()

    # виправний: випра́вний (correctable) vs виправни́й (correctional / penal)
    vyp = enrich_heteronyms.build_heteronyms_for_lemma("виправний")
    assert vyp is not None and len(vyp) == 2
    assert vyp[0]["headword"] == "випра́вний"
    assert "correctable" in vyp[0]["gloss"].lower() or "rectifiable" in vyp[0]["gloss"].lower()
    assert vyp[1]["headword"] == "виправни́й"
    assert "correctional" in vyp[1]["gloss"].lower() or "penal" in vyp[1]["gloss"].lower()
    assert vyp[1]["soviet_colonization_context"] is not None
    assert "Виправна колонія" in vyp[1]["soviet_colonization_context"]["definition"]
    assert "виправно-трудовий" not in vyp[1]["soviet_colonization_context"]["definition"]
    assert vyp[1]["soviet_colonization_context"]["keywords"] == ["виправна колонія"]

    # відбігати: відбі́гати (finish running) vs відбіга́ти (run away)
    vidb = enrich_heteronyms.build_heteronyms_for_lemma("відбігати")
    assert vidb is not None and len(vidb) == 2
    assert vidb[0]["headword"] == "відбі́гати"
    assert "finish" in vidb[0]["gloss"].lower()
    assert vidb[1]["headword"] == "відбіга́ти"
    assert "run away" in vidb[1]["gloss"].lower()

    # вугровий: вугро́вий (eel) vs вугрови́й (acne / pimple)
    vuh = enrich_heteronyms.build_heteronyms_for_lemma("вугровий")
    assert vuh is not None and len(vuh) == 2
    assert vuh[0]["headword"] == "вугро́вий"
    assert "eel" in vuh[0]["gloss"].lower()
    assert "acne" not in vuh[0]["gloss"].lower()
    assert "риба" in vuh[0]["meaning"]["definitions"][0].lower() or "вугор¹" in vuh[0]["meaning"]["definitions"][0].lower()
    assert vuh[1]["headword"] == "вугрови́й"
    assert "acne" in vuh[1]["gloss"].lower() or "pimple" in vuh[1]["gloss"].lower() or "comedon" in vuh[1]["gloss"].lower()
    assert "eel" not in vuh[1]["gloss"].lower()
    assert "вугор²" in vuh[1]["meaning"]["definitions"][0].lower() or "висип" in vuh[1]["meaning"]["definitions"][0].lower()

    # гаванський: га́ванський (harbor) vs гава́нський (Havana)
    hav = enrich_heteronyms.build_heteronyms_for_lemma("гаванський")
    assert hav is not None and len(hav) == 2
    assert hav[0]["headword"] == "га́ванський"
    assert "harbor" in hav[0]["gloss"].lower() or "haven" in hav[0]["gloss"].lower()
    assert hav[1]["headword"] == "гава́нський"
    assert "havana" in hav[1]["gloss"].lower()

    # гребінник: гребі́нник (grass) vs гребінни́к (comb maker)
    hreb = enrich_heteronyms.build_heteronyms_for_lemma("гребінник")
    assert hreb is not None and len(hreb) == 2
    assert hreb[0]["headword"] == "гребі́нник"
    assert "grass" in hreb[0]["gloss"].lower()
    assert hreb[1]["headword"] == "гребінни́к"
    assert "comb" in hreb[1]["gloss"].lower()

    # домовий: домо́вий (residential / domestic) vs домови́й (house spirit)
    dom = enrich_heteronyms.build_heteronyms_for_lemma("домовий")
    assert dom is not None and len(dom) == 2
    assert dom[0]["headword"] == "домо́вий"
    assert "residential" in dom[0]["gloss"].lower() or "domestic" in dom[0]["gloss"].lower()
    assert dom[1]["headword"] == "домови́й"
    assert "spirit" in dom[1]["gloss"].lower() or "goblin" in dom[1]["gloss"].lower()

    # значковий: значко́вий (cartographic symbol) vs значкови́й (Cossack rank)
    znach = enrich_heteronyms.build_heteronyms_for_lemma("значковий")
    assert znach is not None and len(znach) == 2
    assert znach[0]["headword"] == "значко́вий"
    assert "symbol" in znach[0]["gloss"].lower() or "badge" in znach[0]["gloss"].lower()
    assert znach[1]["headword"] == "значкови́й"
    assert "cossack" in znach[1]["gloss"].lower() or "banner" in znach[1]["gloss"].lower()

    # затулка: за́тулка (oven damper / inanimate) vs зату́лка (valve snail / animate)
    zat = enrich_heteronyms.build_heteronyms_for_lemma("затулка")
    assert zat is not None and len(zat) == 2
    assert zat[0]["headword"] == "за́тулка"
    assert zat[0]["morphology"]["paradigm"]["animacy"] == "inanimate"
    assert zat[1]["headword"] == "зату́лка"
    assert zat[1]["morphology"]["paradigm"]["animacy"] == "animate"
    assert "snail" in zat[1]["gloss"].lower() or "mollusk" in zat[1]["gloss"].lower()

    # жировий: жиро́вий (suit of clubs / trefoil) vs жирови́й (fatty / lipid)
    zhyr = enrich_heteronyms.build_heteronyms_for_lemma("жировий")
    assert zhyr is not None and len(zhyr) == 2
    assert zhyr[0]["headword"] == "жиро́вий"
    assert "club" in zhyr[0]["gloss"].lower() or "trefoil" in zhyr[0]["gloss"].lower()
    assert "trump" not in zhyr[0]["gloss"].lower()
    assert "winning" not in zhyr[0]["gloss"].lower()
    assert "wedlock" not in zhyr[0]["gloss"].lower()
    assert "позашлюб" not in zhyr[0]["short_label"].lower()
    assert "трефа" in zhyr[0]["meaning"]["definitions"][0].lower() or "хрести" in zhyr[0]["meaning"]["definitions"][0].lower()
    assert "козир" not in zhyr[0]["meaning"]["definitions"][0].lower()
    assert zhyr[1]["headword"] == "жирови́й"
    assert "fat" in zhyr[1]["gloss"].lower() or "lipid" in zhyr[1]["gloss"].lower()

    # замішка: за́мішка (liquid flour dish) vs замі́шка (confusion / hitch / delay)
    zam = enrich_heteronyms.build_heteronyms_for_lemma("замішка")
    assert zam is not None and len(zam) == 2
    assert zam[0]["headword"] == "за́мішка"
    assert "liquid" in zam[0]["gloss"].lower() or "flour" in zam[0]["gloss"].lower() or "porridge" in zam[0]["gloss"].lower()
    assert "thick" not in zam[0]["gloss"].lower()
    assert "рідка" in zam[0]["meaning"]["definitions"][0].lower()
    assert "густа" not in zam[0]["meaning"]["definitions"][0].lower()
    assert zam[1]["headword"] == "замі́шка"
    assert "confusion" in zam[1]["gloss"].lower() or "delay" in zam[1]["gloss"].lower() or "muddle" in zam[1]["gloss"].lower()

    # жабник: жа́бник (pejorative wader / animate) vs жабни́к (plant / inanimate)
    zhab = enrich_heteronyms.build_heteronyms_for_lemma("жабник")
    assert zhab is not None and len(zhab) == 2
    assert zhab[0]["headword"] == "жа́бник"
    assert zhab[0]["morphology"]["paradigm"]["animacy"] == "animate"
    assert "wader" in zhab[0]["gloss"].lower() or "paddler" in zhab[0]["gloss"].lower()
    assert zhab[1]["headword"] == "жабни́к"
    assert zhab[1]["morphology"]["paradigm"]["animacy"] == "inanimate"
    assert "plant" in zhab[1]["gloss"].lower() or "marigold" in zhab[1]["gloss"].lower() or "filago" in zhab[1]["gloss"].lower()
    # verify verbatim SUM-11 definition without bracketed insertions
    assert "[айстрових]" not in zhab[1]["soviet_colonization_context"]["definition"]
    assert "родини жовтцевих" in zhab[1]["soviet_colonization_context"]["definition"]
    # verify separate attribution for Caltha / Filago
    defs = zhab[1]["meaning"]["definitions"]
    assert any("caltha" in d.lower() or "калюжниц" in d.lower() for d in defs)
    assert any("filago" in d.lower() or "айстров" in d.lower() for d in defs)

    # загукати: загу́кати (resound, hoot) vs загука́ти (shout, call out loudly)
    zah = enrich_heteronyms.build_heteronyms_for_lemma("загукати")
    assert zah is not None and len(zah) == 2
    assert zah[0]["headword"] == "загу́кати"
    assert zah[1]["headword"] == "загука́ти"
    assert "Гуляй!" in zah[1]["distinction_note"]
    assert "повалили" not in zah[1]["distinction_note"]

    # дозвільний: дозві́льний (leisure, free) vs дозвільни́й (permitting)
    doz = enrich_heteronyms.build_heteronyms_for_lemma("дозвільний")
    assert doz is not None and len(doz) == 2
    assert doz[0]["headword"] == "дозві́льний"
    assert "Бо не було дозвільної хвилини" in doz[0]["distinction_note"]


def test_batch7_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 7's 32 lemmas are net-new and mutually disjoint with batches 1-6."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6
    from scripts.lexicon.curated_heteronyms_batch7 import CURATED_HETERONYMS_BATCH_7

    assert len(CURATED_HETERONYMS_BATCH_7) == 32
    assert sum(len(v) for v in CURATED_HETERONYMS_BATCH_7.values()) == 65
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
        | set(CURATED_HETERONYMS_BATCH_6)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_7) == set()
    assert "банник" in CURATED_HETERONYMS_BATCH_7
    assert "бережений" in CURATED_HETERONYMS_BATCH_7
    assert "буритися" in CURATED_HETERONYMS_BATCH_7
    assert "важниця" in CURATED_HETERONYMS_BATCH_7
    assert "валковий" in CURATED_HETERONYMS_BATCH_7
    assert "виправний" in CURATED_HETERONYMS_BATCH_7
    assert "випробуваний" in CURATED_HETERONYMS_BATCH_7
    assert "значковий" in CURATED_HETERONYMS_BATCH_7

    # Verify accurate per-variant heritage classifications and VESUM attestations (#8039)
    bannik = CURATED_HETERONYMS_BATCH_7["банник"]
    assert bannik[0]["heritage_status"]["vesum_attested"] is True
    assert bannik[1]["heritage_status"]["vesum_attested"] is False
    assert bannik[1]["heritage_status"]["classification"] == "authentic-dialectism"

    valkovyi = CURATED_HETERONYMS_BATCH_7["валковий"]
    assert valkovyi[0]["heritage_status"]["vesum_attested"] is True
    assert valkovyi[1]["heritage_status"]["vesum_attested"] is False
    assert valkovyi[1]["heritage_status"]["classification"] == "authentic-historism"

    domovyi = CURATED_HETERONYMS_BATCH_7["домовий"]
    assert domovyi[0]["heritage_status"]["vesum_attested"] is True
    assert domovyi[1]["heritage_status"]["vesum_attested"] is False
    assert domovyi[1]["heritage_status"]["classification"] == "authentic-folklorism"

    znachkovyi = CURATED_HETERONYMS_BATCH_7["значковий"]
    assert znachkovyi[0]["heritage_status"]["classification"] == "standard"
    assert znachkovyi[1]["heritage_status"]["classification"] == "authentic-historism"
    assert znachkovyi[1]["heritage_status"]["vesum_attested"] is True

    burytysya = CURATED_HETERONYMS_BATCH_7["буритися"]
    assert burytysya[0]["heritage_status"]["classification"] == "authentic-dialectism"

    vazhnytsya = CURATED_HETERONYMS_BATCH_7["важниця"]
    assert vazhnytsya[2]["heritage_status"]["classification"] == "authentic-historism"

    vidrubnyi = CURATED_HETERONYMS_BATCH_7["відрубний"]
    assert vidrubnyi[1]["heritage_status"]["classification"] == "authentic-historism"

    zakupka = CURATED_HETERONYMS_BATCH_7["закупка"]
    assert zakupka[0]["heritage_status"]["classification"] == "authentic-archaism"

    vyprobuvanyi = CURATED_HETERONYMS_BATCH_7["випробуваний"]
    assert vyprobuvanyi[0]["heritage_status"]["vesum_attested"] is True
    assert vyprobuvanyi[1]["heritage_status"]["vesum_attested"] is False

    berezhenyi = CURATED_HETERONYMS_BATCH_7["бережений"]
    assert berezhenyi[0]["heritage_status"]["vesum_attested"] is True
    assert berezhenyi[1]["heritage_status"]["vesum_attested"] is False

    zaznanyi = CURATED_HETERONYMS_BATCH_7["зазнаний"]
    assert zaznanyi[0]["heritage_status"]["vesum_attested"] is True
    assert zaznanyi[1]["heritage_status"]["vesum_attested"] is False
    assert "дитинстві" in zaznanyi[0]["soviet_colonization_context"]["definition"]
    assert "юності" not in zaznanyi[0]["soviet_colonization_context"]["definition"]
    assert "Барв." in zaznanyi[1]["soviet_colonization_context"]["definition"]
    assert "Геть з дороги" not in zaznanyi[1]["soviet_colonization_context"]["definition"]


def test_batch8_semantic_and_stress_distinctions():
    """Verify Batch 8 stress and semantic distinctions against academic authorities and Grinchenko."""
    # вивозитися: ви́возитися (get dirty, perf.) vs виво́зитися (be exported, imperf.)
    vyv = enrich_heteronyms.build_heteronyms_for_lemma("вивозитися")
    assert vyv is not None and len(vyv) == 2
    assert vyv[0]["headword"] == "ви́возитися"
    assert "dirty" in vyv[0]["gloss"].lower() or "soil" in vyv[0]["gloss"].lower()
    assert vyv[1]["headword"] == "виво́зитися"
    assert "export" in vyv[1]["gloss"].lower() or "transport" in vyv[1]["gloss"].lower()

    # захватний: захва́тний (clamping / gripping, tech.) vs захватни́й (exciting / thrilling / captivating)
    zah = enrich_heteronyms.build_heteronyms_for_lemma("захватний")
    assert zah is not None and len(zah) == 2
    assert zah[0]["headword"] == "захва́тний"
    assert "gripping" in zah[0]["gloss"].lower() or "clamping" in zah[0]["gloss"].lower()
    assert zah[1]["headword"] == "захватни́й"
    assert "exciting" in zah[1]["gloss"].lower() or "thrilling" in zah[1]["gloss"].lower() or "captivating" in zah[1]["gloss"].lower()

    # дякування: дя́кування (thanking / gratitude) vs дякува́ння (serving as deacon / cantor in church)
    diak = enrich_heteronyms.build_heteronyms_for_lemma("дякування")
    assert diak is not None and len(diak) == 2
    assert diak[0]["headword"] == "дя́кування"
    assert "gratitude" in diak[0]["gloss"].lower() or "thank" in diak[0]["gloss"].lower()
    assert diak[1]["headword"] == "дякува́ння"
    assert "cantor" in diak[1]["gloss"].lower() or "deacon" in diak[1]["gloss"].lower()

    # корівник: корі́вник (cowshed / inanim) vs корівни́к (cowherd / anim)
    kor = enrich_heteronyms.build_heteronyms_for_lemma("корівник")
    assert kor is not None and len(kor) == 2
    assert kor[0]["headword"] == "корі́вник"
    assert kor[0]["morphology"]["paradigm"]["animacy"] == "inanimate"
    assert kor[0]["heritage_status"]["vesum_attested"] is True
    assert kor[1]["headword"] == "корівни́к"
    assert kor[1]["morphology"]["paradigm"]["animacy"] == "animate"
    assert kor[1]["heritage_status"]["vesum_attested"] is False

    # ламповий: ла́мповий (adj: tube/lamp) vs лампови́й (noun: mine lamp-tender)
    lam = enrich_heteronyms.build_heteronyms_for_lemma("ламповий")
    assert lam is not None and len(lam) == 2
    assert lam[0]["headword"] == "ла́мповий"
    assert lam[0]["pos"] == "adj"
    assert lam[0]["heritage_status"]["vesum_attested"] is True
    assert lam[1]["headword"] == "лампови́й"
    assert lam[1]["pos"] == "noun"
    assert lam[1]["heritage_status"]["vesum_attested"] is False

    # лупати: лу́пати (blink eyelids) vs лупа́ти (hew rock: Franko "Каменярі")
    lup = enrich_heteronyms.build_heteronyms_for_lemma("лупати")
    assert lup is not None and len(lup) == 2
    assert lup[0]["headword"] == "лу́пати"
    assert "blink" in lup[0]["gloss"].lower()
    assert lup[1]["headword"] == "лупа́ти"
    assert "hew" in lup[1]["gloss"].lower() or "break" in lup[1]["gloss"].lower() or "chip" in lup[1]["gloss"].lower()
    assert "Лупайте сю скалу" in lup[1]["pre_soviet_witness"]["quote"]

    # лютневий: лю́тневий (relating to lute) vs лютне́вий (February / winter)
    lut = enrich_heteronyms.build_heteronyms_for_lemma("лютневий")
    assert lut is not None and len(lut) == 2
    assert lut[0]["headword"] == "лю́тневий"
    assert "lute" in lut[0]["gloss"].lower()
    assert lut[1]["headword"] == "лютне́вий"
    assert "february" in lut[1]["gloss"].lower()

    # креснути: кре́снути (ice cracking/moving, imperf.) vs кресну́ти (strike spark, perf.)
    kre = enrich_heteronyms.build_heteronyms_for_lemma("креснути")
    assert kre is not None and len(kre) == 2
    assert kre[0]["headword"] == "кре́снути"
    assert kre[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert kre[1]["headword"] == "кресну́ти"
    assert kre[1]["morphology"]["paradigm"]["aspect"] == "доконаний"

    # находитися: нахо́дитися (be found / present, imperf., no birth sense) vs находи́тися (walk plenty, perf.)
    nah = enrich_heteronyms.build_heteronyms_for_lemma("находитися")
    assert nah is not None and len(nah) == 2
    assert nah[0]["headword"] == "нахо́дитися"
    assert nah[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert "born" not in nah[0]["gloss"].lower()
    assert "народжуватися" not in nah[0]["meaning"]["definitions"][0]
    assert nah[1]["headword"] == "находи́тися"
    assert nah[1]["morphology"]["paradigm"]["aspect"] == "доконаний"

    # зорювати: зо́рювати (plow) vs зорюва́ти (sleep outdoors under stars, Grinchenko)
    zor = enrich_heteronyms.build_heteronyms_for_lemma("зорювати")
    assert zor is not None and len(zor) == 2
    assert zor[0]["headword"] == "зо́рювати"
    assert "plow" in zor[0]["gloss"].lower()
    assert zor[1]["headword"] == "зорюва́ти"
    assert "outdoors" in zor[1]["gloss"].lower() or "stars" in zor[1]["gloss"].lower()

    # замикатися: замика́тися (lock / withdraw, imperf.) vs зами́катися (bustle restlessly, dial., perf.)
    zam = enrich_heteronyms.build_heteronyms_for_lemma("замикатися")
    assert zam is not None and len(zam) == 2
    assert zam[0]["headword"] == "замика́тися"
    assert zam[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert zam[1]["headword"] == "зами́катися"
    assert zam[1]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert "заметатися" in zam[1]["meaning"]["definitions"][0] or "заметушитися" in zam[1]["meaning"]["definitions"][0]
    assert "exhaust" not in zam[1]["gloss"].lower() and "wandering" not in zam[1]["gloss"].lower()
    assert "грінченко" not in zam[1]["stress"]["source"].lower()

    # колонковий: коло́нковий (cylindrical device / drill, tech.) vs колонко́вий (weasel / fur)
    kol = enrich_heteronyms.build_heteronyms_for_lemma("колонковий")
    assert kol is not None and len(kol) == 2
    assert kol[0]["headword"] == "коло́нковий"
    assert "newspaper" not in kol[0]["gloss"].lower() and "print" not in kol[0]["gloss"].lower()
    assert "друк" not in kol[0]["meaning"]["definitions"][0]
    assert kol[1]["headword"] == "колонко́вий"
    assert "weasel" in kol[1]["gloss"].lower() or "fur" in kol[1]["gloss"].lower()

    # консерваторка: консерва́торка (conservative woman) vs консервато́рка (female conservatory student)
    kon = enrich_heteronyms.build_heteronyms_for_lemma("консерваторка")
    assert kon is not None and len(kon) == 2
    assert kon[0]["headword"] == "консерва́торка"
    assert "conservative" in kon[0]["gloss"].lower()
    assert kon[1]["headword"] == "консервато́рка"
    assert "student" in kon[1]["gloss"].lower()
    assert "graduate" not in kon[1]["gloss"].lower() and "teacher" not in kon[1]["gloss"].lower()
    assert "викладачка" not in kon[1]["meaning"]["definitions"][0] and "випускниця" not in kon[1]["meaning"]["definitions"][0]


def test_batch8_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 8's 32 lemmas are net-new and mutually disjoint with batches 1-7."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6
    from scripts.lexicon.curated_heteronyms_batch7 import CURATED_HETERONYMS_BATCH_7
    from scripts.lexicon.curated_heteronyms_batch8 import CURATED_HETERONYMS_BATCH_8

    assert len(CURATED_HETERONYMS_BATCH_8) == 32
    assert sum(len(v) for v in CURATED_HETERONYMS_BATCH_8.values()) == 64
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
        | set(CURATED_HETERONYMS_BATCH_6)
        | set(CURATED_HETERONYMS_BATCH_7)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_8) == set()
    assert "вивозитися" in CURATED_HETERONYMS_BATCH_8
    assert "дякування" in CURATED_HETERONYMS_BATCH_8
    assert "захватний" in CURATED_HETERONYMS_BATCH_8
    assert "зорювати" in CURATED_HETERONYMS_BATCH_8
    assert "колонковий" in CURATED_HETERONYMS_BATCH_8
    assert "комірний" in CURATED_HETERONYMS_BATCH_8
    assert "ламповий" in CURATED_HETERONYMS_BATCH_8
    assert "лютневий" in CURATED_HETERONYMS_BATCH_8
    assert "лупати" in CURATED_HETERONYMS_BATCH_8
    assert "нарізний" in CURATED_HETERONYMS_BATCH_8
    assert "находитися" in CURATED_HETERONYMS_BATCH_8

    # Check pre-Soviet witnesses and author citations
    konservatorka = CURATED_HETERONYMS_BATCH_8["консерваторка"]
    assert "Леся Українка" in konservatorka[1]["pre_soviet_witness"]["witness"]
    assert "У мене сестра консерваторка" in konservatorka[1]["pre_soviet_witness"]["quote"]

    nahodytysya = CURATED_HETERONYMS_BATCH_8["находитися"]
    assert "Грінченко" in nahodytysya[0]["pre_soviet_witness"]["witness"]
    assert "Шевч." in nahodytysya[0]["pre_soviet_witness"]["quote"]

    lutnevyi = CURATED_HETERONYMS_BATCH_8["лютневий"]
    assert lutnevyi[0]["heritage_status"]["vesum_attested"] is True
    assert lutnevyi[1]["heritage_status"]["vesum_attested"] is True



def test_homonyms_with_numeric_suffixes_and_identical_stress_not_treated_as_heteronyms(monkeypatch):
    """Separate dictionary article numbers from headword before comparing stress (#8039).

    Ensures that homonyms with identical stress but distinct article numbers (e.g. ТЕ́СТ 1 and ТЕ́СТ 2)
    are not treated as heteronyms, and that numeric suffixes are stripped from headwords.
    """
    from scripts.lexicon import sum20_lookup

    synthetic_same_stress = {
        "lemma": "синтетичнийтест",
        "modern_sum20": [
            {
                "stressed_headword": "ТЕ́СТ 1",
                "grammar": "іменник",
                "senses": [{"definition": "Перше значення тесту"}],
            },
            {
                "stressed_headword": "ТЕ́СТ 2",
                "grammar": "іменник",
                "senses": [{"definition": "Друге значення тесту"}],
            },
        ],
        "soviet_colonization_context": None,
    }

    monkeypatch.setattr(
        sum20_lookup,
        "lookup_decolonized_heteronym_evidence",
        lambda lemma: synthetic_same_stress,
    )
    result_same = enrich_heteronyms.build_heteronyms_for_lemma("синтетичнийтест")
    assert result_same is None

    synthetic_diff_stress = {
        "lemma": "синтетичнийтест",
        "modern_sum20": [
            {
                "stressed_headword": "ТЕ́СТ 1",
                "grammar": "іменник",
                "senses": [{"definition": "Перше значення тесту"}],
            },
            {
                "stressed_headword": "ТЕСТІ́ 2",
                "grammar": "іменник",
                "senses": [{"definition": "Друге значення тесту"}],
            },
        ],
        "soviet_colonization_context": None,
    }

    monkeypatch.setattr(
        sum20_lookup,
        "lookup_decolonized_heteronym_evidence",
        lambda lemma: synthetic_diff_stress,
    )
    result_diff = enrich_heteronyms.build_heteronyms_for_lemma("синтетичнийтест")
    assert result_diff is not None
    assert len(result_diff) == 2
    assert result_diff[0]["headword"] == "ТЕ́СТ"
    assert result_diff[1]["headword"] == "ТЕСТІ́"


def test_build_heteronyms_for_lemma_preserves_all_homonyms_when_stresses_differ(monkeypatch):
    """Verify that when multiple articles share stress but at least one differs, ALL articles are preserved."""
    from scripts.lexicon import sum20_lookup

    synthetic_three_articles = {
        "lemma": "синтетичнийтест",
        "modern_sum20": [
            {
                "stressed_headword": "ТЕ́СТ 1",
                "grammar": "іменник",
                "senses": [{"definition": "Перше значення тесту"}],
            },
            {
                "stressed_headword": "ТЕ́СТ 2",
                "grammar": "іменник",
                "senses": [{"definition": "Друге значення тесту"}],
            },
            {
                "stressed_headword": "ТЕСТІ́ 3",
                "grammar": "іменник",
                "senses": [{"definition": "Третє значення тесту"}],
            },
        ],
        "soviet_colonization_context": None,
    }

    monkeypatch.setattr(
        sum20_lookup,
        "lookup_decolonized_heteronym_evidence",
        lambda lemma: synthetic_three_articles,
    )
    result = enrich_heteronyms.build_heteronyms_for_lemma("синтетичнийтест")
    assert result is not None
    assert len(result) == 3
    assert result[0]["headword"] == "ТЕ́СТ"
    assert result[0]["gloss"] == "Перше значення тесту"
    assert result[1]["headword"] == "ТЕ́СТ"
    assert result[1]["gloss"] == "Друге значення тесту"
    assert result[2]["headword"] == "ТЕСТІ́"
    assert result[2]["gloss"] == "Третє значення тесту"
