"""Stanza proposes clause structure; VESUM supplies grammatical proof (#9661).

The firm switch is deliberately off pending the driver's one-shot frozen run.
A persistent, single-flight child makes load/inference deadlines enforceable:
Python threads cannot interrupt native Torch work safely.
"""

from __future__ import annotations

import atexit
import multiprocessing
import threading
import time
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

from scripts.curriculum.resolver.tokenize import Token
from scripts.verification.stanza_models import manifest

FIRM_ENABLED = False
COLD_LOAD_SECONDS = 20.0
SENTENCE_SECONDS = 0.100
CALL_SECONDS = 0.500
TORCH_THREADS = 4
MAX_SENTENCE_TOKENS = 40
TIME_UNITS = frozenset({"рік", "місяць", "тиждень", "день", "доба", "година", "хвилина", "секунда", "століття"})


def _load_pipeline():
    """Only the candidate-triggered child imports these optional dependencies."""
    from scripts.verification.stanza_models import pipeline_kwargs

    kwargs = pipeline_kwargs()
    import stanza
    import torch

    if stanza.__version__ != manifest()["stanza_version"]:
        raise RuntimeError("stanza_version_mismatch")
    torch.set_num_threads(TORCH_THREADS)
    torch.set_num_interop_threads(TORCH_THREADS)
    return stanza.Pipeline(**kwargs)


def _parser_child(connection):
    """Load once, send only bounded tree structure, never model or input logs."""
    try:
        pipeline = _load_pipeline()
        # Initialize native kernels within the killable cold-load cap. This
        # synthetic warmup contains a candidate; no candidate-free text is parsed.
        pipeline("На протязі року.")
        connection.send((True, None))
        while True:
            text = connection.recv()
            doc = pipeline(text)
            if len(doc.sentences) != 1:
                connection.send((False, "malformed_tree"))
                continue
            connection.send((True, document_tree(doc)))

    except (EOFError, BrokenPipeError):
        pass
    except Exception as error:
        with suppress(EOFError, BrokenPipeError):
            connection.send((False, type(error).__name__))
    finally:
        connection.close()


def document_tree(doc) -> list[dict]:
    """Serialize one aligned sentence; MWT expansion fails closed."""
    if len(doc.sentences) != 1:
        return []
    words = []
    for token in doc.sentences[0].tokens:
        if len(token.words) != 1:
            return []
        word = token.words[0]
        words.append(
            dict(
                id=word.id,
                text=word.text,
                start=token.start_char,
                end=token.end_char,
                head=word.head,
                deprel=word.deprel,
                upos=word.upos,
                feats=word.feats or "",
            )
        )
    return words


class Parser:
    """One attempt per process, nonblocking lock, killable native inference."""

    def __init__(self):
        self.lock = threading.Lock()
        self.process = None
        self.connection = None
        self.failed = False
        self.cold_seconds = None

    def close(self):
        """Terminate without queuing or leaving a timed-out inference alive."""
        if self.process is not None:
            self.process.terminate()
            self.process.join(timeout=0.1)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=0.1)
        if self.connection is not None:
            self.connection.close()
        self.failed = True

    def parse(self, text: str, budget: CallBudget) -> tuple[list[dict] | None, str | None]:
        """Cold load has its own cap; warm work shares the call's inference budget."""
        if self.failed:
            return None, "parser_unavailable"
        if budget.remaining <= 0:
            return None, "budget_exhausted"
        if not self.lock.acquire(blocking=False):
            return None, "lock_busy"
        try:
            if self.process is None:
                started = time.monotonic()
                ctx = multiprocessing.get_context("spawn")
                parent, child = ctx.Pipe()
                self.connection = parent
                self.process = ctx.Process(target=_parser_child, args=(child,), daemon=True)
                self.process.start()
                child.close()
                if not parent.poll(max(0, COLD_LOAD_SECONDS - (time.monotonic() - started))):
                    self.close()
                    return None, "cold_load_budget_exhausted"
                ok, _ = parent.recv()
                self.cold_seconds = time.monotonic() - started
                if not ok:
                    self.close()
                    return None, "parser_unavailable"
            started = time.monotonic()
            try:
                self.connection.send(text)
                allowance = min(SENTENCE_SECONDS, budget.remaining)
                if not self.connection.poll(max(0, allowance - (time.monotonic() - started))):
                    self.close()
                    return None, "budget_exhausted"
                ok, tree = self.connection.recv()
                if time.monotonic() - started > allowance:
                    self.close()
                    return None, "budget_exhausted"
                if not ok:
                    return None, "malformed_tree"
                return tree, None
            finally:
                budget.remaining -= time.monotonic() - started
        except Exception:
            self.close()
            return None, "parser_unavailable"
        finally:
            self.lock.release()


