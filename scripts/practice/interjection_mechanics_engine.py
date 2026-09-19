#!/usr/bin/env python3
"""Interjection and Onomatopoeia Deep Mechanics Practice Engine (Вигук та Звуконаслідування).

Epic #8241: 10 Parts of Speech Deep Mechanics & Practice Hub Re-architecture.
Issue #8275: Interjection & Onomatopoeia Deep Mechanics Practice Engine (Phase 8).

Categories (12 categories x 5 cards = 60 canonical practice cards):
 1. interjection_emotional_positive         - Joy, Delight, Surprise, Admiration (ура, ах, ох, леле, овва) [Академічна граматика; Правопис 2019 § 157, п. 3, § 158, п. 9]
 2. interjection_emotional_negative         - Sorrow, Grief, Fear, Indignation (ой, ай, лишенько, пхе, тьху) [Академічна граматика; Правопис 2019 § 157, п. 3, § 158, п. 9]
 3. interjection_volitional_imperative      - Command, Call to Action, Silence (гайда, марш, годі, геть, цить) [Академічна граматика; Правопис 2019 § 157, п. 3]
 4. interjection_volitional_animal          - Animal Calls and Driving (киць-киць, киш, тпру, но, вйо) [Академічна граматика; СУМ-20]
 5. interjection_etiquette_greeting_farewell- Greeting and Farewell (добрий день, добрий вечір, до побачення, на добраніч, бувайте) [Правопис 2019 § 41, п. 2]
 6. interjection_etiquette_gratitude_apology- Gratitude, Apology, Politeness (будь ласка, дякую, пробачте, перепрошую, вибачте) [Правопис 2019 § 41, п. 2]
 7. interjection_onomatopoeia_nature_mechanics - Nature, Clocks, Bells, Water (дзень-дзелень, тік-так, крап-крап, хлюп-хлюп, цок-цок) [Правопис 2019 § 35, п. 5, 4)]
 8. interjection_onomatopoeia_animal_sounds - Animal and Bird Sounds (гав-гав, няв-няв, ку-ку, кар-кар, ква-ква) [Правопис 2019 § 35, п. 5, 4)]
 9. interjection_spelling_hyphen_repeated   - Repeated & Echoed Interjections (ой-ой-ой, ха-ха-ха, ай-яй-яй, дзень-дзелень, тук-тук) [Правопис 2019 § 35, п. 5, 4)]
10. interjection_spelling_particles_hyphen  - Enclitic Particles -бо, -но, -то & Idioms (годі-бо, ну-бо, давай-но, їй-богу, їй-право) [Правопис 2019 § 35, п. 5, 4), § 44, п. 3, 1)]
11. interjection_spelling_multiword_separate- Multi-word Phrases Spelled Separately (будь ласка, до побачення, на добраніч, о господи, от тобі й маєш) [Правопис 2019 § 41, п. 2, § 53; Авраменко § 88]
12. interjection_syntax_punctuation_particle- Syntax: Interjection vs Vocative Particle О/Ой, Comma vs Exclamation Mark [Правопис 2019 § 46, п. 2, § 157, п. 3, § 158, п. 9, прим. 1]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENCLITIC_PARTICLES: frozenset[str] = frozenset({"бо", "но", "то", "от", "таки"})
REDUPLICATION_BASE_TAG_SUBSTRINGS: tuple[str, ...] = (
    "intj",
    "onomat",
    "predic",
    "part",
    "v_naz",
)
ENCLITIC_STEM_TAG_SUBSTRINGS: tuple[str, ...] = (
    ":impr",
    "intj",
    "predic",
    "adv",
    "part",
)


class InterjectionCategory(StrEnum):
    EMOTIONAL_POSITIVE = "interjection_emotional_positive"
    EMOTIONAL_NEGATIVE = "interjection_emotional_negative"
    VOLITIONAL_IMPERATIVE = "interjection_volitional_imperative"
    VOLITIONAL_ANIMAL = "interjection_volitional_animal"
    ETIQUETTE_GREETING_FAREWELL = "interjection_etiquette_greeting_farewell"
    ETIQUETTE_GRATITUDE_APOLOGY = "interjection_etiquette_gratitude_apology"
    ONOMATOPOEIA_NATURE_MECHANICS = "interjection_onomatopoeia_nature_mechanics"
    ONOMATOPOEIA_ANIMAL_SOUNDS = "interjection_onomatopoeia_animal_sounds"
    SPELLING_HYPHEN_REPEATED = "interjection_spelling_hyphen_repeated"
    SPELLING_PARTICLES_HYPHEN = "interjection_spelling_particles_hyphen"
    SPELLING_MULTIWORD_SEPARATE = "interjection_spelling_multiword_separate"
    SYNTAX_PUNCTUATION_PARTICLE = "interjection_syntax_punctuation_particle"


class InterjectionInterferenceKey(StrEnum):
    HYPHEN_OMISSION = "HYPHEN_OMISSION"
    HYPHEN_SEPARATION = "HYPHEN_SEPARATION"
    UNWARRANTED_HYPHEN = "UNWARRANTED_HYPHEN"
    UNWARRANTED_FUSION = "UNWARRANTED_FUSION"
    PARTICLE_HYPHEN_OMISSION = "PARTICLE_HYPHEN_OMISSION"
    IDIOM_HYPHEN_OMISSION = "IDIOM_HYPHEN_OMISSION"
    PUNCTUATION_COMMA_OMISSION = "PUNCTUATION_COMMA_OMISSION"
    PUNCTUATION_UNWARRANTED_COMMA_PARTICLE = "PUNCTUATION_UNWARRANTED_COMMA_PARTICLE"
    PUNCTUATION_EXCLAMATION_OMISSION = "PUNCTUATION_EXCLAMATION_OMISSION"
    PUNCTUATION_WRONG_DELIMITER = "PUNCTUATION_WRONG_DELIMITER"
    RUSSIANISM_CALQUE = "RUSSIANISM_CALQUE"
    INCORRECT_EMOTIONAL_TONE = "INCORRECT_EMOTIONAL_TONE"
    INCORRECT_VOLITIONAL_COMMAND = "INCORRECT_VOLITIONAL_COMMAND"
    INCORRECT_SOUND_SOURCE = "INCORRECT_SOUND_SOURCE"
    CORRUPTED_ADVERB_FORM = "CORRUPTED_ADVERB_FORM"


@dataclass(frozen=True)
class InterjectionDistractor:
    text: str
    interference_key: InterjectionInterferenceKey
    explanation_ua: str
    explanation_en: str


@dataclass(frozen=True)
class InterjectionCard:
    card_id: str
    category: InterjectionCategory
    prompt: str
    target_token: str
    correct_answer: str
    distractors: tuple[InterjectionDistractor, InterjectionDistractor, InterjectionDistractor]
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


def resolve_emotional_positive_rule() -> tuple[str, str, str]:
    cit = "Академічна граматика; СУМ-20; Правопис 2019 § 157, п. 3, § 158, п. 9"
    ua = "Емоційні вигуки виражають почуття радості, задоволення, здивування, захоплення або полегшення (ура, ах, ох, леле, овва). Вони не називають почуттів, а безпосередньо сигналізують про емоційний стан мовця per § 157, п. 3, § 158, п. 9."
    en = "Emotional interjections express feelings of joy, delight, surprise, admiration, or relief (ура, ах, ох, леле, овва). They do not name emotions but directly signal the speaker's emotional state per § 157, p. 3, § 158, p. 9."
    return cit, ua, en


def resolve_emotional_negative_rule() -> tuple[str, str, str]:
    cit = "Академічна граматика; СУМ-20; Правопис 2019 § 157, п. 3, § 158, п. 9"
    ua = "Емоційні вигуки негативного спектра передають сум, біль, жаль, переляк, обурення, огиду або досаду (ой, ай, лишенько, пхе, тьху). На письмі вони виділяються комами per § 158, п. 9 або знаком оклику per § 157, п. 3."
    en = "Negative emotional interjections convey sorrow, pain, grief, fear, indignation, disgust, or vexation (ой, ай, лишенько, пхе, тьху). In writing, they are set off by commas per § 158, p. 9 or an exclamation mark per § 157, p. 3."
    return cit, ua, en


def resolve_volitional_imperative_rule() -> tuple[str, str, str]:
    cit = "Академічна граматика; СУМ-20; Правопис 2019 § 157, п. 3"
    ua = "Спонукальні (волевиявні) вигуки виражають заклик до дії, наказ, заборону, вимогу тиші або привертання уваги (гайда, марш, годі, геть, цить). Вони спонукають адресата до певної реакції."
    en = "Volitional (imperative) interjections express calls to action, commands, prohibitions, demands for silence, or attention calls (гайда, марш, годі, геть, цить). They prompt the addressee into a specific action."
    return cit, ua, en


def resolve_volitional_animal_rule() -> tuple[str, str, str]:
    cit = "Академічна граматика; СУМ-20"
    ua = "Волевиявні вигуки для тварин слугують для підкликання або відгону свійських тварин і птахів (киць-киць — підкликання котів, киш — відгін птахів, тпру — зупинка коней, но — рух коней уперед, вйо — поганяння упряжі)."
    en = "Volitional animal interjections serve to call or drive domestic animals and birds (киць-киць for cats, киш for driving birds, тпру to halt horses, но to urge horses forward, вйо to urge draught animals)."
    return cit, ua, en


def resolve_etiquette_greeting_farewell_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 2; Академічна граматика; СУМ-20"
    ua = "Формули мовленнєвого етикету для привітання та прощання (добрий день, добрий вечір, до побачення, на добраніч, бувайте) функціонують як вигуки. Багатослівні етикетні сполуки пишуться окремо per § 41, п. 2."
    en = "Speech etiquette formulas for greetings and farewells (добрий день, добрий вечір, до побачення, на добраніч, бувайте) function as interjections. Multi-word etiquette phrases are spelled separately per § 41, p. 2."
    return cit, ua, en


def resolve_etiquette_gratitude_apology_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 2; Академічна граматика; СУМ-20"
    ua = "Етикетні вигуки вдячності, вибачення та ввічливості (будь ласка, дякую, щиро дякую, пробачте, перепрошую, вибачте) регулюють соціальну взаємодію. Сполука «будь ласка» пишеться окремо без дефіса per § 41, п. 2."
    en = "Etiquette interjections of gratitude, apology, and politeness (будь ласка, дякую, щиро дякую, пробачте, перепрошую, вибачте) regulate social interaction. The polite phrase 'будь ласка' is spelled separately without hyphen per § 41, p. 2."
    return cit, ua, en


def resolve_onomatopoeia_nature_mechanics_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 35, п. 5, 4); СУМ-20"
    ua = "Звуконаслідувальні слова відтворюють звуки неживої природи, води, механізмів, годинників чи дзвоників (дзень-дзелень, тік-так, крап-крап, хлюп-хлюп, цок-цок). Повторювані або відлунні звуконаслідування пишуться через дефіс per § 35, п. 5, 4)."
    en = "Onomatopoeic words imitate sounds of inanimate nature, water, machinery, clocks, or bells (дзень-дзелень, тік-так, крап-крап, хлюп-хлюп, цок-цок). Repeated or echoic onomatopoeias are spelled with a hyphen per § 35, p. 5, 4)."
    return cit, ua, en


def resolve_onomatopoeia_animal_sounds_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 35, п. 5, 4); СУМ-20"
    ua = "Звуконаслідування голосів тварин і птахів імітують гавкіт, нявчання, кування зозулі, каркання, квакання (гав-гав, няв-няв, ку-ку, кар-кар, ква-ква). Повторювані звуки пишуться через дефіс per § 35, п. 5, 4)."
    en = "Animal and bird sound onomatopoeias imitate barking, meowing, cuckoo calls, croaking, or quacking (гав-гав, няв-няв, ку-ку, кар-кар, ква-ква). Repeated sounds are hyphenated per § 35, p. 5, 4)."
    return cit, ua, en


def resolve_spelling_hyphen_repeated_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 35, п. 5, 4); СУМ-20"
    ua = "Через дефіс пишуться повторювані або відлунні вигуки та звуконаслідувальні слова: ой-ой-ой, ха-ха-ха, ай-яй-яй, дзень-дзелень, тук-тук per § 35, п. 5, 4)."
    en = "Repeated or echoic interjections and onomatopoeic words are spelled with a hyphen per § 35, p. 5, 4): ой-ой-ой, ха-ха-ха, ай-яй-яй, дзень-дзелень, тук-тук."
    return cit, ua, en


def resolve_spelling_particles_hyphen_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 35, п. 5, 4), § 44, п. 3, 1); СУМ-20"
    ua = "Через дефіс пишуться вигуки з постпозитивними частками -бо, -но, -то (годі-бо, ну-бо, давай-но) per § 44, п. 3, 1), а також усталені вигукові ідіоми їй-богу, їй-право per § 35, п. 5, 4)."
    en = "Interjections with enclitic particles -бо, -но, -то (годі-бо, ну-бо, давай-но) are spelled with a hyphen per § 44, p. 3, 1), as are fixed interjection idioms їй-богу, їй-право per § 35, p. 5, 4)."
    return cit, ua, en


def resolve_spelling_multiword_separate_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 41, п. 2, § 53; СУМ-20; Авраменко § 88"
    ua = "Окремо пишуться складні вигуки та мовленнєві етикетні звороти, що складаються з кількох слів: будь ласка, до побачення, на добраніч, о господи, от тобі й маєш per § 41, п. 2, § 53; Авраменко § 88. Написання через дефіс або разом є грубою орфографічною помилкою."
    en = "Multi-word interjections and speech etiquette phrases consisting of several words are spelled separately: будь ласка, до побачення, на добраніч, о господи, от тобі й маєш per § 41, p. 2, § 53; Avramenko § 88. Writing them with hyphens or fused is an orthographic error."
    return cit, ua, en


def resolve_syntax_punctuation_particle_rule() -> tuple[str, str, str]:
    cit = "Правопис 2019 § 46, п. 2, § 157, п. 3, § 158, п. 9, прим. 1"
    ua = "Вигуки відокремлюються комами per § 158, п. 9 або знаком оклику per § 157, п. 3. Проте слова «о», «ой», ужиті перед звертанням як підсилювальні частки, НЕ відокремлюються комою від наступного іменника: «О краю мій!», «Ой Дніпре мій!» per § 158, п. 9, прим. 1. Якщо ж «о», «ой» є самостійними емоційними вигуками, кома ставиться: «О, краю мій, як довго я тебе шукав!». Якщо вигук на початку речення має знак оклику, наступне слово пишеться з великої букви per § 46, п. 2."
    en = "Interjections are set off by commas per § 158, p. 9 or an exclamation mark per § 157, p. 3. However, words 'о', 'ой' used before an address as intensifying particles are NOT separated by a comma from the following noun: 'О краю мій!', 'Ой Дніпре мій!' per § 158, p. 9, note 1. If 'о', 'ой' are independent emotional interjections, a comma is required: 'О, краю мій...'. If an interjection at sentence start has an exclamation mark, the following word is capitalized per § 46, p. 2."
    return cit, ua, en


def build_canonical_interjection_cards() -> list[InterjectionCard]:
    """Constructs 60 canonical practice cards across 12 interjection and onomatopoeia categories."""
    cards: list[InterjectionCard] = []

    # Category 1: Emotional Positive (5 cards)
    cit1, ua1, en1 = resolve_emotional_positive_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_01",
            category=InterjectionCategory.EMOTIONAL_POSITIVE,
            prompt="«_______! Наша футбольна збірна здобула блискучу перемогу!» — радісно вигукнули вболівальники на стадіоні.",
            target_token="ура",
            correct_answer="Ура",
            distractors=(
                InterjectionDistractor(
                    text="Ой",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="Вигук «ой» виражає переляк, біль або сум, а не тріумф і радість перемоги.",
                    explanation_en="Interjection 'ой' expresses fear, pain, or grief, not triumph and joy of victory.",
                ),
                InterjectionDistractor(
                    text="Тьху",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="Вигук «тьху» виражає презирство, огиду чи розчарування.",
                    explanation_en="Interjection 'тьху' expresses contempt, disgust, or disappointment.",
                ),
                InterjectionDistractor(
                    text="Цить",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Цить» є спонукальним вигуком вимоги тиші, а не радісного захоплення.",
                    explanation_en="'Цить' is an imperative interjection demanding silence, not a joyful exclamation.",
                ),
            ),
            rule_citation=cit1,
            rule_summary_ua=ua1,
            rule_summary_en=en1,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_02",
            category=InterjectionCategory.EMOTIONAL_POSITIVE,
            prompt="«_______, яка чарівна й мелодійна пісня лине з квітучого вишневого саду!» — захоплено мовила Марія.",
            target_token="ах",
            correct_answer="Ах",
            distractors=(
                InterjectionDistractor(
                    text="Пхе",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="Вигук «пхе» виражає зневагу або гордовиту відразу, а не захоплення красою.",
                    explanation_en="Interjection 'пхе' expresses disdain or haughty disgust, not admiration of beauty.",
                ),
                InterjectionDistractor(
                    text="Геть",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Геть» є спонукальним вигуком наказу відійти або зникнути.",
                    explanation_en="'Геть' is an imperative command to leave or go away.",
                ),
                InterjectionDistractor(
                    text="Тпру",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Тпру» є наказом для зупинки коней, а не виразом естетичного захоплення.",
                    explanation_en="'Тпру' is a command to halt horses, not an expression of aesthetic delight.",
                ),
            ),
            rule_citation=cit1,
            rule_summary_ua=ua1,
            rule_summary_en=en1,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_03",
            category=InterjectionCategory.EMOTIONAL_POSITIVE,
            prompt="«_______, як дивовижно виблискує вранішня роса під першими променями сонця!» — шепотів мандрівник.",
            target_token="ох",
            correct_answer="Ох",
            distractors=(
                InterjectionDistractor(
                    text="Жаль",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="Слово «жаль» виражає смуток або співчуття, що суперечить радісному спогляданню краси.",
                    explanation_en="The word 'жаль' expresses sorrow or pity, contradicting joyful admiration of nature.",
                ),
                InterjectionDistractor(
                    text="Марш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Марш» є суворим наказом негайно вирушати, а не емоційним вигуком милування.",
                    explanation_en="'Марш' is a strict command to move immediately, not an emotional interjection.",
                ),
                InterjectionDistractor(
                    text="Киш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киш» слугує для відгону птахів, а не для вираження замилування росою.",
                    explanation_en="'Киш' is used to scare away birds, not to admire the morning dew.",
                ),
            ),
            rule_citation=cit1,
            rule_summary_ua=ua1,
            rule_summary_en=en1,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_04",
            category=InterjectionCategory.EMOTIONAL_POSITIVE,
            prompt="«_______, скільки ж смачних ягід уродило цього літа в лісі!» — радісно здивувалася бабуся.",
            target_token="леле",
            correct_answer="Леле",
            distractors=(
                InterjectionDistractor(
                    text="Тьху",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="Вигук «тьху» сигналізує про прикрість або зневагу, а не про приємне здивування багатим урожаєм.",
                    explanation_en="Interjection 'тьху' signals vexation or disdain, not pleasant surprise at a rich harvest.",
                ),
                InterjectionDistractor(
                    text="Ша",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Ша» є наказом замовкнути й дотримуватися тиші.",
                    explanation_en="'Ша' is a command to be quiet and keep silence.",
                ),
                InterjectionDistractor(
                    text="Вйо",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Вйо» є спонукальним вигуком для прискорення руху коней.",
                    explanation_en="'Вйо' is an imperative command urging horses to move faster.",
                ),
            ),
            rule_citation=cit1,
            rule_summary_ua=ua1,
            rule_summary_en=en1,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_05",
            category=InterjectionCategory.EMOTIONAL_POSITIVE,
            prompt="«_______, невже ти справді власноруч змайстрував такий чудовий вітрильник?» — вражено спитав дідусь.",
            target_token="овва",
            correct_answer="Овва",
            distractors=(
                InterjectionDistractor(
                    text="Лишенько",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Лишенько» виражає біду, страх і тривогу, а «овва» передає щире здивування й подив.",
                    explanation_en="'Лишенько' expresses trouble, fear, and anxiety, whereas 'овва' conveys genuine surprise.",
                ),
                InterjectionDistractor(
                    text="Годі",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Годі» виражає заборону або припинення дії, а не подив від майстерності.",
                    explanation_en="'Годі' expresses prohibition or cessation of action, not surprise at craftsmanship.",
                ),
                InterjectionDistractor(
                    text="Киць-киць",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киць-киць» слугує виключно для підкликання котів.",
                    explanation_en="'Киць-киць' serves solely to call cats.",
                ),
            ),
            rule_citation=cit1,
            rule_summary_ua=ua1,
            rule_summary_en=en1,
        )
    )

    # Category 2: Emotional Negative (5 cards)
    cit2, ua2, en2 = resolve_emotional_negative_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_06",
            category=InterjectionCategory.EMOTIONAL_NEGATIVE,
            prompt="«_______, як сильно ниє поранена нога після падіння на слизькій стежці!» — застогнав турист.",
            target_token="ой",
            correct_answer="Ой",
            distractors=(
                InterjectionDistractor(
                    text="Ура",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ура» є радісним вигуком тріумфу, що неприпустимо при сильному фізичному болю.",
                    explanation_en="'Ура' is a joyous cry of triumph, inappropriate for acute physical pain.",
                ),
                InterjectionDistractor(
                    text="Чудово",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Чудово» виражає найвище схвалення, а не фізичні страждання від травми.",
                    explanation_en="'Чудово' expresses high approval, not physical suffering from an injury.",
                ),
                InterjectionDistractor(
                    text="Гайда",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Гайда» спонукає вирушати в дорогу, що неможливо для людини з травмованою ногою.",
                    explanation_en="'Гайда' urges setting out on a journey, impossible for an injured person.",
                ),
            ),
            rule_citation=cit2,
            rule_summary_ua=ua2,
            rule_summary_en=en2,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_07",
            category=InterjectionCategory.EMOTIONAL_NEGATIVE,
            prompt="«_______, як пече цей кропив'яний лист, коли торкнешся його голою рукою!» — зойкнув малюк.",
            target_token="ай",
            correct_answer="Ай",
            distractors=(
                InterjectionDistractor(
                    text="Овва",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Овва» виражає здивування або іронію, а «ай» передає раптовий гострий фізичний біль.",
                    explanation_en="'Овва' expresses surprise or irony, whereas 'ай' conveys sudden sharp physical pain.",
                ),
                InterjectionDistractor(
                    text="Браво",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Браво» є вигуком захоплення майстерністю, що абсурдно при опіку кропивою.",
                    explanation_en="'Браво' is an exclamation of acclaim for mastery, absurd when stung by nettles.",
                ),
                InterjectionDistractor(
                    text="Но",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Но» є вигуком поганяння коней, а не реакцією на біль від опіку.",
                    explanation_en="'Но' is a call urging horses forward, not a reaction to burning pain.",
                ),
            ),
            rule_citation=cit2,
            rule_summary_ua=ua2,
            rule_summary_en=en2,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_08",
            category=InterjectionCategory.EMOTIONAL_NEGATIVE,
            prompt="«Ой _______, що ж тепер нам робити серед темного дрімучого лісу?» — забідкалися заблукалі діти.",
            target_token="лишенько",
            correct_answer="лишенько",
            distractors=(
                InterjectionDistractor(
                    text="радість",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Радість» виражає позитивну емоцію, несумісну з панікою дітей, які заблукали в хащі.",
                    explanation_en="'Радість' expresses a positive emotion incompatible with panic in the dark woods.",
                ),
                InterjectionDistractor(
                    text="ура",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ура» суперечить почуттю безпорадності та страху у вигуку «ой лишенько».",
                    explanation_en="'Ура' contradicts the sense of helplessness and fear in 'ой лишенько'.",
                ),
                InterjectionDistractor(
                    text="марш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Марш» є військовою чи суворою командою, а не бідканням про лихо.",
                    explanation_en="'Марш' is a strict command, not a lamentation over misfortune.",
                ),
            ),
            rule_citation=cit2,
            rule_summary_ua=ua2,
            rule_summary_en=en2,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_09",
            category=InterjectionCategory.EMOTIONAL_NEGATIVE,
            prompt="«_______, хіба цим простим фокусом можна когось насправді вразити?» — гордовито фиркнув скептик.",
            target_token="пхе",
            correct_answer="Пхе",
            distractors=(
                InterjectionDistractor(
                    text="Ах",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ах» передає захоплення чи розчулення, а «пхе» виражає зневажливу зверхність.",
                    explanation_en="'Ах' conveys admiration, whereas 'пхе' expresses scornful contempt.",
                ),
                InterjectionDistractor(
                    text="Слава богу",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Слава богу» виражає полегшення або вдячність, а не зневагу.",
                    explanation_en="'Слава богу' expresses relief or gratitude, not contempt.",
                ),
                InterjectionDistractor(
                    text="Агов",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Агов» є вигуком для привертання уваги або оклику на відстані.",
                    explanation_en="'Агов' is an interjection for attracting attention or calling from a distance.",
                ),
            ),
            rule_citation=cit2,
            rule_summary_ua=ua2,
            rule_summary_en=en2,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_10",
            category=InterjectionCategory.EMOTIONAL_NEGATIVE,
            prompt="«_______, знову через неуважність переплутав потрібні документи!» — з досадою пробурмотів працівник.",
            target_token="тьху",
            correct_answer="Тьху",
            distractors=(
                InterjectionDistractor(
                    text="Ура",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ура» позначає радість перемоги, що цілком суперечить досаді від власної помилки.",
                    explanation_en="'Ура' denotes joy of victory, entirely contrary to vexation over one's own mistake.",
                ),
                InterjectionDistractor(
                    text="Чудово",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Чудово» є позитивною оцінкою, несумісною з неприємною помилкою.",
                    explanation_en="'Чудово' is a positive assessment incompatible with an annoying mistake.",
                ),
                InterjectionDistractor(
                    text="Тпру",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Тпру» є командою зупинити коней, а не вигуком досади й роздратування.",
                    explanation_en="'Тпру' is a command to halt horses, not an interjection of vexation.",
                ),
            ),
            rule_citation=cit2,
            rule_summary_ua=ua2,
            rule_summary_en=en2,
        )
    )

    # Category 3: Volitional Imperative (5 cards)
    cit3, ua3, en3 = resolve_volitional_imperative_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_11",
            category=InterjectionCategory.VOLITIONAL_IMPERATIVE,
            prompt="«_______, друзі, на річку купатися, поки сонце гріє!» — весело гукнув Тарас.",
            target_token="гайда",
            correct_answer="Гайда",
            distractors=(
                InterjectionDistractor(
                    text="Ой",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ой» виражає емоційний біль чи острах, а «гайда» є закликом до спільного руху.",
                    explanation_en="'Ой' expresses pain or fear, whereas 'гайда' is a call to mutual action.",
                ),
                InterjectionDistractor(
                    text="Тьху",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Тьху» передає огиду або досаду, а не радісний заклик піти купатися.",
                    explanation_en="'Тьху' conveys disgust or vexation, not an eager invitation to go swimming.",
                ),
                InterjectionDistractor(
                    text="Тпру",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Тпру» наказує коням зупинитися, що прямо протилежне заклику вирушати.",
                    explanation_en="'Тпру' orders horses to stop, which is opposite to an urging to set out.",
                ),
            ),
            rule_citation=cit3,
            rule_summary_ua=ua3,
            rule_summary_en=en3,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_12",
            category=InterjectionCategory.VOLITIONAL_IMPERATIVE,
            prompt="«Ану _______ негайно до кімнати вчити невивчені уроки!» — суворо звеліла мати.",
            target_token="марш",
            correct_answer="марш",
            distractors=(
                InterjectionDistractor(
                    text="леле",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Леле» виражає подив або тривогу, а не рішучу вимогу йти робити уроки.",
                    explanation_en="'Леле' expresses surprise or worry, not a decisive command to go study.",
                ),
                InterjectionDistractor(
                    text="дякую",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Дякую» є формулою подяки й не сполучається з наказовою часткою «ану».",
                    explanation_en="'Дякую' is an expression of gratitude and does not combine with imperative 'ану'.",
                ),
                InterjectionDistractor(
                    text="киць-киць",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киць-киць» слугує для підкликання котів, а не для наказу дитині.",
                    explanation_en="'Киць-киць' is used to call cats, not to command a child.",
                ),
            ),
            rule_citation=cit3,
            rule_summary_ua=ua3,
            rule_summary_en=en3,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_13",
            category=InterjectionCategory.VOLITIONAL_IMPERATIVE,
            prompt="«_______ вже марно сумувати за минулим, час діяти!» — підбадьорив товариша Андрій.",
            target_token="годі",
            correct_answer="Годі",
            distractors=(
                InterjectionDistractor(
                    text="Ура",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ура» є вигуком радості й не виражає спонукання припинити марний сум.",
                    explanation_en="'Ура' is a cry of joy and does not express an urging to cease vain grief.",
                ),
                InterjectionDistractor(
                    text="Ах",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ах» передає зітхання й розчулення, а не рішучу вимогу облишити сумніви.",
                    explanation_en="'Ах' conveys a sigh, not a resolute imperative to stop doubting.",
                ),
                InterjectionDistractor(
                    text="Киш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киш» є вигуком для відгону птахів, а не спонуканням людини припинити сумувати.",
                    explanation_en="'Киш' is used to shoo birds away, not an urging for a person to stop sorrowing.",
                ),
            ),
            rule_citation=cit3,
            rule_summary_ua=ua3,
            rule_summary_en=en3,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_14",
            category=InterjectionCategory.VOLITIONAL_IMPERATIVE,
            prompt="«_______ звідси, тривожні сумніви й лячні думки!» — подумки наказав собі юнак.",
            target_token="геть",
            correct_answer="Геть",
            distractors=(
                InterjectionDistractor(
                    text="Будь ласка",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Будь ласка» є ввічливим проханням, а не рішучим наказом прогнати лихі думки.",
                    explanation_en="'Будь ласка' is a polite request, not a resolute command to banish bad thoughts.",
                ),
                InterjectionDistractor(
                    text="Чудово",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Чудово» виражає схвалення, а «геть» рішуче проганяє небажане.",
                    explanation_en="'Чудово' expresses approval, whereas 'геть' decisively expels the unwanted.",
                ),
                InterjectionDistractor(
                    text="Киць-киць",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киць-киць» приваблює котів, а не проганяє страхи й сумніви.",
                    explanation_en="'Киць-киць' attracts cats, rather than banishing fears and doubts.",
                ),
            ),
            rule_citation=cit3,
            rule_summary_ua=ua3,
            rule_summary_en=en3,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_15",
            category=InterjectionCategory.VOLITIONAL_IMPERATIVE,
            prompt="«_______, діти, заспокойтеся і не порушуйте тиші в читальній залі!» — попросила бібліотекарка.",
            target_token="цить",
            correct_answer="Цить",
            distractors=(
                InterjectionDistractor(
                    text="Ура",
                    interference_key=InterjectionInterferenceKey.INCORRECT_EMOTIONAL_TONE,
                    explanation_ua="«Ура» є гучним криком радості, що лише посилює шум замість вимоги тиші.",
                    explanation_en="'Ура' is a loud cheer of joy that increases noise instead of asking for silence.",
                ),
                InterjectionDistractor(
                    text="Гайда",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Гайда» закликає бігти кудись разом, а не поводитися тихо в читальній залі.",
                    explanation_en="'Гайда' urges running somewhere together, not being quiet in a reading room.",
                ),
                InterjectionDistractor(
                    text="Вйо",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Вйо» вигукують візники для прискорення коней, а не для тиші серед людей.",
                    explanation_en="'Вйо' is shouted by coachmen to speed up horses, not to request silence.",
                ),
            ),
            rule_citation=cit3,
            rule_summary_ua=ua3,
            rule_summary_en=en3,
        )
    )

    # Category 4: Volitional Animal (5 cards)
    cit4, ua4, en4 = resolve_volitional_animal_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_16",
            category=InterjectionCategory.VOLITIONAL_ANIMAL,
            prompt="«_______, маленьке пухнасте кошеня, біжи скоріше куштувати тепле молоко!» — покликала Оленка.",
            target_token="киць-киць",
            correct_answer="Киць-киць",
            distractors=(
                InterjectionDistractor(
                    text="Тпру",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Тпру» наказує коню зупинитися, а не підкликає котів.",
                    explanation_en="'Тпру' commands a horse to halt, not calls a kitten.",
                ),
                InterjectionDistractor(
                    text="Киш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киш» відганяє птахів і свійську птицю, а не запрошує кошеня підійти.",
                    explanation_en="'Киш' shoos birds away, rather than inviting a kitten to approach.",
                ),
                InterjectionDistractor(
                    text="Но",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Но» слугує для поганяння коней або волів у дорогу.",
                    explanation_en="'Но' is used to urge horses or oxen forward.",
                ),
            ),
            rule_citation=cit4,
            rule_summary_ua=ua4,
            rule_summary_en=en4,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_17",
            category=InterjectionCategory.VOLITIONAL_ANIMAL,
            prompt="«_______, настирливі горобці, не чіпайте стиглу солодку черешню!» — замахнувся на птахів садівник.",
            target_token="киш",
            correct_answer="Киш",
            distractors=(
                InterjectionDistractor(
                    text="Киць-киць",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киць-киць» підкликає кота, а не проганяє птахів із фруктового дерева.",
                    explanation_en="'Киць-киць' calls a cat, rather than driving birds away from a fruit tree.",
                ),
                InterjectionDistractor(
                    text="Тпру",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Тпру» вживається лише для зупинки коней.",
                    explanation_en="'Тпру' is used exclusively to stop horses.",
                ),
                InterjectionDistractor(
                    text="Вйо",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Вйо» наказує коням рушати або прискорюватися, а не відганяє горобців.",
                    explanation_en="'Вйо' urges horses to move or accelerate, not shoos sparrows away.",
                ),
            ),
            rule_citation=cit4,
            rule_summary_ua=ua4,
            rule_summary_en=en4,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_18",
            category=InterjectionCategory.VOLITIONAL_ANIMAL,
            prompt="«_______, гнідий коню, постій трохи біля прохолодної криниці!» — тихо скомандував візник.",
            target_token="тпру",
            correct_answer="Тпру",
            distractors=(
                InterjectionDistractor(
                    text="Киш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киш» відганяє птахів і не вживається для зупинки коня.",
                    explanation_en="'Киш' shoos birds and is not used to halt a horse.",
                ),
                InterjectionDistractor(
                    text="Киць-киць",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киць-киць» є вигуком підкликання котів, а не наказом постою для коня.",
                    explanation_en="'Киць-киць' is a call for cats, not a halt command for a horse.",
                ),
                InterjectionDistractor(
                    text="Агов",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Агов» слугує для привертання уваги людини, а не для зупинки упряжі.",
                    explanation_en="'Агов' attracts human attention, not halts a carriage horse.",
                ),
            ),
            rule_citation=cit4,
            rule_summary_ua=ua4,
            rule_summary_en=en4,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_19",
            category=InterjectionCategory.VOLITIONAL_ANIMAL,
            prompt="«_______, сивий конику, рушаймо хутчіше, бо вже насувається дощова хмара!» — гукнув селянин.",
            target_token="но",
            correct_answer="Но",
            distractors=(
                InterjectionDistractor(
                    text="Тпру",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Тпру» наказує коневі стати, тоді як мовець спонукає його їхати швидше.",
                    explanation_en="'Тпру' commands a horse to halt, while the speaker urges it to hasten.",
                ),
                InterjectionDistractor(
                    text="Киш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киш» відганяє птахів від городу чи саду.",
                    explanation_en="'Киш' drives birds away from gardens or orchards.",
                ),
                InterjectionDistractor(
                    text="Цить",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Цить» вимагає мовчання від людей, а не спрямовує коня в рух.",
                    explanation_en="'Цить' demands silence from people, rather than urging a horse into motion.",
                ),
            ),
            rule_citation=cit4,
            rule_summary_ua=ua4,
            rule_summary_en=en4,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_20",
            category=InterjectionCategory.VOLITIONAL_ANIMAL,
            prompt="«_______, гей, мої вірні коні, вивезіть воза на круту гору!» — підбадьорив упряж чумак.",
            target_token="вйо",
            correct_answer="Вйо",
            distractors=(
                InterjectionDistractor(
                    text="Киць-киць",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киць-киць» підкликає кошенят, а не заохочує упряж долати крутий підйом.",
                    explanation_en="'Киць-киць' calls kittens, not encourages draft horses on a steep slope.",
                ),
                InterjectionDistractor(
                    text="Тпру",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Тпру» зупиняє рух, що завадило б витягнути воза на гору.",
                    explanation_en="'Тпру' stops movement, preventing hauling the cart up the hill.",
                ),
                InterjectionDistractor(
                    text="Киш",
                    interference_key=InterjectionInterferenceKey.INCORRECT_VOLITIONAL_COMMAND,
                    explanation_ua="«Киш» відлякує птахів і не керує кінською тягловою силою.",
                    explanation_en="'Киш' scares birds and cannot control equine draught power.",
                ),
            ),
            rule_citation=cit4,
            rule_summary_ua=ua4,
            rule_summary_en=en4,
        )
    )

    # Category 5: Etiquette Greeting & Farewell (5 cards)
    cit5, ua5, en5 = resolve_etiquette_greeting_farewell_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_21",
            category=InterjectionCategory.ETIQUETTE_GREETING_FAREWELL,
            prompt="«_______, вельмишановні колеги, раді бачити вас на нашій щорічній конференції!» — розпочав доповідь декан.",
            target_token="добрий день",
            correct_answer="Добрий день",
            distractors=(
                InterjectionDistractor(
                    text="Добрийдень",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Етикетне вітання «добрий день» пишеться строго окремо per § 41, п. 2.",
                    explanation_en="Etiquette greeting 'добрий день' is spelled strictly separately per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="Добрий-день",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Дефіс у виразі «добрий день» є грубою орфографічною помилкою; слова пишуться окремо.",
                    explanation_en="Hyphen in 'добрий день' is an orthographic error; words are written separately.",
                ),
                InterjectionDistractor(
                    text="Здрастє",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Здрастє» є спотвореним суржиковим просторіччям; українською вітаються «добрий день».",
                    explanation_en="'Здрастє' is corrupted Surzhyk vernacular; standard Ukrainian greeting is 'добрий день'.",
                ),
            ),
            rule_citation=cit5,
            rule_summary_ua=ua5,
            rule_summary_en=en5,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_22",
            category=InterjectionCategory.ETIQUETTE_GREETING_FAREWELL,
            prompt="«_______, дорогі друзі, щиро запрошуємо вас до нашого затишного святкового столу!» — привітала господарка.",
            target_token="добрий вечір",
            correct_answer="Добрий вечір",
            distractors=(
                InterjectionDistractor(
                    text="Добрийвечір",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Формула ввічливого привітання «добрий вечір» складається з двох слів і пишеться окремо per § 41, п. 2.",
                    explanation_en="Polite greeting formula 'добрий вечір' consists of two words and is spelled separately per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="Добрий-вечір",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Написання «добрий вечір» через дефіс суперечить правилам українського правопису.",
                    explanation_en="Hyphenated spelling of 'добрий вечір' contradicts Ukrainian orthographic rules.",
                ),
                InterjectionDistractor(
                    text="Добрий ночі",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Форма «добрий ночі» граматично неузгоджена; для вітання ввечері кажуть «добрий вечір».",
                    explanation_en="The form 'добрий ночі' is ungrammatical; standard evening greeting is 'добрий вечір'.",
                ),
            ),
            rule_citation=cit5,
            rule_summary_ua=ua5,
            rule_summary_en=en5,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_23",
            category=InterjectionCategory.ETIQUETTE_GREETING_FAREWELL,
            prompt="«_______, дорогі друзі, щиро зичимо успіхів і сподіваємося на нові приємні зустрічі!» — тепло попрощався вчитель.",
            target_token="до побачення",
            correct_answer="До побачення",
            distractors=(
                InterjectionDistractor(
                    text="Допобачення",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Етикетний зворот «до побачення» пишеться строго окремо per § 41, п. 2.",
                    explanation_en="Etiquette formula 'до побачення' is spelled strictly separately per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="До-побачення",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Написання виразу «до побачення» через дефіс є поширеною помилкою; пишеться окремо.",
                    explanation_en="Hyphenated 'до-побачення' is an error; it must be written as two separate words.",
                ),
                InterjectionDistractor(
                    text="Да пабачення",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Да пабачення» є фонетичною калькою російського акання й неприпустиме в літературній мові.",
                    explanation_en="'Да пабачення' is an illicit phonetic calque of Russian 'akanye' in literary Ukrainian.",
                ),
            ),
            rule_citation=cit5,
            rule_summary_ua=ua5,
            rule_summary_en=en5,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_24",
            category=InterjectionCategory.ETIQUETTE_GREETING_FAREWELL,
            prompt="«_______, міцного й безтурботного вам сну до самого світанку!» — лагідно побажала мама дітям.",
            target_token="на добраніч",
            correct_answer="На добраніч",
            distractors=(
                InterjectionDistractor(
                    text="Надобраніч",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Етикетне побажання спокійного сну «на добраніч» пишеться строго окремо per § 41, п. 2.",
                    explanation_en="Etiquette wish for good night 'на добраніч' is spelled strictly separately per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="На-добраніч",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Написання «на-добраніч» через дефіс помилкове; в українській мові слова пишуться окремо.",
                    explanation_en="Hyphenated 'на-добраніч' is incorrect; words are written separately in Ukrainian.",
                ),
                InterjectionDistractor(
                    text="Спокойної ночі",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Спокойної ночі» є калькою з російської («спокойной ночи»); нормативні українські вислови — «на добраніч», «добраніч».",
                    explanation_en="'Спокойної ночі' is a calque of Russian 'спокойной ночи'; normative Ukrainian is 'на добраніч'.",
                ),
            ),
            rule_citation=cit5,
            rule_summary_ua=ua5,
            rule_summary_en=en5,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_25",
            category=InterjectionCategory.ETIQUETTE_GREETING_FAREWELL,
            prompt="«_______ здорові, любі сусіди, щасливої вам дороги та легкої мандрівки!» — махнув рукою господар.",
            target_token="бувайте",
            correct_answer="Бувайте",
            distractors=(
                InterjectionDistractor(
                    text="Пака",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Пака» є російським жаргонним словом; літературна українська форма прощання — «бувайте».",
                    explanation_en="'Пака' is a Russian slang calque; normative Ukrainian farewell is 'бувайте'.",
                ),
                InterjectionDistractor(
                    text="Бувайтє",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Бувайтє» містить чуже для української дієслівної парадигми пом'якшення кінцевого «те».",
                    explanation_en="'Бувайтє' shows an illicit Russianized softening of final 'те' in standard Ukrainian.",
                ),
                InterjectionDistractor(
                    text="Бувайте-бо",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Етикетна формула прощання «бувайте» у сполученні зі звертанням не приєднує частку -бо.",
                    explanation_en="Farewell formula 'бувайте' combined with address does not take enclitic particle -бо.",
                ),
            ),
            rule_citation=cit5,
            rule_summary_ua=ua5,
            rule_summary_en=en5,
        )
    )

    # Category 6: Etiquette Gratitude & Apology (5 cards)
    cit6, ua6, en6 = resolve_etiquette_gratitude_apology_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_26",
            category=InterjectionCategory.ETIQUETTE_GRATITUDE_APOLOGY,
            prompt="«Допоможіть мені, _______, підняти цю важку валізу на верхню полицю поїзда!» — звернулася пасажирка.",
            target_token="будь ласка",
            correct_answer="будь ласка",
            distractors=(
                InterjectionDistractor(
                    text="будь-ласка",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Етикетний зворот ввічливості «будь ласка» пишеться строго окремо без дефіса per § 41, п. 2.",
                    explanation_en="Etiquette polite phrase 'будь ласка' is spelled strictly separately without hyphen per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="будьласка",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Написання «будьласка» разом є грубою орфографічною помилкою; слова пишуться окремо.",
                    explanation_en="Spelling 'будьласка' as a single fused word is an orthographic error; write separately.",
                ),
                InterjectionDistractor(
                    text="пожалуста",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Пожалуста» є суржиковим спотворенням російського «пожалуйста»; нормативна форма — «будь ласка».",
                    explanation_en="'Пожалуста' is a Surzhyk corruption of Russian 'пожалуйста'; standard form is 'будь ласка'.",
                ),
            ),
            rule_citation=cit6,
            rule_summary_ua=ua6,
            rule_summary_en=en6,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_27",
            category=InterjectionCategory.ETIQUETTE_GRATITUDE_APOLOGY,
            prompt="«Щиро _______ вам за мудру пораду та своєчасну підтримку в біді!» — сказав вдячний юнак.",
            target_token="дякую",
            correct_answer="дякую",
            distractors=(
                InterjectionDistractor(
                    text="спасібо",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Спасібо» є ненормативним суржикізмом; в українській літературній мові вживається «дякую».",
                    explanation_en="'Спасібо' is non-standard Surzhyk; standard literary Ukrainian requires 'дякую'.",
                ),
                InterjectionDistractor(
                    text="благодарю",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Благодарю» є застарілим калькованим канцеляризмом із російської; нормативна форма — «дякую».",
                    explanation_en="'Благодарю' is a calqued clericalism from Russian; normative Ukrainian expression is 'дякую'.",
                ),
                InterjectionDistractor(
                    text="дякуюю",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Подвоєння кінцевого «ю» є орфографічною помилкою; нормативна форма — «дякую».",
                    explanation_en="Doubled final 'ю' is an orthographic error; normative form is 'дякую'.",
                ),
            ),
            rule_citation=cit6,
            rule_summary_ua=ua6,
            rule_summary_en=en6,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_28",
            category=InterjectionCategory.ETIQUETTE_GRATITUDE_APOLOGY,
            prompt="«_______, я ненавмисно зачепив вашу парасольку біля виходу з вагону!» — вибачився перехожий.",
            target_token="пробачте",
            correct_answer="Пробачте",
            distractors=(
                InterjectionDistractor(
                    text="Ізвінітє",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Ізвінітє» є грубим суржикізмом із російської («извините»); нормативна українська форма — «пробачте».",
                    explanation_en="'Ізвінітє' is an illicit Surzhyk calque from Russian 'извините'; normative Ukrainian is 'пробачте'.",
                ),
                InterjectionDistractor(
                    text="Пробачтє",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="Пом'якшення кінцевого «те» в наказовому способі («пробачтє») є фонетичною помилкою.",
                    explanation_en="Softening the final 'те' in the imperative ('пробачтє') is an orthographic and phonetic error.",
                ),
                InterjectionDistractor(
                    text="Пробач-те",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Дефіс усередині дієслівної форми наказового способу неприпустимий; пишеться «пробачте».",
                    explanation_en="A hyphen inside an imperative verbal form is illicit; write 'пробачте' as one word.",
                ),
            ),
            rule_citation=cit6,
            rule_summary_ua=ua6,
            rule_summary_en=en6,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_29",
            category=InterjectionCategory.ETIQUETTE_GRATITUDE_APOLOGY,
            prompt="«_______, котра зараз година, бо мій наручний годинник раптово зупинився?» — чемно поцікавився дідусь.",
            target_token="перепрошую",
            correct_answer="Перепрошую",
            distractors=(
                InterjectionDistractor(
                    text="Ізвиняюсь",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Ізвиняюсь» є ненормативним суржикізмом; ввічлива українська форма звертання — «перепрошую».",
                    explanation_en="'Ізвиняюсь' is non-standard Surzhyk; polite Ukrainian formula of address is 'перепрошую'.",
                ),
                InterjectionDistractor(
                    text="Пере-прошую",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Префікс пере- в дієсловах і вигукових формулах пишеться разом, без дефіса.",
                    explanation_en="Prefix пере- in verbs and etiquette formulas is written fused without hyphen.",
                ),
                InterjectionDistractor(
                    text="Перепрашую",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Форма з літерою «а» в корені є помилковою; нормативний корінь — «-прош-» («перепрошую»).",
                    explanation_en="The form with 'а' in the root is an error; normative root is '-прош-' ('перепрошую').",
                ),
            ),
            rule_citation=cit6,
            rule_summary_ua=ua6,
            rule_summary_en=en6,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_30",
            category=InterjectionCategory.ETIQUETTE_GRATITUDE_APOLOGY,
            prompt="«_______, ви не підкажете, де розташована найближча станція міського метро?» — запитав гість міста.",
            target_token="вибачте",
            correct_answer="Вибачте",
            distractors=(
                InterjectionDistractor(
                    text="Ізвінітє",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Ізвінітє» є суржиковим запозиченням; літературна форма ввічливого звертання — «вибачте».",
                    explanation_en="'Ізвінітє' is an illicit Surzhyk borrowing; standard literary expression is 'вибачте'.",
                ),
                InterjectionDistractor(
                    text="Вибачтє",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="Пом'якшення кінцевого складу («тє») порушує орфоепічні та граматичні норми української мови.",
                    explanation_en="Softening the final syllable ('-тє') violates Ukrainian orthoepic and grammatical norms.",
                ),
                InterjectionDistractor(
                    text="Вибач-те",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Написання вигукової дієслівної форми через дефіс є орфографічною помилкою.",
                    explanation_en="Hyphenating an imperative verbal interjection is an orthographic error.",
                ),
            ),
            rule_citation=cit6,
            rule_summary_ua=ua6,
            rule_summary_en=en6,
        )
    )

    # Category 7: Onomatopoeia Nature & Mechanics (5 cards)
    cit7, ua7, en7 = resolve_onomatopoeia_nature_mechanics_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_31",
            category=InterjectionCategory.ONOMATOPOEIA_NATURE_MECHANICS,
            prompt="«_______!» — весело й лунко задзвонив срібний шкільний дзвоник, скликаючи учнів на перший урок.",
            target_token="дзень-дзелень",
            correct_answer="Дзень-дзелень",
            distractors=(
                InterjectionDistractor(
                    text="Дзеньдзелень",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування передзвону дзвоника «дзень-дзелень» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Bell-ringing onomatopoeia 'дзень-дзелень' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Дзень дзелень",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Написання окремо для парного звуконаслідування помилкове; частини поєднуються дефісом.",
                    explanation_en="Writing paired onomatopoeia separately is incorrect; parts are connected by hyphen.",
                ),
                InterjectionDistractor(
                    text="Дзень-делень",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Втрата африкати дз («делень» замість «дзелень») спотворює дзвінку вимову звуконаслідування.",
                    explanation_en="Loss of affricate дз ('делень' instead of 'дзелень') corrupts onomatopoeic phonetics.",
                ),
            ),
            rule_citation=cit7,
            rule_summary_ua=ua7,
            rule_summary_en=en7,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_32",
            category=InterjectionCategory.ONOMATOPOEIA_NATURE_MECHANICS,
            prompt="«_______» — монотонно й розмірено відраховував кожну хвилину старовинний настінний годинник.",
            target_token="тік-так",
            correct_answer="Тік-так",
            distractors=(
                InterjectionDistractor(
                    text="Тіктак",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування цокання годинника «тік-так» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Clock-ticking onomatopoeia 'тік-так' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Тік так",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Роздільне написання «тік так» суперечить правилу дефісного оформлення звуконаслідувань.",
                    explanation_en="Separate spelling 'тік так' contradicts the rule requiring hyphenated onomatopoeia.",
                ),
                InterjectionDistractor(
                    text="Тик-так",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="Написання з літерою «и» є калькою з російської мови; в українській нормі вживається «тік-так».",
                    explanation_en="Spelling with 'и' is a Russian calque; standard Ukrainian onomatopoeia is 'тік-так'.",
                ),
            ),
            rule_citation=cit7,
            rule_summary_ua=ua7,
            rule_summary_en=en7,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_33",
            category=InterjectionCategory.ONOMATOPOEIA_NATURE_MECHANICS,
            prompt="«_______» — тихо падали на весняне підвіконня перші прозорі краплі травневого дощу.",
            target_token="крап-крап",
            correct_answer="Крап-крап",
            distractors=(
                InterjectionDistractor(
                    text="Крапкрап",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Повторювані звуконаслідувальні слова «крап-крап» пишуться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Repeated onomatopoeic elements 'крап-крап' are hyphenated per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Крап крап",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Написання частин повтору окремо є помилкою; повтори звуків з'єднуються дефісом.",
                    explanation_en="Writing parts of repetition separately is an error; sound repetitions are hyphenated.",
                ),
                InterjectionDistractor(
                    text="Буль-буль",
                    interference_key=InterjectionInterferenceKey.INCORRECT_SOUND_SOURCE,
                    explanation_ua="«Буль-буль» імітує булькання води або рідини, тоді як падіння перших дощових крапель на підвіконня передає «крап-крап».",
                    explanation_en="'Буль-буль' imitates bubbling liquid, whereas raindrops falling on a windowsill are described by 'крап-крап'.",
                ),
            ),
            rule_citation=cit7,
            rule_summary_ua=ua7,
            rule_summary_en=en7,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_34",
            category=InterjectionCategory.ONOMATOPOEIA_NATURE_MECHANICS,
            prompt="«_______» — м'яко хлюпали прохолодні річкові хвилі об дерев'яний борт старого рибальського човна.",
            target_token="хлюп-хлюп",
            correct_answer="Хлюп-хлюп",
            distractors=(
                InterjectionDistractor(
                    text="Хлюпхлюп",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування плескоту хвиль «хлюп-хлюп» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Wave-splashing onomatopoeia 'хлюп-хлюп' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Хлюп хлюп",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Окреме написання повторюваних елементів звуконаслідування суперечить правопису.",
                    explanation_en="Separate spelling of repeated onomatopoeic elements contradicts orthography.",
                ),
                InterjectionDistractor(
                    text="Плюх-плюх",
                    interference_key=InterjectionInterferenceKey.INCORRECT_SOUND_SOURCE,
                    explanation_ua="«Плюх-плюх» імітує падіння важкого предмета у воду, а лагідні хвилі роблять «хлюп-хлюп».",
                    explanation_en="'Плюх-плюх' imitates a heavy object falling into water, whereas gentle waves go 'хлюп-хлюп'.",
                ),
            ),
            rule_citation=cit7,
            rule_summary_ua=ua7,
            rule_summary_en=en7,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_35",
            category=InterjectionCategory.ONOMATOPOEIA_NATURE_MECHANICS,
            prompt="«_______» — лунко вистукували підковані копита коня по кам'яній старій міській бруківці.",
            target_token="цок-цок",
            correct_answer="Цок-цок",
            distractors=(
                InterjectionDistractor(
                    text="Цокцок",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування стукоту копит «цок-цок» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Hoof-clattering onomatopoeia 'цок-цок' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Цок цок",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Окреме написання повторюваного звуку копит є орфографічною помилкою.",
                    explanation_en="Writing the repeated hoof sound separately is an orthographic error.",
                ),
                InterjectionDistractor(
                    text="Чок-чок",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="Форма «чок-чок» є російським звуконаслідуванням; українською копитом цокають «цок-цок».",
                    explanation_en="The form 'чок-чок' is a Russianism; standard Ukrainian onomatopoeia is 'цок-цок'.",
                ),
            ),
            rule_citation=cit7,
            rule_summary_ua=ua7,
            rule_summary_en=en7,
        )
    )

    # Category 8: Onomatopoeia Animal Sounds (5 cards)
    cit8, ua8, en8 = resolve_onomatopoeia_animal_sounds_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_36",
            category=InterjectionCategory.ONOMATOPOEIA_ANIMAL_SOUNDS,
            prompt="«_______!» — дзвінко й радісно загавкало маленьке цуценя, побачивши господаря біля воріт.",
            target_token="гав-гав",
            correct_answer="Гав-гав",
            distractors=(
                InterjectionDistractor(
                    text="Гавгав",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування гавкоту собаки «гав-гав» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Dog barking onomatopoeia 'гав-гав' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Гав гав",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Роздільне написання «гав гав» суперечить нормі дефісного поєднання повторів.",
                    explanation_en="Separate writing 'гав гав' violates the rule requiring hyphenated sound repetitions.",
                ),
                InterjectionDistractor(
                    text="Тяв-тяв",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Тяв-тяв» є калькою з російської мови; питомий український вигук гавкоту — «гав-гав».",
                    explanation_en="'Тяв-тяв' is a calque from Russian; authentic Ukrainian dog barking is 'гав-гав'.",
                ),
            ),
            rule_citation=cit8,
            rule_summary_ua=ua8,
            rule_summary_en=en8,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_37",
            category=InterjectionCategory.ONOMATOPOEIA_ANIMAL_SOUNDS,
            prompt="«_______!» — жалібно й тоненько просило їсти руде пухнасте кошеня біля кухонних дверей.",
            target_token="няв-няв",
            correct_answer="Няв-няв",
            distractors=(
                InterjectionDistractor(
                    text="Нявняв",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування нявкання кота «няв-няв» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Cat meowing onomatopoeia 'няв-няв' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Няв няв",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Окреме написання повторюваного звуку нявчання суперечить правилам правопису.",
                    explanation_en="Separate writing of repeated meowing sound contradicts orthographic rules.",
                ),
                InterjectionDistractor(
                    text="Мяу-мяу",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Мяу-мяу» є калькою з російської орфографії; українська нормативна форма — «няв-няв».",
                    explanation_en="'Мяу-мяу' is an orthographic calque of Russian; standard Ukrainian form is 'няв-няв'.",
                ),
            ),
            rule_citation=cit8,
            rule_summary_ua=ua8,
            rule_summary_en=en8,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_38",
            category=InterjectionCategory.ONOMATOPOEIA_ANIMAL_SOUNDS,
            prompt="«_______!» — раз по раз лунало в зеленому березовому гаю, де кувала невтомна зозуля.",
            target_token="ку-ку",
            correct_answer="Ку-ку",
            distractors=(
                InterjectionDistractor(
                    text="Куку",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування кування зозулі «ку-ку» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Cuckoo call onomatopoeia 'ку-ку' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Ку ку",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Окреме написання повтору звуків «ку ку» є орфографічною помилкою.",
                    explanation_en="Writing sound repetitions 'ку ку' separately is an orthographic error.",
                ),
                InterjectionDistractor(
                    text="Кар-кар",
                    interference_key=InterjectionInterferenceKey.INCORRECT_SOUND_SOURCE,
                    explanation_ua="«Кар-кар» видає ворона, а зозуля кує «ку-ку».",
                    explanation_en="'Кар-кар' is produced by a crow, whereas a cuckoo calls 'ку-ку'.",
                ),
            ),
            rule_citation=cit8,
            rule_summary_ua=ua8,
            rule_summary_en=en8,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_39",
            category=InterjectionCategory.ONOMATOPOEIA_ANIMAL_SOUNDS,
            prompt="«_______!» — хрипко прокричала стара чорна ворона, сівши на верхівку високої сухої сосни.",
            target_token="кар-кар",
            correct_answer="Кар-кар",
            distractors=(
                InterjectionDistractor(
                    text="Каркар",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування каркання ворони «кар-кар» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Crow cawing onomatopoeia 'кар-кар' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Кар кар",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Роздільне написання «кар кар» є помилковим; повтори звуків з'єднуються дефісом.",
                    explanation_en="Separate spelling 'кар кар' is an error; sound repetitions are connected with a hyphen.",
                ),
                InterjectionDistractor(
                    text="Ква-ква",
                    interference_key=InterjectionInterferenceKey.INCORRECT_SOUND_SOURCE,
                    explanation_ua="«Ква-ква» кумкають жаби на болоті, а ворона каркає «кар-кар».",
                    explanation_en="'Ква-ква' is croaked by frogs, whereas a crow caws 'кар-кар'.",
                ),
            ),
            rule_citation=cit8,
            rule_summary_ua=ua8,
            rule_summary_en=en8,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_40",
            category=InterjectionCategory.ONOMATOPOEIA_ANIMAL_SOUNDS,
            prompt="«_______!» — дружно й голосно озивалися зелені жаби у прибережному очереті тихого ставка.",
            target_token="ква-ква",
            correct_answer="Ква-ква",
            distractors=(
                InterjectionDistractor(
                    text="Кваква",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування кумкання жаб «ква-ква» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Frog croaking onomatopoeia 'ква-ква' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Ква ква",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Роздільне написання повторюваного звуку «ква ква» суперечить нормі дефісного написання.",
                    explanation_en="Separate writing of repeated sound 'ква ква' violates the hyphenation rule.",
                ),
                InterjectionDistractor(
                    text="Гав-гав",
                    interference_key=InterjectionInterferenceKey.INCORRECT_SOUND_SOURCE,
                    explanation_ua="«Гав-гав» гавкає собака, а жаби в очереті кумкають «ква-ква».",
                    explanation_en="'Гав-гав' is the bark of a dog, whereas frogs in reeds croak 'ква-ква'.",
                ),
            ),
            rule_citation=cit8,
            rule_summary_ua=ua8,
            rule_summary_en=en8,
        )
    )

    # Category 9: Spelling Hyphen Repeated (5 cards)
    cit9, ua9, en9 = resolve_spelling_hyphen_repeated_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_41",
            category=InterjectionCategory.SPELLING_HYPHEN_REPEATED,
            prompt="«_______, як же тепер виправити цю прикру прикрість!» — розгублено схопився за голову студент.",
            target_token="ой-ой-ой",
            correct_answer="Ой-ой-ой",
            distractors=(
                InterjectionDistractor(
                    text="Ойойой",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Повторюваний вигук розгубленості й жалю «ой-ой-ой» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Repeated interjection of perplexity 'ой-ой-ой' is hyphenated per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Ой ой ой",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Написання вигукового повтору трьома окремими словами є помилкою; пишеться через дефіс.",
                    explanation_en="Writing the repeated interjection as three separate words is an error; write with hyphens.",
                ),
                InterjectionDistractor(
                    text="Ой-ойой",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Усі повторювані компоненти вигуку повинні з'єднуватися дефісами: «ой-ой-ой».",
                    explanation_en="All repeated components of the interjection must be linked with hyphens: 'ой-ой-ой'.",
                ),
            ),
            rule_citation=cit9,
            rule_summary_ua=ua9,
            rule_summary_en=en9,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_42",
            category=InterjectionCategory.SPELLING_HYPHEN_REPEATED,
            prompt="«_______!» — дружно й розкотисто розсміялися всі глядачі у глядацькій залі після вдалого жарту.",
            target_token="ха-ха-ха",
            correct_answer="Ха-ха-ха",
            distractors=(
                InterjectionDistractor(
                    text="Хахаха",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування сміху «ха-ха-ха» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Laughter onomatopoeia 'ха-ха-ха' is spelled with hyphens per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Ха ха ха",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Роздільне написання сміху як окремих слів суперечить нормам українського правопису.",
                    explanation_en="Separate writing of laughter as discrete words contradicts Ukrainian orthography.",
                ),
                InterjectionDistractor(
                    text="Ха-хаха",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Кожен склад сміху у звуконаслідуванні відокремлюється дефісом: «ха-ха-ха».",
                    explanation_en="Each syllable of laughter in the onomatopoeia is separated by a hyphen: 'ха-ха-ха'.",
                ),
            ),
            rule_citation=cit9,
            rule_summary_ua=ua9,
            rule_summary_en=en9,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_43",
            category=InterjectionCategory.SPELLING_HYPHEN_REPEATED,
            prompt="«_______, як не соромно кривдити меншого товариша!» — докірливо похитала головою вчителька.",
            target_token="ай-яй-яй",
            correct_answer="Ай-яй-яй",
            distractors=(
                InterjectionDistractor(
                    text="Айяйяй",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Вигук докору та осуду «ай-яй-яй» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Interjection of reproach 'ай-яй-яй' is spelled with hyphens per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Ай яй яй",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Окреме написання частин вигуку «ай яй яй» є грубою орфографічною помилкою.",
                    explanation_en="Separate spelling of interjection parts 'ай яй яй' is an orthographic error.",
                ),
                InterjectionDistractor(
                    text="Ой-яй-яй",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Нормативна форма вигуку докору має перший склад «ай-»: «ай-яй-яй».",
                    explanation_en="Normative form of reproach interjection begins with 'ай-': 'ай-яй-яй'.",
                ),
            ),
            rule_citation=cit9,
            rule_summary_ua=ua9,
            rule_summary_en=en9,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_44",
            category=InterjectionCategory.SPELLING_HYPHEN_REPEATED,
            prompt="«_______!» — мелодійно й дзвінко відгукнувся кришталевий келих від легкого дотику срібної ложечки.",
            target_token="дзень-дзелень",
            correct_answer="Дзень-дзелень",
            distractors=(
                InterjectionDistractor(
                    text="Дзеньдзелень",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Відлунне звуконаслідування кришталевого дзвону «дзень-дзелень» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Echoic crystal clinking onomatopoeia 'дзень-дзелень' is hyphenated per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Дзень дзелень",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Роздільне написання компонентів відлуння без дефіса є порушенням орфографії.",
                    explanation_en="Separate writing of echoic components without hyphen violates orthography.",
                ),
                InterjectionDistractor(
                    text="Дзень-зелень",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Звук дзвінкого дзвону відтворюється африкатою «дз»: «дзень-дзелень», а не «зелень».",
                    explanation_en="The clinking sound is produced with affricate 'дз': 'дзень-дзелень', not 'зелень'.",
                ),
            ),
            rule_citation=cit9,
            rule_summary_ua=ua9,
            rule_summary_en=en9,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_45",
            category=InterjectionCategory.SPELLING_HYPHEN_REPEATED,
            prompt="«_______!» — хтось обережно й тихо постукав у шибку вікна старого сільського будинку.",
            target_token="тук-тук",
            correct_answer="Тук-тук",
            distractors=(
                InterjectionDistractor(
                    text="Туктук",
                    interference_key=InterjectionInterferenceKey.HYPHEN_OMISSION,
                    explanation_ua="Звуконаслідування стуку «тук-тук» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Knocking onomatopoeia 'тук-тук' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Тук тук",
                    interference_key=InterjectionInterferenceKey.HYPHEN_SEPARATION,
                    explanation_ua="Роздільне написання повторюваного звуку стуку суперечить правилу дефісного оформлення.",
                    explanation_en="Writing repeated knocking sounds separately violates the hyphenation rule.",
                ),
                InterjectionDistractor(
                    text="Стук-стук",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="«Стук» є іменником; звуконаслідувальним словом для стукання в двері чи вікно є «тук-тук».",
                    explanation_en="'Стук' is a noun; standard onomatopoeic interjection for knocking is 'тук-тук'.",
                ),
            ),
            rule_citation=cit9,
            rule_summary_ua=ua9,
            rule_summary_en=en9,
        )
    )

    # Category 10: Spelling Particles Hyphen (5 cards)
    cit10, ua10, en10 = resolve_spelling_particles_hyphen_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_46",
            category=InterjectionCategory.SPELLING_PARTICLES_HYPHEN,
            prompt="«_______ сперечатися через порожні дрібниці, берімося краще разом до корисної справи!» — закликав староста.",
            target_token="годі-бо",
            correct_answer="Годі-бо",
            distractors=(
                InterjectionDistractor(
                    text="Годі бо",
                    interference_key=InterjectionInterferenceKey.PARTICLE_HYPHEN_OMISSION,
                    explanation_ua="Вигук із постпозитивною часткою -бо пишеться через дефіс: «годі-бо» per § 44, п. 3, 1).",
                    explanation_en="Interjection with postpositive particle -бо is hyphenated: 'годі-бо' per § 44, p. 3, 1).",
                ),
                InterjectionDistractor(
                    text="Годібо",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Разом вигуки з частками не пишуться; норма вимагає дефіса: «годі-бо».",
                    explanation_en="Interjections with particles are not fused; the rule requires a hyphen: 'годі-бо'.",
                ),
                InterjectionDistractor(
                    text="Годі-то",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="З вигуком припинення дії «годі» нормативно вживається спонукальна частка «-бо» («годі-бо»).",
                    explanation_en="With the cessation interjection 'годі', normative urging particle is '-бо' ('годі-бо').",
                ),
            ),
            rule_citation=cit10,
            rule_summary_ua=ua10,
            rule_summary_en=en10,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_47",
            category=InterjectionCategory.SPELLING_PARTICLES_HYPHEN,
            prompt="«_______, друже, розкажи нам докладніше про свою дивовижну подорож Карпатами!» — попросили однокласники.",
            target_token="ну-бо",
            correct_answer="Ну-бо",
            distractors=(
                InterjectionDistractor(
                    text="Ну бо",
                    interference_key=InterjectionInterferenceKey.PARTICLE_HYPHEN_OMISSION,
                    explanation_ua="Спонукальний вигук із часткою -бо пишеться через дефіс: «ну-бо» per § 44, п. 3, 1).",
                    explanation_en="Imperative interjection with particle -бо is hyphenated: 'ну-бо' per § 44, p. 3, 1).",
                ),
                InterjectionDistractor(
                    text="Нубо",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Злите написання «нубо» є орфографічною помилкою; сполука пишеться через дефіс.",
                    explanation_en="Fused spelling 'нубо' is an orthographic error; the combination is hyphenated.",
                ),
                InterjectionDistractor(
                    text="Ну-ка",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Ну-ка» є російською часткою; в українській літературній мові нормативною є частка «-бо» («ну-бо»).",
                    explanation_en="'Ну-ка' is a Russianism; in literary Ukrainian the normative form is 'ну-бо'.",
                ),
            ),
            rule_citation=cit10,
            rule_summary_ua=ua10,
            rule_summary_en=en10,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_48",
            category=InterjectionCategory.SPELLING_PARTICLES_HYPHEN,
            prompt="«_______ разом заспіваємо цю старовинну народну колядку біля ялинки!» — запропонувала сестра.",
            target_token="давай-но",
            correct_answer="Давай-но",
            distractors=(
                InterjectionDistractor(
                    text="Давай но",
                    interference_key=InterjectionInterferenceKey.PARTICLE_HYPHEN_OMISSION,
                    explanation_ua="Спонукальна форма з підсилювальною часткою -но пишеться через дефіс: «давай-но» per § 44, п. 3, 1).",
                    explanation_en="Urging form with intensifying particle -но is hyphenated: 'давай-но' per § 44, p. 3, 1).",
                ),
                InterjectionDistractor(
                    text="Давайно",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Написання форми «давайно» разом є помилковим; частка -но приєднується дефісом.",
                    explanation_en="Spelling 'давайно' as one word is an error; particle -но is attached by hyphen.",
                ),
                InterjectionDistractor(
                    text="Давай-ка",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="Частка «-ка» є запозиченням із російської; українська норма вимагає частки «-но» («давай-но»).",
                    explanation_en="Particle '-ка' is borrowed from Russian; Ukrainian standard requires '-но' ('давай-но').",
                ),
            ),
            rule_citation=cit10,
            rule_summary_ua=ua10,
            rule_summary_en=en10,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_49",
            category=InterjectionCategory.SPELLING_PARTICLES_HYPHEN,
            prompt="«_______, я кажу вам чистісіньку правду про все побачене на власні очі!» — палко запевняв свідок події.",
            target_token="їй-богу",
            correct_answer="Їй-богу",
            distractors=(
                InterjectionDistractor(
                    text="Їй богу",
                    interference_key=InterjectionInterferenceKey.IDIOM_HYPHEN_OMISSION,
                    explanation_ua="Усталений вигуковий вираз «їй-богу» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Fixed interjection idiom 'їй-богу' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Їйбогу",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Разом вираз «їй-богу» не пишеться; правописна норма закріплює дефісне написання.",
                    explanation_en="Fused spelling of 'їй-богу' is incorrect; orthographic rule prescribes hyphenation.",
                ),
                InterjectionDistractor(
                    text="Ей-богу",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="«Ей-богу» з літерою «е» є російською калькою; українська форма починається на «їй-»: «їй-богу».",
                    explanation_en="'Ей-богу' with letter 'е' is a Russian calque; Ukrainian form is 'їй-богу'.",
                ),
            ),
            rule_citation=cit10,
            rule_summary_ua=ua10,
            rule_summary_en=en10,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_50",
            category=InterjectionCategory.SPELLING_PARTICLES_HYPHEN,
            prompt="«_______, я ніколи й гадки не мав нікого образити своїм щирим зауваженням!» — знітився хлопець.",
            target_token="їй-право",
            correct_answer="Їй-право",
            distractors=(
                InterjectionDistractor(
                    text="Їй право",
                    interference_key=InterjectionInterferenceKey.IDIOM_HYPHEN_OMISSION,
                    explanation_ua="Усталений вигук запевнення «їй-право» пишеться через дефіс per § 35, п. 5, 4).",
                    explanation_en="Fixed interjection of assurance 'їй-право' is spelled with a hyphen per § 35, p. 5, 4).",
                ),
                InterjectionDistractor(
                    text="Їйправо",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Злите написання «їйправо» є орфографічною помилкою; норма вимагає дефіса.",
                    explanation_en="Fused spelling 'їйправо' is an orthographic error; standard requires hyphenation.",
                ),
                InterjectionDistractor(
                    text="Ей-право",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="Форма на «ей-» є калькою з російської мови; український правопис фіксує форму «їй-право».",
                    explanation_en="The form starting with 'ей-' is a Russianism; Ukrainian orthography establishes 'їй-право'.",
                ),
            ),
            rule_citation=cit10,
            rule_summary_ua=ua10,
            rule_summary_en=en10,
        )
    )

    # Category 11: Spelling Multi-word Separate (5 cards)
    cit11, ua11, en11 = resolve_spelling_multiword_separate_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_51",
            category=InterjectionCategory.SPELLING_MULTIWORD_SEPARATE,
            prompt="«Передайте мені, _______, склянку джерельної води!» — ввічливо попросив стомлений подорожній.",
            target_token="будь ласка",
            correct_answer="будь ласка",
            distractors=(
                InterjectionDistractor(
                    text="будь-ласка",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Слова «будь ласка» пишуться строго окремо без дефіса per § 41, п. 2.",
                    explanation_en="Words 'будь ласка' are written strictly separately without hyphen per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="будьласка",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Злите написання «будьласка» є орфографічною помилкою; пишеться окремо.",
                    explanation_en="Fused 'будьласка' is an orthographic error; write as two words.",
                ),
                InterjectionDistractor(
                    text="буть ласка",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Написання з літерою «т» («буть») спотворює основу дієслова «бути» («будь»).",
                    explanation_en="Spelling with 'т' ('буть') corrupts the imperative stem of 'бути' ('будь').",
                ),
            ),
            rule_citation=cit11,
            rule_summary_ua=ua11,
            rule_summary_en=en11,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_52",
            category=InterjectionCategory.SPELLING_MULTIWORD_SEPARATE,
            prompt="«_______, дорогі випускники, нехай ваше життєве майбутнє буде мирним і щасливим!» — сказав директор школи.",
            target_token="до побачення",
            correct_answer="До побачення",
            distractors=(
                InterjectionDistractor(
                    text="Допобачення",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Вираз «до побачення» пишеться окремо per § 41, п. 2.",
                    explanation_en="Phrase 'до побачення' is spelled separately per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="До-побачення",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Дефіс у виразі «до побачення» є помилкою; прийменник «до» з іменником пишуться окремо.",
                    explanation_en="Hyphen in 'до побачення' is an error; preposition 'до' and noun are written separately.",
                ),
                InterjectionDistractor(
                    text="До побаченняя",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Подвоєння кінцевого «я» є орфографічною помилкою; нормативне написання — «до побачення».",
                    explanation_en="Doubled final 'я' is an orthographic error; standard spelling is 'до побачення'.",
                ),
            ),
            rule_citation=cit11,
            rule_summary_ua=ua11,
            rule_summary_en=en11,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_53",
            category=InterjectionCategory.SPELLING_MULTIWORD_SEPARATE,
            prompt="«_______, любі онучата, спіть солодко й набирайтеся сил до нового сонячного ранку!» — мовила лагідна бабуся.",
            target_token="на добраніч",
            correct_answer="На добраніч",
            distractors=(
                InterjectionDistractor(
                    text="Надобраніч",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Формула побажання сну «на добраніч» пишеться виключно окремо per § 41, п. 2.",
                    explanation_en="Good night formula 'на добраніч' is spelled exclusively separately per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="На-добраніч",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Вживання дефіса у вислові «на добраніч» є грубою помилкою; слова пишуться окремо.",
                    explanation_en="Using a hyphen in 'на добраніч' is an error; words are written separately.",
                ),
                InterjectionDistractor(
                    text="Надобранічь",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="В українській мові після шиплячих кінцевий м'який знак не пишеться: «ніч», а не «нічь».",
                    explanation_en="In Ukrainian, soft sign is not written after sibilants: 'ніч', not 'нічь'.",
                ),
            ),
            rule_citation=cit11,
            rule_summary_ua=ua11,
            rule_summary_en=en11,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_54",
            category=InterjectionCategory.SPELLING_MULTIWORD_SEPARATE,
            prompt="«_______, як же несподівано вдарив оглушливий грім посеред ясного літнього дня!» — скрикнула перелякана дівчина.",
            target_token="о господи",
            correct_answer="О господи",
            distractors=(
                InterjectionDistractor(
                    text="Огосподи",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_FUSION,
                    explanation_ua="Вигуковий зворот «о господи» пишеться окремо per § 41, п. 2, § 53.",
                    explanation_en="Interjection phrase 'о господи' is spelled separately per § 41, p. 2, § 53.",
                ),
                InterjectionDistractor(
                    text="О-господи",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Дефісне написання «о-господи» є помилковим; вигук «о» та звертання пишуться окремо.",
                    explanation_en="Hyphenated 'о-господи' is incorrect; interjection 'о' and noun are written separately.",
                ),
                InterjectionDistractor(
                    text="А господи",
                    interference_key=InterjectionInterferenceKey.CORRUPTED_ADVERB_FORM,
                    explanation_ua="Зворот заклику традиційно використовує вигук «о» («о господи»), а не сполучник «а».",
                    explanation_en="The exclamation traditionally uses interjection 'о' ('о господи'), not conjunction 'а'.",
                ),
            ),
            rule_citation=cit11,
            rule_summary_ua=ua11,
            rule_summary_en=en11,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_55",
            category=InterjectionCategory.SPELLING_MULTIWORD_SEPARATE,
            prompt="«_______, знову напередодні довгоочікуваного вихідного зіпсувалася погода!» — розчаровано зітхнув рибалка.",
            target_token="от тобі й маєш",
            correct_answer="От тобі й маєш",
            distractors=(
                InterjectionDistractor(
                    text="От-тобі й маєш",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Багатослівний фразеологічний вигук «от тобі й маєш» пишеться всіма словами окремо per § 41, п. 2.",
                    explanation_en="Multi-word phraseological interjection 'от тобі й маєш' is written with all words separately per § 41, p. 2.",
                ),
                InterjectionDistractor(
                    text="От тобі-й маєш",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Частка «й» та займенник «тобі» пишуться окремо без жодних дефісів.",
                    explanation_en="Particle 'й' and pronoun 'тобі' are written separately without hyphens.",
                ),
                InterjectionDistractor(
                    text="От тобі й маєшь",
                    interference_key=InterjectionInterferenceKey.RUSSIANISM_CALQUE,
                    explanation_ua="У 2-й особі теперішнього часу дієслова закінчуються на тверде «-ш» («маєш»), а не м'яке «-шь».",
                    explanation_en="In 2nd person present verbs end with hard '-ш' ('маєш'), not soft '-шь'.",
                ),
            ),
            rule_citation=cit11,
            rule_summary_ua=ua11,
            rule_summary_en=en11,
        )
    )

    # Category 12: Syntax Punctuation Particle (5 cards)
    cit12, ua12, en12 = resolve_syntax_punctuation_particle_rule()
    cards.append(
        InterjectionCard(
            card_id="interjection_card_56",
            category=InterjectionCategory.SYNTAX_PUNCTUATION_PARTICLE,
            prompt="«_______ мій, люблю тебе безтямно всім серцем і душею!» — палко на одному диханні без інтонаційної паузи виголосив поет, уживаючи «о» як підсилювальну частку перед звертанням.",
            target_token="о краю",
            correct_answer="О краю",
            distractors=(
                InterjectionDistractor(
                    text="О, краю",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_UNWARRANTED_COMMA_PARTICLE,
                    explanation_ua="Коли «о» виступає в ролі підсилювальної частки при звертанні, кома між ними НЕ ставиться: «О краю мій!» per § 158, п. 9, прим. 1.",
                    explanation_en="When 'о' serves as an intensifying particle before an address, NO comma is placed between them: 'О краю мій!' per § 158, p. 9, note 1.",
                ),
                InterjectionDistractor(
                    text="О! Краю",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_EXCLAMATION_OMISSION,
                    explanation_ua="Знак оклику тут розриває цілісне поетичне звертання «О краю мій», перетворюючи частку на штучний вигук.",
                    explanation_en="An exclamation mark here tears apart the integral poetic address 'О краю мій', turning the particle into an unnatural interjection.",
                ),
                InterjectionDistractor(
                    text="О-краю",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Частка «о» та іменник пишуться окремо без дефіса: «О краю мій».",
                    explanation_en="Particle 'о' and noun are written separately without a hyphen: 'О краю мій'.",
                ),
            ),
            rule_citation=cit12,
            rule_summary_ua=ua12,
            rule_summary_en=en12,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_57",
            category=InterjectionCategory.SYNTAX_PUNCTUATION_PARTICLE,
            prompt="«_______, мій брате широкий, розлий же свої могутні весняні води!» — урочисто без інтонаційної паузи промовив козак, поєднуючи підсилювальну частку «ой» зі звертанням.",
            target_token="ой дніпре",
            correct_answer="Ой Дніпре",
            distractors=(
                InterjectionDistractor(
                    text="Ой, Дніпре",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_UNWARRANTED_COMMA_PARTICLE,
                    explanation_ua="Слово «ой» перед звертанням є підсилювальною часткою, тому кома між часткою «ой» та звертанням «Дніпре» не ставиться per § 158, п. 9, прим. 1.",
                    explanation_en="Word 'ой' before an address is an intensifying particle, so no comma is placed between particle 'ой' and address 'Дніпре' per § 158, p. 9, note 1.",
                ),
                InterjectionDistractor(
                    text="Ой! Дніпре",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_EXCLAMATION_OMISSION,
                    explanation_ua="Знак оклику після частки «ой» руйнує нерозривний поетичний зв'язок частки зі звертанням.",
                    explanation_en="An exclamation mark after particle 'ой' breaks the uninterrupted poetic connection of particle and address.",
                ),
                InterjectionDistractor(
                    text="Ой-Дніпре",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Частка «ой» ніколи не поєднується зі звертанням через дефіс; слова пишуться окремо.",
                    explanation_en="Particle 'ой' is never hyphenated with the address; words are spelled separately.",
                ),
            ),
            rule_citation=cit12,
            rule_summary_ua=ua12,
            rule_summary_en=en12,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_58",
            category=InterjectionCategory.SYNTAX_PUNCTUATION_PARTICLE,
            prompt="«_______, як довго я не бачив твоїх безкраїх золотих нив!» — зітхнув мандрівник, зробивши виразну інтонаційну паузу після самостійного емоційного вигуку «о» перед звертанням.",
            target_token="о краю мій",
            correct_answer="О, краю мій",
            distractors=(
                InterjectionDistractor(
                    text="О краю мій",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_COMMA_OMISSION,
                    explanation_ua="Тут «о» є самостійним емоційним вигуком суму й замилування, що вимовляється з паузою перед звертанням, тому вимагає коми: «О, краю мій...» per § 158, п. 9.",
                    explanation_en="Here 'о' is an independent emotional interjection of longing pronounced with a pause before the address, requiring a comma: 'О, краю мій...' per § 158, p. 9.",
                ),
                InterjectionDistractor(
                    text="О! краю мій",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_EXCLAMATION_OMISSION,
                    explanation_ua="Після знаку оклику наступне слово обов'язково починається з великої літери per § 46, п. 2; тут наступне слово «краю» з малої.",
                    explanation_en="After an exclamation mark the next word must be capitalized per § 46, p. 2; here 'краю' is lowercase.",
                ),
                InterjectionDistractor(
                    text="О-краю мій",
                    interference_key=InterjectionInterferenceKey.UNWARRANTED_HYPHEN,
                    explanation_ua="Вигук «о» та іменник не з'єднуються дефісом; між ними ставиться кома.",
                    explanation_en="Interjection 'о' and the noun are not hyphenated; a comma is placed between them.",
                ),
            ),
            rule_citation=cit12,
            rule_summary_ua=ua12,
            rule_summary_en=en12,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_59",
            category=InterjectionCategory.SYNTAX_PUNCTUATION_PARTICLE,
            prompt="«_______ Що це за дивовижна веселка засяяла над високим лісом?» — виразно з сильною окличною інтонацією вигукнула дитина (наступне речення починається з великої літери).",
            target_token="леле",
            correct_answer="Леле!",
            distractors=(
                InterjectionDistractor(
                    text="Леле,",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_EXCLAMATION_OMISSION,
                    explanation_ua="Оскільки наступне речення починається з великої літери («Що») per § 46, п. 2, а вигук вимовляється з сильною окличною інтонацією, після нього ставиться знак оклику per § 157, п. 3, а не кома.",
                    explanation_en="Since the following sentence begins with a capital letter ('Що') per § 46, p. 2 and the interjection is uttered with strong exclamation intonation, it requires an exclamation mark per § 157, p. 3, not a comma.",
                ),
                InterjectionDistractor(
                    text="Леле—",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_WRONG_DELIMITER,
                    explanation_ua="Тире після вигуку на початку речення не ставиться; емоційне відокремлення позначається знаком оклику per § 157, п. 3.",
                    explanation_en="A dash after an interjection at the beginning of a sentence is incorrect; emotional isolation is marked by an exclamation mark per § 157, p. 3.",
                ),
                InterjectionDistractor(
                    text="Леле",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_COMMA_OMISSION,
                    explanation_ua="Залишення вигуку без жодного розділового знака є грубою синтаксичною помилкою.",
                    explanation_en="Leaving an interjection without any punctuation mark is a syntactic error.",
                ),
            ),
            rule_citation=cit12,
            rule_summary_ua=ua12,
            rule_summary_en=en12,
        )
    )
    cards.append(
        InterjectionCard(
            card_id="interjection_card_60",
            category=InterjectionCategory.SYNTAX_PUNCTUATION_PARTICLE,
            prompt="«_______ як солодко й п'янко пахне скошена лугова трава на світанку!» — спокійно з плавною невикличною інтонацією прошепотіла дівчина (наступне слово починається з малої літери).",
            target_token="ох",
            correct_answer="Ох,",
            distractors=(
                InterjectionDistractor(
                    text="Ох!",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_EXCLAMATION_OMISSION,
                    explanation_ua="Наступне слово «як» написане з малої літери, а вигук вимовляється з повільною розповідною інтонацією, тому він відокремлюється комою per § 158, п. 9, а не знаком оклику.",
                    explanation_en="The following word 'як' is lowercase and the interjection is uttered with gentle narrative intonation, so it is set off by a comma per § 158, p. 9, not an exclamation mark.",
                ),
                InterjectionDistractor(
                    text="Ох—",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_WRONG_DELIMITER,
                    explanation_ua="Тире не використовується на початку речення після вигуку; потрібна кома: «Ох, як солодко...» per § 158, п. 9.",
                    explanation_en="A dash is not used at sentence start after an interjection; a comma is required: 'Ох, як солодко...' per § 158, p. 9.",
                ),
                InterjectionDistractor(
                    text="Ох",
                    interference_key=InterjectionInterferenceKey.PUNCTUATION_COMMA_OMISSION,
                    explanation_ua="Вигук на початку речення не можна залишати без розділового знака; потрібна кома per § 158, п. 9.",
                    explanation_en="An interjection at the beginning of a sentence cannot be left unpunctuated; a comma is required per § 158, p. 9.",
                ),
            ),
            rule_citation=cit12,
            rule_summary_ua=ua12,
            rule_summary_en=en12,
        )
    )

    return cards


def is_valid_vesum_token(cursor: sqlite3.Cursor, raw_token: str) -> bool:
    """Validates an individual token or compound against VESUM dictionary.

    Rejects malformed strings (consecutive hyphens, leading/trailing hyphens, empty parts).
    If the full form exists in forms_all:
      - Accepts if any entry is not tagged with :bad.
      - REJECTS immediately if all entries are tagged with :bad (e.g. чуть-чуть, баю-баю, чи-то, будь-ласка),
        preventing flawed compound fallback approval.

    Only when the full compound is absent from forms_all does it attempt rule-backed compound validation:
      - Exact reduplication (§ 35, п. 5, 4): parts count == identical set, and base morphology must be
        an onomatopoeia, interjection, predicative, particle, or nominative sound noun (excluding :bad).
      - Enclitic particles (§ 44, п. 3, 1): stem + recognized enclitic particle (-бо, -но, -то, -от, -таки),
        where stem morphology must be imperative verb, interjection, predicative, adverb, or particle (excluding :bad).
    """
    strip_punctuation = ".,!?:;—…\"'«»`()[]"
    clean = raw_token.strip(strip_punctuation).lower().replace("’", "'").replace("`", "'")
    if not clean or clean.startswith("-") or clean.endswith("-") or "--" in clean:
        return False

    # 1. Full-form check in forms_all
    cursor.execute(
        "SELECT tags FROM forms_all WHERE word_form = ? OR word_form = ? OR word_form = ?",
        (clean, clean.capitalize(), clean.lower()),
    )
    full_matches = cursor.fetchall()
    if full_matches:
        # If full form is attested, accept if ANY entry is non-bad; reject immediately if all are bad
        return any(":bad" not in row[0] for row in full_matches)

    # 2. Rule-backed compound validation ONLY when full compound is absent from forms_all
    if "-" in clean:
        parts = clean.split("-")
        word_re = re.compile(r"^[а-яіїєґ']+$")
        if not all(p and word_re.match(p) for p in parts):
            return False

        # Case A: Exact reduplication (e.g. гав-гав, крап-крап, хлюп-хлюп, цок-цок) per § 35, п. 5, 4)
        if len(set(parts)) == 1:
            base = parts[0]
            cursor.execute(
                "SELECT tags FROM forms_all WHERE (word_form = ? OR word_form = ? OR word_form = ?) AND tags NOT LIKE '%bad%'",
                (base, base.capitalize(), base.lower()),
            )
            base_tags = [row[0] for row in cursor.fetchall()]
            if not base_tags:
                return False
            # Constrain constituent morphology: must be onomatopoeia, interjection, predicative, particle, or nominative sound noun
            return any(any(sub in tag for sub in REDUPLICATION_BASE_TAG_SUBSTRINGS) for tag in base_tags)

        # Case B: Stem + recognized enclitic particle (e.g. годі-бо, ну-бо, давай-но) per § 44, п. 3, 1)
        if len(parts) == 2 and parts[1] in ENCLITIC_PARTICLES:
            stem = parts[0]
            cursor.execute(
                "SELECT tags FROM forms_all WHERE (word_form = ? OR word_form = ? OR word_form = ?) AND tags NOT LIKE '%bad%'",
                (stem, stem.capitalize(), stem.lower()),
            )
            stem_tags = [row[0] for row in cursor.fetchall()]
            if not stem_tags:
                return False
            # Constrain constituent morphology: must be imperative verb, interjection, predicative, adverb, or particle
            return any(any(sub in tag for sub in ENCLITIC_STEM_TAG_SUBSTRINGS) for tag in stem_tags)

    return False


def verify_deck_with_vesum(
    cards: list[InterjectionCard],
    vesum_db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Validates target tokens of canonical interjection cards against VESUM dictionary.

    Hyphenated repeated forms and particle combinations are validated directly
    or through their constituent elements.
    """
    default_db = PROJECT_ROOT / "data/vesum.db"
    resolved_path = Path(vesum_db_path) if vesum_db_path else default_db

    if not resolved_path.exists() or resolved_path.stat().st_size == 0:
        return {
            "total_cards": len(cards),
            "target_tokens_count": 0,
            "missing_targets": [],
            "empty_cards": [],
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
            "vesum_verified": None,
            "status": "skipped",
            "message": f"forms_all table not found in VESUM database at {resolved_path}",
        }

    strip_punctuation = ".,!?:;—…\"'«»`()[]"

    all_target_tokens: set[str] = set()
    missing_targets: list[str] = []
    empty_cards: list[str] = []
    card_tokens_map: dict[str, list[str]] = {}

    for card in cards:
        raw_tokens = card.target_token.split()
        valid_tokens_for_card: list[str] = []
        for w in raw_tokens:
            clean = w.strip(strip_punctuation).lower().replace("’", "'").replace("`", "'")
            if not clean:
                continue
            valid_tokens_for_card.append(clean)
            all_target_tokens.add(clean)

        if not valid_tokens_for_card:
            empty_cards.append(card.card_id)
            missing_targets.append(f"{card.card_id}: no valid vocabulary tokens in target_token '{card.target_token}'")
        else:
            card_tokens_map[card.card_id] = valid_tokens_for_card

    # Verify each unique valid token in VESUM using strict is_valid_vesum_token
    unattested_tokens: set[str] = set()
    for token in sorted(all_target_tokens):
        if not is_valid_vesum_token(cursor, token):
            unattested_tokens.add(token)

    conn.close()

    if unattested_tokens:
        for card_id, tokens in card_tokens_map.items():
            for tok in tokens:
                if tok in unattested_tokens:
                    missing_targets.append(f"{card_id}: token '{tok}' not found in VESUM")

    total_valid = len(cards) > 0 and len(empty_cards) == 0 and len(missing_targets) == 0 and len(all_target_tokens) > 0

    return {
        "total_cards": len(cards),
        "target_tokens_count": len(all_target_tokens),
        "missing_targets": missing_targets,
        "empty_cards": empty_cards,
        "vesum_verified": total_valid,
        "status": "passed" if total_valid else "failed",
    }


def export_deck(cards: list[InterjectionCard], target_path: Path | str) -> dict[str, Any]:
    """Serializes canonical interjection practice cards to JSON."""
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
        "title": "Практикум: Глибока механіка вигуків та звуконаслідувань (Правопис, спонукання, етикет, звуки, пунктуація)",
        "card_count": len(deck_cards),
        "categories": [c.value for c in InterjectionCategory],
        "cards": deck_cards,
    }

    out_file = Path(target_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Interjection & Onomatopoeia Deep Mechanics Practice Engine")
    parser.add_argument("--verify-vesum", action="store_true", help="Verify targets against VESUM")
    parser.add_argument("--export", action="store_true", help="Export canonical JSON deck")
    parser.add_argument(
        "--output", type=str, default="data/practice/interjection_mechanics_deck.json", help="Output path"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON results to stdout")
    args = parser.parse_args()

    cards = build_canonical_interjection_cards()

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
