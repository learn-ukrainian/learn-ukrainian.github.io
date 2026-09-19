"""Ukrainian Pronoun Deep Mechanics Practice Engine (Займенник).

Implements Ukrainian Pravopys 2019:
  - Part II, § 42: Правопис займенників разом, окремо, через дефіс:
    * П. 1: Разом пишуться займенники з префіксами де-, аби-, ані-, що- та суфіксом -сь (дехто, абихто, аніщо, хтось, щось),
      а також заперечні займенники з часткою ні- (ніхто, ніщо, ніякий, нічий, нікотрий, ніскільки).
    * П. 2: Через дефіс пишуться неозначені займенники з частками будь-, -небудь, казна-, хтозна-, бозна-
      (будь-хто, що-небудь, казна-що, хтозна-який, бозна-хто).
    * П. 3: Окремо (в три слова) пишуться сполуки часток будь, хтозна, казна, бозна, аби, де, ні із займенниками,
      якщо між ними стоїть прийменник (будь у кого, будь з ким, хтозна з ким, аби до кого, де з ким; ні про що, ні з ким, ні до кого, ні за яких).
  - Part III, §§ 115–124: Морфологія — Займенник:
    * § 115: Поділ займенників на розряди за значенням (особові, зворотний, присвійні, вказівні, означальні, питальні, відносні, неозначені, заперечні).
    * § 116: Відмінювання особових займенників:
      - Обов'язковий приставний н- після прийменників у непрямих відмінках 3-ї особи (до нього, біля неї, про них, на ньому).
      - Відсутність приставного н- у формах без прийменників при прямому керуванні (бачу його, чую її, зустрів їх, дав йому, допоміг їй).
      - Орудний відмінок 3-ї особи завжди має форму з н-: ним, нею, ними (як з прийменником, так і без нього).
      - Похідні прийменники з давальним відмінком (завдяки, наперекір, всупереч) не приймають приставного н- (завдяки йому, наперекір їй, всупереч їм).
    * § 117: Відмінювання зворотного займенника себе (не має форми називного відмінка; давальний собі, орудний собою, місцевий на собі).
    * § 118: Відмінювання присвійних займенників (їхній відмінюється за м'якою групою прикметників: їхній, їхнього, їхньому, їхнім, їхніми, їхніх).
    * § 119: Відмінювання вказівних (цей, той) та означальних (весь) займенників (орудний відмінок множини — всіма, не *всьома).
    * §§ 120–121: Відмінювання питально-відносних займенників (хто, що, чий).
  - Академічна стилістика та синтаксис:
    * Розрізнення 'сам' (особисто, без сторонньої допомоги) vs 'самий' (тотожність, виділення межі; викорінення кальки *самий кращий -> найкращий).
    * Вживання особового займенника після прийменника ('до них') vs присвійного означення ('їхній дім').

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


class PronounCategory(StrEnum):
    """Categories of pronoun deep mechanics practice."""

    EPENTHETIC_N_PREPOSITIONAL = "epenthetic_n_prepositional"
    EPENTHETIC_N_ABSENCE_DIRECT = "epenthetic_n_absence_direct"
    EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT = "epenthetic_n_instrumental_omnipresent"
    EPENTHETIC_N_DERIVATIVE_PREPOSITIONS = "epenthetic_n_derivative_prepositions"
    ORTHOGRAPHY_INDEFINITE_TOGETHER = "orthography_indefinite_together"
    ORTHOGRAPHY_INDEFINITE_HYPHEN = "orthography_indefinite_hyphen"
    ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION = "orthography_indefinite_split_preposition"
    ORTHOGRAPHY_NEGATIVE_TOGETHER = "orthography_negative_together"
    ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION = "orthography_negative_split_preposition"
    REFLEXIVE_SEBE_PARADIGM = "reflexive_sebe_paradigm"
    DECLENSION_VES_ALTERNATION = "declension_ves_alternation"
    DECLENSION_TSYEY_TOY = "declension_tsyey_toy"
    INTERROGATIVE_CHYI_KHTO_SHCHO = "interrogative_chyi_khto_shcho"
    SEMANTIC_SAM_VS_SAMYI = "semantic_sam_vs_samyi"
    POSSESSIVE_YIKHNIY_VS_YIKH = "possessive_yikhniy_vs_yikh"


class PronounInterferenceType(StrEnum):
    """Taxonomy of morphological, orthographic, phonological, and syntactic pronoun misconceptions."""

    SPURIOUS_EPENTHETIC_N = "spurious_epenthetic_n"
    MISSING_EPENTHETIC_N = "missing_epenthetic_n"
    CORRUPTED_INSTRUMENTAL_FORM = "corrupted_instrumental_form"
    WRONGLY_ATTACHED_DERIVATIVE_N = "wrongly_attached_derivative_n"
    HYPHENATED_INDEFINITE_CALQUE = "hyphenated_indefinite_calque"
    SEPARATE_INDEFINITE_CALQUE = "separate_indefinite_calque"
    SOLID_WRITTEN_HYPHEN_PARTICLE = "solid_written_hyphen_particle"
    SEPARATE_WRITTEN_HYPHEN_PARTICLE = "separate_written_hyphen_particle"
    HYPHENATED_SPLIT_PREPOSITION = "hyphenated_split_preposition"
    SOLID_SPLIT_PREPOSITION = "solid_split_preposition"
    EXTERNAL_PREPOSITION_RUSSIAN_CALQUE = "external_preposition_russian_calque"
    SEPARATE_NEGATIVE_PRONOUN = "separate_negative_pronoun"
    HYPHENATED_NEGATIVE_PRONOUN = "hyphenated_negative_pronoun"
    DEFECTIVE_REFL_NOMINATIVE = "defective_refl_nominative"
    CORRUPTED_DECLENSION_STEM = "corrupted_declension_stem"
    CONFUSION_SAM_VS_SAMYI = "confusion_sam_vs_samyi"
    CONFUSION_POSSESSIVE_VS_PERSONAL = "confusion_possessive_vs_personal"


@dataclass(frozen=True)
class PronounDistractor:
    """A distractor option with specific linguistic explanation."""

    text: str
    interference_type: PronounInterferenceType
    explanation_ua: str
    explanation_en: str


@dataclass(frozen=True)
class PronounCard:
    """Canonical pronoun practice item."""

    card_id: str
    category: PronounCategory
    cefr_level: str
    sentence_before: str
    sentence_after: str
    correct_answer: str
    distractors: tuple[PronounDistractor, PronounDistractor, PronounDistractor]
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


def resolve_epenthesis_rule(category: PronounCategory) -> tuple[str, str, str]:
    """Return citation and summaries for epenthetic n- rules."""
    citation = "Правопис 2019 § 116"
    if category == PronounCategory.EPENTHETIC_N_PREPOSITIONAL:
        ua = "Після прийменників у формах непрямих відмінків 3-ї особи обов'язково з'являється приставний [н-]: до нього, біля неї, про них, на ньому."
        en = "After prepositions in oblique cases of 3rd-person pronouns, epenthetic [n-] is compulsory: до нього, біля неї, про них, на ньому."
    elif category == PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT:
        ua = "Без прийменників у прямому керуванні (родовий, знахідний, давальний) приставний [н-] не вживається: бачу його, чую її, зустрів їх, дав йому."
        en = "Without prepositions in direct case government (Gen/Acc/Dat), epenthetic [n-] is not used: бачу його, чую її, зустрів їх, дав йому."
    elif category == PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT:
        ua = "В орудному відмінку 3-ї особи звук [н] присутній завжди (як з прийменником, так і без нього): ним, нею, ними."
        en = "In the Instrumental case of 3rd-person pronouns, [n-] is always present (both with and without prepositions): ним, нею, ними."
    elif category == PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS:
        ua = "Після похідних прийменників, що керують давальним відмінком (завдяки, наперекір, всупереч), приставний [н-] не з'являється: завдяки йому, наперекір їй."
        en = "After derivative prepositions governing Dative (завдяки, наперекір, всупереч), epenthetic [n-] is not attached: завдяки йому, наперекір їй."
    else:
        raise ValueError(f"Category {category} is not an epenthesis category")
    return citation, ua, en


def resolve_orthography_rule(category: PronounCategory) -> tuple[str, str, str]:
    """Return citation and summaries for pronoun orthography rules."""
    citation = "Правопис 2019 § 42"
    if category == PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER:
        ua = "Неозначені займенники з частками-префіксами де-, аби-, ані- та суфіксом -сь пишуться разом: дехто, абихто, хтось, щось."
        en = "Indefinite pronouns with prefixes де-, аби-, ані- and suffix -сь are written as a single word: дехто, абихто, хтось, щось."
    elif category == PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN:
        ua = "Неозначені займенники з частками будь-, -небудь, казна-, хтозна-, бозна- пишуться через дефіс: будь-хто, хто-небудь, казна-що, хтозна-який."
        en = "Indefinite pronouns with particles будь-, -небудь, казна-, хтозна-, бозна- are written with a hyphen: будь-хто, хто-небудь, казна-що, хтозна-який."
    elif category == PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION:
        ua = "Якщо між часткою (будь, хтозна, казна, бозна, аби, де) та займенником стоїть прийменник, уся сполука пишеться окремо трьома словами: будь у кого, будь з ким, хтозна з ким."
        en = "When a preposition intervenes between the particle (будь, хтозна, казна, бозна, аби, де) and the pronoun, all three words are written separately: будь у кого, будь з ким, хтозна з ким."
    elif category == PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER:
        ua = "Заперечні займенники з префіксом ні- без прийменників пишуться разом: ніхто, ніщо, ніякий, нічий."
        en = "Negative pronouns with prefix ні- without prepositions are written as a single word: ніхто, ніщо, ніякий, нічий."
    elif category == PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION:
        ua = "За наявності прийменника заперечний займенник розпадається на три окремих слова (ні + прийменник + форма займенника): ні про що, ні з ким, ні до кого."
        en = "When a preposition is present, negative pronouns split into three separate words (ні + preposition + pronoun): ні про що, ні з ким, ні до кого."
    else:
        raise ValueError(f"Category {category} is not an orthography category")
    return citation, ua, en


def resolve_reflexive_sebe_rule() -> tuple[str, str, str]:
    """Return citation and summaries for reflexive pronoun себе."""
    citation = "Правопис 2019 § 117"
    ua = "Зворотний займенник 'себе' не має називного відмінка; давальний відмінок — собі, орудний — собою, місцевий — на собі (при собі)."
    en = "Reflexive pronoun 'себе' lacks Nominative; Dative is собі, Instrumental is собою, Locative is на собі (при собі)."
    return citation, ua, en


def resolve_declension_ves_rule() -> tuple[str, str, str]:
    """Return citation and summaries for pronoun весь."""
    citation = "Правопис 2019 § 119"
    ua = "Займенник 'весь' в орудному відмінку множини має нормативне закінчення -іма: всіма (форми *всьома чи *всеми є ненормативними)."
    en = "The pronoun 'весь' in Instrumental plural takes ending -іма: всіма (forms *всьома and *всеми are ungrammatical)."
    return citation, ua, en


def resolve_demonstrative_rule() -> tuple[str, str, str]:
    """Return citation and summaries for demonstrative pronouns цей and той."""
    citation = "Правопис 2019 § 119"
    ua = "Вказівні займенники 'цей' та 'той' у формах множини та непрямих відмінків однини відмінюються за твердим чи м'яким типом: цими, тими, цього, тому."
    en = "Demonstrative pronouns 'цей' and 'той' decline according to hard/soft pronominal patterns: цими, тими, цього, тому."
    return citation, ua, en


def resolve_interrogative_rule() -> tuple[str, str, str]:
    """Return citation and summaries for interrogative pronouns хто, що, чий."""
    citation = "Правопис 2019 §§ 120–121"
    ua = "Питально-відносні займенники хто, що, чий змінюються за відмінками (кого, чого; кому, чому; ким, чим; чийого, чиєму, чиїм, чиїми)."
    en = "Interrogative-relative pronouns хто, що, чий decline according to pronominal paradigms (кого, чого; кому, чому; ким, чим; чийого, чиєму, чиїм, чиїми)."
    return citation, ua, en


def resolve_sam_vs_samyi_rule() -> tuple[str, str, str]:
    """Return citation and summaries for semantic distinction сам vs самий."""
    citation = "Академічна стилістика та граматика"
    ua = "'Сам' означає дію суб'єкта без сторонньої допомоги або особисто; 'самий' вказує на тотожність (той самий) чи просторову/часову межу (з самого ранку)."
    en = "'Сам' expresses unassisted or personal action; 'самий' expresses identity (той самий) or spatial/temporal boundary (з самого ранку)."
    return citation, ua, en


def resolve_possessive_yikhniy_rule() -> tuple[str, str, str]:
    """Return citation and summaries for possessive їхній vs personal їх."""
    citation = "Правопис 2019 § 118"
    ua = "Присвійний займенник 'їхній' узгоджується з іменником за зразком м'якої групи прикметників; після прийменників з особовим значенням вживається форма 'до них'."
    en = "Possessive pronoun 'їхній' declines like soft-stem adjectives; after prepositions in personal reference, 3rd-person 'до них' is used."
    return citation, ua, en


def build_canonical_pronoun_cards() -> list[PronounCard]:
    """Build canonical deck of 75 Ukrainian pronoun deep mechanics cards across 15 categories."""
    cit_ep, ua_ep_prep, en_ep_prep = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_PREPOSITIONAL)
    _, ua_ep_dir, en_ep_dir = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT)
    _, ua_ep_ins, en_ep_ins = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT)
    _, ua_ep_der, en_ep_der = resolve_epenthesis_rule(PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS)

    cit_orth, ua_orth_tog, en_orth_tog = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER)
    _, ua_orth_hyph, en_orth_hyph = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN)
    _, ua_orth_split_indef, en_orth_split_indef = resolve_orthography_rule(
        PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION
    )
    _, ua_orth_neg_tog, en_orth_neg_tog = resolve_orthography_rule(PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER)
    _, ua_orth_split_neg, en_orth_split_neg = resolve_orthography_rule(
        PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION
    )

    cit_refl, ua_refl, en_refl = resolve_reflexive_sebe_rule()
    cit_ves, ua_ves, en_ves = resolve_declension_ves_rule()
    cit_dem, ua_dem, en_dem = resolve_demonstrative_rule()
    cit_int, ua_int, en_int = resolve_interrogative_rule()
    cit_sam, ua_sam, en_sam = resolve_sam_vs_samyi_rule()
    cit_poss, ua_poss, en_poss = resolve_possessive_yikhniy_rule()

    cards: list[PronounCard] = [
        # ====================================================================
        # 1. EPENTHETIC_N_PREPOSITIONAL (5 cards) [Правопис 2019 § 116]
        # ====================================================================
        PronounCard(
            card_id="pron_epenth_prep_do_nyoho",
            category=PronounCategory.EPENTHETIC_N_PREPOSITIONAL,
            cefr_level="A2",
            sentence_before="Ми давно не бачилися, тому я вирішив завітати",
            sentence_after="у гості.",
            correct_answer="до нього",
            distractors=(
                PronounDistractor(
                    text="до його",
                    interference_type=PronounInterferenceType.MISSING_EPENTHETIC_N,
                    explanation_ua="Після прийменника у формах непрямих відмінків 3-ї особи обов'язковий приставний н-: 'до нього'.",
                    explanation_en="After prepositions, 3rd-person pronouns compulsory take epenthetic n-: 'до нього'.",
                ),
                PronounDistractor(
                    text="до йому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'до' вимагає родового відмінка ('до нього'), а не давального 'йому'.",
                    explanation_en="Preposition 'до' requires Genitive ('до нього'), not Dative 'йому'.",
                ),
                PronounDistractor(
                    text="до нему",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Ненормативна форма закінчення; родовий відмінок чоловічого роду з прийменником — 'до нього'.",
                    explanation_en="Ungrammatical ending; Genitive masculine after preposition is 'до нього'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_prep,
            rule_summary_en=en_ep_prep,
        ),
        PronounCard(
            card_id="pron_epenth_prep_bilya_neyi",
            category=PronounCategory.EPENTHETIC_N_PREPOSITIONAL,
            cefr_level="A2",
            sentence_before="Уся родина зібралася",
            sentence_after=", щоб привітати з ювілеєм.",
            correct_answer="біля неї",
            distractors=(
                PronounDistractor(
                    text="біля її",
                    interference_type=PronounInterferenceType.MISSING_EPENTHETIC_N,
                    explanation_ua="Після прийменника обов'язковий приставний н- у формах 3-ї особи жіночого роду: 'біля неї'.",
                    explanation_en="After prepositions, 3rd-person feminine pronouns require epenthetic n-: 'біля неї'.",
                ),
                PronounDistractor(
                    text="біля їй",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'біля' вимагає родового відмінка ('біля неї'), а не давального 'їй'.",
                    explanation_en="Preposition 'біля' governs Genitive ('біля неї'), not Dative 'їй'.",
                ),
                PronounDistractor(
                    text="біля ній",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'ній' є місцевим або давальним відмінком; з прийменником 'біля' вживається родовий 'біля неї'.",
                    explanation_en="'ній' is Locative/Dative; preposition 'біля' requires Genitive 'біля неї'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_prep,
            rule_summary_en=en_ep_prep,
        ),
        PronounCard(
            card_id="pron_epenth_prep_pro_nykh",
            category=PronounCategory.EPENTHETIC_N_PREPOSITIONAL,
            cefr_level="A2",
            sentence_before="Ми щиро пишаємося нашими захисниками й завжди піклуємося",
            sentence_after=".",
            correct_answer="про них",
            distractors=(
                PronounDistractor(
                    text="про їх",
                    interference_type=PronounInterferenceType.MISSING_EPENTHETIC_N,
                    explanation_ua="Після прийменника у знахідному відмінку множини обов'язковий приставний н-: 'про них'.",
                    explanation_en="After prepositions in Accusative plural, epenthetic n- is compulsory: 'про них'.",
                ),
                PronounDistractor(
                    text="про їм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'про' вимагає знахідного відмінка ('про них'), а не давального 'їм'.",
                    explanation_en="Preposition 'про' governs Accusative ('про них'), not Dative 'їм'.",
                ),
                PronounDistractor(
                    text="про їхніх",
                    interference_type=PronounInterferenceType.CONFUSION_POSSESSIVE_VS_PERSONAL,
                    explanation_ua="'Їхній' — це присвійний займенник; у ролі особового додатка після 'про' вживається 'про них'.",
                    explanation_en="'Їхній' is possessive; personal pronoun object after 'про' requires 'про них'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_prep,
            rule_summary_en=en_ep_prep,
        ),
        PronounCard(
            card_id="pron_epenth_prep_na_nyomu",
            category=PronounCategory.EPENTHETIC_N_PREPOSITIONAL,
            cefr_level="A2",
            sentence_before="Цей старовинний годинник дорогий для мене, бо",
            sentence_after="викарбувано герб родини.",
            correct_answer="на ньому",
            distractors=(
                PronounDistractor(
                    text="на йому",
                    interference_type=PronounInterferenceType.MISSING_EPENTHETIC_N,
                    explanation_ua="У місцевому відмінку після прийменника 'на' обов'язковий приставний н-: 'на ньому'.",
                    explanation_en="In Locative after preposition 'на', epenthetic n- is compulsory: 'на ньому'.",
                ),
                PronounDistractor(
                    text="на його",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'на' у значенні місця вимагає місцевого відмінка ('на ньому'), а не знахідного 'його'.",
                    explanation_en="Preposition 'на' denoting location requires Locative ('на ньому'), not Accusative 'його'.",
                ),
                PronounDistractor(
                    text="на них",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'годинник' — однина; форма множини 'на них' порушує узгодження за числом.",
                    explanation_en="'годинник' is singular; plural 'на них' violates number agreement.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_prep,
            rule_summary_en=en_ep_prep,
        ),
        PronounCard(
            card_id="pron_epenth_prep_pid_nyoho",
            category=PronounCategory.EPENTHETIC_N_PREPOSITIONAL,
            cefr_level="B1",
            sentence_before="Вона знайшла загублений зошит і поклала",
            sentence_after="святкову листівку.",
            correct_answer="під нього",
            distractors=(
                PronounDistractor(
                    text="під його",
                    interference_type=PronounInterferenceType.MISSING_EPENTHETIC_N,
                    explanation_ua="Після прийменників у непрямих відмінках 3-ї особи обов'язковий приставний н-: 'під нього'.",
                    explanation_en="After prepositions in oblique 3rd-person forms, epenthetic n- is compulsory: 'під нього'.",
                ),
                PronounDistractor(
                    text="під йому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'під' не сполучається з давальним відмінком 'йому'.",
                    explanation_en="Preposition 'під' does not combine with Dative 'йому'.",
                ),
                PronounDistractor(
                    text="під ним",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'покласти' позначає напрямок дії (куди?), що вимагає знахідного відмінка 'під нього' (орудний 'під ним' вказував би на статичне місце).",
                    explanation_en="'покласти' indicates direction of motion (куди?), requiring Accusative 'під нього' rather than static Instrumental 'під ним'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_prep,
            rule_summary_en=en_ep_prep,
        ),
        # ====================================================================
        # 2. EPENTHETIC_N_ABSENCE_DIRECT (5 cards) [Правопис 2019 § 116]
        # ====================================================================
        PronounCard(
            card_id="pron_epenth_abs_yoho",
            category=PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT,
            cefr_level="A2",
            sentence_before="Я давно знаю цього фахівця і дуже ціную",
            sentence_after="за порядність.",
            correct_answer="його",
            distractors=(
                PronounDistractor(
                    text="нього",
                    interference_type=PronounInterferenceType.SPURIOUS_EPENTHETIC_N,
                    explanation_ua="Без прийменника у прямому знахідному відмінку приставний н- не вживається: правильно 'ціную його'.",
                    explanation_en="Without a preposition in direct Accusative, epenthetic n- is not used: 'ціную його'.",
                ),
                PronounDistractor(
                    text="йому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'цінувати' керує знахідним відмінком прямого додатка (кого?), а не давальним 'йому'.",
                    explanation_en="'цінувати' governs direct Accusative (кого?), not Dative 'йому'.",
                ),
                PronounDistractor(
                    text="їх",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'фахівець' вжито в однині; форма множини 'їх' порушує узгодження за числом.",
                    explanation_en="'фахівець' is singular; plural 'їх' violates number agreement.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_dir,
            rule_summary_en=en_ep_dir,
        ),
        PronounCard(
            card_id="pron_epenth_abs_yiyi",
            category=PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT,
            cefr_level="A2",
            sentence_before="Вона щиро усміхнулася, коли зустріла",
            sentence_after="на вокзалі.",
            correct_answer="її",
            distractors=(
                PronounDistractor(
                    text="неї",
                    interference_type=PronounInterferenceType.SPURIOUS_EPENTHETIC_N,
                    explanation_ua="Без прийменника у знахідному відмінку приставний н- не вживається: правильно 'зустріла її'.",
                    explanation_en="Without a preposition in Accusative, epenthetic n- is not used: 'зустріла її'.",
                ),
                PronounDistractor(
                    text="їй",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'зустріти' вимагає знахідного відмінка прямого додатка (кого?), а не давального 'їй'.",
                    explanation_en="'зустріти' governs direct Accusative (кого?), not Dative 'їй'.",
                ),
                PronounDistractor(
                    text="ній",
                    interference_type=PronounInterferenceType.SPURIOUS_EPENTHETIC_N,
                    explanation_ua="Форма 'ній' містить приставний н- і є формою давального/місцевого; прямий додаток вимагає 'її'.",
                    explanation_en="'ній' contains epenthetic n- and is Dative/Locative; direct object requires 'її'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_dir,
            rule_summary_en=en_ep_dir,
        ),
        PronounCard(
            card_id="pron_epenth_abs_yikh",
            category=PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT,
            cefr_level="A2",
            sentence_before="Учитель уважно вислухав учнів і похвалив",
            sentence_after="за старанність.",
            correct_answer="їх",
            distractors=(
                PronounDistractor(
                    text="них",
                    interference_type=PronounInterferenceType.SPURIOUS_EPENTHETIC_N,
                    explanation_ua="Без прийменника у знахідному відмінку прямого додатка приставний н- не вживається: правильно 'похвалив їх'.",
                    explanation_en="Without a preposition in direct Accusative, epenthetic n- is not used: 'похвалив їх'.",
                ),
                PronounDistractor(
                    text="їм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'похвалити' керує знахідним відмінком прямого додатка (кого?), а не давальним 'їм'.",
                    explanation_en="'похвалити' governs direct Accusative (кого?), not Dative 'їм'.",
                ),
                PronounDistractor(
                    text="їхніх",
                    interference_type=PronounInterferenceType.CONFUSION_POSSESSIVE_VS_PERSONAL,
                    explanation_ua="'Їхній' — присвійний займенник; у ролі особового додатка вживається форма 'їх'.",
                    explanation_en="'Їхній' is possessive; personal pronoun direct object is 'їх'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_dir,
            rule_summary_en=en_ep_dir,
        ),
        PronounCard(
            card_id="pron_epenth_abs_yomu",
            category=PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT,
            cefr_level="A2",
            sentence_before="Якщо ти побачиш нашого тренера, обов'язково передай",
            sentence_after="цей лист.",
            correct_answer="йому",
            distractors=(
                PronounDistractor(
                    text="ньому",
                    interference_type=PronounInterferenceType.SPURIOUS_EPENTHETIC_N,
                    explanation_ua="Без прийменника у давальному відмінку приставний н- не вживається: правильно 'передай йому'.",
                    explanation_en="Without a preposition in Dative, epenthetic n- is not used: 'передай йому'.",
                ),
                PronounDistractor(
                    text="його",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'передати' керує давальним відмінком адресата (кому?), а не родовим/знахідним 'його'.",
                    explanation_en="'передати' governs Dative for recipient (кому?), not Genitive/Accusative 'його'.",
                ),
                PronounDistractor(
                    text="їм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Адресат 'тренер' — в однині; форма множини 'їм' порушує числове узгодження.",
                    explanation_en="'тренер' is singular; plural 'їм' violates number agreement.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_dir,
            rule_summary_en=en_ep_dir,
        ),
        PronounCard(
            card_id="pron_epenth_abs_yiy",
            category=PronounCategory.EPENTHETIC_N_ABSENCE_DIRECT,
            cefr_level="A2",
            sentence_before="Сестра готувалася до виступу, тому ми допомогли",
            sentence_after="з презентацією.",
            correct_answer="їй",
            distractors=(
                PronounDistractor(
                    text="ній",
                    interference_type=PronounInterferenceType.SPURIOUS_EPENTHETIC_N,
                    explanation_ua="Без прийменника у давальному відмінку приставний н- не вживається: правильно 'допомогли їй'.",
                    explanation_en="Without a preposition in Dative, epenthetic n- is not used: 'допомогли їй'.",
                ),
                PronounDistractor(
                    text="неї",
                    interference_type=PronounInterferenceType.SPURIOUS_EPENTHETIC_N,
                    explanation_ua="Форма 'неї' містить приставний н- і вживається лише з прийменниками у родовому; тут потрібен давальний 'їй'.",
                    explanation_en="'неї' has epenthetic n- and is used with prepositions in Genitive; Dative without preposition is 'їй'.",
                ),
                PronounDistractor(
                    text="її",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'допомогти' керує давальним відмінком адресата (кому?), а не родовим/знахідним 'її'.",
                    explanation_en="'допомогти' governs Dative (кому?), not Genitive/Accusative 'її'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_dir,
            rule_summary_en=en_ep_dir,
        ),
        # ====================================================================
        # 3. EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT (5 cards) [Правопис 2019 § 116]
        # ====================================================================
        PronounCard(
            card_id="pron_epenth_ins_nym",
            category=PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT,
            cefr_level="B1",
            sentence_before="Він досвідчений інженер, і весь колектив щиро пишається",
            sentence_after="за високий професіоналізм.",
            correct_answer="ним",
            distractors=(
                PronounDistractor(
                    text="ім",
                    interference_type=PronounInterferenceType.CORRUPTED_INSTRUMENTAL_FORM,
                    explanation_ua="Орудний відмінок особового займенника 3-ї особи завжди має форму 'ним' (з початковим н-), форма *ім не існує.",
                    explanation_en="Instrumental 3rd-person pronoun always has initial n-: 'ним'; form *ім does not exist.",
                ),
                PronounDistractor(
                    text="його",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'пишатися' керує орудним відмінком (ким?), а не родовим/знахідним 'його'.",
                    explanation_en="'пишатися' governs Instrumental (ким?), not Genitive/Accusative 'його'.",
                ),
                PronounDistractor(
                    text="йому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'пишатися' вимагає орудного відмінка ('ним'), а не давального 'йому'.",
                    explanation_en="'пишатися' requires Instrumental ('ним'), not Dative 'йому'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_ins,
            rule_summary_en=en_ep_ins,
        ),
        PronounCard(
            card_id="pron_epenth_ins_neyu",
            category=PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT,
            cefr_level="B1",
            sentence_before="Вона здобула блискучу перемогу, і глядачі захоплювалися",
            sentence_after="на змаганнях.",
            correct_answer="нею",
            distractors=(
                PronounDistractor(
                    text="єю",
                    interference_type=PronounInterferenceType.CORRUPTED_INSTRUMENTAL_FORM,
                    explanation_ua="Орудний відмінок займенника 'вона' завжди має нормативну форму 'нею' (з початковим н-), форма *єю є спотворенням.",
                    explanation_en="Instrumental of 'вона' strictly requires initial n-: 'нею'; *єю is a corrupted form.",
                ),
                PronounDistractor(
                    text="їй",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'захоплюватися' вимагає орудного відмінка (ким?), а не давального 'їй'.",
                    explanation_en="'захоплюватися' requires Instrumental (ким?), not Dative 'їй'.",
                ),
                PronounDistractor(
                    text="її",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'захоплюватися' керує орудним відмінком ('нею'), а не знахідним 'її'.",
                    explanation_en="'захоплюватися' governs Instrumental ('нею'), not Accusative 'її'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_ins,
            rule_summary_en=en_ep_ins,
        ),
        PronounCard(
            card_id="pron_epenth_ins_nymy",
            category=PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT,
            cefr_level="B1",
            sentence_before="Команда показала відмінний результат, і тренер пишається",
            sentence_after="перед усіма глядачами.",
            correct_answer="ними",
            distractors=(
                PronounDistractor(
                    text="їми",
                    interference_type=PronounInterferenceType.CORRUPTED_INSTRUMENTAL_FORM,
                    explanation_ua="Орудний відмінок множини 3-ї особи завжди має нормативну форму 'ними' (з початковим н-); форма *їми є застарілою або ненормативною.",
                    explanation_en="Instrumental plural 3rd-person pronoun always has initial n-: 'ними'; form *їми is ungrammatical in standard Ukrainian.",
                ),
                PronounDistractor(
                    text="їх",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'пишатися' вимагає орудного відмінка ('ними'), а не родового/знахідного 'їх'.",
                    explanation_en="'пишатися' requires Instrumental ('ними'), not Genitive/Accusative 'їх'.",
                ),
                PronounDistractor(
                    text="їм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'пишатися' керує орудним відмінком (ким?), а не давальним 'їм'.",
                    explanation_en="'пишатися' governs Instrumental (ким?), not Dative 'їм'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_ins,
            rule_summary_en=en_ep_ins,
        ),
        PronounCard(
            card_id="pron_epenth_ins_iz_nym",
            category=PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT,
            cefr_level="B1",
            sentence_before="Ми довго обговорювали новий план проєкту разом",
            sentence_after="в робочому кабінеті.",
            correct_answer="із ним",
            distractors=(
                PronounDistractor(
                    text="із ім",
                    interference_type=PronounInterferenceType.CORRUPTED_INSTRUMENTAL_FORM,
                    explanation_ua="Орудний відмінок 3-ї особи завжди має початковий звук [н]: 'із ним', форма *із ім неприпустима.",
                    explanation_en="Instrumental 3rd-person pronoun always has initial n-: 'із ним'; *із ім is ungrammatical.",
                ),
                PronounDistractor(
                    text="із його",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'із' у значенні сумісності вимагає орудного відмінка ('із ним'), а не родового 'його'.",
                    explanation_en="Preposition 'із' expressing accompaniment governs Instrumental ('із ним'), not Genitive 'його'.",
                ),
                PronounDistractor(
                    text="із йому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'із' не вживається з давальним відмінком 'йому'.",
                    explanation_en="Preposition 'із' does not combine with Dative 'йому'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_ins,
            rule_summary_en=en_ep_ins,
        ),
        PronounCard(
            card_id="pron_epenth_ins_iz_neyu",
            category=PronounCategory.EPENTHETIC_N_INSTRUMENTAL_OMNIPRESENT,
            cefr_level="B1",
            sentence_before="Мати вийшла в садок і довго розмовляла",
            sentence_after="про майбутній вступ до університету.",
            correct_answer="із нею",
            distractors=(
                PronounDistractor(
                    text="із єю",
                    interference_type=PronounInterferenceType.CORRUPTED_INSTRUMENTAL_FORM,
                    explanation_ua="Орудний відмінок 3-ї особи жіночого роду завжди починається на н-: 'із нею', а не *із єю.",
                    explanation_en="Instrumental 3rd-person feminine always starts with n-: 'із нею', not *із єю.",
                ),
                PronounDistractor(
                    text="із їй",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'із' у значенні спільної дії вимагає орудного відмінка ('із нею'), а не давального 'їй'.",
                    explanation_en="Preposition 'із' expressing interaction governs Instrumental ('із нею'), not Dative 'їй'.",
                ),
                PronounDistractor(
                    text="із неї",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'неї' — це родовий відмінок; з прийменником сумісності 'із' вживається орудний 'із нею'.",
                    explanation_en="'неї' is Genitive; preposition 'із' of accompaniment takes Instrumental 'із нею'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_ins,
            rule_summary_en=en_ep_ins,
        ),
        # ====================================================================
        # 4. EPENTHETIC_N_DERIVATIVE_PREPOSITIONS (5 cards) [Правопис 2019 § 116]
        # ====================================================================
        PronounCard(
            card_id="pron_epenth_der_zavdyaky_yomu",
            category=PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS,
            cefr_level="B2",
            sentence_before="Складний проєкт було успішно завершено лише",
            sentence_after="та його наполегливості.",
            correct_answer="завдяки йому",
            distractors=(
                PronounDistractor(
                    text="завдяки ньому",
                    interference_type=PronounInterferenceType.WRONGLY_ATTACHED_DERIVATIVE_N,
                    explanation_ua="Після прийменника 'завдяки', що походить від дієприслівника і керує давальним відмінком, приставний н- не додається: 'завдяки йому'.",
                    explanation_en="After derivative preposition 'завдяки' governing Dative, epenthetic n- is not attached: 'завдяки йому'.",
                ),
                PronounDistractor(
                    text="завдяки його",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'завдяки' вимагає давального відмінка (кому?), а не родового 'його'.",
                    explanation_en="Preposition 'завдяки' requires Dative (кому?), not Genitive 'його'.",
                ),
                PronounDistractor(
                    text="завдяки їм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Контекст узгоджується з одниною 'його наполегливості'; форма множини 'їм' порушує семантичне узгодження.",
                    explanation_en="Context agrees with singular 'його наполегливості'; plural 'їм' violates semantic agreement.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_der,
            rule_summary_en=en_ep_der,
        ),
        PronounCard(
            card_id="pron_epenth_der_naperekir_yiy",
            category=PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS,
            cefr_level="B2",
            sentence_before="Студент успішно склав непростий іспит",
            sentence_after=", показавши бездоганні знання предмета.",
            correct_answer="наперекір їй",
            distractors=(
                PronounDistractor(
                    text="наперекір ній",
                    interference_type=PronounInterferenceType.WRONGLY_ATTACHED_DERIVATIVE_N,
                    explanation_ua="Після прийменника 'наперекір' з давальним відмінком приставний н- не вживається: правильно 'наперекір їй'.",
                    explanation_en="After preposition 'наперекір' governing Dative, epenthetic n- is not used: 'наперекір їй'.",
                ),
                PronounDistractor(
                    text="наперекір неї",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'наперекір' вимагає давального відмінка (кому?), а не родового 'неї'.",
                    explanation_en="Preposition 'наперекір' requires Dative (кому?), not Genitive 'неї'.",
                ),
                PronounDistractor(
                    text="наперекір її",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'наперекір' вимагає давального відмінка 'їй', а не знахідного 'її'.",
                    explanation_en="Preposition 'наперекір' requires Dative 'їй', not Accusative 'її'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_der,
            rule_summary_en=en_ep_der,
        ),
        PronounCard(
            card_id="pron_epenth_der_vsuperech_yim",
            category=PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS,
            cefr_level="B2",
            sentence_before="Важливе рішення було ухвалено",
            sentence_after="та їхнім постійним запереченням.",
            correct_answer="всупереч їм",
            distractors=(
                PronounDistractor(
                    text="всупереч нім",
                    interference_type=PronounInterferenceType.WRONGLY_ATTACHED_DERIVATIVE_N,
                    explanation_ua="Після прийменника 'всупереч' з давальним відмінком приставний н- не додається: правильно 'всупереч їм'.",
                    explanation_en="After preposition 'всупереч' with Dative, epenthetic n- is not attached: 'всупереч їм'.",
                ),
                PronounDistractor(
                    text="всупереч їх",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'всупереч' вимагає давального відмінка (кому?), а не родового/знахідного 'їх'.",
                    explanation_en="Preposition 'всупереч' requires Dative (кому?), not Genitive/Accusative 'їх'.",
                ),
                PronounDistractor(
                    text="всупереч них",
                    interference_type=PronounInterferenceType.WRONGLY_ATTACHED_DERIVATIVE_N,
                    explanation_ua="Прийменник 'всупереч' керує давальним відмінком без приставного н- ('їм'), а не родовим з н- 'них'.",
                    explanation_en="Preposition 'всупереч' governs Dative without n- ('їм'), not Genitive with n- 'них'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_der,
            rule_summary_en=en_ep_der,
        ),
        PronounCard(
            card_id="pron_epenth_der_zavdyaky_yiy",
            category=PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS,
            cefr_level="B2",
            sentence_before="Наша футбольна команда здобула блискучу перемогу",
            sentence_after=", адже вона забила вирішальний гол.",
            correct_answer="завдяки їй",
            distractors=(
                PronounDistractor(
                    text="завдяки ній",
                    interference_type=PronounInterferenceType.WRONGLY_ATTACHED_DERIVATIVE_N,
                    explanation_ua="Після похідного прийменника 'завдяки' у давальному відмінку приставний н- не з'являється: правильно 'завдяки їй'.",
                    explanation_en="After derivative preposition 'завдяки' in Dative, epenthetic n- does not appear: 'завдяки їй'.",
                ),
                PronounDistractor(
                    text="завдяки неї",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'завдяки' керує давальним відмінком (кому?), а не родовим 'неї'.",
                    explanation_en="Preposition 'завдяки' governs Dative (кому?), not Genitive 'неї'.",
                ),
                PronounDistractor(
                    text="завдяки її",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'завдяки' вимагає давального відмінка 'їй', а не знахідного 'її'.",
                    explanation_en="Preposition 'завдяки' requires Dative 'їй', not Accusative 'її'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_der,
            rule_summary_en=en_ep_der,
        ),
        PronounCard(
            card_id="pron_epenth_der_naperekir_yim",
            category=PronounCategory.EPENTHETIC_N_DERIVATIVE_PREPOSITIONS,
            cefr_level="B2",
            sentence_before="Ми вирушили у важку дорогу",
            sentence_after=", не зважаючи на численні застереження.",
            correct_answer="наперекір їм",
            distractors=(
                PronounDistractor(
                    text="наперекір нім",
                    interference_type=PronounInterferenceType.WRONGLY_ATTACHED_DERIVATIVE_N,
                    explanation_ua="Після прийменника 'наперекір' приставний н- не вживається: правильно 'наперекір їм'.",
                    explanation_en="After preposition 'наперекір', epenthetic n- is not used: 'наперекір їм'.",
                ),
                PronounDistractor(
                    text="наперекір них",
                    interference_type=PronounInterferenceType.WRONGLY_ATTACHED_DERIVATIVE_N,
                    explanation_ua="Прийменник 'наперекір' вимагає давального відмінка без н- ('їм'), а не родового з н- 'них'.",
                    explanation_en="Preposition 'наперекір' requires Dative without n- ('їм'), not Genitive with n- 'них'.",
                ),
                PronounDistractor(
                    text="наперекір їх",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'наперекір' вимагає давального відмінка (кому?), а не знахідного/родового 'їх'.",
                    explanation_en="Preposition 'наперекір' requires Dative (кому?), not Accusative/Genitive 'їх'.",
                ),
            ),
            rule_citation=cit_ep,
            rule_summary_ua=ua_ep_der,
            rule_summary_en=en_ep_der,
        ),
        # ====================================================================
        # 5. ORTHOGRAPHY_INDEFINITE_TOGETHER (5 cards) [Правопис 2019 § 42]
        # ====================================================================
        PronounCard(
            card_id="pron_orth_tog_dekhto",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER,
            cefr_level="A2",
            sentence_before="У тихому коридорі почулися швидкі кроки, ніби",
            sentence_after="поспішав на лекцію.",
            correct_answer="дехто",
            distractors=(
                PronounDistractor(
                    text="де-хто",
                    interference_type=PronounInterferenceType.HYPHENATED_INDEFINITE_CALQUE,
                    explanation_ua="Префікс де- у неозначених займенниках пишеться разом: 'дехто'.",
                    explanation_en="Prefix де- in indefinite pronouns is written as a single word: 'дехто'.",
                ),
                PronounDistractor(
                    text="де хто",
                    interference_type=PronounInterferenceType.SEPARATE_INDEFINITE_CALQUE,
                    explanation_ua="Префікс де- без прийменника пишеться із займенником разом: 'дехто'.",
                    explanation_en="Prefix де- without a preposition is written together with the pronoun: 'дехто'.",
                ),
                PronounDistractor(
                    text="дехтось",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Надлишкове нагромадження префікса де- та суфікса -сь: нормативною є форма 'дехто'.",
                    explanation_en="Redundant stacking of prefix де- and suffix -сь; standard form is 'дехто'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_tog,
            rule_summary_en=en_orth_tog,
        ),
        PronounCard(
            card_id="pron_orth_tog_abykhto",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER,
            cefr_level="B1",
            sentence_before="Не варто довіряти важливі таємниці першому зустрічному, бо",
            sentence_after="може скористатися цим.",
            correct_answer="абихто",
            distractors=(
                PronounDistractor(
                    text="аби-хто",
                    interference_type=PronounInterferenceType.HYPHENATED_INDEFINITE_CALQUE,
                    explanation_ua="Префікс аби- з неозначеними займенниками пишеться разом: 'абихто'.",
                    explanation_en="Prefix аби- in indefinite pronouns is written as a single word: 'абихто'.",
                ),
                PronounDistractor(
                    text="аби хто",
                    interference_type=PronounInterferenceType.SEPARATE_INDEFINITE_CALQUE,
                    explanation_ua="Префікс аби- без прийменника пишеться разом із займенником: 'абихто'.",
                    explanation_en="Prefix аби- without a preposition is written together with the pronoun: 'абихто'.",
                ),
                PronounDistractor(
                    text="абикого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У ролі граматичного підмета до присудка 'може скористатися' виступає називний відмінок 'абихто'; форма родового/знахідного відмінка 'абикого' порушує синтаксичну структуру речення.",
                    explanation_en="As grammatical subject for predicate 'може скористатися', Nominative 'абихто' is required; Genitive/Accusative 'абикого' violates syntactic agreement.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_tog,
            rule_summary_en=en_orth_tog,
        ),
        PronounCard(
            card_id="pron_orth_tog_khtos",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER,
            cefr_level="A2",
            sentence_before="За вікном пролунав дивний шум, наче",
            sentence_after="тихо стукав у шибку.",
            correct_answer="хтось",
            distractors=(
                PronounDistractor(
                    text="хто-сь",
                    interference_type=PronounInterferenceType.HYPHENATED_INDEFINITE_CALQUE,
                    explanation_ua="Суфікс -сь у неозначених займенниках завжди пишеться разом: 'хтось'.",
                    explanation_en="Suffix -сь in indefinite pronouns is always written as a single word: 'хтось'.",
                ),
                PronounDistractor(
                    text="хто сь",
                    interference_type=PronounInterferenceType.SEPARATE_INDEFINITE_CALQUE,
                    explanation_ua="Суфікс -сь є частиною слова і не відділяється пробілом: 'хтось'.",
                    explanation_en="Suffix -сь is part of the word morpheme and cannot be separated by a space: 'хтось'.",
                ),
                PronounDistractor(
                    text="когось",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У підрядному реченні потрібен називний відмінок підмета 'хтось' (хто стукав?); форма родового/знахідного відмінка 'когось' порушує узгодження підмета з присудком.",
                    explanation_en="In the clause, Nominative subject 'хтось' is required; form 'когось' (Genitive/Accusative) violates subject-verb agreement.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_tog,
            rule_summary_en=en_orth_tog,
        ),
        PronounCard(
            card_id="pron_orth_tog_abyyaku",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER,
            cefr_level="B1",
            sentence_before="Він не цурався труднощів і брався за",
            sentence_after="роботу, щоб забезпечити родину.",
            correct_answer="абияку",
            distractors=(
                PronounDistractor(
                    text="аби-яку",
                    interference_type=PronounInterferenceType.HYPHENATED_INDEFINITE_CALQUE,
                    explanation_ua="Префікс аби- із займенниками пишеться разом: 'абияку'.",
                    explanation_en="Prefix аби- with pronouns is written as a single word: 'абияку'.",
                ),
                PronounDistractor(
                    text="аби яку",
                    interference_type=PronounInterferenceType.SEPARATE_INDEFINITE_CALQUE,
                    explanation_ua="Префікс аби- без прийменника пишеться разом із займенником: 'абияку'.",
                    explanation_en="Prefix аби- without a preposition is written together: 'абияку'.",
                ),
                PronounDistractor(
                    text="абияка",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'за' у виразі 'братися за щось' вимагає знахідного відмінка жіночого роду: 'абияку'; форма називного відмінка 'абияка' порушує відмінкове узгодження з іменником 'роботу'.",
                    explanation_en="Preposition 'за' in 'братися за щось' governs Accusative: 'абияку'; Nominative form 'абияка' violates case agreement with 'роботу'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_tog,
            rule_summary_en=en_orth_tog,
        ),
        PronounCard(
            card_id="pron_orth_tog_shchos",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_TOGETHER,
            cefr_level="A2",
            sentence_before="У кімнаті було темно, але я помітив",
            sentence_after="біля старої книжкової шафи.",
            correct_answer="щось",
            distractors=(
                PronounDistractor(
                    text="що-сь",
                    interference_type=PronounInterferenceType.HYPHENATED_INDEFINITE_CALQUE,
                    explanation_ua="Суфікс -сь пишеться разом зі словами: 'щось'.",
                    explanation_en="Suffix -сь is written together: 'щось'.",
                ),
                PronounDistractor(
                    text="що сь",
                    interference_type=PronounInterferenceType.SEPARATE_INDEFINITE_CALQUE,
                    explanation_ua="Суфікс -сь є морфемою і пишеться разом: 'щось'.",
                    explanation_en="Suffix -сь is a morpheme written solidly: 'щось'.",
                ),
                PronounDistractor(
                    text="чимось",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'помітити' є перехідним і керує знахідним відмінком прямого додатка: 'щось'; форма орудного відмінка 'чимось' порушує синтаксичне керування.",
                    explanation_en="Verb 'помітити' is transitive and governs Accusative direct object: 'щось'; Instrumental form 'чимось' violates verb government.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_tog,
            rule_summary_en=en_orth_tog,
        ),
        # ====================================================================
        # 6. ORTHOGRAPHY_INDEFINITE_HYPHEN (5 cards) [Правопис 2019 § 42]
        # ====================================================================
        PronounCard(
            card_id="pron_orth_hyph_bud_khto",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN,
            cefr_level="A2",
            sentence_before="Цю просту арифметичну задачу може розв'язати",
            sentence_after="із нашого класу.",
            correct_answer="будь-хто",
            distractors=(
                PronounDistractor(
                    text="будьхто",
                    interference_type=PronounInterferenceType.SOLID_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка будь- із займенниками пишеться через дефіс: 'будь-хто'.",
                    explanation_en="Particle будь- with pronouns is written with a hyphen: 'будь-хто'.",
                ),
                PronounDistractor(
                    text="будь хто",
                    interference_type=PronounInterferenceType.SEPARATE_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка будь- без прийменника пишеться через дефіс, а не окремо: 'будь-хто'.",
                    explanation_en="Particle будь- without a preposition is written with a hyphen, not separately: 'будь-хто'.",
                ),
                PronounDistractor(
                    text="будь-кого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У ролі граматичного підмета при присудку 'може розв'язати' виступає називний відмінок 'будь-хто'; форма родового/знахідного відмінка 'будь-кого' порушує граматичну структуру речення.",
                    explanation_en="As grammatical subject for predicate 'може розв'язати', Nominative 'будь-хто' is required; form 'будь-кого' (Genitive/Accusative) violates syntactic agreement.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_hyph,
            rule_summary_en=en_orth_hyph,
        ),
        PronounCard(
            card_id="pron_orth_hyph_khto_nebud",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN,
            cefr_level="A2",
            sentence_before="Якщо",
            sentence_after="зателефонує, запиши номер і передай мені повідомлення.",
            correct_answer="хто-небудь",
            distractors=(
                PronounDistractor(
                    text="хтонебудь",
                    interference_type=PronounInterferenceType.SOLID_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка -небудь із займенниками пишеться через дефіс: 'хто-небудь'.",
                    explanation_en="Particle -небудь with pronouns is written with a hyphen: 'хто-небудь'.",
                ),
                PronounDistractor(
                    text="хто небудь",
                    interference_type=PronounInterferenceType.SEPARATE_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка -небудь без дефіса не вживається; окреме написання є орфографічною помилкою: 'хто-небудь'.",
                    explanation_en="Particle -небудь is written with a hyphen, never separately: 'хто-небудь'.",
                ),
                PronounDistractor(
                    text="хто-будь",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Частка будь- виступає префіксом ('будь-хто'), а як постфікс вона не вживається.",
                    explanation_en="Particle будь- is a prefix ('будь-хто'); it does not occur as a postfix.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_hyph,
            rule_summary_en=en_orth_hyph,
        ),
        PronounCard(
            card_id="pron_orth_hyph_kazna_shcho",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN,
            cefr_level="B1",
            sentence_before="Не вір безпідставним чуткам, бо це",
            sentence_after=", вигадане недоброзичливцями.",
            correct_answer="казна-що",
            distractors=(
                PronounDistractor(
                    text="казнащо",
                    interference_type=PronounInterferenceType.SOLID_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка казна- із займенниками пишеться через дефіс: 'казна-що'.",
                    explanation_en="Particle казна- with pronouns is written with a hyphen: 'казна-що'.",
                ),
                PronounDistractor(
                    text="казна що",
                    interference_type=PronounInterferenceType.SEPARATE_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка казна- пишеться через дефіс, а не окремо: 'казна-що'.",
                    explanation_en="Particle казна- is written with a hyphen, not separately: 'казна-що'.",
                ),
                PronounDistractor(
                    text="казна-хто",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Слово 'чутки' позначає інформацію (неістоту), тому вживається 'казна-що', а не особовий 'казна-хто'.",
                    explanation_en="'чутки' refers to inanimate information; 'казна-що' is required, not personal 'казна-хто'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_hyph,
            rule_summary_en=en_orth_hyph,
        ),
        PronounCard(
            card_id="pron_orth_hyph_bud_yake",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN,
            cefr_level="A2",
            sentence_before="Він завжди відповідально ставиться до роботи й сумлінно виконує",
            sentence_after="доручення керівника.",
            correct_answer="будь-яке",
            distractors=(
                PronounDistractor(
                    text="будьяке",
                    interference_type=PronounInterferenceType.SOLID_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка будь- пишеться із займенниками через дефіс: 'будь-яке'.",
                    explanation_en="Particle будь- with pronouns is written with a hyphen: 'будь-яке'.",
                ),
                PronounDistractor(
                    text="будь яке",
                    interference_type=PronounInterferenceType.SEPARATE_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка будь- без прийменника пишеться через дефіс: 'будь-яке'.",
                    explanation_en="Particle будь- without preposition is hyphenated: 'будь-яке'.",
                ),
                PronounDistractor(
                    text="будь-який",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'доручення' належить до середнього роду, тому займенник узгоджується у формі середнього роду 'будь-яке'; форма чоловічого роду 'будь-який' порушує узгодження в роді.",
                    explanation_en="Noun 'доручення' is neuter; pronoun must agree in neuter form 'будь-яке'; masculine form 'будь-який' violates gender agreement.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_hyph,
            rule_summary_en=en_orth_hyph,
        ),
        PronounCard(
            card_id="pron_orth_hyph_khtozna_yakyi",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_HYPHEN,
            cefr_level="B1",
            sentence_before="На старій полиці лежав",
            sentence_after="пошарпаний підручник з математики.",
            correct_answer="хтозна-який",
            distractors=(
                PronounDistractor(
                    text="хтознаякий",
                    interference_type=PronounInterferenceType.SOLID_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка хтозна- із займенниками пишеться через дефіс: 'хтозна-який'.",
                    explanation_en="Particle хтозна- with pronouns is written with a hyphen: 'хтозна-який'.",
                ),
                PronounDistractor(
                    text="хтозна який",
                    interference_type=PronounInterferenceType.SEPARATE_WRITTEN_HYPHEN_PARTICLE,
                    explanation_ua="Частка хтозна- пишеться через дефіс; окремо вона пишеться лише за наявності прийменника між ними: 'хтозна-який'.",
                    explanation_en="Particle хтозна- is written with a hyphen; it is written separately only when split by a preposition: 'хтозна-який'.",
                ),
                PronounDistractor(
                    text="хтозна-що",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Займенник узгоджується з іменником 'підручник' (чоловічий рід), тому вимагає означення 'хтозна-який'.",
                    explanation_en="Pronoun modifies masculine noun 'підручник', requiring adjectival pronoun 'хтозна-який'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_hyph,
            rule_summary_en=en_orth_hyph,
        ),
        # ====================================================================
        # 7. ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION (5 cards) [Правопис 2019 § 42]
        # ====================================================================
        PronounCard(
            card_id="pron_orth_split_bud_u_koho",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION,
            cefr_level="B1",
            sentence_before="Ти можеш сміливо запитати правильну дорогу",
            sentence_after="із перехожих на центральній вулиці.",
            correct_answer="будь у кого",
            distractors=(
                PronounDistractor(
                    text="будь-у-кого",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="Якщо між часткою будь- та займенником стоїть прийменник, усі три слова пишуться окремо без дефісів: 'будь у кого'.",
                    explanation_en="When a preposition intervenes between particle будь- and pronoun, all three words are written separately without hyphens: 'будь у кого'.",
                ),
                PronounDistractor(
                    text="будь-кого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'у' пропущено, що руйнує нормативну синтаксичну конструкцію 'запитати у когось'.",
                    explanation_en="Preposition 'у' is omitted, altering the required syntactic government.",
                ),
                PronounDistractor(
                    text="будьукого",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Написання разом є грубою орфографічною помилкою; слід писати окремо в три слова: 'будь у кого'.",
                    explanation_en="Writing solidly is an orthographic error; it must be three separate words: 'будь у кого'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_indef,
            rule_summary_en=en_orth_split_indef,
        ),
        PronounCard(
            card_id="pron_orth_split_bud_z_kym",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION,
            cefr_level="B1",
            sentence_before="Він не боявся вступати в суперечку",
            sentence_after=", коли відстоював справедливість.",
            correct_answer="будь з ким",
            distractors=(
                PronounDistractor(
                    text="будь-з-ким",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="За наявності прийменника між часткою будь- та займенником дефіси зникають: 'будь з ким'.",
                    explanation_en="When a preposition intervenes between particle будь- and the pronoun, hyphens disappear: 'будь з ким'.",
                ),
                PronounDistractor(
                    text="будь-ким",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслівне керування 'вступати в суперечку' обов'язково вимагає прийменника 'з' ('будь з ким'); вживання безприйменникового орудного 'будь-ким' порушує синтаксичний зв'язок.",
                    explanation_en="Verb government 'вступати в суперечку' requires preposition 'з' ('будь з ким'); form without preposition 'будь-ким' violates case government.",
                ),
                PronounDistractor(
                    text="будьзким",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Сполука частки, прийменника та займенника пишеться окремо в три слова: 'будь з ким'.",
                    explanation_en="Sequence of particle, preposition, and pronoun is written as three separate words: 'будь з ким'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_indef,
            rule_summary_en=en_orth_split_indef,
        ),
        PronounCard(
            card_id="pron_orth_split_khtozna_z_kym",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION,
            cefr_level="B1",
            sentence_before="Він поводився легковажно й міг вирушити в далеку мандрівку",
            sentence_after=".",
            correct_answer="хтозна з ким",
            distractors=(
                PronounDistractor(
                    text="хтозна-з-ким",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="Коли між часткою хтозна- і займенником стоїть прийменник, сполука пишеться окремо трьома словами: 'хтозна з ким'.",
                    explanation_en="When a preposition intervenes between particle хтозна- and pronoun, all three words are written separately: 'хтозна з ким'.",
                ),
                PronounDistractor(
                    text="хтозна-ким",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'вирушити в мандрівку' у значенні супутника вимагає прийменника сумісності 'з' ('хтозна з ким'); вживання форми без прийменника 'хтозна-ким' порушує керування.",
                    explanation_en="Denoting accompaniment, 'вирушити в мандрівку' requires preposition 'з' ('хтозна з ким'); form without preposition 'хтозна-ким' violates government.",
                ),
                PronounDistractor(
                    text="хтозназким",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Разом сполука з трьох слів не пишеться; нормативне написання: 'хтозна з ким'.",
                    explanation_en="The three-word phrase cannot be merged; standard spelling is 'хтозна з ким'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_indef,
            rule_summary_en=en_orth_split_indef,
        ),
        PronounCard(
            card_id="pron_orth_split_aby_pered_kym",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION,
            cefr_level="B2",
            sentence_before="Я не збираюся принижуватися й виправдовуватися",
            sentence_after=", бо моє сумління чисте.",
            correct_answer="аби перед ким",
            distractors=(
                PronounDistractor(
                    text="аби-перед-ким",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="За наявності прийменника сполука з часткою аби- пишеться окремо в три слова без дефісів: 'аби перед ким'.",
                    explanation_en="With a preposition, combination with particle аби- is written as three words without hyphens: 'аби перед ким'.",
                ),
                PronounDistractor(
                    text="аби-ким",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'виправдовуватися' вимагає прийменника 'перед' ('аби перед ким'); форма без прийменника 'аби-ким' порушує синтаксичне керування.",
                    explanation_en="Verb 'виправдовуватися' requires preposition 'перед' ('аби перед ким'); form without preposition 'аби-ким' violates government.",
                ),
                PronounDistractor(
                    text="абипередким",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Злиття частки, прийменника та займенника в одне слово ненормативне; правильно: 'аби перед ким'.",
                    explanation_en="Fusing particle, preposition, and pronoun is ungrammatical; write 'аби перед ким'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_indef,
            rule_summary_en=en_orth_split_indef,
        ),
        PronounCard(
            card_id="pron_orth_split_de_z_kym",
            category=PronounCategory.ORTHOGRAPHY_INDEFINITE_SPLIT_PREPOSITION,
            cefr_level="B2",
            sentence_before="Досвідчений майстер не стане радитися",
            sentence_after=", адже знає тонкощі своєї справи досконало.",
            correct_answer="де з ким",
            distractors=(
                PronounDistractor(
                    text="де-з-ким",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="Коли між часткою де- і займенником стоїть прийменник, пишемо окремо трьома словами: 'де з ким'.",
                    explanation_en="When a preposition separates particle де- and pronoun, write as three separate words: 'де з ким'.",
                ),
                PronounDistractor(
                    text="де-ким",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'радитися' керує орудним відмінком із прийменником 'з' ('де з ким'); форма без прийменника 'де-ким' порушує синтаксичне керування.",
                    explanation_en="Verb 'радитися' governs Instrumental with preposition 'з' ('де з ким'); form without preposition 'де-ким' violates government.",
                ),
                PronounDistractor(
                    text="дезким",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Орфографічна норма вимагає роздільного написання в три слова: 'де з ким'.",
                    explanation_en="Standard spelling requires three separate words: 'де з ким'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_indef,
            rule_summary_en=en_orth_split_indef,
        ),
        # ====================================================================
        # 8. ORTHOGRAPHY_NEGATIVE_TOGETHER (5 cards) [Правопис 2019 § 42]
        # ====================================================================
        PronounCard(
            card_id="pron_orth_neg_nikhto",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER,
            cefr_level="A2",
            sentence_before="У порожній університетській аудиторії вже",
            sentence_after="не чекав на початок консультації.",
            correct_answer="ніхто",
            distractors=(
                PronounDistractor(
                    text="ні хто",
                    interference_type=PronounInterferenceType.SEPARATE_NEGATIVE_PRONOUN,
                    explanation_ua="Заперечна частка ні- із займенниками без прийменника пишеться разом: 'ніхто'.",
                    explanation_en="Negative prefix ні- with pronouns without preposition is written solidly: 'ніхто'.",
                ),
                PronounDistractor(
                    text="ні-хто",
                    interference_type=PronounInterferenceType.HYPHENATED_NEGATIVE_PRONOUN,
                    explanation_ua="Частка ні- із займенниками ніколи не пишеться через дефіс; нормативне написання — разом: 'ніхто'.",
                    explanation_en="Prefix ні- with pronouns is never hyphenated; write as a single word: 'ніхто'.",
                ),
                PronounDistractor(
                    text="нікого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У ролі граматичного підмета в реченні виступає форма називного відмінка 'ніхто'.",
                    explanation_en="As grammatical subject of the sentence, Nominative 'ніхто' is required.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_neg_tog,
            rule_summary_en=en_orth_neg_tog,
        ),
        PronounCard(
            card_id="pron_orth_neg_nichoho",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER,
            cefr_level="A2",
            sentence_before="Він уважно слухав лектора, але",
            sentence_after="не зміг зрозуміти зі складної доповіді.",
            correct_answer="нічого",
            distractors=(
                PronounDistractor(
                    text="ні чого",
                    interference_type=PronounInterferenceType.SEPARATE_NEGATIVE_PRONOUN,
                    explanation_ua="Частка ні- із займенником 'що' у родовому відмінку пишеться разом: 'нічого'.",
                    explanation_en="Prefix ні- with Genitive pronoun 'нічого' is written as a single word: 'нічого'.",
                ),
                PronounDistractor(
                    text="ні-чого",
                    interference_type=PronounInterferenceType.HYPHENATED_NEGATIVE_PRONOUN,
                    explanation_ua="Заперечний займенник пишеться разом без дефіса: 'нічого'.",
                    explanation_en="Negative pronoun is written solidly without a hyphen: 'нічого'.",
                ),
                PronounDistractor(
                    text="ніщо",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="При дієслові з запереченням 'не зміг зрозуміти' прямий додаток стоїть у родовому відмінку: 'нічого'.",
                    explanation_en="With negated verb 'не зміг зрозуміти', direct object requires Genitive: 'нічого'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_neg_tog,
            rule_summary_en=en_orth_neg_tog,
        ),
        PronounCard(
            card_id="pron_orth_neg_niyakyi",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER,
            cefr_level="A2",
            sentence_before="Він був непохитним у своєму намірі, і",
            sentence_after="сумнів не міг похитнути його впевненість.",
            correct_answer="ніякий",
            distractors=(
                PronounDistractor(
                    text="ні який",
                    interference_type=PronounInterferenceType.SEPARATE_NEGATIVE_PRONOUN,
                    explanation_ua="Заперечний займенник 'ніякий' пишеться разом: 'ніякий'.",
                    explanation_en="Negative pronoun 'ніякий' is written solidly: 'ніякий'.",
                ),
                PronounDistractor(
                    text="ні-який",
                    interference_type=PronounInterferenceType.HYPHENATED_NEGATIVE_PRONOUN,
                    explanation_ua="Частка ні- із займенниками не поєднується через дефіс; пишемо разом: 'ніякий'.",
                    explanation_en="Prefix ні- is never hyphenated with pronouns; write solidly: 'ніякий'.",
                ),
                PronounDistractor(
                    text="ніякого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'сумнів' є підметом у називному відмінку, тому займенник узгоджується у формі 'ніякий'.",
                    explanation_en="'сумнів' is subject in Nominative, so the modifier must agree in Nominative: 'ніякий'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_neg_tog,
            rule_summary_en=en_orth_neg_tog,
        ),
        PronounCard(
            card_id="pron_orth_neg_nichyi",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER,
            cefr_level="B1",
            sentence_before="Ця старовинна садиба здавалася покинутою, і",
            sentence_after="погляд на ній довго не затримувався.",
            correct_answer="нічий",
            distractors=(
                PronounDistractor(
                    text="ні чий",
                    interference_type=PronounInterferenceType.SEPARATE_NEGATIVE_PRONOUN,
                    explanation_ua="Заперечний присвійний займенник пишеться разом: 'нічий'.",
                    explanation_en="Negative possessive pronoun is written solidly: 'нічий'.",
                ),
                PronounDistractor(
                    text="ні-чий",
                    interference_type=PronounInterferenceType.HYPHENATED_NEGATIVE_PRONOUN,
                    explanation_ua="Написання заперечного займенника через дефіс є помилковим; слід писати разом: 'нічий'.",
                    explanation_en="Hyphenating negative pronoun is incorrect; write solidly: 'нічий'.",
                ),
                PronounDistractor(
                    text="нічия",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'погляд' чоловічого роду; займенник вимагає форми чоловічого роду 'нічий'.",
                    explanation_en="'погляд' is masculine; pronoun requires masculine form 'нічий'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_neg_tog,
            rule_summary_en=en_orth_neg_tog,
        ),
        PronounCard(
            card_id="pron_orth_neg_nishcho",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_TOGETHER,
            cefr_level="A2",
            sentence_before="Ми доклали всіх зусиль, але",
            sentence_after="не могло зарадити цій прикрій біді.",
            correct_answer="ніщо",
            distractors=(
                PronounDistractor(
                    text="ні що",
                    interference_type=PronounInterferenceType.SEPARATE_NEGATIVE_PRONOUN,
                    explanation_ua="Заперечний займенник 'ніщо' пишеться разом: 'ніщо'.",
                    explanation_en="Negative pronoun 'ніщо' is written solidly: 'ніщо'.",
                ),
                PronounDistractor(
                    text="ні-що",
                    interference_type=PronounInterferenceType.HYPHENATED_NEGATIVE_PRONOUN,
                    explanation_ua="Дефіс у заперечних займенниках не вживається; пишемо разом: 'ніщо'.",
                    explanation_en="Hyphen is not used in negative pronouns; write solidly: 'ніщо'.",
                ),
                PronounDistractor(
                    text="нічим",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У ролі граматичного підмета виступає називний відмінок 'ніщо', а не орудний 'нічим'.",
                    explanation_en="As grammatical subject, Nominative 'ніщо' is required, not Instrumental 'нічим'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_neg_tog,
            rule_summary_en=en_orth_neg_tog,
        ),
        # ====================================================================
        # 9. ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION (5 cards) [Правопис 2019 § 42]
        # ====================================================================
        PronounCard(
            card_id="pron_orth_split_neg_ni_pro_shcho",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION,
            cefr_level="A2",
            sentence_before="Він мовчки дивився у вікно й цілий вечір",
            sentence_after="не хотів розмовляти.",
            correct_answer="ні про що",
            distractors=(
                PronounDistractor(
                    text="про ніщо",
                    interference_type=PronounInterferenceType.EXTERNAL_PREPOSITION_RUSSIAN_CALQUE,
                    explanation_ua="Російська калька порушує порядок слів: в українській мові прийменник ставиться всередині — 'ні про що'.",
                    explanation_en="Calqued word order: in Ukrainian, preposition stands inside the phrase — 'ні про що'.",
                ),
                PronounDistractor(
                    text="ніпрощо",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Коли між часткою ні та займенником стоїть прийменник, уся сполука пишеться окремо трьома словами: 'ні про що'.",
                    explanation_en="When a preposition intervenes, the phrase is written as three separate words: 'ні про що'.",
                ),
                PronounDistractor(
                    text="ні-про-що",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="Дефіси у розірваних прийменником заперечних сполуках не вживаються: 'ні про що'.",
                    explanation_en="Hyphens are not used in split negative phrases: 'ні про що'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_neg,
            rule_summary_en=en_orth_split_neg,
        ),
        PronounCard(
            card_id="pron_orth_split_neg_ni_z_kym",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION,
            cefr_level="A2",
            sentence_before="Вона була принциповою людиною і",
            sentence_after="не йшла на сумнівні компроміси.",
            correct_answer="ні з ким",
            distractors=(
                PronounDistractor(
                    text="з ніким",
                    interference_type=PronounInterferenceType.EXTERNAL_PREPOSITION_RUSSIAN_CALQUE,
                    explanation_ua="Російська калька: прийменник в українській мові обов'язково стоїть між ні та займенником: 'ні з ким'.",
                    explanation_en="Calqued word order: in Ukrainian, preposition strictly stands between ні and pronoun: 'ні з ким'.",
                ),
                PronounDistractor(
                    text="нізким",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Прийменникова сполука пишеться окремо трьома словами: 'ні з ким'.",
                    explanation_en="Prepositional negative sequence is written as three separate words: 'ні з ким'.",
                ),
                PronounDistractor(
                    text="ні-з-ким",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="Написання через дефіси є помилковим; слід писати окремо: 'ні з ким'.",
                    explanation_en="Hyphenated spelling is ungrammatical; write separately: 'ні з ким'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_neg,
            rule_summary_en=en_orth_split_neg,
        ),
        PronounCard(
            card_id="pron_orth_split_neg_ni_do_koho",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION,
            cefr_level="A2",
            sentence_before="У важку хвилину хлопець вирішив упоратися сам і",
            sentence_after="не звертався по допомогу.",
            correct_answer="ні до кого",
            distractors=(
                PronounDistractor(
                    text="до нікого",
                    interference_type=PronounInterferenceType.EXTERNAL_PREPOSITION_RUSSIAN_CALQUE,
                    explanation_ua="Ненормативний порядок слів (калька): прийменник стоїть між часткою ні та займенником — 'ні до кого'.",
                    explanation_en="Calqued word order: preposition stands inside between particle ні and pronoun — 'ні до кого'.",
                ),
                PronounDistractor(
                    text="нідокого",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Сполука з прийменником пишеться окремо трьома словами: 'ні до кого'.",
                    explanation_en="Sequence with preposition is written as three words: 'ні до кого'.",
                ),
                PronounDistractor(
                    text="ні-до-кого",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="У розірваних заперечних займенниках дефіси не ставляться: 'ні до кого'.",
                    explanation_en="Hyphens are never placed in split negative pronouns: 'ні до кого'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_neg,
            rule_summary_en=en_orth_split_neg,
        ),
        PronounCard(
            card_id="pron_orth_split_neg_ni_za_yakykh",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION,
            cefr_level="B1",
            sentence_before="Ми не повинні відмовлятися від своїх переконань",
            sentence_after="обставин, хоч би якими важкими вони були.",
            correct_answer="ні за яких",
            distractors=(
                PronounDistractor(
                    text="за ніяких",
                    interference_type=PronounInterferenceType.EXTERNAL_PREPOSITION_RUSSIAN_CALQUE,
                    explanation_ua="Калька: в українській літературній мові прийменник ставиться всередині сполуки — 'ні за яких'.",
                    explanation_en="Calque: in standard Ukrainian, preposition is placed internally — 'ні за яких'.",
                ),
                PronounDistractor(
                    text="нізаяких",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Сполука пишеться окремо трьома словами: 'ні за яких'.",
                    explanation_en="Phrase is written as three separate words: 'ні за яких'.",
                ),
                PronounDistractor(
                    text="ні-за-яких",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="Вживання дефісів тут є грубою орфографічною помилкою: 'ні за яких'.",
                    explanation_en="Using hyphens here is an orthographic error; write 'ні за яких'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_neg,
            rule_summary_en=en_orth_split_neg,
        ),
        PronounCard(
            card_id="pron_orth_split_neg_ni_na_shcho",
            category=PronounCategory.ORTHOGRAPHY_NEGATIVE_SPLIT_PREPOSITION,
            cefr_level="A2",
            sentence_before="Він не зважав",
            sentence_after="і впевнено продовжував рухатися до поставленої мети.",
            correct_answer="ні на що",
            distractors=(
                PronounDistractor(
                    text="на ніщо",
                    interference_type=PronounInterferenceType.EXTERNAL_PREPOSITION_RUSSIAN_CALQUE,
                    explanation_ua="Калькований порядок слів: в українській мові прийменник розриває заперечний займенник: 'ні на що'.",
                    explanation_en="Calqued word order: in Ukrainian, preposition splits negative pronoun: 'ні на що'.",
                ),
                PronounDistractor(
                    text="ні нащо",
                    interference_type=PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
                    explanation_ua="Трикомпонентна сполука містить прийменник 'на' і форму займенника 'що', тому пишеться окремо в три слова: 'ні на що'.",
                    explanation_en="Three-component sequence contains preposition 'на' and pronoun 'що', written as three words: 'ні на що'.",
                ),
                PronounDistractor(
                    text="ні-на-що",
                    interference_type=PronounInterferenceType.HYPHENATED_SPLIT_PREPOSITION,
                    explanation_ua="Дефіси в таких конструкціях не вживаються; пишемо окремо: 'ні на що'.",
                    explanation_en="Hyphens are not used in such constructions; write separately: 'ні на що'.",
                ),
            ),
            rule_citation=cit_orth,
            rule_summary_ua=ua_orth_split_neg,
            rule_summary_en=en_orth_split_neg,
        ),
        # ====================================================================
        # 10. REFLEXIVE_SEBE_PARADIGM (5 cards) [Правопис 2019 § 117]
        # ====================================================================
        PronounCard(
            card_id="pron_refl_sobi",
            category=PronounCategory.REFLEXIVE_SEBE_PARADIGM,
            cefr_level="A2",
            sentence_before="Він замислився над своїми вчинками і дав",
            sentence_after="тверду обіцянку виправити ситуацію.",
            correct_answer="собі",
            distractors=(
                PronounDistractor(
                    text="себі",
                    interference_type=PronounInterferenceType.DEFECTIVE_REFL_NOMINATIVE,
                    explanation_ua="Давальний відмінок зворотного займенника 'себе' має форму 'собі' (з голосним о), форма *себі не існує.",
                    explanation_en="Dative of reflexive 'себе' is 'собі' (with vowel o); *себі does not exist.",
                ),
                PronounDistractor(
                    text="себе",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'дати' керує давальним відмінком адресата (кому?), а не родовим/знахідним 'себе'.",
                    explanation_en="'дати' governs Dative (кому?), not Genitive/Accusative 'себе'.",
                ),
                PronounDistractor(
                    text="собою",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'собою' є орудним відмінком; у значенні адресата дії потрібен давальний 'собі'.",
                    explanation_en="'собою' is Instrumental; Dative 'собі' is required for recipient.",
                ),
            ),
            rule_citation=cit_refl,
            rule_summary_ua=ua_refl,
            rule_summary_en=en_refl,
        ),
        PronounCard(
            card_id="pron_refl_na_sobi",
            category=PronounCategory.REFLEXIVE_SEBE_PARADIGM,
            cefr_level="B1",
            sentence_before="Після тривалого підйому в гори турист відчував",
            sentence_after="вагу важкого наплічника.",
            correct_answer="на собі",
            distractors=(
                PronounDistractor(
                    text="на себі",
                    interference_type=PronounInterferenceType.DEFECTIVE_REFL_NOMINATIVE,
                    explanation_ua="Місцевий відмінок зворотного займенника має голосний [о]: 'на собі', форма *на себі помилкова.",
                    explanation_en="Locative of reflexive pronoun has vowel [о]: 'на собі'; *на себі is ungrammatical.",
                ),
                PronounDistractor(
                    text="на себе",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У значенні локалізації відчуття (де?) вживається місцевий відмінок 'на собі' (знахідний 'на себе' означав би напрямок куди?).",
                    explanation_en="Denoting location of sensation (де?), Locative 'на собі' is required rather than directional Accusative 'на себе'.",
                ),
                PronounDistractor(
                    text="на ним",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дія спрямована на самого суб'єкта (туриста), тому нормативно вживається зворотний займенник 'на собі'.",
                    explanation_en="Action relates back to subject itself; reflexive pronoun 'на собі' is required.",
                ),
            ),
            rule_citation=cit_refl,
            rule_summary_ua=ua_refl,
            rule_summary_en=en_refl,
        ),
        PronounCard(
            card_id="pron_refl_soboyu",
            category=PronounCategory.REFLEXIVE_SEBE_PARADIGM,
            cefr_level="B1",
            sentence_before="Вона була впевнена у власних знаннях і повністю володіла",
            sentence_after="під час виступу.",
            correct_answer="собою",
            distractors=(
                PronounDistractor(
                    text="себою",
                    interference_type=PronounInterferenceType.DEFECTIVE_REFL_NOMINATIVE,
                    explanation_ua="Орудний відмінок зворотного займенника 'себе' має форму 'собою' (з голосним о), форми *себою не існує.",
                    explanation_en="Instrumental of reflexive 'себе' is 'собою' (with o); form *себою does not exist.",
                ),
                PronounDistractor(
                    text="собі",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'володіти' керує орудним відмінком (ким? чим?), а не давальним 'собі'.",
                    explanation_en="'володіти' governs Instrumental (ким? чим?), not Dative 'собі'.",
                ),
                PronounDistractor(
                    text="себе",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'володіти' вимагає орудного відмінка ('собою'), а не знахідного 'себе'.",
                    explanation_en="'володіти' requires Instrumental ('собою'), not Accusative 'себе'.",
                ),
            ),
            rule_citation=cit_refl,
            rule_summary_ua=ua_refl,
            rule_summary_en=en_refl,
        ),
        PronounCard(
            card_id="pron_refl_sebe",
            category=PronounCategory.REFLEXIVE_SEBE_PARADIGM,
            cefr_level="A2",
            sentence_before="Кожен із нас має вміти об'єктивно критикувати",
            sentence_after="за допущені помилки.",
            correct_answer="себе",
            distractors=(
                PronounDistractor(
                    text="себя",
                    interference_type=PronounInterferenceType.DEFECTIVE_REFL_NOMINATIVE,
                    explanation_ua="Російське закінчення-суржик: в українській літературній мові форма має вигляд 'себе'.",
                    explanation_en="Russianized ending; standard Ukrainian form is 'себе'.",
                ),
                PronounDistractor(
                    text="собі",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'критикувати' керує прямим знахідним відмінком (кого?), а не давальним 'собі'.",
                    explanation_en="'критикувати' governs direct Accusative (кого?), not Dative 'собі'.",
                ),
                PronounDistractor(
                    text="собою",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'критикувати' вимагає знахідного відмінка прямого додатка ('себе'), а не орудного 'собою'.",
                    explanation_en="'критикувати' requires direct Accusative ('себе'), not Instrumental 'собою'.",
                ),
            ),
            rule_citation=cit_refl,
            rule_summary_ua=ua_refl,
            rule_summary_en=en_refl,
        ),
        PronounCard(
            card_id="pron_refl_pry_sobi",
            category=PronounCategory.REFLEXIVE_SEBE_PARADIGM,
            cefr_level="B1",
            sentence_before="Художник завжди носив",
            sentence_after="маленький блокнот для швидких ескізів.",
            correct_answer="при собі",
            distractors=(
                PronounDistractor(
                    text="при себі",
                    interference_type=PronounInterferenceType.DEFECTIVE_REFL_NOMINATIVE,
                    explanation_ua="Місцевий відмінок зворотного займенника має нормативну форму 'при собі' (з голосним о).",
                    explanation_en="Locative of reflexive pronoun has standard vowel o: 'при собі'.",
                ),
                PronounDistractor(
                    text="при себе",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'при' вимагає місцевого відмінка ('при собі'), а не родового/знахідного 'себе'.",
                    explanation_en="Preposition 'при' governs Locative ('при собі'), not Genitive/Accusative 'себе'.",
                ),
                PronounDistractor(
                    text="при ньому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Коли дія стосується самого суб'єкта (художника), вживається зворотний займенник 'при собі'.",
                    explanation_en="When referring back to the subject (художник), reflexive 'при собі' is used.",
                ),
            ),
            rule_citation=cit_refl,
            rule_summary_ua=ua_refl,
            rule_summary_en=en_refl,
        ),
        # ====================================================================
        # 11. DECLENSION_VES_ALTERNATION (5 cards) [Правопис 2019 § 119]
        # ====================================================================
        PronounCard(
            card_id="pron_ves_vsima",
            category=PronounCategory.DECLENSION_VES_ALTERNATION,
            cefr_level="A2",
            sentence_before="Учні щиро привітали вчительку",
            sentence_after="квітами, які зібрали у шкільному саду.",
            correct_answer="всіма",
            distractors=(
                PronounDistractor(
                    text="всьома",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Орудний відмінок множини займенника 'весь' має нормативне закінчення -іма: 'всіма', форма *всьома є ненормативною.",
                    explanation_en="Instrumental plural of 'весь' has standard ending -іма: 'всіма'; *всьома is ungrammatical.",
                ),
                PronounDistractor(
                    text="всеми",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Російська калька: в українській літературній мові орудний відмінок множини має закінчення -іма: 'всіма'.",
                    explanation_en="Calque; standard Ukrainian Instrumental plural has ending -іма: 'всіма'.",
                ),
                PronounDistractor(
                    text="всім",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'всім' є давальним відмінком множини або орудним однини; з орудним множини 'квітами' узгоджується 'всіма'.",
                    explanation_en="'всім' is Dative plural or Instrumental singular; Instrumental plural 'квітами' agrees with 'всіма'.",
                ),
            ),
            rule_citation=cit_ves,
            rule_summary_ua=ua_ves,
            rule_summary_en=en_ves,
        ),
        PronounCard(
            card_id="pron_ves_vsim",
            category=PronounCategory.DECLENSION_VES_ALTERNATION,
            cefr_level="A2",
            sentence_before="Організатори щиро побажали успіху",
            sentence_after="учасникам олімпіади з української мови.",
            correct_answer="всім",
            distractors=(
                PronounDistractor(
                    text="всьому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'учасникам' вжито у множині; форма однини 'всьому' порушує узгодження за числом.",
                    explanation_en="'учасникам' is plural; singular 'всьому' violates number agreement.",
                ),
                PronounDistractor(
                    text="всему",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Суржикове спотворення основи; давальний відмінок множини — 'всім'.",
                    explanation_en="Corrupted stem; Dative plural is 'всім'.",
                ),
                PronounDistractor(
                    text="всіх",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'побажати' керує давальним відмінком адресата (кому?), форма 'всіх' є родовим/знахідним.",
                    explanation_en="'побажати' governs Dative for recipient (кому?), whereas 'всіх' is Genitive/Accusative.",
                ),
            ),
            rule_citation=cit_ves,
            rule_summary_ua=ua_ves,
            rule_summary_en=en_ves,
        ),
        PronounCard(
            card_id="pron_ves_vsyoho",
            category=PronounCategory.DECLENSION_VES_ALTERNATION,
            cefr_level="A2",
            sentence_before="Ми відчували втому після",
            sentence_after="робочого дня, сповненого клопотів.",
            correct_answer="всього",
            distractors=(
                PronounDistractor(
                    text="всьогось",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Надлишковий суфікс -сь спотворює значення; нормативна форма родового відмінка — 'всього'.",
                    explanation_en="Redundant suffix -сь distorts the meaning; standard Genitive is 'всього'.",
                ),
                PronounDistractor(
                    text="всего",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Російська калька з літерою е; в українській мові родовий відмінок однини має форму 'всього'.",
                    explanation_en="Russianized spelling with letter е; standard Ukrainian Genitive singular is 'всього'.",
                ),
                PronounDistractor(
                    text="всьому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'після' вимагає родового відмінка ('всього'), а не давального 'всьому'.",
                    explanation_en="Preposition 'після' governs Genitive ('всього'), not Dative 'всьому'.",
                ),
            ),
            rule_citation=cit_ves,
            rule_summary_ua=ua_ves,
            rule_summary_en=en_ves,
        ),
        PronounCard(
            card_id="pron_ves_vsikh",
            category=PronounCategory.DECLENSION_VES_ALTERNATION,
            cefr_level="A2",
            sentence_before="Директор звернувся до",
            sentence_after="присутніх у залі з важливою промовою.",
            correct_answer="всіх",
            distractors=(
                PronounDistractor(
                    text="всех",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Російська калька; в українській мові родовий відмінок множини має форму 'всіх'.",
                    explanation_en="Russianism; standard Ukrainian Genitive plural is 'всіх'.",
                ),
                PronounDistractor(
                    text="всім",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'до' вимагає родового відмінка ('всіх'), а не давального 'всім'.",
                    explanation_en="Preposition 'до' governs Genitive ('всіх'), not Dative 'всім'.",
                ),
                PronounDistractor(
                    text="всіма",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'всіма' є орудним відмінком; після прийменника 'до' вживається родовий 'всіх'.",
                    explanation_en="'всіма' is Instrumental; after preposition 'до', Genitive 'всіх' is required.",
                ),
            ),
            rule_citation=cit_ves,
            rule_summary_ua=ua_ves,
            rule_summary_en=en_ves,
        ),
        PronounCard(
            card_id="pron_ves_vsim_ins",
            category=PronounCategory.DECLENSION_VES_ALTERNATION,
            cefr_level="B1",
            sentence_before="Команда пишалася",
            sentence_after="досягнутим результатом наполегливої праці.",
            correct_answer="всім",
            distractors=(
                PronounDistractor(
                    text="всим",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="В орудному відмінку однини чоловічого/середнього роду пишеться літера і: 'всім', форма *всим ненормативна.",
                    explanation_en="In Instrumental singular masculine/neuter, letter і is written: 'всім'; *всим is ungrammatical.",
                ),
                PronounDistractor(
                    text="всьому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'пишатися' керує орудним відмінком ('всім'), а не давальним 'всьому'.",
                    explanation_en="'пишатися' governs Instrumental ('всім'), not Dative 'всьому'.",
                ),
                PronounDistractor(
                    text="всього",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'пишатися' вимагає орудного відмінка (чим?), а не родового 'всього'.",
                    explanation_en="'пишатися' requires Instrumental (чим?), not Genitive 'всього'.",
                ),
            ),
            rule_citation=cit_ves,
            rule_summary_ua=ua_ves,
            rule_summary_en=en_ves,
        ),
        # ====================================================================
        # 12. DECLENSION_TSYEY_TOY (5 cards) [Правопис 2019 § 119]
        # ====================================================================
        PronounCard(
            card_id="pron_dem_tsymy",
            category=PronounCategory.DECLENSION_TSYEY_TOY,
            cefr_level="A2",
            sentence_before="Ми довго гуляли",
            sentence_after="затишними старовинними вуличками міста.",
            correct_answer="цими",
            distractors=(
                PronounDistractor(
                    text="цима",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Орудний відмінок множини вказівного займенника 'цей' має нормативне закінчення -ими: 'цими', форма *цима є ненормативною.",
                    explanation_en="Instrumental plural of 'цей' takes ending -ими: 'цими'; *цима is non-standard.",
                ),
                PronounDistractor(
                    text="цих",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'цих' є родовим/знахідним відмінком; з орудним відмінком 'вуличками' узгоджується 'цими'.",
                    explanation_en="'цих' is Genitive/Accusative; Instrumental noun 'вуличками' agrees with 'цими'.",
                ),
                PronounDistractor(
                    text="цим",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'цим' — це давальний множини або орудний однини; орудний множини вимагає 'цими'.",
                    explanation_en="'цим' is Dative plural or Instrumental singular; Instrumental plural requires 'цими'.",
                ),
            ),
            rule_citation=cit_dem,
            rule_summary_ua=ua_dem,
            rule_summary_en=en_dem,
        ),
        PronounCard(
            card_id="pron_dem_tsoho",
            category=PronounCategory.DECLENSION_TSYEY_TOY,
            cefr_level="A2",
            sentence_before="Я не пам'ятаю назви",
            sentence_after="величного старовинного замку.",
            correct_answer="цього",
            distractors=(
                PronounDistractor(
                    text="цего",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Родовий відмінок вказівного займенника 'цей' має нормативну форму 'цього' (з суфіксом -ього), форма *цего архаїчна чи ненормативна.",
                    explanation_en="Genitive of 'цей' has standard form 'цього'; form *цего is archaic/non-standard.",
                ),
                PronounDistractor(
                    text="цьому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'назва' керує родовим відмінком (чого?), а не давальним 'цьому'.",
                    explanation_en="'назва' governs Genitive (чого?), not Dative 'цьому'.",
                ),
                PronounDistractor(
                    text="цим",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'цим' є орудним відмінком; у ролі неузгодженого означення потрібен родовий 'цього'.",
                    explanation_en="'цим' is Instrumental; modifier requires Genitive 'цього'.",
                ),
            ),
            rule_citation=cit_dem,
            rule_summary_ua=ua_dem,
            rule_summary_en=en_dem,
        ),
        PronounCard(
            card_id="pron_dem_tomu",
            category=PronounCategory.DECLENSION_TSYEY_TOY,
            cefr_level="A2",
            sentence_before="Завдяки",
            sentence_after="мудрому рішенню ми змогли вчасно завершити проєкт.",
            correct_answer="тому",
            distractors=(
                PronounDistractor(
                    text="тоєму",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Вказівний займенник 'той' у давальному відмінку чоловічого/середнього роду має форму 'тому', форма *тоєму спотворена.",
                    explanation_en="Demonstrative 'той' in Dative masculine/neuter is 'тому'; *тоєму is a corrupted form.",
                ),
                PronounDistractor(
                    text="того",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'завдяки' керує давальним відмінком (чому?), а не родовим 'того'.",
                    explanation_en="Preposition 'завдяки' governs Dative (чому?), not Genitive 'того'.",
                ),
                PronounDistractor(
                    text="тим",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'тим' є орудним відмінком однини або давальним множини; з давальним однини 'рішенню' вживається 'тому'.",
                    explanation_en="'тим' is Instrumental singular or Dative plural; Dative singular 'рішенню' takes 'тому'.",
                ),
            ),
            rule_citation=cit_dem,
            rule_summary_ua=ua_dem,
            rule_summary_en=en_dem,
        ),
        PronounCard(
            card_id="pron_dem_tymy",
            category=PronounCategory.DECLENSION_TSYEY_TOY,
            cefr_level="A2",
            sentence_before="Художник прикрасив картину",
            sentence_after="яскравими фарбами, які привіз із подорожі.",
            correct_answer="тими",
            distractors=(
                PronounDistractor(
                    text="тима",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Орудний відмінок множини вказівного займенника 'той' має закінчення -ими: 'тими', форма *тима є ненормативною.",
                    explanation_en="Instrumental plural of 'той' takes ending -ими: 'тими'; *тима is non-standard.",
                ),
                PronounDistractor(
                    text="тих",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'тих' є родовим відмінком; з орудним множини 'фарбами' узгоджується 'тими'.",
                    explanation_en="'тих' is Genitive; Instrumental noun 'фарбами' agrees with 'тими'.",
                ),
                PronounDistractor(
                    text="тим",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'тим' є давальним множини; орудний відмінок вимагає закінчення -ими: 'тими'.",
                    explanation_en="'тим' is Dative plural; Instrumental case requires ending -ими: 'тими'.",
                ),
            ),
            rule_citation=cit_dem,
            rule_summary_ua=ua_dem,
            rule_summary_en=en_dem,
        ),
        PronounCard(
            card_id="pron_dem_tsomu",
            category=PronounCategory.DECLENSION_TSYEY_TOY,
            cefr_level="A2",
            sentence_before="У",
            sentence_after="науковому розділі книги автор детально аналізує причини історичних подій.",
            correct_answer="цьому",
            distractors=(
                PronounDistractor(
                    text="цьом",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Суржикове усічення закінчення; нормативна форма місцевого відмінка — 'цьому' (або поетичне 'цім').",
                    explanation_en="Corrupted truncated ending; standard Locative form is 'цьому'.",
                ),
                PronounDistractor(
                    text="цему",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Порушення м'якої основи займенника; нормативна форма — 'цьому'.",
                    explanation_en="Violation of soft stem; standard form is 'цьому'.",
                ),
                PronounDistractor(
                    text="цього",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'у' у значенні місця вимагає місцевого відмінка ('цьому'), а не родового 'цього'.",
                    explanation_en="Preposition 'у' denoting location requires Locative ('цьому'), not Genitive 'цього'.",
                ),
            ),
            rule_citation=cit_dem,
            rule_summary_ua=ua_dem,
            rule_summary_en=en_dem,
        ),
        # ====================================================================
        # 13. INTERROGATIVE_CHYI_KHTO_SHCHO (5 cards) [Правопис 2019 §§ 120–121]
        # ====================================================================
        PronounCard(
            card_id="pron_int_chyyoho",
            category=PronounCategory.INTERROGATIVE_CHYI_KHTO_SHCHO,
            cefr_level="B1",
            sentence_before="Ніхто в кімнаті не знав,",
            sentence_after="капелюха залишено на вішалці.",
            correct_answer="чийого",
            distractors=(
                PronounDistractor(
                    text="чийому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Займенник узгоджується з іменником 'капелюха' у родовому відмінку: правильно 'чийого'. Форма 'чийому' є давальним відмінком і порушує синтаксичне керування.",
                    explanation_en="Pronoun agrees with noun 'капелюха' in Genitive: 'чийого'. Form 'чийому' is Dative/Locative and violates case government.",
                ),
                PronounDistractor(
                    text="чиїм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'чиїм' є орудним відмінком однини або давальним множини; тут потрібен родовий 'чийого'.",
                    explanation_en="'чиїм' is Instrumental singular or Dative plural; Genitive 'чийого' is required.",
                ),
                PronounDistractor(
                    text="чийогось",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У підрядному з'ясувальному реченні зв'язок здійснює питально-відносний займенник 'чийого', а не неозначений 'чийогось'.",
                    explanation_en="In indirect relative clause, interrogative-relative 'чийого' is used, not indefinite 'чийогось'.",
                ),
            ),
            rule_citation=cit_int,
            rule_summary_ua=ua_int,
            rule_summary_en=en_int,
        ),
        PronounCard(
            card_id="pron_int_komu",
            category=PronounCategory.INTERROGATIVE_CHYI_KHTO_SHCHO,
            cefr_level="A2",
            sentence_before="Вона поцікавилася,",
            sentence_after="з присутніх колег належить ця чудова ідея.",
            correct_answer="кому",
            distractors=(
                PronounDistractor(
                    text="кім",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'кім' є варіантом місцевого відмінка (на кім); дієслово 'належати' вимагає давального 'кому'.",
                    explanation_en="'кім' is Locative variant (на кім); verb 'належати' requires Dative 'кому'.",
                ),
                PronounDistractor(
                    text="кого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'належати' керує давальним відмінком (кому?), а не родовим/знахідним 'кого'.",
                    explanation_en="'належати' governs Dative (кому?), not Genitive/Accusative 'кого'.",
                ),
                PronounDistractor(
                    text="ким",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'належати' вимагає давального відмінка адресата ('кому'), а не орудного 'ким'.",
                    explanation_en="'належати' requires Dative ('кому'), not Instrumental 'ким'.",
                ),
            ),
            rule_citation=cit_int,
            rule_summary_ua=ua_int,
            rule_summary_en=en_int,
        ),
        PronounCard(
            card_id="pron_int_chym",
            category=PronounCategory.INTERROGATIVE_CHYI_KHTO_SHCHO,
            cefr_level="B1",
            sentence_before="Учень не міг зрозуміти,",
            sentence_after="зумовлені такі несподівані зміни в розкладі занять.",
            correct_answer="чим",
            distractors=(
                PronounDistractor(
                    text="чого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Пасивний дієприкметник 'зумовлені' вимагає орудного відмінка причини/чинника (чим?), а не родового 'чого'.",
                    explanation_en="Participle 'зумовлені' governs Instrumental of cause/agent (чим?), not Genitive 'чого'.",
                ),
                PronounDistractor(
                    text="чому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'чому' є давальним відмінком; для позначення дійового чинника потрібен орудний відмінок 'чим'.",
                    explanation_en="'чому' is Dative; expressing causal factor requires Instrumental 'чим'.",
                ),
                PronounDistractor(
                    text="чім",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'чім' є варіантом місцевого відмінка (у чім); тут потрібен орудний 'чим'.",
                    explanation_en="'чім' is Locative variant (у чім); Instrumental 'чим' is required.",
                ),
            ),
            rule_citation=cit_int,
            rule_summary_ua=ua_int,
            rule_summary_en=en_int,
        ),
        PronounCard(
            card_id="pron_int_chyyimy",
            category=PronounCategory.INTERROGATIVE_CHYI_KHTO_SHCHO,
            cefr_level="B1",
            sentence_before="Ми довго з'ясовували,",
            sentence_after="зусиллями вдалося відновити цю пам'ятку архітектури.",
            correct_answer="чиїми",
            distractors=(
                PronounDistractor(
                    text="чиїма",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Орудний відмінок множини присвійного займенника 'чий' має закінчення -ими: 'чиїми', форма *чиїма ненормативна.",
                    explanation_en="Instrumental plural of 'чий' takes ending -ими: 'чиїми'; *чиїма is non-standard.",
                ),
                PronounDistractor(
                    text="чиїх",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'чиїх' є родовим відмінком; з орудним відмінком іменника 'зусиллями' узгоджується 'чиїми'.",
                    explanation_en="'чиїх' is Genitive; Instrumental noun 'зусиллями' requires 'чиїми'.",
                ),
                PronounDistractor(
                    text="чиїм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'чиїм' є давальним множини; орудний відмінок вимагає закінчення -ими: 'чиїми'.",
                    explanation_en="'чиїм' is Dative plural; Instrumental case requires ending -ими: 'чиїми'.",
                ),
            ),
            rule_citation=cit_int,
            rule_summary_ua=ua_int,
            rule_summary_en=en_int,
        ),
        PronounCard(
            card_id="pron_int_koho",
            category=PronounCategory.INTERROGATIVE_CHYI_KHTO_SHCHO,
            cefr_level="A2",
            sentence_before="Слідчий уважно запитав свідка,",
            sentence_after="саме той бачив на місці події того вечора.",
            correct_answer="кого",
            distractors=(
                PronounDistractor(
                    text="хто",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'бачити' керує знахідним відмінком прямого додатка (кого?), називний відмінок 'хто' неприпустимий.",
                    explanation_en="'бачити' governs direct Accusative (кого?); Nominative 'хто' is ungrammatical.",
                ),
                PronounDistractor(
                    text="кому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'бачити' вимагає знахідного відмінка ('кого'), а не давального 'кому'.",
                    explanation_en="'бачити' requires Accusative ('кого'), not Dative 'кому'.",
                ),
                PronounDistractor(
                    text="ким",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Дієслово 'бачити' вимагає знахідного відмінка прямого додатка ('кого'), а не орудного 'ким'.",
                    explanation_en="'бачити' requires Accusative ('кого'), not Instrumental 'ким'.",
                ),
            ),
            rule_citation=cit_int,
            rule_summary_ua=ua_int,
            rule_summary_en=en_int,
        ),
        # ====================================================================
        # 14. SEMANTIC_SAM_VS_SAMYI (5 cards) [Академічна стилістика]
        # ====================================================================
        PronounCard(
            card_id="pron_sem_sam",
            category=PronounCategory.SEMANTIC_SAM_VS_SAMYI,
            cefr_level="A2",
            sentence_before="Ніхто не підказував хлопцеві, він",
            sentence_after="зміг знайти правильне розв'язання задачі.",
            correct_answer="сам",
            distractors=(
                PronounDistractor(
                    text="самий",
                    interference_type=PronounInterferenceType.CONFUSION_SAM_VS_SAMYI,
                    explanation_ua="Займенник 'самий' вказує на тотожність або межу; для значення 'особисто, без сторонньої допомоги' вживається 'сам'.",
                    explanation_en="'самий' indicates identity or limit; for 'personally, unassisted', 'сам' is used.",
                ),
                PronounDistractor(
                    text="найбільш",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Слово 'найбільш' утворює аналітичний найвищий ступінь прикметників і не виражає самостійності дії суб'єкта.",
                    explanation_en="'найбільш' forms analytic superlatives and does not convey unassisted action.",
                ),
                PronounDistractor(
                    text="самого",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У ролі підмета при особовому займеннику 'він' потрібен називний відмінок 'сам'.",
                    explanation_en="Modifying subject 'він' requires Nominative 'сам'.",
                ),
            ),
            rule_citation=cit_sam,
            rule_summary_ua=ua_sam,
            rule_summary_en=en_sam,
        ),
        PronounCard(
            card_id="pron_sem_toy_samyi",
            category=PronounCategory.SEMANTIC_SAM_VS_SAMYI,
            cefr_level="B1",
            sentence_before="Ми домовилися про зустріч і прибули в",
            sentence_after="день, як і планували заздалегідь.",
            correct_answer="той самий",
            distractors=(
                PronounDistractor(
                    text="той сам",
                    interference_type=PronounInterferenceType.CONFUSION_SAM_VS_SAMYI,
                    explanation_ua="Для вираження тотожності ('однаковий, ідентичний') вживається сполука 'той самий', а не 'той сам'.",
                    explanation_en="Expressing identity ('the very same') requires phrase 'той самий', not 'той сам'.",
                ),
                PronounDistractor(
                    text="самий той",
                    interference_type=PronounInterferenceType.CONFUSION_SAM_VS_SAMYI,
                    explanation_ua="Порушення усталеного порядку слів; значення тотожності передається конструкцією 'той самий'.",
                    explanation_en="Inverted word order; standard construction for identity is 'той самий'.",
                ),
                PronounDistractor(
                    text="такий сам",
                    interference_type=PronounInterferenceType.CONFUSION_SAM_VS_SAMYI,
                    explanation_ua="Сполука 'такий сам' означає подібність властивостей, а точний збіг у часі (ідентичний день) виражає 'той самий'.",
                    explanation_en="'такий сам' denotes qualitative resemblance, whereas temporal identity (the identical day) requires 'той самий'.",
                ),
            ),
            rule_citation=cit_sam,
            rule_summary_ua=ua_sam,
            rule_summary_en=en_sam,
        ),
        PronounCard(
            card_id="pron_sem_naykrashchyi_anti_calque",
            category=PronounCategory.SEMANTIC_SAM_VS_SAMYI,
            cefr_level="B1",
            sentence_before="Цей талановитий архітектор створив",
            sentence_after="проєкт для нового театру в центрі міста.",
            correct_answer="найкращий",
            distractors=(
                PronounDistractor(
                    text="самий кращий",
                    interference_type=PronounInterferenceType.CONFUSION_SAM_VS_SAMYI,
                    explanation_ua="Груба калька: в українській мові слово 'самий' ніколи не утворює найвищого ступеня прикметників; правильно 'найкращий'.",
                    explanation_en="Gross calque: in Ukrainian, 'самий' never forms superlative adjectives; write synthetic 'найкращий'.",
                ),
                PronounDistractor(
                    text="більш кращий",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Подвійний вищий ступінь є граматичною помилкою; слід уживати синтетичну форму 'найкращий'.",
                    explanation_en="Double comparative is ungrammatical; use synthetic form 'найкращий'.",
                ),
                PronounDistractor(
                    text="самий добрий",
                    interference_type=PronounInterferenceType.CONFUSION_SAM_VS_SAMYI,
                    explanation_ua="Кальковане використання 'самий' для найвищої якості; нормативною формою є 'найкращий' або 'найдобріший'.",
                    explanation_en="Calqued use of 'самий' for superlative; standard forms are 'найкращий' or 'найдобріший'.",
                ),
            ),
            rule_citation=cit_sam,
            rule_summary_ua=ua_sam,
            rule_summary_en=en_sam,
        ),
        PronounCard(
            card_id="pron_sem_z_samoho_ranku",
            category=PronounCategory.SEMANTIC_SAM_VS_SAMYI,
            cefr_level="B1",
            sentence_before="Працьовиті господарі працювали в саду з",
            sentence_after="ранку і до пізнього вечора.",
            correct_answer="самого",
            distractors=(
                PronounDistractor(
                    text="сам",
                    interference_type=PronounInterferenceType.CONFUSION_SAM_VS_SAMYI,
                    explanation_ua="Для позначення часової чи просторової межі вживається форма 'з самого ранку', а не займенник самостійності 'сам'.",
                    explanation_en="For temporal boundary, 'з самого ранку' is used, not pronoun 'сам'.",
                ),
                PronounDistractor(
                    text="самого ж",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Усталена ідіоматична часова межа — 'з самого ранку'; додавання частки ж тут стилістично зайве.",
                    explanation_en="Idiomatic phrase of temporal boundary is 'з самого ранку'; adding ж is redundant.",
                ),
                PronounDistractor(
                    text="самим",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'з' у часовому значенні початкової точки вимагає родового відмінка ('з самого'), а не орудного 'самим'.",
                    explanation_en="Preposition 'з' indicating starting point governs Genitive ('з самого'), not Instrumental 'самим'.",
                ),
            ),
            rule_citation=cit_sam,
            rule_summary_ua=ua_sam,
            rule_summary_en=en_sam,
        ),
        PronounCard(
            card_id="pron_sem_sama",
            category=PronounCategory.SEMANTIC_SAM_VS_SAMYI,
            cefr_level="A2",
            sentence_before="Вона не хотіла нікого турбувати, тому вирішила",
            sentence_after="приготувати святковий обід для гостей.",
            correct_answer="сама",
            distractors=(
                PronounDistractor(
                    text="сама ж",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Контекст вимагає нейтрального значення самостійної дії; додавання частки ж вносить невідповідний протиставний відтінок.",
                    explanation_en="Context requires neutral unassisted action; adding ж introduces an unwanted contrastive nuance.",
                ),
                PronounDistractor(
                    text="сама-одна",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Фольклорно-поетична форма 'сама-одна' має надмірну експресію самотності, не властиву нейтральному опису.",
                    explanation_en="Poetic form 'сама-одна' conveys heavy loneliness not suited for neutral prose.",
                ),
                PronounDistractor(
                    text="самій",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У ролі узгодженого означення до суб'єкта 'вона' вимагається називний відмінок 'сама', а не давальний 'самій'.",
                    explanation_en="Agreement with subject 'вона' requires Nominative 'сама', not Dative 'самій'.",
                ),
            ),
            rule_citation=cit_sam,
            rule_summary_ua=ua_sam,
            rule_summary_en=en_sam,
        ),
        # ====================================================================
        # 15. POSSESSIVE_YIKHNIY_VS_YIKH (5 cards) [Правопис 2019 § 118]
        # ====================================================================
        PronounCard(
            card_id="pron_poss_yikhnim_ins",
            category=PronounCategory.POSSESSIVE_YIKHNIY_VS_YIKH,
            cefr_level="B1",
            sentence_before="Ми часто гостювали в цьому затишному селі й милувалися",
            sentence_after="квітучим яблуневим садом.",
            correct_answer="їхнім",
            distractors=(
                PronounDistractor(
                    text="їхньому",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'садом' стоїть в орудному відмінку; форма давального 'їхньому' порушує узгодження.",
                    explanation_en="'садом' is in Instrumental; Dative 'їхньому' violates case agreement.",
                ),
                PronounDistractor(
                    text="їхніми",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'сад' вжито в однині; форма множини 'їхніми' порушує числове узгодження.",
                    explanation_en="'сад' is singular; plural 'їхніми' violates number agreement.",
                ),
                PronounDistractor(
                    text="їхних",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Присвійний займенник 'їхній' відмінюється за м'якою групою прикметників: 'їхнім', форма з твердим закінченням *їхних помилкова.",
                    explanation_en="'їхній' declines as a soft-group adjective: 'їхнім'; hard-stem ending *їхних is ungrammatical.",
                ),
            ),
            rule_citation=cit_poss,
            rule_summary_ua=ua_poss,
            rule_summary_en=en_poss,
        ),
        PronounCard(
            card_id="pron_poss_yikhnye",
            category=PronounCategory.POSSESSIVE_YIKHNIY_VS_YIKH,
            cefr_level="B1",
            sentence_before="Учителі щиро подякували батькам за",
            sentence_after="активне сприяння розвитку шкільної громади.",
            correct_answer="їхнє",
            distractors=(
                PronounDistractor(
                    text="їхне",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Присвійний займенник 'їхній' належить до м'якої групи, тому в середньому роді пишеться літера є: 'їхнє', а не *їхне.",
                    explanation_en="'їхній' belongs to soft group; neuter singular is spelled with letter є: 'їхнє', not *їхне.",
                ),
                PronounDistractor(
                    text="їхнього",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'сприяння' стоїть у знахідному відмінку неістоти (що?); форма родового відмінка 'їхнього' неприпустима.",
                    explanation_en="'сприяння' is inanimate Accusative (що?); Genitive 'їхнього' is ungrammatical here.",
                ),
                PronounDistractor(
                    text="їхній",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'сприяння' середнього роду; форма чоловічого роду 'їхній' порушує узгодження за родом.",
                    explanation_en="'сприяння' is neuter; masculine 'їхній' violates gender agreement.",
                ),
            ),
            rule_citation=cit_poss,
            rule_summary_ua=ua_poss,
            rule_summary_en=en_poss,
        ),
        PronounCard(
            card_id="pron_poss_do_nykh",
            category=PronounCategory.POSSESSIVE_YIKHNIY_VS_YIKH,
            cefr_level="A2",
            sentence_before="Ми прийшли вчасно на зустріч і підійшли",
            sentence_after=", щоб обговорити плани на вихідні.",
            correct_answer="до них",
            distractors=(
                PronounDistractor(
                    text="до їхніх",
                    interference_type=PronounInterferenceType.CONFUSION_POSSESSIVE_VS_PERSONAL,
                    explanation_ua="'Їхній' — присвійний займенник; після прийменника з особовим значенням вживається форма особового займенника 'до них'.",
                    explanation_en="'Їхній' is possessive; personal pronoun after preposition requires 'до них'.",
                ),
                PronounDistractor(
                    text="до їх",
                    interference_type=PronounInterferenceType.MISSING_EPENTHETIC_N,
                    explanation_ua="Після прийменника у формі 3-ї особи множини обов'язковий приставний н-: 'до них'.",
                    explanation_en="After prepositions in 3rd-person plural, epenthetic n- is compulsory: 'до них'.",
                ),
                PronounDistractor(
                    text="до їм",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Прийменник 'до' вимагає родового відмінка ('до них'), а не давального 'їм'.",
                    explanation_en="Preposition 'до' governs Genitive ('до них'), not Dative 'їм'.",
                ),
            ),
            rule_citation=cit_poss,
            rule_summary_ua=ua_poss,
            rule_summary_en=en_poss,
        ),
        PronounCard(
            card_id="pron_poss_yikhniy_nom",
            category=PronounCategory.POSSESSIVE_YIKHNIY_VS_YIKH,
            cefr_level="A2",
            sentence_before="У центрі міста постав новий театр, і це був",
            sentence_after="найбільший спільний успіх архітекторів.",
            correct_answer="їхній",
            distractors=(
                PronounDistractor(
                    text="їхний",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Займенник 'їхній' відмінюється як прикметник м'якої групи із закінченням -ій: 'їхній', форма *їхний ненормативна.",
                    explanation_en="'їхній' declines as a soft-group adjective with ending -ій: 'їхній'; *їхний is ungrammatical.",
                ),
                PronounDistractor(
                    text="їхнього",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'успіх' є частиною іменного присудка в називному відмінку; форма родового 'їхнього' помилкова.",
                    explanation_en="'успіх' is in Nominative predicate; Genitive 'їхнього' violates case agreement.",
                ),
                PronounDistractor(
                    text="їхнім",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="У називному відмінку чоловічого роду потрібна форма 'їхній'; форма орудного 'їхнім' порушує відмінкове узгодження.",
                    explanation_en="Nominative masculine requires 'їхній'; Instrumental 'їхнім' violates agreement.",
                ),
            ),
            rule_citation=cit_poss,
            rule_summary_ua=ua_poss,
            rule_summary_en=en_poss,
        ),
        PronounCard(
            card_id="pron_poss_yikhnim_dav",
            category=PronounCategory.POSSESSIVE_YIKHNIY_VS_YIKH,
            cefr_level="B1",
            sentence_before="Директор гімназії високо оцінив старання учнів і щиро подякував",
            sentence_after="батькам за постійну турботу.",
            correct_answer="їхнім",
            distractors=(
                PronounDistractor(
                    text="їхним",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Присвійний займенник 'їхній' у давальному відмінку множини має м'яку основу: 'їхнім' (з літерою і), форма *їхним ненормативна.",
                    explanation_en="'їхній' in Dative plural has soft ending: 'їхнім' (with letter і); *їхним is ungrammatical.",
                ),
                PronounDistractor(
                    text="їхніми",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Іменник 'батькам' стоїть у давальному відмінку; форма орудного 'їхніми' порушує узгодження за відмінком.",
                    explanation_en="'батькам' is Dative; Instrumental 'їхніми' violates case agreement.",
                ),
                PronounDistractor(
                    text="їхніх",
                    interference_type=PronounInterferenceType.CORRUPTED_DECLENSION_STEM,
                    explanation_ua="Форма 'їхніх' є родовим відмінком; з давальним відмінком адресата (кому?) узгоджується 'їхнім'.",
                    explanation_en="'їхніх' is Genitive; Dative recipient (кому?) requires 'їхнім'.",
                ),
            ),
            rule_citation=cit_poss,
            rule_summary_ua=ua_poss,
            rule_summary_en=en_poss,
        ),
    ]

    return cards


def validate_pronoun_card(card: PronounCard) -> list[str]:
    """Validate a single pronoun practice card for integrity and zero collisions."""
    errors: list[str] = []

    if not card.card_id:
        errors.append("Empty card_id")
    if not card.correct_answer:
        errors.append("Empty correct_answer")
    if len(card.distractors) != 3:
        errors.append(f"Card {card.card_id} must have exactly 3 distractors, got {len(card.distractors)}")

    distractor_texts = [d.text for d in card.distractors]
    if len(set(distractor_texts)) != len(distractor_texts):
        errors.append(f"Card {card.card_id} has duplicate distractors: {distractor_texts}")

    if card.correct_answer in distractor_texts:
        errors.append(f"Card {card.card_id} collision: correct answer '{card.correct_answer}' is in distractors")

    all_opts = card.all_options()
    if len(all_opts) != 4:
        errors.append(f"Card {card.card_id} all_options must return 4 unique items, got {len(all_opts)}")

    if "_______" not in card.prompt_display:
        errors.append(f"Card {card.card_id} prompt_display missing blank placeholder '_______'")

    for d in card.distractors:
        if not d.explanation_ua:
            errors.append(f"Card {card.card_id} distractor '{d.text}' has empty explanation_ua")
        if not d.explanation_en:
            errors.append(f"Card {card.card_id} distractor '{d.text}' has empty explanation_en")

    if not card.rule_citation:
        errors.append(f"Card {card.card_id} missing rule_citation")
    if not card.rule_summary_ua:
        errors.append(f"Card {card.card_id} missing rule_summary_ua")
    if not card.rule_summary_en:
        errors.append(f"Card {card.card_id} missing rule_summary_en")

    return errors


def export_pronoun_mechanics_deck(cards: list[PronounCard], output_path: Path | None = None) -> dict[str, Any]:
    """Export canonical pronoun cards to JSON deck format matching PracticePronounMechanicsCard."""
    deck: dict[str, Any] = {
        "schema_version": "1.0",
        "title": "Ukrainian Pronoun Deep Mechanics Practice (Займенник)",
        "card_count": len(cards),
        "categories": [c.value for c in PronounCategory],
        "cards": [
            {
                "card_id": c.card_id,
                "category": c.category.value,
                "cefr_level": c.cefr_level,
                "prompt_sentence": c.prompt_display,
                "blank_target": c.correct_answer,
                "correct_answer": c.correct_answer,
                "options": c.all_options(),
                "distractors": [
                    {
                        "text": d.text,
                        "interference_type": d.interference_type.value,
                        "explanation": {
                            "ua": d.explanation_ua,
                            "en": d.explanation_en,
                        },
                    }
                    for d in c.distractors
                ],
                "pravopys_section": c.rule_citation,
                "rule_summary": {
                    "ua": c.rule_summary_ua,
                    "en": c.rule_summary_en,
                },
            }
            for c in cards
        ],
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return deck


def verify_deck_with_vesum(cards: list[PronounCard], db_path: Path | None = None) -> dict[str, Any]:
    """Verify that all target inflected pronoun tokens exist in the VESUM sqlite database."""
    vesum_db = db_path or PROJECT_ROOT / "data" / "vesum.db"
    if not vesum_db.exists():
        return {
            "verified": None,
            "status": "skipped",
            "message": f"VESUM database not found at {vesum_db}",
            "missing_count": 0,
            "missing_forms": [],
        }

    conn = sqlite3.connect(vesum_db)
    cursor = conn.cursor()

    missing_forms: list[dict[str, Any]] = []
    checked = 0

    for card in cards:
        # Check every token of the correct answer in VESUM
        tokens = card.correct_answer.strip().split()
        for tok in tokens:
            clean_tok = tok.strip(".,;:!?«»\"'")
            if not clean_tok:
                continue
            checked += 1
            cursor.execute(
                "SELECT count(*) FROM forms_all WHERE word_form = ?",
                (clean_tok,),
            )
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute(
                    "SELECT count(*) FROM forms WHERE word_form = ?",
                    (clean_tok,),
                )
                count = cursor.fetchone()[0]

            if count == 0:
                missing_forms.append(
                    {
                        "card_id": card.card_id,
                        "correct_answer": card.correct_answer,
                        "missing_token": clean_tok,
                    }
                )

    conn.close()
    return {
        "verified": len(missing_forms) == 0,
        "status": "passed" if len(missing_forms) == 0 else "failed",
        "checked_token_count": checked,
        "missing_count": len(missing_forms),
        "missing_forms": missing_forms,
    }


def verify_distractors_with_vesum(cards: list[PronounCard], db_path: Path | None = None) -> dict[str, Any]:
    """Verify that single-word corrupted pronoun distractors do not falsely match standard literary pronouns in VESUM."""
    vesum_db = db_path or PROJECT_ROOT / "data" / "vesum.db"
    if not vesum_db.exists():
        return {
            "verified": None,
            "status": "skipped",
            "message": f"VESUM database not found at {vesum_db}",
            "invalid_distractor_count": 0,
            "invalid_distractors": [],
        }

    conn = sqlite3.connect(vesum_db)
    cursor = conn.cursor()

    corruption_types = {
        PronounInterferenceType.CORRUPTED_INSTRUMENTAL_FORM,
        PronounInterferenceType.DEFECTIVE_REFL_NOMINATIVE,
        PronounInterferenceType.SOLID_WRITTEN_HYPHEN_PARTICLE,
        PronounInterferenceType.SOLID_SPLIT_PREPOSITION,
    }

    invalid_distractors: list[dict[str, Any]] = []
    checked = 0

    for card in cards:
        for dist in card.distractors:
            if dist.interference_type in corruption_types:
                clean_text = dist.text.strip().strip(".,;:!?«»\"'")
                # Only check single-token forms
                if " " in clean_text or "-" in clean_text:
                    continue
                checked += 1
                cursor.execute(
                    "SELECT lemma, pos, tags FROM forms_all WHERE word_form = ?",
                    (clean_text,),
                )
                rows = cursor.fetchall()
                if not rows:
                    cursor.execute(
                        "SELECT lemma, pos, tags FROM forms WHERE word_form = ?",
                        (clean_text,),
                    )
                    rows = cursor.fetchall()

                # A distractor is invalid if it matches a standard literary pronoun without non-standard tags
                standard_pronoun_rows = [
                    r
                    for r in rows
                    if "pron" in r[2]
                    and ":bad" not in r[2]
                    and ":alt" not in r[2]
                    and ":subst" not in r[2]
                    and ":arch" not in r[2]
                    and ":dial" not in r[2]
                ]
                if standard_pronoun_rows:
                    invalid_distractors.append(
                        {
                            "card_id": card.card_id,
                            "distractor": dist.text,
                            "interference_type": dist.interference_type.value,
                            "matching_vesum_rows": standard_pronoun_rows,
                        }
                    )

    conn.close()
    return {
        "verified": len(invalid_distractors) == 0,
        "status": "passed" if len(invalid_distractors) == 0 else "failed",
        "checked_distractor_count": checked,
        "invalid_distractors": invalid_distractors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ukrainian Pronoun Deep Mechanics Practice Engine")
    parser.add_argument(
        "--export",
        type=Path,
        default=PROJECT_ROOT / "data" / "practice" / "pronoun_mechanics_deck.json",
        help="Path to export compiled JSON practice deck",
    )
    parser.add_argument(
        "--verify-vesum",
        action="store_true",
        help="Verify inflected targets against VESUM sqlite database",
    )
    args = parser.parse_args()

    cards = build_canonical_pronoun_cards()
    print(f"Validated {len(cards)} canonical pronoun practice cards across {len(PronounCategory)} categories.")

    total_errors = 0
    for c in cards:
        errs = validate_pronoun_card(c)
        if errs:
            print(f"Error in card {c.card_id}: {errs}", file=sys.stderr)
            total_errors += len(errs)

    if total_errors > 0:
        print(f"Validation failed with {total_errors} errors.", file=sys.stderr)
        sys.exit(1)

    export_pronoun_mechanics_deck(cards, args.export)
    print(f"Exported deck to {args.export}")

    if args.verify_vesum:
        report = verify_deck_with_vesum(cards)
        print(f"VESUM target verification: {report}")
        dist_report = verify_distractors_with_vesum(cards)
        print(f"VESUM distractor verification: {dist_report}")
        if report.get("verified") is False or dist_report.get("verified") is False:
            print("ERROR: VESUM verification failed!", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