@dataclass
class CallBudget:
    """Shared across items and occurrences in one public check_text call."""

    remaining: float = CALL_SECONDS
    trees: dict = field(default_factory=dict)


PARSER = Parser()
atexit.register(PARSER.close)


def _readings(token: Token, morphology: dict) -> list[dict]:
    return morphology.get(token.lookup.lower(), []) or morphology.get(token.lookup, [])


def _tags(reading: dict) -> set[str]:
    return set(reading.get("tags", "").split(":"))


def _external_cases(readings: list[dict]) -> set[str]:
    """Preserve every viable case; numeral animate accusatives cannot time events."""
    cases = set()
    genitive_numerals = {r.get("lemma") for r in readings if r.get("pos") == "numr" and "v_rod" in _tags(r)}
    for reading in readings:
        tags = _tags(reading)
        if "nv" in tags:
            cases.add("unknown")
        for case in tags & {"v_naz", "v_rod", "v_zna"}:
            if case == "v_zna" and (
                "ranim" in tags
                or (
                    reading.get("pos") == "numr" and reading.get("lemma") in genitive_numerals and "rinanim" not in tags
                )
            ):
                continue
            cases.add(case)
    return cases


def _valid_tree(tree: list[dict], sentence: str, tokens: list[Token], offset: int) -> bool:
    """Reject cycles, broken roots/IDs, bad offsets and tokenizer disagreement."""
    if not isinstance(tree, list) or not tree or not all(isinstance(w, dict) for w in tree):
        return False
    if [w.get("id") for w in tree] != list(range(1, len(tree) + 1)):
        return False
    if sum(w.get("head") == 0 for w in tree) != 1:
        return False
    for word in tree:
        if not isinstance(word.get("deprel"), str):
            return False
        start, end, head = word.get("start"), word.get("end"), word.get("head")
        if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(sentence):
            return False
        if sentence[start:end] != word.get("text") or not isinstance(head, int) or not 0 <= head <= len(tree):
            return False
        seen = {word["id"]}
        while head:
            if head in seen:
                return False
            seen.add(head)
            head = tree[head - 1].get("head")
            if not isinstance(head, int) or not 0 <= head <= len(tree):
                return False
    return all(
        any(w["start"] == t.start - offset and w["end"] == t.end - offset for w in tree)
        for t in tokens
        if t.kind in {"cyrillic", "digits"}
    )


