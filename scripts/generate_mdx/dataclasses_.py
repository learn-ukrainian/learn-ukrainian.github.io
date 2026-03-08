"""Data classes for MDX generation.

Defines the typed structures used to represent parsed activity data
(quiz questions, match pairs, fill-in items, etc.) before conversion to JSX.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuizQuestion:
    question: str
    options: list[dict]  # [{"text": str, "correct": bool}]


@dataclass
class MatchPair:
    left: str
    right: str


@dataclass
class FillInItem:
    sentence: str
    answer: str
    options: list[str]


@dataclass
class TrueFalseItem:
    statement: str
    is_true: bool
    explanation: str


@dataclass
class UnjumbleItem:
    jumbled: str
    answer: str


@dataclass
class GroupSortData:
    groups: dict[str, list[str]]  # {group_name: [items]}


@dataclass
class AnagramItem:
    scrambled: str
    answer: str
    hint: str


@dataclass
class ErrorCorrectionItem:
    sentence: str
    errorWord: str
    correctForm: str
    options: list[str]
    explanation: str


@dataclass
class ClozeData:
    passage: str
    blanks: list[dict]  # [{"answer": str, "options": list[str]}]


@dataclass
class SelectQuestion:
    question: str
    options: list[dict]  # [{"text": str, "correct": bool}]


@dataclass
class TranslateQuestion:
    source: str
    options: list[dict]  # [{"text": str, "correct": bool}]


@dataclass
class MarkTheWordsItem:
    text: str  # Plain text with marks removed
    correctWords: list[str]  # List of correct words to mark


@dataclass
class MorphemeItem:
    word: str  # The full word containing the morpheme
    morpheme: str  # The morpheme to highlight within the word
    type: str = 'unknown'  # prefix, root, or suffix


@dataclass
class HighlightMorphemesItem:
    text: str  # Plain text with asterisks removed
    morphemes: list[MorphemeItem]  # List of morphemes to highlight
    instruction: str = ''  # Optional instruction text


@dataclass
class EssayResponseData:
    prompt: str
    modelAnswer: str
    rubric: str


@dataclass
class ComparativeStudyData:
    content: str
    task: str
    modelAnswer: str
