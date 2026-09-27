"""Unit and integration tests for Ukrainian Adjective Deep Mechanics Practice Engine.

Tests:
  1. Degrees of comparison formation rules [Правопис 2019 §§ 110–113]:
     - Consonant mutations: г, ж, з + -ш- -> -жч- (дорожчий, ближчий, вужчий).
     - Consonant mutations: к, с + -ш- -> -щ- (вищий, товщий, кращий).
     - Standard qualitative suffix: -іш- (новіший, тепліший, розумніший).
     - Suppletive comparison (великий -> більший, малий -> менший, поганий -> гірший).
     - Compound analytic comparison (більш / менш + base adjective).
     - Superlative synthetic prefix: най- (найкращий, найвищий; anti-calque: *самий кращий).
     - Emphatic prefixes: якнай-, щонай-.
  2. Declension groups: Hard vs Soft [Правопис 2019 §§ 106–109]:
     - High-error focus: masculine/neuter soft instrumental singular ending strictly -ім
       (синім, літнім, осіннім, раннім), not *-им*.
     - Soft Genitive/Dative: -ього / -ьому.
  3. Possessive adjectives and morphophonemic suffixation [Правопис 2019 §§ 22, 107]:
     - Suffix -ів (-ова, -еве) from II declension masculine nouns.
     - Suffix -ин (-ина, -ине) from I declension nouns with mutations (Ольга -> Ольжин, дочка -> доччин).
     - Derivational suffixes -ськ-, -цьк-, -зьк- (§ 22).
  4. Deck validation: zero collisions, valid option counts, prompt blank markers.
  5. Balanced deterministic shuffle distribution across indices 0..3.
  6. Committed deck file parity.
  7. VESUM database validation for all target inflected forms.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.practice.adjective_mechanics_engine import (
    AdjectiveCategory,
    build_canonical_adjective_cards,
    export_adjective_mechanics_deck,
    resolve_degree_comparison_rule,
    resolve_derivational_suffix_mutation_rule,
    resolve_possessive_suffix_rule,
    resolve_soft_declension_instrumental_rule,
    validate_adjective_card,
    verify_deck_with_vesum,
    verify_distractors_with_vesum,
)


def test_resolve_degree_comparison_rule():
    """Verify degrees of comparison rules per Правопис 2019 §§ 110, 111."""
    # -жч- mutation
    ind_zhch, ua_zhch, en_zhch = resolve_degree_comparison_rule(AdjectiveCategory.COMP_SYNTHETIC_MUTATION_ZHCH)
    assert ind_zhch == "-жч-"
    assert "переходять у -жч-" in ua_zhch
    assert "-zhch-" in en_zhch

    # -щ- mutation
    ind_shch, ua_shch, en_shch = resolve_degree_comparison_rule(AdjectiveCategory.COMP_SYNTHETIC_MUTATION_SHCH)
    assert ind_shch == "-щ-"
    assert "переходять у -щ-" in ua_shch
    assert "-shch-" in en_shch

    # -ш- suffix dropping -k-/-ok-
    ind_dropk, ua_dropk, en_dropk = resolve_degree_comparison_rule(AdjectiveCategory.COMP_SYNTHETIC_SH_DROPPING_K)
    assert "-ш-" in ind_dropk
    assert "випадають" in ua_dropk
    assert "drop" in en_dropk

    # -іш- suffix
    ind_ish, ua_ish, en_ish = resolve_degree_comparison_rule(AdjectiveCategory.COMP_SYNTHETIC_ISH)
    assert ind_ish == "-іш-"
    assert "суфікса -іш-" in ua_ish
    assert "-ish-" in en_ish

    # Suppletive
    ind_sup, ua_sup, en_sup = resolve_degree_comparison_rule(AdjectiveCategory.COMP_SUPPLETIVE)
    assert "Суплетивна" in ind_sup
    assert "інших основ" in ua_sup
    assert "Suppletive" in en_sup

    # Analytic
    ind_an, ua_an, _ = resolve_degree_comparison_rule(AdjectiveCategory.COMP_ANALYTIC_FORMATION)
    assert "більш / менш" in ind_an
    assert "початковою формою" in ua_an

    # Superlative synthetic
    ind_sup_syn, ua_sup_syn, _ = resolve_degree_comparison_rule(AdjectiveCategory.SUPER_SYNTHETIC_PREFIX)
    assert "най-" in ind_sup_syn
    assert "префікса най-" in ua_sup_syn

    # Superlative emphatic
    ind_emph, ua_emph, _ = resolve_degree_comparison_rule(AdjectiveCategory.SUPER_EMPHATIC_PREFIX)
    assert "якнай-" in ind_emph
    assert "разом" in ua_emph


def test_resolve_soft_declension_instrumental_rule():
    """Verify soft group instrumental ending strictly -ім per Правопис 2019 § 108."""
    ending, ua, en = resolve_soft_declension_instrumental_rule()
    assert ending == "-ім"
    assert "закінчення -ім" in ua
    assert "ending -im" in en


def test_resolve_possessive_suffix_rule():
    """Verify possessive adjective suffix rules per Правопис 2019 § 107."""
    # 1st declension
    suf_i, ua_i, en_i = resolve_possessive_suffix_rule(base_noun_declension=1)
    assert "-ин" in suf_i
    assert "Ольжин" in ua_i
    assert "-yn" in en_i

    # 2nd declension
    suf_ii, ua_ii, en_ii = resolve_possessive_suffix_rule(base_noun_declension=2)
    assert "-ів" in suf_ii
    assert "батьків" in ua_ii
    assert "-iv" in en_ii


def test_resolve_derivational_suffix_mutation_rule():
    """Verify derivational suffix -ськ- mutations per Правопис 2019 § 22."""
    # Velars (г, ж, з) -> -зьк-
    suf_v, ua_v, en_v = resolve_derivational_suffix_mutation_rule("г")
    assert suf_v == "-зьк-"
    assert "празький" in ua_v
    assert "-zk-" in en_v

    # Dentals (к, ч, ц) -> -цьк-
    suf_d, ua_d, en_d = resolve_derivational_suffix_mutation_rule("к")
    assert suf_d == "-цьк-"
    assert "козацький" in ua_d
    assert "-tsk-" in en_d

    # Sibilants (х, ш, с) -> -ськ-
    suf_s, ua_s, en_s = resolve_derivational_suffix_mutation_rule("х")
    assert suf_s == "-ськ-"
    assert "чеський" in ua_s
    assert "-skyi" in en_s


def test_canonical_deck_validity_and_zero_collisions():
    """Verify all canonical cards satisfy schema and collision-free requirements."""
    cards = build_canonical_adjective_cards()
    assert len(cards) >= 60, f"Expected at least 60 cards, found {len(cards)}"

    card_ids: set[str] = set()
    category_counts = Counter(c.category for c in cards)

    # Ensure every defined category has at least 3 cards
    for cat in AdjectiveCategory:
        assert category_counts[cat] >= 3, f"Category {cat} has fewer than 3 cards: {category_counts[cat]}"

    for card in cards:
        assert card.card_id not in card_ids, f"Duplicate card ID: {card.card_id}"
        card_ids.add(card.card_id)

        # Validate card
        errors = validate_adjective_card(card)
        assert not errors, f"Card {card.card_id} failed validation: {errors}"

        # Verify options length and uniqueness
        opts = card.all_options()
        assert len(opts) == 4
        assert len(set(opts)) == 4, f"Collision in options for {card.card_id}: {opts}"
        assert card.correct_answer in opts


def test_balanced_option_distribution():
    """Verify that sha256 deterministic shuffle yields balanced correct answer positions."""
    cards = build_canonical_adjective_cards()
    positions = [card.all_options().index(card.correct_answer) for card in cards]
    counts = Counter(positions)

    # With 74 cards and 4 options, expected count per index is 18.5.
    # Assert balanced distribution within tolerance [10, 28].
    for idx in range(4):
        assert 10 <= counts[idx] <= 28, f"Unbalanced position {idx}: count={counts[idx]} in total {len(cards)}"


def test_deck_export_and_file_parity(tmp_path: Path):
    """Verify deck JSON export produces valid schema and matches committed deck."""
    test_out = tmp_path / "adj_deck.json"
    exported_path = export_adjective_mechanics_deck(test_out)

    assert exported_path.exists()
    with open(exported_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "1.0.0"
    assert data["card_count"] == len(build_canonical_adjective_cards())
    assert len(data["cards"]) == data["card_count"]

    # Verify committed deck parity
    repo_deck_path = Path(__file__).resolve().parents[1] / "registry" / "practice" / "adjective_mechanics_deck.json"
    assert repo_deck_path.exists(), "Committed deck file does not exist"

    with open(repo_deck_path, encoding="utf-8") as f:
        committed_data = json.load(f)

    assert data == committed_data, "Committed deck differs from fresh generator export"


@pytest.mark.skipif(
    not Path("data/vesum.db").exists() or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason="Requires full local data/vesum.db (>1MB); CI omits it",
)
def test_vesum_verification():
    """Verify that VESUM database confirms all target words and validates corruption distractors."""
    cards = build_canonical_adjective_cards()
    report = verify_deck_with_vesum(cards)
    assert report["verified"] is True, f"VESUM verification failed: {report.get('missing_forms', [])}"
    assert report["checked_word_count"] >= 70

    # Extended distractor verification: ensure phonological/morphological corruption
    # distractors are not valid standard words in VESUM.
    dist_report = verify_distractors_with_vesum(cards)
    assert dist_report["verified"] is True, (
        f"Corruption distractors matched valid standard words in VESUM: {dist_report.get('invalid_distractors', [])}"
    )
    assert dist_report["checked_distractor_count"] >= 100
