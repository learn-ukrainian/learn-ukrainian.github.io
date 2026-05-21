import json
from pathlib import Path

import pytest

from scripts.ingest.esum_ingest import parse_esum, write_jsonl


def test_esum_ingest_djvutxt_regression():
    # Load vol1 djvu raw text
    repo = Path(__file__).resolve().parents[2]
    vol1_txt = repo / "data" / "raw" / "esum" / "vol1.txt"
    if not vol1_txt.exists():
        pytest.skip("Vol 1 djvutxt file not available locally")

    text = vol1_txt.read_text(encoding="utf-8")
    entries = parse_esum(text, vol=1, source_format="djvutxt")

    # Regression assertion: vol1 djvutxt parses to >= 5000 entries (current is 5146)
    assert len(entries) >= 5000


def test_esum_ingest_textpdf_parsing(tmp_path: Path):
    fixture_text = """
25

надрагуля

надія

509; ЗСЬМ 7, 196; Вгйскпег 107; Маспек ЕЗ)С 113; 5Ккок І 414--415. -Див. ще діти?, на!.

надія, надійний, надіятися,
вітися|

«надіятися»,

надійсь

|наді-

«мабуть,

певно», надісь «тс.», Їзненадійки|
нацька»

Ж,

обезнадіяти,

«зне-

обнадіяти;

-- р. надбяться, бр. надзея, др. надіьятися, п. падлеіа, ч. паде|е, слц. падеі,
вл. пада,

паф2ес

зе, болг. надбя

50, нл.

па?е|а, па?еб

се, м. |надея| «надія»,
схв. надати се, слн. пддеіаїі 5е; -- пел.
паде|а,

падеб

(пайбіаї)

ти», утвореного

похідне

від

основи

«накладати,

за допомогою

інфінітива

поклада-

префікса

па- від дієслова дбїї «Класти». -- Преобр. 1 590; Булаховський Вибр. пр. ШІ
394; ЗСЬМ 7, 196; Вгйскпег 353; Маспек ЕЗО)С 387; ЗеПпизівг-5емс 981-982; Веліа| Е55) П 211; ЗССЯ 21, 235.

--

Див.

ще

діти?,

на!"

--

Пор.

на-

діжка, сподівати.

Надія (жіноче ім'я), Надя, |Надежда| Ж; -- бр. Надзбя; -- калька р.
Надежда, запозиченого, як і болг. Надежда,
з церковнослов'янської
мови;

цел. Мадежда є калькою гр. "Еатіс, -ідос,
власного жіночого імені, утвореного на
основі іменника єЛтіс «надія». -- Пет-

ровский 162; Илчев 352.
надоба,

надббно,

див. надібок.
"""
    entries = parse_esum(fixture_text, vol=4, source_format="text-pdf")

    assert len(entries) >= 2, f"Found only {len(entries)} entries"

    # Check the first entry extracted (надія)
    lemmas = [e["lemma"] for e in entries]
    assert "надія" in lemmas
    assert "надія (жіноче ім'я)" in lemmas or "надія" in lemmas
    assert "надоба" in lemmas

    # Check etymology text
    nadia_texts = [e["etymology_text"] for e in entries if e["lemma"] == "надія"]
    assert any("надія, надійний, надіятися" in t for t in nadia_texts)
    assert any("па- від дієслова дбїї «Класти»" in t for t in nadia_texts)

    output_path = tmp_path / "test.jsonl"
    count = write_jsonl(entries, output_path)
    assert count == len(entries)

    # verify jsonl schema
    lines = output_path.read_text("utf-8").splitlines()
    assert len(lines) == len(entries)
    data = json.loads(lines[0])
    assert "lemma" in data
    assert "vol" in data
    assert "page" in data
    assert "etymology_text" in data
    assert "cognates" in data


def test_textpdf_strong_entry_start_splits_after_continuation():
    fixture_text = """
тагуп(е) і далі фр. ст. тагіп походить від лат.
тагіпи5
піаге
«море»,
спорідненого

субота, ісобітна «вогнище на Ку-

пала» Куз, О, субітка «(заст.) суботні
вечорниці», субдтник; -- р. суббдта,
бр. субдта, др. субота, собота; -- слово
походить від гр. саВфатом «тс.». -- Див. ще суб-.
"""

    entries = parse_esum(fixture_text, vol=5, source_format="text-pdf")
    lemmas = [entry["lemma"] for entry in entries]

    assert "субота" in lemmas
    subota = next(entry for entry in entries if entry["lemma"] == "субота")
    assert subota["etymology_text"].startswith("субота, ісобітна")
    assert "Купала" in subota["etymology_text"]


def test_textpdf_strong_entry_start_handles_hyphenated_prefix_headword():
    fixture_text = """
попереднього

а-, ан- (префіксальний елемент заперечної семантики
в складі запозичених слів); -- гр. а-, ан- «не».
"""

    entries = parse_esum(fixture_text, vol=1, source_format="text-pdf")

    assert [entry["lemma"] for entry in entries] == ["а-"]


def test_textpdf_rejects_source_abbreviation_headwords():
    fixture_text = """
Мак; вороняче око звичайне, Рагіз диадгіїоПа 1.; ластовень лікарський.

ЕМ 283; Вайса ВВЕ П 543--546; Тгацітапп 240.

рука, рукав, рукавець «рукавчик; торбина»;
-- р. рука, бр. рука; -- псл. рука.
"""

    entries = parse_esum(fixture_text, vol=5, source_format="text-pdf")
    lemmas = [entry["lemma"] for entry in entries]

    assert "мак" not in lemmas
    assert "ем" not in lemmas
    assert "рука" in lemmas


def test_textpdf_corrects_common_ocr_damaged_headword():
    fixture_text = """
сднце, Їсдненько| (зменш.), сбнечко «тс»,
сонцевік «астрофізик, який займається дослідженням сонця»;
-- р. солнце, бр. сонца; -- псл. сльньце.
"""

    entries = parse_esum(fixture_text, vol=5, source_format="text-pdf")

    assert [entry["lemma"] for entry in entries] == ["сонце"]
