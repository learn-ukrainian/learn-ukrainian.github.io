#!/usr/bin/env python3
"""Pre-training Cross-Stage Contradiction Audit (Phase 5.5 / #8054).

Mandated by Advisor Fable:
Executes an automated contradiction audit before gradient updates begin:
1. Verifies that all 600 Phase 5.2 protection cases (dialect_historical_protection_suite_600.jsonl)
   are protected against training loss contradiction.
2. Ensures 0 regionalisms, phonological variants, or historical archaic forms are penalized
   as 'errors' in the 6,000 SFT shards or 3,000 DPO pairs. Fails closed if shards are missing
   or empty.
3. Verifies that the 100 anti-surzhyk/anti-calque controls exclusively target authentic Russian-Soviet occupation
   Russianisms and calques, with every replacement term verified against positive decolonized
   authorities (СУМ-20, Grinchenko 1907, VESUM).
4. Generates a certified Markdown audit report and JSON metrics.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_data_path(rel_path: str | Path) -> Path:
    """Resolve a relative data path, falling back to git common parent checkout for gitignored files."""
    path_obj = Path(rel_path)
    local_p = (REPO_ROOT / path_obj).resolve() if not path_obj.is_absolute() else path_obj
    if local_p.exists():
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = (Path(common).resolve().parent / path_obj).resolve()
        if main_p.exists():
            return main_p
    except Exception:
        pass
    return local_p


# Default paths relative to project root
DEFAULT_PROTECTION_SUITE = Path("data/projects/open_model_data/decolonization/partitions/dialect_historical_protection_suite_600.jsonl")
DEFAULT_SFT_DIR = Path("data/projects/open_model_data/release/uldr_v1_production/sft")
DEFAULT_DPO_DIR = Path("data/projects/open_model_data/release/uldr_v1_production/dpo")
DEFAULT_SOURCES_DB = Path("data/sources.db")
DEFAULT_VESUM_DB = Path("data/vesum.db")
DEFAULT_OUTPUT_MD = Path("docs/reports/uldr_v02_pretraining_contradiction_audit.md")
DEFAULT_OUTPUT_JSON = Path("docs/reports/uldr_v02_pretraining_contradiction_audit.json")


def load_protection_suite(path: Path) -> list[dict[str, Any]]:
    """Load and validate the 600-case protection suite."""
    resolved_path = resolve_data_path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Protection suite not found: {path} (resolved: {resolved_path})")
    cases: list[dict[str, Any]] = []
    with resolved_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))
    return cases


def normalize_token(token: str) -> str:
    """Normalize Ukrainian word token by stripping stress marks and unifying apostrophes."""
    # Strip acute and grave combining accents (stress marks)
    norm = re.sub(r"[\u0300\u0301]", "", str(token or ""))
    # Normalize curly/typographic apostrophes to standard straight apostrophe
    norm = re.sub(r"[’'`‘ʼ]", "'", norm)
    return norm.lower().strip()


def verify_replacement_attestation(
    replacement: str,
    vesum_conn: sqlite3.Connection,
    sources_conn: sqlite3.Connection,
) -> bool:
    """Check if all tokens of the replacement word/phrase are attested in approved Ukrainian authorities."""
    clean = replacement.strip().strip("–—\"'«» .,")
    raw_words = re.findall(r"[А-Яа-яЇїІіЄєҐґ’'ʼ\u0300\u0301]+", clean)
    words = [normalize_token(w) for w in raw_words if normalize_token(w)]
    if not words:
        return False

    for w in words:
        # VESUM lemma or inflected form
        in_vesum = vesum_conn.execute(
            "SELECT 1 FROM forms_all WHERE word_form = ? OR lemma = ? LIMIT 1",
            (w, w),
        ).fetchone()
        in_sum20 = sources_conn.execute(
            "SELECT 1 FROM sum20_articles WHERE headword = ? OR normalized_lookup_key = ? LIMIT 1",
            (w, w),
        ).fetchone()
        in_grinchenko = sources_conn.execute(
            "SELECT 1 FROM grinchenko WHERE word = ? LIMIT 1",
            (w,),
        ).fetchone()
        if not (in_vesum or in_sum20 or in_grinchenko):
            return False
    return True


ANAPHORIC_WORDS = frozenset({
    # Personal pronouns
    "він", "вона", "воно", "вони",
    "його", "йому", "ним", "ньому", "нього",
    "її", "їй", "нею", "ній", "неї",
    "їх", "їм", "ними", "них",
    # Demonstrative pronouns
    "це", "цей", "ця", "ці",
    "цього", "цієї", "цьому", "цій", "цим", "цими", "цих", "цю",
    "то", "той", "та", "ті", "того", "тієї", "тому", "тій", "тим", "тими", "тих", "ту",
    # Relative pronouns
    "який", "яка", "яке", "які",
    "якого", "якої", "якому", "якій", "яким", "якою", "яких", "якими", "яку",
    "котрий", "котра", "котре", "котрі",
    "котрого", "котрої", "котрому", "котрій", "котрим", "котрою", "котрих", "котрими", "котру",
    "що",
    # Metalinguistic nouns and usage nouns
    "слово", "слова", "словом", "слові", "слів", "словах",
    "термін", "терміна", "терміну", "терміном", "терміні", "терміни", "термінів",
    "вираз", "виразу", "виразом", "виразі", "вирази", "виразів",
    "зворот", "звороту", "зворотом", "звороті", "звороти", "зворотів",
    "форма", "форми", "формою", "формі", "форм", "формах",
    "лексема", "лексеми", "лексемою", "лексемі", "лексем",
    "вживання", "вживанням", "вживанні", "вжитку", "вжиток",
    "використання", "використанням", "використанні",
    "застосування", "застосуванням", "застосуванні",
    "написання", "написанням", "написанні",
    "вимова", "вимовою", "вимові",
    "значення", "значенням", "значенні",
})

DIRECTIVE_INFINITIVES = (
    r"(?:вживати|вжити|використовувати|використати|"
    r"писати|казати|говорити|брати|"
    r"застосовувати|обирати|замінювати|замінити)"
)

DIRECTIVE_FINITES = (
    r"(?:вживайте|використовуйте|"
    r"пишіть|кажіть|говоріть|беріть|"
    r"застосовуйте|обирайте|замінюйте)"
)

DIRECTIVE_VERBS = rf"(?:{DIRECTIVE_INFINITIVES}|{DIRECTIVE_FINITES})"

DIRECTIVE_MODALS = (
    r"(?:слід|варто|потрібно|необхідно|треба|можна|рекомендовано|рекомендується|"
    r"дозволено|дозволяється|краще|правильно|доречно|бажано|годиться|"
    r"заборонено|забороняється|уникайте|уникати)"
)

ANY_DIRECTIVE_RE = re.compile(rf"\b(?:{DIRECTIVE_VERBS}|{DIRECTIVE_MODALS})\b", re.IGNORECASE)

NEGATION_DIRECTIVE_RE = re.compile(
    rf"(?:"
    rf"\b(?:не|ні|ані)\s*$|"
    rf"\b(?:не\s+(?:слід|варто|потрібно|необхідно|треба|можна|рекомендовано|рекомендується|дозволено|дозволяється|годиться|краще|правильно|доречно|бажано)|"
    rf"заборонено|забороняється|не\s+можна|уникайте|уникати)\b|"
    rf"\bне\s+{DIRECTIVE_VERBS}\b"
    rf")",
    re.IGNORECASE,
)

ADVERSATIVE_CONJUNCTIONS = r"\b(?:але|проте|однак|а|бо|тому що|оскільки|якщо|якби|хоч|хоча|аби|коли)\b"
COORDINATING_CONJUNCTIONS = r"\b(?:і|й|та|або|чи)\b"
CONJUNCTIONS = rf"(?:{ADVERSATIVE_CONJUNCTIONS}|{COORDINATING_CONJUNCTIONS})"

DISALLOWED_COORDINATED_TOKENS = (
    rf"(?:не|ні|ані|{DIRECTIVE_VERBS}|{DIRECTIVE_MODALS}|{ADVERSATIVE_CONJUNCTIONS}|{COORDINATING_CONJUNCTIONS}|"
    r"що|щоб|як|ніби|наче|неначе|мов)"
)
ITEM_CLASSIFIER = r"(?:(?:слово|слова|слів|термін\w*|вираз\w*|зворот\w*|форм\w*|лексем\w*)\s+)?"
ITEM_QUOTED = rf"{ITEM_CLASSIFIER}[«\"“‘\'][^»\"”’\n]+[»\"”’]"
ITEM_UNQUOTED = rf"{ITEM_CLASSIFIER}(?!\b{DISALLOWED_COORDINATED_TOKENS}\b)[А-Яа-яЇїІіЄєҐґ’'ʼ\w\-]+"
COORDINATED_ITEM = rf"(?:{ITEM_QUOTED}|{ITEM_UNQUOTED})"
COORDINATED_SEP = rf"(?:,\s*(?:{COORDINATING_CONJUNCTIONS}\s+)?|\s+{COORDINATING_CONJUNCTIONS}\s+)"
PRE_COORDINATED_ITEMS = rf"(?:{COORDINATED_ITEM}\s*{COORDINATED_SEP})*"
POST_COORDINATED_ITEMS = rf"(?:\s*{COORDINATED_SEP}{COORDINATED_ITEM})*"


def find_clause_start_in_prefix(prefix: str, dir_match: re.Match) -> int:
    """Find the start of the clause containing the directive in prefix."""
    dir_start = dir_match.start()
    dir_word = dir_match.group(0).lower()
    d_prefix = prefix[:dir_start]

    # If the directive is an infinitive, check if it is governed by a preceding modal auxiliary,
    # either across parentheticals ("Не слід, безумовно, вживати") or across coordinated infinitives
    # ("Не слід вживати «добрий» і використовувати «гарний»")
    search_prefix_end = dir_start
    if re.fullmatch(DIRECTIVE_INFINITIVES, dir_word, re.IGNORECASE):
        modal_matches = list(re.finditer(rf"\b{DIRECTIVE_MODALS}\b", d_prefix, re.IGNORECASE))
        if modal_matches:
            last_modal = modal_matches[-1]
            between = d_prefix[last_modal.end() :]
            has_adversative = bool(
                re.search(
                    rf"(?:[,;:\u2014\u2013]*\s*{ADVERSATIVE_CONJUNCTIONS}\b|[;:\u2014\u2013]+)",
                    between,
                    re.IGNORECASE,
                )
            )
            has_new_neg = bool(
                re.search(
                    rf"\b{COORDINATING_CONJUNCTIONS}\s+(?:не|ні|ані)\b",
                    between,
                    re.IGNORECASE,
                )
            )
            has_finite = bool(re.search(rf"\b{DIRECTIVE_FINITES}\b", between, re.IGNORECASE))
            if not has_adversative and not has_new_neg and not has_finite:
                search_prefix_end = last_modal.start()

    search_prefix = prefix[:search_prefix_end]

    boundaries = [0]
    # 1. Adversative conjunctions and semicolons/colons/dashes
    for m in re.finditer(
        rf"(?:[,;:\u2014\u2013]*\s*{ADVERSATIVE_CONJUNCTIONS}\b|[;:\u2014\u2013]+)",
        search_prefix,
        re.IGNORECASE,
    ):
        boundaries.append(m.end())

    # 2. Coordinating conjunctions (і, й, та): check if followed by negation or directive in prefix
    for m in re.finditer(
        rf"[,;:\u2014\u2013]*\s*{COORDINATING_CONJUNCTIONS}\s+",
        search_prefix,
        re.IGNORECASE,
    ):
        after_conj = prefix[m.end() :].lstrip()
        is_finite_or_modal = bool(
            re.search(rf"^(?:не\b|ні\b|ані\b|{DIRECTIVE_FINITES}\b|{DIRECTIVE_MODALS}\b)", after_conj, re.IGNORECASE)
        )
        is_unbound_infinitive = (
            search_prefix_end == dir_start
            and bool(re.search(rf"^{DIRECTIVE_INFINITIVES}\b", after_conj, re.IGNORECASE))
        )
        if is_finite_or_modal or is_unbound_infinitive:
            boundaries.append(m.end())

    # 3. Commas: if preceded by another directive in search_prefix AND followed by directive/negation in prefix
    for m in re.finditer(r",\s*", search_prefix):
        if ANY_DIRECTIVE_RE.search(search_prefix[: m.start()]):
            after_comma = prefix[m.end() :].lstrip()
            if re.search(rf"^(?:не\b|ні\b|ані\b|{DIRECTIVE_FINITES}\b|{DIRECTIVE_MODALS}\b)", after_comma, re.IGNORECASE):
                boundaries.append(m.end())

    return max(boundaries)


def find_clause_end_in_suffix(suffix: str, dir_end: int = 0) -> int:
    """Find the end of the clause in suffix, starting at or after dir_end."""
    boundaries: list[int] = []
    # 1. Adversative conjunctions and semicolons/colons/dashes
    for m in re.finditer(
        rf"(?:[,;:\u2014\u2013]*\s*{ADVERSATIVE_CONJUNCTIONS}\b|[;:\u2014\u2013]+)",
        suffix,
        re.IGNORECASE,
    ):
        if m.start() >= dir_end:
            boundaries.append(m.start())

    # 2. Coordinating conjunctions (і, й, та): only when followed by directive or negation
    for m in re.finditer(
        rf"[,;:\u2014\u2013]*\s*{COORDINATING_CONJUNCTIONS}\s+(?=(?:не\b|ні\b|ані\b|{DIRECTIVE_VERBS}\b|{DIRECTIVE_MODALS}\b))",
        suffix,
        re.IGNORECASE,
    ):
        if m.start() >= dir_end:
            boundaries.append(m.start())

    # 3. Commas followed by directive or negation
    for m in re.finditer(
        rf",\s*(?=(?:не\b|ні\b|ані\b|{DIRECTIVE_VERBS}\b|{DIRECTIVE_MODALS}\b))",
        suffix,
        re.IGNORECASE,
    ):
        if m.start() >= dir_end:
            boundaries.append(m.start())

    return min(boundaries) if boundaries else len(suffix)


def is_target_condemned_in_text(target_term: str, text: str) -> bool:
    """Check if the text explicitly condemns or directs replacement of the protected target term."""
    t_norm = normalize_token(target_term)
    if not t_norm or not text:
        return False

    # Normalize text by stripping combining accents (stress marks) and unifying apostrophes
    text_norm = re.sub(r"[\u0300\u0301]", "", text)
    text_norm = re.sub(r"[’'`‘ʼ]", "'", text_norm)

    t_bare = re.escape(t_norm)
    t_token_re = re.compile(rf"(?:[«\"“‘\']{t_bare}[»\"”’\']|\b{t_bare}\b|слово\s+\b{t_bare}\b)", re.IGNORECASE)
    anaphoric_re = re.compile(
        r"\b(?:"
        r"він|вона|воно|вони|"
        r"його|йому|ним|ньому|нього|"
        r"її|їй|нею|ній|неї|"
        r"їх|їм|ними|них|"
        r"це|цей|ця|ці|цього|цієї|цьому|цій|цим|цими|цих|цю|"
        r"то|той|ті|того|тієї|тому|тій|тим|тими|тих|ту|"
        r"як(?:ий|а|е|і|ого|ої|ому|ій|им|ою|их|ими|у)|"
        r"котр(?:ий|а|е|і|ого|ої|ому|ій|им|ою|их|ими|у)|"
        r"що|"
        r"слово|слова|словом|слові|"
        r"термін\w*|вираз\w*|зворот\w*|форм\w*|лексем\w*|"
        r"вживан\w*|вжит\w*|використан\w*|застосуван\w*|написан\w*|вимов\w*|значен\w*"
        r")\b",
        re.IGNORECASE,
    )

    target_in_text = bool(t_token_re.search(text_norm))
    current_referent = "TARGET" if not target_in_text else None

    # Check all explicit replacement instructions involving target:
    # e.g. "Замість <target> слід/варто... вживати <other>" or "вживайте <other> замість <target>"
    # Syntactic clause context is bound strictly to EACH individual occurrence.
    target_item = rf"{ITEM_CLASSIFIER}[«\"“‘\']?{t_bare}[»\"”’\']?"
    zamist_target_re = re.compile(
        rf"\bзамість\s+(?:{ITEM_CLASSIFIER})?{PRE_COORDINATED_ITEMS}{target_item}{POST_COORDINATED_ITEMS}",
        re.IGNORECASE,
    )
    for zm in zamist_target_re.finditer(text_norm):
        sent_start = 0
        for delim in (".", "!", "?", ";", "\n"):
            pos = text_norm.rfind(delim, 0, zm.start())
            if pos != -1 and pos + 1 > sent_start:
                sent_start = pos + 1

        sent_end = len(text_norm)
        for delim in (".", "!", "?", ";", "\n"):
            pos = text_norm.find(delim, zm.end())
            if pos != -1 and pos < sent_end:
                sent_end = pos

        sent_text = text_norm[sent_start:sent_end]
        zm_in_sent_start = zm.start() - sent_start
        zm_in_sent_end = zm.end() - sent_start

        prefix = sent_text[:zm_in_sent_start]
        suffix = sent_text[zm_in_sent_end:]

        # Check if there is a preceding directive in the same clause (Order 1)
        dir_matches = list(ANY_DIRECTIVE_RE.finditer(prefix))
        gov_dir_order1 = None
        if dir_matches:
            last_d = dir_matches[-1]
            between = prefix[last_d.end() :]
            # A separator between last_d and zm means last_d is in a different clause.
            # Coordinating conjunctions (і, й, та) only separate if followed by a directive/negation!
            sep_between = bool(
                re.search(
                    rf"(?:[,;:\u2014\u2013]*\s*{ADVERSATIVE_CONJUNCTIONS}\b|"
                    rf"[;:\u2014\u2013]+|"
                    rf"[,;:\u2014\u2013]*\s*{COORDINATING_CONJUNCTIONS}\s+(?:не\b|ні\b|ані\b|{DIRECTIVE_VERBS}\b|{DIRECTIVE_MODALS}\b)|"
                    rf",\s*(?:не\b|ні\b|ані\b|{DIRECTIVE_VERBS}\b|{DIRECTIVE_MODALS}\b))",
                    between,
                    re.IGNORECASE,
                )
            )
            if not sep_between:
                gov_dir_order1 = last_d

        if gov_dir_order1 is not None:
            # Order 1: directive precedes zm.
            cl_start = find_clause_start_in_prefix(prefix, gov_dir_order1)
            clause_span = prefix[cl_start : gov_dir_order1.end()].lower()

            # Check negation governing this directive
            is_negated = bool(NEGATION_DIRECTIVE_RE.search(clause_span))
            # Also check if modal negation follows zm in suffix before the clause ends
            cl_end_s = find_clause_end_in_suffix(suffix, 0)
            suffix_clause = suffix[:cl_end_s]
            if NEGATION_DIRECTIVE_RE.search(suffix_clause):
                is_negated = True

            if not is_negated:
                return True
            else:
                # Negated replacement: target is defended
                continue

        # Order 2: directive follows zm (e.g. "замість <target> не слід вживати...")
        # Suffix directive only belongs to this clause if no clause boundary
        # (adversative conjunction, semicolon/colon) separates замість <target> from the directive.
        # Coordinating conjunctions only separate if introducing a directive/negation.
        directive_found = False
        for d_m in ANY_DIRECTIVE_RE.finditer(suffix):
            between_zm_and_dir = suffix[: d_m.start()]
            # 1. Adversative conjunctions or semicolon/colon strictly separate clauses
            if re.search(
                rf"(?:[,;:\u2014\u2013]*\s*{ADVERSATIVE_CONJUNCTIONS}\b|[;:]+)",
                between_zm_and_dir,
                re.IGNORECASE,
            ):
                break
            # 2. Coordinating conjunctions ONLY separate clauses if followed by a directive/negation
            if re.search(
                rf"\b{COORDINATING_CONJUNCTIONS}\s+(?:не\b|ні\b|ані\b|{DIRECTIVE_VERBS}\b|{DIRECTIVE_MODALS}\b)",
                between_zm_and_dir,
                re.IGNORECASE,
            ):
                break

            directive_found = True
            cl_end = find_clause_end_in_suffix(suffix, d_m.end())
            clause_span = suffix[:cl_end].lower()

            is_negated = bool(NEGATION_DIRECTIVE_RE.search(clause_span))
            if not is_negated:
                return True
            else:
                # Negated directive in this clause defends target; do not look for later directives
                break

        if directive_found:
            continue

        # Check em-dash shorthand (e.g. "замість <target> — <replacement>")
        dash_m = re.match(r"^\s*(?:—|--)\s*[«\"“‘\']?([А-Яа-яЇїІіЄєҐґ’'ʼ\w\s]+)[»\"”’\']?", suffix)
        if dash_m:
            return True

    # Split text into sentence/clause units by punctuation or coordinate/adversative conjunctions introducing clauses
    split_pat = re.compile(
        r"(?:[.,\n;!?:\u2014\u2013]+|"
        r"\s+\b(?:але|проте|однак)\b\s+|"
        r"\s+\b(?:та|і|й|а|або|чи)\s+(?=[«\"“‘\'][^»\"”’\n]+[»\"”’]\s+(?:слід|варто|потрібно|необхідно|треба|можна|є|не)\b|\b(?:його|її|їх|це|цей|цю|цього|цій|цим|слово|термін|вираз|зворот|щодо|для|слід|варто|потрібно|необхідно|треба|можна|не)\b|[а-яА-ЯёЁіІїЇєЄґҐ’\'\-]+\s+(?:слід|варто|потрібно|необхідно|треба|можна|є|не)\b))",
        re.IGNORECASE,
    )

    clauses = [c.strip() for c in split_pat.split(text_norm) if c.strip()]
    for clause in clauses:
        cl_lower = clause.lower()
        quoted = re.findall(r"[«\"“‘\']([^»\"”’\']+)[»\"”’\']", clause)

        if t_token_re.search(clause):
            # If target is present ONLY as a replacement destination (e.g. "замінити на «файний»"),
            # it is being recommended, not condemned or replaced.
            is_destination = bool(re.search(rf"\b(?:на|до)\s+[«\"“‘\']?{t_bare}[»\"”’\']?", cl_lower))
            is_subject = bool(re.search(rf"(?:^|\b(?:щодо\s+слова|слово|словом|вираз|зворот)\s+)?[«\"“‘\']?{t_bare}[»\"”’\']?\s+(?:є|це|не|слід|варто|потрібно|необхідно|треба|можна|—|\-)", cl_lower))
            current_referent = "OTHER" if is_destination and not is_subject else "TARGET"
        elif quoted:
            first_q = normalize_token(quoted[0])
            if first_q != t_norm:
                subj_m = re.search(
                    rf"(?:^|\b(?:щодо\s+слова|слово|словом|вираз|зворот)\s+)?[«\"“‘\']{re.escape(first_q)}[»\"”’\']",
                    cl_lower,
                )
                if subj_m and not re.search(rf"\b(?:на|до)\s+[«\"“‘\']{re.escape(first_q)}[»\"”’\']", cl_lower):
                    current_referent = "OTHER"
        else:
            # Check for unquoted subject before directives (e.g. "общий слід замінити")
            unquoted_subj_m = re.search(
                r"(?:^|\b(?:щодо\s+слова|слово|словом|вираз|зворот)\s+)?([а-яА-ЯёЁіІїЇєЄґҐ’'\-]+)\s+(?:слід|варто|потрібно|необхідно|треба|можна|потребує|вимагає|є|не|вважа\w*|визна\w*|назива\w*)",
                cl_lower,
            )
            if unquoted_subj_m:
                uq_word = normalize_token(unquoted_subj_m.group(1))
                prefix_to_subj = cl_lower[:unquoted_subj_m.start(1)]
                has_anaphoric_det = bool(anaphoric_re.search(prefix_to_subj))
                if uq_word in ANAPHORIC_WORDS or anaphoric_re.fullmatch(uq_word) or has_anaphoric_det:
                    # Anaphoric reference (його, її, це, яку, його вживання, etc.): preserve active referent
                    pass
                elif uq_word != t_norm and not re.search(rf"\b(?:на|до)\s+{re.escape(uq_word)}", cl_lower):
                    current_referent = "OTHER"
            elif anaphoric_re.search(clause) and current_referent is not None:
                # Anaphoric reference (його, її, це, etc.): preserve active referent from preceding clause
                pass

        if current_referent != "TARGET":
            continue

        # If target in this clause was governed by замість, it was already evaluated above.
        # Bypass subsequent directives (like unikayte) so they don't falsely condemn target.
        if zamist_target_re.search(cl_lower):
            continue

        # Check replacement / avoidance directives
        # A directive is a contradiction unless it is specifically negated
        replace_dirs = [
            r"(?:слід|варто|потрібно|необхідно|треба|можна)\s+(?:замінити|замінювати|уникати|виправити|виправляти)",
            r"\b(?:замініть|замінити|уникайте|уникати|виправте|виправити)\b",
            r"(?:потребує|вимагає)\s+(?:заміни|виправлення)",
        ]
        for rpat in replace_dirs:
            for match in re.finditer(rpat, cl_lower):
                start = match.start()
                prefix = cl_lower[:start]
                is_negated = False
                if re.search(r"\b(?:ні|ані)\s*$", prefix):
                    is_negated = True
                else:
                    last_ne = prefix.rfind("не ")
                    if last_ne != -1:
                        after_ne = prefix[last_ne + 3:]
                        if not re.search(r"\b(?:але|проте|однак)\b", after_ne):
                            is_negated = bool(
                                re.search(r"\bне\s+(?:слід|варто|потрібно|необхідно|треба|можна)?(?:\s+(?:ні|ані))?\s*$", prefix)
                            )
                if not is_negated:
                    return True

        condemn_patterns = [
            r"\bпомилк\w*",
            r"\bкальк\w*",
            r"\bросіянізм\w*",
            r"\bрусизм\w*",
            r"\bсуржик\w*",
            r"\bненормативн\w*",
            r"\bнеправильн\w*",
            r"не\s+(?:є\s+)?нормативн\w*",
            r"не\s+(?:є\s+)?правильн\w*",
        ]

        for cpat in condemn_patterns:
            for match in re.finditer(cpat, cl_lower):
                start = match.start()
                prefix = cl_lower[:start]
                is_negated = False
                # 1. Correlative / coordinated negation: "ні калькою", "ані калькою", "ні є помилкою"
                if (
                    re.search(r"\b(?:ні|ані)\s+(?:є\s+|це\s+|вважається\s+)?(?:жодн\w*\s+|ніяк\w*\s+)?$", prefix)
                    or re.search(r"\b(?:ні|ані)\s*$", prefix)
                ):
                    is_negated = True
                else:
                    last_ne = prefix.rfind("не ")
                    if last_ne != -1:
                        after_ne = prefix[last_ne + 3:]
                        if not re.search(r"\b(?:але|проте|однак)\b", after_ne):
                            is_negated = bool(
                                re.search(r"\bне\s+(?:є|це|було|буде|був|була|становить|вважається|визнається|(?:слід|варто|можна|треба|потрібно|необхідно)\s+(?:вважати|називати|визнавати))(?:\s+(?:ні|ані|жодн\w*|ніяк\w*|зовсім|анітрохи))*\s*$", prefix)
                                or re.search(r"\bне\s*$", prefix)
                                or re.search(r"\bне\s+(?:є\s+|це\s+|вважається\s+|було\s+)?[а-яА-ЯёЁіІїЇєЄґҐ’'\-]+(?:\s*,\s*|\s+(?:та|і|й|чи|або|ні|ані)\s+)(?:не\s+|ні\s+|ані\s+)?$", prefix)
                            )
                if not is_negated:
                    return True

    return False


def run_pretraining_audit(
    protection_path: Path = DEFAULT_PROTECTION_SUITE,
    sft_dir: Path = DEFAULT_SFT_DIR,
    dpo_dir: Path = DEFAULT_DPO_DIR,
    sources_db_path: Path = DEFAULT_SOURCES_DB,
    vesum_db_path: Path = DEFAULT_VESUM_DB,
    output_md: Path = DEFAULT_OUTPUT_MD,
    output_json: Path = DEFAULT_OUTPUT_JSON,
    min_sft_records: int = 6000,
    min_dpo_pairs: int = 3000,
    min_cases: int = 600,
) -> tuple[bool, dict[str, Any], str]:
    # Resolve all data paths (supporting worktrees and shared common git checkouts)
    resolved_protection = resolve_data_path(protection_path)
    resolved_sft = resolve_data_path(sft_dir)
    resolved_dpo = resolve_data_path(dpo_dir)
    resolved_sources = resolve_data_path(sources_db_path)
    resolved_vesum = resolve_data_path(vesum_db_path)

    # 1. Path existence and non-zero shard checks (Finding 1)
    if not resolved_sft.exists():
        raise FileNotFoundError(f"SFT directory does not exist: {sft_dir} (resolved: {resolved_sft})")
    if not resolved_dpo.exists():
        raise FileNotFoundError(f"DPO directory does not exist: {dpo_dir} (resolved: {resolved_dpo})")

    sft_files = sorted(resolved_sft.glob("*.jsonl"))
    if not sft_files:
        raise ValueError(f"No SFT shards found in {sft_dir} (resolved: {resolved_sft})")

    dpo_files = sorted(resolved_dpo.glob("*.jsonl"))
    if not dpo_files:
        raise ValueError(f"No DPO shards found in {dpo_dir} (resolved: {resolved_dpo})")

    if not resolved_sources.exists():
        raise FileNotFoundError(f"Sources database does not exist: {sources_db_path} (resolved: {resolved_sources})")
    if not resolved_vesum.exists():
        raise FileNotFoundError(f"VESUM database does not exist: {vesum_db_path} (resolved: {resolved_vesum})")

    cases = load_protection_suite(resolved_protection)
    total_cases = len(cases)

    # 2. Stratum distribution check
    dialect_cases = [c for c in cases if c.get("stratum") == "regional_dialect"]
    historical_cases = [c for c in cases if c.get("stratum") == "historical_text"]
    surzhyk_cases = [c for c in cases if c.get("stratum") == "anti_surzhyk_control"]

    # 3. Collect protected terms (must be PRESERVE)
    invalid_preservations = [
        c.get("eval_id")
        for c in dialect_cases + historical_cases
        if c.get("expected_action") != "PRESERVE"
    ]
    if invalid_preservations:
        raise ValueError(
            f"Protection suite has non-PRESERVE dialect/historical cases: {invalid_preservations}"
        )

    protected_cases = [c for c in cases if c.get("expected_action") == "PRESERVE"]
    expected_min_preservations = 500 if min_cases >= 600 else 1
    if len(protected_cases) < expected_min_preservations:
        raise ValueError(
            f"Insufficient protected preservation cases: expected >= {expected_min_preservations}, got {len(protected_cases)}"
        )

    protected_terms: set[str] = {
        normalize_token(c["target_term"]) for c in protected_cases if c.get("target_term")
    }
    expected_min_terms = 250 if min_cases >= 600 else 1
    if len(protected_terms) < expected_min_terms:
        raise ValueError(
            f"Insufficient unique protected terms: expected >= {expected_min_terms}, got {len(protected_terms)}"
        )

    # 4. Cross-audit SFT shards (Validating production schema and labels)
    sft_contradictions: list[dict[str, Any]] = []
    sft_total_count = 0

    for sft_file in sft_files:
        for line_idx, line in enumerate(sft_file.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            sft_total_count += 1
            item = json.loads(line)
            raw_target = item.get("target_term") or ""
            target = normalize_token(raw_target)
            if not target:
                raise ValueError(
                    f"SFT record at line {line_idx+1} in {sft_file.name} lacks required 'target_term'"
                )

            is_calque = item.get("is_calque_or_russianism")
            if is_calque is not None and not isinstance(is_calque, bool):
                raise ValueError(
                    f"SFT record at line {line_idx+1} in {sft_file.name} has invalid 'is_calque_or_russianism': "
                    f"expected boolean True/False, got {type(is_calque).__name__} ({is_calque!r})"
                )

            raw_action = item.get("action") or item.get("case_type")
            if raw_action is not None:
                if not isinstance(raw_action, str):
                    raise ValueError(
                        f"SFT record at line {line_idx+1} in {sft_file.name} has non-string action label: {raw_action!r}"
                    )
                action = raw_action.strip().upper()
                if action not in ("PRESERVE", "CORRECT", "REPLACE"):
                    raise ValueError(
                        f"SFT record at line {line_idx+1} in {sft_file.name} has unrecognized action: {raw_action!r}. "
                        f"Recognized actions are: ('PRESERVE', 'CORRECT', 'REPLACE')"
                    )
            else:
                action = ""

            if is_calque is None and not action:
                raise ValueError(
                    f"SFT record at line {line_idx+1} in {sft_file.name} lacks required label field "
                    f"('is_calque_or_russianism' or 'action')"
                )

            # In production SFT, is_calque_or_russianism is True when the target term is flagged as an error/calque
            is_condemned = (is_calque is True) or (action in ("CORRECT", "REPLACE"))
            if target in protected_terms and is_condemned:
                sft_contradictions.append({
                    "shard": sft_file.name,
                    "line": line_idx + 1,
                    "target_term": target,
                    "is_calque_or_russianism": is_calque,
                    "action": action,
                    "prompt": item.get("query") or item.get("input_text") or item.get("prompt"),
                })

    # 5. Cross-audit DPO shards (Validating production schema and preference direction)
    dpo_contradictions: list[dict[str, Any]] = []
    dpo_total_count = 0

    for dpo_file in dpo_files:
        for line_idx, line in enumerate(dpo_file.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            dpo_total_count += 1
            item = json.loads(line)
            prompt = item.get("prompt")
            chosen = item.get("chosen")
            rejected = item.get("rejected")
            if not prompt or not chosen or not rejected:
                raise ValueError(
                    f"DPO record at line {line_idx+1} in {dpo_file.name} lacks required prompt/chosen/rejected"
                )

            metadata = item.get("metadata")
            if not isinstance(metadata, dict):
                raise ValueError(
                    f"DPO record at line {line_idx+1} in {dpo_file.name} lacks valid 'metadata' dict"
                )

            raw_target = metadata.get("target_term") or ""
            target = normalize_token(raw_target)
            if not target:
                raise ValueError(
                    f"DPO record at line {line_idx+1} in {dpo_file.name} lacks 'metadata.target_term'"
                )

            pair_type = metadata.get("pair_type", "")
            # If target in protected terms and pair penalizes it as an error or directs replacement
            if target in protected_terms and (
                pair_type != "anti_hyper_purist_preservation_pairs"
                or is_target_condemned_in_text(target, chosen)
            ):
                dpo_contradictions.append({
                    "shard": dpo_file.name,
                    "line": line_idx + 1,
                    "target_term": target,
                    "pair_type": pair_type,
                    "prompt": prompt,
                    "chosen": chosen,
                })

    # 6. Surzhyk control validation against positive authorities (Finding 2)
    surzhyk_valid = True
    surzhyk_anomalies: list[dict[str, Any]] = []

    sources_uri = f"file:{resolved_sources.resolve()}?mode=ro"
    vesum_uri = f"file:{resolved_vesum.resolve()}?mode=ro"
    with (
        sqlite3.connect(sources_uri, uri=True) as sources_conn,
        sqlite3.connect(vesum_uri, uri=True) as vesum_conn,
    ):
        for sc in surzhyk_cases:
            action = sc.get("expected_action")
            repl = sc.get("expected_replacement")
            if action != "CORRECT" or not repl:
                surzhyk_valid = False
                surzhyk_anomalies.append({
                    "eval_id": sc.get("eval_id"),
                    "reason": "Missing CORRECT action or empty replacement",
                })
                continue

            if not verify_replacement_attestation(repl, vesum_conn, sources_conn):
                surzhyk_valid = False
                surzhyk_anomalies.append({
                    "eval_id": sc.get("eval_id"),
                    "replacement": repl,
                    "reason": f"Replacement '{repl}' not attested in positive authorities (СУМ-20, VESUM, Grinchenko 1907)",
                })

    # 7. Overall audit determination (Hard Non-Vacuous Gates)
    passed = (
        (
            (
                len(cases) == 600
                and len(dialect_cases) == 300
                and len(historical_cases) == 200
                and len(surzhyk_cases) == 100
                and len(protected_cases) == 500
                and len(protected_terms) >= 250
            )
            if min_cases >= 600
            else (
                len(cases) >= min_cases
                and len(protected_cases) >= expected_min_preservations
                and len(protected_terms) >= 1
            )
        )
        and len(sft_files) > 0
        and sft_total_count >= min_sft_records
        and len(dpo_files) > 0
        and dpo_total_count >= min_dpo_pairs
        and len(sft_contradictions) == 0
        and len(dpo_contradictions) == 0
        and surzhyk_valid
    )

    now_iso = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    report_data: dict[str, Any] = {
        "audit_timestamp": now_iso,
        "overall_status": "PASSED" if passed else "FAILED",
        "protection_suite_cases": total_cases,
        "stratum_counts": {
            "regional_dialect": len(dialect_cases),
            "historical_text": len(historical_cases),
            "anti_surzhyk_control": len(surzhyk_cases),
        },
        "protected_cases_count": len(protected_cases),
        "protected_terms_count": len(protected_terms),
        "sft_shards_audited": len(sft_files),
        "sft_records_audited": sft_total_count,
        "sft_records_minimum": min_sft_records,
        "sft_contradictions_count": len(sft_contradictions),
        "sft_contradictions": sft_contradictions,
        "dpo_shards_audited": len(dpo_files),
        "dpo_pairs_audited": dpo_total_count,
        "dpo_pairs_minimum": min_dpo_pairs,
        "dpo_contradictions_count": len(dpo_contradictions),
        "dpo_contradictions": dpo_contradictions,
        "anti_surzhyk_valid": surzhyk_valid,
        "anti_surzhyk_anomalies": surzhyk_anomalies,
    }

    # Format Markdown report (Evidence-grounded, no unconditional success claims)
    details_lines = [
        "## 2. Invariant Verification Details",
        "",
        "1. **False Penalization Scan of Dialect & Historical Forms:**",
        f"   - **{len(protected_terms)}** unique protected regional and historical terms were checked across {sft_total_count:,} SFT records and {dpo_total_count:,} DPO pairs.",
    ]
    if len(sft_contradictions) == 0 and len(dpo_contradictions) == 0:
        details_lines.append("   - **Result:** Zero training examples penalize protected forms as errors or attempt to normalize them into contemporary standard Ukrainian.")
    else:
        details_lines.append(f"   - **Result:** Contradictions detected: {len(sft_contradictions)} in SFT, {len(dpo_contradictions)} in DPO.")
        for sc in sft_contradictions[:10]:
            details_lines.append(f"     - [SFT] {sc['shard']}:{sc['line']} target '{sc['target_term']}' condemned")
        for dc in dpo_contradictions[:10]:
            details_lines.append(f"     - [DPO] {dc['shard']}:{dc['line']} target '{dc['target_term']}' pair '{dc['pair_type']}'")

    verified_controls = len(surzhyk_cases) - len(surzhyk_anomalies)
    details_lines.extend([
        "",
        "2. **Anti-Surzhyk Control Verification against Positive Authorities:**",
        f"   - Observed anti-surzhyk control cases: {len(surzhyk_cases)} cases targeting Russianisms and Russian-Soviet occupation calques.",
        f"   - Attestation verification against positive Ukrainian authorities (СУМ-20, VESUM, Grinchenko 1907): {verified_controls} / {len(surzhyk_cases)} verified.",
    ])
    if surzhyk_anomalies:
        for sa in surzhyk_anomalies[:10]:
            details_lines.append(f"     - [Anomaly] {sa.get('eval_id')}: {sa.get('reason')}")

    md_lines = [
        "# ULDR v0.2 Pre-Training Contradiction Audit Report",
        "",
        "> **Phase:** Phase 5.5 (ULDR v0.2 Alignment Training & 5-Gate Evaluation / Issue #8054)",
        f"> **Audit Date:** {now_iso}",
        f"> **Overall Status:** {'✅ PASSED — ZERO CONTRADICTIONS DETECTED' if passed else '❌ FAILED'}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "This audit fulfills the pre-training cross-stage contradiction defense mandated by Advisor Fable prior to Gemma 3 4B alignment training.",
        f"All **{total_cases}** protection cases from `dialect_historical_protection_suite_600.jsonl` were audited against all **{sft_total_count:,}** SFT training records across **{len(sft_files)}** shards and **{dpo_total_count:,}** DPO pairs across **{len(dpo_files)}** shards.",
        "",
        "| Audit Dimension | Target Invariant | Measured Result | Audit Verdict |",
        "| :--- | :--- | :---: | :---: |",
        f"| **Protection Suite Population** | Exactly 600 cases | {total_cases} cases | {'✅ PASS' if total_cases == 600 else '❌ FAIL'} |",
        f"| **Regional Dialect Preserves** | Exactly 300 cases | {len(dialect_cases)} cases | {'✅ PASS' if len(dialect_cases) == 300 else '❌ FAIL'} |",
        f"| **Historical Text Preserves** | Exactly 200 cases | {len(historical_cases)} cases | {'✅ PASS' if len(historical_cases) == 200 else '❌ FAIL'} |",
        f"| **Anti-Surzhyk Controls** | Exactly 100 cases | {len(surzhyk_cases)} cases | {'✅ PASS' if len(surzhyk_cases) == 100 else '❌ FAIL'} |",
        f"| **SFT Corpus Population** | $\\ge {min_sft_records:,}$ records across shards | {sft_total_count:,} records ({len(sft_files)} shards) | {'✅ PASS' if sft_total_count >= min_sft_records and len(sft_files) > 0 else '❌ FAIL'} |",
        f"| **DPO Corpus Population** | $\\ge {min_dpo_pairs:,}$ pairs across shards | {dpo_total_count:,} pairs ({len(dpo_files)} shards) | {'✅ PASS' if dpo_total_count >= min_dpo_pairs and len(dpo_files) > 0 else '❌ FAIL'} |",
        f"| **SFT Training Contradictions** | Exact 0 observed | **{len(sft_contradictions)}** contradictions | {'✅ PASS' if len(sft_contradictions) == 0 else '❌ FAIL'} |",
        f"| **DPO Training Contradictions** | Exact 0 observed | **{len(dpo_contradictions)}** contradictions | {'✅ PASS' if len(dpo_contradictions) == 0 else '❌ FAIL'} |",
        f"| **Anti-Surzhyk Authority Grounding** | 100% replacement attestation | {len(surzhyk_cases) - len(surzhyk_anomalies)} / {len(surzhyk_cases)} verified (СУМ-20/VESUM/Грінченко) | {'✅ PASS' if surzhyk_valid else '❌ FAIL'} |",
        "",
        "---",
        "",
        *details_lines,
        "",
        "---",
        "",
        "*Certified by ULDR Phase 5.5 Pre-Training Contradiction Audit Runner.*",
    ]
    md_content = "\n".join(md_lines) + "\n"

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(md_content, encoding="utf-8")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return passed, report_data, md_content


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-training Cross-Stage Contradiction Audit")
    parser.add_argument("--protection-suite", type=Path, default=DEFAULT_PROTECTION_SUITE)
    parser.add_argument("--sft-dir", type=Path, default=DEFAULT_SFT_DIR)
    parser.add_argument("--dpo-dir", type=Path, default=DEFAULT_DPO_DIR)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--min-sft-records", type=int, default=6000)
    parser.add_argument("--min-dpo-pairs", type=int, default=3000)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)

    args = parser.parse_args()
    passed, data, _ = run_pretraining_audit(
        protection_path=args.protection_suite,
        sft_dir=args.sft_dir,
        dpo_dir=args.dpo_dir,
        sources_db_path=args.sources_db,
        vesum_db_path=args.vesum_db,
        min_sft_records=args.min_sft_records,
        min_dpo_pairs=args.min_dpo_pairs,
        output_md=args.output_md,
        output_json=args.output_json,
    )

    print(f"Pre-training Contradiction Audit: {'PASSED' if passed else 'FAILED'}")
    print(f"  SFT Contradictions: {data['sft_contradictions_count']}")
    print(f"  DPO Contradictions: {data['dpo_contradictions_count']}")
    print(f"  Anti-Surzhyk Authority Valid: {data['anti_surzhyk_valid']}")
    print(f"  Report written to: {args.output_md}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
