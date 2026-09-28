"""ULIF synonym-group parsing and the core-pair rule (#8714).

Rows below are excerpts of real checked ULIF synonym groups from
``sources.db`` (``<a>`` links removed, some members elided).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.practice.ulif_synonym_groups import (
    UlifSynonymGroup,
    UlifSynonymGroups,
    group_from_payload,
    parse_group_members,
    payload_from_row_html,
    plain,
)

SPYSOK = (
    "<p><b>СПИ́СОК</b> (опис з перерахуванням яких-небудь осіб або предметів), <b>РЕЄСТР</b>, "
    "<b>ПЕРЕ́ЛІК</b>, <b>ПРЕЙСКУРА́НТ</b>, <b>ІНДЕКС</b>, <b>РЕГІ́СТР</b> <i>спец.; </i> <b>КАТАЛО́Г</b> "
    "(перелік книжок, рукописів, картин тощо, складений у певному порядку); <b>ІНВЕНТА́Р</b> <i>заст. </i> "
    "(список майна, звичайно рухомого). <i>Він шукав своє прізвище в списку</i> (fixture).</p>"
)
KOPATY = (
    "<p><b>КОПА́ТИ</b> (лопатою, заступом тощо робити заглиблення в землі, снігу і т. ін.; видобувати щось із "
    "землі, снігу тощо), <b>РИ́ТИ</b>, <b>ВИКО́ПУВАТИ</b>, <b>ВИРИВА́ТИ</b>, <b>ВИБИРА́ТИ</b> (видобувати із "
    "землі вирощену картоплю); <b>КОПА́ТИСЯ</b> (робити заглиблення в землі); <b>ШТИКУВА́ТИ</b> <i>спец.</i> "
    "(розпушуючи й перекидаючи шари землі).  - Док.: <b>ви́копати</b>, <b>ви́рити</b>, <b>ви́брати</b>. "
    "<i>Копати город</i> (fixture).</p>"
)
ZANEPAD = (
    "<p><b>ЗАНЕ́ПАД</b> (погіршення загального стану, зниження рівня розвитку), <b>РЕГРЕ́С</b>, "
    "<b>ДЕГРАДА́ЦІЯ</b>, <b>ДЕПРЕ́СІЯ</b>, <b>ЗАНЕПА́ДОК</b> <i>заст.; </i> <b>ПІДУПА́Д</b> <i>рідше</i> "
    "(у дещо меншій мірі); <b>ДЕКАДА́НС</b> <i>книжн.</i> (у мистецтві, літературі і т. п.); <b>РО́ЗКЛАД</b> "
    "(у суспільстві, моралі тощо).</p>"
)
OBLYCHCHIA = (
    "<p><b>ОБЛИ́ЧЧЯ</b> (передня частина голови людини), <b>ЛИЦЕ́</b>, <b>ВИД</b>, <b>О́БРАЗ</b> <i>розм., </i> "
    "<b>ЛИК</b> <i>поет., заст., </i> <b>ТВАР</b> <i>ч. і ж., заст., вульг.</i> <i>- Їсти хочеш, і сім'я теж. "
    "Я нагодую!</i> (В. Барка);</p>"
)
ZALYSHATY = (
    "<p><b>ЗАЛИША́ТИ</b> (вирушаючи звідкись або кудись, не брати з собою кого-, що-небудь), <b>ЛИША́ТИ</b>, "
    "<b>ПОКИДА́ТИ</b>, <b>ОСТАВЛЯ́ТИ</b> <b>[ЗОСТАВЛЯ́ТИ]</b> <i>рідко,</i> <b>ВІДБІГА́ТИ</b> <i>кого, заст.</i> "
    "- Док.: <b>залиши́ти</b>, <b>лиши́ти</b>, <b>поки́нути</b>, <b>оста́вити</b> <b>[зоста́вити]</b>, "
    "<b>відбі́гти</b>. <i>Він згадав, що в майстерні залишив косу</i> (М. Стельмах);</p>"
)


def _groups(*rows: str) -> UlifSynonymGroups:
    return UlifSynonymGroups.from_payloads(payload_from_row_html(row) for row in rows)


@pytest.mark.parametrize(
    "change",
    [
        lambda group: replace(group, group_id="changed"),
        lambda group: replace(group, terms=(*group.terms, "new-member")),
        lambda group: replace(group, members=(replace(group.members[0], lemma="changed"), *group.members[1:])),
        lambda group: replace(group, members=(group.members[0], replace(group.members[1], cluster=1), *group.members[2:])),
        lambda group: replace(group, members=(group.members[0], replace(group.members[1], labels=("розм.",)), *group.members[2:])),
        lambda group: replace(group, members=(group.members[0], replace(group.members[1], note="changed"), *group.members[2:])),
        lambda group: replace(group, members=(group.members[0], replace(group.members[1], perfective=True), *group.members[2:])),
        lambda group: replace(group, members=(group.members[1], group.members[0], *group.members[2:])),
    ],
)
def test_fingerprint_changes_with_membership_or_pair_eligibility(
    change: Callable[[UlifSynonymGroup], UlifSynonymGroup],
) -> None:
    group = group_from_payload(payload_from_row_html(SPYSOK))
    assert group is not None
    changed = change(group)
    assert UlifSynonymGroups([group]).fingerprint() != UlifSynonymGroups([changed]).fingerprint()


def test_plain_strips_stress_brackets_and_hyphen_spacing() -> None:
    assert plain("ВИ́ГЛЯД") == "вигляд"
    assert plain("[ УЗІ́Р ]") == "узір"
    assert plain("БУ́ДЬ - ДЕ") == "будь-де"
    assert plain("П’ЯТЬ") == "п'ять"


def test_row_structure_clusters_labels_notes_and_perfective_row() -> None:
    members = {member.lemma: member for member in parse_group_members(KOPATY)}
    assert members["копати"].note is not None and members["копати"].cluster == 0
    assert members["рити"].note is None and members["рити"].cluster == 0
    assert members["вибирати"].note == "видобувати із землі вирощену картоплю"
    assert members["копатися"].cluster == 1
    assert members["штикувати"].register_labels == ("спец.",)
    assert members["викопати"].perfective and not members["рити"].perfective


def test_label_italic_holding_the_cluster_separator_closes_the_cluster() -> None:
    members = {member.lemma: member for member in parse_group_members(ZANEPAD)}
    assert members["депресія"].cluster == 0
    assert members["занепадок"].register_labels == ("заст.",)
    assert members["підупад"].cluster == 1
    assert members["розклад"].cluster == 3


def test_bracketed_variant_shares_labels_and_government_is_not_a_register() -> None:
    members = {member.lemma: member for member in parse_group_members(ZALYSHATY)}
    assert members["оставляти"].register_labels == ("рідко",)
    assert members["зоставляти"].register_labels == ("рідко",)
    assert members["відбігати"].register_labels == ("кого, заст.",)
    assert members["лишати"].register_labels == ()


def test_example_citations_are_not_members_or_labels() -> None:
    members = {member.lemma: member for member in parse_group_members(OBLYCHCHIA)}
    assert set(members) == {"обличчя", "лице", "вид", "образ", "лик", "твар"}
    assert members["твар"].register_labels == ("ч. і ж., заст., вульг.",)


def test_core_pair_is_dominant_plus_unmarked_member_of_its_cluster() -> None:
    groups = _groups(SPYSOK, KOPATY, ZANEPAD)
    evidence = groups.core_pair("перелік", "список")
    assert evidence is not None
    assert evidence.dominant == "список"
    assert evidence.sense == "опис з перерахуванням яких-небудь осіб або предметів"
    assert groups.core_pair("копати", "рити") is not None
    # Neither word is the dominant.
    assert groups.core_pair("реєстр", "перелік") is None
    # Register label, later cluster, own note, perfective row.
    assert groups.core_pair("список", "регістр") is None
    assert groups.core_pair("список", "каталог") is None
    assert groups.core_pair("копати", "вибирати") is None
    assert groups.core_pair("копати", "викопати") is None
    # депресія → розклад (#8714): same group, different clusters.
    assert groups.shares_group("депресія", "розклад")
    assert groups.core_pair("депресія", "розклад") is None
    assert groups.core_pair("занепад", "депресія") is not None


def test_co_members_include_every_cluster_label_and_aspect_row() -> None:
    groups = _groups(KOPATY)
    assert {"рити", "вибирати", "копатися", "штикувати", "викопати"} <= groups.co_members("копати")
    assert "копати" not in groups.co_members("копати")
    assert groups.co_members("зате") == set()


def test_from_sources_db_reads_only_checked_ok_entries(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE ulif_dictua_entries (
                id INTEGER PRIMARY KEY, normalized_query TEXT, homonym_checked INTEGER, status TEXT
            );
            CREATE TABLE ulif_dictua_sections (
                id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT, source_order INTEGER, payload_json TEXT
            );
            """
        )
        conn.execute("INSERT INTO ulif_dictua_entries VALUES (1, 'список', 1, 'ok')")
        conn.execute("INSERT INTO ulif_dictua_entries VALUES (2, 'копати', 0, 'ok')")
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (1, 1, 'synonyms', 0, ?)",
            (json.dumps(payload_from_row_html(SPYSOK), ensure_ascii=False),),
        )
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (2, 2, 'synonyms', 0, ?)",
            (json.dumps(payload_from_row_html(KOPATY), ensure_ascii=False),),
        )
    groups = UlifSynonymGroups.from_sources_db(db, ["спи́сок", "копати"])
    assert groups is not None and len(groups) == 1
    assert groups.core_pair("список", "перелік") is not None
    assert groups.core_pair("копати", "рити") is None
    assert UlifSynonymGroups.from_sources_db(tmp_path / "missing.db", ["список"]) is None


def test_from_sources_db_finds_groups_filed_under_another_headword(tmp_path: Path) -> None:
    # The СПИСОК group filed only under the РЕЄСТР entry still answers for перелік.
    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE ulif_dictua_entries (
                id INTEGER PRIMARY KEY, normalized_query TEXT, homonym_checked INTEGER, status TEXT
            );
            CREATE TABLE ulif_dictua_sections (
                id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT, source_order INTEGER, payload_json TEXT
            );
            """
        )
        conn.execute("INSERT INTO ulif_dictua_entries VALUES (1, 'реєстр', 1, 'ok')")
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (1, 1, 'synonyms', 0, ?)",
            (json.dumps(payload_from_row_html(SPYSOK), ensure_ascii=False),),
        )
    groups = UlifSynonymGroups.from_sources_db(db, ["перелік"])
    assert groups is not None and len(groups) == 1
    assert groups.shares_group("перелік", "каталог")
    assert groups.core_pair("список", "перелік") is not None
    unrelated = UlifSynonymGroups.from_sources_db(db, ["копати"])
    assert unrelated is not None and len(unrelated) == 0
