"""Ukrainian Euphony and Stem Alternations Engine.

Implements Ukrainian Pravopys 2019 (§ 23–25) and Academic Grammar rules for:
  1. Preposition Euphony: у vs в (§ 23), з vs із vs зі (§ 25).
  2. Conjunction Euphony: і vs й (§ 24).
  3. Historical Vowel Shifts: [о], [е] <-> [і] in open vs closed syllables (Академічна граматика).
  4. Second Palatalization: г -> з', к -> ц', х -> с' in Dative/Locative singular (Академічна граматика).
  5. First Palatalization: г -> ж, к -> ч, х -> ш in Vocative singular (Академічна граматика).
  6. Verb Iotation: Epenthetic -л- (любити -> люблю) and dental shifts (д -> дж, т -> ч, з -> ж, с -> ш) in 1st person singular (Академічна граматика).

Provides targeted pedagogical feedback explaining the phonetic rule (open vs closed syllables,
consonant cluster relief, palatalization) and guarantees zero options collisions.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ukrainian vowels
VOWELS = set("аеєиіїоуюя")
SIBILANTS = set("жчшщзсц")
SIBILANT_CLUSTERS = {"зб", "зд", "зг", "зм", "зн", "зр", "зв", "зл", "сн", "ст", "ск", "сп", "см", "шв", "шк", "шп"}


class EuphonyCategory(StrEnum):
    """Categories of euphony and stem alternations."""

    PREPOSITION_U_V = "preposition_u_v"
    CONJUNCTION_I_Y = "conjunction_i_y"
    PREPOSITION_Z_IZ_ZI = "preposition_z_iz_zi"
    VOWEL_SHIFT_O_E_I = "vowel_shift_o_e_i"
    SECOND_PALATALIZATION = "second_palatalization"
    FIRST_PALATALIZATION_VOCATIVE = "first_palatalization_vocative"
    VERB_IOTATION = "verb_iotation"


class EuphonyInterferenceType(StrEnum):
    """Taxonomy of phonetic and morphophonological errors."""

    HIATUS_CONSONANT_CLASH = "hiatus_consonant_clash"
    HIATUS_VOWEL_CLASH = "hiatus_vowel_clash"
    SIBILANT_CLUSTER_CLASH = "sibilant_cluster_clash"
    NON_ALTERNATING_STEM = "non_alternating_stem"
    FIRST_FOR_SECOND_PALATALIZATION = "first_for_second_palatalization"
    MISSING_EPENTHETIC_L = "missing_epenthetic_l"
    NON_ALTERNATING_DENTAL = "non_alternating_dental"
    RUSSIAN_CLOSED_SYLLABLE_CALQUE = "russian_closed_syllable_calque"


@dataclass(frozen=True)
class EuphonyDistractor:
    """A distractor option with pedagogical explanation and error classification."""

    form: str
    interference_type: EuphonyInterferenceType
    explanation_ua: str
    explanation_en: str


@dataclass
class EuphonyCard:
    """A verified challenge card for euphony or stem alternation."""

    id: str
    category: EuphonyCategory
    prompt_ua: str
    prompt_en: str
    target_display: str
    correct_answer: str
    options: list[str]
    distractors: list[dict[str, Any]] = field(default_factory=list)
    pedagogical_rule_ua: str = ""
    pedagogical_rule_en: str = ""
    pravopys_ref: str = "Правопис 2019, § 23–25; Академічна граматика"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "prompt_ua": self.prompt_ua,
            "prompt_en": self.prompt_en,
            "target_display": self.target_display,
            "correct_answer": self.correct_answer,
            "options": self.options,
            "distractors": self.distractors,
            "pedagogical_rule_ua": self.pedagogical_rule_ua,
            "pedagogical_rule_en": self.pedagogical_rule_en,
            "pravopys_ref": self.pravopys_ref,
        }


def ends_with_vowel(word: str) -> bool:
    """Check if word ends with a Ukrainian vowel."""
    clean = word.rstrip(".,;:!?»\"') \n\t")
    return bool(clean) and clean[-1].lower() in VOWELS


def starts_with_vowel(word: str) -> bool:
    """Check if word starts with a Ukrainian vowel."""
    clean = word.lstrip("«\"'( \n\t")
    return bool(clean) and clean[0].lower() in VOWELS


def resolve_u_v_rule(prev_word: str | None, next_word: str) -> tuple[str, str, str]:
    """Resolve correct preposition У vs В per Правопис 2019 (§ 23)."""
    next_clean = next_word.lstrip("«\"'( \n\t").lower()
    prev_clean = prev_word.rstrip(".,;:!?»\"') \n\t").lower() if prev_word else None

    # Condition 1: Before в, ф or clusters with в/ф (льв, хв, св, тв...)
    if next_clean.startswith(("в", "ф", "льв", "хв", "св", "тв")):
        return (
            "у",
            "Перед словами, що починаються на в, ф або буквосполучення льв, хв, св, тв, завжди вживається «у» "
            "для уникнення важковимовного збігу приголосних.",
            "Always use 'у' before words starting with 'в', 'ф', or clusters like 'льв', 'хв' to avoid consonant clash.",
        )

    # Condition 2: Beginning of sentence or after pause
    if not prev_clean:
        if starts_with_vowel(next_word):
            return (
                "в",
                "На початку речення перед голосним уживається «в»: «В очах радість».",
                "At the start of a sentence before a vowel, use 'в'.",
            )
        return (
            "у",
            "На початку речення перед приголосним уживається «у»: «У лісі тихо».",
            "At the start of a sentence before a consonant, use 'у'.",
        )

    # Condition 3: Between consonants
    if not ends_with_vowel(prev_clean) and not starts_with_vowel(next_clean):
        return (
            "у",
            "Між приголосними завжди вживається «у» для милозвучності: «день у школі», «він у місті».",
            "Between consonants, always use 'у' for euphony.",
        )

    # Condition 4: Between vowels
    if ends_with_vowel(prev_clean) and starts_with_vowel(next_clean):
        return (
            "в",
            "Між голосними вживається «в» для уникнення зяяння (збігу голосних): «була в Одесі».",
            "Between vowels, use 'в' to prevent vowel hiatus.",
        )

    # Condition 5: After vowel before consonant
    if ends_with_vowel(prev_clean) and not starts_with_vowel(next_clean):
        return (
            "в",
            "Після голосного перед приголосним уживається «в»: «була в Києві», «жила в селі».",
            "After a vowel before a consonant, use 'в'.",
        )

    # Condition 6: After consonant before vowel
    return (
        "в",
        "Після приголосного перед голосним уживається «в»: «він в аудиторії».",
        "After a consonant before a vowel, use 'в'.",
    )


def resolve_i_y_rule(prev_word: str | None, next_word: str) -> tuple[str, str, str]:
    """Resolve correct conjunction І vs Й per Правопис 2019 (§ 24)."""
    next_clean = next_word.lstrip("«\"'( \n\t").lower()
    prev_clean = prev_word.rstrip(".,;:!?»\"') \n\t").lower() if prev_word else None

    if not prev_clean:
        return (
            "і",
            "На початку речення зазвичай уживається сполучник «і»: «І день іде...».",
            "At the beginning of a sentence, the conjunction 'і' is used.",
        )

    # Between consonants -> і
    if not ends_with_vowel(prev_clean) and not starts_with_vowel(next_clean):
        return (
            "і",
            "Між приголосними вживається сполучник «і»: «брат і сестра», «стіл і стілець».",
            "Between consonants, use 'і'.",
        )

    # Between vowels -> й
    if ends_with_vowel(prev_clean) and starts_with_vowel(next_clean):
        return (
            "й",
            "Між голосними вживається сполучник «й»: «мама й донька», «весна й осінь».",
            "Between vowels, use 'й'.",
        )

    # After vowel before consonant -> й
    if ends_with_vowel(prev_clean) and not starts_with_vowel(next_clean):
        return (
            "й",
            "Після голосного перед приголосним уживається сполучник «й»: «висока й струнка».",
            "After a vowel before a consonant, use 'й'.",
        )

    # After consonant before vowel -> і
    return (
        "і",
        "Після приголосного перед голосним уживається «і»: «дуб і ясен».",
        "After a consonant before a vowel, use 'і'.",
    )


def resolve_z_iz_zi_rule(prev_word: str | None, next_word: str) -> tuple[str, str, str]:
    """Resolve correct preposition З vs ІЗ vs ЗІ per Правопис 2019 (§ 25)."""
    next_clean = next_word.lstrip("«\"'( \n\t").lower()
    prev_clean = prev_word.rstrip(".,;:!?»\"') \n\t").lower() if prev_word else None

    # Condition 1: with pronoun «мною»
    if next_clean.startswith("мн"):
        return (
            "зі",
            "Перед займенником «мною» завжди вживається «зі»: «зі мною».",
            "Before 'мною', always use 'зі': 'зі мною'.",
        )

    # Condition 2: before sibilant clusters (с, з, ш, ж + consonant)
    if any(next_clean.startswith(c) for c in SIBILANT_CLUSTERS) or (
        len(next_clean) >= 2 and next_clean[0] in SIBILANTS and next_clean[1] not in VOWELS
    ):
        return (
            "зі",
            "Перед сполученням кількох приголосних, особливо із свистячими чи шиплячими "
            "(с, з, ш, ж, ч, щ), уживається «зі»: «зі сну», «зі страху», «зі школи».",
            "Before consonant clusters, especially with sibilants (s, z, sh, zh...), use 'зі': 'зі сну'.",
        )

    # Condition 3: before a vowel -> з
    if starts_with_vowel(next_clean):
        return (
            "з",
            "Перед голосним завжди вживається прийменник «з»: «з одного боку», «з артистом».",
            "Before a vowel, always use 'з': 'з одного боку'.",
        )

    # Condition 4: between consonants to avoid heavy cluster clash (e.g. лист із Бразилії, поїзд із Харкова)
    if prev_clean and not ends_with_vowel(prev_clean) and (
        (len(next_clean) >= 2 and next_clean[0] not in VOWELS and next_clean[1] not in VOWELS)
        or next_clean[0] in SIBILANTS
    ):
        return (
            "із",
            "Між приголосними для уникнення важкого збігу звуків уживається «із»: «лист із Бразилії», «поїзд із Харкова».",
            "Between consonants to avoid heavy clusters, use 'із': 'лист із Бразилії'.",
        )

    return (
        "з",
        "Перед поодиноким приголосним уживається прийменник «з»: «з братом», «з другом».",
        "Before a single consonant, use 'з': 'з братом'.",
    )


# Curated corpus of sentences and patterns for all categories
EUPHONY_SENTENCES = [
    # У vs В
    {"prev": "Він живе", "next": "Києві", "frame": "Він живе {p} Києві.", "type": "u_v"},
    {"prev": "Ольга була", "next": "Франції", "frame": "Ольга була {p} Франції.", "type": "u_v"},
    {"prev": "Студенти зайшли", "next": "аудиторію", "frame": "Студенти зайшли {p} аудиторію.", "type": "u_v"},
    {"prev": None, "next": "Львові йде дощ", "frame": "{p} Львові йде дощ.", "type": "u_v"},
    {"prev": None, "next": "очах дитини сяяла радість", "frame": "{p} очах дитини сяяла радість.", "type": "u_v"},
    {"prev": "Працював цілий день", "next": "школі", "frame": "Працював цілий день {p} школі.", "type": "u_v"},
    {"prev": "Діти гуляли", "next": "саду", "frame": "Діти гуляли {p} саду.", "type": "u_v"},
    {"prev": "Він пірнув", "next": "воду", "frame": "Він пірнув {p} воду.", "type": "u_v"},
    {"prev": "Сестра вчиться", "next": "університеті", "frame": "Сестра вчиться {p} університеті.", "type": "u_v"},
    {"prev": "Вони відпочивали", "next": "Одесі", "frame": "Вони відпочивали {p} Одесі.", "type": "u_v"},
    # І vs Й
    {"prev": "брат", "next": "сестра", "frame": "Мій брат {p} сестра вчаться разом.", "type": "i_y"},
    {"prev": "мама", "next": "тато", "frame": "Дома чекають мама {p} тато.", "type": "i_y"},
    {"prev": "весна", "next": "осінь", "frame": "У природі чергуються весна {p} осінь.", "type": "i_y"},
    {"prev": "дуб", "next": "ясен", "frame": "У лісі ростуть дуб {p} ясен.", "type": "i_y"},
    {"prev": "струнка", "next": "висока", "frame": "Вона була струнка {p} висока.", "type": "i_y"},
    # З vs ІЗ vs ЗІ
    {"prev": "Поговори", "next": "мною", "frame": "Поговори {p} мною.", "type": "z_iz_zi"},
    {"prev": "Він прокинувся", "next": "сну", "frame": "Він швидко прокинувся {p} сну.", "type": "z_iz_zi"},
    {"prev": "Ми приїхали", "next": "братом", "frame": "Ми приїхали {p} братом.", "type": "z_iz_zi"},
    {"prev": "Вони вийшли", "next": "школи", "frame": "Вони вийшли {p} школи.", "type": "z_iz_zi"},
    {"prev": "Він зустрівся", "next": "артистом", "frame": "Він зустрівся {p} артистом.", "type": "z_iz_zi"},
    {"prev": "Прийшов лист", "next": "Бразилії", "frame": "Прийшов лист {p} Бразилії.", "type": "z_iz_zi"},
]

HISTORICAL_VOWEL_SHIFTS = [
    # [о], [е] <-> [і]
    {
        "lemma": "кіт",
        "closed_nom_sg": "кіт",
        "open_gen_sg": "кота",
        "open_nom_pl": "коти",
        "frame": "Ми взяли додому маленького (кіт) ➔ ___.",
        "target": "кота",
        "calque_wrong": "кіта",
        "russian_wrong": "кот",
        "vowel_pair": "і/о",
    },
    {
        "lemma": "стіл",
        "closed_nom_sg": "стіл",
        "open_gen_sg": "стола",
        "open_nom_pl": "столи",
        "frame": "Біля вікна не було (стіл) ➔ ___.",
        "target": "стола",
        "calque_wrong": "стіла",
        "russian_wrong": "стол",
        "vowel_pair": "і/о",
    },
    {
        "lemma": "ніч",
        "closed_nom_sg": "ніч",
        "open_gen_sg": "ночі",
        "open_nom_pl": "ночі",
        "frame": "Серед глухої (ніч) ➔ ___ почувся звук.",
        "target": "ночі",
        "calque_wrong": "нічі",
        "russian_wrong": "ночь",
        "vowel_pair": "і/о",
    },
    {
        "lemma": "двір",
        "closed_nom_sg": "двір",
        "open_gen_sg": "двору",
        "open_nom_pl": "двори",
        "frame": "Діти вибігли з (двір) ➔ ___.",
        "target": "двору",
        "calque_wrong": "двіру",
        "russian_wrong": "двор",
        "vowel_pair": "і/о",
    },
    {
        "lemma": "камінь",
        "closed_nom_sg": "камінь",
        "open_gen_sg": "каменя",
        "open_nom_pl": "камені",
        "frame": "Будинок збудовано з міцного (камінь) ➔ ___.",
        "target": "каменя",
        "calque_wrong": "каміня",
        "russian_wrong": "камень",
        "vowel_pair": "і/е",
    },
    {
        "lemma": "осінь",
        "closed_nom_sg": "осінь",
        "open_gen_sg": "осені",
        "open_nom_pl": "осені",
        "frame": "До самої пізньої (осінь) ➔ ___ цвіли айстри.",
        "target": "осені",
        "calque_wrong": "осіні",
        "russian_wrong": "осень",
        "vowel_pair": "і/е",
    },
    {
        "lemma": "піч",
        "closed_nom_sg": "піч",
        "open_gen_sg": "печі",
        "open_nom_pl": "печі",
        "frame": "Бабуся витягла пиріг із (піч) ➔ ___.",
        "target": "печі",
        "calque_wrong": "пічі",
        "russian_wrong": "печь",
        "vowel_pair": "і/е",
    },
    {
        "lemma": "вечір",
        "closed_nom_sg": "вечір",
        "open_gen_sg": "вечора",
        "open_nom_pl": "вечори",
        "frame": "До самого пізнього (вечір) ➔ ___ тривала розмова.",
        "target": "вечора",
        "calque_wrong": "вечіра",
        "russian_wrong": "вечер",
        "vowel_pair": "і/о",
    },
]

SECOND_PALATALIZATION_ITEMS = [
    # г -> з', к -> ц', х -> с' in Dative/Locative
    {
        "lemma": "рука",
        "consonant": "к",
        "target": "руці",
        "frame": "У мене в (рука) ➔ ___ був квиток.",
        "wrong_unaltered": "рукі",
        "wrong_first_palat": "ручі",
        "other_form": "руку",
    },
    {
        "lemma": "нога",
        "consonant": "г",
        "target": "нозі",
        "frame": "На лівій (нога) ➔ ___ був новий черевик.",
        "wrong_unaltered": "ногі",
        "wrong_first_palat": "ножі",
        "other_form": "ногу",
    },
    {
        "lemma": "муха",
        "consonant": "х",
        "target": "мусі",
        "frame": "На крилі у (муха) ➔ ___ блищала крапля.",
        "wrong_unaltered": "мухі",
        "wrong_first_palat": "муші",
        "other_form": "муху",
    },
    {
        "lemma": "книга",
        "consonant": "г",
        "target": "книзі",
        "frame": "У цій цікавій (книга) ➔ ___ багато ілюстрацій.",
        "wrong_unaltered": "книгі",
        "wrong_first_palat": "книжі",
        "other_form": "книгу",
    },
    {
        "lemma": "аптека",
        "consonant": "к",
        "target": "аптеці",
        "frame": "Ліки купили в найближчій (аптека) ➔ ___.",
        "wrong_unaltered": "аптекі",
        "wrong_first_palat": "аптечі",
        "other_form": "аптеку",
    },
    {
        "lemma": "підлога",
        "consonant": "г",
        "target": "підлозі",
        "frame": "Килим лежить на дерев'яній (підлога) ➔ ___.",
        "wrong_unaltered": "підлогі",
        "wrong_first_palat": "підложі",
        "other_form": "підлогу",
    },
    {
        "lemma": "ріка",
        "consonant": "к",
        "target": "ріці",
        "frame": "Вода в гірській (ріка) ➔ ___ була кришталево чистою.",
        "wrong_unaltered": "рікі",
        "wrong_first_palat": "річі",
        "other_form": "ріку",
    },
    {
        "lemma": "дошка",
        "consonant": "к",
        "target": "дошці",
        "frame": "Учитель написав завдання на (дошка) ➔ ___.",
        "wrong_unaltered": "дошкі",
        "wrong_first_palat": "дошчі",
        "other_form": "дошку",
    },
]

FIRST_PALATALIZATION_VOCATIVE_ITEMS = [
    # г -> ж, к -> ч, х -> ш in Vocative
    {
        "lemma": "друг",
        "consonant": "г",
        "target": "друже",
        "frame": "Мій дорогий (друг) ➔ ___, як твої справи?",
        "wrong_unaltered": "друге",
        "wrong_second": "друзе",
        "other_form": "друга",
    },
    {
        "lemma": "чоловік",
        "consonant": "к",
        "target": "чоловіче",
        "frame": "Добрий (чоловік) ➔ ___, підкажіть дорогу!",
        "wrong_unaltered": "чоловіке",
        "wrong_second": "чоловіце",
        "other_form": "чоловіка",
    },
    {
        "lemma": "козак",
        "consonant": "к",
        "target": "козаче",
        "frame": "Славний (козак) ➔ ___, куди прямуєш?",
        "wrong_unaltered": "козаке",
        "wrong_second": "козаце",
        "other_form": "козака",
    },
    {
        "lemma": "пастух",
        "consonant": "х",
        "target": "пастуше",
        "frame": "Гей, (пастух) ➔ ___, чи бачив отару?",
        "wrong_unaltered": "пастухе",
        "wrong_second": "пастусе",
        "other_form": "пастуха",
    },
    {
        "lemma": "юнак",
        "consonant": "к",
        "target": "юначе",
        "frame": "Шановний (юнак) ➔ ___, сідайте, будь ласка.",
        "wrong_unaltered": "юнаке",
        "wrong_second": "юнаце",
        "other_form": "юнака",
    },
]

VERB_IOTATION_ITEMS = [
    # Labials: б, п, в, м, ф + [j] -> insert л
    {
        "infinitive": "любити",
        "stem_type": "labial",
        "target": "люблю",
        "frame": "Я дуже (любити) ➔ ___ українські пісні.",
        "wrong_missing_l": "любу",
        "wrong_person": "любиш",
        "wrong_plural": "люблять",
        "rule_ua": "Губні приголосні (б, п, в, м, ф) перед я, ю, є вимагають вставного [л]: любити ➔ люблю.",
        "rule_en": "Labial consonants (б, п, в, м, ф) require an epenthetic [л]: любити ➔ люблю.",
    },
    {
        "infinitive": "купити",
        "stem_type": "labial",
        "target": "куплю",
        "frame": "Завтра я обов'язково (купити) ➔ ___ свіжий хліб.",
        "wrong_missing_l": "купю",
        "wrong_person": "купиш",
        "wrong_plural": "куплять",
        "rule_ua": "Губні приголосні (б, п, в, м, ф) перед ю у 1-й особі однини мають вставний [л]: купити ➔ куплю.",
        "rule_en": "Labial consonants require epenthetic [л]: купити ➔ куплю.",
    },
    {
        "infinitive": "робити",
        "stem_type": "labial",
        "target": "роблю",
        "frame": "Щодня я (робити) ➔ ___ ранкову зарядку.",
        "wrong_missing_l": "робю",
        "wrong_person": "робиш",
        "wrong_plural": "роблять",
        "rule_ua": "Губний [б] у 1-й особі однини чергується з [бл]: робити ➔ роблю.",
        "rule_en": "Labial [б] alternates with [бл]: робити ➔ роблю.",
    },
    # Dentals: д -> дж, т -> ч, з -> ж, с -> ш
    {
        "infinitive": "ходити",
        "stem_type": "dental_d",
        "target": "ходжу",
        "frame": "Щовечора я (ходити) ➔ ___ пішки до парку.",
        "wrong_missing_l": "ходю",
        "wrong_person": "ходиш",
        "wrong_plural": "ходять",
        "rule_ua": "Зубний приголосний [д] у 1-й особі однини чергується з [дж]: ходити ➔ ходжу.",
        "rule_en": "Dental [д] alternates with [дж]: ходити ➔ ходжу.",
    },
    {
        "infinitive": "сидіти",
        "stem_type": "dental_d",
        "target": "сиджу",
        "frame": "Зараз я (сидіти) ➔ ___ в бібліотеці та читаю.",
        "wrong_missing_l": "сидю",
        "wrong_person": "сидиш",
        "wrong_plural": "сидять",
        "rule_ua": "Зубний [д] у 1-й особі однини чергується з [дж]: сидіти ➔ сиджу.",
        "rule_en": "Dental [д] alternates with [дж]: сидіти ➔ сиджу.",
    },
    {
        "infinitive": "платити",
        "stem_type": "dental_t",
        "target": "плачу",
        "frame": "Я завжди (платити) ➔ ___ за комунальні послуги вчасно.",
        "wrong_missing_l": "платю",
        "wrong_person": "платиш",
        "wrong_plural": "платять",
        "rule_ua": "Зубний [т] у 1-й особі однини чергується з [ч]: платити ➔ плачу.",
        "rule_en": "Dental [т] alternates with [ч]: платити ➔ плачу.",
    },
    {
        "infinitive": "просити",
        "stem_type": "dental_s",
        "target": "прошу",
        "frame": "Я дуже (просити) ➔ ___ вас про допомогу.",
        "wrong_missing_l": "просю",
        "wrong_person": "просиш",
        "wrong_plural": "просять",
        "rule_ua": "Зубний [с] у 1-й особі однини чергується з [ш]: просити ➔ прошу.",
        "rule_en": "Dental [с] alternates with [ш]: просити ➔ прошу.",
    },
    {
        "infinitive": "возити",
        "stem_type": "dental_z",
        "target": "вожу",
        "frame": "Щовихідних я (возити) ➔ ___ дітей до бабусі.",
        "wrong_missing_l": "возю",
        "wrong_person": "возиш",
        "wrong_plural": "возять",
        "rule_ua": "Зубний [з] у 1-й особі однини чергується з [ж]: возити ➔ вожу.",
        "rule_en": "Dental [з] alternates with [ж]: возити ➔ вожу.",
    },
]


def generate_preposition_card(item: dict[str, Any], idx: int) -> EuphonyCard:
    """Generate a preposition/conjunction euphony card with 4 distinct choices."""
    rng = random.Random(f"prep_{idx}_{item['frame']}")
    cat_type = item["type"]

    if cat_type == "u_v":
        correct_p, rule_ua, rule_en = resolve_u_v_rule(item["prev"], item["next"])
        cat = EuphonyCategory.PREPOSITION_U_V
        distractor_p = "в" if correct_p == "у" else "у"
        distractors_pool = [
            EuphonyDistractor(
                form=distractor_p,
                interference_type=(
                    EuphonyInterferenceType.HIATUS_CONSONANT_CLASH
                    if correct_p == "у"
                    else EuphonyInterferenceType.HIATUS_VOWEL_CLASH
                ),
                explanation_ua=f"Неправильно. Тут потрібен прийменник «{correct_p}»: {rule_ua}",
                explanation_en=f"Incorrect. Here '{correct_p}' is required: {rule_en}",
            ),
            EuphonyDistractor(
                form="до",
                interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
                explanation_ua="Прийменник «до» змінює значення напрямку/руху, тоді як контекст вимагає місцезнаходження.",
                explanation_en="The preposition 'до' implies direction rather than static location.",
            ),
            EuphonyDistractor(
                form="на",
                interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
                explanation_ua="Прийменник «на» не узгоджується семантично з цим просторовим орієнтиром.",
                explanation_en="The preposition 'на' does not semantically fit this spatial context.",
            ),
        ]
        options = [correct_p, distractor_p, "до", "на"]
        pravopys_ref = "Правопис 2019, § 23"

    elif cat_type == "i_y":
        correct_p, rule_ua, rule_en = resolve_i_y_rule(item["prev"], item["next"])
        cat = EuphonyCategory.CONJUNCTION_I_Y
        distractor_p = "й" if correct_p == "і" else "і"
        distractors_pool = [
            EuphonyDistractor(
                form=distractor_p,
                interference_type=(
                    EuphonyInterferenceType.HIATUS_CONSONANT_CLASH
                    if correct_p == "і"
                    else EuphonyInterferenceType.HIATUS_VOWEL_CLASH
                ),
                explanation_ua=f"Неправильно. Тут потрібен сполучник «{correct_p}»: {rule_ua}",
                explanation_en=f"Incorrect. Here '{correct_p}' is required: {rule_en}",
            ),
            EuphonyDistractor(
                form="та",
                interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
                explanation_ua="Хоча «та» є синонімом, у вправі на чергування і/й слід обирати форму милозвучності.",
                explanation_en="While 'та' is a synonym, this exercise specifically practices the і/й alternation.",
            ),
            EuphonyDistractor(
                form="але",
                interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
                explanation_ua="Сполучник «але» є протиставним і суперечить єднальному значенню речення.",
                explanation_en="The conjunction 'але' is adversative ('but'), contradicting the additive meaning.",
            ),
        ]
        options = [correct_p, distractor_p, "та", "але"]
        pravopys_ref = "Правопис 2019, § 24"

    else:  # z_iz_zi
        correct_p, rule_ua, rule_en = resolve_z_iz_zi_rule(item["prev"], item["next"])
        cat = EuphonyCategory.PREPOSITION_Z_IZ_ZI
        other_choices = [p for p in ["з", "зі", "із"] if p != correct_p]
        distractors_pool = [
            EuphonyDistractor(
                form=other_choices[0],
                interference_type=EuphonyInterferenceType.SIBILANT_CLUSTER_CLASH,
                explanation_ua=f"Форма «{other_choices[0]}» створює важкий збіг звуків. {rule_ua}",
                explanation_en=f"'{other_choices[0]}' creates a harsh sound clash. {rule_en}",
            ),
            EuphonyDistractor(
                form=other_choices[1],
                interference_type=EuphonyInterferenceType.SIBILANT_CLUSTER_CLASH,
                explanation_ua=f"Форма «{other_choices[1]}» тут надлишкова або фонетично невідповідна. {rule_ua}",
                explanation_en=f"'{other_choices[1]}' is phonetically inappropriate here. {rule_en}",
            ),
            EuphonyDistractor(
                form="від",
                interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
                explanation_ua="Прийменник «від» означає вихідний пункт або віддалення, а не спільність чи джерело.",
                explanation_en="The preposition 'від' implies departure away from, not accompaniment.",
            ),
        ]
        options = [correct_p, other_choices[0], other_choices[1], "від"]
        pravopys_ref = "Правопис 2019, § 25"

    rng.shuffle(options)
    prompt_ua = item["frame"].replace("{p}", "___")
    prompt_en = f"Select the correct euphonic particle: {prompt_ua}"

    return EuphonyCard(
        id=f"euphony-{cat.value}-{idx}",
        category=cat,
        prompt_ua=prompt_ua,
        prompt_en=prompt_en,
        target_display=correct_p,
        correct_answer=correct_p,
        options=options,
        distractors=[
            {
                "form": d.form,
                "interference_type": d.interference_type.value,
                "explanation_ua": d.explanation_ua,
                "explanation_en": d.explanation_en,
            }
            for d in distractors_pool
        ],
        pedagogical_rule_ua=rule_ua,
        pedagogical_rule_en=rule_en,
        pravopys_ref=pravopys_ref,
    )


def generate_vowel_shift_card(item: dict[str, Any], idx: int) -> EuphonyCard:
    """Generate a card testing [о], [е] <-> [і] vowel alternation in open vs closed syllables."""
    rng = random.Random(f"vowel_{idx}_{item['lemma']}")
    correct = item["target"]
    calque = item["calque_wrong"]
    russian = item["russian_wrong"]
    other = item["open_nom_pl"] if item["open_nom_pl"] != correct else item["closed_nom_sg"]

    distractors_pool = [
        EuphonyDistractor(
            form=calque,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=(
                f"У відкритому складі голосний [і] закономірно чергується з [{item['vowel_pair'].split('/')[-1]}]: "
                f"«{item['closed_nom_sg']}» (закритий склад) ➔ «{correct}» (відкритий склад). Форма «{calque}» є помилковою."
            ),
            explanation_en=(
                f"In open syllables, [і] regularly alternates with [{item['vowel_pair'].split('/')[-1]}]: "
                f"'{item['closed_nom_sg']}' (closed) ➔ '{correct}' (open). '{calque}' is incorrect."
            ),
        ),
        EuphonyDistractor(
            form=russian,
            interference_type=EuphonyInterferenceType.RUSSIAN_CLOSED_SYLLABLE_CALQUE,
            explanation_ua=(
                f"Форма «{russian}» є російською або початковою формою без відмінкового закінчення. "
                f"В українській мові в закритому складі виступає [і] («{item['closed_nom_sg']}»), "
                f"а у відкритому — «{correct}»."
            ),
            explanation_en=(
                f"'{russian}' is a Russianism or uninflected form. Ukrainian has [і] in closed syllables "
                f"('{item['closed_nom_sg']}') and alternates in open syllables ('{correct}')."
            ),
        ),
        EuphonyDistractor(
            form=other,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=(
                f"Форма «{other}» не відповідає граматичному контексту цього речення; потрібна форма «{correct}»."
            ),
            explanation_en=f"The form '{other}' does not match the required case; '{correct}' is needed.",
        ),
    ]

    options = [correct, calque, russian, other]
    rng.shuffle(options)

    rule_ua = (
        "В українській мові звуки [о], [е] у відкритих складах закономірно чергуються з [і] "
        "у закритих складах: кіт — кота, ніч — ночі, камінь — каменя."
    )
    rule_en = (
        "In Ukrainian, vowels [о], [е] in open syllables alternate with [і] in closed syllables: "
        "кіт — кота, ніч — ночі, камінь — каменя."
    )

    prompt_ua = item["frame"]
    prompt_en = f"Complete the sentence with the correctly alternated form for ({item['lemma']}):"

    return EuphonyCard(
        id=f"stem-vowel-{item['lemma']}-{idx}",
        category=EuphonyCategory.VOWEL_SHIFT_O_E_I,
        prompt_ua=prompt_ua,
        prompt_en=prompt_en,
        target_display=correct,
        correct_answer=correct,
        options=options,
        distractors=[
            {
                "form": d.form,
                "interference_type": d.interference_type.value,
                "explanation_ua": d.explanation_ua,
                "explanation_en": d.explanation_en,
            }
            for d in distractors_pool
        ],
        pedagogical_rule_ua=rule_ua,
        pedagogical_rule_en=rule_en,
        pravopys_ref="Академічна граматика: чергування [о], [е] з [і]",
    )


def generate_second_palatalization_card(item: dict[str, Any], idx: int) -> EuphonyCard:
    """Generate a card testing second palatalization (г, к, х -> з', ц', с' in Dative/Locative)."""
    rng = random.Random(f"palat2_{idx}_{item['lemma']}")
    correct = item["target"]
    unaltered = item["wrong_unaltered"]
    first_palat = item["wrong_first_palat"]
    other = item["other_form"]

    cons = item["consonant"]
    target_cons = "з'" if cons == "г" else ("ц'" if cons == "к" else "с'")

    distractors_pool = [
        EuphonyDistractor(
            form=unaltered,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=(
                f"У давальному та місцевому відмінках однини приголосний [{cons}] обов'язково чергується "
                f"із [{target_cons}]: «{item['lemma']}» ➔ «{correct}». Форма «{unaltered}» є російською калькою."
            ),
            explanation_en=(
                f"In Dative/Locative singular, [{cons}] must alternate with [{target_cons}]: "
                f"'{item['lemma']}' ➔ '{correct}'. '{unaltered}' is a Russianism calque."
            ),
        ),
        EuphonyDistractor(
            form=first_palat,
            interference_type=EuphonyInterferenceType.FIRST_FOR_SECOND_PALATALIZATION,
            explanation_ua=(
                f"Форма «{first_palat}» містить звук першої палаталізації (як у кличному відмінку), "
                f"але в давальному/місцевому відмінку відбувається друга палаталізація: [{cons}] ➔ [{target_cons}] («{correct}»)."
            ),
            explanation_en=(
                f"'{first_palat}' mistakenly uses first palatalization. Dative/Locative requires second "
                f"palatalization: [{cons}] ➔ [{target_cons}] ('{correct}')."
            ),
        ),
        EuphonyDistractor(
            form=other,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=f"Форма «{other}» є знахідним відмінком, а контекст вимагає місцевого відмінка («{correct}»).",
            explanation_en=f"'{other}' is Accusative case; Locative case ('{correct}') is required.",
        ),
    ]

    options = [correct, unaltered, first_palat, other]
    rng.shuffle(options)

    rule_ua = (
        "Друга перехідна палаталізація: перед закінченням -і у давальному та місцевому відмінках "
        "приголосні г, к, х чергуються із з', ц', с': нога ➔ на нозі, рука ➔ на руці, муха ➔ на мусі."
    )
    rule_en = (
        "Second palatalization: before -і in Dative and Locative singular, consonants г, к, х "
        "shift to з', ц', с': нога ➔ на нозі, рука ➔ на руці, муха ➔ на мусі."
    )

    return EuphonyCard(
        id=f"stem-palat2-{item['lemma']}-{idx}",
        category=EuphonyCategory.SECOND_PALATALIZATION,
        prompt_ua=item["frame"],
        prompt_en=f"Choose the correct alternated form for ({item['lemma']}):",
        target_display=correct,
        correct_answer=correct,
        options=options,
        distractors=[
            {
                "form": d.form,
                "interference_type": d.interference_type.value,
                "explanation_ua": d.explanation_ua,
                "explanation_en": d.explanation_en,
            }
            for d in distractors_pool
        ],
        pedagogical_rule_ua=rule_ua,
        pedagogical_rule_en=rule_en,
        pravopys_ref="Академічна граматика: друга палаталізація (г, к, х ➔ з', ц', с')",
    )


def generate_first_palatalization_vocative_card(item: dict[str, Any], idx: int) -> EuphonyCard:
    """Generate a card testing first palatalization in Vocative singular (г, к, х -> ж, ч, ш)."""
    rng = random.Random(f"palat1_{idx}_{item['lemma']}")
    correct = item["target"]
    unaltered = item["wrong_unaltered"]
    second_palat = item["wrong_second"]
    other = item["other_form"]

    cons = item["consonant"]
    target_cons = "ж" if cons == "г" else ("ч" if cons == "к" else "ш")

    distractors_pool = [
        EuphonyDistractor(
            form=unaltered,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=(
                f"У кличному відмінку перед закінченням -е приголосний [{cons}] закономірно чергується "
                f"із [{target_cons}]: «{item['lemma']}» ➔ «{correct}». Форма «{unaltered}» є ненормативною."
            ),
            explanation_en=(
                f"In Vocative singular before -е, [{cons}] alternates with [{target_cons}]: "
                f"'{item['lemma']}' ➔ '{correct}'. '{unaltered}' is non-standard."
            ),
        ),
        EuphonyDistractor(
            form=second_palat,
            interference_type=EuphonyInterferenceType.FIRST_FOR_SECOND_PALATALIZATION,
            explanation_ua=(
                f"Звук другої палаталізації вживається у давальному/місцевому відмінку, "
                f"а в кличному відмінку діє перша палаталізація: [{cons}] ➔ [{target_cons}] («{correct}»)."
            ),
            explanation_en=(
                f"Second palatalization occurs in Dative/Locative; Vocative requires first palatalization: "
                f"[{cons}] ➔ [{target_cons}] ('{correct}')."
            ),
        ),
        EuphonyDistractor(
            form=other,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=f"Форма «{other}» є формою родового/знахідного відмінка, а не кличного («{correct}»).",
            explanation_en=f"'{other}' is Genitive/Accusative case, not Vocative ('{correct}').",
        ),
    ]

    options = [correct, unaltered, second_palat, other]
    rng.shuffle(options)

    rule_ua = (
        "Перша палаталізація у кличному відмінку: приголосні г, к, х перед закінченням -е "
        "чергуються з ж, ч, ш: друг ➔ друже, козак ➔ козаче, пастух ➔ пастуше."
    )
    rule_en = (
        "First palatalization in Vocative singular: consonants г, к, х shift to ж, ч, ш before -е: "
        "друг ➔ друже, козак ➔ козаче, пастух ➔ пастуше."
    )

    return EuphonyCard(
        id=f"stem-palat1-{item['lemma']}-{idx}",
        category=EuphonyCategory.FIRST_PALATALIZATION_VOCATIVE,
        prompt_ua=item["frame"],
        prompt_en=f"Choose the correct vocative form for ({item['lemma']}):",
        target_display=correct,
        correct_answer=correct,
        options=options,
        distractors=[
            {
                "form": d.form,
                "interference_type": d.interference_type.value,
                "explanation_ua": d.explanation_ua,
                "explanation_en": d.explanation_en,
            }
            for d in distractors_pool
        ],
        pedagogical_rule_ua=rule_ua,
        pedagogical_rule_en=rule_en,
        pravopys_ref="Академічна граматика: перша палаталізація (г, к, х ➔ ж, ч, ш)",
    )


def generate_verb_iotation_card(item: dict[str, Any], idx: int) -> EuphonyCard:
    """Generate a card testing verb iotation in 1st person singular present/future."""
    rng = random.Random(f"iotation_{idx}_{item['infinitive']}")
    correct = item["target"]
    wrong_iotation = item["wrong_missing_l"]
    wrong_person = item["wrong_person"]
    wrong_plural = item["wrong_plural"]

    is_labial = item["stem_type"] == "labial"
    interference = (
        EuphonyInterferenceType.MISSING_EPENTHETIC_L if is_labial else EuphonyInterferenceType.NON_ALTERNATING_DENTAL
    )

    distractors_pool = [
        EuphonyDistractor(
            form=wrong_iotation,
            interference_type=interference,
            explanation_ua=f"Неправильно. {item['rule_ua']} Форма «{wrong_iotation}» є помилковою.",
            explanation_en=f"Incorrect. {item['rule_en']} The form '{wrong_iotation}' is an error.",
        ),
        EuphonyDistractor(
            form=wrong_person,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=f"Форма «{wrong_person}» є 2-ю особою однини (ти), а контекст вимагає 1-ї особи (я ➔ «{correct}»).",
            explanation_en=f"'{wrong_person}' is 2nd person (ти); 1st person (я ➔ '{correct}') is required.",
        ),
        EuphonyDistractor(
            form=wrong_plural,
            interference_type=EuphonyInterferenceType.NON_ALTERNATING_STEM,
            explanation_ua=f"Форма «{wrong_plural}» є 3-ю особою множини (вони), а контекст вимагає 1-ї особи однини (я ➔ «{correct}»).",
            explanation_en=f"'{wrong_plural}' is 3rd person plural (вони); 1st person singular ('{correct}') is required.",
        ),
    ]

    options = [correct, wrong_iotation, wrong_person, wrong_plural]
    rng.shuffle(options)

    prompt_ua = item["frame"]
    prompt_en = f"Choose the correct 1st person form for ({item['infinitive']}):"

    return EuphonyCard(
        id=f"stem-iotation-{item['infinitive']}-{idx}",
        category=EuphonyCategory.VERB_IOTATION,
        prompt_ua=prompt_ua,
        prompt_en=prompt_en,
        target_display=correct,
        correct_answer=correct,
        options=options,
        distractors=[
            {
                "form": d.form,
                "interference_type": d.interference_type.value,
                "explanation_ua": d.explanation_ua,
                "explanation_en": d.explanation_en,
            }
            for d in distractors_pool
        ],
        pedagogical_rule_ua=item["rule_ua"],
        pedagogical_rule_en=item["rule_en"],
        pravopys_ref="Академічна граматика: чергування приголосних у дієсловах ІІ дієвідміни",
    )


def validate_euphony_card(card: EuphonyCard) -> list[str]:
    """Strictly validate a euphony/stem card for correctness and zero collisions."""
    errors: list[str] = []
    if len(card.options) != 4:
        errors.append(f"Card {card.id} has {len(card.options)} options, expected 4.")
    if len(set(card.options)) != 4:
        errors.append(f"Collision in {card.id}: options {card.options} contain duplicates.")
    if card.correct_answer not in card.options:
        errors.append(f"Correct answer '{card.correct_answer}' not in options {card.options}.")
    if len(card.distractors) != 3:
        errors.append(f"Card {card.id} has {len(card.distractors)} distractors, expected 3.")
    for d in card.distractors:
        if d["form"] == card.correct_answer:
            errors.append(f"Distractor matches correct answer '{card.correct_answer}'.")
        if not d.get("explanation_ua") or not d.get("explanation_en"):
            errors.append(f"Missing explanation in distractor {d['form']}.")
        if not d.get("interference_type"):
            errors.append(f"Missing interference_type in distractor {d['form']}.")
    return errors


def generate_comprehensive_euphony_deck(target_count: int = 1200) -> list[EuphonyCard]:
    """Generate a balanced deck covering preposition euphony and stem alternations."""
    cards: list[EuphonyCard] = []
    card_idx = 0

    while len(cards) < target_count:
        # 1. Preposition / Conjunction Euphony
        for item in EUPHONY_SENTENCES:
            card = generate_preposition_card(item, card_idx)
            errs = validate_euphony_card(card)
            if not errs:
                cards.append(card)
                card_idx += 1
            if len(cards) >= target_count:
                break

        # 2. Historical Vowel Shifts
        for item in HISTORICAL_VOWEL_SHIFTS:
            card = generate_vowel_shift_card(item, card_idx)
            errs = validate_euphony_card(card)
            if not errs:
                cards.append(card)
                card_idx += 1
            if len(cards) >= target_count:
                break

        # 3. Second Palatalization
        for item in SECOND_PALATALIZATION_ITEMS:
            card = generate_second_palatalization_card(item, card_idx)
            errs = validate_euphony_card(card)
            if not errs:
                cards.append(card)
                card_idx += 1
            if len(cards) >= target_count:
                break

        # 4. First Palatalization Vocative
        for item in FIRST_PALATALIZATION_VOCATIVE_ITEMS:
            card = generate_first_palatalization_vocative_card(item, card_idx)
            errs = validate_euphony_card(card)
            if not errs:
                cards.append(card)
                card_idx += 1
            if len(cards) >= target_count:
                break

        # 5. Verb Iotation
        for item in VERB_IOTATION_ITEMS:
            card = generate_verb_iotation_card(item, card_idx)
            errs = validate_euphony_card(card)
            if not errs:
                cards.append(card)
                card_idx += 1
            if len(cards) >= target_count:
                break

    return cards


def main() -> None:
    """CLI entrypoint for Euphony and Stem Alternations Engine."""
    parser = argparse.ArgumentParser(description="Ukrainian Euphony & Stem Alternations Engine")
    parser.add_argument("--target-cards", type=int, default=1000, help="Target cards count")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    args = parser.parse_args()

    print(f"Generating euphony & stem alternations cards (target={args.target_cards})...")
    cards = generate_comprehensive_euphony_deck(target_count=args.target_cards)
    print(f"Generated {len(cards)} cards.")

    # Category breakdown
    cat_counts: dict[str, int] = {}
    for c in cards:
        cat_counts[c.category.value] = cat_counts.get(c.category.value, 0) + 1

    print("\n--- Category Breakdown ---")
    for cat, cnt in cat_counts.items():
        print(f"  {cat}: {cnt} cards")

    # Validation
    total_errors = 0
    for c in cards:
        errs = validate_euphony_card(c)
        if errs:
            total_errors += len(errs)
            print(f"Validation error in {c.id}: {errs}")

    if total_errors == 0:
        print("\n✅ Zero-collision guarantee verified: 100% cards have 4 strictly distinct choices.")
    else:
        print(f"\n❌ {total_errors} validation errors detected!")
        sys.exit(1)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in cards], f, ensure_ascii=False, indent=2)
        print(f"Exported cards deck to {args.output}")


if __name__ == "__main__":
    main()
