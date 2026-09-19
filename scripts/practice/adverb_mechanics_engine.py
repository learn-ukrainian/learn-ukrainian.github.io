#!/usr/bin/env python3
"""Adverb Deep Mechanics Practice Engine (Прислівник).

Epic #8241: 10 Parts of Speech Deep Mechanics & Practice Hub Re-architecture.
Issue #8274: Adverb Deep Mechanics Practice Engine (Phase 7).

Categories (15 categories x 5 cards = 75 canonical practice cards):
 1. adverb_semantic_manner_action         - Manner & Qualitative (як? яким способом?) [Правопис 2019 § 41, п. 1]
 2. adverb_semantic_time                  - Time (коли? відколи? доки?) [Правопис 2019 § 41, п. 1]
 3. adverb_semantic_place_direction       - Place & Direction (де? куди? звідки?) [Правопис 2019 § 41, п. 1]
 4. adverb_semantic_measure_degree        - Measure & Degree (скільки? наскільки? якою мірою?) [Правопис 2019 § 41, п. 1]
 5. adverb_semantic_cause_purpose         - Cause & Purpose (чому? навіщо? з якої причини?) [Правопис 2019 § 41, п. 1]
 6. adverb_spelling_prefix_po             - Hyphenated spelling: prefix по- [Правопис 2019 § 41, п. 3, 1)]
 7. adverb_spelling_particles_hyphen      - Hyphenated spelling: particles будь-, -небудь, казна-, хтозна-, бозна-, -таки [Правопис 2019 § 41, п. 3, 2)]
 8. adverb_spelling_reduplication         - Hyphenated spelling: duplicated roots & synonymous pairs [Правопис 2019 § 41, п. 3, 3)]
 9. adverb_spelling_together_fused        - One-word fused adverbs from prepositional combinations [Правопис 2019 § 41, п. 1]
10. adverb_homophone_napamyat_vden_dodomu - Homophone discrimination 1 (напам'ять vs на пам'ять, вдень vs в день, додому vs до дому) [Правопис 2019 § 41, пп. 1, 2]
11. adverb_homophone_zgory_nazustrich_ubik- Homophone discrimination 2 (згори vs з гори, назустріч vs на зустріч, убік vs у бік) [Правопис 2019 § 41, пп. 1, 2]
12. adverb_spelling_separate              - Separate spelling: adverbial phrases [Правопис 2019 § 41, п. 2: на жаль, до речі, без сумніву, день у день]
13. adverb_comparison_synthetic           - Comparative degree: synthetic & suppletive forms [Правопис 2019 § 20; Академічна граматика]
14. adverb_comparison_superlative         - Superlative degree: prefix най- and intensifiers як-, що- [Правопис 2019 § 20; Академічна граматика]
15. adverb_anti_calque                    - Anti-calque adverbials & speech culture [Антоненко-Давидович; СУМ-20]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AdverbCategory(StrEnum):
    MANNER_ACTION = "adverb_semantic_manner_action"
    TIME = "adverb_semantic_time"
    PLACE_DIRECTION = "adverb_semantic_place_direction"
    MEASURE_DEGREE = "adverb_semantic_measure_degree"
    CAUSE_PURPOSE = "adverb_semantic_cause_purpose"
    PREFIX_PO_HYPHEN = "adverb_spelling_prefix_po"
    PARTICLES_HYPHEN = "adverb_spelling_particles_hyphen"
    REDUPLICATION = "adverb_spelling_reduplication"
    TOGETHER_FUSED = "adverb_spelling_together_fused"
    HOMOPHONE_DISCRIMINATION_1 = "adverb_homophone_napamyat_vden_dodomu"
    HOMOPHONE_DISCRIMINATION_2 = "adverb_homophone_zgory_nazustrich_ubik"
    SEPARATE_PHRASES = "adverb_spelling_separate"
    COMPARISON_SYNTHETIC = "adverb_comparison_synthetic"
    COMPARISON_SUPERLATIVE = "adverb_comparison_superlative"
    ANTI_CALQUE = "adverb_anti_calque"


class AdverbInterferenceKey(StrEnum):
    HYPHEN_OMISSION = "HYPHEN_OMISSION"
    HYPHEN_SEPARATION = "HYPHEN_SEPARATION"
    UNWARRANTED_HYPHEN = "UNWARRANTED_HYPHEN"
    UNWARRANTED_FUSION = "UNWARRANTED_FUSION"
    UNWARRANTED_SEPARATION = "UNWARRANTED_SEPARATION"
    HOMOPHONE_NOUN_PREP_CONFUSION = "HOMOPHONE_NOUN_PREP_CONFUSION"
    HOMOPHONE_ADVERB_CONFUSION = "HOMOPHONE_ADVERB_CONFUSION"
    COMPARATIVE_COMPOUND_CALQUE = "COMPARATIVE_COMPOUND_CALQUE"
    COMPARATIVE_RUSSIAN_SUFFIX = "COMPARATIVE_RUSSIAN_SUFFIX"
    SUPERLATIVE_CALQUE_SAMYI = "SUPERLATIVE_CALQUE_SAMYI"
    SUPERLATIVE_HYPHEN_ERROR = "SUPERLATIVE_HYPHEN_ERROR"
    RUSSIANISM_CALQUE = "RUSSIANISM_CALQUE"
    CORRUPTED_ADVERB_FORM = "CORRUPTED_ADVERB_FORM"
    INCORRECT_QUESTION_CATEGORY = "INCORRECT_QUESTION_CATEGORY"


@dataclass(frozen=True)
class AdverbDistractor:
    text: str
    interference_key: AdverbInterferenceKey
    explanation_ua: str
    explanation_en: str


@dataclass(frozen=True)
class AdverbCard:
    card_id: str
    category: AdverbCategory
    prompt: str
    target_token: str
    correct_answer: str
    distractors: tuple[AdverbDistractor, AdverbDistractor, AdverbDistractor]
    rule_citation: str
    rule_summary_ua: str
    rule_summary_en: str

    def all_options(self) -> list[str]:
        raw_options = [self.correct_answer] + [d.text for d in self.distractors]
        hash_seed = int(hashlib.sha256(self.card_id.encode("utf-8")).hexdigest(), 16)
        positions = [0, 1, 2, 3]
        shift = hash_seed % 4
        shuffled_indices = positions[shift:] + positions[:shift]
        if (hash_seed // 4) % 2 == 1:
            shuffled_indices[1], shuffled_indices[2] = shuffled_indices[2], shuffled_indices[1]
        return [raw_options[i] for i in shuffled_indices]


def resolve_manner_action_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 1; СУМ-20"
    ua = "Прислівники способу дії відповідають на питання 'як?', 'яким способом?' і характеризують якість або спосіб протікання дії (напам'ять, вголос, пішки, пошепки, навпомацки). Більшість таких прислівників, утворених від прийменників та іменників, пишуться разом per § 41, п. 1."
    en = "Adverbs of manner answer 'how?' or 'in what manner?' and describe how an action is performed (напам'ять, вголос, пішки, пошепки, навпомацки). Most formed by fusion of prepositions and nominal stems are spelled as one word per § 41, p. 1."
    return cit, ua, en


def resolve_time_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 1; СУМ-20"
    ua = "Прислівники часу відповідають на питання 'коли?', 'відколи?', 'доки?' (вдень, влітку, щодня, зранку, допізна). Складні прислівники з префіксами в-, з-, до- та часткою що- пишуться разом per § 41, п. 1."
    en = "Adverbs of time answer 'when?', 'since when?', 'until when?' (вдень, влітку, щодня, зранку, допізна). Compound adverbs formed with prefixes в-, з-, до- and particle що- are spelled as one word per § 41, p. 1."
    return cit, ua, en


def resolve_place_direction_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 1; СУМ-20"
    ua = "Прислівники місця та напрямку відповідають на питання 'де?', 'куди?', 'звідки?' (додому, вгору, донизу, вперед, ззаду). Вони пишуться разом per § 41, п. 1, коли утворені злиттям прийменників з іменниковими основами без пояснювальних слів."
    en = "Adverbs of place and direction answer 'where?', 'where to?', 'where from?' (додому, вгору, донизу, вперед, ззаду). They are spelled as a single word per § 41, p. 1 when fused from prepositions and nominal stems without dependents."
    return cit, ua, en


def resolve_measure_degree_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 1; СУМ-20"
    ua = "Прислівники міри й ступеня відповідають на питання 'скільки?', 'наскільки?', 'якою мірою?' (наполовину, дощенту, зовсім, набагато, вкрай). Пишуться разом за правилом злиття прийменників з іменниками, числівниками або займенниками per § 41, п. 1."
    en = "Adverbs of measure and degree answer 'how much?', 'to what extent?' (наполовину, дощенту, зовсім, набагато, вкрай). They are written as one word per the fusion rule of prepositions with nominal bases per § 41, p. 1."
    return cit, ua, en


def resolve_cause_purpose_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 1; СУМ-20"
    ua = "Прислівники причини й мети відповідають на питання 'чому?', 'з якої причини?', 'навіщо?', 'з якою метою?' (зопалу, згарячу, навмисне, напоказ, наперекір). Зрощені префіксально-суфіксальні форми пишуться разом per § 41, п. 1."
    en = "Adverbs of cause and purpose answer 'why?', 'for what reason?', 'for what purpose?' (зопалу, згарячу, навмисне, напоказ, наперекір). Fused prefixal-suffixal derivatives are written as one word per § 41, p. 1."
    return cit, ua, en


def resolve_prefix_po_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 3, 1); СУМ-20"
    ua = "Прислівники з префіксом по-, утворені від прикметників і займенників із суфіксами -ому, -ему, -и, -ськи, -цьки, пишуться через дефіс: по-українськи, по-новому, по-батьківськи, по-моєму, по-дитячому per § 41, п. 3, 1)."
    en = "Adverbs with prefix по- formed from adjectives and pronouns with suffixes -ому, -ему, -и, -ськи, -цьки are hyphenated per § 41, p. 3, 1): по-українськи, по-новому, по-батьківськи, по-моєму, по-дитячому."
    return cit, ua, en


def resolve_particles_hyphen_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 3, 3); СУМ-20"
    ua = "Прислівники з частками будь-, -небудь, казна-, хтозна-, бозна-, -таки, -то пишуться через дефіс per § 41, п. 3, 3): будь-де, як-небудь, хтозна-як, казна-коли, бозна-як, так-таки."
    en = "Adverbs with particles будь-, -небудь, казна-, хтозна-, бозна-, -таки, -то are hyphenated per § 41, p. 3, 3): будь-де, як-небудь, хтозна-як, казна-коли, бозна-як, так-таки."
    return cit, ua, en


def resolve_reduplication_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 3, 5); СУМ-20"
    ua = "Прислівники, утворені повторенням того самого слова, поєднанням синонімів або антонімів, а також парних слів з прийменником між ними, пишуться через дефіс per § 41, п. 3, 5): віч-на-віч, пліч-о-пліч, тишком-нишком, ледве-ледве, давним-давно."
    en = "Adverbs formed by reduplication of identical words, synonymous pairs, or identical roots connected by a preposition are hyphenated per § 41, p. 3, 5): віч-на-віч, пліч-о-пліч, тишком-нишком, ледве-ледве, давним-давно."
    return cit, ua, en


def resolve_together_fused_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 1; СУМ-20"
    ua = "Складні прислівники, утворені злиттям прийменників з іменниками, числівниками чи займенниками, коли вони втратили значення окремих частин мови, пишуться разом per § 41, п. 1: спочатку, вперше, спідлоба, навшпиньки, насторожі."
    en = "Compound adverbs formed by complete fusion of prepositions with nominal bases, where individual syntactic independence is lost, are spelled as one word per § 41, p. 1: спочатку, вперше, спідлоба, навшпиньки, насторожі."
    return cit, ua, en


def resolve_homophone_1_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, пп. 1, 2; СУМ-20"
    ua = "Слід чітко розрізняти прислівники, що пишуться разом (§ 41, п. 1), та омонімічні іменникові сполуки з прийменниками, що пишуться окремо (§ 41, п. 2): вивчити напам'ять (як?) vs подарувати на пам'ять (на що? на пам'ять про подію); спати вдень (коли?) vs у цей пам'ятний день (у що?); іти додому (куди?) vs підійти до дому лісника (до якої споруди?)."
    en = "Distinguish fused adverbs (spelled as one word per § 41, p. 1) from homophonous prepositional phrases with nouns (spelled separately per § 41, p. 2): вивчити напам'ять (manner) vs на пам'ять (as a keepsake); спати вдень (time) vs в день народження (on the day of); іти додому (direction) vs підійти до дому (to the house of)."
    return cit, ua, en


def resolve_homophone_2_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, пп. 1, 2; СУМ-20"
    ua = "Прислівники напрямку пишуться разом per § 41, п. 1 (згори вниз, бігти назустріч, відійти вбік), тоді як сполуки прийменника з іменником за наявності залежних слів пишуться окремо per § 41, п. 2 (спускатися з високої гори, вирушити на зустріч із друзями, поглянути у правий бік вулиці)."
    en = "Directional adverbs are written as one word per § 41, p. 1 (згори, назустріч, вбік), whereas preposition + noun phrases with dependent words are written separately per § 41, p. 2 (з гори, на зустріч, у бік)."
    return cit, ua, en


def resolve_separate_phrases_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 2; СУМ-20"
    ua = "Прислівникові сполучення, утворені з прийменника та іменника, що зберігають відмінкову самостійність, пишуться окремо per § 41, п. 2: на жаль, до речі, без сумніву, день у день, до побачення. Написання їх разом (*нажаль, *доречі, *допобачення) є грубою помилкою."
    en = "Adverbial expressions consisting of a preposition and a noun that retain grammatical independence are spelled separately per § 41, p. 2: на жаль, до речі, без сумніву, день у день, до побачення. Writing them as single words (*нажаль, *доречі) is an error."
    return cit, ua, en


def resolve_comparison_synthetic_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 20; Академічна граматика; СУМ-20"
    ua = "Вищий ступінь порівняння якісних прислівників на -о, -е утворюється за допомогою суфіксів -ше, -іше (швидко -> швидше, тепло -> тепліше, глибоко -> глибше) з чергуванням приголосних per § 20 або суплетивно (добре/гарно -> краще, погано -> гірше). Змішування слів 'більш' із синтетичною формою (*більш краще) є неприпустимим."
    en = "The comparative degree of qualitative adverbs ending in -о, -е is formed synthetically with suffixes -ше, -іше (швидше, тепліше, глибше) with consonant changes per § 20 or suppletively (краще, гірше). Mixing 'більш' with synthetic forms (*більш краще) is grammatically invalid."
    return cit, ua, en


def resolve_comparison_superlative_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 20; Академічна граматика; СУМ-20"
    ua = "Найвищий ступінь порівняння утворюється додаванням префікса най- до форми вищого ступеня (найкраще, найвище) per § 20 та за нормами академічної граматики. Значення можна посилити префіксами як-, що-, які пишуться разом: якнайшвидше, щонайдовше. Використання частки 'самий' (*самий краще) є російською калькою."
    en = "The superlative degree is formed by prefixing най- to the comparative form (найкраще, найвище) per § 20 and academic grammar. Intensifying prefixes як-, що- are attached as single words (якнайшвидше, щонайдовше). Using 'самий' (*самий краще) is an ungrammatical calque."
    return cit, ua, en


def resolve_anti_calque_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019; Антоненко-Давидович «Як ми говоримо»; СУМ-20"
    ua = "Слід уникати калькованих канцеляризмів та суржику: вживайте 'насамперед / передусім' замість 'в першу чергу'; 'навряд чи' замість 'вряд ли'; 'переважно / здебільшого' замість 'по більшій мірі'; 'принаймні' замість 'по крайній мірі'; 'у крайньому разі' замість 'в крайньому випадку'."
    en = "Avoid Russian bureaucratic calques and Surzhyk: use 'насамперед' instead of *в першу чергу*; 'навряд чи' instead of *вряд ли*; 'переважно' instead of *по більшій мірі*; 'принаймні' instead of *по крайній мірі*; 'у крайньому разі' instead of *в крайньому випадку*."
    return cit, ua, en


def build_canonical_adverb_cards() -> list[AdverbCard]:
    cards: list[AdverbCard] = []

    # Category 1: Manner & Qualitative
    cit_man, ua_man, en_man = resolve_manner_action_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_01",
                category=AdverbCategory.MANNER_ACTION,
                prompt="Студент уважно прочитав вірш і вирішив вивчити його _______ перед іспитом.",
                target_token="напам'ять",
                correct_answer="напам'ять",
                distractors=(
                    AdverbDistractor(
                        text="на пам'ять",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«На пам'ять» окремо є іменником з прийменником (наприклад, «подарувати на добру пам'ять»), тоді як спосіб дії «вивчити як?» вимагає прислівника, що пишеться разом: «напам'ять» per § 41, п. 1.",
                        explanation_en="'На пам'ять' separately is a noun with a preposition (e.g. as a souvenir), whereas the adverb of manner 'how to memorize?' is written as one word: 'напам'ять' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="по пам'яті",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «по пам'яті» є калькою з російської («по памяти»); природно сказати «напам'ять» або «з пам'яті».",
                        explanation_en="The phrase 'по пам'яті' is a Russian calque; authentic Ukrainian uses 'напам'ять' or 'з пам'яті'.",
                    ),
                    AdverbDistractor(
                        text="на-пам'ять",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівники, утворені злиттям прийменника з іменником, пишуться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverbs formed by fusing a preposition with a noun are written as one word without a hyphen per § 41, p. 1.",
                    ),
                ),
                rule_citation=cit_man,
                rule_summary_ua=ua_man,
                rule_summary_en=en_man,
            ),
            AdverbCard(
                card_id="adverb_card_02",
                category=AdverbCategory.MANNER_ACTION,
                prompt="Учитель попросив школяра читати текст _______, щоб усі добре чули.",
                target_token="вголос",
                correct_answer="вголос",
                distractors=(
                    AdverbDistractor(
                        text="в голос",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="«Вголос» є складним прислівником способу дії і пишеться разом per § 41, п. 1; окремо «в голос» може бути лише рідкісною сполукою прийменника та іменника.",
                        explanation_en="'Вголос' is a compound adverb of manner written as one word per § 41, p. 1; separately 'в голос' is only an unusual preposition + noun sequence.",
                    ),
                    AdverbDistractor(
                        text="по голосу",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="«По голосу» означає розпізнавання за ознакою (впізнати по голосу), а не спосіб читання (як? голосно/вголос).",
                        explanation_en="'По голосу' signifies recognition by timbre (recognize by voice), not the manner of reading aloud.",
                    ),
                    AdverbDistractor(
                        text="в-голос",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Складний прислівник «вголос» пишеться разом per § 41, п. 1, дефіс не вживається.",
                        explanation_en="Compound adverb 'вголос' is written as one word per § 41, p. 1; no hyphen is used.",
                    ),
                ),
                rule_citation=cit_man,
                rule_summary_ua=ua_man,
                rule_summary_en=en_man,
            ),
            AdverbCard(
                card_id="adverb_card_03",
                category=AdverbCategory.MANNER_ACTION,
                prompt="Погода була чудова, тому ми вирішили йти до парку _______.",
                target_token="пішки",
                correct_answer="пішки",
                distractors=(
                    AdverbDistractor(
                        text="пішком",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Форма «пішком» є ненормативною або русизмом («пешком»); нормативне українське слово — «пішки».",
                        explanation_en="Form 'пішком' is non-standard Russian interference ('пешком'); standard Ukrainian is 'пішки'.",
                    ),
                    AdverbDistractor(
                        text="піши",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Такої форми в українській мові немає; правильна нормативна форма прислівника — «пішки».",
                        explanation_en="Such a form does not exist in standard Ukrainian; the correct adverb is 'пішки'.",
                    ),
                    AdverbDistractor(
                        text="на пішки",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник «пішки» вживається самостійно без зайвих прийменників.",
                        explanation_en="The adverb 'пішки' is used independently without unnecessary prepositions.",
                    ),
                ),
                rule_citation=cit_man,
                rule_summary_ua=ua_man,
                rule_summary_en=en_man,
            ),
            AdverbCard(
                card_id="adverb_card_04",
                category=AdverbCategory.MANNER_ACTION,
                prompt="У бібліотеці потрібно дотримуватися тиші й розмовляти лише _______.",
                target_token="пошепки",
                correct_answer="пошепки",
                distractors=(
                    AdverbDistractor(
                        text="по шепки",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="«Пошепки» — цілісний прислівник способу дії, утворений від префікса та основи; пишеться разом per § 41, п. 1.",
                        explanation_en="'Пошепки' is a fused adverb of manner written as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="по-шепки",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Префікс по- пишеться через дефіс лише перед суфіксами -ому, -ему, -и, -ськи, -цьки (по-українськи); у слові «пошепки» дефіс не ставиться.",
                        explanation_en="Prefix по- is hyphenated only with suffixes -ому, -ему, -и, -ськи, -цьки; 'пошепки' takes no hyphen.",
                    ),
                    AdverbDistractor(
                        text="пошепком",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Нормативною літературною формою прислівника способу дії є «пошепки».",
                        explanation_en="The normative literary form for the adverb of manner is 'пошепки'.",
                    ),
                ),
                rule_citation=cit_man,
                rule_summary_ua=ua_man,
                rule_summary_en=en_man,
            ),
            AdverbCard(
                card_id="adverb_card_05",
                category=AdverbCategory.MANNER_ACTION,
                prompt="Коли згасло світло в кімнаті, хлопчик шукав ліхтарик _______.",
                target_token="навпомацки",
                correct_answer="навпомацки",
                distractors=(
                    AdverbDistractor(
                        text="на впомацки",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник «навпомацки» зрощений з кількох морфем і пишеться строго разом per § 41, п. 1.",
                        explanation_en="Adverb 'навпомацки' is fused from multiple morphemes and is written strictly as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-впомацки",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="У слові «навпомацки» немає підстав для написання через дефіс; воно пишеться разом per § 41, п. 1.",
                        explanation_en="There is no grammatical basis for hyphenating 'навпомацки'; it is written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="навпомацьки",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Слово «навпомацки» закінчується твердим суфіксом -ки без м'якого знака.",
                        explanation_en="Word 'навпомацки' ends with hard suffix -ки without a soft sign.",
                    ),
                ),
                rule_citation=cit_man,
                rule_summary_ua=ua_man,
                rule_summary_en=en_man,
            ),
        ]
    )

    # Category 2: Time
    cit_time, ua_time, en_time = resolve_time_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_06",
                category=AdverbCategory.TIME,
                prompt="Нічні хижаки зазвичай сплять _______, а полюють після заходу сонця.",
                target_token="вдень",
                correct_answer="вдень",
                distractors=(
                    AdverbDistractor(
                        text="в день",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«В день» окремо пишеться лише коли є залежне слово (наприклад, «в день свята»), а часовий прислівник «коли? вдень» пишеться разом per § 41, п. 1.",
                        explanation_en="'В день' separately is used only with dependent words (e.g. on the day of the holiday), while time adverb 'when? вдень' is written as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в-день",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівники часу, утворені злиттям прийменника з іменником, пишуться разом без дефіса per § 41, п. 1.",
                        explanation_en="Time adverbs formed by preposition + noun fusion are written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="по-вдень",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Форма «по-вдень» є штучною та неіснуючою в українській мові; правильний часовий прислівник — «вдень» per § 41, п. 1.",
                        explanation_en="The form 'по-вдень' is artificial and non-existent in Ukrainian; the correct temporal adverb is 'вдень' per § 41, p. 1.",
                    ),
                ),
                rule_citation=cit_time,
                rule_summary_ua=ua_time,
                rule_summary_en=en_time,
            ),
            AdverbCard(
                card_id="adverb_card_07",
                category=AdverbCategory.TIME,
                prompt="Школярі мають три місяці канікул _______, коли надворі тепло й сонячно.",
                target_token="влітку",
                correct_answer="влітку",
                distractors=(
                    AdverbDistractor(
                        text="в літку",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="«Влітку» — часовий прислівник (відповідає на питання «коли?»), утворений від прийменника та іменника; пишеться разом per § 41, п. 1.",
                        explanation_en="'Влітку' is a temporal adverb (answering 'when?') formed from preposition + noun; written as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в-літку",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="У слові «влітку» дефіс не пишеться; злиття прийменника з іменником відбувається разом per § 41, п. 1.",
                        explanation_en="Hyphen is not used in 'влітку'; fusion of preposition and noun is written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="по літньому",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="«По-літньому» означає спосіб дії або якість (як? одягнений по-літньому), а не час (коли? влітку).",
                        explanation_en="'По-літньому' denotes manner or quality (how? dressed like in summer), not time (when? in summer).",
                    ),
                ),
                rule_citation=cit_time,
                rule_summary_ua=ua_time,
                rule_summary_en=en_time,
            ),
            AdverbCard(
                card_id="adverb_card_08",
                category=AdverbCategory.TIME,
                prompt="Спортсмен тренується _______, не пропускаючи жодного ранкового заняття.",
                target_token="щодня",
                correct_answer="щодня",
                distractors=(
                    AdverbDistractor(
                        text="що дня",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник «щодня» утворений за допомогою частки що- та іменникової основи; пишеться разом per § 41, п. 1.",
                        explanation_en="Adverb 'щодня' is formed with particle що- and nominal base; written as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="що-дня",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Частка що- у складі часових прислівників (щодня, щомісяця, щогодини) пишеться разом, без дефіса per § 41, п. 1.",
                        explanation_en="Particle що- in temporal adverbs (щодня, щомісяця) is attached without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="по-щодня",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Префікс по- з часовим прислівником не вживається; нормативна форма — «щодня».",
                        explanation_en="Prefix по- is not used with temporal adverbs; standard form is 'щодня'.",
                    ),
                ),
                rule_citation=cit_time,
                rule_summary_ua=ua_time,
                rule_summary_en=en_time,
            ),
            AdverbCard(
                card_id="adverb_card_09",
                category=AdverbCategory.TIME,
                prompt="Ми прокинулися рано _______, щоб встигнути на перший потяг.",
                target_token="зранку",
                correct_answer="зранку",
                distractors=(
                    AdverbDistractor(
                        text="з ранку",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник часу «зранку» пишеться разом per § 41, п. 1; окремо «з ранку» пишеться лише в парній конструкції «з ранку до вечора».",
                        explanation_en="Temporal adverb 'зранку' is written together per § 41, p. 1; separately 'з ранку' appears only in paired phrase 'з ранку до вечора'.",
                    ),
                    AdverbDistractor(
                        text="з-ранку",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прийменник з- з основами іменників у складі прислівника пишеться разом per § 41, п. 1, дефіс не ставиться.",
                        explanation_en="Preposition з- merged into an adverb is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="від ранку",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="Сполука «від ранку» позначає часову межу тривалості (від ранку до полудня), а момент пробудження (коли?) позначає «зранку» або «вранці».",
                        explanation_en="'Від ранку' denotes starting boundary of duration; the moment of waking up is expressed by 'зранку'.",
                    ),
                ),
                rule_citation=cit_time,
                rule_summary_ua=ua_time,
                rule_summary_en=en_time,
            ),
            AdverbCard(
                card_id="adverb_card_10",
                category=AdverbCategory.TIME,
                prompt="Науковці затрималися в лабораторії _______, завершуючи важливий експеримент.",
                target_token="допізна",
                correct_answer="допізна",
                distractors=(
                    AdverbDistractor(
                        text="до пізна",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="«Допізна» — прислівник часу, утворений від прийменника та короткої форми прикметника; пишеться разом per § 41, п. 1.",
                        explanation_en="'Допізна' is a time adverb formed from preposition + short adjective form; written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="до-пізна",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Дефіс у прислівнику «допізна» є орфографічною помилкою; слово пишеться разом per § 41, п. 1.",
                        explanation_en="Hyphen in 'допізна' is an error; the word is spelled together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="до пізнього",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Словосполучення «до пізнього» є граматично неповним; правильний прислівник — «допізна».",
                        explanation_en="Phrase 'до пізнього' is grammatically incomplete; the correct adverb is 'допізна'.",
                    ),
                ),
                rule_citation=cit_time,
                rule_summary_ua=ua_time,
                rule_summary_en=en_time,
            ),
        ]
    )

    # Category 3: Place & Direction
    cit_place, ua_place, en_place = resolve_place_direction_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_11",
                category=AdverbCategory.PLACE_DIRECTION,
                prompt="Після тривалого робочого дня втомлені робітники повертаються _______.",
                target_token="додому",
                correct_answer="додому",
                distractors=(
                    AdverbDistractor(
                        text="до дому",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«До дому» окремо вживається тоді, коли йдеться про конкретну будівлю з означенням (наприклад, підійти до великого дому), а напрямок руху «куди?» позначає прислівник «додому» per § 41, п. 1.",
                        explanation_en="'До дому' separately refers to a physical building with modifiers; direction homeward ('where to?') is the fused adverb 'додому' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="до-дому",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «додому» пишеться разом, дефіс заборонено per § 41, п. 1.",
                        explanation_en="Adverb 'додому' is written as one word; hyphens are prohibited per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в дім",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Конструкція «йти в дім» є невластивою українській мові для позначення повернення до свого житла; нормативно — «іти додому».",
                        explanation_en="'Йти в дім' is an unnatural calque for returning home; authentic Ukrainian is 'іти додому'.",
                    ),
                ),
                rule_citation=cit_place,
                rule_summary_ua=ua_place,
                rule_summary_en=en_place,
            ),
            AdverbCard(
                card_id="adverb_card_12",
                category=AdverbCategory.PLACE_DIRECTION,
                prompt="Дитина підняла очі й подивилася _______ на зоряне нічне небо.",
                target_token="вгору",
                correct_answer="вгору",
                distractors=(
                    AdverbDistractor(
                        text="в гору",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«В гору» окремо вживається тоді, коли мова йде про географічну височину (врізатися в круту гору), а напрямок руху «куди? вгору» пишеться разом per § 41, п. 1.",
                        explanation_en="'В гору' separately refers to a physical mountain; upward direction ('where to? upwards') is the fused adverb 'вгору' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в-гору",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «вгору» пишеться разом per § 41, п. 1.",
                        explanation_en="Adverb 'вгору' is written as a single word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на верх",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Просторовий напрямок погляду вгору передається прислівником «вгору» (або «наверх» разом per § 41, п. 1, але не окремо «на верх»).",
                        explanation_en="Direction of gaze upwards is conveyed by 'вгору'; separate 'на верх' is incorrect here.",
                    ),
                ),
                rule_citation=cit_place,
                rule_summary_ua=ua_place,
                rule_summary_en=en_place,
            ),
            AdverbCard(
                card_id="adverb_card_13",
                category=AdverbCategory.PLACE_DIRECTION,
                prompt="Стежка круто повертала й вела мандрівників _______ до гірської річки.",
                target_token="донизу",
                correct_answer="донизу",
                distractors=(
                    AdverbDistractor(
                        text="до низу",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник напрямку «донизу» (куди?) утворений злиттям прийменника й іменника та пишеться разом per § 41, п. 1.",
                        explanation_en="Directional adverb 'донизу' ('where to? downwards') is formed by fusion and written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="до-низу",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Дефіс у прислівнику «донизу» є помилкою; слово пишеться разом per § 41, п. 1.",
                        explanation_en="Hyphen in adverb 'донизу' is an error; it is written as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="під низ",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="«Під низ» — це прийменниково-іменникова сполука місця (покласти під низ), а не напрямок спуску (донизу / вниз).",
                        explanation_en="'Під низ' is a prepositional phrase of location, not the directional adverb of descent ('донизу').",
                    ),
                ),
                rule_citation=cit_place,
                rule_summary_ua=ua_place,
                rule_summary_en=en_place,
            ),
            AdverbCard(
                card_id="adverb_card_14",
                category=AdverbCategory.PLACE_DIRECTION,
                prompt="Незважаючи на труднощі, наша команда продовжує впевнено рухатися _______.",
                target_token="вперед",
                correct_answer="вперед",
                distractors=(
                    AdverbDistractor(
                        text="в перед",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник «вперед» є зрощеним і пишеться разом per § 41, п. 1; окремого написання «в перед» у сучасній мові не існує.",
                        explanation_en="Adverb 'вперед' is fused and written together per § 41, p. 1; separate 'в перед' does not exist in modern Ukrainian.",
                    ),
                    AdverbDistractor(
                        text="в-перед",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «вперед» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'вперед' is written as one word without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="вперід",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Форма «вперід» є орфографічно помилковою (чергування е/і тут відсутнє); нормативне написання — «вперед» per § 41, п. 1.",
                        explanation_en="Form 'вперід' is an orthographic error; standard spelling is 'вперед' per § 41, p. 1.",
                    ),
                ),
                rule_citation=cit_place,
                rule_summary_ua=ua_place,
                rule_summary_en=en_place,
            ),
            AdverbCard(
                card_id="adverb_card_15",
                category=AdverbCategory.PLACE_DIRECTION,
                prompt="Охоронець стояв _______ за спинами гостей, пильно спостерігаючи за залою.",
                target_token="ззаду",
                correct_answer="ззаду",
                distractors=(
                    AdverbDistractor(
                        text="з заду",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник місця «ззаду» пишеться разом per § 41, п. 1; подвоєння букв «з» виникає на стику прийменника з- та кореня зад-.",
                        explanation_en="Spatial adverb 'ззаду' is written together per § 41, p. 1; geminated 'зз' occurs at prefix з- + root зад- junction.",
                    ),
                    AdverbDistractor(
                        text="з-заду",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Дефіс у слові «ззаду» не пишеться; це складний прислівник, який пишеться разом per § 41, п. 1.",
                        explanation_en="Hyphen is not written in 'ззаду'; it is a compound adverb written as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="сзаду",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="В українській мові немає префікса с- перед дзвінкими приголосними; правильно — «ззаду» (з подвоєнням букв «з»).",
                        explanation_en="Ukrainian has no prefix с- before voiced consonants; the correct spelling is 'ззаду' with doubled 'з'.",
                    ),
                ),
                rule_citation=cit_place,
                rule_summary_ua=ua_place,
                rule_summary_en=en_place,
            ),
        ]
    )

    # Category 4: Measure & Degree
    cit_meas, ua_meas, en_meas = resolve_measure_degree_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_16",
                category=AdverbCategory.MEASURE_DEGREE,
                prompt="Складний переклад наукової статті вже виконано _______.",
                target_token="наполовину",
                correct_answer="наполовину",
                distractors=(
                    AdverbDistractor(
                        text="на половину",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«На половину» окремо вживається як іменник з прийменником (наприклад, розділити пиріг на рівну половину), а міра виконання дії (наскільки?) виражається прислівником «наполовину» per § 41, п. 1.",
                        explanation_en="'На половину' separately is a noun with preposition; the adverb of measure ('to what degree?') is written as one word: 'наполовину' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-половину",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівники міри й ступеня, утворені злиттям прийменника з іменником, пишуться разом per § 41, п. 1.",
                        explanation_en="Adverbs of measure fused from preposition + noun are written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в половину",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Конструкція «в половину» є калькою з російської («вполовину»); нормативно українською — «наполовину».",
                        explanation_en="'В половину' is a Russian calque; authentic Ukrainian is 'наполовину'.",
                    ),
                ),
                rule_citation=cit_meas,
                rule_summary_ua=ua_meas,
                rule_summary_en=en_meas,
            ),
            AdverbCard(
                card_id="adverb_card_17",
                category=AdverbCategory.MEASURE_DEGREE,
                prompt="Пожежа знищила дерев'яну старовинну споруду _______.",
                target_token="дощенту",
                correct_answer="дощенту",
                distractors=(
                    AdverbDistractor(
                        text="до щенту",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник міри «дощенту» утворений злиттям прийменника до- та іменника щент і пишеться разом per § 41, п. 1.",
                        explanation_en="Adverb of degree 'дощенту' is formed by fusion of до- and щент and is written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="до-щенту",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="У слові «дощенту» дефіс не ставиться; воно пишеться разом per § 41, п. 1.",
                        explanation_en="No hyphen is used in 'дощенту'; it is spelled as a single word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="до щента",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Закінченням прислівника є -у («дощенту»), форма «до щента» є ненормативною.",
                        explanation_en="The ending of this adverb is -у ('дощенту'); form 'до щента' is non-standard.",
                    ),
                ),
                rule_citation=cit_meas,
                rule_summary_ua=ua_meas,
                rule_summary_en=en_meas,
            ),
            AdverbCard(
                card_id="adverb_card_18",
                category=AdverbCategory.MEASURE_DEGREE,
                prompt="Після тривалої прогулянки лісом мандрівник _______ не відчував утоми.",
                target_token="зовсім",
                correct_answer="зовсім",
                distractors=(
                    AdverbDistractor(
                        text="зо всім",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«Зо всім» окремо є прийменником із займенником (наприклад, погодитися зо всім почутим), а міру заперечення «зовсім не» виражає прислівник «зовсім» per § 41, п. 1.",
                        explanation_en="'Зо всім' separately is preposition + pronoun; degree of negation ('not at all') is the fused adverb 'зовсім' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="зо-всім",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «зовсім» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'зовсім' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="совсім",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Слово «совсім» є русизмом; в українській літературній мові нормативним є прислівник «зовсім».",
                        explanation_en="'Совсім' is Russian interference; literary Ukrainian strictly uses 'зовсім'.",
                    ),
                ),
                rule_citation=cit_meas,
                rule_summary_ua=ua_meas,
                rule_summary_en=en_meas,
            ),
            AdverbCard(
                card_id="adverb_card_19",
                category=AdverbCategory.MEASURE_DEGREE,
                prompt="Новий процесор працює _______ швидше за попередню модель.",
                target_token="набагато",
                correct_answer="набагато",
                distractors=(
                    AdverbDistractor(
                        text="на багато",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник «набагато» пишеться разом per § 41, п. 1; окремо «на багато» вживається лише у сполуках з іменником (наприклад, на багато років).",
                        explanation_en="Adverb 'набагато' is written together per § 41, p. 1; separate 'на багато' is only used with nouns (for many years).",
                    ),
                    AdverbDistractor(
                        text="на-багато",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «набагато» пишеться разом per § 41, п. 1, використання дефіса помилкове.",
                        explanation_en="Adverb 'набагато' is written as one word per § 41, p. 1; hyphenation is erroneous.",
                    ),
                    AdverbDistractor(
                        text="куда",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Використання частки «куда» для підсилення вищого ступеня («куда швидше») є російською калькою; нормативно українською — «набагато швидше» або «значно швидше».",
                        explanation_en="Using 'куда' to intensify comparatives ('куда швидше') is a Russianism; Ukrainian uses 'набагато швидше' or 'значно швидше'.",
                    ),
                ),
                rule_citation=cit_meas,
                rule_summary_ua=ua_meas,
                rule_summary_en=en_meas,
            ),
            AdverbCard(
                card_id="adverb_card_20",
                category=AdverbCategory.MEASURE_DEGREE,
                prompt="Лікарі наголосили, що прийняти ці ліки вчасно є _______ необхідним для одужання.",
                target_token="вкрай",
                correct_answer="вкрай",
                distractors=(
                    AdverbDistractor(
                        text="в край",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«В край» окремо означає рух до краю або географічної землі (поїхати в рідний край), а високий ступінь ознаки (якою мірою? надзвичайно) передає прислівник «вкрай» per § 41, п. 1.",
                        explanation_en="'В край' separately denotes spatial movement to an edge/region; high degree ('extremely') is the adverb 'вкрай' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в-край",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «вкрай» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'вкрай' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="крайнє",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Вживання форми «крайнє» у значенні прислівника міри («крайнє необхідним») є ненормативним суржиком; нормативно — «вкрай».",
                        explanation_en="Using 'крайнє' as an adverb of degree ('крайнє необхідним') is non-standard; authentic Ukrainian is 'вкрай'.",
                    ),
                ),
                rule_citation=cit_meas,
                rule_summary_ua=ua_meas,
                rule_summary_en=en_meas,
            ),
        ]
    )

    # Category 5: Cause & Purpose
    cit_cause, ua_cause, en_cause = resolve_cause_purpose_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_21",
                category=AdverbCategory.CAUSE_PURPOSE,
                prompt="Він не хотів образити друга, а вигукнув ці різкі слова просто _______.",
                target_token="зопалу",
                correct_answer="зопалу",
                distractors=(
                    AdverbDistractor(
                        text="з опалу",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник причини «зопалу» утворений від прийменника зо- та кореня пал і пишеться разом per § 41, п. 1.",
                        explanation_en="Causal adverb 'зопалу' is fused from preposition зо- and root пал; written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="зо-палу",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Слово «зопалу» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Word 'зопалу' is spelled together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="з гаряча",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «з гаряча» є калькою з російської («сгоряча»); нормативні українські відповідники — «зопалу» або «згарячу».",
                        explanation_en="'З гаряча' is a Russian calque ('сгоряча'); authentic Ukrainian equivalents are 'зопалу' or 'згарячу'.",
                    ),
                ),
                rule_citation=cit_cause,
                rule_summary_ua=ua_cause,
                rule_summary_en=en_cause,
            ),
            AdverbCard(
                card_id="adverb_card_22",
                category=AdverbCategory.CAUSE_PURPOSE,
                prompt="Не варто приймати доленосні рішення _______, коли вирують емоції.",
                target_token="згарячу",
                correct_answer="згарячу",
                distractors=(
                    AdverbDistractor(
                        text="з гарячу",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник причини «згарячу» пишеться разом per § 41, п. 1.",
                        explanation_en="Causal adverb 'згарячу' is written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="з-гарячу",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Дефіс у слові «згарячу» є орфографічною помилкою; слово пишеться разом per § 41, п. 1.",
                        explanation_en="Hyphen in 'згарячу' is an error; it is spelled as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="згаряча",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Форма на -а («згаряча») є російським впливом; в українській літературній мові закріплена форма на -у: «згарячу».",
                        explanation_en="Ending -а ('згаряча') is Russian interference; Ukrainian standard maintains -у: 'згарячу'.",
                    ),
                ),
                rule_citation=cit_cause,
                rule_summary_ua=ua_cause,
                rule_summary_en=en_cause,
            ),
            AdverbCard(
                card_id="adverb_card_23",
                category=AdverbCategory.CAUSE_PURPOSE,
                prompt="Він не випадково запізнився на нараду, а зробив це цілком _______.",
                target_token="навмисне",
                correct_answer="навмисне",
                distractors=(
                    AdverbDistractor(
                        text="на вмисне",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник мети «навмисне» є зрощеним словом і пишеться разом per § 41, п. 1.",
                        explanation_en="Purpose adverb 'навмисне' is fused and written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-вмисне",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Слово «навмисне» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Word 'навмисне' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="нарошно",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Слово «нарошно» є російським просторіччям («нарочно»); нормативні українські слова — «навмисне» або «навмисно».",
                        explanation_en="'Нарошно' is colloquial Russian interference ('нарочно'); standard Ukrainian uses 'навмисне' or 'навмисно'.",
                    ),
                ),
                rule_citation=cit_cause,
                rule_summary_ua=ua_cause,
                rule_summary_en=en_cause,
            ),
            AdverbCard(
                card_id="adverb_card_24",
                category=AdverbCategory.CAUSE_PURPOSE,
                prompt="Щедрий меценат допомагав людям скромно, не виставляючи свої благодіяння _______.",
                target_token="напоказ",
                correct_answer="напоказ",
                distractors=(
                    AdverbDistractor(
                        text="на показ",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«На показ» окремо вживається тоді, коли йдеться про сеанс чи виставу (піти на показ фільму), а мету дії «навіщо?» позначає прислівник «напоказ» per § 41, п. 1.",
                        explanation_en="'На показ' separately refers to a film screening or show; purpose adverb 'for show' is 'напоказ' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-показ",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник мети «напоказ» пишеться разом per § 41, п. 1.",
                        explanation_en="Adverb of purpose 'напоказ' is written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на показність",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Такої прислівникової форми не існує; правильне нормативне слово — «напоказ».",
                        explanation_en="Such an adverbial form does not exist; standard word is 'напоказ'.",
                    ),
                ),
                rule_citation=cit_cause,
                rule_summary_ua=ua_cause,
                rule_summary_en=en_cause,
            ),
            AdverbCard(
                card_id="adverb_card_25",
                category=AdverbCategory.CAUSE_PURPOSE,
                prompt="Він завжди мав норовливий характер і робив усе _______, не зважаючи на застереження друзів.",
                target_token="наперекір",
                correct_answer="наперекір",
                distractors=(
                    AdverbDistractor(
                        text="на перекір",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник мети й наміру «наперекір» (у значенні «на зло, усупереч іншим») пишеться разом per § 41, п. 1.",
                        explanation_en="Adverb of intent/purpose 'наперекір' (meaning 'in defiance, spitefully') is written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-перекір",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «наперекір» пишеться разом, дефіс не вживається per § 41, п. 1.",
                        explanation_en="Adverb 'наперекір' is written together; no hyphen is used per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на перекор",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Форма «на перекор» з голосним [о] є русизмом; в українській літературній мові нормативним є прислівник «наперекір» з ікавізмом у закритому складі.",
                        explanation_en="Form 'на перекор' is Russian interference; standard Ukrainian uses adverb 'наперекір' with ikavism in a closed syllable.",
                    ),
                ),
                rule_citation=cit_cause,
                rule_summary_ua=ua_cause,
                rule_summary_en=en_cause,
            ),
        ]
    )

    # Category 6: Prefix по- Hyphenated
    cit_po, ua_po, en_po = resolve_prefix_po_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_26",
                category=AdverbCategory.PREFIX_PO_HYPHEN,
                prompt="Іноземні гості щиро намагалися розмовляти _______ під час перебування у Львові.",
                target_token="по-українськи",
                correct_answer="по-українськи",
                distractors=(
                    AdverbDistractor(
                        text="по українськи",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Прислівники з префіксом по- та суфіксами -ськи, -цьки пишуться через дефіс per § 41, п. 3, 1).",
                        explanation_en="Adverbs with prefix по- and suffixes -ськи, -цьки are hyphenated per § 41, p. 3, 1).",
                    ),
                    AdverbDistractor(
                        text="поукраїнськи",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Написання разом є грубою орфографічною помилкою; за правилом § 41, п. 2 а префікс по- з суфіксом -ськи пишеться через дефіс.",
                        explanation_en="Writing as one word is a serious error; per § 41, p. 3, 1) prefix по- with suffix -ськи requires a hyphen.",
                    ),
                    AdverbDistractor(
                        text="на українській",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Конструкція «говорити на українській» є калькою з російської («говорить на украинском»); правильно — «говорити по-українськи» або «говорити українською мовою».",
                        explanation_en="'Говорити на українській' is a Russian calque; authentic Ukrainian is 'говорити по-українськи' or 'говорити українською мовою'.",
                    ),
                ),
                rule_citation=cit_po,
                rule_summary_ua=ua_po,
                rule_summary_en=en_po,
            ),
            AdverbCard(
                card_id="adverb_card_27",
                category=AdverbCategory.PREFIX_PO_HYPHEN,
                prompt="Після реформ колектив вирішив організувати виробничий процес цілком _______.",
                target_token="по-новому",
                correct_answer="по-новому",
                distractors=(
                    AdverbDistractor(
                        text="по новому",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Прислівник способу дії «по-новому» пишеться через дефіс per § 41, п. 3, 1); окремо пишеться лише прийменник з прикметником: «по новому шляху».",
                        explanation_en="Adverb of manner 'по-новому' is hyphenated per § 41, p. 3, 1); separate 'по новому' is only preposition + adjective.",
                    ),
                    AdverbDistractor(
                        text="поновому",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Прислівники з префіксом по- та суфіксом -ому пишуться через дефіс, а не разом per § 41, п. 3, 1).",
                        explanation_en="Adverbs with prefix по- and suffix -ому are hyphenated, not written as one word per § 41, p. 3, 1).",
                    ),
                    AdverbDistractor(
                        text="за новим",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="Вираз «за новим» вимагає узгоджуваного іменника (за новим розкладом); самостійний прислівник способу дії — «по-новому».",
                        explanation_en="'За новим' requires an agreeing noun; independent adverb of manner is 'по-новому'.",
                    ),
                ),
                rule_citation=cit_po,
                rule_summary_ua=ua_po,
                rule_summary_en=en_po,
            ),
            AdverbCard(
                card_id="adverb_card_28",
                category=AdverbCategory.PREFIX_PO_HYPHEN,
                prompt="Старий учитель тепло й _______ підбадьорив засмученого учня перед виступом.",
                target_token="по-батьківськи",
                correct_answer="по-батьківськи",
                distractors=(
                    AdverbDistractor(
                        text="по батьківськи",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Прислівники з префіксом по- та суфіксами -ськи/-цьки обов'язково пишуться через дефіс per § 41, п. 3, 1).",
                        explanation_en="Adverbs with prefix по- and suffixes -ськи/-цьки must be hyphenated per § 41, p. 3, 1).",
                    ),
                    AdverbDistractor(
                        text="побатьківськи",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Префікс по- з суфіксом -ськи не пишеться разом; обов'язковий дефіс per § 41, п. 3, 1).",
                        explanation_en="Prefix по- with suffix -ськи cannot be written together; hyphen is mandatory per § 41, p. 3, 1).",
                    ),
                    AdverbDistractor(
                        text="як по батькові",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="Вираз «по батькові» вказує на патронім (звертатися по батькові), а спосіб дії «з батьківською турботою» передає прислівник «по-батьківськи».",
                        explanation_en="'По батькові' refers to patronymics; manner with fatherly warmth is 'по-батьківськи'.",
                    ),
                ),
                rule_citation=cit_po,
                rule_summary_ua=ua_po,
                rule_summary_en=en_po,
            ),
            AdverbCard(
                card_id="adverb_card_29",
                category=AdverbCategory.PREFIX_PO_HYPHEN,
                prompt="Зробимо так, як ти пропонуєш, хоча все одно врешті-решт вийде _______.",
                target_token="по-моєму",
                correct_answer="по-моєму",
                distractors=(
                    AdverbDistractor(
                        text="по моєму",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Прислівник «по-моєму» пишеться через дефіс per § 41, п. 3, 1); окремо «по моєму» пишеться лише тоді, коли «моєму» є означенням до іменника («по моєму сліду»).",
                        explanation_en="Adverb 'по-моєму' is hyphenated per § 41, p. 3, 1); separate 'по моєму' occurs only with an explicit noun ('по моєму сліду').",
                    ),
                    AdverbDistractor(
                        text="помоєму",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Прислівники, утворені від займенників з префіксом по- та суфіксом -ему/-ому, пишуться через дефіс, а не разом per § 41, п. 3, 1).",
                        explanation_en="Pronominal adverbs with prefix по- and suffix -ему/-ому are hyphenated, not fused per § 41, p. 3, 1).",
                    ),
                    AdverbDistractor(
                        text="по-мойому",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="В українській мові після м'яких приголосних пишеться літера є: «по-моєму», а не йо.",
                        explanation_en="In Ukrainian after soft consonants letter є is written: 'по-моєму', not йо.",
                    ),
                ),
                rule_citation=cit_po,
                rule_summary_ua=ua_po,
                rule_summary_en=en_po,
            ),
            AdverbCard(
                card_id="adverb_card_30",
                category=AdverbCategory.PREFIX_PO_HYPHEN,
                prompt="Дідусь щиро й _______ радів несподіваному подарунку від онуків.",
                target_token="по-дитячому",
                correct_answer="по-дитячому",
                distractors=(
                    AdverbDistractor(
                        text="по дитячому",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Прислівники з префіксом по- та суфіксом -ому пишуться через дефіс per § 41, п. 3, 1).",
                        explanation_en="Adverbs with prefix по- and suffix -ому are hyphenated per § 41, p. 3, 1).",
                    ),
                    AdverbDistractor(
                        text="подитячому",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Разом прислівник «по-дитячому» не пишеться; наявність префікса по- та суфікса -ому вимагає дефіса per § 41, п. 3, 1).",
                        explanation_en="'По-дитячому' cannot be written together; presence of по- and -ому requires a hyphen per § 41, p. 3, 1).",
                    ),
                    AdverbDistractor(
                        text="по дитячи",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="В українській мові немає форми «по дитячи»; нормативними є «по-дитячому» або «по-дитячи» (через дефіс), проте з суфіксом -ому є найпоширенішим.",
                        explanation_en="Form 'по дитячи' is incorrect; normative forms require a hyphen ('по-дитячому').",
                    ),
                ),
                rule_citation=cit_po,
                rule_summary_ua=ua_po,
                rule_summary_en=en_po,
            ),
        ]
    )

    # Category 7: Particles with Hyphen
    cit_part, ua_part, en_part = resolve_particles_hyphen_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_31",
                category=AdverbCategory.PARTICLES_HYPHEN,
                prompt="Цю рідкісну книгу зараз важко відшукати _______ у міських книгарнях.",
                target_token="будь-де",
                correct_answer="будь-де",
                distractors=(
                    AdverbDistractor(
                        text="будь де",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Частка будь- у складі прислівників завжди пишеться через дефіс per § 41, п. 3, 3) (будь-де, будь-коли, будь-куди).",
                        explanation_en="Particle будь- in adverbs is always hyphenated per § 41, p. 3, 3) (будь-де, будь-коли).",
                    ),
                    AdverbDistractor(
                        text="будьде",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Частка будь- не пишеться разом із прислівниками; правильне написання — через дефіс per § 41, п. 3, 3).",
                        explanation_en="Particle будь- is never fused with adverbs; correct spelling requires a hyphen per § 41, p. 3, 3).",
                    ),
                    AdverbDistractor(
                        text="будь-куди",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="«Будь-куди» вказує на напрямок руху (куди?), тоді як у реченні запитується про місцезнаходження (де? шукати де? — будь-де).",
                        explanation_en="'Будь-куди' denotes direction of motion (where to?), whereas the sentence requires location (where? look where? — будь-де).",
                    ),
                ),
                rule_citation=cit_part,
                rule_summary_ua=ua_part,
                rule_summary_en=en_part,
            ),
            AdverbCard(
                card_id="adverb_card_32",
                category=AdverbCategory.PARTICLES_HYPHEN,
                prompt="Справжній майстер ніколи не виконує важливу роботу _______, а дбає про кожну деталь.",
                target_token="як-небудь",
                correct_answer="як-небудь",
                distractors=(
                    AdverbDistractor(
                        text="як небудь",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Частка -небудь у складі неозначених прислівників пишеться через дефіс per § 41, п. 3, 3) (як-небудь, де-небудь, коли-небудь).",
                        explanation_en="Particle -небудь in indefinite adverbs is hyphenated per § 41, p. 3, 3) (як-небудь, де-небудь).",
                    ),
                    AdverbDistractor(
                        text="якнебудь",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Частка -небудь не пишеться разом з основою; вона завжди приєднується дефісом per § 41, п. 3, 3).",
                        explanation_en="Particle -небудь is never written as one word; it is always attached with a hyphen per § 41, p. 3, 3).",
                    ),
                    AdverbDistractor(
                        text="як-не-будь",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Частка -небудь утворює єдиний формант і приєднується одним дефісом: «як-небудь» per § 41, п. 3, 3); написання з двома дефісами («як-не-будь») є помилковим.",
                        explanation_en="The particle -небудь is a single formant attached with one hyphen: 'як-небудь' per § 41, p. 3, 3); writing with two hyphens ('як-не-будь') is incorrect.",
                    ),
                ),
                rule_citation=cit_part,
                rule_summary_ua=ua_part,
                rule_summary_en=en_part,
            ),
            AdverbCard(
                card_id="adverb_card_33",
                category=AdverbCategory.PARTICLES_HYPHEN,
                prompt="Він зумів розв'язати цю заплутану задачу _______ хитро й нестандартно.",
                target_token="хтозна-як",
                correct_answer="хтозна-як",
                distractors=(
                    AdverbDistractor(
                        text="хтозна як",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Частка хтозна- пишеться з прислівниками через дефіс per § 41, п. 3, 3) (хтозна-як, хтозна-де, хтозна-коли).",
                        explanation_en="Particle хтозна- is hyphenated with adverbs per § 41, p. 3, 3) (хтозна-як, хтозна-де).",
                    ),
                    AdverbDistractor(
                        text="хтознаяк",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Слово «хтозна-як» не пишеться разом; частка хтозна- вимагає написання через дефіс per § 41, п. 3, 3).",
                        explanation_en="'Хтозна-як' cannot be fused; particle хтозна- strictly requires a hyphen per § 41, p. 3, 3).",
                    ),
                    AdverbDistractor(
                        text="хтозна-де",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="«Хтозна-де» вказує на невідоме місце (де?), тоді як для характеристики способу розв'язання задачі потрібен прислівник способу дії «хтозна-як» (як? — хтозна-як хитро).",
                        explanation_en="'Хтозна-де' indicates an unknown location (where?), whereas characterizing manner of action requires manner adverb 'хтозна-як' (how? — хтозна-як хитро).",
                    ),
                ),
                rule_citation=cit_part,
                rule_summary_ua=ua_part,
                rule_summary_en=en_part,
            ),
            AdverbCard(
                card_id="adverb_card_34",
                category=AdverbCategory.PARTICLES_HYPHEN,
                prompt="Ця старовинна легенда зародилася в наших краях _______ в сиву давнину.",
                target_token="казна-коли",
                correct_answer="казна-коли",
                distractors=(
                    AdverbDistractor(
                        text="казна коли",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Частка казна- з прислівниками пишеться через дефіс per § 41, п. 3, 3).",
                        explanation_en="Particle казна- with adverbs is hyphenated per § 41, p. 3, 3).",
                    ),
                    AdverbDistractor(
                        text="казнаколи",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Написання разом є орфографічною помилкою; частка казна- приєднується через дефіс per § 41, п. 3, 3).",
                        explanation_en="Fused spelling is an orthographic error; particle казна- attaches via hyphen per § 41, p. 3, 3).",
                    ),
                    AdverbDistractor(
                        text="бозна коли",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Частка бозна- так само вимагає дефіса (бозна-коли); роздільне написання помилкове per § 41, п. 3, 3).",
                        explanation_en="Particle бозна- likewise requires a hyphen (бозна-коли); separate writing is wrong per § 41, p. 3, 3).",
                    ),
                ),
                rule_citation=cit_part,
                rule_summary_ua=ua_part,
                rule_summary_en=en_part,
            ),
            AdverbCard(
                card_id="adverb_card_35",
                category=AdverbCategory.PARTICLES_HYPHEN,
                prompt="Ніхто не міг збагнути, як їм вдалося вибратися з темного яру _______ швидко.",
                target_token="бозна-як",
                correct_answer="бозна-як",
                distractors=(
                    AdverbDistractor(
                        text="бозна як",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Частка бозна- у складі неозначених прислівників завжди пишеться через дефіс per § 41, п. 3, 3).",
                        explanation_en="Particle бозна- in indefinite adverbs is always hyphenated per § 41, p. 3, 3).",
                    ),
                    AdverbDistractor(
                        text="бознаяк",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Частка бозна- не пишеться разом; обов'язкове написання через дефіс per § 41, п. 3, 3).",
                        explanation_en="Particle бозна- is not written together; hyphenation is mandatory per § 41, p. 3, 3).",
                    ),
                    AdverbDistractor(
                        text="бозна-куди",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="«Бозна-куди» вказує на невизначений напрямок чи місце (куди? де?), а не на міру чи спосіб швидкої дії (як? наскільки? — бозна-як швидко).",
                        explanation_en="'Бозна-куди' denotes indefinite direction or location (where to?), not manner or degree of swift action (how? — бозна-як).",
                    ),
                ),
                rule_citation=cit_part,
                rule_summary_ua=ua_part,
                rule_summary_en=en_part,
            ),
        ]
    )

    # Category 8: Reduplication & Compounds
    cit_red, ua_red, en_red = resolve_reduplication_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_36",
                category=AdverbCategory.REDUPLICATION,
                prompt="Дипломати залишилися в кабінеті, щоб обговорити суперечливі питання _______.",
                target_token="віч-на-віч",
                correct_answer="віч-на-віч",
                distractors=(
                    AdverbDistractor(
                        text="віч на віч",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Складний прислівник «віч-на-віч» пишеться з двома дефісами per § 41, п. 3, 5).",
                        explanation_en="Compound adverb 'віч-на-віч' is written with two hyphens per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="вічнавіч",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Слово «віч-на-віч» не пишеться разом; воно складається з двох однакових іменників, з'єднаних прийменником, і пишеться через дефіси per § 41, п. 3, 5).",
                        explanation_en="'Віч-на-віч' cannot be fused; identical nouns joined by preposition take hyphens per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="віч на-віч",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="У складному прислівнику «віч-на-віч» обидва з'єднання вимагають дефісів per § 41, п. 3, 5); односторонній дефіс неприпустимий.",
                        explanation_en="In compound adverb 'віч-на-віч' both junctures require hyphens per § 41, p. 3, 5); a single hyphen is incorrect.",
                    ),
                ),
                rule_citation=cit_red,
                rule_summary_ua=ua_red,
                rule_summary_en=en_red,
            ),
            AdverbCard(
                card_id="adverb_card_37",
                category=AdverbCategory.REDUPLICATION,
                prompt="Волонтери та рятувальники працювали _______, допомагаючи постраждалим мешканцям.",
                target_token="пліч-о-пліч",
                correct_answer="пліч-о-пліч",
                distractors=(
                    AdverbDistractor(
                        text="пліч о пліч",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Прислівникове сполучення «пліч-о-пліч» пишеться з двома дефісами per § 41, п. 3, 5).",
                        explanation_en="Adverbial phrase 'пліч-о-пліч' is written with two hyphens per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="плічопліч",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Написання разом помилкове; сполука «пліч-о-пліч» обов'язково оформлюється через дефіси per § 41, п. 3, 5).",
                        explanation_en="Writing together is wrong; 'пліч-о-пліч' strictly requires hyphens per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="пліч-на-пліч",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Усталений складний прислівник має сполучний голосний о: «пліч-о-пліч», а не прийменник на per § 41, п. 3, 5).",
                        explanation_en="The set compound adverb has linking vowel о: 'пліч-о-пліч', not preposition на per § 41, p. 3, 5).",
                    ),
                ),
                rule_citation=cit_red,
                rule_summary_ua=ua_red,
                rule_summary_en=en_red,
            ),
            AdverbCard(
                card_id="adverb_card_38",
                category=AdverbCategory.REDUPLICATION,
                prompt="Кіт _______ підкрався до миски й спритно схопив шматочок риби.",
                target_token="тишком-нишком",
                correct_answer="тишком-нишком",
                distractors=(
                    AdverbDistractor(
                        text="тишком нишком",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Синонімічні парні прислівники пишуться через дефіс per § 41, п. 3, 5) (тишком-нишком, зроду-віку).",
                        explanation_en="Synonymous paired adverbs are hyphenated per § 41, p. 3, 5) (тишком-нишком).",
                    ),
                    AdverbDistractor(
                        text="тишкомнишком",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Парне повторення близьких за значенням слів не пишеться разом; потрібен дефіс per § 41, п. 3, 5).",
                        explanation_en="Paired synonymous roots are not written together; a hyphen is required per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="тихо-нишком",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Обидві частини стійкого парного прислівника мають однакове закінчення: «тишком-нишком».",
                        explanation_en="Both parts of this set paired adverb have matching endings: 'тишком-нишком'.",
                    ),
                ),
                rule_citation=cit_red,
                rule_summary_ua=ua_red,
                rule_summary_en=en_red,
            ),
            AdverbCard(
                card_id="adverb_card_39",
                category=AdverbCategory.REDUPLICATION,
                prompt="Після виснажливого марафону бігун _______ переставляв стомлені ноги.",
                target_token="ледве-ледве",
                correct_answer="ледве-ледве",
                distractors=(
                    AdverbDistractor(
                        text="ледве ледве",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Повторення того самого слова для підсилення значення пишеться через дефіс per § 41, п. 3, 5).",
                        explanation_en="Reduplication of the same word for emphasis is hyphenated per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="ледвеледве",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Повторювані слова ніколи не зливаються в одне слово; дефіс обов'язковий per § 41, п. 3, 5).",
                        explanation_en="Reduplicated words never merge into a single word; hyphen is mandatory per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="чуть-чуть",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Слово «чуть-чуть» є прямим запозиченням з російської мови; літературні українські відповідники — «ледве-ледве», «ледь-ледь» або «трохи».",
                        explanation_en="'Чуть-чуть' is a direct Russianism; literary Ukrainian uses 'ледве-ледве', 'ледь-ледь', or 'трохи'.",
                    ),
                ),
                rule_citation=cit_red,
                rule_summary_ua=ua_red,
                rule_summary_en=en_red,
            ),
            AdverbCard(
                card_id="adverb_card_40",
                category=AdverbCategory.REDUPLICATION,
                prompt="Ці величні замкові мури були зведені _______ хоробрими лицарями.",
                target_token="давним-давно",
                correct_answer="давним-давно",
                distractors=(
                    AdverbDistractor(
                        text="давним давно",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Підсилювальне сполучення однакових коренів різної форми пишеться через дефіс per § 41, п. 3, 5) (давним-давно, повік-віки).",
                        explanation_en="Emphatic combination of identical roots in different forms is hyphenated per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="давнимдавно",
                        interference_key=AdverbInterferenceKey.HYPHEN_OMISSION,
                        explanation_ua="Слово «давним-давно» пишеться через дефіс, а не разом per § 41, п. 3, 5).",
                        explanation_en="Word 'давним-давно' is hyphenated, not written as one word per § 41, p. 3, 5).",
                    ),
                    AdverbDistractor(
                        text="давнім-давно",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Перша частина підсилювального прислівника має суфікс орудного відмінка -им («давним-давно»), а не прикметникову форму «давнім».",
                        explanation_en="The first part of reduplicative adverb давним-давно takes instrumental ending -им ('давним-давно'), not adjective form 'давнім'.",
                    ),
                ),
                rule_citation=cit_red,
                rule_summary_ua=ua_red,
                rule_summary_en=en_red,
            ),
        ]
    )

    # Category 9: Fused Together
    cit_fused, ua_fused, en_fused = resolve_together_fused_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_41",
                category=AdverbCategory.TOGETHER_FUSED,
                prompt="Коли експеримент зазнав невдачі, вчені вирішили розпочати дослідження _______.",
                target_token="спочатку",
                correct_answer="спочатку",
                distractors=(
                    AdverbDistractor(
                        text="з початку",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«З початку» окремо вживається тоді, коли є залежне слово (наприклад, з початку місяця), а часовий прислівник «спочатку» (заново, спершу) пишеться разом per § 41, п. 1.",
                        explanation_en="'З початку' separately is used with dependent words (from the beginning of the month); adverb 'anew/initially' is 'спочатку' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="с початку",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Префікс с- перед глухими приголосними пишеться разом у складі прислівника «спочатку» per § 41, п. 1.",
                        explanation_en="Prefix с- before voiceless consonants is fused in adverb 'спочатку' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="с-початку",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «спочатку» пишеться разом per § 41, п. 1, дефіс помилковий.",
                        explanation_en="Adverb 'спочатку' is written together per § 41, p. 1; hyphens are erroneous.",
                    ),
                ),
                rule_citation=cit_fused,
                rule_summary_ua=ua_fused,
                rule_summary_en=en_fused,
            ),
            AdverbCard(
                card_id="adverb_card_42",
                category=AdverbCategory.TOGETHER_FUSED,
                prompt="Молоді поети _______ познайомилися на літературному вечорі в Києві.",
                target_token="вперше",
                correct_answer="вперше",
                distractors=(
                    AdverbDistractor(
                        text="в перше",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«В перше» окремо вживається з числівником (поглянути в перше вікно), а часовий прислівник «вперше» пишеться разом per § 41, п. 1.",
                        explanation_en="'В перше' separately is used with numerals (look into the first window); time adverb 'for the first time' is 'вперше' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в-перше",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «вперше» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'вперше' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="по-вперше",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Форми «по-вперше» не існує; часовий прислівник «вперше» пишеться разом per § 41, п. 1 (не плутати зі вставним словом «по-перше» per § 41, п. 3, 2)).",
                        explanation_en="The form 'по-вперше' does not exist; temporal adverb 'вперше' is written together per § 41, p. 1 (not to be confused with introductory word 'по-перше' per § 41, p. 3, 2)).",
                    ),
                ),
                rule_citation=cit_fused,
                rule_summary_ua=ua_fused,
                rule_summary_en=en_fused,
            ),
            AdverbCard(
                card_id="adverb_card_43",
                category=AdverbCategory.TOGETHER_FUSED,
                prompt="Ображений хлопчик насупився й сердито подивився на перехожого _______.",
                target_token="спідлоба",
                correct_answer="спідлоба",
                distractors=(
                    AdverbDistractor(
                        text="спід-лоба",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник способу погляду «спідлоба» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb of gaze 'спідлоба' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="зпід лоба",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник способу дії пишеться разом: «спідлоба» per § 41, п. 1.",
                        explanation_en="Adverb of manner is written together: 'спідлоба' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="спід лоба",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Слово «спідлоба» пишеться разом як єдиний прислівник per § 41, п. 1.",
                        explanation_en="Word 'спідлоба' is spelled together as a single adverb per § 41, p. 1.",
                    ),
                ),
                rule_citation=cit_fused,
                rule_summary_ua=ua_fused,
                rule_summary_en=en_fused,
            ),
            AdverbCard(
                card_id="adverb_card_44",
                category=AdverbCategory.TOGETHER_FUSED,
                prompt="Маленька дівчинка стала _______, намагаючись дістати улюблену іграшку з полиці.",
                target_token="навшпиньки",
                correct_answer="навшпиньки",
                distractors=(
                    AdverbDistractor(
                        text="на вшпиньки",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник «навшпиньки» утворений від префіксів на-, в- та кореня шпинька і пишеться разом per § 41, п. 1.",
                        explanation_en="Adverb 'навшпиньки' is formed from prefixes на-, в- and base шпинька; written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-вшпиньки",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Дефіс у слові «навшпиньки» не пишеться; це складний прислівник, який пишеться разом per § 41, п. 1.",
                        explanation_en="No hyphen is used in 'навшпиньки'; it is a fused adverb written together per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на ципочки",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «стати на ципочки» є грубим русизмом («на цыпочки»); нормативний український вислів — «стати навшпиньки».",
                        explanation_en="'Стати на ципочки' is Russian interference; authentic Ukrainian is 'стати навшпиньки'.",
                    ),
                ),
                rule_citation=cit_fused,
                rule_summary_ua=ua_fused,
                rule_summary_en=en_fused,
            ),
            AdverbCard(
                card_id="adverb_card_45",
                category=AdverbCategory.TOGETHER_FUSED,
                prompt="Відчуваючи небезпеку в темному лісі, досвідчений мандрівник увесь час тримався _______, прислухаючись до кожного шурхоту.",
                target_token="насторожі",
                correct_answer="насторожі",
                distractors=(
                    AdverbDistractor(
                        text="по-сторожі",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Форма «по-сторожі» є штучною та ненормативною; стан пильності передається прислівником «насторожі», який пишеться разом per § 41, п. 1.",
                        explanation_en="The form 'по-сторожі' is artificial and non-normative; the state of alertness is expressed by the adverb 'насторожі', which is written as one word per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-сторожі",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Складний прислівник «насторожі» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="The compound adverb 'насторожі' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="всторожі",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Такої прислівникової форми не існує; нормативне слово зі значенням пильності — «насторожі» per § 41, п. 1.",
                        explanation_en="Such an adverbial form does not exist; normative word for alertness is 'насторожі' per § 41, p. 1.",
                    ),
                ),
                rule_citation=cit_fused,
                rule_summary_ua=ua_fused,
                rule_summary_en=en_fused,
            ),
        ]
    )

    # Category 10: Homophone Discrimination 1
    cit_hom1, ua_hom1, en_hom1 = resolve_homophone_1_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_46",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_1,
                prompt="Друзі подарували випускникові пам'ятний годинник _______ про шкільні роки.",
                target_token="на пам'ять",
                correct_answer="на пам'ять",
                distractors=(
                    AdverbDistractor(
                        text="напам'ять",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_ADVERB_CONFUSION,
                        explanation_ua="Тут вжито іменник «пам'ять» у значенні спогаду (подарувати на пам'ять про подію), тому прийменник пишеться окремо per § 41, п. 2; разом «напам'ять» пишеться лише про запам'ятовування тексту напам'ять.",
                        explanation_en="Here noun 'пам'ять' is used meaning keepsake/remembrance; preposition is written separately ('на пам'ять') per § 41, p. 2. Fused 'напам'ять' means reciting by heart.",
                    ),
                    AdverbDistractor(
                        text="на-пам'ять",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Дефіс у сполуці «на пам'ять» не вживається.",
                        explanation_en="Hyphens are never used in prepositional phrase 'на пам'ять'.",
                    ),
                    AdverbDistractor(
                        text="для пам'яті",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="Усталений український вираз для пам'ятного дарунку — «подарувати на пам'ять» (окремо).",
                        explanation_en="Established Ukrainian idiom for a keepsake gift is 'подарувати на пам'ять' (written separately).",
                    ),
                ),
                rule_citation=cit_hom1,
                rule_summary_ua=ua_hom1,
                rule_summary_en=en_hom1,
            ),
            AdverbCard(
                card_id="adverb_card_47",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_1,
                prompt="Актор за один вечір вивчив усю свою роль у п'єсі _______.",
                target_token="напам'ять",
                correct_answer="напам'ять",
                distractors=(
                    AdverbDistractor(
                        text="на пам'ять",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="Спосіб засвоєння тексту (як? напам'ять) виражається прислівником, що пишеться разом per § 41, п. 1; окремо «на пам'ять» пишеться тільки як іменникова сполука (подарувати на пам'ять).",
                        explanation_en="Manner of memorization ('by heart') is expressed by the fused adverb 'напам'ять' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-пам'ять",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «напам'ять» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'напам'ять' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="в пам'ять",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="«В пам'ять» пишеться окремо у значеннях вшанування («в пам'ять загиблих»), а не для способу вивчення тексту.",
                        explanation_en="'В пам'ять' is used in memorial contexts (in honor of), not for memorization.",
                    ),
                ),
                rule_citation=cit_hom1,
                rule_summary_ua=ua_hom1,
                rule_summary_en=en_hom1,
            ),
            AdverbCard(
                card_id="adverb_card_48",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_1,
                prompt="Усі родичі та друзі прийшли привітати ювіляра _______ його народження.",
                target_token="в день",
                correct_answer="в день",
                distractors=(
                    AdverbDistractor(
                        text="вдень",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_ADVERB_CONFUSION,
                        explanation_ua="Тут є конкретний іменник «день» із залежним родовим відмінком («день народження»), тому прийменник пишеться окремо per § 41, п. 2; разом «вдень» пишеться тільки прислівник на позначення світлої частини доби.",
                        explanation_en="Here noun 'день' has dependent Genitive ('день народження'), so preposition is written separately per § 41, p. 2; fused 'вдень' is strictly the temporal adverb for daytime.",
                    ),
                    AdverbDistractor(
                        text="в-день",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Іменник з прийменником «в день» пишеться окремо без дефіса.",
                        explanation_en="Noun with preposition 'в день' is written separately without a hyphen.",
                    ),
                    AdverbDistractor(
                        text="удень",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_ADVERB_CONFUSION,
                        explanation_ua="Форма «удень» є варіантом прислівника і не може керувати іменником «народження».",
                        explanation_en="'Удень' is an adverbial variant and cannot govern the genitive noun 'народження'.",
                    ),
                ),
                rule_citation=cit_hom1,
                rule_summary_ua=ua_hom1,
                rule_summary_en=en_hom1,
            ),
            AdverbCard(
                card_id="adverb_card_49",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_1,
                prompt="Будівельники активно працювали _______, поки світило яскраве сонце.",
                target_token="вдень",
                correct_answer="вдень",
                distractors=(
                    AdverbDistractor(
                        text="в день",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="Часовий прислівник (коли? вдень) пишеться разом per § 41, п. 1; окремо пишеться лише за наявності залежних слів (в день свята).",
                        explanation_en="Time adverb (when? in daytime) is written together per § 41, p. 1; separately only when modifying words are present.",
                    ),
                    AdverbDistractor(
                        text="в-день",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «вдень» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'вдень' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="у день",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="Сполука «у день» з прийменником пишеться окремо per § 41, п. 2, тоді як часовий прислівник «вдень» пишеться разом per § 41, п. 1.",
                        explanation_en="Prepositional phrase 'у день' is written separately per § 41, p. 2, while temporal adverb 'вдень' is written together per § 41, p. 1.",
                    ),
                ),
                rule_citation=cit_hom1,
                rule_summary_ua=ua_hom1,
                rule_summary_en=en_hom1,
            ),
            AdverbCard(
                card_id="adverb_card_50",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_1,
                prompt="Мандрівники пройшли крізь сад і підійшли _______ старовинної садиби.",
                target_token="до дому",
                correct_answer="до дому",
                distractors=(
                    AdverbDistractor(
                        text="додому",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_ADVERB_CONFUSION,
                        explanation_ua="Тут «до дому» вжито як прийменник з конкретним іменником чоловічого роду (будівлею), що має означення («старовинної садиби»), тому пишеться окремо per § 41, п. 2; прислівник «додому» означає своє помешкання й не має залежних іменників.",
                        explanation_en="Here 'до дому' is a preposition with a specific modified noun ('house of the estate'); fused 'додому' means one's own home without dependents per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="до-дому",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прийменник з іменником пишеться окремо без дефіса.",
                        explanation_en="Preposition with noun is written separately without a hyphen.",
                    ),
                    AdverbDistractor(
                        text="в дім",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="З дієсловом «підійти» нормативно вживається прийменник «до» («до дому»), а не «в».",
                        explanation_en="With verb 'підійти' the normative preposition is 'до' ('до дому'), not 'в'.",
                    ),
                ),
                rule_citation=cit_hom1,
                rule_summary_ua=ua_hom1,
                rule_summary_en=en_hom1,
            ),
        ]
    )

    # Category 11: Homophone Discrimination 2
    cit_hom2, ua_hom2, en_hom2 = resolve_homophone_2_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_51",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_2,
                prompt="Учні радісно закінчили уроки й поспішили _______ обідати.",
                target_token="додому",
                correct_answer="додому",
                distractors=(
                    AdverbDistractor(
                        text="до дому",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="Прислівник напрямку «куди? додому» (до свого житла) пишеться разом per § 41, п. 1; окремо «до дому» пишеться лише тоді, коли йдеться про конкретний будинок з означенням per § 41, п. 2.",
                        explanation_en="Directional adverb 'homewards' is written together per § 41, p. 1; separate 'до дому' applies only to a concrete building with modifiers per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="до-дому",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «додому» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'додому' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на дім",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «на дім» (наприклад, взяти завдання на дім) є русизмом; правильно — «додому».",
                        explanation_en="'На дім' is Russian interference; standard Ukrainian is 'додому'.",
                    ),
                ),
                rule_citation=cit_hom2,
                rule_summary_ua=ua_hom2,
                rule_summary_en=en_hom2,
            ),
            AdverbCard(
                card_id="adverb_card_52",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_2,
                prompt="Сноубордисти на великій швидкості спускалися _______ Говерли.",
                target_token="з гори",
                correct_answer="з гори",
                distractors=(
                    AdverbDistractor(
                        text="згори",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_ADVERB_CONFUSION,
                        explanation_ua="Тут є конкретний географічний об'єкт — гора («з гори Говерли»), тому прийменник «з» пишеться окремо від іменника per § 41, п. 2; разом «згори» пишеться тільки прислівник напрямку (дивитися згори вниз).",
                        explanation_en="Here is a concrete mountain ('from Mount Hoverla'), so preposition 'з' is separate per § 41, p. 2; fused 'згори' is strictly the directional adverb.",
                    ),
                    AdverbDistractor(
                        text="з-гори",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Іменник з прийменником «з гори» пишеться окремо без жодного дефіса.",
                        explanation_en="Noun with preposition 'з гори' is written separately without any hyphen.",
                    ),
                    AdverbDistractor(
                        text="ізгори",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Такої форми в українській мові немає; прислівник пишеться «згори» per § 41, п. 1, а іменник з прийменником — «з гори» або «із гори» окремо.",
                        explanation_en="Such a fused form does not exist; write adverb 'згори' or prepositional phrase 'із гори' separately.",
                    ),
                ),
                rule_citation=cit_hom2,
                rule_summary_ua=ua_hom2,
                rule_summary_en=en_hom2,
            ),
            AdverbCard(
                card_id="adverb_card_53",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_2,
                prompt="Орел кружляв у небі й пильно спостерігав за здобиччю _______ вниз.",
                target_token="згори",
                correct_answer="згори",
                distractors=(
                    AdverbDistractor(
                        text="з гори",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="Прислівник напрямку «звідки? згори» пишеться разом per § 41, п. 1, коли немає конкретного іменника (гори); окремо «з гори» пишеться лише про реальну височину per § 41, п. 2.",
                        explanation_en="Directional adverb 'from above' is written together per § 41, p. 1 when no physical mountain is referenced.",
                    ),
                    AdverbDistractor(
                        text="з-гори",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Прислівник «згори» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Adverb 'згори' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="зверхньо",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="Слово «зверхньо» означає зневажливе ставлення (як? гордовито), тоді як просторовий напрямок згори вниз передає «згори».",
                        explanation_en="'Зверхньо' means condescendingly/arrogantly, whereas spatial direction downwards is 'згори'.",
                    ),
                ),
                rule_citation=cit_hom2,
                rule_summary_ua=ua_hom2,
                rule_summary_en=en_hom2,
            ),
            AdverbCard(
                card_id="adverb_card_54",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_2,
                prompt="Письменник прийшов у книгарню _______ зі своїми юними читачами.",
                target_token="на зустріч",
                correct_answer="на зустріч",
                distractors=(
                    AdverbDistractor(
                        text="назустріч",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_ADVERB_CONFUSION,
                        explanation_ua="Тут маємо іменник «зустріч» (подія, захід) з означенням («зі своїми читачами»), тому прийменник пишеться окремо: «на зустріч» per § 41, п. 2; разом «назустріч» пишеться прислівник руху (йти назустріч вітру) per § 41, п. 1.",
                        explanation_en="Here noun 'зустріч' refers to an event with readers, so preposition is separate ('на зустріч') per § 41, p. 2; fused 'назустріч' is the directional adverb per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="на-зустріч",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Сполука прийменника з іменником «на зустріч» пишеться окремо без дефіса.",
                        explanation_en="Prepositional phrase 'на зустріч' is written separately without a hyphen.",
                    ),
                    AdverbDistractor(
                        text="до зустрічі",
                        interference_key=AdverbInterferenceKey.INCORRECT_QUESTION_CATEGORY,
                        explanation_ua="«До зустрічі» — це формула прощання, а не мета руху на запланований захід.",
                        explanation_en="'До зустрічі' is a parting farewell phrase, not a purpose of attending an event.",
                    ),
                ),
                rule_citation=cit_hom2,
                rule_summary_ua=ua_hom2,
                rule_summary_en=en_hom2,
            ),
            AdverbCard(
                card_id="adverb_card_55",
                category=AdverbCategory.HOMOPHONE_DISCRIMINATION_2,
                prompt="Маленьке цуценя радісно замахало хвостом і побігло _______ господарю.",
                target_token="назустріч",
                correct_answer="назустріч",
                distractors=(
                    AdverbDistractor(
                        text="на зустріч",
                        interference_key=AdverbInterferenceKey.HOMOPHONE_NOUN_PREP_CONFUSION,
                        explanation_ua="Прислівник/прийменниковий прислівник напрямку руху (куди? назустріч) пишеться разом per § 41, п. 1; окремо пишеться лише іменник події (іти на зустріч випускників) per § 41, п. 2.",
                        explanation_en="Directional adverb 'towards' is written together per § 41, p. 1; separate 'на зустріч' refers to an event/meeting per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="на-зустріч",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Слово «назустріч» пишеться разом без дефіса per § 41, п. 1.",
                        explanation_en="Word 'назустріч' is written together without a hyphen per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="встріч",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Слово «встріч» є архаїчним або діалектним; у сучасній літературній мові нормативним є «назустріч».",
                        explanation_en="'Встріч' is dialectal/archaic; standard literary Ukrainian uses 'назустріч'.",
                    ),
                ),
                rule_citation=cit_hom2,
                rule_summary_ua=ua_hom2,
                rule_summary_en=en_hom2,
            ),
        ]
    )

    # Category 12: Separate Prepositional Phrases
    cit_sep, ua_sep, en_sep = resolve_separate_phrases_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_56",
                category=AdverbCategory.SEPARATE_PHRASES,
                prompt="Ми, _______, не зможемо взяти участь у завтрашньому семінарі.",
                target_token="на жаль",
                correct_answer="на жаль",
                distractors=(
                    AdverbDistractor(
                        text="нажаль",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_FUSION,
                        explanation_ua="Прислівникове сполучення «на жаль» складається з прийменника та іменника й пишеться строго ОКРЕМО per § 41, п. 2; написання разом є поширеною помилкою.",
                        explanation_en="Phrase 'на жаль' consists of preposition + noun and is written strictly SEPARATELY per § 41, p. 2; fusing is a common error.",
                    ),
                    AdverbDistractor(
                        text="на-жаль",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="У сполуці «на жаль» дефіс заборонено; слова пишуться окремо per § 41, п. 2.",
                        explanation_en="Hyphen is prohibited in 'на жаль'; words are written separately per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="к жалю",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «к жалю» є грубою калькою з російської («к сожалению»); нормативне українське вставне сполучення — «на жаль».",
                        explanation_en="'К жалю' is a Russian calque ('к сожалению'); standard Ukrainian parenthetical phrase is 'на жаль'.",
                    ),
                ),
                rule_citation=cit_sep,
                rule_summary_ua=ua_sep,
                rule_summary_en=en_sep,
            ),
            AdverbCard(
                card_id="adverb_card_57",
                category=AdverbCategory.SEPARATE_PHRASES,
                prompt="Ця нова інформація, _______, виявилася надзвичайно корисною для нашого звіту.",
                target_token="до речі",
                correct_answer="до речі",
                distractors=(
                    AdverbDistractor(
                        text="доречі",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_FUSION,
                        explanation_ua="Прислівникове сполучення «до речі» пишеться завжди ОКРЕМО per § 41, п. 2; написання разом є грубою орфографічною помилкою.",
                        explanation_en="Adverbial phrase 'до речі' is always written SEPARATELY per § 41, p. 2; fusing is an orthographic error.",
                    ),
                    AdverbDistractor(
                        text="до-речі",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Сполучення «до речі» пишеться окремо без дефіса per § 41, п. 2.",
                        explanation_en="Phrase 'до речі' is written separately without a hyphen per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="к речі",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «к речі» є калькою з російської («кстати / к слову»); літературна українська норма — «до речі».",
                        explanation_en="'К речі' is a Russian calque; literary Ukrainian standard is 'до речі'.",
                    ),
                ),
                rule_citation=cit_sep,
                rule_summary_ua=ua_sep,
                rule_summary_en=en_sep,
            ),
            AdverbCard(
                card_id="adverb_card_58",
                category=AdverbCategory.SEPARATE_PHRASES,
                prompt="Це відкриття, _______, здійснить справжній прорив у сучасній медицині.",
                target_token="без сумніву",
                correct_answer="без сумніву",
                distractors=(
                    AdverbDistractor(
                        text="безсумніву",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_FUSION,
                        explanation_ua="Прислівникове сполучення з прийменником «без сумніву» пишеться ОКРЕМО per § 41, п. 2.",
                        explanation_en="Adverbial prepositional phrase 'без сумніву' is written SEPARATELY per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="без-сумніву",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="У сполуці «без сумніву» дефіс не ставиться; слова пишуться окремо per § 41, п. 2.",
                        explanation_en="No hyphen in 'без сумніву'; words are spelled separately per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="безспорно",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Слово «безспорно» є калькою з російської («бесспорно»); нормативні українські вирази — «без сумніву» або «безперечно».",
                        explanation_en="'Безспорно' is a Russian calque; standard Ukrainian uses 'без сумніву' or 'безперечно'.",
                    ),
                ),
                rule_citation=cit_sep,
                rule_summary_ua=ua_sep,
                rule_summary_en=en_sep,
            ),
            AdverbCard(
                card_id="adverb_card_59",
                category=AdverbCategory.SEPARATE_PHRASES,
                prompt="Він наполегливо працював над картиною _______ протягом багатьох місяців.",
                target_token="день у день",
                correct_answer="день у день",
                distractors=(
                    AdverbDistractor(
                        text="день-у-день",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Сполучення двох однакових іменників з прийменником між ними пишуться ОКРЕМО per § 41, п. 2 (день у день, раз у раз, сам на сам).",
                        explanation_en="Repetitions of identical nouns with preposition between them are written SEPARATELY per § 41, p. 2 (день у день, раз у раз).",
                    ),
                    AdverbDistractor(
                        text="день удень",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_FUSION,
                        explanation_ua="Обидва іменники пишуться окремо від прийменника: «день у день» per § 41, п. 2.",
                        explanation_en="Both nouns are written separately from preposition: 'день у день' per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="день в день",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Використання прийменника «в» замість «у» між приголосними є порушенням милозвучності та калькою («день в день»); правильно — «день у день».",
                        explanation_en="Using 'в' instead of 'у' between consonants violates euphony; standard is 'день у день'.",
                    ),
                ),
                rule_citation=cit_sep,
                rule_summary_ua=ua_sep,
                rule_summary_en=en_sep,
            ),
            AdverbCard(
                card_id="adverb_card_60",
                category=AdverbCategory.SEPARATE_PHRASES,
                prompt="Наприкінці уроку вчитель усміхнувся учням і промовив: «_______!».",
                target_token="до побачення",
                correct_answer="до побачення",
                distractors=(
                    AdverbDistractor(
                        text="допобачення",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_FUSION,
                        explanation_ua="Етикетний вираз «до побачення» складається з прийменника та віддієслівного іменника й пишеться ОКРЕМО per § 41, п. 2.",
                        explanation_en="Etiquette formula 'до побачення' consists of preposition + verbal noun and is written SEPARATELY per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="до-побачення",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="У виразі «до побачення» дефіс не вживається; слова пишуться окремо per § 41, п. 2.",
                        explanation_en="Hyphens are not used in 'до побачення'; words are written separately per § 41, p. 2.",
                    ),
                    AdverbDistractor(
                        text="давай до побачення",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Зворот «давай до побачення» є розмовним суржиком; нормативна формула прощання — «до побачення» або «на все добре».",
                        explanation_en="'Давай до побачення' is colloquial Surzhyk; standard farewell is 'до побачення'.",
                    ),
                ),
                rule_citation=cit_sep,
                rule_summary_ua=ua_sep,
                rule_summary_en=en_sep,
            ),
        ]
    )

    # Category 13: Comparison Synthetic
    cit_comp, ua_comp, en_comp = resolve_comparison_synthetic_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_61",
                category=AdverbCategory.COMPARISON_SYNTHETIC,
                prompt="Новий швидкісний потяг мчить значно _______ за старий приміський автобус.",
                target_token="швидше",
                correct_answer="швидше",
                distractors=(
                    AdverbDistractor(
                        text="більш швидше",
                        interference_key=AdverbInterferenceKey.COMPARATIVE_COMPOUND_CALQUE,
                        explanation_ua="Поєднання слова «більш» із простою формою вищого ступеня («більш швидше») є грубою граматичною помилкою; слід уживати або просту форму «швидше», або складену «більш швидко» per § 20.",
                        explanation_en="Combining 'більш' with simple comparative ('більш швидше') is a grammatical error; use either simple 'швидше' or compound 'більш швидко' per § 20.",
                    ),
                    AdverbDistractor(
                        text="швидкіше",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Від прикметника «швидкий» нормативна проста форма вищого ступеня утворюється за допомогою суфікса -ше: «швидше», а не -іше per § 20.",
                        explanation_en="From 'швидкий' standard comparative takes suffix -ше: 'швидше', not -іше per § 20.",
                    ),
                    AdverbDistractor(
                        text="самий швидко",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Слово «самий» є калькою з російської; в українській мові ступені порівняння утворюються суфіксами або префіксом най-.",
                        explanation_en="Word 'самий' is a Russian calque; Ukrainian degrees of comparison are formed via suffixes or prefix най-.",
                    ),
                ),
                rule_citation=cit_comp,
                rule_summary_ua=ua_comp,
                rule_summary_en=en_comp,
            ),
            AdverbCard(
                card_id="adverb_card_62",
                category=AdverbCategory.COMPARISON_SYNTHETIC,
                prompt="Завдяки щоденним репетиціям актор зіграв прем'єрну виставу значно _______.",
                target_token="краще",
                correct_answer="краще",
                distractors=(
                    AdverbDistractor(
                        text="більш краще",
                        interference_key=AdverbInterferenceKey.COMPARATIVE_COMPOUND_CALQUE,
                        explanation_ua="Поєднання слова «більш» із простою формою вищого ступеня («більш краще») є грубою граматичною помилкою; слід уживати або просту форму «краще», або «більш якісно» per § 20.",
                        explanation_en="Combining 'більш' with synthetic comparative ('більш краще') is a gross error; use simple 'краще' or 'більш якісно' per § 20.",
                    ),
                    AdverbDistractor(
                        text="самий краще",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Конструкція зі словом «самий» є суржиком і калькою з російської («самый лучше»); в українській мові вживають суплетивну форму «краще» або «найкраще».",
                        explanation_en="Using 'самий' is Russian calque ('самый лучше'); Ukrainian uses suppletive 'краще' or superlative 'найкраще'.",
                    ),
                    AdverbDistractor(
                        text="лучче",
                        interference_key=AdverbInterferenceKey.COMPARATIVE_RUSSIAN_SUFFIX,
                        explanation_ua="Форма «лучче» є ненормативним просторіччям або суржиком; літературна суплетивна форма — «краще».",
                        explanation_en="Form 'лучче' is dialectal/Surzhyk; standard literary form is 'краще'.",
                    ),
                ),
                rule_citation=cit_comp,
                rule_summary_ua=ua_comp,
                rule_summary_en=en_comp,
            ),
            AdverbCard(
                card_id="adverb_card_63",
                category=AdverbCategory.COMPARISON_SYNTHETIC,
                prompt="Хворий проігнорував поради лікаря, тому наступного ранку почувався ще _______.",
                target_token="гірше",
                correct_answer="гірше",
                distractors=(
                    AdverbDistractor(
                        text="більш гірше",
                        interference_key=AdverbInterferenceKey.COMPARATIVE_COMPOUND_CALQUE,
                        explanation_ua="Змішування аналітичної та синтетичної форм («більш гірше») суворо заборонено граматикою; правильно — «гірше» per § 20.",
                        explanation_en="Mixing analytic and synthetic comparative forms ('більш гірше') is prohibited; correct is 'гірше' per § 20.",
                    ),
                    AdverbDistractor(
                        text="самий гірше",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Слово «самий» не вживається для ступенювання українських прислівників.",
                        explanation_en="Word 'самий' is not used for Ukrainian adverb degree comparison.",
                    ),
                    AdverbDistractor(
                        text="хужче",
                        interference_key=AdverbInterferenceKey.COMPARATIVE_RUSSIAN_SUFFIX,
                        explanation_ua="Форма «хужче» є суржиком від російського «хуже»; літературний суплетивний вищий ступінь від «погано» — «гірше».",
                        explanation_en="'Хужче' is Russian interference ('хуже'); literary suppletive comparative from 'погано' is 'гірше'.",
                    ),
                ),
                rule_citation=cit_comp,
                rule_summary_ua=ua_comp,
                rule_summary_en=en_comp,
            ),
            AdverbCard(
                card_id="adverb_card_64",
                category=AdverbCategory.COMPARISON_SYNTHETIC,
                prompt="Досвідчений аквалангіст обережно занурився _______ у морські глибини.",
                target_token="глибше",
                correct_answer="глибше",
                distractors=(
                    AdverbDistractor(
                        text="глибокіше",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="При утворенні вищого ступеня суфікс -ок- випадає: глибокий -> глибше (а не «глибокіше») per § 20.",
                        explanation_en="In forming the comparative suffix -ок- drops: глибокий -> глибше (not 'глибокіше') per § 20.",
                    ),
                    AdverbDistractor(
                        text="більш глибше",
                        interference_key=AdverbInterferenceKey.COMPARATIVE_COMPOUND_CALQUE,
                        explanation_ua="Поєднання «більш» з синтетичною формою «глибше» є плеонастичною граматичною помилкою.",
                        explanation_en="Combining 'більш' with synthetic 'глибше' is a redundant grammatical error.",
                    ),
                    AdverbDistractor(
                        text="самий глибоко",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Кальковане поєднання «самий глибоко» є неприпустимим; нормативна форма — «глибше».",
                        explanation_en="Calque 'самий глибоко' is unacceptable in Ukrainian; standard comparative is 'глибше'.",
                    ),
                ),
                rule_citation=cit_comp,
                rule_summary_ua=ua_comp,
                rule_summary_en=en_comp,
            ),
            AdverbCard(
                card_id="adverb_card_65",
                category=AdverbCategory.COMPARISON_SYNTHETIC,
                prompt="Коли засяяло весняне сонце, надворі стало значно _______.",
                target_token="тепліше",
                correct_answer="тепліше",
                distractors=(
                    AdverbDistractor(
                        text="більш тепліше",
                        interference_key=AdverbInterferenceKey.COMPARATIVE_COMPOUND_CALQUE,
                        explanation_ua="Змішування слова «більш» з формою вищого ступеня («більш тепліше») є помилкою; правильно — «тепліше» per § 20.",
                        explanation_en="Mixing 'більш' with comparative form ('більш тепліше') is an error; correct is 'тепліше' per § 20.",
                    ),
                    AdverbDistractor(
                        text="теплійо",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Такої форми в українській мові немає; вищий ступінь від «тепло» утворюється суфіксом -іше: «тепліше» per § 20.",
                        explanation_en="Such a form does not exist; comparative from 'тепло' takes suffix -іше: 'тепліше' per § 20.",
                    ),
                    AdverbDistractor(
                        text="самий тепліше",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Калька з російської; слово «самий» для вираження порівняння не вживається.",
                        explanation_en="Russian calque; word 'самий' is not used for comparison.",
                    ),
                ),
                rule_citation=cit_comp,
                rule_summary_ua=ua_comp,
                rule_summary_en=en_comp,
            ),
        ]
    )

    # Category 14: Comparison Superlative
    cit_sup, ua_sup, en_sup = resolve_comparison_superlative_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_66",
                category=AdverbCategory.COMPARISON_SUPERLATIVE,
                prompt="Серед усіх конкурсантів вона виконала складну фортепіанну сонату _______.",
                target_token="найкраще",
                correct_answer="найкраще",
                distractors=(
                    AdverbDistractor(
                        text="самий краще",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Формування найвищого ступеня за допомогою частки «самий» («самий краще») є грубим суржиком; нормативна українська форма має префікс най-: «найкраще» per § 20.",
                        explanation_en="Forming the superlative with 'самий' is Surzhyk; standard Ukrainian uses prefix най-: 'найкраще' per § 20.",
                    ),
                    AdverbDistractor(
                        text="най краще",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Префікс най- у найвищому ступені прислівників завжди пишеться РАЗОМ із словом per § 20 (найкраще, найшвидше).",
                        explanation_en="Prefix най- in superlative adverbs is always written TOGETHER per § 20 (найкраще).",
                    ),
                    AdverbDistractor(
                        text="най-краще",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_HYPHEN_ERROR,
                        explanation_ua="Префікс най- приєднується без дефіса; написання разом є обов'язковим per § 20.",
                        explanation_en="Prefix най- attaches without a hyphen; fused spelling is mandatory per § 20.",
                    ),
                ),
                rule_citation=cit_sup,
                rule_summary_ua=ua_sup,
                rule_summary_en=en_sup,
            ),
            AdverbCard(
                card_id="adverb_card_67",
                category=AdverbCategory.COMPARISON_SUPERLATIVE,
                prompt="Керівник попросив команду передати термінові документи замовнику _______.",
                target_token="якнайшвидше",
                correct_answer="якнайшвидше",
                distractors=(
                    AdverbDistractor(
                        text="як найшвидше",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Підсилювальні частки як- та що- у складі найвищого ступеня порівняння пишуться РАЗОМ per § 20 (якнайшвидше, щонайдовше).",
                        explanation_en="Intensifying particles як- and що- in superlatives are written TOGETHER per § 20 (якнайшвидше).",
                    ),
                    AdverbDistractor(
                        text="як-найшвидше",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_HYPHEN_ERROR,
                        explanation_ua="Дефіс між часткою як- і префіксом най- не ставиться; слово пишеться повністю разом per § 20.",
                        explanation_en="No hyphen between particle як- and prefix най-; the word is spelled completely together per § 20.",
                    ),
                    AdverbDistractor(
                        text="самий швидше",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Слово «самий» є російською калькою; в українській мові найвищий ступінь утворюється за допомогою префікса най- та підсилення як-: «якнайшвидше» per § 20.",
                        explanation_en="Word 'самий' is a Russian calque; Ukrainian superlatives are formed with prefix най- and intensifier як-: 'якнайшвидше' per § 20.",
                    ),
                ),
                rule_citation=cit_sup,
                rule_summary_ua=ua_sup,
                rule_summary_en=en_sup,
            ),
            AdverbCard(
                card_id="adverb_card_68",
                category=AdverbCategory.COMPARISON_SUPERLATIVE,
                prompt="Музейні реставратори намагалися зберегти стародавній манускрипт _______.",
                target_token="щонайдовше",
                correct_answer="щонайдовше",
                distractors=(
                    AdverbDistractor(
                        text="що найдовше",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Підсилювальна частка що- з формою найвищого ступеня пишеться разом per § 20: «щонайдовше».",
                        explanation_en="Intensifying particle що- with superlative form is written together per § 20: 'щонайдовше'.",
                    ),
                    AdverbDistractor(
                        text="що-найдовше",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_HYPHEN_ERROR,
                        explanation_ua="Дефіс після частки що- є помилкою; слово пишеться разом per § 20.",
                        explanation_en="Hyphen after particle що- is an error; the word is spelled together per § 20.",
                    ),
                    AdverbDistractor(
                        text="самий довше",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Калька з російської («самый дольше»); нормативна українська мова вимагає префікса най- з підсиленням що-: «щонайдовше» per § 20.",
                        explanation_en="Russian calque ('самый дольше'); standard Ukrainian requires prefix най- with що-: 'щонайдовше' per § 20.",
                    ),
                ),
                rule_citation=cit_sup,
                rule_summary_ua=ua_sup,
                rule_summary_en=en_sup,
            ),
            AdverbCard(
                card_id="adverb_card_69",
                category=AdverbCategory.COMPARISON_SUPERLATIVE,
                prompt="Гірський беркут змахнув могутніми крилами й піднявся _______ серед усіх птахів.",
                target_token="найвище",
                correct_answer="найвище",
                distractors=(
                    AdverbDistractor(
                        text="самий вище",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Слово «самий» не використовується для утворення найвищого ступеня; правильно — «найвище» per § 20.",
                        explanation_en="Word 'самий' is not used for superlative formation; correct is 'найвище' per § 20.",
                    ),
                    AdverbDistractor(
                        text="най вище",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Префікс най- пишеться разом із прислівником per § 20.",
                        explanation_en="Prefix най- is written together with the adverb per § 20.",
                    ),
                    AdverbDistractor(
                        text="най-вище",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_HYPHEN_ERROR,
                        explanation_ua="Дефіс у префіксі най- заборонений; слово пишеться разом per § 20.",
                        explanation_en="Hyphen in prefix най- is prohibited; it is written as one word per § 20.",
                    ),
                ),
                rule_citation=cit_sup,
                rule_summary_ua=ua_sup,
                rule_summary_en=en_sup,
            ),
            AdverbCard(
                card_id="adverb_card_70",
                category=AdverbCategory.COMPARISON_SUPERLATIVE,
                prompt="Перед запуском ракети інженери перевірили кожну деталь двигуна _______.",
                target_token="якнайретельніше",
                correct_answer="якнайретельніше",
                distractors=(
                    AdverbDistractor(
                        text="як найретельніше",
                        interference_key=AdverbInterferenceKey.HYPHEN_SEPARATION,
                        explanation_ua="Частка як- із префіксом най- пишеться разом: «якнайретельніше» per § 20.",
                        explanation_en="Particle як- with prefix най- is written together: 'якнайретельніше' per § 20.",
                    ),
                    AdverbDistractor(
                        text="як-найретельніше",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_HYPHEN_ERROR,
                        explanation_ua="Написання через дефіс є орфографічною помилкою; слово пишеться разом per § 20.",
                        explanation_en="Hyphenated spelling is an orthographic error; the word is written together per § 20.",
                    ),
                    AdverbDistractor(
                        text="самий ретельно",
                        interference_key=AdverbInterferenceKey.SUPERLATIVE_CALQUE_SAMYI,
                        explanation_ua="Кальковане поєднання «самий ретельно» є неприпустимим в українській мові; норма — «якнайретельніше» per § 20.",
                        explanation_en="'Самий ретельно' is an unacceptable calque; standard Ukrainian is 'якнайретельніше' per § 20.",
                    ),
                ),
                rule_citation=cit_sup,
                rule_summary_ua=ua_sup,
                rule_summary_en=en_sup,
            ),
        ]
    )

    # Category 15: Anti-Calque Adverbials
    cit_calque, ua_calque, en_calque = resolve_anti_calque_rule()
    cards.extend(
        [
            AdverbCard(
                card_id="adverb_card_71",
                category=AdverbCategory.ANTI_CALQUE,
                prompt="Перед початком зборів слід _______ узгодити порядок денний і регламент.",
                target_token="насамперед",
                correct_answer="насамперед",
                distractors=(
                    AdverbDistractor(
                        text="в першу чергу",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «в першу чергу» є типовою калькою з російської («в первую очередь»); нормативні українські відповідники — «насамперед», «передусім», «найперше».",
                        explanation_en="'В першу чергу' is a Russian calque ('в первую очередь'); standard Ukrainian equivalents are 'насамперед', 'передусім'.",
                    ),
                    AdverbDistractor(
                        text="першим ділом",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Калька з російського «первым делом»; літературною нормою є прислівник «насамперед».",
                        explanation_en="Calque of Russian 'первым делом'; literary norm is adverb 'насамперед'.",
                    ),
                    AdverbDistractor(
                        text="на сам перед",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Прислівник «насамперед» є зрощеним і пишеться разом per § 41, п. 1.",
                        explanation_en="Adverb 'насамперед' is fused and written together per § 41, p. 1.",
                    ),
                ),
                rule_citation=cit_calque,
                rule_summary_ua=ua_calque,
                rule_summary_en=en_calque,
            ),
            AdverbCard(
                card_id="adverb_card_72",
                category=AdverbCategory.ANTI_CALQUE,
                prompt="Він _______ погодиться на цю невигідну й ризиковану пропозицію.",
                target_token="навряд чи",
                correct_answer="навряд чи",
                distractors=(
                    AdverbDistractor(
                        text="вряд ли",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Сполука «вряд ли» є прямим російським виразом; нормативний український відповідник — «навряд чи».",
                        explanation_en="'Вряд ли' is direct Russian vocabulary; standard Ukrainian equivalent is 'навряд чи'.",
                    ),
                    AdverbDistractor(
                        text="наврядчи",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_FUSION,
                        explanation_ua="Частка «чи» після прислівника «навряд» пишеться ОКРЕМО: «навряд чи».",
                        explanation_en="Particle 'чи' after adverb 'навряд' is written SEPARATELY: 'навряд чи'.",
                    ),
                    AdverbDistractor(
                        text="навряд-чи",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_HYPHEN,
                        explanation_ua="Частка «чи» не приєднується через дефіс; вона пишеться окремо.",
                        explanation_en="Particle 'чи' does not attach via hyphen; it is written separately.",
                    ),
                ),
                rule_citation=cit_calque,
                rule_summary_ua=ua_calque,
                rule_summary_en=en_calque,
            ),
            AdverbCard(
                card_id="adverb_card_73",
                category=AdverbCategory.ANTI_CALQUE,
                prompt="Учасники наукового круглого столу спілкувалися _______ українською мовою.",
                target_token="переважно",
                correct_answer="переважно",
                distractors=(
                    AdverbDistractor(
                        text="по-переважно",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Форма «по-переважно» є штучною та ненормативною; якісно-означальний прислівник вживається без префікса: «переважно» per § 41, п. 1.",
                        explanation_en="The form 'по-переважно' is artificial and non-normative; the qualitative adverb is used without a prefix: 'переважно' per § 41, p. 1.",
                    ),
                    AdverbDistractor(
                        text="по більшій мірі",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Калька з російського «по большей части / мере»; правильно — «переважно» або «здебільшого».",
                        explanation_en="Calque of Russian 'по большей части'; correct is 'переважно' or 'здебільшого'.",
                    ),
                    AdverbDistractor(
                        text="главним образом",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Грубий суржик від російського «главным образом»; нормативне слово — «переважно».",
                        explanation_en="Gross Surzhyk from Russian 'главным образом'; standard Ukrainian word is 'переважно'.",
                    ),
                ),
                rule_citation=cit_calque,
                rule_summary_ua=ua_calque,
                rule_summary_en=en_calque,
            ),
            AdverbCard(
                card_id="adverb_card_74",
                category=AdverbCategory.ANTI_CALQUE,
                prompt="Ти повинен уважно прочитати й законспектувати _______ перший розділ підручника.",
                target_token="принаймні",
                correct_answer="принаймні",
                distractors=(
                    AdverbDistractor(
                        text="по крайній мірі",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «по крайній мірі» є поширеною калькою з російської («по крайней мере»); нормативні українські слова — «принаймні», «щонайменше», «хоча б».",
                        explanation_en="'По крайній мірі' is a common Russian calque ('по крайней мере'); standard Ukrainian words are 'принаймні', 'щонайменше'.",
                    ),
                    AdverbDistractor(
                        text="при наймні",
                        interference_key=AdverbInterferenceKey.UNWARRANTED_SEPARATION,
                        explanation_ua="Слово «принаймні» є цілісним прислівником і пишеться разом.",
                        explanation_en="Word 'принаймні' is an integral adverb and is written as one word.",
                    ),
                    AdverbDistractor(
                        text="принаймі",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Форма «принаймі» без літери «н» є орфографічною помилкою; правильне написання — «принаймні».",
                        explanation_en="Form 'принаймі' lacking letter 'н' is an orthographic error; correct spelling is 'принаймні'.",
                    ),
                ),
                rule_citation=cit_calque,
                rule_summary_ua=ua_calque,
                rule_summary_en=en_calque,
            ),
            AdverbCard(
                card_id="adverb_card_75",
                category=AdverbCategory.ANTI_CALQUE,
                prompt="Якщо потяг затримається, _______ ми візьмемо таксі на вокзалі.",
                target_token="у крайньому разі",
                correct_answer="у крайньому разі",
                distractors=(
                    AdverbDistractor(
                        text="в крайньому випадку",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Словосполучення «в крайньому випадку» є калькою з російської («в крайнем случае»); літературною нормою для вираження вибору за крайніх обставин є «у крайньому разі».",
                        explanation_en="'В крайньому випадку' is a Russian calque ('в крайнем случае'); the literary standard for last-resort choice is 'у крайньому разі'.",
                    ),
                    AdverbDistractor(
                        text="на крайній случай",
                        interference_key=AdverbInterferenceKey.RUSSIANISM_CALQUE,
                        explanation_ua="Вираз «на крайній случай» є суржиком із російським коренем «случай»; нормативний український зворот — «у крайньому разі».",
                        explanation_en="'На крайній случай' is Surzhyk with the Russian root 'случай'; standard Ukrainian uses 'у крайньому разі'.",
                    ),
                    AdverbDistractor(
                        text="по-крайньому",
                        interference_key=AdverbInterferenceKey.CORRUPTED_ADVERB_FORM,
                        explanation_ua="Штучна форма «по-крайньому» не існує в українській мові; прислівниковий зворот крайньої можливості вживається окремо: «у крайньому разі».",
                        explanation_en="The artificial form 'по-крайньому' does not exist in Ukrainian; the adverbial phrase of last resort is 'у крайньому разі'.",
                    ),
                ),
                rule_citation=cit_calque,
                rule_summary_ua=ua_calque,
                rule_summary_en=en_calque,
            ),
        ]
    )

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


def verify_deck_with_vesum(cards: list[AdverbCard], vesum_db_path: Path | str | None = None) -> dict[str, Any]:
    """Verify that all target vocabulary exists in VESUM and that every card contributes valid vocabulary."""
    import re

    resolved_path = find_vesum_db(Path(vesum_db_path) if vesum_db_path else None)
    if not resolved_path.exists() or resolved_path.stat().st_size < 1_000_000:
        return {
            "total_cards": len(cards),
            "target_tokens_count": 0,
            "missing_targets": [],
            "empty_cards": [],
            "distractor_tokens_count": 0,
            "vesum_verified": None,
            "status": "skipped",
            "message": f"VESUM database not found or incomplete at {resolved_path}",
        }

    conn = sqlite3.connect(str(resolved_path))
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='forms_all'")
    if not cursor.fetchone():
        conn.close()
        return {
            "total_cards": len(cards),
            "target_tokens_count": 0,
            "missing_targets": [],
            "empty_cards": [],
            "distractor_tokens_count": 0,
            "vesum_verified": None,
            "status": "skipped",
            "message": f"forms_all table not found in VESUM database at {resolved_path}",
        }

    word_pattern = re.compile(r"^[а-яіїєґА-ЯІЇЄҐ'\-]+$")
    strip_punctuation = ".,!?:;—…\"'«»`()[]"

    all_target_tokens: set[str] = set()
    missing_targets: list[str] = []
    empty_cards: list[str] = []
    card_tokens_map: dict[str, list[str]] = {}

    for card in cards:
        raw_tokens = card.correct_answer.split()
        valid_tokens_for_card: list[str] = []
        for w in raw_tokens:
            clean = w.strip(strip_punctuation).lower().replace("’", "'").replace("`", "'")
            if not clean:
                continue
            if not word_pattern.match(clean):
                missing_targets.append(f"{card.card_id}: malformed token '{clean}'")
                continue
            valid_tokens_for_card.append(clean)
            all_target_tokens.add(clean)

        if not valid_tokens_for_card:
            empty_cards.append(card.card_id)
            missing_targets.append(
                f"{card.card_id}: no valid vocabulary tokens in correct_answer '{card.correct_answer}'"
            )
        else:
            card_tokens_map[card.card_id] = valid_tokens_for_card

    # Verify each unique valid token in VESUM
    unattested_tokens: set[str] = set()
    for token in sorted(all_target_tokens):
        cursor.execute("SELECT 1 FROM forms_all WHERE word_form = ? LIMIT 1", (token,))
        if not cursor.fetchone():
            unattested_tokens.add(token)

    conn.close()

    if unattested_tokens:
        for card_id, tokens in card_tokens_map.items():
            for tok in tokens:
                if tok in unattested_tokens:
                    missing_targets.append(f"{card_id}: token '{tok}' not found in VESUM")

    # A deck passes IF AND ONLY IF:
    # 1. There are cards
    # 2. No card had empty/punctuation-only answer
    # 3. No token was missing or malformed
    # 4. At least one target token was checked
    total_valid = len(cards) > 0 and len(empty_cards) == 0 and len(missing_targets) == 0 and len(all_target_tokens) > 0

    return {
        "total_cards": len(cards),
        "target_tokens_count": len(all_target_tokens),
        "missing_targets": missing_targets,
        "empty_cards": empty_cards,
        "vesum_verified": total_valid,
        "status": "passed" if total_valid else "failed",
    }


def export_deck(cards: list[AdverbCard], target_path: Path | str) -> dict[str, Any]:
    """Serializes canonical adverb practice cards to JSON."""
    deck_cards = []

    for card in cards:
        deck_cards.append(
            {
                "id": card.card_id,
                "category": card.category.value,
                "prompt": card.prompt,
                "target_token": card.target_token,
                "correct_answer": card.correct_answer,
                "options": card.all_options(),
                "distractors": [
                    {
                        "text": d.text,
                        "interference_key": d.interference_key.value,
                        "explanation": {
                            "ua": d.explanation_ua,
                            "en": d.explanation_en,
                        },
                    }
                    for d in card.distractors
                ],
                "rule_citation": card.rule_citation,
                "rule_summary": {
                    "ua": card.rule_summary_ua,
                    "en": card.rule_summary_en,
                },
            }
        )

    payload = {
        "schema_version": "1.0",
        "title": "Практикум: Глибока механіка прислівника (Правопис, омоніми, ступені порівняння, антикальки)",
        "card_count": len(deck_cards),
        "categories": [c.value for c in AdverbCategory],
        "cards": deck_cards,
    }

    out_file = Path(target_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Adverb Deep Mechanics Practice Engine")
    parser.add_argument("--verify-vesum", action="store_true", help="Verify targets against VESUM")
    parser.add_argument("--export", action="store_true", help="Export canonical JSON deck")
    parser.add_argument("--output", type=str, default="data/practice/adverb_mechanics_deck.json", help="Output path")
    parser.add_argument("--json", action="store_true", help="Output JSON results to stdout")
    args = parser.parse_args()

    cards = build_canonical_adverb_cards()

    if args.verify_vesum:
        res = verify_deck_with_vesum(cards)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"Cards: {res['total_cards']}, Target tokens: {res['target_tokens_count']}")
            print(f"Missing targets: {len(res['missing_targets'])}")
            if res.get("status") == "skipped":
                print(f"VESUM verification: SKIPPED ({res.get('message', 'VESUM database unavailable')})")
            elif res["missing_targets"]:
                print("Missing:", res["missing_targets"])
            else:
                print("VESUM verification: PASSED (100% target coverage)")
        if res.get("status") == "skipped" or res["missing_targets"] or not res.get("vesum_verified", False):
            sys.exit(1)

    if args.export:
        out_path = Path(args.output) if Path(args.output).is_absolute() else PROJECT_ROOT / args.output
        payload = export_deck(cards, out_path)
        print(f"Successfully exported {payload['card_count']} cards to {args.output}")


if __name__ == "__main__":
    main()
