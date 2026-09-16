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
    Batch 9 (#8039 continuation): +32 lemmas selected from academic authorities and
    Grinchenko (1907) with explicit pre-Soviet witness citations and Soviet
    colonization context, expanding SSOT to 296 and dropping residual to 126.
    Batch 10 (#8039 continuation): +32 lemmas selected from academic authorities and
    Grinchenko (1907) with explicit pre-Soviet witness citations and Soviet
    colonization context, expanding SSOT to 328 and dropping residual to 94.
    Batch 11 (#8039 continuation): +32 lemmas selected from academic authorities and
    Grinchenko (1907) with explicit pre-Soviet witness citations and Soviet
    colonization context, expanding SSOT to 360 and dropping residual to 62.
    Batch 12 (#8039 continuation): +32 lemmas selected from academic authorities and
    Grinchenko (1907) with explicit pre-Soviet witness citations and Soviet
    colonization context, expanding SSOT to 392 and dropping residual to 30.
    """
    total_curated = len(enrich_heteronyms.CURATED_HETERONYMS)
    assert total_curated == 392
    # Corrected denominator is 422 true two-way-stress candidates;
    # residual is 422 - 392 = 30
    assert 422 - total_curated == 30


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

    # дякування: дя́кування (thanking / gratitude) vs дякува́ння (serving as parish cantor / church reader)
    diak = enrich_heteronyms.build_heteronyms_for_lemma("дякування")
    assert diak is not None and len(diak) == 2
    assert diak[0]["headword"] == "дя́кування"
    assert "gratitude" in diak[0]["gloss"].lower() or "thank" in diak[0]["gloss"].lower()
    assert diak[1]["headword"] == "дякува́ння"
    assert "cantor" in diak[1]["gloss"].lower()
    assert "deacon" not in diak[1]["gloss"].lower()

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

    # значитися: зна́читися (be listed/registered, imperf.) vs значи́тися (be marked/stand out, imperf.)
    zn = enrich_heteronyms.build_heteronyms_for_lemma("значитися")
    assert zn is not None and len(zn) == 2
    assert zn[0]["headword"] == "зна́читися"
    assert "signify" not in zn[0]["gloss"].lower() and "have meaning" not in zn[0]["gloss"].lower()
    assert "важити" not in zn[0]["distinction_note"] and "мати значення" not in zn[0]["distinction_note"]
    assert "списк" in zn[0]["meaning"]["definitions"][0] or "реєстр" in zn[0]["meaning"]["definitions"][0]
    assert zn[1]["headword"] == "значи́тися"

    # зольник: зо́льник (archaeological ash mound) vs зольни́к (furnace ash-pit, tech.)
    zol = enrich_heteronyms.build_heteronyms_for_lemma("зольник")
    assert zol is not None and len(zol) == 2
    assert zol[0]["headword"] == "зо́льник"
    assert "archaeological" in zol[0]["gloss"].lower() or "mound" in zol[0]["gloss"].lower()
    assert zol[1]["headword"] == "зольни́к"
    assert "tanning" not in zol[1]["gloss"].lower() and "hide" not in zol[1]["gloss"].lower()
    assert "шкір" not in zol[1]["meaning"]["definitions"][0] and "чинбар" not in zol[1]["meaning"]["definitions"][0]
    assert "піддувало" in zol[1]["meaning"]["definitions"][0] or "топк" in zol[1]["meaning"]["definitions"][0]


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


def test_batch9_semantic_and_stress_distinctions():
    """Verify Batch 9 stress and semantic distinctions against academic authorities and Grinchenko."""
    # лупання: лу́пання (blinking eyelids) vs лупа́ння (chipping rock/ore)
    lup = enrich_heteronyms.build_heteronyms_for_lemma("лупання")
    assert lup is not None and len(lup) == 2
    assert lup[0]["headword"] == "лу́пання"
    assert "blinking" in lup[0]["gloss"].lower()
    assert lup[1]["headword"] == "лупа́ння"
    assert "peeling" in lup[1]["gloss"].lower() or "chipping" in lup[1]["gloss"].lower() or "quarrying" in lup[1]["gloss"].lower()

    # люстровий: лю́стровий (chandelier) vs люстро́вий (lustrine fabric / mirror)
    lus = enrich_heteronyms.build_heteronyms_for_lemma("люстровий")
    assert lus is not None and len(lus) == 2
    assert lus[0]["headword"] == "лю́стровий"
    assert "chandelier" in lus[0]["gloss"].lower()
    assert lus[1]["headword"] == "люстро́вий"
    assert "lustrine" in lus[1]["gloss"].lower() or "mirror" in lus[1]["gloss"].lower()

    # маячний: мая́чний (lighthouse/beacon) vs маячни́й (delirious/hallucinatory)
    may = enrich_heteronyms.build_heteronyms_for_lemma("маячний")
    assert may is not None and len(may) == 2
    assert may[0]["headword"] == "мая́чний"
    assert "lighthouse" in may[0]["gloss"].lower() or "beacon" in may[0]["gloss"].lower()
    assert may[1]["headword"] == "маячни́й"
    assert "delirious" in may[1]["gloss"].lower() or "feverish" in may[1]["gloss"].lower()

    # набігати: набі́гати (perf., acquire by running) vs набіга́ти (imperf., surge/rush onto)
    nab = enrich_heteronyms.build_heteronyms_for_lemma("набігати")
    assert nab is not None and len(nab) == 2
    assert nab[0]["headword"] == "набі́гати"
    assert nab[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert nab[1]["headword"] == "набіга́ти"
    assert nab[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # набухати: набу́хати (perf., pour/dump plenty) vs набуха́ти (imperf., swell up)
    nbh = enrich_heteronyms.build_heteronyms_for_lemma("набухати")
    assert nbh is not None and len(nbh) == 2
    assert nbh[0]["headword"] == "набу́хати"
    assert nbh[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert nbh[1]["headword"] == "набуха́ти"
    assert nbh[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # наварний: нава́рний (rich broth) vs наварни́й (welded-on, tech.)
    nav = enrich_heteronyms.build_heteronyms_for_lemma("наварний")
    assert nav is not None and len(nav) == 2
    assert nav[0]["headword"] == "нава́рний"
    assert "broth" in nav[0]["gloss"].lower() or "rich" in nav[0]["gloss"].lower()
    assert nav[1]["headword"] == "наварни́й"
    assert "welded" in nav[1]["gloss"].lower()

    # навозити: наво́зити (imperf., cart in quantity) vs навози́ти (perf., haul multiple trips or fertilize)
    nvz = enrich_heteronyms.build_heteronyms_for_lemma("навозити")
    assert nvz is not None and len(nvz) == 2
    assert nvz[0]["headword"] == "наво́зити"
    assert nvz[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert nvz[1]["headword"] == "навози́ти"
    assert nvz[1]["morphology"]["paradigm"]["aspect"] == "доконаний"

    # назубок: назу́бок (noun: special file) vs назубо́к (adv: by heart, thoroughly)
    naz = enrich_heteronyms.build_heteronyms_for_lemma("назубок")
    assert naz is not None and len(naz) == 2
    assert naz[0]["headword"] == "назу́бок"
    assert naz[0]["pos"] == "noun"
    assert naz[1]["headword"] == "назубо́к"
    assert naz[1]["pos"] == "adv"

    # наслухати: наслу́хати (perf., hear through rumors) vs наслуха́ти (imperf., listen intently)
    nsl = enrich_heteronyms.build_heteronyms_for_lemma("наслухати")
    assert nsl is not None and len(nsl) == 2
    assert nsl[0]["headword"] == "наслу́хати"
    assert nsl[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert nsl[1]["headword"] == "наслуха́ти"
    assert nsl[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # настильний: насти́льний (flat-trajectory, mil.) vs настильни́й (flooring/decking)
    nas = enrich_heteronyms.build_heteronyms_for_lemma("настильний")
    assert nas is not None and len(nas) == 2
    assert nas[0]["headword"] == "насти́льний"
    assert "trajectory" in nas[0]["gloss"].lower() or "flat" in nas[0]["gloss"].lower()
    assert nas[1]["headword"] == "настильни́й"
    assert "flooring" in nas[1]["gloss"].lower() or "decking" in nas[1]["gloss"].lower()

    # невигода: неви́года (material loss) vs невиго́да (inconvenience, discomfort)
    nev = enrich_heteronyms.build_heteronyms_for_lemma("невигода")
    assert nev is not None and len(nev) == 2
    assert nev[0]["headword"] == "неви́года"
    assert "loss" in nev[0]["gloss"].lower() or "profit" in nev[0]["gloss"].lower()
    assert nev[1]["headword"] == "невиго́да"
    assert "inconvenience" in nev[1]["gloss"].lower() or "discomfort" in nev[1]["gloss"].lower()

    # неперехідний: неперехі́дний (impassable) vs неперехідни́й (intransitive)
    nep = enrich_heteronyms.build_heteronyms_for_lemma("неперехідний")
    assert nep is not None and len(nep) == 2
    assert nep[0]["headword"] == "неперехі́дний"
    assert "impassable" in nep[0]["gloss"].lower() or "uncrossable" in nep[0]["gloss"].lower()
    assert nep[1]["headword"] == "неперехідни́й"
    assert "intransitive" in nep[1]["gloss"].lower()

    # неповоротний: неповоро́тний (irreversible) vs неповоротни́й (clumsy/unwieldy)
    npv = enrich_heteronyms.build_heteronyms_for_lemma("неповоротний")
    assert npv is not None and len(npv) == 2
    assert npv[0]["headword"] == "неповоро́тний"
    assert "irreversible" in npv[0]["gloss"].lower() or "irrevocable" in npv[0]["gloss"].lower()
    assert npv[1]["headword"] == "неповоротни́й"
    assert "clumsy" in npv[1]["gloss"].lower() or "unwieldy" in npv[1]["gloss"].lower()

    # оббігати: оббі́гати (perf., visit many places) vs оббіга́ти (imperf., run around in circle)
    obb = enrich_heteronyms.build_heteronyms_for_lemma("оббігати")
    assert obb is not None and len(obb) == 2
    assert obb[0]["headword"] == "оббі́гати"
    assert obb[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert obb[1]["headword"] == "оббіга́ти"
    assert obb[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # обводити: обво́дити (imperf., outline/lead around) vs обводи́ти (perf., take someone everywhere)
    obv = enrich_heteronyms.build_heteronyms_for_lemma("обводити")
    assert obv is not None and len(obv) == 2
    assert obv[0]["headword"] == "обво́дити"
    assert obv[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert obv[1]["headword"] == "обводи́ти"
    assert obv[1]["morphology"]["paradigm"]["aspect"] == "доконаний"

    # обідець: обі́дець (small nice dinner/meal) vs обіде́ць (small rim/hoop)
    obi = enrich_heteronyms.build_heteronyms_for_lemma("обідець")
    assert obi is not None and len(obi) == 2
    assert obi[0]["headword"] == "обі́дець"
    assert "dinner" in obi[0]["gloss"].lower() or "meal" in obi[0]["gloss"].lower()
    assert obi[1]["headword"] == "обіде́ць"
    assert "rim" in obi[1]["gloss"].lower() or "hoop" in obi[1]["gloss"].lower()

    # обрізання: обрі́зання (circumcision rite) vs обріза́ння (pruning/trimming)
    obr = enrich_heteronyms.build_heteronyms_for_lemma("обрізання")
    assert obr is not None and len(obr) == 2
    assert obr[0]["headword"] == "обрі́зання"
    assert "circumcision" in obr[0]["gloss"].lower()
    assert obr[1]["headword"] == "обріза́ння"
    assert "pruning" in obr[1]["gloss"].lower() or "trimming" in obr[1]["gloss"].lower()

    # окісний: о́кісний (culinary, gammon/ham) vs окі́сний (anatomy, periosteal)
    oki = enrich_heteronyms.build_heteronyms_for_lemma("окісний")
    assert oki is not None and len(oki) == 2
    assert oki[0]["headword"] == "о́кісний"
    assert "ham" in oki[0]["gloss"].lower() or "gammon" in oki[0]["gloss"].lower()
    assert oki[1]["headword"] == "окі́сний"
    assert "periosteal" in oki[1]["gloss"].lower()

    # окружний: окру́жний (roundabout/detour) vs окружни́й (district/regional)
    okr = enrich_heteronyms.build_heteronyms_for_lemma("окружний")
    assert okr is not None and len(okr) == 2
    assert okr[0]["headword"] == "окру́жний"
    assert "roundabout" in okr[0]["gloss"].lower() or "circuitous" in okr[0]["gloss"].lower()
    assert okr[1]["headword"] == "окружни́й"
    assert "district" in okr[1]["gloss"].lower() or "regional" in okr[1]["gloss"].lower()

    # описка: о́писка (potter's clay pigment) vs опи́ска (slip of the pen)
    opy = enrich_heteronyms.build_heteronyms_for_lemma("описка")
    assert opy is not None and len(opy) == 2
    assert opy[0]["headword"] == "о́писка"
    assert "clay" in opy[0]["gloss"].lower() or "potter" in opy[0]["gloss"].lower()
    assert opy[1]["headword"] == "опи́ска"
    assert "pen" in opy[1]["gloss"].lower() or "writing" in opy[1]["gloss"].lower()

    # пахолок: па́холок (withers of horse) vs пахо́лок (page, squire, servant lad)
    pah = enrich_heteronyms.build_heteronyms_for_lemma("пахолок")
    assert pah is not None and len(pah) == 2
    assert pah[0]["headword"] == "па́холок"
    assert pah[0]["morphology"]["paradigm"]["animacy"] == "inanimate"
    assert pah[1]["headword"] == "пахо́лок"
    assert pah[1]["morphology"]["paradigm"]["animacy"] == "animate"

    # перевозити: перево́зити (imperf.) vs перевози́ти (perf.)
    prv = enrich_heteronyms.build_heteronyms_for_lemma("перевозити")
    assert prv is not None and len(prv) == 2
    assert prv[0]["headword"] == "перево́зити"
    assert prv[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert prv[1]["headword"] == "перевози́ти"
    assert prv[1]["morphology"]["paradigm"]["aspect"] == "доконаний"

    # перекладка: пере́кладка (crossbar/strut) vs перекла́дка (repositioning/relaying)
    prk = enrich_heteronyms.build_heteronyms_for_lemma("перекладка")
    assert prk is not None and len(prk) == 2
    assert prk[0]["headword"] == "пере́кладка"
    assert "crossbar" in prk[0]["gloss"].lower() or "crossbeam" in prk[0]["gloss"].lower()
    assert prk[1]["headword"] == "перекла́дка"
    assert "repositioning" in prk[1]["gloss"].lower() or "shifting" in prk[1]["gloss"].lower()
    assert "translat" not in prk[1]["gloss"].lower()
    for v in prk:
        assert "переклад тексту" not in v["distinction_note"].lower()
        assert "translat" not in v["gloss"].lower()
        assert "переклад тексту" not in v["short_label"].lower()
        for d in v["meaning"]["definitions"]:
            assert "переклад тексту" not in d.lower()

    # переливний: перели́вний (iridescent) vs переливни́й (overflow/spillway)
    prl = enrich_heteronyms.build_heteronyms_for_lemma("переливний")
    assert prl is not None and len(prl) == 2
    assert prl[0]["headword"] == "перели́вний"
    assert "iridescent" in prl[0]["gloss"].lower() or "shimmering" in prl[0]["gloss"].lower()
    assert prl[1]["headword"] == "переливни́й"
    assert "overflow" in prl[1]["gloss"].lower() or "spillway" in prl[1]["gloss"].lower()

    # переруб: пере́руб (grain bin, dial.) vs переру́б (overlogging, forestry)
    prr = enrich_heteronyms.build_heteronyms_for_lemma("переруб")
    assert prr is not None and len(prr) == 2
    assert prr[0]["headword"] == "пере́руб"
    assert "bin" in prr[0]["gloss"].lower() or "granary" in prr[0]["gloss"].lower()
    assert prr[1]["headword"] == "переру́б"
    assert "overlogging" in prr[1]["gloss"].lower() or "cut" in prr[1]["gloss"].lower()

    # попадати: попа́дати (perf., fall down) vs попада́ти (imperf., hit target)
    pop = enrich_heteronyms.build_heteronyms_for_lemma("попадати")
    assert pop is not None and len(pop) == 2
    assert pop[0]["headword"] == "попа́дати"
    assert pop[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert pop[1]["headword"] == "попада́ти"
    assert pop[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # посипатися: поси́патися (perf., tumble down) vs посипа́тися (imperf., be sprinkled)
    pos = enrich_heteronyms.build_heteronyms_for_lemma("посипатися")
    assert pos is not None and len(pos) == 2
    assert pos[0]["headword"] == "поси́патися"
    assert pos[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert pos[1]["headword"] == "посипа́тися"
    assert pos[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # пригар: при́гар (burnt smell/taste, dial.) vs прига́р (burnt sand crust on casting, tech.)
    pri = enrich_heteronyms.build_heteronyms_for_lemma("пригар")
    assert pri is not None and len(pri) == 2
    assert pri[0]["headword"] == "при́гар"
    assert "burnt" in pri[0]["gloss"].lower() or "scorched" in pri[0]["gloss"].lower()
    assert pri[1]["headword"] == "прига́р"
    assert "casting" in pri[1]["gloss"].lower() or "scab" in pri[1]["gloss"].lower()

    # провозити: прово́зити (imperf.) vs провози́ти (perf.)
    prv2 = enrich_heteronyms.build_heteronyms_for_lemma("провозити")
    assert prv2 is not None and len(prv2) == 2
    assert prv2[0]["headword"] == "прово́зити"
    assert prv2[0]["morphology"]["paradigm"]["aspect"] == "недоконаний"
    assert prv2[1]["headword"] == "провози́ти"
    assert prv2[1]["morphology"]["paradigm"]["aspect"] == "доконаний"

    # розбігатися: розбі́гатися (perf., bustle about) vs розбіга́тися (imperf., scatter)
    roz = enrich_heteronyms.build_heteronyms_for_lemma("розбігатися")
    assert roz is not None and len(roz) == 2
    assert roz[0]["headword"] == "розбі́гатися"
    assert roz[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert roz[1]["headword"] == "розбіга́тися"
    assert roz[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # рябець: ря́бець (kite bird) vs рябе́ць (grouse, Tetrastes bonasia)
    ryb = enrich_heteronyms.build_heteronyms_for_lemma("рябець")
    assert ryb is not None and len(ryb) == 2
    assert ryb[0]["headword"] == "ря́бець"
    assert "kite" in ryb[0]["gloss"].lower() or "prey" in ryb[0]["gloss"].lower()
    assert ryb[1]["headword"] == "рябе́ць"
    assert "grouse" in ryb[1]["gloss"].lower() or "tetrastes" in ryb[1]["gloss"].lower()

    # травник: тра́вник (herbarium / herbal book) vs травни́к (grassy plot / lawn)
    trv = enrich_heteronyms.build_heteronyms_for_lemma("травник")
    assert trv is not None and len(trv) == 2
    assert trv[0]["headword"] == "тра́вник"
    assert "herbarium" in trv[0]["gloss"].lower() or "herbal" in trv[0]["gloss"].lower()
    assert trv[1]["headword"] == "травни́к"
    assert "lawn" in trv[1]["gloss"].lower() or "grassy" in trv[1]["gloss"].lower()
    assert "tincture" not in trv[1]["gloss"].lower()
    assert trv[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "травника́"
    for v in trv:
        assert "настоянк" not in v["distinction_note"].lower()
        assert "tincture" not in v["gloss"].lower()
        assert "настоянк" not in v["short_label"].lower()
        for d in v["meaning"]["definitions"]:
            assert "настоянк" not in d.lower()


def test_batch9_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 9's 32 lemmas are net-new and mutually disjoint with batches 1-8."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6
    from scripts.lexicon.curated_heteronyms_batch7 import CURATED_HETERONYMS_BATCH_7
    from scripts.lexicon.curated_heteronyms_batch8 import CURATED_HETERONYMS_BATCH_8
    from scripts.lexicon.curated_heteronyms_batch9 import CURATED_HETERONYMS_BATCH_9

    assert len(CURATED_HETERONYMS_BATCH_9) == 32
    assert sum(len(v) for v in CURATED_HETERONYMS_BATCH_9.values()) == 64
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
        | set(CURATED_HETERONYMS_BATCH_6)
        | set(CURATED_HETERONYMS_BATCH_7)
        | set(CURATED_HETERONYMS_BATCH_8)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_9) == set()
    assert "лупання" in CURATED_HETERONYMS_BATCH_9
    assert "люстровий" in CURATED_HETERONYMS_BATCH_9
    assert "маячний" in CURATED_HETERONYMS_BATCH_9
    assert "набігати" in CURATED_HETERONYMS_BATCH_9
    assert "набухати" in CURATED_HETERONYMS_BATCH_9
    assert "наварний" in CURATED_HETERONYMS_BATCH_9
    assert "навозити" in CURATED_HETERONYMS_BATCH_9
    assert "назубок" in CURATED_HETERONYMS_BATCH_9
    assert "наслухати" in CURATED_HETERONYMS_BATCH_9
    assert "настильний" in CURATED_HETERONYMS_BATCH_9
    assert "невигода" in CURATED_HETERONYMS_BATCH_9
    assert "неперехідний" in CURATED_HETERONYMS_BATCH_9
    assert "неповоротний" in CURATED_HETERONYMS_BATCH_9
    assert "оббігати" in CURATED_HETERONYMS_BATCH_9
    assert "обводити" in CURATED_HETERONYMS_BATCH_9
    assert "обідець" in CURATED_HETERONYMS_BATCH_9
    assert "обрізання" in CURATED_HETERONYMS_BATCH_9
    assert "окісний" in CURATED_HETERONYMS_BATCH_9
    assert "окружний" in CURATED_HETERONYMS_BATCH_9
    assert "описка" in CURATED_HETERONYMS_BATCH_9
    assert "пахолок" in CURATED_HETERONYMS_BATCH_9
    assert "перевозити" in CURATED_HETERONYMS_BATCH_9
    assert "перекладка" in CURATED_HETERONYMS_BATCH_9
    assert "переливний" in CURATED_HETERONYMS_BATCH_9
    assert "переруб" in CURATED_HETERONYMS_BATCH_9
    assert "попадати" in CURATED_HETERONYMS_BATCH_9
    assert "посипатися" in CURATED_HETERONYMS_BATCH_9
    assert "пригар" in CURATED_HETERONYMS_BATCH_9
    assert "провозити" in CURATED_HETERONYMS_BATCH_9
    assert "розбігатися" in CURATED_HETERONYMS_BATCH_9
    assert "рябець" in CURATED_HETERONYMS_BATCH_9
    assert "травник" in CURATED_HETERONYMS_BATCH_9

    # Check pre-Soviet witnesses
    lupannya = CURATED_HETERONYMS_BATCH_9["лупання"]
    assert "Грінченко" in lupannya[0]["pre_soviet_witness"]["witness"]
    assert "Миганіе" in lupannya[0]["pre_soviet_witness"]["quote"]
    assert "Откалываніе" in lupannya[1]["pre_soviet_witness"]["quote"]

    obidets = CURATED_HETERONYMS_BATCH_9["обідець"]
    assert "Грінченко" in obidets[0]["pre_soviet_witness"]["witness"]
    assert "обід" in obidets[0]["pre_soviet_witness"]["quote"].lower()
    assert "Ободок" in obidets[1]["pre_soviet_witness"]["quote"]

    # Morphology check: лупання must be singular-only, переруб genitive must be пере́рубу, травник genitive must be травника́
    assert "plural" not in lupannya[0]["morphology"]["paradigm"]["cases"]["називний"]
    assert "plural" not in lupannya[1]["morphology"]["paradigm"]["cases"]["називний"]
    pererub = CURATED_HETERONYMS_BATCH_9["переруб"]
    assert pererub[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "пере́рубу"
    travnik = CURATED_HETERONYMS_BATCH_9["травник"]
    assert travnik[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "травника́"

    # Decolonization check: no normative СУМ-11 citations outside soviet_colonization_context
    for lemma, variants in CURATED_HETERONYMS_BATCH_9.items():
        for v in variants:
            assert "СУМ-11" not in v["meaning"]["source"], f"Found СУМ-11 in meaning.source for {lemma}"
            assert "СУМ-11" not in v["stress"]["source"], f"Found СУМ-11 in stress.source for {lemma}"


def test_batch10_semantic_and_stress_distinctions():
    """Verify Batch 10 stress and semantic distinctions against academic authorities and Grinchenko."""
    # виїмковий: ви́їмковий (mining extraction) vs виїмко́вий (exceptional/singular, dial.)
    vyi = enrich_heteronyms.build_heteronyms_for_lemma("виїмковий")
    assert vyi is not None and len(vyi) == 2
    assert vyi[0]["headword"] == "ви́їмковий"
    assert "mining" in vyi[0]["gloss"].lower() or "extraction" in vyi[0]["gloss"].lower()
    assert vyi[1]["headword"] == "виїмко́вий"
    assert "exceptional" in vyi[1]["gloss"].lower() or "extraordinary" in vyi[1]["gloss"].lower()

    # люковий: лю́ковий (hatch/trapdoor) vs люкови́й (hatch worker/operator)
    lyu = enrich_heteronyms.build_heteronyms_for_lemma("люковий")
    assert lyu is not None and len(lyu) == 2
    assert lyu[0]["headword"] == "лю́ковий"
    assert "hatch" in lyu[0]["gloss"].lower()
    assert lyu[1]["headword"] == "люкови́й"
    assert "worker" in lyu[1]["gloss"].lower() or "operator" in lyu[1]["gloss"].lower()

    # магістерський: магі́стерський (chivalric grand master) vs магісте́рський (academic master's degree)
    mag = enrich_heteronyms.build_heteronyms_for_lemma("магістерський")
    assert mag is not None and len(mag) == 2
    assert mag[0]["headword"] == "магі́стерський"
    assert mag[0]["pronunciation"]["ipa"] == "[mɐˈɦistɛrsʲkɪj]"
    assert "master" in mag[0]["gloss"].lower() and "chivalric" in mag[0]["gloss"].lower()
    assert mag[1]["headword"] == "магісте́рський"
    assert "academic" in mag[1]["gloss"].lower() or "degree" in mag[1]["gloss"].lower()

    # масничка: ма́сничка (carnival/Masnytsia) vs масни́чка (butter churn)
    mas = enrich_heteronyms.build_heteronyms_for_lemma("масничка")
    assert mas is not None and len(mas) == 2
    assert mas[0]["headword"] == "ма́сничка"
    assert "masnytsia" in mas[0]["gloss"].lower() or "carnival" in mas[0]["gloss"].lower()
    assert mas[1]["headword"] == "масни́чка"
    assert "churn" in mas[1]["gloss"].lower() or "butter" in mas[1]["gloss"].lower()

    # нагніт: на́гніт (oppression/tyranny) vs нагні́т (withers gall in horses)
    nag = enrich_heteronyms.build_heteronyms_for_lemma("нагніт")
    assert nag is not None and len(nag) == 2
    assert nag[0]["headword"] == "на́гніт"
    assert nag[0]["soviet_colonization_context"]["sovietization_risk"] == 1
    assert "глитай" in nag[0]["soviet_colonization_context"]["keywords"]
    assert "oppression" in nag[0]["gloss"].lower() or "tyranny" in nag[0]["gloss"].lower()
    assert nag[1]["headword"] == "нагні́т"
    assert "gall" in nag[1]["gloss"].lower() or "sore" in nag[1]["gloss"].lower() or "withers" in nag[1]["gloss"].lower()

    # накликатися: накли́катися (perf., call until exhausted) vs наклика́тися (imperf., volunteer/invite oneself)
    nak = enrich_heteronyms.build_heteronyms_for_lemma("накликатися")
    assert nak is not None and len(nak) == 2
    assert nak[0]["headword"] == "накли́катися"
    assert nak[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert nak[1]["headword"] == "наклика́тися"
    assert nak[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # наривний: нари́вний (abscess/boil) vs наривни́й (suppurative/drawing plaster)
    nar = enrich_heteronyms.build_heteronyms_for_lemma("наривний")
    assert nar is not None and len(nar) == 2
    assert nar[0]["headword"] == "нари́вний"
    assert "abscess" in nar[0]["gloss"].lower() or "boil" in nar[0]["gloss"].lower()
    assert nar[1]["headword"] == "наривни́й"
    assert "suppurative" in nar[1]["gloss"].lower() or "plaster" in nar[1]["gloss"].lower() or "blister" in nar[1]["gloss"].lower()

    # наслухатися: наслу́хатися (perf., hear plenty) vs наслуха́тися (imperf., strain ears to listen)
    nasl = enrich_heteronyms.build_heteronyms_for_lemma("наслухатися")
    assert nasl is not None and len(nasl) == 2
    assert nasl[0]["headword"] == "наслу́хатися"
    assert nasl[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert nasl[1]["headword"] == "наслуха́тися"
    assert nasl[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # натруска: на́труска (historic powder horn) vs натру́ска (sprinkling or reprimand)
    nat = enrich_heteronyms.build_heteronyms_for_lemma("натруска")
    assert nat is not None and len(nat) == 2
    assert nat[0]["headword"] == "на́труска"
    assert "powder horn" in nat[0]["gloss"].lower() or "flask" in nat[0]["gloss"].lower()
    assert nat[1]["headword"] == "натру́ска"
    assert "sprinkling" in nat[1]["gloss"].lower() or "reprimand" in nat[1]["gloss"].lower()

    # невигідність: неви́гідність (unprofitability) vs невигі́дність (inconvenience/discomfort)
    nevy = enrich_heteronyms.build_heteronyms_for_lemma("невигідність")
    assert nevy is not None and len(nevy) == 2
    assert nevy[0]["headword"] == "неви́гідність"
    assert "unprofitability" in nevy[0]["gloss"].lower() or "disadvantage" in nevy[0]["gloss"].lower()
    assert nevy[1]["headword"] == "невигі́дність"
    assert "inconvenience" in nevy[1]["gloss"].lower() or "discomfort" in nevy[1]["gloss"].lower()

    # нівідки: ні́відки (absence of source, dial.) vs ніві́дки (from no place, dial./lit.)
    niv = enrich_heteronyms.build_heteronyms_for_lemma("нівідки")
    assert niv is not None and len(niv) == 2
    assert niv[0]["headword"] == "ні́відки"
    assert niv[0]["pos"] == "adv"
    assert "source" in niv[0]["gloss"].lower() or "obtain" in niv[0]["gloss"].lower() or "nowhere to get" in niv[0]["gloss"].lower()
    assert niv[1]["headword"] == "ніві́дки"
    assert niv[1]["pos"] == "adv"
    assert "no place" in niv[1]["gloss"].lower() or "nowhere" in niv[1]["gloss"].lower()

    # обрость: о́брость (biofouling/water organisms) vs обро́сть (young shoots/offspring)
    obr = enrich_heteronyms.build_heteronyms_for_lemma("обрость")
    assert obr is not None and len(obr) == 2
    assert obr[0]["headword"] == "о́брость"
    assert "biofouling" in obr[0]["gloss"].lower() or "aquatic" in obr[0]["gloss"].lower()
    assert obr[1]["headword"] == "обро́сть"
    assert "shoots" in obr[1]["gloss"].lower() or "offspring" in obr[1]["gloss"].lower()

    # перекочування: переко́чування (rolling across) vs перекочува́ння (relocation / nomadic migration)
    per = enrich_heteronyms.build_heteronyms_for_lemma("перекочування")
    assert per is not None and len(per) == 2
    assert per[0]["headword"] == "переко́чування"
    assert "rolling" in per[0]["gloss"].lower()
    assert per[1]["headword"] == "перекочува́ння"
    assert "relocation" in per[1]["gloss"].lower() or "migration" in per[1]["gloss"].lower()

    # переплавний: перепла́вний (Mid-Pentecost) vs переплавни́й (remelted/smelted)
    pep = enrich_heteronyms.build_heteronyms_for_lemma("переплавний")
    assert pep is not None and len(pep) == 2
    assert pep[0]["headword"] == "перепла́вний"
    assert "pentecost" in pep[0]["gloss"].lower()
    assert pep[1]["headword"] == "переплавни́й"
    assert "remelted" in pep[1]["gloss"].lower() or "smelted" in pep[1]["gloss"].lower()

    # переповзати: перепо́взати (perf.) vs переповза́ти (imperf.)
    ppv = enrich_heteronyms.build_heteronyms_for_lemma("переповзати")
    assert ppv is not None and len(ppv) == 2
    assert ppv[0]["headword"] == "перепо́взати"
    assert ppv[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert ppv[1]["headword"] == "переповза́ти"
    assert ppv[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # перетіпати: переті́пати (shake/chills, perf.) vs перетіпа́ти (scutch flax, perf.)
    ptp = enrich_heteronyms.build_heteronyms_for_lemma("перетіпати")
    assert ptp is not None and len(ptp) == 2
    assert ptp[0]["headword"] == "переті́пати"
    assert ptp[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert ptp[1]["headword"] == "перетіпа́ти"
    assert ptp[1]["morphology"]["paradigm"]["aspect"] == "доконаний"

    # пікірування: пікі́рування (aviation dive) vs пікірува́ння (horticulture pricking out)
    pik = enrich_heteronyms.build_heteronyms_for_lemma("пікірування")
    assert pik is not None and len(pik) == 2
    assert pik[0]["headword"] == "пікі́рування"
    assert "dive" in pik[0]["gloss"].lower()
    assert pik[1]["headword"] == "пікірува́ння"
    assert "pricking" in pik[1]["gloss"].lower() or "transplanting" in pik[1]["gloss"].lower()

    # пікірувати: пікі́рувати (dive in airplane) vs пікірува́ти (transplant seedlings)
    pkv = enrich_heteronyms.build_heteronyms_for_lemma("пікірувати")
    assert pkv is not None and len(pkv) == 2
    assert pkv[0]["headword"] == "пікі́рувати"
    assert "dive" in pkv[0]["gloss"].lower()
    assert pkv[1]["headword"] == "пікірува́ти"
    assert "transplant" in pkv[1]["gloss"].lower() or "prick out" in pkv[1]["gloss"].lower()
    assert pkv[1]["morphology"]["paradigm"]["aspect"] == "недоконаний і доконаний"

    # пікіруватися: пікі́руватися (bicker/spar) vs пікірува́тися (be transplanted)
    pks = enrich_heteronyms.build_heteronyms_for_lemma("пікіруватися")
    assert pks is not None and len(pks) == 2
    assert pks[0]["headword"] == "пікі́руватися"
    assert "bicker" in pks[0]["gloss"].lower() or "spar" in pks[0]["gloss"].lower()
    assert pks[1]["headword"] == "пікірува́тися"
    assert "transplanted" in pks[1]["gloss"].lower() or "passive" in pks[1]["gloss"].lower()

    # побережник: побере́жник (shorebird) vs побережни́к (riparian warden)
    pob = enrich_heteronyms.build_heteronyms_for_lemma("побережник")
    assert pob is not None and len(pob) == 2
    assert pob[0]["headword"] == "побере́жник"
    assert "bird" in pob[0]["gloss"].lower() or "sandpiper" in pob[0]["gloss"].lower()
    assert pob[1]["headword"] == "побережни́к"
    assert "warden" in pob[1]["gloss"].lower() or "guard" in pob[1]["gloss"].lower()

    # повищати: пови́щати (grow taller) vs повища́ти (squeal/screech for a while)
    pvsh = enrich_heteronyms.build_heteronyms_for_lemma("повищати")
    assert pvsh is not None and len(pvsh) == 2
    assert pvsh[0]["headword"] == "пови́щати"
    assert "taller" in pvsh[0]["gloss"].lower() or "height" in pvsh[0]["gloss"].lower()
    assert pvsh[1]["headword"] == "повища́ти"
    assert "squeal" in pvsh[1]["gloss"].lower() or "screech" in pvsh[1]["gloss"].lower()

    # пожалити: пожа́лити (take pity, dial.) vs пожали́ти (sting with nettles/bees)
    pzh = enrich_heteronyms.build_heteronyms_for_lemma("пожалити")
    assert pzh is not None and len(pzh) == 2
    assert pzh[0]["headword"] == "пожа́лити"
    assert "pity" in pzh[0]["gloss"].lower() or "mercy" in pzh[0]["gloss"].lower()
    assert pzh[1]["headword"] == "пожали́ти"
    assert "sting" in pzh[1]["gloss"].lower() or "nettles" in pzh[1]["gloss"].lower()

    # пожалитися: пожа́литися (feel compassion, dial.) vs пожали́тися (sting oneself)
    pzhs = enrich_heteronyms.build_heteronyms_for_lemma("пожалитися")
    assert pzhs is not None and len(pzhs) == 2
    assert pzhs[0]["headword"] == "пожа́литися"
    assert "pity" in pzhs[0]["gloss"].lower() or "compassion" in pzhs[0]["gloss"].lower()
    assert pzhs[1]["headword"] == "пожали́тися"
    assert "sting" in pzhs[1]["gloss"].lower()

    # пожарище: пожа́рище (huge fire) vs пожари́ще (fire site/ruins)
    pzhr = enrich_heteronyms.build_heteronyms_for_lemma("пожарище")
    assert pzhr is not None and len(pzhr) == 2
    assert pzhr[0]["headword"] == "пожа́рище"
    assert "fire" in pzhr[0]["gloss"].lower() or "blaze" in pzhr[0]["gloss"].lower()
    assert pzhr[1]["headword"] == "пожари́ще"
    assert "site" in pzhr[1]["gloss"].lower() or "ruins" in pzhr[1]["gloss"].lower()

    # позбігати: позбі́гати (run around everywhere) vs позбіга́ти (drain off / run off)
    pzb = enrich_heteronyms.build_heteronyms_for_lemma("позбігати")
    assert pzb is not None and len(pzb) == 2
    assert pzb[0]["headword"] == "позбі́гати"
    assert "run around" in pzb[0]["gloss"].lower()
    assert pzb[1]["headword"] == "позбіга́ти"
    assert "drain" in pzb[1]["gloss"].lower() or "run off" in pzb[1]["gloss"].lower()
    assert "gather" not in pzb[1]["gloss"].lower()

    # позорювати: позо́рювати (plough fields) vs позорюва́ти (spend night outdoors / dawn sleep)
    pzo = enrich_heteronyms.build_heteronyms_for_lemma("позорювати")
    assert pzo is not None and len(pzo) == 2
    assert pzo[0]["headword"] == "позо́рювати"
    assert "plough" in pzo[0]["gloss"].lower()
    assert pzo[1]["headword"] == "позорюва́ти"
    assert "outdoors" in pzo[1]["gloss"].lower() or "dawn" in pzo[1]["gloss"].lower() or "night" in pzo[1]["gloss"].lower()

    # покрапати: покра́пати (perf., drizzle for a while) vs покрапа́ти (imperf., drip intermittently)
    pkr = enrich_heteronyms.build_heteronyms_for_lemma("покрапати")
    assert pkr is not None and len(pkr) == 2
    assert pkr[0]["headword"] == "покра́пати"
    assert pkr[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert pkr[1]["headword"] == "покрапа́ти"
    assert pkr[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # полик: по́лик (sleeping bench) vs поли́к (shirt shoulder gusset)
    pol = enrich_heteronyms.build_heteronyms_for_lemma("полик")
    assert pol is not None and len(pol) == 2
    assert pol[0]["headword"] == "по́лик"
    assert "sleeping" in pol[0]["gloss"].lower() or "bench" in pol[0]["gloss"].lower() or "berth" in pol[0]["gloss"].lower()
    assert pol[1]["headword"] == "поли́к"
    assert "gusset" in pol[1]["gloss"].lower() or "insert" in pol[1]["gloss"].lower() or "shirt" in pol[1]["gloss"].lower()

    # половник: поло́вник (chaff bin/barn) vs половни́к (feudal sharecropper)
    plv = enrich_heteronyms.build_heteronyms_for_lemma("половник")
    assert plv is not None and len(plv) == 2
    assert plv[0]["headword"] == "поло́вник"
    assert "chaff" in plv[0]["gloss"].lower()
    assert plv[1]["headword"] == "половни́к"
    assert "feudal" in plv[1]["gloss"].lower() or "sharecropper" in plv[1]["gloss"].lower()

    # полупати: полу́пати (blink eyes) vs полупа́ти (chop/split firewood)
    plp = enrich_heteronyms.build_heteronyms_for_lemma("полупати")
    assert plp is not None and len(plp) == 2
    assert plp[0]["headword"] == "полу́пати"
    assert "blink" in plp[0]["gloss"].lower() or "eyes" in plp[0]["gloss"].lower()
    assert plp[1]["headword"] == "полупа́ти"
    assert "chop" in plp[1]["gloss"].lower() or "split" in plp[1]["gloss"].lower()

    # помикати: поми́кати (perf., comb flax) vs помика́ти (imperf., boss/push around)
    pmk = enrich_heteronyms.build_heteronyms_for_lemma("помикати")
    assert pmk is not None and len(pmk) == 2
    assert pmk[0]["headword"] == "поми́кати"
    assert pmk[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert pmk[1]["headword"] == "помика́ти"
    assert pmk[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"

    # попадатися: попа́датися (perf., wear out/fray) vs попада́тися (imperf., fall into trap / be caught)
    ppd = enrich_heteronyms.build_heteronyms_for_lemma("попадатися")
    assert ppd is not None and len(ppd) == 2
    assert ppd[0]["headword"] == "попа́датися"
    assert ppd[0]["morphology"]["paradigm"]["aspect"] == "доконаний"
    assert ppd[1]["headword"] == "попада́тися"
    assert ppd[1]["morphology"]["paradigm"]["aspect"] == "недоконаний"


def test_batch10_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 10's 32 lemmas are net-new and mutually disjoint with batches 1-9."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6
    from scripts.lexicon.curated_heteronyms_batch7 import CURATED_HETERONYMS_BATCH_7
    from scripts.lexicon.curated_heteronyms_batch8 import CURATED_HETERONYMS_BATCH_8
    from scripts.lexicon.curated_heteronyms_batch9 import CURATED_HETERONYMS_BATCH_9
    from scripts.lexicon.curated_heteronyms_batch10 import CURATED_HETERONYMS_BATCH_10

    assert len(CURATED_HETERONYMS_BATCH_10) == 32
    assert sum(len(v) for v in CURATED_HETERONYMS_BATCH_10.values()) == 64
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
        | set(CURATED_HETERONYMS_BATCH_6)
        | set(CURATED_HETERONYMS_BATCH_7)
        | set(CURATED_HETERONYMS_BATCH_8)
        | set(CURATED_HETERONYMS_BATCH_9)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_10) == set()
    for lemma in [
        "виїмковий", "люковий", "магістерський", "масничка", "нагніт",
        "накликатися", "наривний", "наслухатися", "натруска", "невигідність",
        "нівідки", "обрость", "перекочування", "переплавний", "переповзати",
        "перетіпати", "пікірування", "пікірувати", "пікіруватися", "побережник",
        "повищати", "пожалити", "пожалитися", "пожарище", "позбігати",
        "позорювати", "покрапати", "полик", "половник", "полупати",
        "помикати", "попадатися",
    ]:
        assert lemma in CURATED_HETERONYMS_BATCH_10

    # Check pre-Soviet witnesses
    polyk = CURATED_HETERONYMS_BATCH_10["полик"]
    assert "Грінченко" in polyk[0]["pre_soviet_witness"]["witness"]
    assert "Полик" in polyk[0]["pre_soviet_witness"]["quote"]

    popad = CURATED_HETERONYMS_BATCH_10["попадатися"]
    assert "Грінченко" in popad[0]["pre_soviet_witness"]["witness"]
    assert "Попадатися 1" in popad[0]["pre_soviet_witness"]["quote"]
    assert "Грінченко" in popad[1]["pre_soviet_witness"]["witness"]
    assert "Попадатися 2" in popad[1]["pre_soviet_witness"]["quote"]

    # Decolonization check: no normative СУМ-11 citations outside soviet_colonization_context
    for lemma, variants in CURATED_HETERONYMS_BATCH_10.items():
        for v in variants:
            assert "СУМ-11" not in v["meaning"]["source"], f"Found СУМ-11 in meaning.source for {lemma}"
            assert "СУМ-11" not in v["stress"]["source"], f"Found СУМ-11 in stress.source for {lemma}"


def test_batch11_semantic_and_stress_distinctions():
    """Verify Batch 11 stress and semantic distinctions against academic authorities and Grinchenko."""
    # 1. попереносити: поперено́сити (carry/transfer many items) vs попереноси́ти (carry many things over an extended period)
    pop = enrich_heteronyms.build_heteronyms_for_lemma("попереносити")
    assert pop is not None and len(pop) == 2
    assert pop[0]["headword"] == "поперено́сити"
    assert "carry" in pop[0]["gloss"].lower() or "transfer" in pop[0]["gloss"].lower()
    assert "туди й сюди" not in pop[0]["distinction_note"]
    assert "за довгий час" in pop[0]["distinction_note"]
    assert pop[1]["headword"] == "попереноси́ти"
    assert "extended period" in pop[1]["gloss"].lower() or "many things" in pop[1]["gloss"].lower() or "haul" in pop[1]["gloss"].lower()

    # 2. поправний: попра́вний (correctable/remediable) vs поправни́й (correctional/reformatory penal institution)
    popr = enrich_heteronyms.build_heteronyms_for_lemma("поправний")
    assert popr is not None and len(popr) == 2
    assert popr[0]["headword"] == "попра́вний"
    assert "correctable" in popr[0]["gloss"].lower() or "remediable" in popr[0]["gloss"].lower()
    assert "reformatory" not in popr[0]["gloss"].lower()
    assert "коефіцієнт" not in popr[0]["distinction_note"]
    assert "виправний заклад" in popr[0]["distinction_note"]
    assert popr[1]["headword"] == "поправни́й"
    assert "reformatory" in popr[1]["gloss"].lower() or "correctional" in popr[1]["gloss"].lower()
    assert "coefficient" not in popr[1]["gloss"].lower()
    assert "коефіцієнт" not in popr[1]["distinction_note"]

    # 3. скликання: скли́кання (convocation/cohort) vs склика́ння (convening/gathering)
    sklyk = enrich_heteronyms.build_heteronyms_for_lemma("скликання")
    assert sklyk is not None and len(sklyk) == 2
    assert sklyk[0]["headword"] == "скли́кання"
    assert "convocation" in sklyk[0]["gloss"].lower() or "session" in sklyk[0]["gloss"].lower() or "assembly" in sklyk[0]["gloss"].lower()
    assert sklyk[0]["soviet_colonization_context"]["sovietization_risk"] == 1
    assert "ленін" in sklyk[0]["soviet_colonization_context"]["keywords"]
    assert sklyk[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "скли́кання"
    assert sklyk[0]["morphology"]["paradigm"]["cases"]["родовий"]["plural"] == "скли́кань"
    assert sklyk[0]["morphology"]["paradigm"]["cases"]["орудний"]["singular"] == "скли́канням"
    assert sklyk[1]["headword"] == "склика́ння"
    assert "convening" in sklyk[1]["gloss"].lower() or "gathering" in sklyk[1]["gloss"].lower()
    assert sklyk[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "склика́ння"
    assert sklyk[1]["morphology"]["paradigm"]["cases"]["родовий"]["plural"] == "склика́нь"
    assert sklyk[1]["morphology"]["paradigm"]["cases"]["орудний"]["singular"] == "склика́нням"

    # 4. посвататися: посва́татися (propose marriage) vs посвата́тися (become in-laws)
    posv = enrich_heteronyms.build_heteronyms_for_lemma("посвататися")
    assert posv is not None and len(posv) == 2
    assert posv[0]["headword"] == "посва́татися"
    assert "propose" in posv[0]["gloss"].lower() or "matchmakers" in posv[0]["gloss"].lower()
    assert posv[1]["headword"] == "посвата́тися"
    assert "in-laws" in posv[1]["gloss"].lower()

    # 5. потикати: поти́кати (poke/jab repeatedly) vs потика́ти (poke one's nose somewhere)
    poty = enrich_heteronyms.build_heteronyms_for_lemma("потикати")
    assert poty is not None and len(poty) == 2
    assert poty[0]["headword"] == "поти́кати"
    assert "poke" in poty[0]["gloss"].lower() or "jab" in poty[0]["gloss"].lower()
    assert poty[1]["headword"] == "потика́ти"
    assert "nose" in poty[1]["gloss"].lower() or "show oneself" in poty[1]["gloss"].lower()

    # 6. потіпати: поті́пати (shake/twitch a while) vs потіпа́ти (scutch flax/thrash)
    poti = enrich_heteronyms.build_heteronyms_for_lemma("потіпати")
    assert poti is not None and len(poti) == 2
    assert poti[0]["headword"] == "поті́пати"
    assert "shake" in poti[0]["gloss"].lower() or "twitch" in poti[0]["gloss"].lower()
    assert poti[1]["headword"] == "потіпа́ти"
    assert "scutch" in poti[1]["gloss"].lower() or "thrash" in poti[1]["gloss"].lower()

    # 7. потріпати: потрі́пати (flap/flutter) vs потріпа́ти (fray/batter, Sovietization risk 1)
    potr = enrich_heteronyms.build_heteronyms_for_lemma("потріпати")
    assert potr is not None and len(potr) == 2
    assert potr[0]["headword"] == "потрі́пати"
    assert "flap" in potr[0]["gloss"].lower() or "flutter" in potr[0]["gloss"].lower()
    assert potr[1]["headword"] == "потріпа́ти"
    assert "fray" in potr[1]["gloss"].lower() or "batter" in potr[1]["gloss"].lower()
    assert potr[1]["soviet_colonization_context"]["sovietization_risk"] == 1
    assert "кпу" in potr[1]["soviet_colonization_context"]["keywords"]

    # 8. пречудний: пречу́дний (wondrous/gorgeous) vs пречудни́й (exceedingly strange/bizarre)
    prec = enrich_heteronyms.build_heteronyms_for_lemma("пречудний")
    assert prec is not None and len(prec) == 2
    assert prec[0]["headword"] == "пречу́дний"
    assert "wondrous" in prec[0]["gloss"].lower() or "beautiful" in prec[0]["gloss"].lower()
    assert prec[1]["headword"] == "пречудни́й"
    assert "strange" in prec[1]["gloss"].lower() or "bizarre" in prec[1]["gloss"].lower()

    # 9. припадковий: припа́дковий (seizures/paroxysmal) vs припадко́вий (accidental/incidental, dial.)
    prip = enrich_heteronyms.build_heteronyms_for_lemma("припадковий")
    assert prip is not None and len(prip) == 2
    assert prip[0]["headword"] == "припа́дковий"
    assert "fits" in prip[0]["gloss"].lower() or "seizures" in prip[0]["gloss"].lower() or "paroxysmal" in prip[0]["gloss"].lower()
    assert prip[1]["headword"] == "припадко́вий"
    assert "accidental" in prip[1]["gloss"].lower() or "incidental" in prip[1]["gloss"].lower()

    # 10. присікання: присі́кання (nagging/faultfinding) vs присіка́ння (pruning/truncation)
    pris = enrich_heteronyms.build_heteronyms_for_lemma("присікання")
    assert pris is not None and len(pris) == 2
    assert pris[0]["headword"] == "присі́кання"
    assert "faultfinding" in pris[0]["gloss"].lower() or "nagging" in pris[0]["gloss"].lower()
    assert pris[1]["headword"] == "присіка́ння"
    assert "pruning" in pris[1]["gloss"].lower() or "truncation" in pris[1]["gloss"].lower()

    # 11. провозитися: прово́зитися (passive, be transported) vs провози́тися (spend time fussing)
    prov = enrich_heteronyms.build_heteronyms_for_lemma("провозитися")
    assert prov is not None and len(prov) == 2
    assert prov[0]["headword"] == "прово́зитися"
    assert "transported" in prov[0]["gloss"].lower() or "carted" in prov[0]["gloss"].lower()
    assert prov[1]["headword"] == "провози́тися"
    assert "fussing" in prov[1]["gloss"].lower() or "tinkering" in prov[1]["gloss"].lower()

    # 12. продихати: проди́хати (stay alive/survive a while) vs продиха́ти (blow fresh breeze through)
    prod = enrich_heteronyms.build_heteronyms_for_lemma("продихати")
    assert prod is not None and len(prod) == 2
    assert prod[0]["headword"] == "проди́хати"
    assert "survive" in prod[0]["gloss"].lower() or "alive" in prod[0]["gloss"].lower()
    assert prod[1]["headword"] == "продиха́ти"
    assert "breeze" in prod[1]["gloss"].lower() or "breathe" in prod[1]["gloss"].lower()

    # 13. продублювати: проду́блювати (tan leather/harden skin) vs продублюва́ти (duplicate/dub film, Sovietization risk 1: Aurora)
    pdub = enrich_heteronyms.build_heteronyms_for_lemma("продублювати")
    assert pdub is not None and len(pdub) == 2
    assert pdub[0]["headword"] == "проду́блювати"
    assert "tan" in pdub[0]["gloss"].lower() or "leather" in pdub[0]["gloss"].lower()
    assert pdub[1]["headword"] == "продублюва́ти"
    assert "duplicate" in pdub[1]["gloss"].lower() or "dub" in pdub[1]["gloss"].lower()
    assert pdub[1]["soviet_colonization_context"]["sovietization_risk"] == 1
    assert "аврора" in pdub[1]["soviet_colonization_context"]["keywords"]

    # 14. прозірний: прозі́рний (transparent/limpid) vs прозірни́й (penetrable by sight/see-through)
    proz = enrich_heteronyms.build_heteronyms_for_lemma("прозірний")
    assert proz is not None and len(proz) == 2
    assert proz[0]["headword"] == "прозі́рний"
    assert "transparent" in proz[0]["gloss"].lower() or "clear" in proz[0]["gloss"].lower() or "limpid" in proz[0]["gloss"].lower()
    assert proz[1]["headword"] == "прозірни́й"
    assert "penetrable" in proz[1]["gloss"].lower() or "see-through" in proz[1]["gloss"].lower() or "sight" in proz[1]["gloss"].lower()

    # 15. проповзати: пропо́взати (perf., crawl a while) vs проповза́ти (imperf., creep through)
    prop = enrich_heteronyms.build_heteronyms_for_lemma("проповзати")
    assert prop is not None and len(prop) == 2
    assert prop[0]["headword"] == "пропо́взати"
    assert "crawl" in prop[0]["gloss"].lower() and "while" in prop[0]["gloss"].lower()
    assert prop[1]["headword"] == "проповза́ти"
    assert "through" in prop[1]["gloss"].lower() or "past" in prop[1]["gloss"].lower()

    # 16. прополювати: пропо́лювати (weed out crops) vs прополюва́ти (lose while hunting / hunt for a while)
    propol = enrich_heteronyms.build_heteronyms_for_lemma("прополювати")
    assert propol is not None and len(propol) == 2
    assert propol[0]["headword"] == "пропо́лювати"
    assert "weed" in propol[0]["gloss"].lower()
    assert propol[1]["headword"] == "прополюва́ти"
    assert "hunting" in propol[1]["gloss"].lower()

    # 17. розбірний: розбі́рний (legible/discerning) vs розбірни́й (demountable/collapsible)
    rozb = enrich_heteronyms.build_heteronyms_for_lemma("розбірний")
    assert rozb is not None and len(rozb) == 2
    assert rozb[0]["headword"] == "розбі́рний"
    assert "legible" in rozb[0]["gloss"].lower() or "clear" in rozb[0]["gloss"].lower()
    assert rozb[1]["headword"] == "розбірни́й"
    assert "demountable" in rozb[1]["gloss"].lower() or "collapsible" in rozb[1]["gloss"].lower()

    # 18. розвідниця: розві́дниця (reconnaissance scout) vs розвідни́ця (female saw-tooth setter)
    rozv = enrich_heteronyms.build_heteronyms_for_lemma("розвідниця")
    assert rozv is not None and len(rozv) == 2
    assert rozv[0]["headword"] == "розві́дниця"
    assert "scout" in rozv[0]["gloss"].lower() or "intelligence" in rozv[0]["gloss"].lower()
    assert rozv[1]["headword"] == "розвідни́ця"
    assert "saw" in rozv[1]["gloss"].lower() or "teeth" in rozv[1]["gloss"].lower() or "tooth" in rozv[1]["gloss"].lower() or "setter" in rozv[1]["gloss"].lower()

    # 19. розвозитися: розво́зитися (passive delivery) vs розвози́тися (dally fussing / dawdling)
    rozvo = enrich_heteronyms.build_heteronyms_for_lemma("розвозитися")
    assert rozvo is not None and len(rozvo) == 2
    assert rozvo[0]["headword"] == "розво́зитися"
    assert "delivered" in rozvo[0]["gloss"].lower() or "distributed" in rozvo[0]["gloss"].lower()
    assert rozvo[1]["headword"] == "розвози́тися"
    assert "fussing" in rozvo[1]["gloss"].lower() or "dawdle" in rozvo[1]["gloss"].lower()

    # 20. розкидання: розки́дання (perf. scattering) vs розкида́ння (imperf. broadcasting)
    rozk = enrich_heteronyms.build_heteronyms_for_lemma("розкидання")
    assert rozk is not None and len(rozk) == 2
    assert rozk[0]["headword"] == "розки́дання"
    assert "scattering" in rozk[0]["gloss"].lower() or "rapidly" in rozk[0]["gloss"].lower()
    assert rozk[1]["headword"] == "розкида́ння"
    assert "broadcasting" in rozk[1]["gloss"].lower() or "regularly" in rozk[1]["gloss"].lower()

    # 21. розпаювати: розпа́ювати (unsolder) vs розпаюва́ти (allot into shares)
    rozp = enrich_heteronyms.build_heteronyms_for_lemma("розпаювати")
    assert rozp is not None and len(rozp) == 2
    assert rozp[0]["headword"] == "розпа́ювати"
    assert "unsolder" in rozp[0]["gloss"].lower()
    assert rozp[1]["headword"] == "розпаюва́ти"
    assert "shares" in rozp[1]["gloss"].lower() or "allot" in rozp[1]["gloss"].lower()

    # 22. розповзатися: розпо́взатися (perf. start crawling) vs розповза́тися (imperf. scatter/unravel)
    rozpo = enrich_heteronyms.build_heteronyms_for_lemma("розповзатися")
    assert rozpo is not None and len(rozpo) == 2
    assert rozpo[0]["headword"] == "розпо́взатися"
    assert "crawling" in rozpo[0]["gloss"].lower() and "start" in rozpo[0]["gloss"].lower()
    assert rozpo[1]["headword"] == "розповза́тися"
    assert "directions" in rozpo[1]["gloss"].lower() or "seams" in rozpo[1]["gloss"].lower()

    # 23. розсадний: розса́дний (seedlings agri) vs розсадни́й (planting out)
    rozs = enrich_heteronyms.build_heteronyms_for_lemma("розсадний")
    assert rozs is not None and len(rozs) == 2
    assert rozs[0]["headword"] == "розса́дний"
    assert "seedlings" in rozs[0]["gloss"].lower() or "nursery" in rozs[0]["gloss"].lower()
    assert rozs[1]["headword"] == "розсадни́й"
    assert "planting out" in rozs[1]["gloss"].lower() or "transplanting" in rozs[1]["gloss"].lower()

    # 24. розсильний: розси́льний (messenger/courier) vs розсильни́й (dispatch/delivery record)
    rozsy = enrich_heteronyms.build_heteronyms_for_lemma("розсильний")
    assert rozsy is not None and len(rozsy) == 2
    assert rozsy[0]["headword"] == "розси́льний"
    assert "courier" in rozsy[0]["gloss"].lower() or "messenger" in rozsy[0]["gloss"].lower()
    assert rozsy[1]["headword"] == "розсильни́й"
    assert "dispatch" in rozsy[1]["gloss"].lower() or "delivery" in rozsy[1]["gloss"].lower()

    # 25. розсипка: ро́зсипка (spillage loss) vs розси́пка (scattering act)
    rozsp = enrich_heteronyms.build_heteronyms_for_lemma("розсипка")
    assert rozsp is not None and len(rozsp) == 2
    assert rozsp[0]["headword"] == "ро́зсипка"
    assert "loss" in rozsp[0]["gloss"].lower() or "spillage" in rozsp[0]["gloss"].lower()
    assert rozsp[1]["headword"] == "розси́пка"
    assert "scattering" in rozsp[1]["gloss"].lower() or "scattered" in rozsp[1]["gloss"].lower()

    # 26. романець: рома́нець (trashy pulp novel) vs романе́ць (wild chamomile/folk flower)
    rom = enrich_heteronyms.build_heteronyms_for_lemma("романець")
    assert rom is not None and len(rom) == 2
    assert rom[0]["headword"] == "рома́нець"
    assert "novel" in rom[0]["gloss"].lower() or "pulp" in rom[0]["gloss"].lower()
    assert rom[1]["headword"] == "романе́ць"
    assert "chamomile" in rom[1]["gloss"].lower() or "flower" in rom[1]["gloss"].lower()

    # 27. сажковий: са́жковий (smut fungal) vs сажко́вий (fattening coop/pen)
    sazh = enrich_heteronyms.build_heteronyms_for_lemma("сажковий")
    assert sazh is not None and len(sazh) == 2
    assert sazh[0]["headword"] == "са́жковий"
    assert "smut" in sazh[0]["gloss"].lower() or "fungal" in sazh[0]["gloss"].lower()
    assert sazh[1]["headword"] == "сажко́вий"
    assert "coop" in sazh[1]["gloss"].lower() or "pen" in sazh[1]["gloss"].lower()

    # 28. сапання: са́пання (heavy wheezing) vs сапа́ння (hoeing/weeding)
    sap = enrich_heteronyms.build_heteronyms_for_lemma("сапання")
    assert sap is not None and len(sap) == 2
    assert sap[0]["headword"] == "са́пання"
    assert "wheezing" in sap[0]["gloss"].lower() or "breathing" in sap[0]["gloss"].lower()
    assert sap[1]["headword"] == "сапа́ння"
    assert "hoeing" in sap[1]["gloss"].lower() or "weeding" in sap[1]["gloss"].lower()

    # 29. свататися: сва́татися (court/propose marriage) vs свата́тися (foster in-law relations)
    svat = enrich_heteronyms.build_heteronyms_for_lemma("свататися")
    assert svat is not None and len(svat) == 2
    assert svat[0]["headword"] == "сва́татися"
    assert "marriage" in svat[0]["gloss"].lower() or "court" in svat[0]["gloss"].lower()
    assert svat[1]["headword"] == "свата́тися"
    assert "in-law" in svat[1]["gloss"].lower()

    # 30. сипнути: си́пнути (grow hoarse/husky) vs сипну́ти (scatter/sprinkle once)
    syp = enrich_heteronyms.build_heteronyms_for_lemma("сипнути")
    assert syp is not None and len(syp) == 2
    assert syp[0]["headword"] == "си́пнути"
    assert "hoarse" in syp[0]["gloss"].lower() or "husky" in syp[0]["gloss"].lower()
    assert syp[1]["headword"] == "сипну́ти"
    assert "scatter" in syp[1]["gloss"].lower() or "sprinkle" in syp[1]["gloss"].lower()

    # 31. складування: скла́дування (compiling/folding rare) vs складува́ння (warehousing spec.)
    sklad = enrich_heteronyms.build_heteronyms_for_lemma("складування")
    assert sklad is not None and len(sklad) == 2
    assert sklad[0]["headword"] == "скла́дування"
    assert "compiling" in sklad[0]["gloss"].lower() or "folding" in sklad[0]["gloss"].lower()
    assert sklad[1]["headword"] == "складува́ння"
    assert "warehousing" in sklad[1]["gloss"].lower() or "storage" in sklad[1]["gloss"].lower()

    # 32. складувати: скла́дувати (compile/compose rare) vs складува́ти (warehouse/store spec.)
    sklv = enrich_heteronyms.build_heteronyms_for_lemma("складувати")
    assert sklv is not None and len(sklv) == 2
    assert sklv[0]["headword"] == "скла́дувати"
    assert "compile" in sklv[0]["gloss"].lower() or "fold" in sklv[0]["gloss"].lower()
    assert sklv[1]["headword"] == "складува́ти"
    assert "warehouse" in sklv[1]["gloss"].lower() or "store" in sklv[1]["gloss"].lower()


def test_batch11_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 11's 32 lemmas are net-new and mutually disjoint with batches 1-10."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6
    from scripts.lexicon.curated_heteronyms_batch7 import CURATED_HETERONYMS_BATCH_7
    from scripts.lexicon.curated_heteronyms_batch8 import CURATED_HETERONYMS_BATCH_8
    from scripts.lexicon.curated_heteronyms_batch9 import CURATED_HETERONYMS_BATCH_9
    from scripts.lexicon.curated_heteronyms_batch10 import CURATED_HETERONYMS_BATCH_10
    from scripts.lexicon.curated_heteronyms_batch11 import CURATED_HETERONYMS_BATCH_11

    assert len(CURATED_HETERONYMS_BATCH_11) == 32
    assert sum(len(v) for v in CURATED_HETERONYMS_BATCH_11.values()) == 64
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
        | set(CURATED_HETERONYMS_BATCH_6)
        | set(CURATED_HETERONYMS_BATCH_7)
        | set(CURATED_HETERONYMS_BATCH_8)
        | set(CURATED_HETERONYMS_BATCH_9)
        | set(CURATED_HETERONYMS_BATCH_10)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_11) == set()
    for lemma in [
        "попереносити", "поправний", "посвататися", "потикати",
        "потіпати", "потріпати", "пречудний", "припадковий", "присікання",
        "провозитися", "продихати", "продублювати", "прозірний", "проповзати",
        "прополювати", "розбірний", "розвідниця", "розвозитися", "розкидання",
        "розпаювати", "розповзатися", "розсадний", "розсильний", "розсипка",
        "романець", "сажковий", "сапання", "свататися", "сипнути",
        "складування", "складувати", "скликання",
    ]:
        assert lemma in CURATED_HETERONYMS_BATCH_11

    # Check pre-Soviet witnesses
    sklyk = CURATED_HETERONYMS_BATCH_11["скликання"]
    assert "Грінченко" in sklyk[0]["pre_soviet_witness"]["witness"]
    assert "Скликання" in sklyk[0]["pre_soviet_witness"]["quote"]

    potip = CURATED_HETERONYMS_BATCH_11["потіпати"]
    assert "Грінченко" in potip[1]["pre_soviet_witness"]["witness"]
    assert "Потіпати" in potip[1]["pre_soviet_witness"]["quote"]

    rozsp = CURATED_HETERONYMS_BATCH_11["розсипка"]
    assert "Грінченко" in rozsp[1]["pre_soviet_witness"]["witness"]
    assert "Розсипка" in rozsp[1]["pre_soviet_witness"]["quote"]

    rom = CURATED_HETERONYMS_BATCH_11["романець"]
    assert "Грінченко" in rom[1]["pre_soviet_witness"]["witness"]
    assert "Романець" in rom[1]["pre_soviet_witness"]["quote"]

    sap = CURATED_HETERONYMS_BATCH_11["сапання"]
    assert "Грінченко" in sap[1]["pre_soviet_witness"]["witness"]
    assert "Сапання" in sap[1]["pre_soviet_witness"]["quote"]

    svat = CURATED_HETERONYMS_BATCH_11["свататися"]
    assert "Грінченко" in svat[0]["pre_soviet_witness"]["witness"]
    assert "Свататися" in svat[0]["pre_soviet_witness"]["quote"]

    syp = CURATED_HETERONYMS_BATCH_11["сипнути"]
    assert "Грінченко" in syp[1]["pre_soviet_witness"]["witness"]
    assert "Сипнути" in syp[1]["pre_soviet_witness"]["quote"]

    # Decolonization check: no normative СУМ-11 citations outside soviet_colonization_context
    for lemma, variants in CURATED_HETERONYMS_BATCH_11.items():
        for v in variants:
            assert "СУМ-11" not in v["meaning"]["source"], f"Found СУМ-11 in meaning.source for {lemma}"
            assert "СУМ-11" not in v["stress"]["source"], f"Found СУМ-11 in stress.source for {lemma}"


def test_batch12_semantic_and_stress_distinctions():
    """Verify Batch 12 stress and semantic distinctions against academic authorities and Grinchenko."""
    # 1. бовтнути: бо́втну́ти vs бо́втнути
    var_бовтнути = enrich_heteronyms.build_heteronyms_for_lemma("бовтнути")
    assert var_бовтнути is not None and len(var_бовтнути) == 2
    assert var_бовтнути[0]["headword"] == "бо́втну́ти"
    assert var_бовтнути[1]["headword"] == "бо́втнути"
    assert var_бовтнути[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_бовтнути[0]["pre_soviet_witness"]["witness"]

    # 2. гуконути: гуко́ну́ти vs гукону́ти
    var_гуконути = enrich_heteronyms.build_heteronyms_for_lemma("гуконути")
    assert var_гуконути is not None and len(var_гуконути) == 2
    assert var_гуконути[0]["headword"] == "гуко́ну́ти"
    assert var_гуконути[1]["headword"] == "гукону́ти"
    assert var_гуконути[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_гуконути[0]["pre_soviet_witness"]["witness"]

    # 3. натяжка: на́тя́жка vs натя́жка
    var_натяжка = enrich_heteronyms.build_heteronyms_for_lemma("натяжка")
    assert var_натяжка is not None and len(var_натяжка) == 2
    assert var_натяжка[0]["headword"] == "на́тя́жка"
    assert var_натяжка[1]["headword"] == "натя́жка"
    assert var_натяжка[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "на́тя́жка"
    assert var_натяжка[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "на́тя́жки"
    assert var_натяжка[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "натя́жка"
    assert var_натяжка[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "натя́жки"

    # 4. недіючий: неді́ючий vs недію́чий
    var_недіючий = enrich_heteronyms.build_heteronyms_for_lemma("недіючий")
    assert var_недіючий is not None and len(var_недіючий) == 2
    assert var_недіючий[0]["headword"] == "неді́ючий"
    assert var_недіючий[1]["headword"] == "недію́чий"

    # 5. обладувати: обла́дувати vs обла́дува́ти
    var_обладувати = enrich_heteronyms.build_heteronyms_for_lemma("обладувати")
    assert var_обладувати is not None and len(var_обладувати) == 2
    assert var_обладувати[0]["headword"] == "обла́дувати"
    assert var_обладувати[1]["headword"] == "обла́дува́ти"
    assert var_обладувати[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_обладувати[0]["pre_soviet_witness"]["witness"]
    assert var_обладувати[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_обладувати[1]["pre_soviet_witness"]["witness"]

    # 6. поливка: по́ли́вка vs поли́вка
    var_поливка = enrich_heteronyms.build_heteronyms_for_lemma("поливка")
    assert var_поливка is not None and len(var_поливка) == 2
    assert var_поливка[0]["headword"] == "по́ли́вка"
    assert var_поливка[1]["headword"] == "поли́вка"
    assert var_поливка[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_поливка[1]["pre_soviet_witness"]["witness"]
    assert var_поливка[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "по́ливка"
    assert var_поливка[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "по́ливки"
    assert var_поливка[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "поли́вка"
    assert var_поливка[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "поли́вки"

    # 7. помісний: по́місни́й vs помі́сний
    var_помісний = enrich_heteronyms.build_heteronyms_for_lemma("помісний")
    assert var_помісний is not None and len(var_помісний) == 2
    assert var_помісний[0]["headword"] == "по́місни́й"
    assert var_помісний[1]["headword"] == "помі́сний"

    # 8. поставляти: поста́вляти vs поставля́ти
    var_поставляти = enrich_heteronyms.build_heteronyms_for_lemma("поставляти")
    assert var_поставляти is not None and len(var_поставляти) == 2
    assert var_поставляти[0]["headword"] == "поста́вляти"
    assert var_поставляти[1]["headword"] == "поставля́ти"
    assert var_поставляти[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_поставляти[0]["pre_soviet_witness"]["witness"]
    assert var_поставляти[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_поставляти[1]["pre_soviet_witness"]["witness"]

    # 9. складуватися: скла́дуватися vs складува́тися
    var_складуватися = enrich_heteronyms.build_heteronyms_for_lemma("складуватися")
    assert var_складуватися is not None and len(var_складуватися) == 2
    assert var_складуватися[0]["headword"] == "скла́дуватися"
    assert var_складуватися[1]["headword"] == "складува́тися"

    # 10. склепувати: скле́пувати vs склепува́ти
    var_склепувати = enrich_heteronyms.build_heteronyms_for_lemma("склепувати")
    assert var_склепувати is not None and len(var_склепувати) == 2
    assert var_склепувати[0]["headword"] == "скле́пувати"
    assert var_склепувати[1]["headword"] == "склепува́ти"
    assert var_склепувати[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_склепувати[0]["pre_soviet_witness"]["witness"]

    # 11. совковий: со́вковий vs совко́вий
    var_совковий = enrich_heteronyms.build_heteronyms_for_lemma("совковий")
    assert var_совковий is not None and len(var_совковий) == 2
    assert var_совковий[0]["headword"] == "со́вковий"
    assert var_совковий[1]["headword"] == "совко́вий"

    # 12. сопуха: со́пу́ха vs сопу́ха
    var_сопуха = enrich_heteronyms.build_heteronyms_for_lemma("сопуха")
    assert var_сопуха is not None and len(var_сопуха) == 2
    assert var_сопуха[0]["headword"] == "со́пу́ха"
    assert var_сопуха[1]["headword"] == "сопу́ха"
    assert var_сопуха[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_сопуха[0]["pre_soviet_witness"]["witness"]
    assert var_сопуха[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "со́пуха"
    assert var_сопуха[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "со́пухи"
    assert var_сопуха[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "сопу́ха"
    assert var_сопуха[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "сопу́хи"

    # 13. сосковий: со́сковий vs соско́вий
    var_сосковий = enrich_heteronyms.build_heteronyms_for_lemma("сосковий")
    assert var_сосковий is not None and len(var_сосковий) == 2
    assert var_сосковий[0]["headword"] == "со́сковий"
    assert var_сосковий[1]["headword"] == "соско́вий"

    # 14. співанка: спі́ванка vs спі́ва́нка
    var_співанка = enrich_heteronyms.build_heteronyms_for_lemma("співанка")
    assert var_співанка is not None and len(var_співанка) == 2
    assert var_співанка[0]["headword"] == "спі́ванка"
    assert var_співанка[1]["headword"] == "спі́ва́нка"
    assert var_співанка[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_співанка[0]["pre_soviet_witness"]["witness"]
    assert var_співанка[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "спі́ванка"
    assert var_співанка[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "спі́ванки"
    assert var_співанка[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "співа́нка"
    assert var_співанка[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "співа́нки"

    # 15. споритися: спо́ритися vs спори́тися
    var_споритися = enrich_heteronyms.build_heteronyms_for_lemma("споритися")
    assert var_споритися is not None and len(var_споритися) == 2
    assert var_споритися[0]["headword"] == "спо́ритися"
    assert var_споритися[1]["headword"] == "спори́тися"
    assert var_споритися[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_споритися[0]["pre_soviet_witness"]["witness"]
    assert var_споритися[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_споритися[1]["pre_soviet_witness"]["witness"]

    # 16. справниця: спра́вниця vs справни́ця
    var_справниця = enrich_heteronyms.build_heteronyms_for_lemma("справниця")
    assert var_справниця is not None and len(var_справниця) == 2
    assert var_справниця[0]["headword"] == "спра́вниця"
    assert var_справниця[1]["headword"] == "справни́ця"
    assert var_справниця[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_справниця[1]["pre_soviet_witness"]["witness"]
    assert var_справниця[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "спра́вниця"
    assert var_справниця[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "спра́вниці"
    assert var_справниця[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "справни́ця"
    assert var_справниця[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "справни́ці"

    # 17. становий: ста́новий vs ста́нови́й
    var_становий = enrich_heteronyms.build_heteronyms_for_lemma("становий")
    assert var_становий is not None and len(var_становий) == 2
    assert var_становий[0]["headword"] == "ста́новий"
    assert var_становий[1]["headword"] == "ста́нови́й"
    assert var_становий[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_становий[1]["pre_soviet_witness"]["witness"]

    # 18. степний: сте́пний vs степни́й
    var_степний = enrich_heteronyms.build_heteronyms_for_lemma("степний")
    assert var_степний is not None and len(var_степний) == 2
    assert var_степний[0]["headword"] == "сте́пний"
    assert var_степний[1]["headword"] == "степни́й"
    assert var_степний[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_степний[0]["pre_soviet_witness"]["witness"]

    # 19. стовпище: сто́впище vs стовпи́ще
    var_стовпище = enrich_heteronyms.build_heteronyms_for_lemma("стовпище")
    assert var_стовпище is not None and len(var_стовпище) == 2
    assert var_стовпище[0]["headword"] == "сто́впище"
    assert var_стовпище[1]["headword"] == "стовпи́ще"
    assert var_стовпище[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_стовпище[0]["pre_soviet_witness"]["witness"]
    assert var_стовпище[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "сто́впище"
    assert var_стовпище[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "сто́впища"
    assert var_стовпище[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "стовпи́ще"
    assert var_стовпище[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "стовпи́ща"

    # 20. стожище: сто́жище vs стожи́ще
    var_стожище = enrich_heteronyms.build_heteronyms_for_lemma("стожище")
    assert var_стожище is not None and len(var_стожище) == 2
    assert var_стожище[0]["headword"] == "сто́жище"
    assert var_стожище[1]["headword"] == "стожи́ще"
    assert var_стожище[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "сто́жище"
    assert var_стожище[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "сто́жища"
    assert var_стожище[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "стожи́ще"
    assert var_стожище[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "стожи́ща"

    # 21. струхнути: стру́хнути vs струхну́ти
    var_струхнути = enrich_heteronyms.build_heteronyms_for_lemma("струхнути")
    assert var_струхнути is not None and len(var_струхнути) == 2
    assert var_струхнути[0]["headword"] == "стру́хнути"
    assert var_струхнути[1]["headword"] == "струхну́ти"
    assert var_струхнути[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_струхнути[0]["pre_soviet_witness"]["witness"]
    assert var_струхнути[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_струхнути[1]["pre_soviet_witness"]["witness"]

    # 22. сунутися: су́нутися vs суну́тися
    var_сунутися = enrich_heteronyms.build_heteronyms_for_lemma("сунутися")
    assert var_сунутися is not None and len(var_сунутися) == 2
    assert var_сунутися[0]["headword"] == "су́нутися"
    assert var_сунутися[1]["headword"] == "суну́тися"
    assert var_сунутися[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_сунутися[0]["pre_soviet_witness"]["witness"]
    assert var_сунутися[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_сунутися[1]["pre_soviet_witness"]["witness"]

    # 23. сушений: су́шений vs суше́ний
    var_сушений = enrich_heteronyms.build_heteronyms_for_lemma("сушений")
    assert var_сушений is not None and len(var_сушений) == 2
    assert var_сушений[0]["headword"] == "су́шений"
    assert var_сушений[1]["headword"] == "суше́ний"

    # 24. схрипнути: схри́пнути vs схрипну́ти
    var_схрипнути = enrich_heteronyms.build_heteronyms_for_lemma("схрипнути")
    assert var_схрипнути is not None and len(var_схрипнути) == 2
    assert var_схрипнути[0]["headword"] == "схри́пнути"
    assert var_схрипнути[1]["headword"] == "схрипну́ти"

    # 25. тамбур: та́мбур vs тамбу́р
    var_тамбур = enrich_heteronyms.build_heteronyms_for_lemma("тамбур")
    assert var_тамбур is not None and len(var_тамбур) == 2
    assert var_тамбур[0]["headword"] == "та́мбур"
    assert var_тамбур[1]["headword"] == "тамбу́р"
    assert var_тамбур[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_тамбур[1]["pre_soviet_witness"]["witness"]
    assert var_тамбур[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "та́мбур"
    assert var_тамбур[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "та́мбура"
    assert var_тамбур[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "тамбу́р"
    assert var_тамбур[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "тамбу́ра"

    # 26. танковий: та́нковий vs та́нко́вий
    var_танковий = enrich_heteronyms.build_heteronyms_for_lemma("танковий")
    assert var_танковий is not None and len(var_танковий) == 2
    assert var_танковий[0]["headword"] == "та́нковий"
    assert var_танковий[1]["headword"] == "та́нко́вий"

    # 27. темник: те́мник vs темни́к
    var_темник = enrich_heteronyms.build_heteronyms_for_lemma("темник")
    assert var_темник is not None and len(var_темник) == 2
    assert var_темник[0]["headword"] == "те́мник"
    assert var_темник[1]["headword"] == "темни́к"
    assert var_темник[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_темник[1]["pre_soviet_witness"]["witness"]
    assert var_темник[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "те́мник"
    assert var_темник[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "те́мника"
    assert var_темник[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "темни́к"
    assert var_темник[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "темника́"

    # 28. товчений: то́вчений vs товче́ний
    var_товчений = enrich_heteronyms.build_heteronyms_for_lemma("товчений")
    assert var_товчений is not None and len(var_товчений) == 2
    assert var_товчений[0]["headword"] == "то́вчений"
    assert var_товчений[1]["headword"] == "товче́ний"

    # 29. тікання: ті́кання vs тіка́ння
    var_тікання = enrich_heteronyms.build_heteronyms_for_lemma("тікання")
    assert var_тікання is not None and len(var_тікання) == 2
    assert var_тікання[0]["headword"] == "ті́кання"
    assert var_тікання[1]["headword"] == "тіка́ння"
    assert var_тікання[1]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_тікання[1]["pre_soviet_witness"]["witness"]
    assert var_тікання[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "ті́кання"
    assert var_тікання[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "ті́кання"
    assert var_тікання[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "тіка́ння"
    assert var_тікання[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "тіка́ння"

    # 30. тіпання: ті́пання vs тіпа́ння
    var_тіпання = enrich_heteronyms.build_heteronyms_for_lemma("тіпання")
    assert var_тіпання is not None and len(var_тіпання) == 2
    assert var_тіпання[0]["headword"] == "ті́пання"
    assert var_тіпання[1]["headword"] == "тіпа́ння"
    assert var_тіпання[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_тіпання[0]["pre_soviet_witness"]["witness"]
    assert var_тіпання[0]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "ті́пання"
    assert var_тіпання[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "ті́пання"
    assert var_тіпання[1]["morphology"]["paradigm"]["cases"]["називний"]["singular"] == "тіпа́ння"
    assert var_тіпання[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "тіпа́ння"

    # 31. тіпати: ті́пати vs тіпа́ти
    var_тіпати = enrich_heteronyms.build_heteronyms_for_lemma("тіпати")
    assert var_тіпати is not None and len(var_тіпати) == 2
    assert var_тіпати[0]["headword"] == "ті́пати"
    assert var_тіпати[1]["headword"] == "тіпа́ти"
    assert var_тіпати[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_тіпати[0]["pre_soviet_witness"]["witness"]

    # 32. тіпатися: ті́патися vs тіпа́тися
    var_тіпатися = enrich_heteronyms.build_heteronyms_for_lemma("тіпатися")
    assert var_тіпатися is not None and len(var_тіпатися) == 2
    assert var_тіпатися[0]["headword"] == "ті́патися"
    assert var_тіпатися[1]["headword"] == "тіпа́тися"
    assert var_тіпатися[0]["pre_soviet_witness"] is not None
    assert "Грінченко" in var_тіпатися[0]["pre_soviet_witness"]["witness"]

def test_batch12_lemmas_not_duplicated_from_earlier_batches():
    """Ensure Batch 12 lemmas do not collide with earlier batches or core set."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6
    from scripts.lexicon.curated_heteronyms_batch7 import CURATED_HETERONYMS_BATCH_7
    from scripts.lexicon.curated_heteronyms_batch8 import CURATED_HETERONYMS_BATCH_8
    from scripts.lexicon.curated_heteronyms_batch9 import CURATED_HETERONYMS_BATCH_9
    from scripts.lexicon.curated_heteronyms_batch10 import CURATED_HETERONYMS_BATCH_10
    from scripts.lexicon.curated_heteronyms_batch11 import CURATED_HETERONYMS_BATCH_11
    from scripts.lexicon.curated_heteronyms_batch12 import CURATED_HETERONYMS_BATCH_12

    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
        | set(CURATED_HETERONYMS_BATCH_6)
        | set(CURATED_HETERONYMS_BATCH_7)
        | set(CURATED_HETERONYMS_BATCH_8)
        | set(CURATED_HETERONYMS_BATCH_9)
        | set(CURATED_HETERONYMS_BATCH_10)
        | set(CURATED_HETERONYMS_BATCH_11)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_12) == set()
    assert len(CURATED_HETERONYMS_BATCH_12) == 32
    # Decolonization check: no normative СУМ-11 citations outside soviet_colonization_context
    for lemma, variants in CURATED_HETERONYMS_BATCH_12.items():
        for v in variants:
            assert "СУМ-11" not in v["meaning"]["source"], f"Found СУМ-11 in meaning.source for {lemma}"
            assert "СУМ-11" not in v["stress"]["source"], f"Found СУМ-11 in stress.source for {lemma}"


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
