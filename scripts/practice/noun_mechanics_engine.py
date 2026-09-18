"""Ukrainian Noun Deep Mechanics Practice Engine (Іменник).

Implements Ukrainian Pravopys 2019 (§§ 68, 73, 80, 82, 87) and Academic Grammar rules for:
  1. II Declension Genitive Singular Endings (-а/-я vs -у/-ю) [Правопис 2019 § 82]:
     - § 82, п. 1 (-а/-я):
       * 1.1: Beings, persons, animals (студента, вовка, коня, вчителя).
       * 1.2: Concrete countable items, tools, furniture (стола, ножа, олівця, трактора).
       * 1.3: Settlements, cities, towns (Києва, Львова, Харкова, Парижа).
       * 1.4: Units of measure, currency, months, days of week (метра, кілограма, долара, січня, понеділка).
     - § 82, п. 2 (-у/-ю):
       * 2.1: Materials, substances, mass terms (цукру, піску, меду, кисню, чаю).
       * 2.2: Collective nouns, groups (лісу, народу, полку, хору, оркестру).
       * 2.3: Buildings, institutions, premises (університету, театру, вокзалу, заводу).
       * 2.4: Abstract concepts, states, processes, illnesses, phenomena (розвитку, болю, прогресу, грипу, дощу).
       * 2.5: Geographical areas, countries, regions, rivers (Криму, Кавказу, Донбасу, Китаю).
     - § 82, п. 3: Semantic homonym pairs distinguishing meaning:
       * каменя (individual stone) vs каменю (material/rock).
       * листопада (month of November) vs листопаду (autumn leaf-fall).
       * апарата (physical instrument) vs апарату (administrative organ).
       * папера (official document/security) vs паперу (paper material).
       * акта (document/decree) vs акту (action/theatrical act).
       * терміна (specialized scientific term) vs терміну (deadline/time period).
       * рахунка (commercial invoice) vs рахунку (bank account/game score).

  2. Vocative Case Endings (-е, -у, -ю, -о) [Правопис 2019 §§ 74, 87]:
     - § 87, п. 1 (-е): II declension hard group with historical consonant mutations
       (брате, друже [г->ж], козаче [к->ч], пастуше [х->ш], чоловіче).
     - § 87, п. 2 (-у): II declension masculine with suffixes -ник, -ак, -ок or hard velar stems
       (батьку, синку, робітнику, діду).
     - § 87, п. 3 (-ю): II declension soft group and hypocoristics (вчителю, Василю, бійцю, Андрію, татусю).
     - § 73, п. 1 (-о): I declension hard group feminine and masculine (мамо, сестро, Оксано, Миколо).
     - § 73, п. 2 (-е, -є, -ю): I declension soft/vowel stems (земле, Маріє, доню, бабусю).

  3. Stem Groups & Instrumental Singular (-ом vs -ем vs -єм) [Правопис 2019 § 80]:
     - Hard group -> -ом (столом, братом).
     - Mixed sibilant stem (ж, ч, ш, щ) -> -ем (ножем, товаришем, плащем, мечем) [anti-calque *ножом].
     - Soft group -> -ем / -єм (конем, краєм, бійцем).

  4. Animacy in Masculine Accusative (Істоти vs Неістоти):
     - Animate beings (Accusative = Genitive): «зустрів студента», «побачив вовка».
     - Inanimate objects (Accusative = Nominative): «купив новий стіл», «поклав олівець».

Provides targeted pedagogical feedback explaining the specific rule and misconception,
and guarantees zero collisions among options.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class NounMechanicsCategory(StrEnum):
    """Specific categories of noun deep mechanics practice."""

    # II Declension Genitive singular
    GEN_II_BEING_CONCRETE = "gen_ii_being_concrete"
    GEN_II_SETTLEMENT_MEASURE = "gen_ii_settlement_measure"
    GEN_II_SUBSTANCE_MASS = "gen_ii_substance_mass"
    GEN_II_ABSTRACT_PROCESS = "gen_ii_abstract_process"
    GEN_II_COLLECTIVE_TERRITORY = "gen_ii_collective_territory"
    GEN_II_HOMONYM_PAIR = "gen_ii_homonym_pair"

    # Vocative Case
    VOC_II_HARD_E = "voc_ii_hard_e"
    VOC_II_VELAR_SUFFIX_U = "voc_ii_velar_suffix_u"
    VOC_II_SOFT_YU = "voc_ii_soft_yu"
    VOC_I_HARD_O = "voc_i_hard_o"
    VOC_I_SOFT_YE_YU = "voc_i_soft_ye_yu"

    # Instrumental Case Stem Groups
    INST_II_MIXED_SIBILANT_EM = "inst_ii_mixed_sibilant_em"

    # Animacy in Accusative
    ANIMACY_ACCUSATIVE = "animacy_accusative"


class NounMechanicsInterferenceType(StrEnum):
    """Taxonomy of morphological, phonological, and semantic noun misconceptions."""

    FALSE_GENITIVE_A_FOR_ABSTRACT_MASS = "false_genitive_a_for_abstract_mass"
    FALSE_GENITIVE_U_FOR_CONCRETE_BEING = "false_genitive_u_for_concrete_being"
    FALSE_GENITIVE_U_FOR_SETTLEMENT = "false_genitive_u_for_settlement"
    FALSE_GENITIVE_A_FOR_COLLECTIVE = "false_genitive_a_for_collective"
    HOMONYM_GENITIVE_MEANING_MISMATCH = "homonym_genitive_meaning_mismatch"
    FALSE_NOMINATIVE_FOR_GENITIVE = "false_nominative_for_genitive"
    FALSE_INSTRUMENTAL_FOR_GENITIVE = "false_instrumental_for_genitive"
    FALSE_DATIVE_FOR_GENITIVE = "false_dative_for_genitive"
    FALSE_VOCATIVE_NOMINATIVE = "false_vocative_nominative"
    FALSE_VOCATIVE_U_FOR_HARD_E = "false_vocative_u_for_hard_e"
    FALSE_VOCATIVE_E_FOR_SUFFIX_U = "false_vocative_e_for_suffix_u"
    FALSE_VOCATIVE_E_FOR_SOFT_YU = "false_vocative_e_for_soft_yu"
    FALSE_VOCATIVE_YU_FOR_HARD_E = "false_vocative_yu_for_hard_e"
    FALSE_VOCATIVE_O_FOR_SOFT = "false_vocative_o_for_soft"
    FALSE_MUTATION_MISSING = "false_mutation_missing"
    FALSE_INSTRUMENTAL_OM_FOR_SIBILANT = "false_instrumental_om_for_sibilant"
    FALSE_INSTRUMENTAL_IM_FOR_NOUN = "false_instrumental_im_for_noun"
    FALSE_NOMINATIVE_FOR_INSTRUMENTAL = "false_nominative_for_instrumental"
    FALSE_INSTRUMENTAL_EM_FOR_HARD = "false_instrumental_em_for_hard"
    FALSE_ANIMACY_ACCUSATIVE_INANIMATE = "false_animacy_accusative_inanimate"
    FALSE_ANIMACY_ACCUSATIVE_ANIMATE = "false_animacy_accusative_animate"
    FALSE_INSTRUMENTAL_FOR_ACCUSATIVE = "false_instrumental_for_accusative"
    FALSE_DATIVE_FOR_ACCUSATIVE = "false_dative_for_accusative"
    RUSSIAN_DECLENSION_INTERFERENCE = "russian_declension_interference"


INTERFERENCE_EXPLANATIONS: dict[NounMechanicsInterferenceType, dict[str, str]] = {
    NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS: {
        "ua": "Помилкове вживання закінчення -а/-я для назв речовин, матеріалів або абстрактних понять. За Правописом 2019 § 82, п. 2 вони мають закінчення -у/-ю.",
        "en": "Erroneous use of ending -a/-ya for substances or abstract concepts. Under Pravopys 2019 § 82, item 2, mass substances and abstract notions take -u/-yu.",
    },
    NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING: {
        "ua": "Помилкове вживання закінчення -у/-ю для назв істот або чітко окреслених предметів. За Правописом 2019 § 82, п. 1 вони мають закінчення -а/-я.",
        "en": "Erroneous use of ending -u/-yu for beings or concrete countable objects. Under Pravopys 2019 § 82, item 1, they take -a/-ya.",
    },
    NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_SETTLEMENT: {
        "ua": "Помилкове вживання закінчення -у/-ю для назв міст і населених пунктів. За Правописом 2019 § 82, п. 1.3 назви міст мають закінчення -а/-я (Києва, Львова, Харкова).",
        "en": "Erroneous use of ending -u/-yu for cities and settlements. Under Pravopys 2019 § 82, item 1.3, town and city names take -a/-ya.",
    },
    NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE: {
        "ua": "Помилкове вживання закінчення -а/-я для збірних понять чи територій. За Правописом 2019 § 82, п. 2.2 вони вимагають закінчення -у/-ю (лісу, народу, полку).",
        "en": "Erroneous use of ending -a/-ya for collective nouns or territories. Under Pravopys 2019 § 82, item 2.2, collective nouns take -u/-yu.",
    },
    NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH: {
        "ua": "Невідповідність закінчення значенню слова в контексті. За Правописом 2019 § 82, п. 3 закінчення -а/-я вказує на конкретний предмет чи місяць, а -у/-ю — на матеріал, процес чи збірність.",
        "en": "Ending mismatch with word sense in context. Under Pravopys 2019 § 82, item 3, -a/-ya denotes a concrete object/month, whereas -u/-yu denotes material, process, or collection.",
    },
    NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE: {
        "ua": "Вживання форми називного відмінка замість обов'язкового родового (наприклад, після прийменників «біля», «до», «без» або при запереченні «немає»).",
        "en": "Use of nominative form instead of required genitive (e.g. after prepositions 'bilia', 'do', 'bez' or negation 'nemaie').",
    },
    NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE: {
        "ua": "Вживання форми орудного відмінка замість родового.",
        "en": "Use of instrumental form instead of genitive.",
    },
    NounMechanicsInterferenceType.FALSE_DATIVE_FOR_GENITIVE: {
        "ua": "Вживання закінчення давального відмінка замість родового.",
        "en": "Use of dative case ending instead of genitive.",
    },
    NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_INSTRUMENTAL: {
        "ua": "Форма називного відмінка замість орудного знаряддя, способу дії чи супроводу.",
        "en": "Nominative form instead of instrumental of instrument, means, or accompaniment.",
    },
    NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_ACCUSATIVE: {
        "ua": "Форма орудного відмінка замість знахідного прямого додатка.",
        "en": "Instrumental form instead of accusative direct object.",
    },
    NounMechanicsInterferenceType.FALSE_DATIVE_FOR_ACCUSATIVE: {
        "ua": "Форма давального відмінка замість знахідного прямого додатка.",
        "en": "Dative form instead of accusative direct object.",
    },
    NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_EM_FOR_HARD: {
        "ua": "Помилкове закінчення -ем замість -ом для твердої групи другої відміни в орудному відмінку.",
        "en": "Erroneous ending -em instead of -om for 2nd declension hard stem in the instrumental.",
    },
    NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE: {
        "ua": "Вживання форми Називного відмінка замість обов'язкового Кличного під час звертання. В українській мові звертання завжди вимагає Кличного відмінка (Правопис 2019 §§ 74, 87).",
        "en": "Use of Nominative case instead of mandatory Vocative in address. Ukrainian syntax strictly requires the Vocative case when addressing persons (Pravopys 2019 §§ 74, 87).",
    },
    NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E: {
        "ua": "Помилкове вживання закінчення -у для іменників твердої групи другої відміни без зменшувальних суфіксів. За Правописом 2019 § 87, п. 1 вони приймають закінчення -е (брате, козаче).",
        "en": "Erroneous use of ending -u for 2nd declension hard stem nouns without diminutive suffixes. Under Pravopys 2019 § 87, item 1, they take -e.",
    },
    NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U: {
        "ua": "Помилкове закінчення -е для іменників із суфіксами -ник, -ак, -ок або на задньоязиковий приголосний. За Правописом 2019 § 87, п. 2 вони вимагають закінчення -у (батьку, синку).",
        "en": "Erroneous ending -e for nouns with suffixes -nyk, -ak, -ok or velar stems. Under Pravopys 2019 § 87, item 2, they require -u.",
    },
    NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU: {
        "ua": "Помилкове закінчення -е для іменників м'якої групи другої відміни. За Правописом 2019 § 87, п. 3 вони приймають закінчення -ю (вчителю, Василю, Андрію).",
        "en": "Erroneous ending -e for 2nd declension soft stem nouns. Under Pravopys 2019 § 87, item 3, they take -yu.",
    },
    NounMechanicsInterferenceType.FALSE_VOCATIVE_YU_FOR_HARD_E: {
        "ua": "Помилкове пом'якшення та вживання закінчення -ю для іменників твердої групи. Тверда група другої відміни приймає закінчення -е (друже, Степане).",
        "en": "Erroneous softening and use of ending -yu for hard group nouns. Second declension hard stems take -e.",
    },
    NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT: {
        "ua": "Помилкове тверде закінчення -о для іменників м'якої групи першої відміни. М'яка група приймає закінчення -е/-є або пестливе -ю (Маріє, доню, бабусю).",
        "en": "Erroneous hard ending -o for 1st declension soft stems. Soft stems take -e/-ye or affectionate -yu.",
    },
    NounMechanicsInterferenceType.FALSE_MUTATION_MISSING: {
        "ua": "Пропуск історичного чергування приголосних г->ж, к->ч, х->ш перед закінченням -е у Кличному відмінку (Правопис 2019 § 87, п. 1: друг -> друже, козак -> козаче).",
        "en": "Missing historical consonant mutation g->zh, k->ch, kh->sh before ending -e in the Vocative (Pravopys 2019 § 87, item 1: druh -> druzhe, kozak -> kozache).",
    },
    NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT: {
        "ua": "Помилкове закінчення -ом для іменників мішаної групи з основою на шиплячий (ж, ч, ш, щ). За Правописом 2019 § 80 вони приймають закінчення -ем (ножем, товаришем, плащем).",
        "en": "Erroneous ending -om for mixed sibilant stem nouns (zh, ch, sh, shch). Under Pravopys 2019 § 80, sibilant stems require ending -em (nozhem, tovaryshem, plashchem).",
    },
    NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN: {
        "ua": "Помилкове прикметникове закінчення -им для іменника в орудному відмінку.",
        "en": "Erroneous adjective ending -ym for a noun in the Instrumental case.",
    },
    NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_INANIMATE: {
        "ua": "Помилкове вживання форми родового відмінка (-а/-я) для неістоти у Знахідному відмінку. За нормами літературної мови неістоти чоловічого роду в Знахідному відмінку мають форму Називного (купив олівець, стіл).",
        "en": "Erroneous use of Genitive form (-a/-ya) for inanimate objects in the Accusative. Standard literary Ukrainian requires Nominative form for inanimate masculine nouns (bought a pencil, table).",
    },
    NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_ANIMATE: {
        "ua": "Помилкове вживання форми називного відмінка для істоти у Знахідному відмінку. Істоти чоловічого роду в Знахідному відмінку обов'язково набувають форми Родового відмінка (бачу студента, вовка).",
        "en": "Erroneous use of Nominative form for animate beings in the Accusative. Animate masculine nouns strictly require the Genitive form in the Accusative (bachu studenta).",
    },
    NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE: {
        "ua": "Калькована форма під впливом російської словозміни (наприклад, суржикове закінчення або відсутність кличного відмінка).",
        "en": "Calqued form influenced by Russian declension patterns (e.g. absent vocative or incorrect case suffix).",
    },
}


@dataclass(frozen=True)
class NounMechanicsDistractor:
    """Distractor option with structured linguistic feedback."""

    text: str
    interference_type: NounMechanicsInterferenceType
    explanation: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "interference_type": self.interference_type.value,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class NounMechanicsCard:
    """Practice card for Ukrainian noun mechanics."""

    card_id: str
    category: NounMechanicsCategory
    cefr_level: str
    prompt_sentence: str
    blank_target: str
    correct_answer: str
    distractors: list[NounMechanicsDistractor]
    pravopys_section: str
    rule_summary: dict[str, str]

    def all_options(self) -> list[str]:
        """Return all options shuffled deterministically by card_id sha256."""
        opts = [self.correct_answer] + [d.text for d in self.distractors]
        seed_int = int(hashlib.sha256(self.card_id.encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed_int)
        rng.shuffle(opts)
        return opts

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "category": self.category.value,
            "cefr_level": self.cefr_level,
            "prompt_sentence": self.prompt_sentence,
            "blank_target": self.blank_target,
            "correct_answer": self.correct_answer,
            "options": self.all_options(),
            "distractors": [d.to_dict() for d in self.distractors],
            "pravopys_section": self.pravopys_section,
            "rule_summary": self.rule_summary,
        }


# ============================================================================
# Rule Resolvers
# ============================================================================


def resolve_noun_genitive_ii(
    category: NounMechanicsCategory,
    is_concrete_or_being: bool,
    is_settlement_or_measure: bool = False,
    is_semantic_concrete: bool = False,
) -> tuple[str, str, str]:
    """Resolve II declension Genitive singular ending per Правопис 2019 § 82.

    Returns:
        (ending, rule_ua, rule_en)
    """
    if is_concrete_or_being or is_settlement_or_measure or is_semantic_concrete:
        return (
            "-а / -я",
            "Іменники II відміни чоловічого роду, що означають істот, чітко окреслені предмети, населені пункти або міри, мають закінчення -а/-я (Правопис 2019 § 82, п. 1).",
            "Second declension masculine nouns denoting beings, concrete countable objects, settlements, or units of measure take -a/-ya (Pravopys 2019 § 82, item 1).",
        )
    return (
        "-у / -ю",
        "Іменники II відміни чоловічого роду, що означають речовини, матеріали, збірні поняття, абстрактні явища або території, мають закінчення -у/-ю (Правопис 2019 § 82, п. 2).",
        "Second declension masculine nouns denoting substances, mass terms, collective entities, abstract concepts, or territories take -u/-yu (Pravopys 2019 § 82, item 2).",
    )


def resolve_noun_vocative(
    declension: int,
    stem_group: str,
    has_velar_or_diminutive: bool = False,
    is_soft_hypocoristic: bool = False,
) -> tuple[str, str, str]:
    """Resolve Vocative case ending per Правопис 2019 §§ 74, 87.

    Returns:
        (ending, rule_ua, rule_en)
    """
    if declension == 1:
        if stem_group == "hard":
            return (
                "-о",
                "Іменники I відміни твердої групи у кличному відмінку мають закінчення -о (Правопис 2019 § 73, п. 1: мамо, сестро, Миколо).",
                "First declension hard stem nouns in the vocative take ending -o (Pravopys 2019 § 73, item 1).",
            )
        if is_soft_hypocoristic:
            return (
                "-ю",
                "Пестливі іменники I відміни м'якої групи у кличному відмінку мають закінчення -ю (Правопис 2019 § 73, п. 2: доню, матусю, бабусю).",
                "Affectionate 1st declension soft stem nouns in the vocative take ending -yu (Pravopys 2019 § 73, item 2).",
            )
        return (
            "-е / -є",
            "Іменники I відміни м'якої групи у кличному відмінку мають закінчення -е (після голосного -є) (Правопис 2019 § 73, п. 2: земле, Маріє).",
            "First declension soft stem nouns in the vocative take ending -e (after vowels -ye) (Pravopys 2019 § 73, item 2).",
        )

    # Declension 2
    if stem_group == "hard":
        if has_velar_or_diminutive:
            return (
                "-у",
                "Іменники II відміни на задньоязиковий або з суфіксами -ник, -ак, -ок у кличному відмінку мають закінчення -у (Правопис 2019 § 87, п. 2: батьку, синку).",
                "Second declension nouns ending in velars or with suffixes -nyk, -ak, -ok take vocative ending -u (Pravopys 2019 § 87, item 2).",
            )
        return (
            "-е",
            "Іменники II відміни твердої групи у кличному відмінку мають закінчення -е з історичним чергуванням г->ж, к->ч, х->ш (Правопис 2019 § 87, п. 1: друже, козаче, брате).",
            "Second declension hard stem nouns in the vocative take ending -e with historical consonant mutation (Pravopys 2019 § 87, item 1).",
        )
    if stem_group == "soft":
        return (
            "-ю",
            "Іменники II відміни м'якої групи у кличному відмінку мають закінчення -ю (Правопис 2019 § 87, п. 3: вчителю, Василю, бійцю, Андрію).",
            "Second declension soft stem nouns in the vocative take ending -yu (Pravopys 2019 § 87, item 3).",
        )
    # Mixed group
    return (
        "-е",
        "Іменники II відміни мішаної групи з основою на шиплячий у кличному відмінку мають закінчення -е (Правопис 2019 § 87, п. 1: юначе, школяре).",
        "Second declension mixed sibilant stem nouns in the vocative take ending -e (Pravopys 2019 § 87, item 1).",
    )


def resolve_instrumental_singular_ii(stem_group: str) -> tuple[str, str, str]:
    """Resolve II declension Instrumental singular ending per Правопис 2019 § 80."""
    if stem_group == "hard":
        return (
            "-ом",
            "Іменники II відміни твердої групи в орудному відмінку однини мають закінчення -ом (Правопис 2019 § 80: столом, братом).",
            "Second declension hard stem nouns in the instrumental singular take -om (Pravopys 2019 § 80).",
        )
    if stem_group == "mixed":
        return (
            "-ем",
            "Іменники II відміни мішаної групи (з основою на шиплячий ж, ч, ш, щ) в орудному відмінку мають закінчення -ем, а не -ом (Правопис 2019 § 80: ножем, товаришем, плащем).",
            "Second declension mixed sibilant stems (zh, ch, sh, shch) strictly take ending -em, not -om, in the instrumental (Pravopys 2019 § 80).",
        )
    return (
        "-ем / -єм",
        "Іменники II відміни м'якої групи в орудному відмінку мають закінчення -ем (після голосного -єм) (Правопис 2019 § 80: конем, краєм, бійцем).",
        "Second declension soft stem nouns in the instrumental take -em (-yem after vowels) (Pravopys 2019 § 80).",
    )


def resolve_animacy_accusative(is_animate: bool) -> tuple[str, str, str]:
    """Resolve masculine Accusative case form (Animacy vs Inanimacy)."""
    if is_animate:
        return (
            "Родовий відмінок (-а/-я)",
            "Іменники чоловічого роду — назви істот — у знахідному відмінку однини мають форму, спільну з родовим відмінком (зустрів студента, бачу вовка).",
            "Masculine animate nouns (beings) in the accusative singular take the genitive form (e.g. zustriv studenta).",
        )
    return (
        "Називний відмінок (без закінчення)",
        "Іменники чоловічого роду — назви неістот — у знахідному відмінку однини мають форму, спільну з називним відмінком (купив новий стіл, поклав олівець).",
        "Masculine inanimate nouns in the accusative singular strictly take the nominative form (e.g. kupyv stil, not *stola).",
    )


# ============================================================================
# Canonical Card Bank Generator (54 cards)
# ============================================================================


def build_canonical_noun_mechanics_cards() -> list[NounMechanicsCard]:
    """Build the canonical suite of 54 cards covering all noun mechanics."""
    cards: list[NounMechanicsCard] = []

    # ------------------------------------------------------------------------
    # 1. Genitive II: Beings & Concrete Countable Items (-а / -я)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_being_student_1",
            category=NounMechanicsCategory.GEN_II_BEING_CONCRETE,
            cefr_level="A1",
            prompt_sentence="У нашій групі сьогодні немає нового ___.",
            blank_target="студента",
            correct_answer="студента",
            distractors=[
                NounMechanicsDistractor(
                    text="студенту",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING],
                ),
                NounMechanicsDistractor(
                    text="студент",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість обов'язкового родового при запереченні «немає».",
                        "en": "Nominative form instead of required Genitive after negation 'nemaie'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="студентом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.1",
            rule_summary={
                "ua": "Назви осіб та істот чоловічого роду II відміни мають у родовому відмінку закінчення -а (студента, брата, лікаря).",
                "en": "Masculine nouns of the 2nd declension denoting persons and beings take ending -a in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_being_vchytel_2",
            category=NounMechanicsCategory.GEN_II_BEING_CONCRETE,
            cefr_level="A1",
            prompt_sentence="На уроці діти уважно слухали свого ___.",
            blank_target="вчителя",
            correct_answer="вчителя",
            distractors=[
                NounMechanicsDistractor(
                    text="вчителю",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING],
                ),
                NounMechanicsDistractor(
                    text="вчитель",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE],
                ),
                NounMechanicsDistractor(
                    text="вчителем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.1",
            rule_summary={
                "ua": "Іменники м'якої групи на позначення істот мають у родовому відмінку закінчення -я (вчителя, коваля).",
                "en": "Soft-group nouns denoting beings take ending -ya in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_concrete_stil_3",
            category=NounMechanicsCategory.GEN_II_BEING_CONCRETE,
            cefr_level="A1",
            prompt_sentence="Біля письмового ___ стояло зручне дерев'яне крісло.",
            blank_target="стола",
            correct_answer="стола",
            distractors=[
                NounMechanicsDistractor(
                    text="столу",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING],
                ),
                NounMechanicsDistractor(
                    text="стіл",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового після прийменника «біля».",
                        "en": "Nominative form instead of Genitive after preposition 'bilia'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="столом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.2",
            rule_summary={
                "ua": "Назви конкретних окреслених предметів та меблів мають закінчення -а (стола, стільця, шафи).",
                "en": "Nouns denoting concrete countable objects and furniture take ending -a (stola, olivtsia).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_concrete_nizh_4",
            category=NounMechanicsCategory.GEN_II_BEING_CONCRETE,
            cefr_level="A2",
            prompt_sentence="Кухар не зміг знайти гострого кухонного ___.",
            blank_target="ножа",
            correct_answer="ножа",
            distractors=[
                NounMechanicsDistractor(
                    text="ножу",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING],
                ),
                NounMechanicsDistractor(
                    text="ніж",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового при запереченні «не зміг знайти».",
                        "en": "Nominative form instead of Genitive under negated transitive verb.",
                    },
                ),
                NounMechanicsDistractor(
                    text="ножем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.2",
            rule_summary={
                "ua": "Назви знарядь праці та інструментів мають закінчення -а (ножа, молотка, олівця).",
                "en": "Names of tools and instruments take ending -a in the genitive (nozha, molotka).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_concrete_traktor_5",
            category=NounMechanicsCategory.GEN_II_BEING_CONCRETE,
            cefr_level="A2",
            prompt_sentence="Фермер відремонтував мотор старого ___.",
            blank_target="трактора",
            correct_answer="трактора",
            distractors=[
                NounMechanicsDistractor(
                    text="трактору",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING],
                ),
                NounMechanicsDistractor(
                    text="трактор",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового приналежності.",
                        "en": "Nominative form instead of possessive Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="трактором",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.2",
            rule_summary={
                "ua": "Назви машин, механізмів та транспортних засобів мають закінчення -а (трактора, комбайна, автомобіля).",
                "en": "Names of vehicles and machines take ending -a in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_concrete_dub_6",
            category=NounMechanicsCategory.GEN_II_BEING_CONCRETE,
            cefr_level="B1",
            prompt_sentence="Пташка звила гніздо на гілці вікового ___.",
            blank_target="дуба",
            correct_answer="дуба",
            distractors=[
                NounMechanicsDistractor(
                    text="дубу",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING],
                ),
                NounMechanicsDistractor(
                    text="дуб",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового приналежності.",
                        "en": "Nominative form instead of possessive Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="дубом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.1",
            rule_summary={
                "ua": "Назви конкретних дерев та рослин мають закінчення -а (дуба, ясеня, клена, береста).",
                "en": "Names of specific trees take ending -a in the genitive (duba, yasenia).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 2. Genitive II: Settlements, Cities, Measures, Time (-а / -я)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_settle_kyiv_1",
            category=NounMechanicsCategory.GEN_II_SETTLEMENT_MEASURE,
            cefr_level="A1",
            prompt_sentence="Поїзд вирушає з центрального вокзалу ___ о шостій ранку.",
            blank_target="Києва",
            correct_answer="Києва",
            distractors=[
                NounMechanicsDistractor(
                    text="Києву",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_SETTLEMENT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_SETTLEMENT],
                ),
                NounMechanicsDistractor(
                    text="Київ",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового після прийменника «з».",
                        "en": "Nominative form instead of Genitive after preposition 'z'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="Києвом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.3",
            rule_summary={
                "ua": "Назви міст та інших населених пунктів мають закінчення -а/-я (Києва, Львова, Харкова, Чернігова).",
                "en": "Names of cities and towns take ending -a/-ya in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_settle_lviv_2",
            category=NounMechanicsCategory.GEN_II_SETTLEMENT_MEASURE,
            cefr_level="A1",
            prompt_sentence="Минулого літа ми повернулися зі старовинного ___.",
            blank_target="Львова",
            correct_answer="Львова",
            distractors=[
                NounMechanicsDistractor(
                    text="Львову",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_SETTLEMENT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_SETTLEMENT],
                ),
                NounMechanicsDistractor(
                    text="Львів",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового з прийменником «зі».",
                        "en": "Nominative form instead of Genitive with preposition 'zi'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="Львовом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.3",
            rule_summary={
                "ua": "Назви міст закінчуються на -а (Львова, Парижа, Берліна).",
                "en": "Names of cities take ending -a in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_measure_metr_3",
            category=NounMechanicsCategory.GEN_II_SETTLEMENT_MEASURE,
            cefr_level="A2",
            prompt_sentence="Для пошиття костюма майстру не вистачило одного ___ тканини.",
            blank_target="метра",
            correct_answer="метра",
            distractors=[
                NounMechanicsDistractor(
                    text="метру",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation={
                        "ua": "Одиниці вимірювання за Правописом 2019 § 82, п. 1.4 мають закінчення -а (метра, грама, літра).",
                        "en": "Units of measure under Pravopys 2019 § 82, item 1.4 take ending -a (metra, litra).",
                    },
                ),
                NounMechanicsDistractor(
                    text="метр",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового після кількісного числівника «одного».",
                        "en": "Nominative form instead of Genitive after numeral 'odnoho'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="метром",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.4",
            rule_summary={
                "ua": "Назви мір, ваги та грошових одиниць мають закінчення -а (метра, кілограма, літра, долара).",
                "en": "Units of measure, weight, and currency take ending -a in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_measure_dolar_4",
            category=NounMechanicsCategory.GEN_II_SETTLEMENT_MEASURE,
            cefr_level="A2",
            prompt_sentence="Курс одного американського ___ сьогодні залишився стабільним.",
            blank_target="долара",
            correct_answer="долара",
            distractors=[
                NounMechanicsDistractor(
                    text="долару",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation={
                        "ua": "Назви грошових одиниць мають закінчення -а (долара, фунта, франка).",
                        "en": "Names of monetary units take ending -a (dolara, funta).",
                    },
                ),
                NounMechanicsDistractor(
                    text="долар",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="доларом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.4",
            rule_summary={
                "ua": "Грошові одиниці чоловічого роду мають закінчення -а (долара, юаня).",
                "en": "Masculine monetary units take ending -a.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_time_ponedilok_5",
            category=NounMechanicsCategory.GEN_II_SETTLEMENT_MEASURE,
            cefr_level="A1",
            prompt_sentence="З наступного ___ починається новий навчальний семестр.",
            blank_target="понеділка",
            correct_answer="понеділка",
            distractors=[
                NounMechanicsDistractor(
                    text="понеділку",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation={
                        "ua": "Дні тижня та місяці за Правописом 2019 § 82, п. 1.4 мають закінчення -а/-я (понеділка, вівторка, четверга).",
                        "en": "Days of the week and months under Pravopys 2019 § 82, item 1.4 take ending -a/-ya.",
                    },
                ),
                NounMechanicsDistractor(
                    text="понеділок",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового з прийменником «з».",
                        "en": "Nominative form instead of Genitive after 'z'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="понеділком",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.4",
            rule_summary={
                "ua": "Назви днів тижня чоловічого роду приймають закінчення -а (понеділка, вівторка, четверга).",
                "en": "Masculine names of days of the week take ending -a.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_time_sichen_6",
            category=NounMechanicsCategory.GEN_II_SETTLEMENT_MEASURE,
            cefr_level="A1",
            prompt_sentence="Першого ___ в Україні традиційно святкують Новий рік.",
            blank_target="січня",
            correct_answer="січня",
            distractors=[
                NounMechanicsDistractor(
                    text="січню",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_U_FOR_CONCRETE_BEING,
                    explanation={
                        "ua": "Назви місяців за Правописом 2019 § 82, п. 1.4 мають закінчення -я/-а (січня, березня, квітня).",
                        "en": "Names of calendar months take ending -ya/-a in the genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="січень",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового дати.",
                        "en": "Nominative form instead of Genitive in date expression.",
                    },
                ),
                NounMechanicsDistractor(
                    text="січнем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 1.4",
            rule_summary={
                "ua": "Назви місяців чоловічого роду мають закінчення -я/-а (січня, квітня, травня).",
                "en": "Masculine month names take ending -ya/-a.",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 3. Genitive II: Substances, Materials, Mass Terms (-у / -ю)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_substance_tsukor_1",
            category=NounMechanicsCategory.GEN_II_SUBSTANCE_MASS,
            cefr_level="A1",
            prompt_sentence="Він додав до гарячої кави дві ложки білого ___.",
            blank_target="цукру",
            correct_answer="цукру",
            distractors=[
                NounMechanicsDistractor(
                    text="цукра",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="цукор",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового кількісного.",
                        "en": "Nominative form instead of quantitative Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="цукром",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.1",
            rule_summary={
                "ua": "Назви речовин, матеріалів, сипких тіл мають закінчення -у/-ю (цукру, піску, меду, солі).",
                "en": "Nouns denoting substances, granular matter, and materials take -u/-yu in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_substance_pisok_2",
            category=NounMechanicsCategory.GEN_II_SUBSTANCE_MASS,
            cefr_level="A2",
            prompt_sentence="Для будівництва фундаменту привезли три тонни річкового ___.",
            blank_target="піску",
            correct_answer="піску",
            distractors=[
                NounMechanicsDistractor(
                    text="піска",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="пісок",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового міри.",
                        "en": "Nominative form instead of Genitive of quantity.",
                    },
                ),
                NounMechanicsDistractor(
                    text="піском",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.1",
            rule_summary={
                "ua": "Назви будівельних та природних матеріалів мають закінчення -у (піску, щебеню, торфу, воску).",
                "en": "Names of materials and mineral matter take ending -u (pisku, shchebeniu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_substance_med_3",
            category=NounMechanicsCategory.GEN_II_SUBSTANCE_MASS,
            cefr_level="A1",
            prompt_sentence="Бабуся дала хворому онуку чашку липового чаю з ложкою ___.",
            blank_target="меду",
            correct_answer="меду",
            distractors=[
                NounMechanicsDistractor(
                    text="меда",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="мед",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="медом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.1",
            rule_summary={
                "ua": "Назви харчових продуктів та рідких речовин приймають закінчення -у (меду, квасу, сиропу).",
                "en": "Names of food products and liquid substances take -u (medu, kvasu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_substance_kysend_4",
            category=NounMechanicsCategory.GEN_II_SUBSTANCE_MASS,
            cefr_level="B1",
            prompt_sentence="У високогірних районах відчувається значний дефіцит ___.",
            blank_target="кисню",
            correct_answer="кисню",
            distractors=[
                NounMechanicsDistractor(
                    text="кисня",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="кисень",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="киснем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.1",
            rule_summary={
                "ua": "Назви газів та хімічних елементів мають закінчення -у/-ю (кисню, водню, азоту).",
                "en": "Names of gases and chemical elements take ending -u/-yu (kysniu, azotu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_substance_chai_5",
            category=NounMechanicsCategory.GEN_II_SUBSTANCE_MASS,
            cefr_level="A1",
            prompt_sentence="Після довгої зимової прогулянки ми випили склянку гарячого ___.",
            blank_target="чаю",
            correct_answer="чаю",
            distractors=[
                NounMechanicsDistractor(
                    text="чая",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="чай",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового кількісного.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="чаєм",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.1",
            rule_summary={
                "ua": "Назви напоїв та рідин мають закінчення -ю/-у (чаю, соку, компоту).",
                "en": "Names of beverages and liquids take ending -yu/-u in the genitive.",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 4. Genitive II: Abstract Concepts, Processes, States (-у / -ю)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_abstract_rozvytok_1",
            category=NounMechanicsCategory.GEN_II_ABSTRACT_PROCESS,
            cefr_level="B1",
            prompt_sentence="Ця державна програма сприяє прискоренню економічного ___.",
            blank_target="розвитку",
            correct_answer="розвитку",
            distractors=[
                NounMechanicsDistractor(
                    text="розвитка",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="розвиток",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового при дієслівному іменнику «прискорення».",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="розвитком",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.4",
            rule_summary={
                "ua": "Назви процесів, станів та абстрактних понять мають закінчення -у/-ю (розвитку, прогресу, занепаду).",
                "en": "Names of processes, states, and abstract concepts take -u/-yu in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_abstract_prohres_2",
            category=NounMechanicsCategory.GEN_II_ABSTRACT_PROCESS,
            cefr_level="B1",
            prompt_sentence="Вчені досягли значного наукового й технічного ___.",
            blank_target="прогресу",
            correct_answer="прогресу",
            distractors=[
                NounMechanicsDistractor(
                    text="прогреса",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="прогрес",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="прогресом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.4",
            rule_summary={
                "ua": "Абстрактні поняття та явища мають закінчення -у (прогресу, успіху, аналізу).",
                "en": "Abstract concepts and phenomena take ending -u.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_abstract_bil_3",
            category=NounMechanicsCategory.GEN_II_ABSTRACT_PROCESS,
            cefr_level="A2",
            prompt_sentence="Пацієнт прийняв ліки для полегшення гострого ___.",
            blank_target="болю",
            correct_answer="болю",
            distractors=[
                NounMechanicsDistractor(
                    text="боля",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="біль",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="болем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.4",
            rule_summary={
                "ua": "Назви фізичних та душевних станів, почуттів мають закінчення -ю/-у (болю, жалю, гніву, смутку).",
                "en": "Nouns denoting physical or emotional states take ending -yu/-u.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_abstract_doshch_4",
            category=NounMechanicsCategory.GEN_II_ABSTRACT_PROCESS,
            cefr_level="A1",
            prompt_sentence="Діти сховалися під густим навісом від сильного ___.",
            blank_target="дощу",
            correct_answer="дощу",
            distractors=[
                NounMechanicsDistractor(
                    text="доща",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="дощ",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового після прийменника «від».",
                        "en": "Nominative form instead of Genitive after 'vid'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="дощем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.4",
            rule_summary={
                "ua": "Назви природних явищ приймають закінчення -у/-ю (дощу, снігу, вітру, туману, грому).",
                "en": "Names of natural phenomena take ending -u/-yu in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_abstract_sport_5",
            category=NounMechanicsCategory.GEN_II_ABSTRACT_PROCESS,
            cefr_level="A2",
            prompt_sentence="Він із раннього дитинства не уявляв життя без активного ___.",
            blank_target="спорту",
            correct_answer="спорту",
            distractors=[
                NounMechanicsDistractor(
                    text="спорта",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_ABSTRACT_MASS],
                ),
                NounMechanicsDistractor(
                    text="спорт",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового після прийменника «без».",
                        "en": "Nominative form instead of Genitive after 'bez'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="спортом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.4",
            rule_summary={
                "ua": "Назви галузей діяльності, ігор та спорту мають закінчення -у (спорту, футболу, хокею, туризму).",
                "en": "Names of fields of activity and sports take ending -u (sportu, futbolu).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 5. Genitive II: Collective Nouns & Territories (-у / -ю)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_coll_lis_1",
            category=NounMechanicsCategory.GEN_II_COLLECTIVE_TERRITORY,
            cefr_level="A1",
            prompt_sentence="З глибини дрімучого ___ долинали звуки сови.",
            blank_target="лісу",
            correct_answer="лісу",
            distractors=[
                NounMechanicsDistractor(
                    text="ліса",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE],
                ),
                NounMechanicsDistractor(
                    text="ліс",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="лісом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.2",
            rule_summary={
                "ua": "Збірні назви рослинного світу мають закінчення -у (лісу, гаю, саду, парку).",
                "en": "Collective plant and forest nouns take ending -u (lisu, haiu, sadu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_coll_narod_2",
            category=NounMechanicsCategory.GEN_II_COLLECTIVE_TERRITORY,
            cefr_level="B1",
            prompt_sentence="Конституція закріплює суверенітет і волю українського ___.",
            blank_target="народу",
            correct_answer="народу",
            distractors=[
                NounMechanicsDistractor(
                    text="народа",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE],
                ),
                NounMechanicsDistractor(
                    text="народ",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="народом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.2",
            rule_summary={
                "ua": "Збірні назви людей та спільнот мають закінчення -у (народу, натовпу, гурту, полку).",
                "en": "Collective nouns denoting communities take ending -u (narodu, hurtu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_terr_krym_3",
            category=NounMechanicsCategory.GEN_II_COLLECTIVE_TERRITORY,
            cefr_level="A2",
            prompt_sentence="Скелясті береги сонячного ___ завжди приваблювали туристів.",
            blank_target="Криму",
            correct_answer="Криму",
            distractors=[
                NounMechanicsDistractor(
                    text="Крима",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE],
                ),
                NounMechanicsDistractor(
                    text="Крим",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового приналежності.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="Кримом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.5",
            rule_summary={
                "ua": "Назви регіонів, півостровів та територій мають закінчення -у (Криму, Кавказу, Сибіру, Донбасу).",
                "en": "Names of geographical regions, territories, and peninsulas take ending -u.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_terr_kytai_4",
            category=NounMechanicsCategory.GEN_II_COLLECTIVE_TERRITORY,
            cefr_level="A2",
            prompt_sentence="Шовковий шлях пролягав від стародавнього ___ до Європи.",
            blank_target="Китаю",
            correct_answer="Китаю",
            distractors=[
                NounMechanicsDistractor(
                    text="Китая",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE],
                ),
                NounMechanicsDistractor(
                    text="Китай",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового після прийменника «від».",
                        "en": "Nominative form instead of Genitive after 'vid'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="Китаєм",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.5",
            rule_summary={
                "ua": "Назви країн та континентів мають закінчення -у/-ю (Китаю, Єгипту, Алжиру, Сибіру).",
                "en": "Names of countries and continents take ending -u/-yu in the genitive.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_coll_orkestr_5",
            category=NounMechanicsCategory.GEN_II_COLLECTIVE_TERRITORY,
            cefr_level="B1",
            prompt_sentence="Музиканти симфонічного ___ піднялися на сцену філармонії.",
            blank_target="оркестру",
            correct_answer="оркестру",
            distractors=[
                NounMechanicsDistractor(
                    text="оркестра",
                    interference_type=NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_GENITIVE_A_FOR_COLLECTIVE],
                ),
                NounMechanicsDistractor(
                    text="оркестр",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="оркестром",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 2.2",
            rule_summary={
                "ua": "Збірні назви колективів та ансамблів мають закінчення -у (оркестру, ансамблю, хору).",
                "en": "Names of collective groups and ensembles take ending -u in the genitive.",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 6. Genitive II: Semantic Homonym Pairs (Meaning Differentiation)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_kamina_item_1",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B1",
            prompt_sentence="Археолог підняв із землі й дослідив форму одного обтесаного ___.",
            blank_target="каменя",
            correct_answer="каменя",
            distractors=[
                NounMechanicsDistractor(
                    text="каменю",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -ю позначає речовину/матеріал (будинок із каменю), тоді як окремий предметний камінь має закінчення -я (одного каменя).",
                        "en": "Ending -yu denotes rock material (z kameniu), while a single countable stone takes ending -ya (odnoho kamenia).",
                    },
                ),
                NounMechanicsDistractor(
                    text="камінь",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="каменем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Одиничний камінь як окремий предмет має закінчення -я (каменя), а гірська порода чи матеріал — -ю (каменю).",
                "en": "An individual stone takes -ya (kamenia), while stone as mineral matter takes -yu (kaminiu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_kaminu_mass_2",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B1",
            prompt_sentence="Міцну фортецю звели з міцного природного ___.",
            blank_target="каменю",
            correct_answer="каменю",
            distractors=[
                NounMechanicsDistractor(
                    text="каменя",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -я позначає окремий штучний камінь, тоді як матеріал і порода мають закінчення -ю.",
                        "en": "Ending -ya denotes a single stone, while material/rock takes -yu.",
                    },
                ),
                NounMechanicsDistractor(
                    text="камінь",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового з прийменником «з».",
                        "en": "Nominative form instead of Genitive with 'z'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="каменем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Камінь як матеріал або сировина має закінчення -ю (каменю).",
                "en": "Stone as building material or mineral mass takes ending -yu.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_lystopada_month_3",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="A2",
            prompt_sentence="Останні теплі дні відчувалися на початку ___.",
            blank_target="листопада",
            correct_answer="листопада",
            distractors=[
                NounMechanicsDistractor(
                    text="листопаду",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Форма «листопаду» з закінченням -у означає явище опадання листя, а календарний місяць має закінчення -а (листопада).",
                        "en": "The form 'lystopadu' (-u) denotes autumn leaf-fall, whereas the calendar month takes -a (lystopada).",
                    },
                ),
                NounMechanicsDistractor(
                    text="листопад",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового часу.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="листопадом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Календарний місяць листопад у родовому відмінку має закінчення -а (листопада), а процес падіння листя — -у (листопаду).",
                "en": "The month of November takes -a (lystopada), whereas the phenomenon of leaf-fall takes -u (lystopadu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_lystopadu_process_4",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B1",
            prompt_sentence="Паркові алеї вкрилися золотом під час осіннього ___.",
            blank_target="листопаду",
            correct_answer="листопаду",
            distractors=[
                NounMechanicsDistractor(
                    text="листопада",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -а вживається для назви місяця (двадцятого листопада), а процес опадання листя має закінчення -у.",
                        "en": "Ending -a is for the month name, whereas the natural process of falling leaves requires -u.",
                    },
                ),
                NounMechanicsDistractor(
                    text="листопад",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового після «під час».",
                        "en": "Nominative form instead of Genitive after 'pid chas'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="листопадом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Природне явище опадання листя приймає закінчення -у (листопаду).",
                "en": "The natural process of leaf-fall takes ending -u (lystopadu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_aparata_device_5",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B2",
            prompt_sentence="Інженер замінив пошкоджену деталь рентгенівського ___.",
            blank_target="апарата",
            correct_answer="апарата",
            distractors=[
                NounMechanicsDistractor(
                    text="апарату",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -у вживається для органу влади або установи (державного апарату), а фізичний прилад має закінчення -а (апарата).",
                        "en": "Ending -u denotes an administrative institution, while a physical device/instrument takes ending -a (aparata).",
                    },
                ),
                NounMechanicsDistractor(
                    text="апарат",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового приналежності.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="апаратом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Фізичний прилад/механізм має закінчення -а (апарата), а установа/орган влади — -у (апарату).",
                "en": "A physical instrument takes -a (aparata), while an administrative body takes -u (aparatu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_aparatu_org_6",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B2",
            prompt_sentence="Уряд ухвалив рішення про скорочення штату міністерського ___.",
            blank_target="апарату",
            correct_answer="апарату",
            distractors=[
                NounMechanicsDistractor(
                    text="апарата",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -а вживається для фізичного приладу/механізму (фотоапарата), а установа чи орган влади має закінчення -у (державного апарату).",
                        "en": "Ending -a denotes a physical instrument/device, while an administrative body or institution takes -u (aparatu).",
                    },
                ),
                NounMechanicsDistractor(
                    text="апарат",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE],
                ),
                NounMechanicsDistractor(
                    text="апаратом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE],
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Установа, орган влади або організаційна структура має в родовому відмінку закінчення -у (апарату), а фізичний прилад — -а (апарата).",
                "en": "An administrative body takes ending -u (aparatu), while a physical instrument takes -a (aparata).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_papera_doc_7",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B2",
            prompt_sentence="Юрист уважно перевірив справжність цього цінного державного ___.",
            blank_target="папера",
            correct_answer="папера",
            distractors=[
                NounMechanicsDistractor(
                    text="паперу",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -у означає матеріал або сировину (аркуш паперу), тоді як офіційний документ чи цінний папір має закінчення -а (цінного папера).",
                        "en": "Ending -u denotes paper material, while an official document or security certificate takes -a (papera).",
                    },
                ),
                NounMechanicsDistractor(
                    text="папір",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE],
                ),
                NounMechanicsDistractor(
                    text="папером",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE],
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Цінний папір або офіційний документ має закінчення -а (папера), а папір як матеріал — -у (паперу).",
                "en": "A financial security or official document takes ending -a (papera), while paper as material takes -u (paperu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_paperu_mass_8",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B1",
            prompt_sentence="Для друку тиражу книги видавництву бракувало білого ___.",
            blank_target="паперу",
            correct_answer="паперу",
            distractors=[
                NounMechanicsDistractor(
                    text="папера",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -а вживається для документа або цінного папера, а речовина/матеріал має закінчення -у (паперу).",
                        "en": "Ending -a denotes an official security/document, while paper material strictly takes -u (paperu).",
                    },
                ),
                NounMechanicsDistractor(
                    text="папір",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE],
                ),
                NounMechanicsDistractor(
                    text="папером",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE],
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Папір як речовина чи матеріал має у родовому відмінку закінчення -у (паперу).",
                "en": "Paper as substance or writing material takes ending -u in the genitive (paperu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_akta_doc_9",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B2",
            prompt_sentence="Комісія підписала оригінал підсумкового юридичного ___.",
            blank_target="акта",
            correct_answer="акта",
            distractors=[
                NounMechanicsDistractor(
                    text="акту",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -у позначає дію або частину вистави (першого акту), а офіційний документ чи протокол має закінчення -а (юридичного акта).",
                        "en": "Ending -u denotes an action or theatrical act, while an official document/decree takes ending -a (akta).",
                    },
                ),
                NounMechanicsDistractor(
                    text="акт",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE],
                ),
                NounMechanicsDistractor(
                    text="актом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE],
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Документ, закон або офіційна постанова має закінчення -а (акта), а дія чи театральна дія — -у (акту).",
                "en": "A formal legal document takes -a (akta), while an action or play act takes -u (aktu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_aktu_action_10",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B1",
            prompt_sentence="Глядачі бурхливо аплодували акторам після першого драматичного ___ вистави.",
            blank_target="акту",
            correct_answer="акту",
            distractors=[
                NounMechanicsDistractor(
                    text="акта",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -а вживається для офіційного документа (державного акта), а дія або театральна частина має закінчення -у (першого акту).",
                        "en": "Ending -a is for an official document/act, whereas an action or theatrical act requires ending -u (aktu).",
                    },
                ),
                NounMechanicsDistractor(
                    text="акт",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE],
                ),
                NounMechanicsDistractor(
                    text="актом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE],
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Дія, окремий вчинок або частина спектаклю має закінчення -у (акту).",
                "en": "An action or a part of a theatrical production takes ending -u (aktu).",
            },
        )
    )
    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_termina_term_11",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B1",
            prompt_sentence="Мовознавець детально пояснив етимологію цього наукового ___.",
            blank_target="терміна",
            correct_answer="терміна",
            distractors=[
                NounMechanicsDistractor(
                    text="терміну",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Форма «терміну» означає проміжок часу або строк (терміну дії), тоді як спеціальне мовне чи наукове слово має закінчення -а (наукового терміна).",
                        "en": "Form 'terminu' (-u) denotes a time duration/deadline, whereas a specialized linguistic or scientific word takes -a (termina).",
                    },
                ),
                NounMechanicsDistractor(
                    text="термін",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового.",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="терміном",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Слово в значенні лінгвістичного поняття має закінчення -а (терміна), а часовий строк — -у (терміну).",
                "en": "A specialized technical term takes ending -a (termina), while a time period/deadline takes -u (terminu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_gen_ii_homonym_terminu_time_12",
            category=NounMechanicsCategory.GEN_II_HOMONYM_PAIR,
            cefr_level="B1",
            prompt_sentence="Клієнт звернувся до банку для продовження ___ дії договору.",
            blank_target="терміну",
            correct_answer="терміну",
            distractors=[
                NounMechanicsDistractor(
                    text="терміна",
                    interference_type=NounMechanicsInterferenceType.HOMONYM_GENITIVE_MEANING_MISMATCH,
                    explanation={
                        "ua": "Закінчення -а вживається для наукового слова/поняття, тоді як часовий строк дії вимагає закінчення -у.",
                        "en": "Ending -a is for a specialized scientific word, while a time period or deadline requires -u.",
                    },
                ),
                NounMechanicsDistractor(
                    text="термін",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма називного відмінка замість родового при дієслівному іменнику «продовження».",
                        "en": "Nominative form instead of Genitive.",
                    },
                ),
                NounMechanicsDistractor(
                    text="терміном",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_GENITIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість родового.",
                        "en": "Instrumental form instead of Genitive.",
                    },
                ),
            ],
            pravopys_section="§ 82, п. 3",
            rule_summary={
                "ua": "Часовий проміжок, строк виконання має закінчення -у (терміну).",
                "en": "Time duration or contract deadline takes ending -u (terminu).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 7. Vocative Case II: Hard Group with Mutations (-е)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_hard_brate_1",
            category=NounMechanicsCategory.VOC_II_HARD_E,
            cefr_level="A1",
            prompt_sentence="Рідний мій ___, допоможи мені з цим завданням!",
            blank_target="брате",
            correct_answer="брате",
            distractors=[
                NounMechanicsDistractor(
                    text="брат",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="брату",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E],
                ),
                NounMechanicsDistractor(
                    text="братю",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_YU_FOR_HARD_E,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_YU_FOR_HARD_E],
                ),
            ],
            pravopys_section="§ 87, п. 1",
            rule_summary={
                "ua": "Іменники II відміни твердої групи у кличному відмінку мають закінчення -е (брате, друже, козаче, Степане).",
                "en": "Second declension hard stems take vocative ending -e (brate, druzhe, kozache).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_hard_druzhe_2",
            category=NounMechanicsCategory.VOC_II_HARD_E,
            cefr_level="A1",
            prompt_sentence="Щирий мій ___, радий тебе знову бачити!",
            blank_target="друже",
            correct_answer="друже",
            distractors=[
                NounMechanicsDistractor(
                    text="друг",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="друге",
                    interference_type=NounMechanicsInterferenceType.FALSE_MUTATION_MISSING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_MUTATION_MISSING],
                ),
                NounMechanicsDistractor(
                    text="другу",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E],
                ),
            ],
            pravopys_section="§ 87, п. 1",
            rule_summary={
                "ua": "Перед закінченням -е відбувається історичне чергування г->ж (друг -> друже, ворог -> вороже).",
                "en": "Historical mutation g->zh occurs before ending -e in vocative (druh -> druzhe).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_hard_kozache_3",
            category=NounMechanicsCategory.VOC_II_HARD_E,
            cefr_level="A2",
            prompt_sentence="Славний ___, захисти рідний край від ворогів!",
            blank_target="козаче",
            correct_answer="козаче",
            distractors=[
                NounMechanicsDistractor(
                    text="козак",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="козаке",
                    interference_type=NounMechanicsInterferenceType.FALSE_MUTATION_MISSING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_MUTATION_MISSING],
                ),
                NounMechanicsDistractor(
                    text="козаку",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E],
                ),
            ],
            pravopys_section="§ 87, п. 1",
            rule_summary={
                "ua": "Перед закінченням -е приголосний к чергується з ч (козак -> козаче, юнак -> юначе).",
                "en": "Consonant mutation k->ch occurs before ending -e in vocative (kozak -> kozache).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_hard_pastushe_4",
            category=NounMechanicsCategory.VOC_II_HARD_E,
            cefr_level="B1",
            prompt_sentence="Добрий ___, повертай отару додому перед грозою!",
            blank_target="пастуше",
            correct_answer="пастуше",
            distractors=[
                NounMechanicsDistractor(
                    text="пастух",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="пастухе",
                    interference_type=NounMechanicsInterferenceType.FALSE_MUTATION_MISSING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_MUTATION_MISSING],
                ),
                NounMechanicsDistractor(
                    text="пастуху",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E],
                ),
            ],
            pravopys_section="§ 87, п. 1",
            rule_summary={
                "ua": "Приголосний х чергується з ш перед закінченням -е (пастух -> пастуше, волох -> волоше).",
                "en": "Consonant mutation kh->sh occurs before ending -e in vocative (pastukh -> pastushe).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_hard_choloviche_5",
            category=NounMechanicsCategory.VOC_II_HARD_E,
            cefr_level="A2",
            prompt_sentence="Шановний ___, підкажіть, будь ласка, котра зараз година!",
            blank_target="чоловіче",
            correct_answer="чоловіче",
            distractors=[
                NounMechanicsDistractor(
                    text="чоловік",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="чоловіке",
                    interference_type=NounMechanicsInterferenceType.FALSE_MUTATION_MISSING,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_MUTATION_MISSING],
                ),
                NounMechanicsDistractor(
                    text="чоловіку",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_U_FOR_HARD_E],
                ),
            ],
            pravopys_section="§ 87, п. 1",
            rule_summary={
                "ua": "Слово «чоловік» має у кличному відмінку чергування к->ч та закінчення -е (чоловіче).",
                "en": "Noun 'cholovik' undergoes mutation k->ch and takes -e in vocative (choloviche).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 8. Vocative Case II: Suffixes -ник, -ак, -ок & Velars (-у)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_velar_batku_1",
            category=NounMechanicsCategory.VOC_II_VELAR_SUFFIX_U,
            cefr_level="A1",
            prompt_sentence="Дорогий ___, дякую тобі за турботу й підтримку!",
            blank_target="батьку",
            correct_answer="батьку",
            distractors=[
                NounMechanicsDistractor(
                    text="батько",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="батьче",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U],
                ),
                NounMechanicsDistractor(
                    text="батьків",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Форма присвійного прикметника або родового множини замість кличного однини.",
                        "en": "Possessive form instead of vocative singular.",
                    },
                ),
            ],
            pravopys_section="§ 87, п. 2",
            rule_summary={
                "ua": "Іменники на задньоязиковий або на суфікс -ко мають у кличному відмінку закінчення -у (батьку, синку).",
                "en": "Nouns with suffix -ko or velar stems take vocative ending -u (batku, synku).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_velar_synku_2",
            category=NounMechanicsCategory.VOC_II_VELAR_SUFFIX_U,
            cefr_level="A1",
            prompt_sentence="Мій любий ___, бережи себе в далекій дорозі!",
            blank_target="синку",
            correct_answer="синку",
            distractors=[
                NounMechanicsDistractor(
                    text="синок",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="синче",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U],
                ),
                NounMechanicsDistractor(
                    text="синке",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U],
                ),
            ],
            pravopys_section="§ 87, п. 2",
            rule_summary={
                "ua": "Зменшувальні форми на -ок у кличному відмінку завжди приймають закінчення -у (синку, котику).",
                "en": "Diminutives with suffix -ok strictly take vocative ending -u (synku, kotyku).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_velar_robitnyku_3",
            category=NounMechanicsCategory.VOC_II_VELAR_SUFFIX_U,
            cefr_level="B1",
            prompt_sentence="Шановний ___, зверніть увагу на правила безпеки!",
            blank_target="робітнику",
            correct_answer="робітнику",
            distractors=[
                NounMechanicsDistractor(
                    text="робітник",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="робітнике",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U],
                ),
                NounMechanicsDistractor(
                    text="робітниче",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation={
                        "ua": "Суфікс -ник вимагає закінчення -у, чергування з -че тут нормативно не застосовується (Правопис 2019 § 87, п. 2).",
                        "en": "Suffix -nyk requires ending -u; mutation to -che is non-standard here.",
                    },
                ),
            ],
            pravopys_section="§ 87, п. 2",
            rule_summary={
                "ua": "Іменники з суфіксами -ник, -ак, -ок у кличному відмінку мають закінчення -у (робітнику, гірнику, моряку).",
                "en": "Nouns with suffixes -nyk, -ak, -ok take vocative ending -u.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_velar_didu_4",
            category=NounMechanicsCategory.VOC_II_VELAR_SUFFIX_U,
            cefr_level="A1",
            prompt_sentence="Любий ___, розкажи мені казку про давні часи!",
            blank_target="діду",
            correct_answer="діду",
            distractors=[
                NounMechanicsDistractor(
                    text="дід",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="діде",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation={
                        "ua": "Традиційною нормативною формою для слова «дід» є форма з закінченням -у (діду, дідусю).",
                        "en": "Traditional standard vocative for 'did' is didu.",
                    },
                ),
                NounMechanicsDistractor(
                    text="дідо",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Діалектна або ненормативна форма звертання.",
                        "en": "Dialectal or non-standard address form.",
                    },
                ),
            ],
            pravopys_section="§ 87, п. 2",
            rule_summary={
                "ua": "Іменник «дід» у кличному відмінку має закінчення -у (діду).",
                "en": "Noun 'did' in vocative takes ending -u (didu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_velar_khlopchyku_5",
            category=NounMechanicsCategory.VOC_II_VELAR_SUFFIX_U,
            cefr_level="A1",
            prompt_sentence="Маленький ___, як тебе звати і де твоя мама?",
            blank_target="хлопчику",
            correct_answer="хлопчику",
            distractors=[
                NounMechanicsDistractor(
                    text="хлопчик",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="хлопчиче",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U],
                ),
                NounMechanicsDistractor(
                    text="хлопчике",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SUFFIX_U],
                ),
            ],
            pravopys_section="§ 87, п. 2",
            rule_summary={
                "ua": "Іменники зі зменшувально-пестливим суфіксом -ик приймають у кличному відмінку закінчення -у (хлопчику, братику).",
                "en": "Diminutives with suffix -yk take vocative ending -u (khlopchyku, bratyku).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 9. Vocative Case II: Soft Group (-ю)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_soft_vchytelyu_1",
            category=NounMechanicsCategory.VOC_II_SOFT_YU,
            cefr_level="A1",
            prompt_sentence="Шановний ___, поясніть нам ще раз це складне правило!",
            blank_target="вчителю",
            correct_answer="вчителю",
            distractors=[
                NounMechanicsDistractor(
                    text="вчитель",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="вчителе",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU],
                ),
                NounMechanicsDistractor(
                    text="вчительо",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT],
                ),
            ],
            pravopys_section="§ 87, п. 3",
            rule_summary={
                "ua": "Іменники м'якої групи другої відміни у кличному відмінку мають закінчення -ю (вчителю, лікарю, ковалю).",
                "en": "Second declension soft-group nouns in the vocative take ending -yu (vchyteliu, likariu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_soft_vasyliu_2",
            category=NounMechanicsCategory.VOC_II_SOFT_YU,
            cefr_level="A1",
            prompt_sentence="Друже ___, ходімо разом на футбольний матч!",
            blank_target="Василю",
            correct_answer="Василю",
            distractors=[
                NounMechanicsDistractor(
                    text="Василь",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="Василе",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU],
                ),
                NounMechanicsDistractor(
                    text="Вася",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Російська усічена розмовна форма замість українського кличного відмінка Василю.",
                        "en": "Russian clipped colloquial form instead of Ukrainian vocative Vasyliu.",
                    },
                ),
            ],
            pravopys_section="§ 87, п. 3",
            rule_summary={
                "ua": "Чоловічі імена м'якої групи мають у кличному відмінку закінчення -ю (Василю, Юрію, Олексію).",
                "en": "Masculine soft-group personal names take vocative ending -yu (Vasyliu, Yuriu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_soft_biytsiu_3",
            category=NounMechanicsCategory.VOC_II_SOFT_YU,
            cefr_level="B1",
            prompt_sentence="Мужній ___, народ дякує тобі за героїчну службу!",
            blank_target="бійцю",
            correct_answer="бійцю",
            distractors=[
                NounMechanicsDistractor(
                    text="боєць",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="бойче",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU,
                    explanation={
                        "ua": "Іменники м'якої групи на -ець мають закінчення -ю (бійцю, знавцю, хлопцю).",
                        "en": "Soft-group nouns ending in -ets take vocative -yu (biitsiu, khloptsiu).",
                    },
                ),
                NounMechanicsDistractor(
                    text="бійце",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU],
                ),
            ],
            pravopys_section="§ 87, п. 3",
            rule_summary={
                "ua": "Іменники з суфіксом -ець належать до м'якої групи і мають у кличному закінчення -ю (бійцю, молодцю, добровольцю).",
                "en": "Nouns with suffix -ets belong to the soft group and take vocative ending -yu.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_soft_andriiu_4",
            category=NounMechanicsCategory.VOC_II_SOFT_YU,
            cefr_level="A1",
            prompt_sentence="Привіт, ___, чи ти виконав домашнє завдання?",
            blank_target="Андрію",
            correct_answer="Андрію",
            distractors=[
                NounMechanicsDistractor(
                    text="Андрій",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="Андріє",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU],
                ),
                NounMechanicsDistractor(
                    text="Андрійко",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation={
                        "ua": "Пестлива форма в називному відмінку без кличного закінчення.",
                        "en": "Diminutive form in nominative without vocative ending.",
                    },
                ),
            ],
            pravopys_section="§ 87, п. 3",
            rule_summary={
                "ua": "Імена на -ій у кличному відмінку мають закінчення -ю (Андрію, Сергію, Віталію).",
                "en": "Names ending in -ii take vocative ending -yu (Andriiu, Serhiiu).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_ii_soft_tatusiu_5",
            category=NounMechanicsCategory.VOC_II_SOFT_YU,
            cefr_level="A1",
            prompt_sentence="Рідний ___, ходімо прогуляємося парком!",
            blank_target="татусю",
            correct_answer="татусю",
            distractors=[
                NounMechanicsDistractor(
                    text="татусь",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="татусе",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_E_FOR_SOFT_YU],
                ),
                NounMechanicsDistractor(
                    text="татуся",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation={
                        "ua": "Форма родового відмінка замість кличного.",
                        "en": "Genitive form instead of vocative.",
                    },
                ),
            ],
            pravopys_section="§ 87, п. 3",
            rule_summary={
                "ua": "Пестливі іменники на -усь у кличному відмінку мають закінчення -ю (татусю, дідусю).",
                "en": "Affectionate nouns ending in -us take vocative ending -yu (tatusiu, didusiu).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 10. Vocative Case I: Declension I (-о, -е, -є, -ю)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_i_hard_mamo_1",
            category=NounMechanicsCategory.VOC_I_HARD_O,
            cefr_level="A1",
            prompt_sentence="Рідна моя ___, вітаю тебе зі святом!",
            blank_target="мамо",
            correct_answer="мамо",
            distractors=[
                NounMechanicsDistractor(
                    text="мама",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="маме",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Закінчення -е належить м'якій групі, а тверда група першої відміни має закінчення -о (мамо, сестро).",
                        "en": "Ending -e belongs to soft stems; 1st declension hard stems strictly take -o (mamo, sestro).",
                    },
                ),
                NounMechanicsDistractor(
                    text="мами",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation={
                        "ua": "Форма родового відмінка замість кличного.",
                        "en": "Genitive form instead of vocative.",
                    },
                ),
            ],
            pravopys_section="§ 74, п. 1",
            rule_summary={
                "ua": "Іменники I відміни твердої групи у кличному відмінку мають закінчення -о (мамо, сестро, дружино).",
                "en": "First declension hard-group nouns take vocative ending -o (mamo, sestro).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_i_hard_mykolo_2",
            category=NounMechanicsCategory.VOC_I_HARD_O,
            cefr_level="A1",
            prompt_sentence="Добрий день, пане ___, чи вільне це місце?",
            blank_target="Миколо",
            correct_answer="Миколо",
            distractors=[
                NounMechanicsDistractor(
                    text="Микола",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="Миколе",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Чоловічі імена I відміни твердої групи приймають закінчення -о (Миколо, Петро -> Петре [II відміна]).",
                        "en": "First declension masculine hard names take ending -o (Mykolo).",
                    },
                ),
                NounMechanicsDistractor(
                    text="Коля",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Російська розмовна форма замість українського кличного Миколо.",
                        "en": "Russian colloquial form instead of Ukrainian vocative Mykolo.",
                    },
                ),
            ],
            pravopys_section="§ 74, п. 1",
            rule_summary={
                "ua": "Чоловічі імена I відміни на -а мають у кличному відмінку закінчення -о (Миколо, Кузьмо).",
                "en": "First declension masculine names ending in -a take vocative ending -o (Mykolo).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_i_hard_sestro_3",
            category=NounMechanicsCategory.VOC_I_HARD_O,
            cefr_level="A1",
            prompt_sentence="Люба моя ___, допоможи мені вибрати нову сукню!",
            blank_target="сестро",
            correct_answer="сестро",
            distractors=[
                NounMechanicsDistractor(
                    text="сестра",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="сестре",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Іменники I відміни твердої групи у кличному відмінку мають закінчення -о (сестро, мамо), а не -е.",
                        "en": "First declension hard-group nouns take vocative ending -o (sestro, mamo), not -e.",
                    },
                ),
                NounMechanicsDistractor(
                    text="сестри",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation={
                        "ua": "Форма родового відмінка або називного множини замість кличного однини.",
                        "en": "Genitive singular or nominative plural form instead of vocative singular.",
                    },
                ),
            ],
            pravopys_section="§ 74, п. 1",
            rule_summary={
                "ua": "Іменники I відміни твердої групи закінчуються на -о у кличному відмінку (сестро, мамо, весно).",
                "en": "First declension hard-group nouns take ending -o in the vocative (sestro, mamo).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_i_hard_oksano_4",
            category=NounMechanicsCategory.VOC_I_HARD_O,
            cefr_level="A1",
            prompt_sentence="Добрий ранок, шановна ___, чи готові результати аналізу?",
            blank_target="Оксано",
            correct_answer="Оксано",
            distractors=[
                NounMechanicsDistractor(
                    text="Оксана",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="Оксане",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Жіночі імена твердої групи першої відміни мають у кличному відмінку закінчення -о (Оксано, Ганно, Світлано).",
                        "en": "Feminine hard-group names of the 1st declension take -o in the vocative (Oksano, Hanno).",
                    },
                ),
                NounMechanicsDistractor(
                    text="Оксану",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation={
                        "ua": "Форма знахідного відмінка замість кличного під час звертання.",
                        "en": "Accusative form instead of vocative in direct address.",
                    },
                ),
            ],
            pravopys_section="§ 74, п. 1",
            rule_summary={
                "ua": "Жіночі імена I відміни твердої групи мають у кличному відмінку закінчення -о (Оксано, Тетяно, Ларисо).",
                "en": "Feminine names of 1st declension hard group take vocative ending -o.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_i_soft_mariie_1",
            category=NounMechanicsCategory.VOC_I_SOFT_YE_YU,
            cefr_level="A1",
            prompt_sentence="Пані ___, підпишіть, будь ласка, цей документ!",
            blank_target="Маріє",
            correct_answer="Маріє",
            distractors=[
                NounMechanicsDistractor(
                    text="Марія",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="Марійо",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT],
                ),
                NounMechanicsDistractor(
                    text="Машу",
                    interference_type=NounMechanicsInterferenceType.RUSSIAN_DECLENSION_INTERFERENCE,
                    explanation={
                        "ua": "Російська форма звертання замість українського кличного Маріє.",
                        "en": "Russian vocative borrowing instead of Ukrainian Mariie.",
                    },
                ),
            ],
            pravopys_section="§ 74, п. 2",
            rule_summary={
                "ua": "Імена I відміни на -ія у кличному відмінку мають закінчення -є (Маріє, Софіє, Надіє).",
                "en": "First declension feminine names ending in -iia take vocative ending -ye (Mariie, Sofiie).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_i_soft_zemle_2",
            category=NounMechanicsCategory.VOC_I_SOFT_YE_YU,
            cefr_level="A2",
            prompt_sentence="О рідна українська ___, ти даруєш силу й натхнення!",
            blank_target="земле",
            correct_answer="земле",
            distractors=[
                NounMechanicsDistractor(
                    text="земля",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="земльо",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT],
                ),
                NounMechanicsDistractor(
                    text="землі",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation={
                        "ua": "Форма родового або давального відмінка замість кличного.",
                        "en": "Genitive or Dative form instead of Vocative.",
                    },
                ),
            ],
            pravopys_section="§ 74, п. 2",
            rule_summary={
                "ua": "Іменники I відміни м'якої групи у кличному відмінку мають закінчення -е (земле, доле, пісне).",
                "en": "First declension soft-group nouns take vocative ending -e (zemle, dole, pisne).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_voc_i_soft_doniu_3",
            category=NounMechanicsCategory.VOC_I_SOFT_YE_YU,
            cefr_level="A1",
            prompt_sentence="Моя мила ___, швидше збирайся до школи!",
            blank_target="доню",
            correct_answer="доню",
            distractors=[
                NounMechanicsDistractor(
                    text="доня",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE],
                ),
                NounMechanicsDistractor(
                    text="доне",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_NOMINATIVE,
                    explanation={
                        "ua": "Пестливі іменники I відміни приймають закінчення -ю (доню, матусю, бабусю).",
                        "en": "Affectionate 1st declension soft nouns take ending -yu (doniu, matusiu).",
                    },
                ),
                NounMechanicsDistractor(
                    text="доньо",
                    interference_type=NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_VOCATIVE_O_FOR_SOFT],
                ),
            ],
            pravopys_section="§ 74, п. 2",
            rule_summary={
                "ua": "Пестливі іменники I відміни на -я мають у кличному відмінку закінчення -ю (доню, бабусю, матусю).",
                "en": "Affectionate 1st declension nouns take vocative ending -yu (doniu, babusiu).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 11. Instrumental Singular II: Sibilant Mixed Group (-ем)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_inst_ii_sibilant_nizhem_1",
            category=NounMechanicsCategory.INST_II_MIXED_SIBILANT_EM,
            cefr_level="A1",
            prompt_sentence="Мама нарізала свіжий хліб гострим ___.",
            blank_target="ножем",
            correct_answer="ножем",
            distractors=[
                NounMechanicsDistractor(
                    text="ножом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT],
                ),
                NounMechanicsDistractor(
                    text="ніж",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_INSTRUMENTAL,
                    explanation={
                        "ua": "Форма називного відмінка замість орудного знаряддя дії.",
                        "en": "Nominative form instead of instrumental of instrument.",
                    },
                ),
                NounMechanicsDistractor(
                    text="ножим",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN],
                ),
            ],
            pravopys_section="§ 80",
            rule_summary={
                "ua": "Іменники II відміни з основою на шиплячий (ж, ч, ш, щ) в орудному відмінку мають закінчення -ем (ножем, мечем, товаришем).",
                "en": "Second declension nouns ending in a sibilant strictly take instrumental ending -em, not -om.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_inst_ii_sibilant_tovaryshem_2",
            category=NounMechanicsCategory.INST_II_MIXED_SIBILANT_EM,
            cefr_level="A2",
            prompt_sentence="Ми довго радилися з давнім шкільним ___ про спільну поїздку.",
            blank_target="товаришем",
            correct_answer="товаришем",
            distractors=[
                NounMechanicsDistractor(
                    text="товаришом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT],
                ),
                NounMechanicsDistractor(
                    text="товариш",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_INSTRUMENTAL,
                    explanation={
                        "ua": "Форма називного відмінка замість орудного супроводу з «з».",
                        "en": "Nominative form instead of instrumental with 'z'.",
                    },
                ),
                NounMechanicsDistractor(
                    text="товаришим",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN],
                ),
            ],
            pravopys_section="§ 80",
            rule_summary={
                "ua": "Основа на шиплячий «ш» вимагає в орудному відмінку закінчення -ем (товаришем).",
                "en": "Stem ending in sibilant 'sh' requires instrumental ending -em (tovaryshem).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_inst_ii_sibilant_plashchem_3",
            category=NounMechanicsCategory.INST_II_MIXED_SIBILANT_EM,
            cefr_level="A2",
            prompt_sentence="Мандрівник накрився від сильного дощу непромокальним ___.",
            blank_target="плащем",
            correct_answer="плащем",
            distractors=[
                NounMechanicsDistractor(
                    text="плащом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT],
                ),
                NounMechanicsDistractor(
                    text="плащ",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_INSTRUMENTAL,
                    explanation={
                        "ua": "Форма називного відмінка замість орудного засобу дії.",
                        "en": "Nominative form instead of instrumental.",
                    },
                ),
                NounMechanicsDistractor(
                    text="плащим",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN],
                ),
            ],
            pravopys_section="§ 80",
            rule_summary={
                "ua": "Основа на шиплячий «щ» [шч] в орудному відмінку однини має закінчення -ем (плащем, кущем, дощем).",
                "en": "Stem ending in 'shch' takes instrumental ending -em (plashchem, doshchem).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_inst_ii_sibilant_mechem_4",
            category=NounMechanicsCategory.INST_II_MIXED_SIBILANT_EM,
            cefr_level="B1",
            prompt_sentence="Воїн уміло відбивав удари супротивника старовинним ___.",
            blank_target="мечем",
            correct_answer="мечем",
            distractors=[
                NounMechanicsDistractor(
                    text="мечом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT],
                ),
                NounMechanicsDistractor(
                    text="меч",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_INSTRUMENTAL,
                    explanation={
                        "ua": "Форма називного відмінка замість орудного знаряддя.",
                        "en": "Nominative form instead of instrumental.",
                    },
                ),
                NounMechanicsDistractor(
                    text="мечим",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN],
                ),
            ],
            pravopys_section="§ 80",
            rule_summary={
                "ua": "Основа на шиплячий «ч» приймає в орудному відмінку закінчення -ем (мечем, плечем, глядачем).",
                "en": "Stem ending in sibilant 'ch' takes instrumental ending -em (mechem).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_inst_ii_sibilant_plechem_5",
            category=NounMechanicsCategory.INST_II_MIXED_SIBILANT_EM,
            cefr_level="A2",
            prompt_sentence="Спортсмен ненароком зачепив двері травмованим ___.",
            blank_target="плечем",
            correct_answer="плечем",
            distractors=[
                NounMechanicsDistractor(
                    text="плечом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_OM_FOR_SIBILANT],
                ),
                NounMechanicsDistractor(
                    text="плече",
                    interference_type=NounMechanicsInterferenceType.FALSE_NOMINATIVE_FOR_INSTRUMENTAL,
                    explanation={
                        "ua": "Форма називного відмінка замість орудного знаряддя.",
                        "en": "Nominative form instead of instrumental.",
                    },
                ),
                NounMechanicsDistractor(
                    text="плечим",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_IM_FOR_NOUN],
                ),
            ],
            pravopys_section="§ 80",
            rule_summary={
                "ua": "Іменники середнього роду з основою на шиплячий мають в орудному відмінку закінчення -ем (плечем, прізвищем, явищем).",
                "en": "Neuter nouns with sibilant stems take ending -em in the instrumental (plechem).",
            },
        )
    )

    # ------------------------------------------------------------------------
    # 12. Animacy in Masculine Accusative (Істоти vs Неістоти)
    # ------------------------------------------------------------------------
    cards.append(
        NounMechanicsCard(
            card_id="noun_animacy_inanimate_stil_1",
            category=NounMechanicsCategory.ANIMACY_ACCUSATIVE,
            cefr_level="A1",
            prompt_sentence="Ми придбали в новий кабінет великий дерев'яний ___.",
            blank_target="стіл",
            correct_answer="стіл",
            distractors=[
                NounMechanicsDistractor(
                    text="стола",
                    interference_type=NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_INANIMATE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_INANIMATE],
                ),
                NounMechanicsDistractor(
                    text="столу",
                    interference_type=NounMechanicsInterferenceType.FALSE_DATIVE_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма давального відмінка або помилкового родового замість знахідного.",
                        "en": "Dative or false genitive form instead of accusative.",
                    },
                ),
                NounMechanicsDistractor(
                    text="столом",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість знахідного прямого додатка.",
                        "en": "Instrumental form instead of direct object accusative.",
                    },
                ),
            ],
            pravopys_section="Академічна граматика; Категорія істот і неістот",
            rule_summary={
                "ua": "Неістоти чоловічого роду в знахідному відмінку мають форму, спільну з називним (купив стіл, олівець, ніж), а не родового (*стола).",
                "en": "Masculine inanimate nouns in the accusative take the nominative form (stil, olivets), not genitive (*stola).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_animacy_inanimate_olivets_2",
            category=NounMechanicsCategory.ANIMACY_ACCUSATIVE,
            cefr_level="A1",
            prompt_sentence="Учень узяв у руку простий графітовий ___.",
            blank_target="олівець",
            correct_answer="олівець",
            distractors=[
                NounMechanicsDistractor(
                    text="олівця",
                    interference_type=NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_INANIMATE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_INANIMATE],
                ),
                NounMechanicsDistractor(
                    text="олівцю",
                    interference_type=NounMechanicsInterferenceType.FALSE_DATIVE_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма давального відмінка замість знахідного.",
                        "en": "Dative form instead of accusative.",
                    },
                ),
                NounMechanicsDistractor(
                    text="олівцем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість знахідного.",
                        "en": "Instrumental form instead of accusative.",
                    },
                ),
            ],
            pravopys_section="Академічна граматика; Категорія істот і неістот",
            rule_summary={
                "ua": "Неістота «олівець» у ролі прямого додатка вживається у формі називного відмінка: «узяв олівець» (розмовне «узяв олівця» є ненормативним).",
                "en": "Inanimate noun 'olivets' as direct object takes the nominative form in literary Ukrainian.",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_animacy_animate_vovk_3",
            category=NounMechanicsCategory.ANIMACY_ACCUSATIVE,
            cefr_level="A2",
            prompt_sentence="У густому засніженому лісі мисливці помітили сірого ___.",
            blank_target="вовка",
            correct_answer="вовка",
            distractors=[
                NounMechanicsDistractor(
                    text="вовк",
                    interference_type=NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_ANIMATE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_ANIMATE],
                ),
                NounMechanicsDistractor(
                    text="вовку",
                    interference_type=NounMechanicsInterferenceType.FALSE_DATIVE_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма давального відмінка або кличного замість знахідного істоти.",
                        "en": "Dative/vocative form instead of animate accusative.",
                    },
                ),
                NounMechanicsDistractor(
                    text="вовком",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість знахідного прямого додатка.",
                        "en": "Instrumental form instead of direct object accusative.",
                    },
                ),
            ],
            pravopys_section="Академічна граматика; Категорія істот і неістот",
            rule_summary={
                "ua": "Назви тварин та істот у знахідному відмінку обов'язково мають форму родового відмінка (помітили вовка, ведмедя, коня).",
                "en": "Animate animal nouns in the accusative strictly take the genitive form (vovka, vedmedia).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_animacy_animate_likar_4",
            category=NounMechanicsCategory.ANIMACY_ACCUSATIVE,
            cefr_level="A1",
            prompt_sentence="У коридорі лікарні пацієнти зустріли головного ___.",
            blank_target="лікаря",
            correct_answer="лікаря",
            distractors=[
                NounMechanicsDistractor(
                    text="лікар",
                    interference_type=NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_ANIMATE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_ANIMATE],
                ),
                NounMechanicsDistractor(
                    text="лікарю",
                    interference_type=NounMechanicsInterferenceType.FALSE_DATIVE_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма давального відмінка замість знахідного істоти.",
                        "en": "Dative form instead of animate accusative.",
                    },
                ),
                NounMechanicsDistractor(
                    text="лікарем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість знахідного прямого додатка.",
                        "en": "Instrumental form instead of accusative.",
                    },
                ),
            ],
            pravopys_section="Академічна граматика; Категорія істот і неістот",
            rule_summary={
                "ua": "Особи та істоти чоловічого роду в знахідному відмінку мають закінчення родового (зустріли лікаря, вчителя).",
                "en": "Masculine persons in the accusative take genitive endings (likaria, vchytelia).",
            },
        )
    )

    cards.append(
        NounMechanicsCard(
            card_id="noun_animacy_inanimate_avtomobil_5",
            category=NounMechanicsCategory.ANIMACY_ACCUSATIVE,
            cefr_level="A2",
            prompt_sentence="Сім'я вирішила придбати сучасний електричний ___.",
            blank_target="автомобіль",
            correct_answer="автомобіль",
            distractors=[
                NounMechanicsDistractor(
                    text="автомобіля",
                    interference_type=NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_INANIMATE,
                    explanation=INTERFERENCE_EXPLANATIONS[NounMechanicsInterferenceType.FALSE_ANIMACY_ACCUSATIVE_INANIMATE],
                ),
                NounMechanicsDistractor(
                    text="автомобілю",
                    interference_type=NounMechanicsInterferenceType.FALSE_DATIVE_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма давального відмінка замість знахідного неістоти.",
                        "en": "Dative form instead of inanimate accusative.",
                    },
                ),
                NounMechanicsDistractor(
                    text="автомобілем",
                    interference_type=NounMechanicsInterferenceType.FALSE_INSTRUMENTAL_FOR_ACCUSATIVE,
                    explanation={
                        "ua": "Форма орудного відмінка замість знахідного прямого додатка.",
                        "en": "Instrumental form instead of accusative.",
                    },
                ),
            ],
            pravopys_section="Академічна граматика; Категорія істот і неістот",
            rule_summary={
                "ua": "Неістоти чоловічого роду в знахідному відмінку мають форму називного: «придбати автомобіль» (а не *автомобіля).",
                "en": "Masculine inanimates in the accusative take the nominative form: 'prydbaty avtomobil' (not *avtomobilia).",
            },
        )
    )

    return cards


# ============================================================================
# Validation & Export
# ============================================================================


def validate_noun_mechanics_card(card: NounMechanicsCard) -> list[str]:
    """Validate a single card for schema integrity, uniqueness, and collision freedom."""
    errors: list[str] = []

    # 1. Option count
    if len(card.distractors) != 3:
        errors.append(f"{card.card_id}: must have exactly 3 distractors, found {len(card.distractors)}")

    # 2. Duplicate options check
    all_opt_texts = [card.correct_answer] + [d.text for d in card.distractors]
    norm_opts = [unicodedata.normalize("NFC", t.strip().lower()) for t in all_opt_texts]
    if len(set(norm_opts)) != len(norm_opts):
        errors.append(f"{card.card_id}: collision detected in options: {all_opt_texts}")

    # 3. Blank target in prompt
    if "___" not in card.prompt_sentence:
        errors.append(f"{card.card_id}: prompt sentence missing '___' fill-in blank")

    # 4. Correct answer validity
    if not card.correct_answer.strip():
        errors.append(f"{card.card_id}: correct answer is empty")

    # 5. Distractor explanation integrity
    for idx, d in enumerate(card.distractors):
        if not d.text.strip():
            errors.append(f"{card.card_id}: distractor #{idx} text is empty")
        if not d.explanation.get("ua") or not d.explanation.get("en"):
            errors.append(f"{card.card_id}: distractor #{idx} missing dual language explanation")

    return errors


def export_noun_mechanics_deck(
    output_path: Path | str = PROJECT_ROOT / "data" / "practice" / "noun_mechanics_deck.json",
) -> Path:
    """Export the canonical noun mechanics card bank to JSON."""
    cards = build_canonical_noun_mechanics_cards()
    all_errors: list[str] = []
    card_ids: set[str] = set()

    for card in cards:
        if card.card_id in card_ids:
            all_errors.append(f"Duplicate card_id found: {card.card_id}")
        card_ids.add(card.card_id)
        all_errors.extend(validate_noun_mechanics_card(card))

    if all_errors:
        raise ValueError(f"Deck validation failed with {len(all_errors)} errors:\n" + "\n".join(all_errors))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": "1.0.0",
        "title": "Ukrainian Noun Deep Mechanics Practice Deck",
        "description": "Morphological, orthographic, and declension mastery deck covering II declension genitive (-а vs -у), vocative case, instrumental sibilants, and animacy distinctions per Правопис 2019.",
        "card_count": len(cards),
        "cards": [card.to_dict() for card in cards],
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Ukrainian Noun Mechanics Practice Engine")
    parser.add_argument("--export", action="store_true", help="Export canonical cards to JSON")
    parser.add_argument("--validate", action="store_true", help="Validate all canonical cards")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "practice" / "noun_mechanics_deck.json",
        help="Target path for deck export",
    )
    args = parser.parse_args()

    cards = build_canonical_noun_mechanics_cards()
    print(f"Generated {len(cards)} canonical cards across {len(NounMechanicsCategory)} categories.")

    if args.validate or not (args.export or args.validate):
        total_errors = 0
        card_ids = set()
        for card in cards:
            if card.card_id in card_ids:
                print(f"[ERROR] Duplicate card_id: {card.card_id}")
                total_errors += 1
            card_ids.add(card.card_id)
            errs = validate_noun_mechanics_card(card)
            if errs:
                for e in errs:
                    print(f"[ERROR] {e}")
                total_errors += len(errs)
        if total_errors == 0:
            print(f"[VALIDATION OK] All {len(cards)} cards passed schema, uniqueness, and collision checks.")
        else:
            print(f"[VALIDATION FAILED] Found {total_errors} errors.")
            sys.exit(1)

    if args.export:
        out_file = export_noun_mechanics_deck(args.output)
        print(f"[EXPORT OK] Deck exported to {out_file}")


if __name__ == "__main__":
    main()