def grammar_reading(
    text: str, tokens: list[Token], start: int, tree: list[dict], morphology: dict
) -> tuple[str, str, int]:
    """Require a complete genitive NP and agreement; parse-only exclusions abstain.

    Reversed/approximate quantities, asides, subjects and unknown valency retain
    alternatives. In particular a genitive noun inside a quantity is not proof
    of external genitive government.
    """
    end = start + 2
    phrase = []
    noun = None
    for index in range(end, min(len(tokens), end + 8)):
        token = tokens[index]
        if token.kind not in {"cyrillic", "digits"} or not text[tokens[index - 1].end : token.start].isspace():
            return "undecided", "unsupported_scope", end
        readings = _readings(token, morphology)
        if not readings:
            return "undecided", "missing_morphology", end
        time_readings = [r for r in readings if r.get("pos") == "noun" and r.get("lemma") in TIME_UNITS]
        if time_readings:
            noun = (token, time_readings)
            end = index + 1
            break
        modifiers = [r for r in readings if r.get("pos") in {"adj", "numr"}]
        if not modifiers:
            # No time complement: locative reading is viable, not certified.
            return "undecided", "no_temporal_complement", end
        phrase.append((token, modifiers))
    if noun is None:
        return "undecided", "no_temporal_complement", end
    noun_token, noun_readings = noun
    # A following numeral/quantifier anywhere before a clause boundary preserves
    # independent duration, even across a comma aside or an approximating particle.
    for token in tokens[end:]:
        if token.lookup in {";", ".", "!", "?"}:
            break
        readings = _readings(token, morphology)
        if token.kind == "digits" or any(r.get("pos") == "numr" or r.get("lemma") == "десяток" for r in readings):
            return "undecided", "quantity_or_aside_alternative", end
    noun_cases = _external_cases(noun_readings)
    modifier_cases = [_external_cases(readings) for _, readings in phrase]
    # Exclusive accusative duration is positive counterevidence, independently
    # confirmed by the parser's duration proposal; parser alone cannot suppress.
    node = next(w for w in tree if w["start"] == noun_token.start and w["end"] == noun_token.end)
    if "v_rod" not in noun_cases and "v_zna" in noun_cases and node["deprel"].startswith("obl"):
        return "draught", "vesum_accusative_duration", end
    if "v_rod" not in noun_cases or any("v_rod" not in cases for cases in modifier_cases):
        return "undecided", "no_genitive_government", end
    if any(cases != {"v_rod"} for cases in modifier_cases):
        return "undecided", "modifier_case_alternative", end
    if noun_cases != {"v_rod"}:
        # Agreement can eliminate a nominal case alternative only when there is
        # an agreeing, case-exclusive adjective (not an internally governed noun).
        if not phrase or not any(any(r.get("pos") == "adj" for r in rs) for _, rs in phrase):
            return "undecided", "noun_case_alternative", end
        for case in noun_cases - {"v_rod"}:
            if case == "unknown" or any(case in cases for cases in modifier_cases):
                return "undecided", "noun_case_alternative", end
    genitive_nouns = [r for r in noun_readings if "v_rod" in _tags(r)]
    for _, readings in phrase:
        adjectives = [r for r in readings if r.get("pos") == "adj" and "v_rod" in _tags(r)]
        if adjectives and not any(
            ("p" in _tags(a) and "p" in _tags(n))
            or ("p" not in _tags(a) and "p" not in _tags(n) and bool(_tags(a) & _tags(n) & {"m", "f", "n"}))
            for a in adjectives
            for n in genitive_nouns
        ):
            return "undecided", "agreement_disagreement", end
        if any(r.get("pos") == "numr" for r in readings) and not any("p" in _tags(n) for n in genitive_nouns):
            return "undecided", "numeral_government_disagreement", end
    # Require the proposed NP to be governed by the candidate's locative noun.
    protiah = next(w for w in tree if w["start"] == tokens[start + 1].start)
    if node["head"] != protiah["id"] or node["deprel"] != "nmod":
        return "undecided", "parser_grammar_disagreement", end
    for token, _ in phrase:
        modifier = next(w for w in tree if w["start"] == token.start)
        if modifier["head"] != node["id"] or modifier["deprel"] not in {"amod", "det", "nummod", "nummod:gov"}:
            return "undecided", "parser_grammar_disagreement", end
    return "temporal", "vesum_genitive_government", end


def classify(
    text: str,
    tokens: list[Token],
    start: int,
    morphology: dict,
    *,
    budget: CallBudget | None = None,
    parser=None,
    firm_enabled: bool | None = None,
) -> dict[str, Any]:
    """Classify one occurrence; every unavailable/over-budget result is suspicion."""
    budget = budget if budget is not None else CallBudget()
    evidence = {"model_revision": manifest()["revision"]}
    result = dict(reading="undecided", status="suspicion", end=start + 2, evidence=evidence)
    # Tokens carry exact source offsets. Split on explicit hard boundaries only;
    # comma asides remain in their complete candidate-containing sentence.
    left = start
    while left > 0 and not tokens[left].sentence_initial and tokens[left - 1].lookup not in {";", ".", "!", "?"}:
        left -= 1
    right = start + 2
    while (
        right < len(tokens)
        and not tokens[right].sentence_initial
        and tokens[right - 1].lookup not in {";", ".", "!", "?"}
    ):
        right += 1
    sentence_tokens = tokens[left:right]
    offset = sentence_tokens[0].start
    sentence = text[offset : sentence_tokens[-1].end]
    key = sentence
    if len(sentence_tokens) > MAX_SENTENCE_TOKENS:
        tree, reason = None, "sentence_token_budget_exhausted"
    elif key in budget.trees:
        tree, reason = budget.trees[key]
    else:
        tree, reason = (parser or PARSER).parse(sentence, budget)
        budget.trees[key] = (tree, reason)
    if reason or not _valid_tree(tree, sentence, sentence_tokens, offset):
        evidence.update(parser_unavailable=True, reason=reason or "malformed_tree")
        return result
    # Grammar works with original offsets, never parser case predictions.
    tree = [dict(w, start=w["start"] + offset, end=w["end"] + offset) for w in tree]
    reading, reason, end = grammar_reading(text, tokens[:right], start, tree, morphology)
    evidence.update(reason=reason, positive_genitive_government=reading == "temporal")
    enabled = FIRM_ENABLED if firm_enabled is None else firm_enabled
    result.update(reading=reading, end=end)
    if reading == "temporal" and enabled:
        result["status"] = "documented_calque"
    elif reading == "draught":
        result["status"] = "none"
    return result
