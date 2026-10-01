"""Listening models attested by locked pack records, never synthetic audio."""

from __future__ import annotations

from typing import Any

from scripts.curriculum.evidence.pack import load_schema
from scripts.curriculum.resolver.tokenize import lookup_form

# The structured table carries its source citations: Pravopys 2019,
# sections 10 and 63.2, and primer/textbook chunks verified through sources MCP.
# Section 1 concerns E/I spelling, not the isolated sound overlaps.
# https://mon.gov.ua/static-objects/mon/sites/1/zagalna%20serednya/Pravopys.2019/ukr.pravopys-2019.pdf
# Digraphs are atomic sounds; iotated letters are modeled in isolation here.
_MODEL_LETTERS = load_schema("evidence-pack-v1.schema.json")["$defs"]["video_record"]["properties"]["models"][
    "properties"
]["letters"]
LETTER_SOUNDS = {letter: tuple(sounds) for letter, sounds in _MODEL_LETTERS["x-sound-sequences"].items()}


def model_target(
    target_ref: str | None, video_ref: str, pack: dict[str, Any], words: dict[str, Any]
) -> tuple[str | None, str | None]:
    """Resolve an explicit letter/sound or word ID from structured host models."""
    video = next((v for v in pack.get("videos", []) if v.get("id") == video_ref), None)
    if video is None or not video.get("url"):
        return None, "listening_video_missing"
    if not isinstance(target_ref, str):
        return None, "listening_target_invalid"
    models = video.get("models")
    if not isinstance(models, dict):
        return None, "listening_model_undeclared"
    if target_ref.startswith("W-"):
        target = next((w for w in words.get("words", []) if w.get("id") == target_ref), None)
        if target is None:
            return None, "listening_target_invalid"
        value = target.get("lemma")
        if not any(f.get("learner") is True and f.get("form") == value for f in target.get("forms", [])):
            return None, "listening_target_invalid"
        declared = target_ref in models.get("words", [])
    else:
        if target_ref.casefold() not in LETTER_SOUNDS:
            return None, "listening_target_invalid"
        value = target_ref
        declared = target_ref.casefold() in {letter.casefold() for letter in models.get("letters", [])}
    if not isinstance(value, str) or not value:
        return None, "listening_target_invalid"
    if not declared:
        return None, "listening_model_unverified"
    return value, None


def choice_error(
    item: dict[str, Any],
    texts: list[Any],
    key: int,
    target: str,
    words: dict[str, Any],
    *,
    letters: set[str],
    record_ids: set[str],
) -> str | None:
    """Require one target and taught options with no contained sound distractor."""
    if not 0 <= key < len(texts):
        return "listening_key_not_unique"
    if not all(isinstance(text, str) for text in texts):
        return "listening_option_invalid"
    spellings = [lookup_form(text).casefold() for text in texts]
    matches = [text == lookup_form(target).casefold() for text in spellings]
    if len(set(spellings)) != len(spellings) or matches != [i == key for i in range(len(texts))]:
        return "listening_key_not_unique"
    if not item["target_record"].startswith("W-"):
        target_sounds = LETTER_SOUNDS.get(target.casefold())
        if target_sounds is None:
            return "listening_target_invalid"
        if any(
            text not in LETTER_SOUNDS or text not in {letter.casefold() for letter in letters} for text in spellings
        ):
            return "listening_letter_not_taught"
        for index, text in enumerate(spellings):
            if index == key:
                continue
            sounds = LETTER_SOUNDS[text]
            if any(target_sounds[start : start + len(sounds)] == sounds for start in range(len(target_sounds))):
                return "listening_key_not_unique"
    else:
        bindings = item.get("option_records")
        records = {w["id"]: w for w in words.get("words", []) if w["id"] in record_ids}
        if not isinstance(bindings, list) or len(bindings) != len(texts):
            return "listening_option_record_missing"
        for ref, text in zip(bindings, texts, strict=True):
            if not any(
                f.get("learner") is True and lookup_form(f.get("form", "")).casefold() == lookup_form(text).casefold()
                for f in records.get(ref, {}).get("forms", [])
            ):
                return "listening_option_not_taught"
        if bindings[key] != item["target_record"]:
            return "listening_target_record_mismatch"
    return None
