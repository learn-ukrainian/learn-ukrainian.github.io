"""Numeral + Noun Agreement Engine for Ukrainian Language Learning.

Implements Ukrainian Pravopys 2019 (§ 105–107) rules for numeral and noun agreement
across all 5 distinct number tiers:
  Tier 1: Ends in 1, except 11 -> Nominative singular (21 день, 41 книга).
  Tier 2: Ends in 2, 3, 4, except 12–14 -> Nominative plural (2 столи, 3 сестри, 4 вікна).
  Tier 3: 5–20, 30, 50–80, teens 11–14 -> Genitive plural (5 столів, 12 сестер).
  Tier 4: Fractional & Decimal -> Genitive singular (півтора яблука, півтори доби, 2.5 літра).
  Tier 5: Collective numerals -> Genitive plural (двоє хлопців, троє дітей).

Provides a pedagogical distractor taxonomy capturing Russianism calques (e.g. *два журнала* ❌),
teen-tier misapplications (e.g. *чотирнадцять студенти* ❌), compound last-word misagreements
(e.g. *двадцять два днів* ❌), and base-case biases with zero-collision guarantees.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.verification.vesum import get_vesum_connection


class NumeralTier(StrEnum):
    """The five distinct Ukrainian numeral agreement tiers."""

    TIER_1_SINGULAR = "tier_1_ends_in_1"
    TIER_2_PAUCAL = "tier_2_ends_in_2_3_4"
    TIER_3_PLURAL = "tier_3_plural_5_plus"
    TIER_4_FRACTIONAL = "tier_4_fractional"
    TIER_5_COLLECTIVE = "tier_5_collective"


class InterferenceType(StrEnum):
    """Taxonomy of grammatical misconceptions and interference patterns."""

    RUSSIANISM_CALQUE = "russianism_calque"
    TEEN_TIER_VIOLATION = "teen_tier_violation"
    COMPOUND_LAST_WORD_MISAGREEMENT = "compound_last_word_misagreement"
    NOMINATIVE_SINGULAR_BIAS = "nominative_singular_bias"
    COLLECTIVE_CASE_VIOLATION = "collective_case_violation"
    FRACTIONAL_CASE_VIOLATION = "fractional_case_violation"
    OBLIQUE_PLURAL_CONFUSION = "oblique_plural_confusion"
    OVERGENERALIZED_PLURAL = "overgeneralized_plural"


@dataclass(frozen=True)
class NounParadigm:
    """Noun paradigm forms necessary for numeral agreement generation."""

    lemma: str
    gender: str  # 'm', 'f', 'n'
    is_anim: bool
    cefr_level: str
    nom_sg: str
    gen_sg: str
    nom_pl: str
    gen_pl: str
    dat_pl: str | None = None
    loc_pl: str | None = None
    oru_sg: str | None = None


@dataclass(frozen=True)
class NumeralDistractor:
    """A distractor option with pedagogical explanation and error classification."""

    form: str
    interference_type: InterferenceType
    explanation_ua: str
    explanation_en: str


@dataclass
class NumeralAgreementCard:
    """A verified practice challenge card for numeral + noun agreement."""

    id: str
    tier: NumeralTier
    numeral_display: str
    numeral_words: str
    lemma: str
    gender: str
    is_anim: bool
    cefr_level: str
    target_case: str
    target_number: str
    correct_form: str
    options: list[str]
    distractors: list[dict[str, Any]] = field(default_factory=list)
    prompt_ua: str = ""
    prompt_en: str = ""
    pedagogical_rule_ua: str = ""
    pedagogical_rule_en: str = ""
    pravopys_ref: str = "Правопис 2019, § 105–107"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tier": self.tier.value,
            "numeral_display": self.numeral_display,
            "numeral_words": self.numeral_words,
            "lemma": self.lemma,
            "gender": self.gender,
            "is_anim": self.is_anim,
            "cefr_level": self.cefr_level,
            "target_case": self.target_case,
            "target_number": self.target_number,
            "correct_form": self.correct_form,
            "options": self.options,
            "distractors": self.distractors,
            "prompt_ua": self.prompt_ua,
            "prompt_en": self.prompt_en,
            "pedagogical_rule_ua": self.pedagogical_rule_ua,
            "pedagogical_rule_en": self.pedagogical_rule_en,
            "pravopys_ref": self.pravopys_ref,
            # CamelCase aliases for direct TypeScript frontend ingestion
            "numeralDisplay": self.numeral_display,
            "numeralWords": self.numeral_words,
            "isAnim": self.is_anim,
            "cefrLevel": self.cefr_level,
            "targetCase": self.target_case,
            "targetNumber": self.target_number,
            "correctForm": self.correct_form,
            "promptUa": self.prompt_ua,
            "promptEn": self.prompt_en,
            "pedagogicalRuleUa": self.pedagogical_rule_ua,
            "pedagogicalRuleEn": self.pedagogical_rule_en,
            "pravopysRef": self.pravopys_ref,
        }


def classify_numeral_tier(value: int | float | str) -> NumeralTier:
    """Classify any numeral or numeral expression into its agreement tier."""
    if isinstance(value, str):
        val_str = value.strip().lower()
        if val_str in {"півтора", "півтори", "0.5", "1.5", "2.5", "3.5"} or "." in val_str:
            return NumeralTier.TIER_4_FRACTIONAL
        if val_str in {
            "двоє",
            "троє",
            "четверо",
            "п'ятеро",
            "шестеро",
            "семеро",
            "восьмеро",
            "дев'ятеро",
            "десятеро",
        }:
            return NumeralTier.TIER_5_COLLECTIVE
        try:
            val_int = int(val_str)
            return classify_numeral_tier(val_int)
        except ValueError:
            return NumeralTier.TIER_3_PLURAL

    if isinstance(value, float):
        return NumeralTier.TIER_4_FRACTIONAL

    val = abs(int(value))
    last_two = val % 100
    last_one = val % 10
    if 11 <= last_two <= 14:
        return NumeralTier.TIER_3_PLURAL
    if last_one == 1:
        return NumeralTier.TIER_1_SINGULAR
    if last_one in {2, 3, 4}:
        return NumeralTier.TIER_2_PAUCAL
    return NumeralTier.TIER_3_PLURAL


def format_numeral_words(val: int | float | str, gender: str) -> tuple[str, str]:
    """Format numeral display string and words with appropriate gender inflection."""
    if isinstance(val, str):
        s = val.strip().lower()
        if s in {"півтора", "півтори"}:
            actual = "півтори" if gender == "f" else "півтора"
            return actual, actual
        if s in {
            "двоє",
            "троє",
            "четверо",
            "п'ятеро",
            "шестеро",
            "семеро",
            "восьмеро",
            "дев'ятеро",
            "десятеро",
        }:
            return s, s
        try:
            v_int = int(s)
            return format_numeral_words(v_int, gender)
        except ValueError:
            return s, s

    if isinstance(val, float):
        disp = str(val)
        return disp, f"{disp} (дві цілих і п'ять десятих)" if val == 2.5 else disp

    v = int(val)
    disp = str(v)
    last_two = v % 100

    # Number words lookup for 1..99
    units_m = {
        1: "один",
        2: "два",
        3: "три",
        4: "чотири",
        5: "п'ять",
        6: "шість",
        7: "сім",
        8: "вісім",
        9: "дев'ять",
    }
    units_f = {1: "одна", 2: "дві", 3: "три", 4: "чотири"}
    units_n = {1: "одне", 2: "два", 3: "три", 4: "чотири"}

    teens = {
        10: "десять",
        11: "одинадцять",
        12: "дванадцять",
        13: "тринадцять",
        14: "чотирнадцять",
        15: "п'ятнадцять",
        16: "шістнадцять",
        17: "сімнадцять",
        18: "вісімнадцять",
        19: "дев'ятнадцять",
    }
    tens = {
        20: "двадцять",
        30: "тридцять",
        40: "сорок",
        50: "п'ятдесят",
        60: "шістдесят",
        70: "сімдесят",
        80: "вісімдесят",
        90: "дев'яносто",
    }

    if 11 <= last_two <= 19:
        prefix = ""
        if v >= 100:
            prefix = f"{v // 100 * 100} "
        return disp, prefix + teens[last_two]

    unit_dict = units_f if gender == "f" else (units_n if gender == "n" else units_m)

    if v in unit_dict:
        return disp, unit_dict[v]
    if v in tens:
        return disp, tens[v]

    if 21 <= last_two <= 99:
        ten_part = tens[(last_two // 10) * 10]
        unit_val = last_two % 10
        unit_part = unit_dict.get(unit_val, units_m.get(unit_val, ""))
        phrase = f"{ten_part} {unit_part}".strip()
        if v >= 100:
            hundred_prefix = f"{v // 100 * 100} "
            return disp, hundred_prefix + phrase
        return disp, phrase

    return disp, disp


def load_noun_paradigms_from_db(
    vesum_db_path: Path | None = None,
    vocab_db_path: Path | None = None,
    limit: int | None = None,
) -> list[NounParadigm]:
    """Extract clean noun paradigms with verified forms from VESUM and vocabulary.db."""
    if vocab_db_path is None:
        vocab_db_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "vocabulary.db"

    lemmas_info: dict[str, dict[str, Any]] = {}

    if vocab_db_path.is_file():
        conn_vocab = sqlite3.connect(str(vocab_db_path))
        conn_vocab.row_factory = sqlite3.Row
        cur = conn_vocab.cursor()
        rows = cur.execute(
            """
            SELECT uk, gender, level
            FROM lemmas
            WHERE pos = 'noun'
              AND uk NOT LIKE '%-%'
              AND uk GLOB '[а-яіїєґ]*'
            """
        ).fetchall()
        for r in rows:
            lemmas_info[r["uk"]] = {
                "gender": r["gender"] if r["gender"] in {"m", "f", "n"} else "m",
                "level": r["level"] or "A2",
            }
        conn_vocab.close()

    paradigms: list[NounParadigm] = []

    with get_vesum_connection(vesum_db_path) as conn:
        # If no vocab DB or few entries, pull directly from VESUM
        target_lemmas = list(lemmas_info.keys())
        if len(target_lemmas) < 500:
            direct_rows = conn.execute(
                """
                SELECT DISTINCT lemma
                FROM forms
                WHERE pos = 'noun'
                  AND lemma NOT LIKE '%-%'
                  AND lemma GLOB '[а-яіїєґ]*'
                LIMIT 4000
                """
            ).fetchall()
            for dr in direct_rows:
                lem = dr["lemma"]
                if lem not in lemmas_info:
                    lemmas_info[lem] = {"gender": "m", "level": "B1"}
            target_lemmas = list(lemmas_info.keys())

        for lem in target_lemmas:
            forms_rows = conn.execute(
                """
                SELECT word_form, tags
                FROM forms
                WHERE lemma = ?
                """,
                (lem,),
            ).fetchall()

            if not forms_rows:
                continue

            nom_sg = None
            gen_sg = None
            nom_pl = None
            gen_pl = None
            dat_pl = None
            loc_pl = None
            oru_sg = None
            is_anim = False
            detected_gender = lemmas_info[lem]["gender"]

            for fr in forms_rows:
                wf = fr["word_form"]
                tg = fr["tags"]
                if ":rare" in tg:
                    continue
                if "noun:anim:" in tg:
                    is_anim = True
                if ":m:" in tg:
                    detected_gender = "m"
                elif ":f:" in tg:
                    detected_gender = "f"
                elif ":n:" in tg:
                    detected_gender = "n"

                if (":m:v_naz" in tg or ":f:v_naz" in tg or ":n:v_naz" in tg) and nom_sg is None:
                    nom_sg = wf
                elif ":v_rod" in tg and ":p:" not in tg and gen_sg is None:
                    gen_sg = wf
                elif ":p:v_naz" in tg and nom_pl is None:
                    nom_pl = wf
                elif ":p:v_rod" in tg and gen_pl is None:
                    gen_pl = wf
                elif ":p:v_dav" in tg and dat_pl is None:
                    dat_pl = wf
                elif ":p:v_mis" in tg and loc_pl is None:
                    loc_pl = wf
                elif ":v_oru" in tg and ":p:" not in tg and oru_sg is None:
                    oru_sg = wf

            if nom_sg and gen_sg and nom_pl and gen_pl:
                p = NounParadigm(
                    lemma=lem,
                    gender=detected_gender,
                    is_anim=is_anim,
                    cefr_level=lemmas_info[lem].get("level", "A2"),
                    nom_sg=nom_sg,
                    gen_sg=gen_sg,
                    nom_pl=nom_pl,
                    gen_pl=gen_pl,
                    dat_pl=dat_pl,
                    loc_pl=loc_pl,
                    oru_sg=oru_sg,
                )
                paradigms.append(p)
                if limit and len(paradigms) >= limit:
                    break

    return paradigms


def is_dropping_yn_paucal_exception(noun: NounParadigm) -> bool:
    """Detect masculine nouns with suffix -ин that drops in the plural.

    Under Ukrainian academic grammar (Volkova, Maslo 2012, p. 91), nouns such as
    «громадянин», «селянин», «киянин», «львів'янин», «болгарин» take Genitive singular
    after numerals 2, 3, 4 («два громадянина», «три селянина»), rather than Nominative plural.
    """
    if noun.gender != "m":
        return False
    if noun.lemma.endswith("ин") and len(noun.lemma) > 3:
        stem = noun.lemma[:-2]
        if noun.nom_pl.startswith(stem) and not noun.nom_pl[len(stem) :].startswith(("ин", "ін", "їн")):
            return True
    return False


def generate_card_for_tier(
    noun: NounParadigm,
    tier: NumeralTier,
    seed_idx: int = 0,
) -> NumeralAgreementCard | None:
    """Generate a single NumeralAgreementCard for a noun and target tier.

    Ensures zero-collision: 4 distinct options with detailed pedagogical error models.
    """
    rng = random.Random(f"{noun.lemma}_{tier.value}_{seed_idx}")

    # Pick numeral based on tier
    if tier == NumeralTier.TIER_1_SINGULAR:
        numeral_val = rng.choice([1, 21, 31, 41, 51, 101])
        target_case = "називний"
        target_number = "singular"
        correct_form = noun.nom_sg
        pravopys_rule_ua = (
            "Числівник «один» (та складені числівники, що закінчуються на «один») узгоджується "
            "з іменником у роді, числі й відмінку: вимагає називного відмінка однини."
        )
        pravopys_rule_en = "Numerals ending in 'one' (1, 21, 31...) agree in gender and govern Nominative singular."
        pravopys_citation = "Правопис 2019, § 105 (узгодження з числівником «один»)"

    elif tier == NumeralTier.TIER_2_PAUCAL:
        numeral_val = rng.choice([2, 3, 4, 22, 23, 24, 32, 34])
        if is_dropping_yn_paucal_exception(noun):
            target_case = "родовий"
            target_number = "singular"
            correct_form = noun.gen_sg
            pravopys_rule_ua = (
                "Іменники чоловічого роду на -ин, що втрачають цей суфікс у множині "
                "(«громадянин», «селянин», «киянин»), після числівників 2, 3, 4 "
                "вживаються у формі родового відмінка однини: «два громадянина», «три селянина»."
            )
            pravopys_rule_en = (
                "Masculine nouns ending in -ин that lose this suffix in the plural "
                "(e.g. 'громадянин' -> 'громадяни') take Genitive singular after 2, 3, 4: "
                "'два громадянина', 'три селянина'."
            )
            pravopys_citation = "Правопис 2019, § 105; Морфологія української мови (Волкова, Масло 2012, с. 91)"
        else:
            target_case = "називний"
            target_number = "plural"
            correct_form = noun.nom_pl
            pravopys_rule_ua = (
                "Числівники 2, 3, 4 (та складені, що закінчуються на 2, 3, 4, крім 12–14) керують "
                "іменником у називному відмінку множини: «два столи», «три сестри», «чотири вікна»."
            )
            pravopys_rule_en = "Numerals 2, 3, 4 (except 12–14) govern Nominative plural: 'два столи', 'три сестри'."
            pravopys_citation = "Правопис 2019, § 105 (сполучення з числівниками 2, 3, 4)"

    elif tier == NumeralTier.TIER_3_PLURAL:
        # Include teens to test teen-tier violation specifically
        is_teen = rng.choice([True, False])
        numeral_val = rng.choice([11, 12, 13, 14]) if is_teen else rng.choice([5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 50])
        target_case = "родовий"
        target_number = "plural"
        correct_form = noun.gen_pl
        pravopys_rule_ua = (
            "Числівники від 5 до 20, 30, а також числівники другого десятка (11–14) керують "
            "іменником у родовому відмінку множини: «п'ять столів», «дванадцять сестер»."
        )
        pravopys_rule_en = "Numerals 5–20, 30, and teens 11–14 govern Genitive plural: 'п'ять столів'."
        pravopys_citation = "Правопис 2019, § 105 (сполучення з числівниками 5 і більше)"

    elif tier == NumeralTier.TIER_4_FRACTIONAL:
        use_decimal = rng.choice([False, True])
        numeral_val = rng.choice([0.5, 1.5, 2.5]) if use_decimal else ("півтори" if noun.gender == "f" else "півтора")
        target_case = "родовий"
        target_number = "singular"
        correct_form = noun.gen_sg
        pravopys_rule_ua = (
            "Числівники «півтора» (для чол./сер. роду) та «півтори» (для жін. роду), а також "
            "десяткові дроби вимагають родового відмінка однини: «півтора року», «півтори доби», «2.5 літра»."
        )
        pravopys_rule_en = (
            "'Півтора' (m/n), 'півтори' (f), and decimals govern Genitive singular: 'півтора року', '2.5 літра'."
        )
        pravopys_citation = "Правопис 2019, § 107 (сполучення з дробовими числівниками)"

    elif tier == NumeralTier.TIER_5_COLLECTIVE:
        # Collective numerals apply strictly to masculine animates and neuters (Pravopys 2019, § 105)
        if not ((noun.gender == "m" and noun.is_anim) or noun.gender == "n"):
            return None
        numeral_val = rng.choice(["двоє", "троє", "четверо", "п'ятеро"])
        target_case = "родовий"
        target_number = "plural"
        correct_form = noun.gen_pl
        pravopys_rule_ua = (
            "Збірні числівники (двоє, троє, четверо...) сполучаються з іменниками у родовому "
            "відмінку множини: «двоє хлопців», «троє дітей», «четверо вікон»."
        )
        pravopys_rule_en = "Collective numerals (двоє, троє, четверо...) govern Genitive plural: 'двоє хлопців'."
        pravopys_citation = "Правопис 2019, § 105 (сполучення зі збірними числівниками)"
    else:
        return None

    disp, words = format_numeral_words(numeral_val, noun.gender)

    # Assemble candidate distractors with dedicated pedagogical error models
    candidate_distractors: list[NumeralDistractor] = []

    if tier == NumeralTier.TIER_2_PAUCAL:
        if is_dropping_yn_paucal_exception(noun):
            # 1. Overgeneralized Nominative plural distractor (treating like regular nouns)
            candidate_distractors.append(
                NumeralDistractor(
                    form=noun.nom_pl,
                    interference_type=InterferenceType.OVERGENERALIZED_PLURAL,
                    explanation_ua=(
                        f"Форма «{noun.nom_pl}» є називним відмінком множини. Для іменників на -ин, "
                        f"що втрачають цей суфікс у множині, після 2, 3, 4 норма вимагає родового відмінка однини: «{disp} {correct_form}»."
                    ),
                    explanation_en=(
                        f"'{noun.nom_pl}' is Nominative plural. For nouns in -ин losing this suffix in plural, "
                        f"Ukrainian standard requires Genitive singular after 2, 3, 4: '{disp} {correct_form}'."
                    ),
                )
            )
            # 2. Genitive plural (5+ overgeneralization)
            candidate_distractors.append(
                NumeralDistractor(
                    form=noun.gen_pl,
                    interference_type=InterferenceType.OVERGENERALIZED_PLURAL,
                    explanation_ua=(
                        f"Форма «{noun.gen_pl}» — це родовий відмінок множини (вживається після 5+). "
                        f"Після 2, 3, 4 для цього іменника потрібен родовий відмінок однини: «{disp} {correct_form}»."
                    ),
                    explanation_en=(
                        f"'{noun.gen_pl}' is Genitive plural (used after 5+). "
                        f"Numerals 2, 3, 4 require Genitive singular for this noun: '{disp} {correct_form}'."
                    ),
                )
            )
        else:
            # 1. Critical Russianism Calque: Genitive singular (*два журнала* vs *два журнали*)
            candidate_distractors.append(
                NumeralDistractor(
                    form=noun.gen_sg,
                    interference_type=InterferenceType.RUSSIANISM_CALQUE,
                    explanation_ua=(
                        f"У родовому відмінку однини іменники після 2, 3, 4 вживаються в російській мові "
                        f"(«два журнала»). В українській мові після 2, 3, 4 потрібен називний відмінок "
                        f"множини: «{disp} {correct_form}»."
                    ),
                    explanation_en=(
                        f"Using Genitive singular after 2, 3, 4 is a Russianism calque. Ukrainian requires "
                        f"Nominative plural: '{disp} {correct_form}'."
                    ),
                )
            )
            # 2. Genitive plural (5+ overgeneralization or compound misagreement)
            if isinstance(numeral_val, int) and numeral_val > 20:
                candidate_distractors.append(
                    NumeralDistractor(
                        form=noun.gen_pl,
                        interference_type=InterferenceType.COMPOUND_LAST_WORD_MISAGREEMENT,
                        explanation_ua=(
                            f"У складених числівниках іменник узгоджується з останнім словом: оскільки "
                            f"останнє слово «{words.split()[-1]}», потрібен називний відмінок множини "
                            f"(«{disp} {correct_form}»), а не родовий."
                        ),
                        explanation_en=(
                            f"In compound numerals, the noun agrees with the last word. Since the last "
                            f"word is '{words.split()[-1]}', Nominative plural is required."
                        ),
                    )
                )
            else:
                candidate_distractors.append(
                    NumeralDistractor(
                        form=noun.gen_pl,
                        interference_type=InterferenceType.OVERGENERALIZED_PLURAL,
                        explanation_ua=(
                            f"Родовий відмінок множини вживається після числівників 5 і більше. "
                            f"Після 2, 3, 4 потрібен називний відмінок множини: «{disp} {correct_form}»."
                        ),
                        explanation_en=(
                            f"Genitive plural is used after 5+. Numerals 2, 3, and 4 require "
                            f"Nominative plural: '{disp} {correct_form}'."
                        ),
                    )
                )
        # 3. Base Nominative Singular Bias (both regular and dropping -ин)
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.nom_sg,
                interference_type=InterferenceType.NOMINATIVE_SINGULAR_BIAS,
                explanation_ua=(
                    f"Початкова словникова форма (однина) вживається лише з числівником «один». "
                    f"Після {disp} потрібна форма «{correct_form}»."
                ),
                explanation_en=(
                    f"Dictionary singular is only used with 'one'. After {disp}, the required form is '{correct_form}'."
                ),
            )
        )

    elif tier == NumeralTier.TIER_3_PLURAL:
        # If teen 11–14: Critical Teen Tier Violation (treating like 1–4)
        if isinstance(numeral_val, int) and 11 <= (numeral_val % 100) <= 14:
            candidate_distractors.append(
                NumeralDistractor(
                    form=noun.nom_pl,
                    interference_type=InterferenceType.TEEN_TIER_VIOLATION,
                    explanation_ua=(
                        f"Числівники від 11 до 14 закінчуються на -надцять і належать до групи 5–20. "
                        f"Вони керують родовим відмінком множини («{disp} {correct_form}»), а не називним."
                    ),
                    explanation_en=(
                        f"Teens 11–14 end in -надцять and govern Genitive plural ('{disp} {correct_form}'), "
                        f"not Nominative plural."
                    ),
                )
            )
        else:
            candidate_distractors.append(
                NumeralDistractor(
                    form=noun.nom_pl,
                    interference_type=InterferenceType.OVERGENERALIZED_PLURAL,
                    explanation_ua=(
                        f"Після числівників 5 і більше потрібен родовий відмінок множини "
                        f"(«{disp} {correct_form}»), а не називний."
                    ),
                    explanation_en=(
                        f"After numerals 5 and above, Ukrainian requires Genitive plural: '{disp} {correct_form}'."
                    ),
                )
            )
        # Base Nom Sg bias
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.nom_sg,
                interference_type=InterferenceType.NOMINATIVE_SINGULAR_BIAS,
                explanation_ua=(
                    f"Після числівників 5+ потрібен родовий відмінок множини («{correct_form}»), а не однина."
                ),
                explanation_en=(f"After numerals 5+, Genitive plural is required ('{correct_form}'), not singular."),
            )
        )
        # Genitive singular false match
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.gen_sg,
                interference_type=InterferenceType.RUSSIANISM_CALQUE,
                explanation_ua=(f"Потрібна форма множини у родовому відмінку («{correct_form}»), а не однини."),
                explanation_en=(f"Plural form in Genitive case ('{correct_form}') is required, not singular."),
            )
        )

    elif tier == NumeralTier.TIER_1_SINGULAR:
        # Nom Plur (plural bias)
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.nom_pl,
                interference_type=InterferenceType.OVERGENERALIZED_PLURAL,
                explanation_ua=(
                    f"Числівник «{words}» вимагає називного відмінка однини («{disp} {correct_form}»), а не множини."
                ),
                explanation_en=(
                    f"The numeral '{words}' governs Nominative singular ('{disp} {correct_form}'), not plural."
                ),
            )
        )
        # Gen Plur (5+ overgeneralization)
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.gen_pl,
                interference_type=InterferenceType.OVERGENERALIZED_PLURAL,
                explanation_ua=(
                    f"Родовий відмінок множини вживається після 5+, а з «{words}» потрібен називний "
                    f"відмінок однини: «{disp} {correct_form}»."
                ),
                explanation_en=(
                    f"Genitive plural is used after 5+. With '{words}', Nominative singular is "
                    f"required: '{disp} {correct_form}'."
                ),
            )
        )
        # Gen Sg
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.gen_sg,
                interference_type=InterferenceType.RUSSIANISM_CALQUE,
                explanation_ua=(
                    f"Числівник «{words}» вимагає називного відмінка однини («{correct_form}»), а не родового."
                ),
                explanation_en=(f"The numeral '{words}' governs Nominative singular ('{correct_form}'), not Genitive."),
            )
        )

    elif tier == NumeralTier.TIER_4_FRACTIONAL:
        # Gen Plur (plural violation)
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.gen_pl,
                interference_type=InterferenceType.FRACTIONAL_CASE_VIOLATION,
                explanation_ua=(
                    f"Числівники «{disp}» вимагають родового відмінка однини («{disp} {correct_form}»), а не множини."
                ),
                explanation_en=(
                    f"The numeral '{disp}' governs Genitive singular ('{disp} {correct_form}'), not plural."
                ),
            )
        )
        # Nom Sg (base bias)
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.nom_sg,
                interference_type=InterferenceType.NOMINATIVE_SINGULAR_BIAS,
                explanation_ua=(f"Після «{disp}» іменник має стояти у родовому відмінку однини («{correct_form}»)."),
                explanation_en=(f"After '{disp}', the noun must be in Genitive singular ('{correct_form}')."),
            )
        )
        # Nom Plur
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.nom_pl,
                interference_type=InterferenceType.FRACTIONAL_CASE_VIOLATION,
                explanation_ua=(
                    f"Дробові числівники сполучаються з родовим відмінком однини («{correct_form}»), "
                    f"а не з називним множини."
                ),
                explanation_en=(f"Fractions combine with Genitive singular ('{correct_form}'), not Nominative plural."),
            )
        )

    elif tier == NumeralTier.TIER_5_COLLECTIVE:
        # Nom Plur (collective violation)
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.nom_pl,
                interference_type=InterferenceType.COLLECTIVE_CASE_VIOLATION,
                explanation_ua=(
                    f"Збірні числівники («{disp}») керують родовим відмінком множини: "
                    f"«{disp} {correct_form}», а не називним."
                ),
                explanation_en=(
                    f"Collective numerals ('{disp}') govern Genitive plural ('{disp} {correct_form}'), "
                    f"not Nominative plural."
                ),
            )
        )
        # Nom Sg (base bias)
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.nom_sg,
                interference_type=InterferenceType.NOMINATIVE_SINGULAR_BIAS,
                explanation_ua=(
                    f"Збірні числівники позначають сукупність і вимагають родового відмінка множини: «{correct_form}»."
                ),
                explanation_en=(f"Collective numerals denote a group and require Genitive plural: '{correct_form}'."),
            )
        )
        # Gen Sg
        candidate_distractors.append(
            NumeralDistractor(
                form=noun.gen_sg,
                interference_type=InterferenceType.COLLECTIVE_CASE_VIOLATION,
                explanation_ua=(f"Збірні числівники вимагають форми множини («{correct_form}»), а не однини."),
                explanation_en=(f"Collective numerals require plural ('{correct_form}'), not singular."),
            )
        )

    # Deduplicate and guarantee zero collision with correct_form
    selected_distractors: list[NumeralDistractor] = []
    seen_forms: set[str] = {correct_form}

    for cd in candidate_distractors:
        if cd.form not in seen_forms and len(selected_distractors) < 3:
            seen_forms.add(cd.form)
            selected_distractors.append(cd)

    # Fallbacks from secondary paradigm slots if any collisions occurred
    fallback_pool = [
        (noun.dat_pl, "давальний відмінок множини"),
        (noun.loc_pl, "місцевий відмінок множини"),
        (noun.oru_sg, "орудний відмінок однини"),
    ]

    for fb_form, case_name in fallback_pool:
        if len(selected_distractors) >= 3:
            break
        if fb_form and fb_form not in seen_forms:
            seen_forms.add(fb_form)
            selected_distractors.append(
                NumeralDistractor(
                    form=fb_form,
                    interference_type=InterferenceType.OBLIQUE_PLURAL_CONFUSION,
                    explanation_ua=(
                        f"Форма «{fb_form}» ({case_name}) не вживається в цій позиції; "
                        f"правильна форма: «{correct_form}»."
                    ),
                    explanation_en=(f"The form '{fb_form}' is incorrect here; the required form is '{correct_form}'."),
                )
            )

    # Strict zero-collision guarantee: must have exactly 3 distinct distractors
    if len(selected_distractors) < 3:
        return None

    # Assemble 4 options and shuffle with fixed seed
    options = [correct_form] + [d.form for d in selected_distractors]
    if len(set(options)) != 4:
        return None

    rng.shuffle(options)

    card_id = f"numeral-{tier.value}-{noun.lemma}-{disp}".replace("'", "").replace(" ", "_")
    prompt_ua = f"{disp} ({noun.lemma}) ➔ {disp} …"
    prompt_en = f"Choose the correct noun form for: {disp} ({noun.lemma})"

    return NumeralAgreementCard(
        id=card_id,
        tier=tier,
        numeral_display=disp,
        numeral_words=words,
        lemma=noun.lemma,
        gender=noun.gender,
        is_anim=noun.is_anim,
        cefr_level=noun.cefr_level,
        target_case=target_case,
        target_number=target_number,
        correct_form=correct_form,
        options=options,
        distractors=[
            {
                "form": d.form,
                "interference_type": d.interference_type.value,
                "explanation_ua": d.explanation_ua,
                "explanation_en": d.explanation_en,
                # CamelCase aliases for TypeScript frontend ingestion
                "interferenceType": d.interference_type.value,
                "explanationUa": d.explanation_ua,
                "explanationEn": d.explanation_en,
            }
            for d in selected_distractors
        ],
        prompt_ua=prompt_ua,
        prompt_en=prompt_en,
        pedagogical_rule_ua=pravopys_rule_ua,
        pedagogical_rule_en=pravopys_rule_en,
        pravopys_ref=pravopys_citation,
    )


def validate_numeral_card(card: NumeralAgreementCard) -> list[str]:
    """Strictly validate a numeral card for correctness and zero collisions."""
    errors: list[str] = []
    if len(card.options) != 4:
        errors.append(f"Card {card.id} has {len(card.options)} options, expected 4.")
    if len(set(card.options)) != 4:
        errors.append(f"Collision detected in card {card.id}: options {card.options} contain duplicates.")
    if card.correct_form not in card.options:
        errors.append(f"Correct form '{card.correct_form}' not in options {card.options}.")
    if len(card.distractors) != 3:
        errors.append(f"Card {card.id} has {len(card.distractors)} distractors, expected 3.")
    for d in card.distractors:
        if d["form"] == card.correct_form:
            errors.append(f"Distractor form matches correct form '{card.correct_form}'.")
        if not d.get("explanation_ua") or not d.get("explanation_en"):
            errors.append(f"Missing explanation in distractor {d['form']}.")
        if not d.get("interference_type"):
            errors.append(f"Missing interference_type in distractor {d['form']}.")
    return errors


def generate_deck_across_all_tiers(
    paradigms: list[NounParadigm],
    target_count: int = 1200,
) -> list[NumeralAgreementCard]:
    """Generate a balanced deck across all 5 tiers covering >= 1,000 noun items."""
    cards: list[NumeralAgreementCard] = []
    tiers = [
        NumeralTier.TIER_1_SINGULAR,
        NumeralTier.TIER_2_PAUCAL,
        NumeralTier.TIER_3_PLURAL,
        NumeralTier.TIER_4_FRACTIONAL,
        NumeralTier.TIER_5_COLLECTIVE,
    ]

    for idx, p in enumerate(paradigms):
        tier = tiers[idx % len(tiers)]
        card = generate_card_for_tier(p, tier, seed_idx=idx)
        if card:
            errs = validate_numeral_card(card)
            if not errs:
                cards.append(card)
        if len(cards) >= target_count:
            break

    return cards


def main() -> None:
    """CLI entrypoint for numeral agreement engine."""
    parser = argparse.ArgumentParser(description="Ukrainian Numeral + Noun Agreement Engine")
    parser.add_argument("--limit", type=int, default=1500, help="Maximum nouns to inspect")
    parser.add_argument("--target-cards", type=int, default=1200, help="Target cards count")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    parser.add_argument("--check-collisions", action="store_true", help="Perform collision audit")
    args = parser.parse_args()

    print(f"Loading noun paradigms (limit={args.limit})...")
    paradigms = load_noun_paradigms_from_db(limit=args.limit)
    print(f"Loaded {len(paradigms)} verified noun paradigms.")

    cards = generate_deck_across_all_tiers(paradigms, target_count=args.target_cards)
    print(f"Generated {len(cards)} numeral agreement cards.")

    # Tier breakdown
    tier_counts: dict[str, int] = {}
    for c in cards:
        tier_counts[c.tier.value] = tier_counts.get(c.tier.value, 0) + 1

    print("\n--- Tier Distribution ---")
    for t, cnt in tier_counts.items():
        print(f"  {t}: {cnt} cards")

    # Collision & error audit
    total_errors = 0
    for c in cards:
        errs = validate_numeral_card(c)
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
