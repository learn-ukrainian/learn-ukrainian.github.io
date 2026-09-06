"""Offline admission at both factory emit paths; fixture receipts only."""
from __future__ import annotations

import json

import pytest

from scripts.audit import generate_practice_deck as factory
from scripts.practice.creation_review import (
    DEFAULT_LEDGER,
    CreationReview,
    frame_identity,
    frame_sha,
    heritage_source,
)
from tests.test_generate_practice_deck import (
    ALLOWLIST,
    CLOZE_SOURCES,
    VESUM,
    _fixture_heritage_pair,
    _fixture_lexemes,
)


@pytest.fixture(params=['heritage', 'cloze'])
def frame_case(request):
    lexemes = _fixture_lexemes()
    if request.param == 'heritage':
        pair = _fixture_heritage_pair()
        frame = pair['frames'][0]
        pair['frames'] = [frame]
        args = ('heritage', frame['sentence_with_slot'], frame['answer_form'], frame['calque_form'])
        source = heritage_source(pair, frame)
        def emit(policy):
            return factory._build_heritage_items(pair, lexemes[0], lexemes, 'fixture', creation_review=policy)
        def drift():
            frame['origin'] += '-changed'
    else:
        row = factory.read_cloze_sources(CLOZE_SOURCES)[0]
        lexeme = next(x for x in lexemes if x['lemmaId'] == row['lemmaId'])
        args = ('cloze', row['sentence'], row['form'], lexeme['lemmaPlain'])
        source = row
        def emit(policy):
            return factory._build_cloze_items(
                lexeme, [row], factory.ReviewedSourceAllowlist.from_path(ALLOWLIST),
                factory.JsonVesumVerifier.from_path(VESUM), 'fixture', creation_review=policy,
            )
        def drift():
            row['clozeEn'] += ' Changed.'
    return args, source, emit, drift


def receipt(args, source):
    return {'agent': 'agy', 'resolved_model': 'gemini-fixture-model', 'verdict': 'pass',
            'reviewed_at': '2026-09-06T12:00:00Z', 'frame_sha': frame_sha(*args, source)}


def test_grandfathered_fixture_emits(frame_case):
    args, _, emit, _ = frame_case
    assert len(emit(CreationReview(frozenset({frame_identity(*args)})))) == 1


def test_new_frame_without_receipt_does_not_emit(frame_case, capsys):
    args, _, emit, _ = frame_case
    assert emit(CreationReview()) == []
    assert frame_identity(*args) in capsys.readouterr().err


@pytest.mark.parametrize('verdict,expected', [('pass', 1), ('fail', 0)])
def test_new_frame_receipt_controls_emit(frame_case, tmp_path, verdict, expected):
    args, source, emit, _ = frame_case
    review = receipt(args, source)
    review['verdict'] = verdict
    path = tmp_path / 'ledger.json'
    path.write_text(json.dumps({'schema_version': 1, 'grandfathered': [],
                               'receipts': {frame_identity(*args): review}}))
    assert len(emit(CreationReview.from_path(path))) == expected


def test_frame_payload_drift_does_not_emit(frame_case):
    args, source, emit, drift = frame_case
    policy = CreationReview(receipts={frame_identity(*args): receipt(args, source)})
    assert len(emit(policy)) == 1
    drift()
    assert emit(policy) == []


@pytest.mark.parametrize('field,value', [
    ('agent', 'codex'), ('agent', None), ('resolved_model', ''),
    ('resolved_model', 'gpt-fixture'), ('verdict', 'PASS'),
    ('reviewed_at', 'bad'), ('reviewed_at', '2026-09-06'),
    ('reviewed_at', '2026-09-06T12:00:00'), ('frame_sha', '0' * 64),
])
def test_malformed_receipts_fail_closed(frame_case, field, value):
    args, source, emit, _ = frame_case
    review = receipt(args, source)
    review[field] = value
    assert emit(CreationReview(receipts={frame_identity(*args): review})) == []


@pytest.mark.parametrize('payload', ['', 'null', '[]', '{}', '{"schema_version":1,"grandfathered":[],"receipts":{},"receipts":{}}'])
def test_invalid_ledger_fails_closed(tmp_path, payload):
    path = tmp_path / 'ledger.json'
    path.write_text(payload)
    policy = CreationReview.from_path(path)
    assert not policy.grandfathered and not policy.receipts


def test_missing_ledger_fails_closed(tmp_path):
    assert CreationReview.from_path(tmp_path / 'missing.json') == CreationReview()


def test_default_builders_enforce_creation_gate(frame_case):
    _, _, emit, _ = frame_case
    assert emit(None) == []  # synthetic frames are absent from the production baseline


def test_resolved_answer_drift_cannot_reuse_receipt():
    args = ('cloze', 'Fixture ___', 'answer', 'lemma')
    source = {'sentence': args[1]}  # derived form absent in source
    policy = CreationReview(receipts={frame_identity(*args): receipt(args, source)})
    assert policy.allows(*args, source)
    assert not policy.allows('cloze', args[1], 'changed answer', args[3], source)


def test_identity_preserves_prompt_answer_stress_and_kind():
    base = frame_identity('cloze', 'Prompt ___', 'answer', 'lemma')
    assert base != frame_identity('cloze', 'Prompt ___', 'answe\u0301r', 'lemma')
    assert base != frame_identity('heritage', 'Prompt ___', 'answer', 'lemma')


def test_current_source_identities_are_grandfathered():
    policy = CreationReview.from_path(DEFAULT_LEDGER)
    pairs = factory.read_heritage_pairs(factory.DEFAULT_HERITAGE_PAIRS)
    rows = factory.read_cloze_sources(factory.DEFAULT_CLOZE_SOURCES) + factory.read_sentence_inventory(factory.DEFAULT_SENTENCE_INVENTORY)
    identities = set()
    for pair in pairs:
        for frame in pair.get('frames', []):
            args = ('heritage', frame['sentence_with_slot'].strip(), frame['answer_form'].strip(), frame['calque_form'].strip())
            identities.add(frame_identity(*args))
            assert policy.allows(*args, heritage_source(pair, frame))
    for row in rows:
        args = ('cloze', row['sentence'].strip(), row['form'].strip(), factory._plain(row['lemma']))
        identities.add(frame_identity(*args))
        assert policy.allows(*args, row)
    assert identities == policy.grandfathered


def test_ledger_changes_deck_version_without_changing_sampling_inputs():
    from scripts.practice_deck.io import compute_deck_version
    args = ([], [], [], {}, [], 1)
    assert compute_deck_version(*args, creation_review={'receipts': {}}) != compute_deck_version(
        *args, creation_review={'receipts': {'new': {'verdict': 'pass'}}})
