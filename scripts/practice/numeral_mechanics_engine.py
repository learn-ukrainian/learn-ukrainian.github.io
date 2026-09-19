"""Ukrainian Numeral Deep Mechanics Practice Engine (Числівник).

Implements Ukrainian Pravopys 2019 and Academic Grammar rules for:
  - Part III, §§ 105–107: Морфологія — Числівник:
    * § 105: Кількісні числівники:
      - § 105.4: Відмінювання числівників від 50 до 80 (п'ятдесят — вісімдесят):
        * Відмінюється лише ДРУГА частина (-десят -> -десяти/-десятьох, -десятьом, -десятьма/-десятьома, на -десяти/-десятьох).
        * Перша частина залишається незмінною (п'ят-, шіст-, сім-, вісім-).
        * Викорінення суржикових кальок: *п'ятидесяти* ❌ -> п'ятдесяти ✅, *шестидесяти* ❌ -> шістдесяти ✅.
      - § 105.5: Відмінювання числівників від 200 до 900 (двісті — дев'ятсот):
        * Відмінюються ОБИДВІ частини:
          - Родовий: двохсот, трьохсот, чотирьохсот, п'ятисот, шестисот, семисот, восьмисот, дев'ятисот (не *п'ятиста* ❌).
          - Давальний: двомстам, трьомстам, чотирьомстам, п'ятистам, шістстам, семистам, вісімстам, дев'ятистам.
          - Орудний: двомастами, трьомастами, чотирмастами, п'ятьмастами (п'ятьомастами), шістьмастами, сьомастами, восьмастами (вісьмастами), дев'ятьмастами.
          - Місцевий: на двохстах, на трьохстах, на чотирьохстах, на п'ятистах, на шестистах.
      - § 105 (пп. 8–10) та синтаксичні норми: Збірні числівники (двоє, троє, четверо...):
        * Сполучаються з іменниками чоловічого роду (назви істот: троє братів), іменниками середнього роду (четверо вікон, троє каченят)
          та pluralia tantum (двоє дверей, троє саней).
        * Не сполучаються з іменниками жіночого роду на позначення дорослих осіб (*двоє жінок* ❌ -> дві жінки ✅).
      - § 105.7: Відмінювання числівників сорок, дев'яносто, сто:
        * Мають лише дві відмінкові форми: закінчення -о в називному та знахідному (сорок, дев'яносто, сто)
          і закінчення -а в усіх інших непрямих відмінках (сорока, дев'яноста, ста).
    * § 106: Порядкові числівники:
      - § 106.2: Відмінювання складених порядкових числівників:
        * У складених порядкових числівниках відмінюється ЛИШЕ ОСТАННЄ слово (у дві тисячі двадцять четвертому році).
    * § 107: Дробові числівники (півтора, півтори, дві третіх):
      - Дробові числівники півтора, півтори керують родовим відмінком ОДНИНИ (півтора місяця, півтори доби).
  - Синтаксис керування числівників (Синтаксичні норми ЗНО/НМТ):
    * Числівники 2, 3, 4 керують називним відмінком множини (два брати, три олівці, чотири студенти; не *два брата* ❌).
    * Числівники 5+ керують родовим відмінком множини (п'ять братів, сім олівців).
    * У складених кількісних числівниках керування залежить від ОСТАННЬОГО слова (двадцять один день, двадцять два дні, двадцять п'ять днів).
    * Дробові числівники (півтора, півтори, дві третіх) керують родовим відмінком ОДНИНИ (півтора місяця, півтори доби).
  - Культура мовлення та автентичні конструкції часу й наближеної кількості:
    * Автентичні форми позначення часу: о десятій годині (не *в десять годин* ❌), чверть на одинадцяту (не *без п'ятнадцяти* ❌),
      пів на дванадцяту (не *половина дванадцятого* ❌), за двадцять третя (не *без двадцяти три* ❌).
    * Позначення приблизної кількості інверсією: років п'ять, зо дві години; прийменники близько, понад, з (близько ста людей; не *біля ста* ❌).

Provides structured pedagogical feedback explaining the specific rule and misconception,
and guarantees zero collisions among options.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sqlite3
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class NumeralCategory(StrEnum):
    """Categories of numeral deep mechanics practice."""

    CARDINAL_50_80_INFLECTION = "cardinal_50_80_inflection"
    CARDINAL_200_900_GENITIVE = "cardinal_200_900_genitive"
    CARDINAL_200_900_DATIVE_LOCATIVE = "cardinal_200_900_dative_locative"
    CARDINAL_200_900_INSTRUMENTAL = "cardinal_200_900_instrumental"
    CARDINAL_40_90_100_PARADIGM = "cardinal_40_90_100_paradigm"
    GOVERNMENT_2_3_4_NOMINATIVE_PLURAL = "government_2_3_4_nominative_plural"
    GOVERNMENT_5_PLUS_GENITIVE_PLURAL = "government_5_plus_genitive_plural"
    GOVERNMENT_COMPOUND_LAST_DIGIT = "government_compound_last_digit"
    COLLECTIVE_MASCULINE_ANIMATE = "collective_masculine_animate"
    COLLECTIVE_RESTRICTION_FEMININE = "collective_restriction_feminine"
    COLLECTIVE_PLURALIA_TANTUM_NEUTER = "collective_pluralia_tantum_neuter"
    FRACTIONAL_PIVTORA_GOVERNMENT = "fractional_pivtora_government"
    ORDINAL_COMPOUND_DECLENSION = "ordinal_compound_declension"
    TIME_EXPRESSIONS_ANTI_CALQUE = "time_expressions_anti_calque"
    APPROXIMATE_NUMERICAL_CONSTRUCTIONS = "approximate_numerical_constructions"


class NumeralInterferenceType(StrEnum):
    """Taxonomy of morphological, syntactic, and stylistic numeral misconceptions."""

    INFLECTED_FIRST_ROOT_50_80 = "inflected_first_root_50_80"
    UNINFLECTED_BASE_FORM = "uninflected_base_form"
    CORRUPTED_ENDING_200_900 = "corrupted_ending_200_900"
    RUSSIANISM_GENITIVE_HUNDREDS = "russianism_genitive_hundreds"
    RUSSIANISM_INSTRUMENTAL_HUNDREDS = "russianism_instrumental_hundreds"
    CASE_CONFUSION_DATIVE_LOCATIVE = "case_confusion_dative_locative"
    WRONG_STEM_40_90_100 = "wrong_stem_40_90_100"
    RUSSIANISM_GENITIVE_SINGULAR_CALQUE = "russianism_genitive_singular_calque"
    WRONG_CASE_GOVERNMENT_5_PLUS = "wrong_case_government_5_plus"
    COMPOUND_GLOBAL_MISAGREEMENT = "compound_global_misagreement"
    COLLECTIVE_WITH_ADULT_FEMALE = "collective_with_adult_female"
    CARDINAL_WITH_PLURALIA_TANTUM = "cardinal_with_pluralia_tantum"
    FRACTIONAL_PLURAL_GOVERNMENT = "fractional_plural_government"
    FRACTIONAL_GENDER_MISMATCH = "fractional_gender_mismatch"
    DECLINING_PREVIOUS_ORDINAL_COMPONENTS = "declining_previous_ordinal_components"
    TIME_EXPRESSION_RUSSIAN_CALQUE = "time_expression_russian_calque"
    IMPROPER_APPROXIMATION_PREPOSITION = "improper_approximation_preposition"


@dataclass(frozen=True)
class NumeralDistractor:
    """A distractor option with specific linguistic explanation."""

    text: str
    interference_type: NumeralInterferenceType
    explanation_ua: str
    explanation_en: str


@dataclass(frozen=True)
class NumeralCard:
    """Canonical numeral practice item."""

    card_id: str
    category: NumeralCategory
    cefr_level: str
    sentence_before: str
    sentence_after: str
    correct_answer: str
    distractors: tuple[NumeralDistractor, NumeralDistractor, NumeralDistractor]
    rule_citation: str
    rule_summary_ua: str
    rule_summary_en: str

    @property
    def full_sentence(self) -> str:
        """Render complete sentence with correct answer."""
        sep_before = " " if self.sentence_before and not self.sentence_before.endswith(" ") else ""
        sep_after = (
            " "
            if self.sentence_after and not self.sentence_after.startswith((" ", ",", ".", "!", "?", ":", ";"))
            else ""
        )
        return f"{self.sentence_before}{sep_before}{self.correct_answer}{sep_after}{self.sentence_after}".strip()

    @property
    def prompt_display(self) -> str:
        """Render prompt with placeholder blank."""
        sep_before = " " if self.sentence_before and not self.sentence_before.endswith(" ") else ""
        sep_after = (
            " "
            if self.sentence_after and not self.sentence_after.startswith((" ", ",", ".", "!", "?", ":", ";"))
            else ""
        )
        return f"{self.sentence_before}{sep_before}_______{sep_after}{self.sentence_after}".strip()

    def all_options(self, seed: int | None = None) -> list[str]:
        """Return 4 unique shuffled options with deterministic balanced positioning."""
        opts = [self.correct_answer] + [d.text for d in self.distractors]
        if seed is not None:
            rnd = random.Random(seed)
        else:
            card_seed = int(hashlib.sha256(self.card_id.encode("utf-8")).hexdigest()[:8], 16)
            rnd = random.Random(card_seed)
        rnd.shuffle(opts)
        return opts


def resolve_cardinal_50_80_rule() -> tuple[str, str, str]:
    citation = "Правопис 2019 § 105.4"
    ua = "У числівниках на позначення десятків 50–80 (п'ятдесят — вісімдесят) відмінюється лише друга частина (-десят); перша частина ніколи не змінюється: п'ятдесяти (не *п'ятидесяти*), шістдесятьма (не *шестидесятьма*)."
    en = "In numerals 50–80 (п'ятдесят — вісімдесят), only the second root declines (-десят); the first root remains invariant: п'ятдесяти (not *п'ятидесяти*), шістдесятьма (not *шестидесятьма*)."
    return citation, ua, en


def resolve_cardinal_200_900_genitive_rule() -> tuple[str, str, str]:
    citation = "Правопис 2019 § 105.5"
    ua = "У числівниках на позначення сотень 200–900 у родовому відмінку відмінюються обидві частини, і друга частина має закінчення -сот: двохсот, трьохсот, чотирьохсот, п'ятисот, шестисот (не *п'ятиста*)."
    en = "In numerals 200–900 in the Genitive case, both roots decline and the second root ends in -сот: двохсот, трьохсот, п'ятисот, шестисот (not *п'ятиста*)."
    return citation, ua, en


def resolve_cardinal_200_900_dative_locative_rule() -> tuple[str, str, str]:
    citation = "Правопис 2019 § 105.5"
    ua = "У давальному відмінку числівники 200–900 мають закінчення -стам (двомстам, трьомстам, п'ятистам), а в місцевому — -стах (на двохстах, на трьохстах, на п'ятистах)."
    en = "In the Dative case, numerals 200–900 end in -стам (двомстам, п'ятистам); in the Locative case, they end in -стах (на двохстах, на п'ятистах)."
    return citation, ua, en


def resolve_cardinal_200_900_instrumental_rule() -> tuple[str, str, str]:
    citation = "Правопис 2019 § 105.5"
    ua = "В орудному відмінку числівники 200–900 мають закінчення -стами: двомастами, трьомастами, чотирмастами, п'ятьмастами (не *п'ятистами*)."
    en = "In the Instrumental case, numerals 200–900 end in -стами: двомастами, трьомастами, чотирмастами, п'ятьмастами (not *п'ятистами*)."
    return citation, ua, en


def resolve_cardinal_40_90_100_rule() -> tuple[str, str, str]:
    citation = "Правопис 2019 § 105.7"
    ua = "Числівники сорок, дев'яносто, сто мають лише дві форми: закінчення -о в називному й знахідному відмінках та закінчення -а в усіх непрямих відмінках (сорока, дев'яноста, ста)."
    en = "Numerals сорок, дев'яносто, сто have only two forms: ending -о in Nominative/Accusative and ending -а in all oblique cases (сорока, дев'яноста, ста)."
    return citation, ua, en


def resolve_government_2_3_4_rule() -> tuple[str, str, str]:
    citation = "Синтаксичні норми української мови / Правопис 2019"
    ua = "Числівники два, три, чотири керують іменниками у формі називного відмінка множини: два брати, три олівці, чотири студенти (калька родового відмінка *два брата* неприпустима)."
    en = "Numerals два, три, чотири govern nouns in the Nominative plural: два брати, три олівці, чотири студенти (calque *два брата* is incorrect)."
    return citation, ua, en


def resolve_government_5_plus_rule() -> tuple[str, str, str]:
    citation = "Синтаксичні норми української мови"
    ua = "Числівники від п'яти й більше (п'ять, шість, десять, двадцять тощо) у називному відмінку керують іменниками у формі родового відмінка множини: п'ять братів, десять рулонів, сім книжок."
    en = "Numerals from five onwards (п'ять, шість, десять...) in the Nominative govern nouns in the Genitive plural: п'ять братів, десять рулонів, сім книжок."
    return citation, ua, en


def resolve_government_compound_last_digit_rule() -> tuple[str, str, str]:
    citation = "Синтаксичні норми української мови"
    ua = "У складених числівниках форма іменника визначається винятково останнім словом: на один — називний однини (двадцять один день), на два, три, чотири — називний множини (тридцять два дні), на п'ять і більше — родовий множини (сорок п'ять днів)."
    en = "In compound numerals, noun agreement is determined strictly by the last numeral: ending in один -> Nom sing, ending in два/три/чотири -> Nom plur, ending in 5+ -> Gen plur."
    return citation, ua, en


def resolve_collective_masculine_rule() -> tuple[str, str, str]:
    citation = "Синтаксичні норми української мови / Правопис 2019 § 105 (пп. 8–10)"
    ua = "Збірні числівники (двоє, троє, четверо, п'ятеро тощо) природно вживаються з іменниками чоловічого роду — назвами осіб: двоє братів, троє друзів, четверо хлопців."
    en = "Collective numerals (двоє, троє, четверо...) naturally combine with masculine animate nouns denoting persons: двоє братів, троє друзів, четверо хлопців."
    return citation, ua, en


def resolve_collective_feminine_restriction_rule() -> tuple[str, str, str]:
    citation = "Синтаксичні норми української мови (сполучуваність збірних числівників)"
    ua = "Збірні числівники НЕ вживаються з іменниками жіночого роду на позначення дорослих осіб: вживаються лише власне кількісні числівники — дві жінки (не *двоє жінок*), три сестри (не *троє сестер*)."
    en = "Collective numerals are NOT used with feminine nouns denoting adult persons: only cardinal numerals are admissible — дві жінки (not *двоє жінок*), три сестри (not *троє сестер*)."
    return citation, ua, en


def resolve_collective_pluralia_neuter_rule() -> tuple[str, str, str]:
    citation = "Синтаксичні норми української мови / Правопис 2019 § 105 (пп. 8–10)"
    ua = "Збірні числівники обов'язково вживаються з іменниками, що мають лише форму множини (pluralia tantum: двоє дверей, троє ножиць, двоє саней), а також із назвами малят (четверо каченят)."
    en = "Collective numerals are mandatory with pluralia tantum nouns (двоє дверей, троє ножиць, двоє саней) and neuter nouns denoting young animals/beings (четверо каченят)."
    return citation, ua, en


def resolve_fractional_pivtora_rule() -> tuple[str, str, str]:
    citation = "Правопис 2019 § 107"
    ua = "Дробові числівники півтора (для чоловічого та середнього роду) і півтори (для жіночого роду) завжди керують іменниками у формі родового відмінка ОДНИНИ: півтора року, півтори доби, півтора місяця."
    en = "Fractional numerals півтора (masc/neut) and півтори (fem) always govern nouns in the Genitive SINGULAR: півтора року, півтори доби, півтора місяця."
    return citation, ua, en


def resolve_ordinal_compound_declension_rule() -> tuple[str, str, str]:
    citation = "Правопис 2019 § 106.2"
    ua = "У складених порядкових числівниках відмінюється ЛИШЕ ОСТАННЄ слово; усі попередні слова зберігають початкову форму називного відмінка: у дві тисячі двадцять четвертому році (не *у двох тисячах*)."
    en = "In compound ordinal numerals, ONLY the last word inflects; all preceding words remain in the Nominative: у дві тисячі двадцять четвертому році (not *у двох тисячах*)."
    return citation, ua, en


def resolve_time_expressions_rule() -> tuple[str, str, str]:
    citation = "Культура мовлення / Автентичні синтаксичні норми"
    ua = "Для позначення точного часу в українській мові вживають прийменник 'о' / 'об' із порядковим числівником (о десятій годині), форми 'чверть на одинадцяту', 'пів на дванадцяту', 'за двадцять третя' (кальки *в десять годин*, *без двадцяти* неприпустимі)."
    en = "Authentic Ukrainian time expressions use 'о' + ordinal numeral (о десятій годині), 'чверть на одинадцяту', 'пів на дванадцяту', 'за двадцять третя' (calques *в десять годин*, *без двадцяти* are errors)."
    return citation, ua, en


def resolve_approximate_constructions_rule() -> tuple[str, str, str]:
    citation = "Культура мовлення / Синтаксис"
    ua = "Приблизну кількість у нормативному літературному мовленні позначають інверсією (років п'ять, хвилин двадцять) або прийменниками близько, понад, з (близько ста; конструкція 'біля ста' має розмовний характер, а не офіційно-літературний)."
    en = "In standard literary Ukrainian, approximate quantity is expressed via inversion (років п'ять, хвилин двадцять) or prepositions близько, понад, з (близько ста; 'біля ста' is marked as colloquial)."
    return citation, ua, en


def build_canonical_numeral_cards() -> list[NumeralCard]:
    """Build all 75 canonical numeral deep mechanics cards (15 categories x 5 cards)."""
    cit_50_80, ua_50_80, en_50_80 = resolve_cardinal_50_80_rule()
    cit_200_gen, ua_200_gen, en_200_gen = resolve_cardinal_200_900_genitive_rule()
    cit_200_dat, ua_200_dat, en_200_dat = resolve_cardinal_200_900_dative_locative_rule()
    cit_200_ins, ua_200_ins, en_200_ins = resolve_cardinal_200_900_instrumental_rule()
    cit_40_90, ua_40_90, en_40_90 = resolve_cardinal_40_90_100_rule()
    cit_gov_234, ua_gov_234, en_gov_234 = resolve_government_2_3_4_rule()
    cit_gov_5p, ua_gov_5p, en_gov_5p = resolve_government_5_plus_rule()
    cit_gov_comp, ua_gov_comp, en_gov_comp = resolve_government_compound_last_digit_rule()
    cit_coll_masc, ua_coll_masc, en_coll_masc = resolve_collective_masculine_rule()
    cit_coll_fem, ua_coll_fem, en_coll_fem = resolve_collective_feminine_restriction_rule()
    cit_coll_plur, ua_coll_plur, en_coll_plur = resolve_collective_pluralia_neuter_rule()
    cit_frac, ua_frac, en_frac = resolve_fractional_pivtora_rule()
    cit_ord, ua_ord, en_ord = resolve_ordinal_compound_declension_rule()
    cit_time, ua_time, en_time = resolve_time_expressions_rule()
    cit_approx, ua_approx, en_approx = resolve_approximate_constructions_rule()

    cards: list[NumeralCard] = [
        # -------------------------------------------------------------
        # Category 1: CARDINAL_50_80_INFLECTION (Cards 1–5)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_01",
            category=NumeralCategory.CARDINAL_50_80_INFLECTION,
            cefr_level="A2",
            sentence_before="У конференції взяли участь понад",
            sentence_after="делегатів із різних країн Європи.",
            correct_answer="п'ятдесят",
            distractors=(
                NumeralDistractor(
                    text="п'ятидесят",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="У числівнику 50 перша частина 'п'ят-' ніколи не відмінюється; форма *п'ятидесят* є грубою помилкою.",
                    explanation_en="In numeral 50, the first root 'п'ят-' never inflects; *п'ятидесят* is an erroneous form.",
                ),
                NumeralDistractor(
                    text="п'ятидесяти",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Форма *п'ятидесяти* є калькою з російської мови; після прийменника понад вживається знахідний відмінок 'п'ятдесят'.",
                    explanation_en="The form *п'ятидесяти* is a Russian calque; after preposition 'понад', Accusative 'п'ятдесят' is required.",
                ),
                NumeralDistractor(
                    text="п'ятьдесят",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Написання *п'ятьдесят* із м'яким знаком у середині слова суперечить правопису (§ 105.4).",
                    explanation_en="Spelling *п'ятьдесят* with a soft sign in the middle violates orthography rules (§ 105.4).",
                ),
            ),
            rule_citation=cit_50_80,
            rule_summary_ua=ua_50_80,
            rule_summary_en=en_50_80,
        ),
        NumeralCard(
            card_id="numeral_02",
            category=NumeralCategory.CARDINAL_50_80_INFLECTION,
            cefr_level="B1",
            sentence_before="Директор звернувся до",
            sentence_after="працівників підприємства зі словами подяки.",
            correct_answer="шістдесятьох",
            distractors=(
                NumeralDistractor(
                    text="шестидесятьох",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Перша частина 'шіст-' не змінюється: правильно 'шістдесятьох', а не суржикове *шестидесятьох*.",
                    explanation_en="The first root 'шіст-' does not decline: correctly 'шістдесятьох', not calqued *шестидесятьох*.",
                ),
                NumeralDistractor(
                    text="шістдесят",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Після прийменника 'до' обов'язковий родовий відмінок: 'шістдесятьох' або 'шістдесяти'.",
                    explanation_en="Preposition 'до' requires the Genitive case: 'шістдесятьох' or 'шістдесяти'.",
                ),
                NumeralDistractor(
                    text="шестидесяти",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Форма *шестидесяти* містить відмінювання першої частини, що неприпустимо в українській мові.",
                    explanation_en="*шестидесяти* erroneously declines the first root, which is prohibited in Ukrainian.",
                ),
            ),
            rule_citation=cit_50_80,
            rule_summary_ua=ua_50_80,
            rule_summary_en=en_50_80,
        ),
        NumeralCard(
            card_id="numeral_03",
            category=NumeralCategory.CARDINAL_50_80_INFLECTION,
            cefr_level="B1",
            sentence_before="Ми пишаємося нашими",
            sentence_after="випускниками, які вступили до вишів.",
            correct_answer="сімдесятьма",
            distractors=(
                NumeralDistractor(
                    text="семидесятьма",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="У числівнику 70 перша частина не відмінюється: правильно 'сімдесятьма', а не *семидесятьма*.",
                    explanation_en="In numeral 70, the first root is invariant: correctly 'сімдесятьма', not *семидесятьма*.",
                ),
                NumeralDistractor(
                    text="сімдесят",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="З прийменником 'з/нашими' потрібен орудний відмінок 'сімдесятьма', а не називний 'сімдесят'.",
                    explanation_en="Instrumental case 'сімдесятьма' is required here, not the Nominative base form 'сімдесят'.",
                ),
                NumeralDistractor(
                    text="семидесятьома",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Перша основа числівника 70 не набуває форми 'семи-': правильно 'сімдесятьома' або 'сімдесятьма'.",
                    explanation_en="First root never takes the form 'семи-': standard forms are 'сімдесятьома' or 'сімдесятьма'.",
                ),
            ),
            rule_citation=cit_50_80,
            rule_summary_ua=ua_50_80,
            rule_summary_en=en_50_80,
        ),
        NumeralCard(
            card_id="numeral_04",
            category=NumeralCategory.CARDINAL_50_80_INFLECTION,
            cefr_level="B1",
            sentence_before="Завдяки допомозі",
            sentence_after="волонтерів вдалося відновити будівлю лікарні.",
            correct_answer="вісімдесяти",
            distractors=(
                NumeralDistractor(
                    text="восьмидесяти",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Перша частина 'вісім-' залишається незмінною: правильно 'вісімдесяти', а не суржикове *восьмидесяти*.",
                    explanation_en="First root 'вісім-' is invariant: correctly 'вісімдесяти', not *восьмидесяти*.",
                ),
                NumeralDistractor(
                    text="вісімдесят",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Іменник 'волонтерів' стоїть у родовому відмінку, тому числівник вимагає форми 'вісімдесяти'.",
                    explanation_en="Context requires the Genitive case 'вісімдесяти', not base form 'вісімдесят'.",
                ),
                NumeralDistractor(
                    text="восьмидесятьох",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Форма *восьмидесятьох* помилково відмінює першу основу; літературна форма — 'вісімдесятьох'.",
                    explanation_en="*восьмидесятьох* improperly inflects the initial root; standard form is 'вісімдесятьох'.",
                ),
            ),
            rule_citation=cit_50_80,
            rule_summary_ua=ua_50_80,
            rule_summary_en=en_50_80,
        ),
        NumeralCard(
            card_id="numeral_05",
            category=NumeralCategory.CARDINAL_50_80_INFLECTION,
            cefr_level="B2",
            sentence_before="Організатори надали практичні рекомендації",
            sentence_after="учасникам наукової конференції.",
            correct_answer="п'ятдесятьом",
            distractors=(
                NumeralDistractor(
                    text="п'ятидесятьом",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Перша основа не відмінюється: правильно 'п'ятдесятьом', а не *п'ятидесятьом*.",
                    explanation_en="Initial stem never inflects: standard Ukrainian is 'п'ятдесятьом', not *п'ятидесятьом*.",
                ),
                NumeralDistractor(
                    text="п'ятдесят",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="У давальному відмінку потрібна форма 'п'ятдесятьом' або 'п'ятдесяти', а не називний.",
                    explanation_en="Dative case requires 'п'ятдесятьом' or 'п'ятдесяти', not uninflected Nominative.",
                ),
                NumeralDistractor(
                    text="п'ятьомдесятьом",
                    interference_type=NumeralInterferenceType.INFLECTED_FIRST_ROOT_50_80,
                    explanation_ua="Подвійне відмінювання обох частин у числівниках 50–80 є грубою граматичною помилкою.",
                    explanation_en="Declining both stems in numerals 50–80 is a severe grammatical error.",
                ),
            ),
            rule_citation=cit_50_80,
            rule_summary_ua=ua_50_80,
            rule_summary_en=en_50_80,
        ),
        # -------------------------------------------------------------
        # Category 2: CARDINAL_200_900_GENITIVE (Cards 6–10)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_06",
            category=NumeralCategory.CARDINAL_200_900_GENITIVE,
            cefr_level="A2",
            sentence_before="У залі не вистачало близько",
            sentence_after="місць для всіх зареєстрованих гостей.",
            correct_answer="двохсот",
            distractors=(
                NumeralDistractor(
                    text="двісті",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Після прийменника 'близько' обов'язковий родовий відмінок 'двохсот', а не називний 'двісті'.",
                    explanation_en="After preposition 'близько', Genitive 'двохсот' is required, not base form 'двісті'.",
                ),
                NumeralDistractor(
                    text="двохста",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_HUNDREDS,
                    explanation_ua="Закінчення *-ста* у родовому відмінку — це калька з російської мови; в українській мові норма — 'двохсот'.",
                    explanation_en="Ending *-ста* in Genitive is a Russian calque; Ukrainian norm is 'двохсот'.",
                ),
                NumeralDistractor(
                    text="двохсотів",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Закінчення *-сотів* не існує в парадигмі числівників; нормативна форма — 'двохсот'.",
                    explanation_en="Ending *-сотів* is corrupted and non-existent; standard form is 'двохсот'.",
                ),
            ),
            rule_citation=cit_200_gen,
            rule_summary_ua=ua_200_gen,
            rule_summary_en=en_200_gen,
        ),
        NumeralCard(
            card_id="numeral_07",
            category=NumeralCategory.CARDINAL_200_900_GENITIVE,
            cefr_level="B1",
            sentence_before="На придбання підручників витратили менше",
            sentence_after="гривень із бюджету школи.",
            correct_answer="трьохсот",
            distractors=(
                NumeralDistractor(
                    text="триста",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Слово 'менше' керує родовим відмінком: правильно 'трьохсот', а не називний 'триста'.",
                    explanation_en="Comparative 'менше' governs Genitive case: correctly 'трьохсот', not Nominative 'триста'.",
                ),
                NumeralDistractor(
                    text="трьохста",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_HUNDREDS,
                    explanation_ua="Форма *трьохста* є ненормативною російською калькою; друга основа має закінчення '-сот'.",
                    explanation_en="Form *трьохста* is an ungrammatical calque; second root must have ending '-сот'.",
                ),
                NumeralDistractor(
                    text="трисот",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="У числівнику 300 відмінюються обидві частини: перша частина в родовому відмінку — 'трьох-', а не 'три-'.",
                    explanation_en="In numeral 300 both roots decline: first root in Genitive is 'трьох-', not 'три-'.",
                ),
            ),
            rule_citation=cit_200_gen,
            rule_summary_ua=ua_200_gen,
            rule_summary_en=en_200_gen,
        ),
        NumeralCard(
            card_id="numeral_08",
            category=NumeralCategory.CARDINAL_200_900_GENITIVE,
            cefr_level="B1",
            sentence_before="У сховищі музею налічується понад",
            sentence_after="старовинних рукописів і грамот.",
            correct_answer="п'ятсот",
            distractors=(
                NumeralDistractor(
                    text="п'ятисот",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Після прийменника 'понад' числівники вживаються у знахідному відмінку, тотожному називному: 'понад п'ятсот', а не в родовому.",
                    explanation_en="After preposition 'понад', numerals take Accusative identical to Nominative ('понад п'ятсот'), not Genitive.",
                ),
                NumeralDistractor(
                    text="п'ятиста",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_HUNDREDS,
                    explanation_ua="Форма *п'ятиста* є помилковою суржиковою калькою; такої форми в українській мові немає.",
                    explanation_en="*п'ятиста* is an erroneous calqued form non-existent in Ukrainian.",
                ),
                NumeralDistractor(
                    text="п'ятьсот",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="У середині числівника 500 перед суфіксом м'який знак не пишеться: правильно 'п'ятсот'.",
                    explanation_en="Soft sign is not written inside numeral 500: standard spelling is 'п'ятсот'.",
                ),
            ),
            rule_citation=cit_200_gen,
            rule_summary_ua=ua_200_gen,
            rule_summary_en=en_200_gen,
        ),
        NumeralCard(
            card_id="numeral_09",
            category=NumeralCategory.CARDINAL_200_900_GENITIVE,
            cefr_level="B2",
            sentence_before="Площа нового заповідника сягає понад",
            sentence_after="гектарів незайманого лісу.",
            correct_answer="шістсот",
            distractors=(
                NumeralDistractor(
                    text="шестисот",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Прийменник 'понад' вимагає знахідного відмінка ('понад шістсот'), а не родового.",
                    explanation_en="Preposition 'понад' requires Accusative case ('понад шістсот'), not Genitive.",
                ),
                NumeralDistractor(
                    text="шестиста",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_HUNDREDS,
                    explanation_ua="Форма *шестиста* є ненормативною калькою; числівники на -сот не мають закінчення -ста.",
                    explanation_en="*шестиста* is an ungrammatical calque; numerals in -сот never take ending -ста.",
                ),
                NumeralDistractor(
                    text="шістьсот",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="У числівнику 'шістсот' спрощення відбувається на письмі, м'який знак не вживається.",
                    explanation_en="In numeral 'шістсот', simplification is orthographically fixed without a soft sign.",
                ),
            ),
            rule_citation=cit_200_gen,
            rule_summary_ua=ua_200_gen,
            rule_summary_en=en_200_gen,
        ),
        NumeralCard(
            card_id="numeral_10",
            category=NumeralCategory.CARDINAL_200_900_GENITIVE,
            cefr_level="B2",
            sentence_before="У місті проживає близько",
            sentence_after="тисяч жителів, зайнятих у промисловості.",
            correct_answer="восьмисот",
            distractors=(
                NumeralDistractor(
                    text="вісімсот",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Після прийменника 'близько' обов'язковий родовий відмінок: правильно 'восьмисот', а не 'вісімсот'.",
                    explanation_en="Preposition 'близько' requires Genitive case: correctly 'восьмисот', not base form 'вісімсот'.",
                ),
                NumeralDistractor(
                    text="восьмиста",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_HUNDREDS,
                    explanation_ua="Форма *восьмиста* — суржикова калька; друга частина числівника у родовому відмінку має вигляд '-сот'.",
                    explanation_en="*восьмиста* is an erroneous calque; Genitive of hundreds strictly ends in '-сот'.",
                ),
                NumeralDistractor(
                    text="вісьмисот",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="У непрямих відмінках числівника 800 у першій основі чергування 'і' переходить в 'о': 'восьмисот', а не *вісьмисот*.",
                    explanation_en="In oblique cases of 800, vowel alternation changes 'і' to 'о': 'восьмисот', not *вісьмисот*.",
                ),
            ),
            rule_citation=cit_200_gen,
            rule_summary_ua=ua_200_gen,
            rule_summary_en=en_200_gen,
        ),
        # -------------------------------------------------------------
        # Category 3: CARDINAL_200_900_DATIVE_LOCATIVE (Cards 11–15)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_11",
            category=NumeralCategory.CARDINAL_200_900_DATIVE_LOCATIVE,
            cefr_level="B1",
            sentence_before="Університет надав гуртожиток",
            sentence_after="іногороднім першокурсникам факультету.",
            correct_answer="двомстам",
            distractors=(
                NumeralDistractor(
                    text="двісті",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Дієслово 'надати' керує давальним відмінком адресата: 'двомстам', а не називним 'двісті'.",
                    explanation_en="Verb 'надати' governs Dative case for recipient: 'двомстам', not Nominative 'двісті'.",
                ),
                NumeralDistractor(
                    text="двомста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="У давальному відмінку друга основа закінчується на '-стам': правильно 'двомстам', а не *двомста*.",
                    explanation_en="Dative ending of hundreds is strictly '-стам': correctly 'двомстам', not *двомста*.",
                ),
                NumeralDistractor(
                    text="двохстам",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Перша частина числівника 200 у давальному відмінку має форму 'двом-', а не родову 'двох-'.",
                    explanation_en="First stem in Dative is 'двом-', not the Genitive form 'двох-'.",
                ),
            ),
            rule_citation=cit_200_dat,
            rule_summary_ua=ua_200_dat,
            rule_summary_en=en_200_dat,
        ),
        NumeralCard(
            card_id="numeral_12",
            category=NumeralCategory.CARDINAL_200_900_DATIVE_LOCATIVE,
            cefr_level="B1",
            sentence_before="Премію виплатили",
            sentence_after="науковцям за визначні досягнення.",
            correct_answer="трьомстам",
            distractors=(
                NumeralDistractor(
                    text="триста",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Контекст вимагає давального відмінка: правильно 'трьомстам', а не початкова форма 'триста'.",
                    explanation_en="Context demands Dative case: standard Ukrainian is 'трьомстам', not base form 'триста'.",
                ),
                NumeralDistractor(
                    text="трьомста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Закінчення давального відмінка сотень — '-стам': 'трьомстам', а не усічене *трьомста*.",
                    explanation_en="Standard Dative ending of hundreds is '-стам': 'трьомстам', not truncated *трьомста*.",
                ),
                NumeralDistractor(
                    text="трьохстам",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="У давальному відмінку перша частина має форму 'трьом-', а не родову 'трьох-'.",
                    explanation_en="First root takes Dative form 'трьом-', not Genitive 'трьох-'.",
                ),
            ),
            rule_citation=cit_200_dat,
            rule_summary_ua=ua_200_dat,
            rule_summary_en=en_200_dat,
        ),
        NumeralCard(
            card_id="numeral_13",
            category=NumeralCategory.CARDINAL_200_900_DATIVE_LOCATIVE,
            cefr_level="B2",
            sentence_before="Фонд надав фінансову допомогу",
            sentence_after="малозабезпеченим родинам області.",
            correct_answer="п'ятистам",
            distractors=(
                NumeralDistractor(
                    text="п'ятсот",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="У давальному відмінку числівник 500 змінюється на 'п'ятистам', основа 'п'ятсот' неприпустима.",
                    explanation_en="In Dative case, numeral 500 inflects to 'п'ятистам', base form 'п'ятсот' is incorrect.",
                ),
                NumeralDistractor(
                    text="п'ятиста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Форма *п'ятиста* є усіченою або калькованою; нормативна форма давального відмінка — 'п'ятистам'.",
                    explanation_en="*п'ятиста* is a corrupted form; standard Dative is 'п'ятистам'.",
                ),
                NumeralDistractor(
                    text="п'ятьомстам",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Перша частина числівника 500 у давальному відмінку має вигляд 'п'яти-', а не 'п'ятьом-'.",
                    explanation_en="Initial stem of 500 in Dative is 'п'яти-', not 'п'ятьом-'.",
                ),
            ),
            rule_citation=cit_200_dat,
            rule_summary_ua=ua_200_dat,
            rule_summary_en=en_200_dat,
        ),
        NumeralCard(
            card_id="numeral_14",
            category=NumeralCategory.CARDINAL_200_900_DATIVE_LOCATIVE,
            cefr_level="B2",
            sentence_before="На",
            sentence_after="сторінках цієї монографії викладено історію краю.",
            correct_answer="чотирьохстах",
            distractors=(
                NumeralDistractor(
                    text="чотириста",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="З прийменником 'на' у значенні розташування вживається місцевий відмінок: 'чотирьохстах'.",
                    explanation_en="Preposition 'на' requires Locative case: correctly 'чотирьохстах', not base form 'чотириста'.",
                ),
                NumeralDistractor(
                    text="чотирьохстам",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Закінчення '-стам' є ознакою давального відмінка, а в місцевому відмінку обов'язкове закінчення '-стах'.",
                    explanation_en="Ending '-стам' marks Dative; Locative strictly requires ending '-стах'.",
                ),
                NumeralDistractor(
                    text="чотирьохста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Форма *чотирьохста* є грубою помилкою; у місцевому відмінку норма — 'чотирьохстах'.",
                    explanation_en="*чотирьохста* is an invalid ending; Locative standard form is 'чотирьохстах'.",
                ),
            ),
            rule_citation=cit_200_dat,
            rule_summary_ua=ua_200_dat,
            rule_summary_en=en_200_dat,
        ),
        NumeralCard(
            card_id="numeral_15",
            category=NumeralCategory.CARDINAL_200_900_DATIVE_LOCATIVE,
            cefr_level="B2",
            sentence_before="На",
            sentence_after="гектарах фермерського господарства висіяли пшеницю.",
            correct_answer="шестистах",
            distractors=(
                NumeralDistractor(
                    text="шістсот",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="У місцевому відмінку числівник 600 має форму 'шестистах', а не початкову 'шістсот'.",
                    explanation_en="In Locative case, numeral 600 takes form 'шестистах', not Nominative 'шістсот'.",
                ),
                NumeralDistractor(
                    text="шестистам",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма 'шестистам' належить до давального відмінка; у місцевому відмінку норма — 'шестистах'.",
                    explanation_en="Form 'шестистам' is Dative; Locative case strictly demands 'шестистах'.",
                ),
                NumeralDistractor(
                    text="шестиста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Закінчення *-ста* не властиве місцевому відмінку числівників на позначення сотень.",
                    explanation_en="Ending *-ста* is not an admissible Locative ending for hundreds.",
                ),
            ),
            rule_citation=cit_200_dat,
            rule_summary_ua=ua_200_dat,
            rule_summary_en=en_200_dat,
        ),
        # -------------------------------------------------------------
        # Category 4: CARDINAL_200_900_INSTRUMENTAL (Cards 16–20)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_16",
            category=NumeralCategory.CARDINAL_200_900_INSTRUMENTAL,
            cefr_level="B1",
            sentence_before="Командир пишався своїми",
            sentence_after="бійцями, які стримали наступ ворога.",
            correct_answer="двомастами",
            distractors=(
                NumeralDistractor(
                    text="двісті",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Дієслово 'пишатися' вимагає орудного відмінка: правильно 'двомастами', а не називний 'двісті'.",
                    explanation_en="Verb 'пишатися' governs Instrumental case: correctly 'двомастами', not Nominative 'двісті'.",
                ),
                NumeralDistractor(
                    text="двомаста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="В орудному відмінку друга основа має закінчення '-стами': 'двомастами', а не усічене *двомаста*.",
                    explanation_en="In Instrumental case, second root ends in '-стами': 'двомастами', not truncated *двомаста*.",
                ),
                NumeralDistractor(
                    text="двумастами",
                    interference_type=NumeralInterferenceType.RUSSIANISM_INSTRUMENTAL_HUNDREDS,
                    explanation_ua="Форма *двумастами* є фонетичною калькою з російської мови; українська норма — 'двомастами'.",
                    explanation_en="*двумастами* is a Russian phonetic calque; Ukrainian norm is strictly 'двомастами'.",
                ),
            ),
            rule_citation=cit_200_ins,
            rule_summary_ua=ua_200_ins,
            rule_summary_en=en_200_ins,
        ),
        NumeralCard(
            card_id="numeral_17",
            category=NumeralCategory.CARDINAL_200_900_INSTRUMENTAL,
            cefr_level="B1",
            sentence_before="Автобус вирушив у рейс із",
            sentence_after="пасажирами на борту.",
            correct_answer="трьомастами",
            distractors=(
                NumeralDistractor(
                    text="триста",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="З прийменником 'із' вживається орудний відмінок: правильно 'трьомастами', а не 'триста'.",
                    explanation_en="Preposition 'із' takes Instrumental case: standard form is 'трьомастами', not 'триста'.",
                ),
                NumeralDistractor(
                    text="трьомаста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Усічена форма *трьомаста* суперечить літературній нормі орудного відмінка ('трьомастами').",
                    explanation_en="Truncated form *трьомаста* violates standard Ukrainian Instrumental morphology ('трьомастами').",
                ),
                NumeralDistractor(
                    text="трьохстами",
                    interference_type=NumeralInterferenceType.RUSSIANISM_INSTRUMENTAL_HUNDREDS,
                    explanation_ua="Перша частина в орудному відмінку має форму 'трьома-', а не родову 'трьох-' (*трехстами*).",
                    explanation_en="First stem in Instrumental takes 'трьома-', not Genitive calqued 'трьох-'.",
                ),
            ),
            rule_citation=cit_200_ins,
            rule_summary_ua=ua_200_ins,
            rule_summary_en=en_200_ins,
        ),
        NumeralCard(
            card_id="numeral_18",
            category=NumeralCategory.CARDINAL_200_900_INSTRUMENTAL,
            cefr_level="B2",
            sentence_before="Перед",
            sentence_after="слухачами виступив провідний професор університету.",
            correct_answer="чотирмастами",
            distractors=(
                NumeralDistractor(
                    text="чотириста",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Прийменник 'перед' вимагає орудного відмінка: правильно 'чотирмастами', а не початкова форма 'чотириста'.",
                    explanation_en="Preposition 'перед' governs Instrumental case: correctly 'чотирмастами', not 'чотириста'.",
                ),
                NumeralDistractor(
                    text="чотирмаста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Закінчення орудного відмінка сотень — обов'язково '-стами': 'чотирмастами', а не *чотирмаста*.",
                    explanation_en="Instrumental ending of hundreds must be '-стами': 'чотирмастами', not *чотирмаста*.",
                ),
                NumeralDistractor(
                    text="чотирьохстами",
                    interference_type=NumeralInterferenceType.RUSSIANISM_INSTRUMENTAL_HUNDREDS,
                    explanation_ua="Форма *чотирьохстами* містить основу родового відмінка; в орудному відмінку вживається 'чотирмастами'.",
                    explanation_en="*чотирьохстами* erroneously uses the Genitive root; standard Instrumental is 'чотирмастами'.",
                ),
            ),
            rule_citation=cit_200_ins,
            rule_summary_ua=ua_200_ins,
            rule_summary_en=en_200_ins,
        ),
        NumeralCard(
            card_id="numeral_19",
            category=NumeralCategory.CARDINAL_200_900_INSTRUMENTAL,
            cefr_level="B2",
            sentence_before="Завод забезпечив регіон",
            sentence_after="одиницями нової спеціальної техніки.",
            correct_answer="п'ятьмастами",
            distractors=(
                NumeralDistractor(
                    text="п'ятсот",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Дієслово 'забезпечити' вимагає форми орудного відмінка: 'п'ятьмастами', а не називного 'п'ятсот'.",
                    explanation_en="Verb 'забезпечити' requires Instrumental case: 'п'ятьмастами', not base form 'п'ятсот'.",
                ),
                NumeralDistractor(
                    text="п'ятистами",
                    interference_type=NumeralInterferenceType.RUSSIANISM_INSTRUMENTAL_HUNDREDS,
                    explanation_ua="Форма *п'ятистами* є калькою з російської мови (*пятистами*); українська норма — 'п'ятьмастами'.",
                    explanation_en="*п'ятистами* is a Russian calque (*пятистами*); standard Ukrainian form is 'п'ятьмастами'.",
                ),
                NumeralDistractor(
                    text="п'ятьмаста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Усічена форма *п'ятьмаста* не відповідає літературній морфологічній нормі ('п'ятьмастами').",
                    explanation_en="Truncated form *п'ятьмаста* violates standard Ukrainian morphology ('п'ятьмастами').",
                ),
            ),
            rule_citation=cit_200_ins,
            rule_summary_ua=ua_200_ins,
            rule_summary_en=en_200_ins,
        ),
        NumeralCard(
            card_id="numeral_20",
            category=NumeralCategory.CARDINAL_200_900_INSTRUMENTAL,
            cefr_level="B2",
            sentence_before="Керівництво експедиції опікувалося",
            sentence_after="дослідниками в базовому таборі.",
            correct_answer="сьомастами",
            distractors=(
                NumeralDistractor(
                    text="сімсот",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Дієслово 'опікуватися' керує орудним відмінком: нормативна форма — 'сьомастами' (або 'сімомастами').",
                    explanation_en="Verb 'опікуватися' governs Instrumental case: standard form is 'сьомастами' (or 'сімомастами').",
                ),
                NumeralDistractor(
                    text="семистами",
                    interference_type=NumeralInterferenceType.RUSSIANISM_INSTRUMENTAL_HUNDREDS,
                    explanation_ua="Форма *семистами* є прямою калькою з російської мови; в українській мові перша частина має чергування — 'сьомастами'.",
                    explanation_en="*семистами* is a direct Russian calque; Ukrainian norm exhibits vowel alternation: 'сьомастами'.",
                ),
                NumeralDistractor(
                    text="сьомаста",
                    interference_type=NumeralInterferenceType.CORRUPTED_ENDING_200_900,
                    explanation_ua="Усічене закінчення *-ста* замість нормативного '-стами' є граматичною помилкою.",
                    explanation_en="Truncated ending *-ста* instead of standard '-стами' is a grammatical error.",
                ),
            ),
            rule_citation=cit_200_ins,
            rule_summary_ua=ua_200_ins,
            rule_summary_en=en_200_ins,
        ),
        # -------------------------------------------------------------
        # Category 5: CARDINAL_40_90_100_PARADIGM (Cards 21–25)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_21",
            category=NumeralCategory.CARDINAL_40_90_100_PARADIGM,
            cefr_level="A2",
            sentence_before="У круглому столі взяли участь близько",
            sentence_after="провідних експертів галузі.",
            correct_answer="сорока",
            distractors=(
                NumeralDistractor(
                    text="сорок",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Після прийменника 'близько' числівник вимагає форми родового відмінка на '-а': 'сорока'.",
                    explanation_en="After preposition 'близько', numeral requires Genitive ending in '-а': 'сорока'.",
                ),
                NumeralDistractor(
                    text="сороку",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Числівник 40 у непрямих відмінках має винятково закінчення '-а', форма *сороку* не існує.",
                    explanation_en="Numeral 40 in oblique cases strictly takes ending '-а', form *сороку* does not exist.",
                ),
                NumeralDistractor(
                    text="сороком",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Числівник 40 не має закінчення *-ом*; правильна форма для всіх непрямих відмінків — 'сорока'.",
                    explanation_en="Numeral 40 never takes ending *-ом*; standard oblique form is strictly 'сорока'.",
                ),
            ),
            rule_citation=cit_40_90,
            rule_summary_ua=ua_40_90,
            rule_summary_en=en_40_90,
        ),
        NumeralCard(
            card_id="numeral_22",
            category=NumeralCategory.CARDINAL_40_90_100_PARADIGM,
            cefr_level="B1",
            sentence_before="Учитель роздав індивідуальні завдання",
            sentence_after="учням випускного класу.",
            correct_answer="сорока",
            distractors=(
                NumeralDistractor(
                    text="сорок",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="У давальному відмінку числівник 40 набуває закінчення '-а': 'сорока', а не початкової форми.",
                    explanation_en="In Dative case, numeral 40 takes ending '-а': 'сорока', not base form 'сорок'.",
                ),
                NumeralDistractor(
                    text="сорокам",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Форма *сорокам* помилково утворена за зразком іменників; числівник 40 має форму 'сорока'.",
                    explanation_en="*сорокам* is erroneously modeled after noun declension; standard Dative is 'сорока'.",
                ),
                NumeralDistractor(
                    text="сороком",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Закінчення *-ом* не існує в парадигмі числівника 40: правильна форма — 'сорока'.",
                    explanation_en="Ending *-ом* does not exist in numeral 40 paradigm: standard form is 'сорока'.",
                ),
            ),
            rule_citation=cit_40_90,
            rule_summary_ua=ua_40_90,
            rule_summary_en=en_40_90,
        ),
        NumeralCard(
            card_id="numeral_23",
            category=NumeralCategory.CARDINAL_40_90_100_PARADIGM,
            cefr_level="B1",
            sentence_before="Експедиція повернулася з",
            sentence_after="новими зразками рідкісних мінералів.",
            correct_answer="дев'яноста",
            distractors=(
                NumeralDistractor(
                    text="дев'яносто",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="В орудному відмінку числівник 90 змінює закінчення '-о' на '-а': 'дев'яноста'.",
                    explanation_en="In Instrumental case, numeral 90 replaces ending '-о' with '-а': 'дев'яноста'.",
                ),
                NumeralDistractor(
                    text="дев'яностом",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Форма *дев'яностом* є помилковою; числівник 90 в усіх непрямих відмінках має форму 'дев'яноста'.",
                    explanation_en="*дев'яностом* is incorrect; numeral 90 across all oblique cases strictly takes 'дев'яноста'.",
                ),
                NumeralDistractor(
                    text="дев'яностами",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Закінчення множини *-ами* не приєднується до числівника 90; нормативна форма — 'дев'яноста'.",
                    explanation_en="Plural ending *-ами* is invalid for numeral 90; standard form is strictly 'дев'яноста'.",
                ),
            ),
            rule_citation=cit_40_90,
            rule_summary_ua=ua_40_90,
            rule_summary_en=en_40_90,
        ),
        NumeralCard(
            card_id="numeral_24",
            category=NumeralCategory.CARDINAL_40_90_100_PARADIGM,
            cefr_level="B1",
            sentence_before="Школа пишається своїми",
            sentence_after="призерами всеукраїнських олімпіад.",
            correct_answer="ста",
            distractors=(
                NumeralDistractor(
                    text="сто",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="З прикметником 'своїми' у формі орудного відмінка числівник набуває форми 'ста', а не 'сто'.",
                    explanation_en="In Instrumental case, numeral 100 takes form 'ста', not base form 'сто'.",
                ),
                NumeralDistractor(
                    text="стом",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Форма *стом* не існує в українській мові; в орудному відмінку вживається лише 'ста'.",
                    explanation_en="Form *стом* does not exist in Ukrainian; Instrumental case is strictly 'ста'.",
                ),
                NumeralDistractor(
                    text="стами",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Форма *стами* — калька з російської мови; український числівник 100 має форму 'ста'.",
                    explanation_en="Form *стами* is a Russian calque; standard Ukrainian form is 'ста'.",
                ),
            ),
            rule_citation=cit_40_90,
            rule_summary_ua=ua_40_90,
            rule_summary_en=en_40_90,
        ),
        NumeralCard(
            card_id="numeral_25",
            category=NumeralCategory.CARDINAL_40_90_100_PARADIGM,
            cefr_level="B1",
            sentence_before="На",
            sentence_after="сторінках ювілейного альбому вміщено рідкісні світлини.",
            correct_answer="ста",
            distractors=(
                NumeralDistractor(
                    text="сто",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="У місцевому відмінку числівник 100 має закінчення '-а': 'на ста сторінках'.",
                    explanation_en="In Locative case, numeral 100 takes ending '-а': 'на ста сторінках'.",
                ),
                NumeralDistractor(
                    text="стах",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Закінчення *-ах* не приєднується до числівника 100; літературна норма — 'ста'.",
                    explanation_en="Ending *-ах* is invalid for numeral 100; literary standard is strictly 'ста'.",
                ),
                NumeralDistractor(
                    text="стом",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Числівник 100 має лише дві форми: 'сто' та 'ста'; форми *стом* не існує.",
                    explanation_en="Numeral 100 has only two forms: 'сто' and 'ста'; form *стом* is invalid.",
                ),
            ),
            rule_citation=cit_40_90,
            rule_summary_ua=ua_40_90,
            rule_summary_en=en_40_90,
        ),
        # -------------------------------------------------------------
        # Category 6: GOVERNMENT_2_3_4_NOMINATIVE_PLURAL (Cards 26–30)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_26",
            category=NumeralCategory.GOVERNMENT_2_3_4_NOMINATIVE_PLURAL,
            cefr_level="A1",
            sentence_before="У моєму дворі ростуть три високі",
            sentence_after="і милують око зеленню.",
            correct_answer="дуби",
            distractors=(
                NumeralDistractor(
                    text="дуба",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Числівники 2, 3, 4 керують називним множини ('три дуби'); форма родового однини *три дуба* є російською калькою.",
                    explanation_en="Numerals 2, 3, 4 govern Nominative plural ('три дуби'); Genitive singular *три дуба* is a Russian calque.",
                ),
                NumeralDistractor(
                    text="дубів",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Родовий відмінок множини 'дубів' вживається з числівниками від 5, а не з числівником 3.",
                    explanation_en="Genitive plural 'дубів' is governed by numerals 5+, not by numeral 3.",
                ),
                NumeralDistractor(
                    text="дубові",
                    interference_type=NumeralInterferenceType.WRONG_STEM_40_90_100,
                    explanation_ua="Форма 'дубові' є давальним відмінком однини або прикметником, а не формою називного множини.",
                    explanation_en="Form 'дубові' is Dative singular or adjective, not Nominative plural.",
                ),
            ),
            rule_citation=cit_gov_234,
            rule_summary_ua=ua_gov_234,
            rule_summary_en=en_gov_234,
        ),
        NumeralCard(
            card_id="numeral_27",
            category=NumeralCategory.GOVERNMENT_2_3_4_NOMINATIVE_PLURAL,
            cefr_level="A1",
            sentence_before="На столі лежали чотири новенькі",
            sentence_after="і зошити для практичних робіт.",
            correct_answer="підручники",
            distractors=(
                NumeralDistractor(
                    text="підручника",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Числівник 4 вимагає називного відмінка множини ('чотири підручники'); *чотири підручника* — калька.",
                    explanation_en="Numeral 4 requires Nominative plural ('чотири підручники'); *чотири підручника* is a Russian calque.",
                ),
                NumeralDistractor(
                    text="підручників",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Форма 'підручників' (родовий множини) поєднується з числівниками 5 і більше, а не з 4.",
                    explanation_en="Genitive plural 'підручників' is used with 5+, not with numeral 4.",
                ),
                NumeralDistractor(
                    text="підручнику",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма давального чи місцевого відмінка однини не поєднується з числівником чотири.",
                    explanation_en="Dative/Locative singular form cannot agree with numeral 4.",
                ),
            ),
            rule_citation=cit_gov_234,
            rule_summary_ua=ua_gov_234,
            rule_summary_en=en_gov_234,
        ),
        NumeralCard(
            card_id="numeral_28",
            category=NumeralCategory.GOVERNMENT_2_3_4_NOMINATIVE_PLURAL,
            cefr_level="A2",
            sentence_before="До аудиторії зайшли два нові",
            sentence_after="і привіталися з викладачем.",
            correct_answer="студенти",
            distractors=(
                NumeralDistractor(
                    text="студента",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="В українській мові числівник 2 керує називним множини: 'два студенти', а не калькою *два студента*.",
                    explanation_en="In Ukrainian, numeral 2 governs Nominative plural: 'два студенти', not calqued *два студента*.",
                ),
                NumeralDistractor(
                    text="студентів",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Родовий відмінок множини 'студентів' вживається з числівниками від 5 (п'ять студентів).",
                    explanation_en="Genitive plural 'студентів' is governed by numerals 5+ (e.g. п'ять студентів).",
                ),
                NumeralDistractor(
                    text="студентові",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Закінчення '-ові' належить давальному відмінку однини і не вживається в ролі підмета у множині.",
                    explanation_en="Ending '-ові' marks Dative singular and cannot function as a plural subject.",
                ),
            ),
            rule_citation=cit_gov_234,
            rule_summary_ua=ua_gov_234,
            rule_summary_en=en_gov_234,
        ),
        NumeralCard(
            card_id="numeral_29",
            category=NumeralCategory.GOVERNMENT_2_3_4_NOMINATIVE_PLURAL,
            cefr_level="A2",
            sentence_before="У бібліотеці ми обрали три цікаві",
            sentence_after="із сучасної української літератури.",
            correct_answer="журнали",
            distractors=(
                NumeralDistractor(
                    text="журнала",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Після числівника 3 іменник має стояти в називному множини ('три журнали'); *три журнала* — типова калька.",
                    explanation_en="After numeral 3, noun must be in Nominative plural ('три журнали'); *три журнала* is a typical calque.",
                ),
                NumeralDistractor(
                    text="журналів",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Форма родового множини 'журналів' узгоджується з числівниками від 5, а не з числівником 3.",
                    explanation_en="Genitive plural 'журналів' agrees with numerals 5+, not with numeral 3.",
                ),
                NumeralDistractor(
                    text="журналі",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма 'журналі' є місцевим відмінком однини і граматично не узгоджується з числівником.",
                    explanation_en="Form 'журналі' is Locative singular and does not grammatically agree with the numeral.",
                ),
            ),
            rule_citation=cit_gov_234,
            rule_summary_ua=ua_gov_234,
            rule_summary_en=en_gov_234,
        ),
        NumeralCard(
            card_id="numeral_30",
            category=NumeralCategory.GOVERNMENT_2_3_4_NOMINATIVE_PLURAL,
            cefr_level="A2",
            sentence_before="На святковому столі стояли чотири порцелянові",
            sentence_after="з ароматним чаєм.",
            correct_answer="чашки",
            distractors=(
                NumeralDistractor(
                    text="чашок",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Числівник 4 поєднується з називним відмінком множини ('чотири чашки'); 'чашок' — форма для 5+.",
                    explanation_en="Numeral 4 combines with Nominative plural ('чотири чашки'); 'чашок' is used with 5+.",
                ),
                NumeralDistractor(
                    text="чашку",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма знахідного відмінка однини 'чашку' не узгоджується з підметом у множині.",
                    explanation_en="Accusative singular form 'чашку' cannot agree with a plural subject.",
                ),
                NumeralDistractor(
                    text="чашкою",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма орудного відмінка однини не може поєднуватися з числівником у ролі підмета.",
                    explanation_en="Instrumental singular form cannot combine with numeral in subject position.",
                ),
            ),
            rule_citation=cit_gov_234,
            rule_summary_ua=ua_gov_234,
            rule_summary_en=en_gov_234,
        ),
        # -------------------------------------------------------------
        # Category 7: GOVERNMENT_5_PLUS_GENITIVE_PLURAL (Cards 31–35)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_31",
            category=NumeralCategory.GOVERNMENT_5_PLUS_GENITIVE_PLURAL,
            cefr_level="A1",
            sentence_before="У нашому шкільному саду росте сім яблуневих",
            sentence_after="і багато квітів.",
            correct_answer="дерев",
            distractors=(
                NumeralDistractor(
                    text="дерева",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Числівник 7 вимагає родового відмінка множини: 'сім дерев', а не форми називного множини 'дерева'.",
                    explanation_en="Numeral 7 requires Genitive plural: 'сім дерев', not Nominative plural 'дерева'.",
                ),
                NumeralDistractor(
                    text="дерево",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Числівник 7 поєднується з іменником у множині, форма однини 'дерево' неприпустима.",
                    explanation_en="Numeral 7 combines with plural noun, singular form 'дерево' is invalid.",
                ),
                NumeralDistractor(
                    text="деревам",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Форма давального відмінка множини 'деревам' не відповідає синтаксичному керуванню числівника.",
                    explanation_en="Dative plural form 'деревам' does not match syntactic government of numeral 7.",
                ),
            ),
            rule_citation=cit_gov_5p,
            rule_summary_ua=ua_gov_5p,
            rule_summary_en=en_gov_5p,
        ),
        NumeralCard(
            card_id="numeral_32",
            category=NumeralCategory.GOVERNMENT_5_PLUS_GENITIVE_PLURAL,
            cefr_level="A2",
            sentence_before="Для ремонту кімнати майстри придбали десять",
            sentence_after="якісних шпалер.",
            correct_answer="рулонів",
            distractors=(
                NumeralDistractor(
                    text="рулони",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Числівник 10 керує родовим відмінком множини: 'десять рулонів', а не називним 'рулони'.",
                    explanation_en="Numeral 10 governs Genitive plural: 'десять рулонів', not Nominative 'рулони'.",
                ),
                NumeralDistractor(
                    text="рулона",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Форма родового відмінка однини 'рулона' не вживається з числівником 10.",
                    explanation_en="Genitive singular form 'рулона' is never governed by numeral 10.",
                ),
                NumeralDistractor(
                    text="рулон",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Числівник 10 поєднується з формою множини, форма однини 'рулон' неприпустима.",
                    explanation_en="Numeral 10 agrees with plural form, singular 'рулон' is inadmissible.",
                ),
            ),
            rule_citation=cit_gov_5p,
            rule_summary_ua=ua_gov_5p,
            rule_summary_en=en_gov_5p,
        ),
        NumeralCard(
            card_id="numeral_33",
            category=NumeralCategory.GOVERNMENT_5_PLUS_GENITIVE_PLURAL,
            cefr_level="A2",
            sentence_before="На обласну конференцію приїхали вісім",
            sentence_after="із різних районів міста.",
            correct_answer="вчителів",
            distractors=(
                NumeralDistractor(
                    text="вчителі",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Числівник 8 вимагає форми родового відмінка множини: 'вісім вчителів', а не 'вчителі'.",
                    explanation_en="Numeral 8 requires Genitive plural: 'вісім вчителів', not 'вчителі'.",
                ),
                NumeralDistractor(
                    text="вчителя",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Форма родового однини 'вчителя' не узгоджується з числівником 8.",
                    explanation_en="Genitive singular 'вчителя' does not agree with numeral 8.",
                ),
                NumeralDistractor(
                    text="вчитель",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Числівник 8 не поєднується з формою називного відмінка однини 'вчитель'.",
                    explanation_en="Numeral 8 cannot combine with Nominative singular form 'вчитель'.",
                ),
            ),
            rule_citation=cit_gov_5p,
            rule_summary_ua=ua_gov_5p,
            rule_summary_en=en_gov_5p,
        ),
        NumeralCard(
            card_id="numeral_34",
            category=NumeralCategory.GOVERNMENT_5_PLUS_GENITIVE_PLURAL,
            cefr_level="A2",
            sentence_before="У легкоатлетичних змаганнях взяли участь двадцять",
            sentence_after="із нашої спортивної школи.",
            correct_answer="спортсменів",
            distractors=(
                NumeralDistractor(
                    text="спортсмени",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Після числівника 20 вживається родовий відмінок множини: 'двадцять спортсменів'.",
                    explanation_en="After numeral 20, Genitive plural is required: 'двадцять спортсменів'.",
                ),
                NumeralDistractor(
                    text="спортсмена",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Форма родового однини 'спортсмена' не може узгоджуватися з числівником 20.",
                    explanation_en="Genitive singular form 'спортсмена' cannot agree with numeral 20.",
                ),
                NumeralDistractor(
                    text="спортсмен",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма однини 'спортсмен' не відповідає числівникові 20.",
                    explanation_en="Singular form 'спортсмен' does not match numeral 20.",
                ),
            ),
            rule_citation=cit_gov_5p,
            rule_summary_ua=ua_gov_5p,
            rule_summary_en=en_gov_5p,
        ),
        NumeralCard(
            card_id="numeral_35",
            category=NumeralCategory.GOVERNMENT_5_PLUS_GENITIVE_PLURAL,
            cefr_level="A2",
            sentence_before="Для сервірування столу офіціант приніс шість",
            sentence_after="із вишуканим візерунком.",
            correct_answer="тарілок",
            distractors=(
                NumeralDistractor(
                    text="тарілки",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Числівник 6 вимагає форми родового відмінка множини: 'шість тарілок', а не називного 'тарілки'.",
                    explanation_en="Numeral 6 requires Genitive plural: 'шість тарілок', not Nominative plural 'тарілки'.",
                ),
                NumeralDistractor(
                    text="тарілку",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма знахідного відмінка однини не узгоджується з числівником 6.",
                    explanation_en="Accusative singular form does not agree with numeral 6.",
                ),
                NumeralDistractor(
                    text="тарілка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма називного відмінка однини суперечить кількісному значенню числівника 6.",
                    explanation_en="Nominative singular form contradicts the plural quantity of numeral 6.",
                ),
            ),
            rule_citation=cit_gov_5p,
            rule_summary_ua=ua_gov_5p,
            rule_summary_en=en_gov_5p,
        ),
        # -------------------------------------------------------------
        # Category 8: GOVERNMENT_COMPOUND_LAST_DIGIT (Cards 36–40)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_36",
            category=NumeralCategory.GOVERNMENT_COMPOUND_LAST_DIGIT,
            cefr_level="B1",
            sentence_before="До завершення міжнародного проєкту залишився двадцять один",
            sentence_after="напруженої праці.",
            correct_answer="день",
            distractors=(
                NumeralDistractor(
                    text="дні",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="У складених числівниках, що закінчуються на 'один', іменник ставиться в називному однини: 'двадцять один день'.",
                    explanation_en="In compound numerals ending in 'один', noun takes Nominative singular: 'двадцять один день'.",
                ),
                NumeralDistractor(
                    text="днів",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Форма родового множини 'днів' суперечить останньому слову числівника 'один'.",
                    explanation_en="Genitive plural 'днів' violates agreement with the final numeral 'один'.",
                ),
                NumeralDistractor(
                    text="дня",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Форма родового відмінка однини 'дня' є помилковою; правильна форма — називний відмінок 'день'.",
                    explanation_en="Genitive singular 'дня' is invalid; correct form is Nominative 'день'.",
                ),
            ),
            rule_citation=cit_gov_comp,
            rule_summary_ua=ua_gov_comp,
            rule_summary_en=en_gov_comp,
        ),
        NumeralCard(
            card_id="numeral_37",
            category=NumeralCategory.GOVERNMENT_COMPOUND_LAST_DIGIT,
            cefr_level="B1",
            sentence_before="У з'їзді асоціації взяли участь тридцять два",
            sentence_after="із різних областей України.",
            correct_answer="делегати",
            distractors=(
                NumeralDistractor(
                    text="делегатів",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Останнє слово числівника — 'два', тому іменник має стояти в називному множини: 'делегати', а не 'делегатів'.",
                    explanation_en="Final numeral is 'два', so the noun takes Nominative plural: 'делегати', not 'делегатів'.",
                ),
                NumeralDistractor(
                    text="делегата",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Форма *делегата* є калькою з російської мови; українська норма — називний множини 'делегати'.",
                    explanation_en="Form *делегата* is a Russian calque; Ukrainian standard demands Nominative plural 'делегати'.",
                ),
                NumeralDistractor(
                    text="делегат",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма однини не узгоджується з числівником, що закінчується на 'два'.",
                    explanation_en="Singular form cannot agree with a numeral ending in 'два'.",
                ),
            ),
            rule_citation=cit_gov_comp,
            rule_summary_ua=ua_gov_comp,
            rule_summary_en=en_gov_comp,
        ),
        NumeralCard(
            card_id="numeral_38",
            category=NumeralCategory.GOVERNMENT_COMPOUND_LAST_DIGIT,
            cefr_level="B1",
            sentence_before="В експозиції галереї було представлено сорок чотири",
            sentence_after="сучасних художників.",
            correct_answer="картини",
            distractors=(
                NumeralDistractor(
                    text="картин",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Останнє слово — 'чотири', тому іменник ставиться у формі називного множини: 'сорок чотири картини'.",
                    explanation_en="Last word is 'чотири', requiring Nominative plural: 'сорок чотири картини'.",
                ),
                NumeralDistractor(
                    text="картину",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма знахідного відмінка однини не відповідає числівникові 'чотири' в підметі.",
                    explanation_en="Accusative singular form does not agree with numeral 'чотири' in subject position.",
                ),
                NumeralDistractor(
                    text="картиною",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма орудного відмінка однини є граматично некоректною в цьому контексті.",
                    explanation_en="Instrumental singular form is grammatically invalid in this context.",
                ),
            ),
            rule_citation=cit_gov_comp,
            rule_summary_ua=ua_gov_comp,
            rule_summary_en=en_gov_comp,
        ),
        NumeralCard(
            card_id="numeral_39",
            category=NumeralCategory.GOVERNMENT_COMPOUND_LAST_DIGIT,
            cefr_level="B1",
            sentence_before="У новому житловому комплексі налічується п'ятдесят п'ять",
            sentence_after="покращеного планування.",
            correct_answer="квартир",
            distractors=(
                NumeralDistractor(
                    text="квартири",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Останнє слово 'п'ять' вимагає родового відмінка множини: 'квартир', а не називного 'квартири'.",
                    explanation_en="Final word 'п'ять' governs Genitive plural: 'квартир', not Nominative 'квартири'.",
                ),
                NumeralDistractor(
                    text="квартиру",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма однини 'квартиру' суперечить числівникові 'п'ять'.",
                    explanation_en="Singular form 'квартиру' contradicts the numeral 'п'ять'.",
                ),
                NumeralDistractor(
                    text="квартира",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Початкова форма називного відмінка однини не може поєднуватися з числівником 'п'ять'.",
                    explanation_en="Nominative singular base form cannot combine with numeral 'п'ять'.",
                ),
            ),
            rule_citation=cit_gov_comp,
            rule_summary_ua=ua_gov_comp,
            rule_summary_en=en_gov_comp,
        ),
        NumeralCard(
            card_id="numeral_40",
            category=NumeralCategory.GOVERNMENT_COMPOUND_LAST_DIGIT,
            cefr_level="B2",
            sentence_before="В експедицію вирушив шістдесят один",
            sentence_after="із науково-дослідного інституту.",
            correct_answer="науковець",
            distractors=(
                NumeralDistractor(
                    text="науковці",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Якщо числівник закінчується на 'один', підмет ставиться в однині: 'шістдесят один науковець'.",
                    explanation_en="When a numeral ends in 'один', the subject is singular: 'шістдесят один науковець'.",
                ),
                NumeralDistractor(
                    text="науковців",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Форма родового множини 'науковців' суперечить останньому компонентові числівника 'один'.",
                    explanation_en="Genitive plural 'науковців' conflicts with the final numeral component 'один'.",
                ),
                NumeralDistractor(
                    text="науковця",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_SINGULAR_CALQUE,
                    explanation_ua="Форма родового однини не вживається в називному підметі після складеного числівника на 'один'.",
                    explanation_en="Genitive singular is not used in Nominative subject position after numeral ending in 'один'.",
                ),
            ),
            rule_citation=cit_gov_comp,
            rule_summary_ua=ua_gov_comp,
            rule_summary_en=en_gov_comp,
        ),
        # -------------------------------------------------------------
        # Category 9: COLLECTIVE_MASCULINE_ANIMATE (Cards 41–45)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_41",
            category=NumeralCategory.COLLECTIVE_MASCULINE_ANIMATE,
            cefr_level="B1",
            sentence_before="У дворі весело гралися",
            sentence_after="хлопців із сусіднього під'їзду.",
            correct_answer="троє",
            distractors=(
                NumeralDistractor(
                    text="три",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="З формою родового відмінка множини 'хлопців' на позначення групи вживається збірний числівник 'троє', а 'три' вимагає називного відмінка 'три хлопці'.",
                    explanation_en="With Genitive plural 'хлопців' denoting a group, collective 'троє' is used; cardinal 'три' governs Nominative 'три хлопці'.",
                ),
                NumeralDistractor(
                    text="трійка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Слово 'трійка' є іменником, а не числівником, і має інше граматичне значення.",
                    explanation_en="'трійка' is a noun, not a numeral, and carries a different grammatical meaning.",
                ),
                NumeralDistractor(
                    text="трьома",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма орудного відмінка 'трьома' не може виступати частиною називного підмета.",
                    explanation_en="Instrumental form 'трьома' cannot function as part of the nominative subject.",
                ),
            ),
            rule_citation=cit_coll_masc,
            rule_summary_ua=ua_coll_masc,
            rule_summary_en=en_coll_masc,
        ),
        NumeralCard(
            card_id="numeral_42",
            category=NumeralCategory.COLLECTIVE_MASCULINE_ANIMATE,
            cefr_level="B1",
            sentence_before="На автобусній зупинці стояли",
            sentence_after="друзів і жваво обговорювали плани.",
            correct_answer="двоє",
            distractors=(
                NumeralDistractor(
                    text="два",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="Числівник 'два' вимагає називного множини 'два друзі', тоді як перед формою 'друзів' виступає збірний числівник 'двоє'.",
                    explanation_en="Cardinal 'два' requires Nominative 'два друзі', whereas Genitive 'друзів' requires collective 'двоє'.",
                ),
                NumeralDistractor(
                    text="двійка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="'Двійка' є іменником на позначення оцінки або групи, а не числівником.",
                    explanation_en="'Двійка' is a noun denoting a grade or pair, not a grammatical numeral.",
                ),
                NumeralDistractor(
                    text="двома",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма орудного відмінка 'двома' не може виступати частиною називного підмета.",
                    explanation_en="Instrumental form 'двома' cannot function as part of the nominative subject.",
                ),
            ),
            rule_citation=cit_coll_masc,
            rule_summary_ua=ua_coll_masc,
            rule_summary_en=en_coll_masc,
        ),
        NumeralCard(
            card_id="numeral_43",
            category=NumeralCategory.COLLECTIVE_MASCULINE_ANIMATE,
            cefr_level="B1",
            sentence_before="До кабінету зайшли",
            sentence_after="студентів для складання іспиту.",
            correct_answer="четверо",
            distractors=(
                NumeralDistractor(
                    text="чотири",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="Числівник 'чотири' поєднується з називним відмінком 'чотири студенти', а з формою 'студентів' — збірний 'четверо'.",
                    explanation_en="Cardinal 'чотири' combines with Nominative 'чотири студенти'; Genitive 'студентів' requires collective 'четверо'.",
                ),
                NumeralDistractor(
                    text="четвірка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="'Четвірка' є іменником, що означає оцінку або групу, а не числівником.",
                    explanation_en="'Четвірка' is a noun denoting an evaluation grade or group, not a numeral.",
                ),
                NumeralDistractor(
                    text="чотирьох",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма родового відмінка 'чотирьох' не може виконувати функцію називного підмета.",
                    explanation_en="Genitive form 'чотирьох' cannot function as a Nominative subject.",
                ),
            ),
            rule_citation=cit_coll_masc,
            rule_summary_ua=ua_coll_masc,
            rule_summary_en=en_coll_masc,
        ),
        NumeralCard(
            card_id="numeral_44",
            category=NumeralCategory.COLLECTIVE_MASCULINE_ANIMATE,
            cefr_level="B2",
            sentence_before="У родині підростало",
            sentence_after="синів, які допомагали батькам по господарству.",
            correct_answer="п'ятеро",
            distractors=(
                NumeralDistractor(
                    text="п'ятьма",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма орудного відмінка 'п'ятьма' не може виступати частиною називного підмета.",
                    explanation_en="Instrumental form 'п'ятьма' cannot function as part of the nominative subject.",
                ),
                NumeralDistractor(
                    text="п'ятірка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="'П'ятірка' є іменником і не функціонує як власне числівник у цьому реченні.",
                    explanation_en="'П'ятірка' is a noun and cannot function as a core numeral in this sentence.",
                ),
                NumeralDistractor(
                    text="п'яти",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма родового відмінка числівника 'п'яти' не може виступати підметом без контексту керування.",
                    explanation_en="Genitive numeral form 'п'яти' cannot serve as subject without governing context.",
                ),
            ),
            rule_citation=cit_coll_masc,
            rule_summary_ua=ua_coll_masc,
            rule_summary_en=en_coll_masc,
        ),
        NumeralCard(
            card_id="numeral_45",
            category=NumeralCategory.COLLECTIVE_MASCULINE_ANIMATE,
            cefr_level="B2",
            sentence_before="На нараду прибули",
            sentence_after="директорів провідних підприємств регіону.",
            correct_answer="шестеро",
            distractors=(
                NumeralDistractor(
                    text="шістьма",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма орудного відмінка 'шістьма' не може виступати частиною називного підмета.",
                    explanation_en="Instrumental form 'шістьма' cannot function as part of the nominative subject.",
                ),
                NumeralDistractor(
                    text="шістка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Слово 'шістка' — це іменник, а не кількісний чи збірний числівник.",
                    explanation_en="Word 'шістка' is a noun, not a quantitative or collective numeral.",
                ),
                NumeralDistractor(
                    text="шести",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма 'шести' є непрямим відмінком і не вживається в ролі називного підмета.",
                    explanation_en="Form 'шести' is an oblique case and cannot function as a Nominative subject.",
                ),
            ),
            rule_citation=cit_coll_masc,
            rule_summary_ua=ua_coll_masc,
            rule_summary_en=en_coll_masc,
        ),
        # -------------------------------------------------------------
        # Category 10: COLLECTIVE_RESTRICTION_FEMININE (Cards 46–50)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_46",
            category=NumeralCategory.COLLECTIVE_RESTRICTION_FEMININE,
            cefr_level="B1",
            sentence_before="До магазину зайшли",
            sentence_after="і почали уважно роздивлятися нові сукні.",
            correct_answer="три жінки",
            distractors=(
                NumeralDistractor(
                    text="троє жінок",
                    interference_type=NumeralInterferenceType.COLLECTIVE_WITH_ADULT_FEMALE,
                    explanation_ua="З іменниками жіночого роду на позначення осіб збірні числівники не вживаються (*троє жінок* — помилка; літературна норма — 'три жінки').",
                    explanation_en="Collective numerals do not combine with feminine nouns denoting persons (*троє жінок* is invalid; standard norm is 'три жінки').",
                ),
                NumeralDistractor(
                    text="три жінок",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Числівник 3 вимагає називного відмінка множини ('три жінки'), а не родового (*три жінок*).",
                    explanation_en="Numeral 3 governs Nominative plural ('три жінки'), not Genitive (*три жінок*).",
                ),
                NumeralDistractor(
                    text="три жінці",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма однини 'жінці' не узгоджується з числівником 'три' у ролі підмета.",
                    explanation_en="Singular form 'жінці' cannot agree with numeral 'три' in subject role.",
                ),
            ),
            rule_citation=cit_coll_fem,
            rule_summary_ua=ua_coll_fem,
            rule_summary_en=en_coll_fem,
        ),
        NumeralCard(
            card_id="numeral_47",
            category=NumeralCategory.COLLECTIVE_RESTRICTION_FEMININE,
            cefr_level="B1",
            sentence_before="У затишному сквері розмовляли",
            sentence_after="і згадували шкільні роки.",
            correct_answer="дві подруги",
            distractors=(
                NumeralDistractor(
                    text="двоє подруг",
                    interference_type=NumeralInterferenceType.COLLECTIVE_WITH_ADULT_FEMALE,
                    explanation_ua="Вживання збірного числівника з особою жіночого роду (*двоє подруг*) є ненормативним; літературна норма — 'дві подруги'.",
                    explanation_en="Using collective numerals with female persons (*двоє подруг*) is non-standard; literary norm is 'дві подруги'.",
                ),
                NumeralDistractor(
                    text="дві подруг",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Числівник 'дві' вимагає називного відмінка множини: 'дві подруги', а не родового (*дві подруг*).",
                    explanation_en="Numeral 'дві' requires Nominative plural: 'дві подруги', not Genitive (*дві подруг*).",
                ),
                NumeralDistractor(
                    text="дві подрузі",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма однини 'подрузі' не узгоджується з числівником у функції множинного підмета.",
                    explanation_en="Singular form 'подрузі' cannot agree with numeral in plural subject position.",
                ),
            ),
            rule_citation=cit_coll_fem,
            rule_summary_ua=ua_coll_fem,
            rule_summary_en=en_coll_fem,
        ),
        NumeralCard(
            card_id="numeral_48",
            category=NumeralCategory.COLLECTIVE_RESTRICTION_FEMININE,
            cefr_level="B1",
            sentence_before="У міському конкурсі перемогли",
            sentence_after="із нашого університету.",
            correct_answer="чотири дівчини",
            distractors=(
                NumeralDistractor(
                    text="чотирьох дівчат",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма родового/знахідного відмінка 'чотирьох дівчат' не може виступати підметом у називному контексті без прийменника чи керуючого слова; правильна форма називного відмінка — 'чотири дівчини'.",
                    explanation_en="Genitive/Accusative form 'чотирьох дівчат' cannot serve as the subject in a nominative context without governing context; correct nominative form is 'чотири дівчини'.",
                ),
                NumeralDistractor(
                    text="чотири дівчат",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Числівник 4 вимагає називного множини ('чотири дівчини'), форма родового відмінка 'дівчат' вживається з 5+.",
                    explanation_en="Numeral 4 takes Nominative plural ('чотири дівчини'); Genitive 'дівчат' is governed by 5+.",
                ),
                NumeralDistractor(
                    text="чотири дівчині",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма давального/місцевого відмінка однини не може узгоджуватися з числівником у ролі підмета.",
                    explanation_en="Dative/Locative singular form cannot agree with numeral in subject position.",
                ),
            ),
            rule_citation=cit_coll_fem,
            rule_summary_ua=ua_coll_fem,
            rule_summary_en=en_coll_fem,
        ),
        NumeralCard(
            card_id="numeral_49",
            category=NumeralCategory.COLLECTIVE_RESTRICTION_FEMININE,
            cefr_level="B1",
            sentence_before="У дружній родині підростали",
            sentence_after="які завжди підтримували одна одну.",
            correct_answer="дві сестри",
            distractors=(
                NumeralDistractor(
                    text="двоє сестер",
                    interference_type=NumeralInterferenceType.COLLECTIVE_WITH_ADULT_FEMALE,
                    explanation_ua="З іменниками жіночого роду збірні числівники не вживаються: літературна норма — 'дві сестри', а не *двоє сестер*.",
                    explanation_en="Collective numerals are avoided with feminine nouns: literary norm is 'дві сестри', not *двоє сестер*.",
                ),
                NumeralDistractor(
                    text="дві сестер",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Числівник 'дві' сполучається з формою називного відмінка множини: 'дві сестри', а не родового (*дві сестер*).",
                    explanation_en="Numeral 'дві' combines with Nominative plural: 'дві сестри', not Genitive (*дві сестер*).",
                ),
                NumeralDistractor(
                    text="дві сестрою",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма орудного відмінка однини не узгоджується з числівником 'дві' у ролі підмета.",
                    explanation_en="Instrumental singular form cannot agree with numeral 'дві' in subject position.",
                ),
            ),
            rule_citation=cit_coll_fem,
            rule_summary_ua=ua_coll_fem,
            rule_summary_en=en_coll_fem,
        ),
        NumeralCard(
            card_id="numeral_50",
            category=NumeralCategory.COLLECTIVE_RESTRICTION_FEMININE,
            cefr_level="B2",
            sentence_before="На конференції виступили",
            sentence_after="із доповідями про сучасні технології.",
            correct_answer="три студентки",
            distractors=(
                NumeralDistractor(
                    text="троє студенток",
                    interference_type=NumeralInterferenceType.COLLECTIVE_WITH_ADULT_FEMALE,
                    explanation_ua="Збірний числівник *троє студенток* є помилковим для жіночих назв осіб; літературна норма — 'три студентки'.",
                    explanation_en="Collective *троє студенток* is invalid for feminine personal nouns; standard is 'три студентки'.",
                ),
                NumeralDistractor(
                    text="три студенток",
                    interference_type=NumeralInterferenceType.WRONG_CASE_GOVERNMENT_5_PLUS,
                    explanation_ua="Числівник 3 вимагає називного відмінка множини: 'три студентки', а не родового (*три студенток*).",
                    explanation_en="Numeral 3 demands Nominative plural: 'три студентки', not Genitive (*три студенток*).",
                ),
                NumeralDistractor(
                    text="три студентці",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма давального відмінка однини не узгоджується з числівником у функції підмета.",
                    explanation_en="Dative singular form cannot agree with numeral in subject role.",
                ),
            ),
            rule_citation=cit_coll_fem,
            rule_summary_ua=ua_coll_fem,
            rule_summary_en=en_coll_fem,
        ),
        # -------------------------------------------------------------
        # Category 11: COLLECTIVE_PLURALIA_TANTUM_NEUTER (Cards 51–55)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_51",
            category=NumeralCategory.COLLECTIVE_PLURALIA_TANTUM_NEUTER,
            cefr_level="B1",
            sentence_before="У новенькому коридорі встановили",
            sentence_after="дубових дверей із надійними замками.",
            correct_answer="двоє",
            distractors=(
                NumeralDistractor(
                    text="дві",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="З іменниками, що вживаються лише у множині (двері), обов'язково вживається збірний числівник 'двоє' (не *дві двері*).",
                    explanation_en="With pluralia tantum nouns (двері), collective numeral 'двоє' is compulsory (not *дві двері*).",
                ),
                NumeralDistractor(
                    text="два",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="Числівник 'два' чоловічого роду не може поєднуватися з іменником pluralia tantum 'двері'.",
                    explanation_en="Masculine numeral 'два' cannot combine with pluralia tantum noun 'двері'.",
                ),
                NumeralDistractor(
                    text="двійка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="'Двійка' — це іменник, а не числівник, і не вживається в цій синтаксичній конструкції.",
                    explanation_en="'Двійка' is a noun, not a numeral, and is inappropriate in this syntactic frame.",
                ),
            ),
            rule_citation=cit_coll_plur,
            rule_summary_ua=ua_coll_plur,
            rule_summary_en=en_coll_plur,
        ),
        NumeralCard(
            card_id="numeral_52",
            category=NumeralCategory.COLLECTIVE_PLURALIA_TANTUM_NEUTER,
            cefr_level="B1",
            sentence_before="Для майстерні кравець придбав",
            sentence_after="гострих кравецьких ножиць.",
            correct_answer="троє",
            distractors=(
                NumeralDistractor(
                    text="три",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="З іменником pluralia tantum 'ножиці' вживається винятково збірний числівник 'троє' (не *три ножиці*).",
                    explanation_en="With pluralia tantum 'ножиці', collective numeral 'троє' is strictly required (not *три ножиці*).",
                ),
                NumeralDistractor(
                    text="трійка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Слово 'трійка' є іменником і не виражає кількісного числівникового значення предметів.",
                    explanation_en="'Трійка' is a noun and cannot express quantitative numeral count of objects.",
                ),
                NumeralDistractor(
                    text="трьох",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма родового відмінка 'трьох' без прийменника не може виступати прямим додатком неістот.",
                    explanation_en="Genitive form 'трьох' without preposition cannot serve as direct object for inanimate nouns.",
                ),
            ),
            rule_citation=cit_coll_plur,
            rule_summary_ua=ua_coll_plur,
            rule_summary_en=en_coll_plur,
        ),
        NumeralCard(
            card_id="numeral_53",
            category=NumeralCategory.COLLECTIVE_PLURALIA_TANTUM_NEUTER,
            cefr_level="B1",
            sentence_before="Біля ставка плавало",
            sentence_after="жовтеньких пухнастих каченят.",
            correct_answer="четверо",
            distractors=(
                NumeralDistractor(
                    text="чотири",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="З назвами малят (середній рід IV відміни: каченята) зазвичай уживаються збірні числівники: 'четверо каченят'.",
                    explanation_en="With names of young beings (neuter declension IV: каченята), collective numerals are standard: 'четверо каченят'.",
                ),
                NumeralDistractor(
                    text="четвірка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="'Четвірка' є іменником, що означає оцінку або групу, а не власне кількісним словом.",
                    explanation_en="'Четвірка' is a noun denoting an evaluation mark or group, not a count numeral.",
                ),
                NumeralDistractor(
                    text="чотирьох",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма родового відмінка числівника 'чотирьох' не узгоджується як називний підмет речення.",
                    explanation_en="Genitive numeral form 'чотирьох' cannot function as a Nominative subject.",
                ),
            ),
            rule_citation=cit_coll_plur,
            rule_summary_ua=ua_coll_plur,
            rule_summary_en=en_coll_plur,
        ),
        NumeralCard(
            card_id="numeral_54",
            category=NumeralCategory.COLLECTIVE_PLURALIA_TANTUM_NEUTER,
            cefr_level="B2",
            sentence_before="Дідусь змайстрував для онуків",
            sentence_after="дерев'яних саней для зимових розваг.",
            correct_answer="двоє",
            distractors=(
                NumeralDistractor(
                    text="два",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="З іменником pluralia tantum 'сани' поєднуються лише збірні числівники: 'двоє саней', а не *два сани*.",
                    explanation_en="With pluralia tantum 'сани', only collective numerals are admissible: 'двоє саней', not *два сани*.",
                ),
                NumeralDistractor(
                    text="дві",
                    interference_type=NumeralInterferenceType.CARDINAL_WITH_PLURALIA_TANTUM,
                    explanation_ua="Форма жіночого роду 'дві' не поєднується з іменниками, що мають лише множину (*дві сани* — помилка).",
                    explanation_en="Feminine 'дві' cannot combine with nouns existing only in the plural (*дві сани* is invalid).",
                ),
                NumeralDistractor(
                    text="двома",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма орудного відмінка 'двома' не узгоджується як прямий додаток у цій синтаксичній позиції.",
                    explanation_en="Instrumental form 'двома' cannot function as a direct object in this syntactic position.",
                ),
            ),
            rule_citation=cit_coll_plur,
            rule_summary_ua=ua_coll_plur,
            rule_summary_en=en_coll_plur,
        ),
        NumeralCard(
            card_id="numeral_55",
            category=NumeralCategory.COLLECTIVE_PLURALIA_TANTUM_NEUTER,
            cefr_level="B2",
            sentence_before="На вітрині оптики лежало",
            sentence_after="стильних сонцезахисних окулярів.",
            correct_answer="п'ятеро",
            distractors=(
                NumeralDistractor(
                    text="п'ятьма",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма орудного відмінка 'п'ятьма' не може виступати кількісним означенням підмета.",
                    explanation_en="Instrumental form 'п'ятьма' cannot serve as a quantitative modifier of the subject.",
                ),
                NumeralDistractor(
                    text="п'ятірка",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="'П'ятірка' є іменником зі значенням оцінки або предметної групи, а не числівником.",
                    explanation_en="'П'ятірка' is a noun denoting an evaluation grade or group, not a numeral.",
                ),
                NumeralDistractor(
                    text="п'яти",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Форма родового відмінка числівника не може замінити називну форму підмета.",
                    explanation_en="Genitive form of numeral cannot substitute for Nominative subject.",
                ),
            ),
            rule_citation=cit_coll_plur,
            rule_summary_ua=ua_coll_plur,
            rule_summary_en=en_coll_plur,
        ),
        # -------------------------------------------------------------
        # Category 12: FRACTIONAL_PIVTORA_GOVERNMENT (Cards 56–60)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_56",
            category=NumeralCategory.FRACTIONAL_PIVTORA_GOVERNMENT,
            cefr_level="A2",
            sentence_before="Будівництво нового спортивного комплексу тривало півтора",
            sentence_after="без зупинки робіт.",
            correct_answer="року",
            distractors=(
                NumeralDistractor(
                    text="роки",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Числівник 'півтора' керує родовим відмінком ОДНИНИ ('півтора року'), а не називним множини 'роки'.",
                    explanation_en="Numeral 'півтора' governs Genitive SINGULAR ('півтора року'), not Nominative plural 'роки'.",
                ),
                NumeralDistractor(
                    text="років",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Форма родового відмінка множини 'років' неприпустима після числівника півтора (тільки однина: 'року').",
                    explanation_en="Genitive plural 'років' is invalid after півтора (strictly singular: 'року').",
                ),
                NumeralDistractor(
                    text="роком",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма орудного відмінка однини не відповідає синтаксичному керуванню числівника півтора.",
                    explanation_en="Instrumental singular form does not match the syntactic government of півтора.",
                ),
            ),
            rule_citation=cit_frac,
            rule_summary_ua=ua_frac,
            rule_summary_en=en_frac,
        ),
        NumeralCard(
            card_id="numeral_57",
            category=NumeralCategory.FRACTIONAL_PIVTORA_GOVERNMENT,
            cefr_level="A2",
            sentence_before="Швидкісний поїзд запізнився на півтори",
            sentence_after="через аварію на колії.",
            correct_answer="години",
            distractors=(
                NumeralDistractor(
                    text="годин",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Числівник 'півтори' (жіночий рід) керує родовим відмінком однини: 'півтори години' (не *півтори годин*).",
                    explanation_en="Feminine 'півтори' governs Genitive singular: 'півтори години' (not *півтори годин*).",
                ),
                NumeralDistractor(
                    text="годину",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма знахідного відмінка однини 'годину' не узгоджується з числівником півтори.",
                    explanation_en="Accusative singular 'годину' does not agree with numeral півтори.",
                ),
                NumeralDistractor(
                    text="годинами",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Орудний відмінок множини 'годинами' є граматично некоректним після числівника півтори.",
                    explanation_en="Instrumental plural 'годинами' is grammatically incorrect after півтори.",
                ),
            ),
            rule_citation=cit_frac,
            rule_summary_ua=ua_frac,
            rule_summary_en=en_frac,
        ),
        NumeralCard(
            card_id="numeral_58",
            category=NumeralCategory.FRACTIONAL_PIVTORA_GOVERNMENT,
            cefr_level="B1",
            sentence_before="Складна рятувальна операція тривала півтори",
            sentence_after="в екстремальних погодних умовах.",
            correct_answer="доби",
            distractors=(
                NumeralDistractor(
                    text="діб",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Числівник 'півтори' вимагає родового відмінка однини: 'доби', а не форми множини 'діб'.",
                    explanation_en="Numeral 'півтори' demands Genitive singular: 'доби', not plural form 'діб'.",
                ),
                NumeralDistractor(
                    text="добу",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма знахідного відмінка однини не відповідає правилам керування дробового числівника.",
                    explanation_en="Accusative singular form does not comply with fractional numeral government.",
                ),
                NumeralDistractor(
                    text="добою",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Орудний відмінок однини не вживається після числівника півтори.",
                    explanation_en="Instrumental singular is never governed by numeral півтори.",
                ),
            ),
            rule_citation=cit_frac,
            rule_summary_ua=ua_frac,
            rule_summary_en=en_frac,
        ),
        NumeralCard(
            card_id="numeral_59",
            category=NumeralCategory.FRACTIONAL_PIVTORA_GOVERNMENT,
            cefr_level="B1",
            sentence_before="Для приготування полуничного варення потрібно півтора",
            sentence_after="цукру.",
            correct_answer="кілограма",
            distractors=(
                NumeralDistractor(
                    text="кілограми",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Іменник чоловічого роду після числівника 'півтора' ставиться в родовому однини: 'кілограма'.",
                    explanation_en="Masculine noun after 'півтора' takes Genitive singular: 'кілограма'.",
                ),
                NumeralDistractor(
                    text="кілограмів",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Форма родового множини 'кілограмів' після півтора є помилковою; норма вимагає однини.",
                    explanation_en="Genitive plural 'кілограмів' is erroneous after півтора; standard demands singular.",
                ),
                NumeralDistractor(
                    text="кілограмом",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма орудного відмінка однини не узгоджується з числівником півтора.",
                    explanation_en="Instrumental singular form cannot agree with numeral півтора.",
                ),
            ),
            rule_citation=cit_frac,
            rule_summary_ua=ua_frac,
            rule_summary_en=en_frac,
        ),
        NumeralCard(
            card_id="numeral_60",
            category=NumeralCategory.FRACTIONAL_PIVTORA_GOVERNMENT,
            cefr_level="B1",
            sentence_before="Аспірант перебував на закордонному стажуванні півтора",
            sentence_after="і зібрав цінний матеріал.",
            correct_answer="місяця",
            distractors=(
                NumeralDistractor(
                    text="місяці",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Числівник 'півтора' керує родовим відмінком однини: 'півтора місяця', а не формою називного множини 'місяці'.",
                    explanation_en="Numeral 'півтора' governs Genitive singular: 'півтора місяця', not Nominative plural 'місяці'.",
                ),
                NumeralDistractor(
                    text="місяців",
                    interference_type=NumeralInterferenceType.FRACTIONAL_PLURAL_GOVERNMENT,
                    explanation_ua="Форма родового множини 'місяців' є типовою помилкою; після півтора вживається лише однина 'місяця'.",
                    explanation_en="Genitive plural 'місяців' is a frequent error; after півтора only singular 'місяця' is valid.",
                ),
                NumeralDistractor(
                    text="місяцем",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Форма орудного відмінка однини граматично не узгоджується з числівником півтора.",
                    explanation_en="Instrumental singular form is grammatically incompatible with numeral півтора.",
                ),
            ),
            rule_citation=cit_frac,
            rule_summary_ua=ua_frac,
            rule_summary_en=en_frac,
        ),
        # -------------------------------------------------------------
        # Category 13: ORDINAL_COMPOUND_DECLENSION (Cards 61–65)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_61",
            category=NumeralCategory.ORDINAL_COMPOUND_DECLENSION,
            cefr_level="B1",
            sentence_before="Україна відновила свою державну незалежність у",
            sentence_after="році.",
            correct_answer="тисяча дев'ятсот дев'яносто першому",
            distractors=(
                NumeralDistractor(
                    text="тисячі дев'ятисот дев'яносто першому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="У складених порядкових числівниках відмінюється ЛИШЕ останнє слово; відмінювання 'тисячі дев'ятисот' є помилкою.",
                    explanation_en="In compound ordinals, ONLY the final word inflects; inflecting 'тисячі дев'ятисот' is an error.",
                ),
                NumeralDistractor(
                    text="тисячу дев'ятсот дев'яносто першому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Слово 'тисяча' має залишатися у формі називного відмінка, а не знахідного *тисячу*.",
                    explanation_en="Word 'тисяча' must stay in Nominative, not Accusative *тисячу*.",
                ),
                NumeralDistractor(
                    text="тисяча дев'ятсот дев'яностих першому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Десятки мають залишатися незмінними ('дев'яносто'), а не набувати форми місцевого множини *дев'яностих*.",
                    explanation_en="Tens component must remain invariant ('дев'яносто'), not inflected into plural *дев'яностих*.",
                ),
            ),
            rule_citation=cit_ord,
            rule_summary_ua=ua_ord,
            rule_summary_en=en_ord,
        ),
        NumeralCard(
            card_id="numeral_62",
            category=NumeralCategory.ORDINAL_COMPOUND_DECLENSION,
            cefr_level="B1",
            sentence_before="Олімпійські ігри в Парижі відбулися у",
            sentence_after="році.",
            correct_answer="дві тисячі двадцять четвертому",
            distractors=(
                NumeralDistractor(
                    text="двох тисячах двадцять четвертому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="У складеному порядковому числівнику перша частина не відмінюється: правильно 'дві тисячі', а не *двох тисячах*.",
                    explanation_en="In compound ordinal, previous words do not decline: correctly 'дві тисячі', not *двох тисячах*.",
                ),
                NumeralDistractor(
                    text="двох тисячах двадцятому четвертому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Відмінювання всіх слів складеного числівника суперечить українському правопису (§ 106.2).",
                    explanation_en="Declining all components of a compound ordinal numeral violates Ukrainian orthography (§ 106.2).",
                ),
                NumeralDistractor(
                    text="дві тисячі двадцятому четвертому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Слово 'двадцять' не повинно відмінюватися; змінюється лише останнє слово — 'четвертому'.",
                    explanation_en="Word 'двадцять' must not inflect; only the final word inflects to 'четвертому'.",
                ),
            ),
            rule_citation=cit_ord,
            rule_summary_ua=ua_ord,
            rule_summary_en=en_ord,
        ),
        NumeralCard(
            card_id="numeral_63",
            category=NumeralCategory.ORDINAL_COMPOUND_DECLENSION,
            cefr_level="B2",
            sentence_before="Перше видання 'Кобзаря' Тараса Шевченка побачило світ у",
            sentence_after="році.",
            correct_answer="тисяча вісімсот сороковому",
            distractors=(
                NumeralDistractor(
                    text="тисячі восьмисотому сороковому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Відмінювання попередніх слів є грубою помилкою: попередні компоненти мають форму 'тисяча вісімсот'.",
                    explanation_en="Declining preceding elements is an error: initial components must be 'тисяча вісімсот'.",
                ),
                NumeralDistractor(
                    text="тисячі вісімсот сороковому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Слово 'тисяча' має зберігати форму називного відмінка, форма *тисячі* — помилкова.",
                    explanation_en="Component 'тисяча' must retain Nominative form, inflected *тисячі* is incorrect.",
                ),
                NumeralDistractor(
                    text="тисяча вісімсотому сороковому",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Сотні не відмінюються, якщо вони не є останнім словом: правильно 'вісімсот', а не *вісімсотому*.",
                    explanation_en="Hundreds do not inflect unless they form the final component: correctly 'вісімсот', not *вісімсотому*.",
                ),
            ),
            rule_citation=cit_ord,
            rule_summary_ua=ua_ord,
            rule_summary_en=en_ord,
        ),
        NumeralCard(
            card_id="numeral_64",
            category=NumeralCategory.ORDINAL_COMPOUND_DECLENSION,
            cefr_level="B1",
            sentence_before="Урочистий останній дзвінок у школі пролунає",
            sentence_after="травня.",
            correct_answer="двадцять п'ятого",
            distractors=(
                NumeralDistractor(
                    text="двадцятого п'ятого",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="У датах відмінюється лише останнє слово: правильно 'двадцять п'ятого', а не *двадцятого п'ятого*.",
                    explanation_en="In dates, only the final numeral declines: correctly 'двадцять п'ятого', not *двадцятого п'ятого*.",
                ),
                NumeralDistractor(
                    text="двадцяти п'ятого",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Слово 'двадцять' не набуває форми родового відмінка; попередні слова залишаються у формі називного.",
                    explanation_en="Word 'двадцять' does not take Genitive; preceding words remain in Nominative.",
                ),
                NumeralDistractor(
                    text="двадцять п'ятим",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="На позначення дати у відповіді на питання 'коли?' вживається родовий відмінок ('п'ятого'), а не орудний.",
                    explanation_en="To denote dates answering 'when?', Genitive case is used ('п'ятого'), not Instrumental.",
                ),
            ),
            rule_citation=cit_ord,
            rule_summary_ua=ua_ord,
            rule_summary_en=en_ord,
        ),
        NumeralCard(
            card_id="numeral_65",
            category=NumeralCategory.ORDINAL_COMPOUND_DECLENSION,
            cefr_level="B1",
            sentence_before="Звітну конференцію трудового колективу призначено на",
            sentence_after="березня.",
            correct_answer="тридцять перше",
            distractors=(
                NumeralDistractor(
                    text="тридцяте перше",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Перше слово 'тридцять' залишається незмінним: правильно 'тридцять перше', а не *тридцяте перше*.",
                    explanation_en="First word 'тридцять' remains uninflected: correctly 'тридцять перше', not *тридцяте перше*.",
                ),
                NumeralDistractor(
                    text="тридцяти перше",
                    interference_type=NumeralInterferenceType.DECLINING_PREVIOUS_ORDINAL_COMPONENTS,
                    explanation_ua="Попередній компонент не повинен приймати відмінкове закінчення: норма — 'тридцять'.",
                    explanation_en="Preceding component must not accept case inflections: standard is 'тридцять'.",
                ),
                NumeralDistractor(
                    text="тридцять першого",
                    interference_type=NumeralInterferenceType.CASE_CONFUSION_DATIVE_LOCATIVE,
                    explanation_ua="Конструкція 'призначити на...' вимагає знахідного відмінка середнього роду: 'на тридцять перше' (число).",
                    explanation_en="Construction 'призначити на...' governs Accusative neuter: 'на тридцять перше' (число).",
                ),
            ),
            rule_citation=cit_ord,
            rule_summary_ua=ua_ord,
            rule_summary_en=en_ord,
        ),
        # -------------------------------------------------------------
        # Category 14: TIME_EXPRESSIONS_ANTI_CALQUE (Cards 66–70)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_66",
            category=NumeralCategory.TIME_EXPRESSIONS_ANTI_CALQUE,
            cefr_level="A1",
            sentence_before="Пленарне засідання наукової ради розпочнеться",
            sentence_after="в головній актовій залі.",
            correct_answer="о десятій годині",
            distractors=(
                NumeralDistractor(
                    text="в десять годин",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Конструкція *в десять годин* є російською калькою; в українській мові точний час позначають: 'о десятій годині'.",
                    explanation_en="Construction *в десять годин* is a Russian calque; Ukrainian uses: 'о десятій годині'.",
                ),
                NumeralDistractor(
                    text="у десять годин",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Поєднання 'у' з кількісним числівником для вказівки на час є ненормативним (правильно — 'о десятій').",
                    explanation_en="Combining 'у' with a cardinal numeral for time is ungrammatical (correctly 'о десятій').",
                ),
                NumeralDistractor(
                    text="о десятьох годинах",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Вказівка на час потребує порядкового числівника однини ('о десятій'), а не кількісного числівника множини.",
                    explanation_en="Time designation requires singular ordinal numeral ('о десятій'), not plural cardinal.",
                ),
            ),
            rule_citation=cit_time,
            rule_summary_ua=ua_time,
            rule_summary_en=en_time,
        ),
        NumeralCard(
            card_id="numeral_67",
            category=NumeralCategory.TIME_EXPRESSIONS_ANTI_CALQUE,
            cefr_level="A2",
            sentence_before="На вокзальному годиннику зараз рівно",
            sentence_after=", і посадка на швидкісний поїзд уже розпочалася.",
            correct_answer="чверть на одинадцяту",
            distractors=(
                NumeralDistractor(
                    text="п'ятнадцять хвилин одинадцятого",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Вислів *п'ятнадцять хвилин одинадцятого* є калькою з російської; українська норма — 'чверть на одинадцяту' або 'п'ятнадцять хвилин по десятій'.",
                    explanation_en="*п'ятнадцять хвилин одинадцятого* is a calque; standard Ukrainian is 'чверть на одинадцяту' or 'по десятій'.",
                ),
                NumeralDistractor(
                    text="без п'ятнадцяти одинадцять",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Конструкція *без п'ятнадцяти* не властива українській мові; на позначення нестачі часу вживають прийменник 'за'.",
                    explanation_en="Construction *без п'ятнадцяти* is foreign to Ukrainian; preposition 'за' is used instead.",
                ),
                NumeralDistractor(
                    text="чверть одинадцятого",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Уживання родового відмінка без прийменника (*чверть одинадцятого*) є помилковим; обов'язковий прийменник 'на'.",
                    explanation_en="Using Genitive without preposition (*чверть одинадцятого*) is an error; preposition 'на' is required.",
                ),
            ),
            rule_citation=cit_time,
            rule_summary_ua=ua_time,
            rule_summary_en=en_time,
        ),
        NumeralCard(
            card_id="numeral_68",
            category=NumeralCategory.TIME_EXPRESSIONS_ANTI_CALQUE,
            cefr_level="A2",
            sentence_before="Поглянь на годинник: зараз уже",
            sentence_after="і нам час поспішати.",
            correct_answer="пів на дванадцяту",
            distractors=(
                NumeralDistractor(
                    text="половина дванадцятого",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Вислів *половина дванадцятого* — російська калька; літературна українська форма — 'пів на дванадцяту'.",
                    explanation_en="*половина дванадцятого* is a Russian calque; literary Ukrainian norm is 'пів на дванадцяту'.",
                ),
                NumeralDistractor(
                    text="пів дванадцятого",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Форма без прийменника 'на' (*пів дванадцятого*) є суржиковою; норма вимагає конструкції 'пів на + знахідний'.",
                    explanation_en="Form lacking preposition 'на' (*пів дванадцятого*) is non-standard; norm requires 'пів на + Accusative'.",
                ),
                NumeralDistractor(
                    text="пів дванадцять",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Сполука *пів дванадцять* є спотвореною розмовною калькою, неприпустимою в літературній мові.",
                    explanation_en="*пів дванадцять* is a corrupted colloquial calque unacceptable in standard Ukrainian.",
                ),
            ),
            rule_citation=cit_time,
            rule_summary_ua=ua_time,
            rule_summary_en=en_time,
        ),
        NumeralCard(
            card_id="numeral_69",
            category=NumeralCategory.TIME_EXPRESSIONS_ANTI_CALQUE,
            cefr_level="B1",
            sentence_before="Поглянь на шкільний годинник: зараз уже",
            sentence_after=", і дзвінок на перерву пролунає за лічені хвилини.",
            correct_answer="за двадцять третя",
            distractors=(
                NumeralDistractor(
                    text="без двадцяти три",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Конструкція *без двадцяти три* є прямою калькою з російської мови; українська норма — 'за двадцять третя'.",
                    explanation_en="Construction *без двадцяти три* is a direct Russian calque; standard Ukrainian is 'за двадцять третя'.",
                ),
                NumeralDistractor(
                    text="двадцять до трьох",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Вислів *двадцять до трьох* є ненормативною калькою з англійської чи польської мови; в українській вживають 'за'.",
                    explanation_en="*двадцять до трьох* is a foreign calque; standard Ukrainian uses preposition 'за'.",
                ),
                NumeralDistractor(
                    text="без двадцяти третя",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Прийменник 'без' не вживається в українських часових конструкціях; правильно — 'за двадцять третя'.",
                    explanation_en="Preposition 'без' is not used in Ukrainian time constructions; standard form is 'за двадцять третя'.",
                ),
            ),
            rule_citation=cit_time,
            rule_summary_ua=ua_time,
            rule_summary_en=en_time,
        ),
        NumeralCard(
            card_id="numeral_70",
            category=NumeralCategory.TIME_EXPRESSIONS_ANTI_CALQUE,
            cefr_level="B1",
            sentence_before="Поглянь на годинник у вітальні: зараз уже",
            sentence_after=", тож перші гості мають ось-ось прийти.",
            correct_answer="десять хвилин по шостій",
            distractors=(
                NumeralDistractor(
                    text="десять хвилин сьомого",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Вислів *десять хвилин сьомого* є російською калькою; правильно говорити: 'десять хвилин по шостій' або 'на сьому'.",
                    explanation_en="*десять хвилин сьомого* is a Russian calque; correct Ukrainian is 'десять хвилин по шостій' or 'на сьому'.",
                ),
                NumeralDistractor(
                    text="в шість десять",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Конструкція *в шість десять* є суржиковим відтворенням російського мовлення; літературна норма — 'по шостій'.",
                    explanation_en="*в шість десять* is a calqued colloquialism; literary standard requires preposition 'по' or 'на'.",
                ),
                NumeralDistractor(
                    text="по шостій десять",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Порушено порядок слів: правильна послідовність компонентів — 'десять хвилин по шостій'.",
                    explanation_en="Word order is distorted: standard syntax is 'десять хвилин по шостій'.",
                ),
            ),
            rule_citation=cit_time,
            rule_summary_ua=ua_time,
            rule_summary_en=en_time,
        ),
        # -------------------------------------------------------------
        # Category 15: APPROXIMATE_NUMERICAL_CONSTRUCTIONS (Cards 71–75)
        # -------------------------------------------------------------
        NumeralCard(
            card_id="numeral_71",
            category=NumeralCategory.APPROXIMATE_NUMERICAL_CONSTRUCTIONS,
            cefr_level="B1",
            sentence_before="В офіційному звіті зазначено, що на площі зібралося",
            sentence_after="громадян, які вимагали реформ.",
            correct_answer="близько ста",
            distractors=(
                NumeralDistractor(
                    text="біля ста",
                    interference_type=NumeralInterferenceType.IMPROPER_APPROXIMATION_PREPOSITION,
                    explanation_ua="У нормативному літературному та офіційно-діловому стилях для позначення приблизної кількості вживають 'близько ста'; прийменник 'біля' в кількісному значенні є розмовним (СУМ-20: розм.).",
                    explanation_en="In standard literary and official register, approximate quantity is expressed with 'близько ста'; preposition 'біля' in quantitative sense is colloquial (SUM-20: розм.).",
                ),
                NumeralDistractor(
                    text="в районі ста",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Канцелярський вислів *в районі ста* є калькою з російської мови; нормативне позначення — 'близько ста'.",
                    explanation_en="Bureaucratic *в районі ста* is a Russian calque; standard expression is 'близько ста'.",
                ),
                NumeralDistractor(
                    text="близько сто",
                    interference_type=NumeralInterferenceType.UNINFLECTED_BASE_FORM,
                    explanation_ua="Прийменник 'близько' вимагає родового відмінка: правильно 'близько ста', а не називний 'сто'.",
                    explanation_en="Preposition 'близько' governs Genitive case: correctly 'близько ста', not base form 'сто'.",
                ),
            ),
            rule_citation=cit_approx,
            rule_summary_ua=ua_approx,
            rule_summary_en=en_approx,
        ),
        NumeralCard(
            card_id="numeral_72",
            category=NumeralCategory.APPROXIMATE_NUMERICAL_CONSTRUCTIONS,
            cefr_level="B1",
            sentence_before="Пасажири чекали на прибуття поїзда",
            sentence_after="на засніженому пероні.",
            correct_answer="хвилин двадцять",
            distractors=(
                NumeralDistractor(
                    text="в районі двадцяти хвилин",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Вислів *в районі двадцяти хвилин* є канцелярською калькою; природна українська норма передає приблизність інверсією: 'хвилин двадцять'.",
                    explanation_en="*в районі двадцяти хвилин* is a bureaucratic calque; authentic Ukrainian uses noun-numeral inversion: 'хвилин двадцять'.",
                ),
                NumeralDistractor(
                    text="десь біля двадцяти хвилин",
                    interference_type=NumeralInterferenceType.IMPROPER_APPROXIMATION_PREPOSITION,
                    explanation_ua="Сполука *десь біля двадцяти хвилин* містить розмовний плеоназм; у літературній мові вживають інверсію ('хвилин двадцять') або нормативне 'близько двадцяти хвилин'.",
                    explanation_en="Phrase *десь біля двадцяти хвилин* is a colloquial pleonasm; literary norm requires inversion ('хвилин двадцять') or standard 'близько двадцяти хвилин'.",
                ),
                NumeralDistractor(
                    text="двадцять близько хвилин",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Порядок слів спотворено: прийменник не може розривати числівник та іменник у такий спосіб.",
                    explanation_en="Word order is corrupted: preposition cannot disrupt numeral and noun in this manner.",
                ),
            ),
            rule_citation=cit_approx,
            rule_summary_ua=ua_approx,
            rule_summary_en=en_approx,
        ),
        NumeralCard(
            card_id="numeral_73",
            category=NumeralCategory.APPROXIMATE_NUMERICAL_CONSTRUCTIONS,
            cefr_level="B2",
            sentence_before="У Всеукраїнській олімпіаді взяли участь",
            sentence_after="талановитих учнів із різних областей.",
            correct_answer="понад двісті",
            distractors=(
                NumeralDistractor(
                    text="вище двохсот",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Вислів *вище двохсот* є калькою з російської мови (*выше двухсот*); в українській вживають 'понад двісті' або 'більше як двісті'.",
                    explanation_en="*вище двохсот* is a Russian calque (*выше двухсот*); standard Ukrainian uses 'понад двісті'.",
                ),
                NumeralDistractor(
                    text="понад двохсот",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Прийменник 'понад' керує знахідним відмінком ('понад двісті'), а не родовим 'двохсот'.",
                    explanation_en="Preposition 'понад' governs Accusative ('понад двісті'), not Genitive 'двохсот'.",
                ),
                NumeralDistractor(
                    text="понад двохста",
                    interference_type=NumeralInterferenceType.RUSSIANISM_GENITIVE_HUNDREDS,
                    explanation_ua="Форма *двохста* є подвійною помилкою: хибне закінчення та неправильний відмінок після прийменника понад.",
                    explanation_en="*двохста* is a double error: corrupted suffix and incorrect case after 'понад'.",
                ),
            ),
            rule_citation=cit_approx,
            rule_summary_ua=ua_approx,
            rule_summary_en=en_approx,
        ),
        NumeralCard(
            card_id="numeral_74",
            category=NumeralCategory.APPROXIMATE_NUMERICAL_CONSTRUCTIONS,
            cefr_level="B2",
            sentence_before="У фондах рідкісної книги залишилося",
            sentence_after="унікальних стародруків XVI століття.",
            correct_answer="з десяток",
            distractors=(
                NumeralDistractor(
                    text="в районі десятка",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Канцелярський зворот *в районі десятка* не відповідає нормам української мови; природна ідіома — 'з десяток'.",
                    explanation_en="Bureaucratic phrase *в районі десятка* violates Ukrainian norms; natural idiom is 'з десяток'.",
                ),
                NumeralDistractor(
                    text="десь біля десяти",
                    interference_type=NumeralInterferenceType.IMPROPER_APPROXIMATION_PREPOSITION,
                    explanation_ua="Сполука *десь біля десяти* є розмовним плеоназмом; у нормативному мовленні вживають питомий вислів 'з десяток' або 'близько десяти'.",
                    explanation_en="Phrase *десь біля десяти* is a colloquial pleonasm; standard literary usage requires 'з десяток' or 'близько десяти'.",
                ),
                NumeralDistractor(
                    text="з десятка",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Прийменник 'з' у значенні приблизності керує знахідним відмінком: правильно 'з десяток', а не *з десятка*.",
                    explanation_en="Preposition 'з' for approximation governs Accusative: correctly 'з десяток', not *з десятка*.",
                ),
            ),
            rule_citation=cit_approx,
            rule_summary_ua=ua_approx,
            rule_summary_en=en_approx,
        ),
        NumeralCard(
            card_id="numeral_75",
            category=NumeralCategory.APPROXIMATE_NUMERICAL_CONSTRUCTIONS,
            cefr_level="B2",
            sentence_before="Реставраційні роботи в старовинному замку триватимуть",
            sentence_after="за попередніми оцінками архітекторів.",
            correct_answer="роки три",
            distractors=(
                NumeralDistractor(
                    text="порядка трьох років",
                    interference_type=NumeralInterferenceType.IMPROPER_APPROXIMATION_PREPOSITION,
                    explanation_ua="Конструкція *порядка трьох років* є грубою калькою з російської мови (*порядка трех лет*); приблизність позначають інверсією ('роки три') або 'близько трьох років'.",
                    explanation_en="The phrase *порядка трьох років* is an ungrammatical Russian calque (*порядка трех лет*); approximation is expressed via inversion ('роки три') or 'близько трьох років'.",
                ),
                NumeralDistractor(
                    text="в районі трьох років",
                    interference_type=NumeralInterferenceType.TIME_EXPRESSION_RUSSIAN_CALQUE,
                    explanation_ua="Суржиковий вислів *в районі трьох років* не вживається в літературній українській мові.",
                    explanation_en="Calqued expression *в районі трьох років* is inadmissible in standard literary Ukrainian.",
                ),
                NumeralDistractor(
                    text="три близько роки",
                    interference_type=NumeralInterferenceType.COMPOUND_GLOBAL_MISAGREEMENT,
                    explanation_ua="Порушено порядок слів: прийменник 'близько' має передувати числівно-іменниковій групі.",
                    explanation_en="Word order is violated: preposition 'близько' must precede the numeral-noun phrase.",
                ),
            ),
            rule_citation=cit_approx,
            rule_summary_ua=ua_approx,
            rule_summary_en=en_approx,
        ),
    ]

    return cards


def find_vesum_db(specified: Path | None = None) -> Path:
    """Finds vesum.db checking specified path, local tree, or primary checkout."""
    if specified and specified.exists() and specified.stat().st_size > 0:
        return specified
    candidates = [
        PROJECT_ROOT / "data" / "vesum.db",
        PROJECT_ROOT.parent.parent.parent / "data" / "vesum.db",
        Path("/home/ops/learn-ukrainian/data/vesum.db"),
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 0:
            return c
    return specified or (PROJECT_ROOT / "data" / "vesum.db")


def verify_deck_with_vesum(cards: list[NumeralCard], vesum_db_path: Path | str | None = None) -> dict[str, Any]:
    """Verify that all target vocabulary and distractors exist in VESUM."""
    import re

    resolved_path = find_vesum_db(Path(vesum_db_path) if vesum_db_path else None)
    conn = sqlite3.connect(str(resolved_path))
    cursor = conn.cursor()

    word_pattern = re.compile(r"^[а-яіїєґА-ЯІЇЄҐ'\-]+$")
    strip_punctuation = ".,!?:;—…\"'«»`()[]"

    all_target_tokens: set[str] = set()
    all_distractor_tokens: set[str] = set()

    for card in cards:
        for w in card.correct_answer.split():
            clean = w.strip(strip_punctuation).lower()
            if clean and word_pattern.match(clean):
                all_target_tokens.add(clean)

        for d in card.distractors:
            for w in d.text.split():
                clean = w.strip(strip_punctuation).lower()
                if clean and word_pattern.match(clean):
                    all_distractor_tokens.add(clean)

    missing_targets: list[str] = []
    for token in sorted(all_target_tokens):
        cursor.execute("SELECT 1 FROM forms_all WHERE word_form = ? LIMIT 1", (token,))
        if not cursor.fetchone():
            missing_targets.append(token)

    invalid_distractors: list[str] = []
    # Distractors can be intentional grammatical errors or valid words in incorrect case
    for token in sorted(all_distractor_tokens):
        cursor.execute("SELECT 1 FROM forms_all WHERE word_form = ? LIMIT 1", (token,))
        if not cursor.fetchone():
            # Check if it's intentionally invalid morphology (e.g. п'ятидесят, шестиста, двохста)
            invalid_distractors.append(token)

    conn.close()

    return {
        "total_cards": len(cards),
        "target_tokens_count": len(all_target_tokens),
        "missing_targets": missing_targets,
        "distractor_tokens_count": len(all_distractor_tokens),
        "unattested_distractor_tokens": invalid_distractors,
        "vesum_verified": len(missing_targets) == 0,
    }


def export_deck(cards: list[NumeralCard], target_path: Path | str) -> dict[str, Any]:
    """Export canonical numeral practice deck to JSON artifact."""
    deck_cards: list[dict[str, Any]] = []

    for card in cards:
        deck_cards.append(
            {
                "card_id": card.card_id,
                "category": card.category.value,
                "cefr_level": card.cefr_level,
                "prompt_sentence": card.prompt_display,
                "blank_target": card.correct_answer,
                "correct_answer": card.correct_answer,
                "options": card.all_options(),
                "distractors": [
                    {
                        "text": d.text,
                        "interference_type": d.interference_type.value,
                        "explanation": {
                            "ua": d.explanation_ua,
                            "en": d.explanation_en,
                        },
                    }
                    for d in card.distractors
                ],
                "pravopys_section": card.rule_citation,
                "rule_summary": {
                    "ua": card.rule_summary_ua,
                    "en": card.rule_summary_en,
                },
            }
        )

    payload = {
        "schema_version": "1.0",
        "title": "Практикум: Глибока механіка числівника (Відмінювання, керування, автентичний час)",
        "card_count": len(deck_cards),
        "categories": [c.value for c in NumeralCategory],
        "cards": deck_cards,
    }

    out_file = Path(target_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Numeral Deep Mechanics Practice Engine")
    parser.add_argument("--verify-vesum", action="store_true", help="Verify targets against VESUM")
    parser.add_argument("--export", action="store_true", help="Export canonical JSON deck")
    parser.add_argument("--output", type=str, default="data/practice/numeral_mechanics_deck.json", help="Output path")
    parser.add_argument("--json", action="store_true", help="Output JSON results to stdout")
    args = parser.parse_args()

    cards = build_canonical_numeral_cards()

    if args.verify_vesum:
        res = verify_deck_with_vesum(cards)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"Cards: {res['total_cards']}, Target tokens: {res['target_tokens_count']}")
            print(f"Missing targets: {len(res['missing_targets'])}")
            if res["missing_targets"]:
                print("Missing:", res["missing_targets"])
            else:
                print("VESUM verification: PASSED (100% target coverage)")
        if res["missing_targets"] or not res.get("vesum_verified", False):
            sys.exit(1)

    if args.export:
        out_path = Path(args.output) if Path(args.output).is_absolute() else PROJECT_ROOT / args.output
        payload = export_deck(cards, out_path)
        print(f"Successfully exported {payload['card_count']} cards to {args.output}")


if __name__ == "__main__":
    main()
