"""Listening models attested by locked pack records, never synthetic audio."""

from __future__ import annotations

from typing import Any

from scripts.curriculum.resolver.tokenize import lookup_form


def model_target(
    target_ref: str | None, video_ref: str, pack: dict[str, Any], words: dict[str, Any]
) -> tuple[str | None, str | None]:
    """Read a word lemma or primer's letter heading and its explicit media model.

    The pack's `use` is the source builder's attestation, not a transcript.
    Generic episode descriptions cannot establish that a particular word is heard.
    """
    video = next((v for v in pack.get("videos", []) if v.get("id") == video_ref), None)
    if video is None or not video.get("url"):
        return None, "listening_video_missing"
    if not isinstance(target_ref, str):
        return None, "listening_target_invalid"
    target = next((w for w in words.get("words", []) if w.get("id") == target_ref), None)
    if target_ref.startswith("W-") and target:
        value = target.get("lemma")
        if not any(f.get("learner") is True and f.get("form") == value for f in target.get("forms", [])):
            return None, "listening_target_invalid"
    else:
        target = next((t for t in pack.get("texts", []) if t.get("id") == target_ref), None)
        heading = str((target or {}).get("quote", "")).strip().splitlines()
        pair = heading[0].split() if heading else []
        if len(pair) != 2 or len(pair[0]) != 1 or pair != [pair[0].upper(), pair[0].lower()]:
            return None, "listening_target_invalid"
        value = pair[0]
    if not isinstance(value, str) or not value:
        return None, "listening_target_invalid"
    use = video.get("use", "")
    # The existing pack uses this exact model declaration for per-letter videos.
    # Do not search arbitrary descriptions for a coincidental word or letter.
    declarations = (f"Pronunciation model for {value}", f"Listening model for {value}")
    if not isinstance(use, str) or not any(
        use == declaration or use.startswith(declaration + " ") or use.startswith(declaration + ".")
        for declaration in declarations
    ):
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
    """Require one exact target and taught, nonmatching letter or word options."""
    if not 0 <= key < len(texts):
        return "listening_key_not_unique"
    if not all(isinstance(text, str) for text in texts):
        return "listening_option_invalid"
    spellings = [lookup_form(text).casefold() for text in texts]
    matches = [text == lookup_form(target).casefold() for text in spellings]
    if len(set(spellings)) != len(spellings) or matches != [i == key for i in range(len(texts))]:
        return "listening_key_not_unique"
    if item["target_record"].startswith("T-"):
        if any(len(text) != 1 or text not in {letter.casefold() for letter in letters} for text in spellings):
            return "listening_letter_not_taught"
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
