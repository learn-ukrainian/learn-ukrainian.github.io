"""Synthetic layout regressions; the owned PDF is never a CI dependency."""

import json
import sqlite3
from collections import Counter
from pathlib import Path

import pytest
import yaml

from scripts.ingest import build_ohoiko_a1_reference as build
from scripts.ingest import prove_ohoiko_a1_reference as proof


def span(text, bold=True, *, x=46, y=100, size=9):
    return {'text': text, 'font': 'Arial-BoldMT' if bold else 'ArialMT', 'size': size,
            'bbox': (x, y, x + len(text), y + 12),
            'chars': [{'c': c, 'bbox': (x + i, y, x + i + 1, y + 12)} for i, c in enumerate(text)]}


def line(*spans):
    return {'spans': list(spans), 'bbox': spans[0]['bbox']}


@pytest.mark.parametrize('spans,heads,positions', [
    ([span('швидка́'), span(' ', False), span('допомо́га'), span(', ж., ', False)], ['швидка́ допомо́га'], ['noun']),
    ([span('цьо́го'), span(' ', False), span('ра́зу'), span(', присл., ', False)], ['цьо́го ра́зу'], ['adv']),
    ([span('коха́ний'), span(', ч., ', False), span('коха́на'), span(', ж., ', False)], ['коха́ний', 'коха́на'], ['noun', 'noun']),
    ([span('три́дцять'), span(' ', False), span('чоти́ри'), span(', ', False)], ['три́дцять чоти́ри'], ['unlabelled']),
    ([span('Львів'), span(',', False), span(' '), span('ч., ', False)], ['Львів'], ['noun']),
    ([span('сільни́ця'), span(', ', False), span('сільни́чка'), span(', ж., ', False)], ['сільни́ця, сільни́чка'], ['noun']),
])
def test_pos_boundaries_and_independent_label_offsets(spans, heads, positions):
    assert build.glossary_groups(spans) == list(zip(heads, positions, strict=True))
    independently = proof.line_entries(line(*spans), 200)
    assert independently == [proof.expected(h, p, 200) for h, p in zip(heads, positions, strict=True)]


@pytest.mark.parametrize('head,pos,lemma,variants,kind', [
    ('вчо́ра, учо́ра', 'adv', 'вчора', ['учора'], 'word'),
    ('Бува́й! Бува́йте!', 'unlabelled', 'бувай', ['бувайте'], 'word'),
    ('Що (в те́бе) ново́го?', 'unlabelled', 'Що нового?', ['Що в тебе нового?'], 'phrase'),
    ('провести́ час (ми провели́ час)', 'verb', 'провести час', ['провели час'], 'phrase'),
    ('мій (моя, моє, мої)', 'unlabelled', 'мій', ['моя', 'моє', 'мої'], 'word'),
    ('сумка (сумочка)', 'noun', 'сумка', ['сумка сумочка'], 'word'),
    ('чита́ти (кни́гу)', 'verb', 'читати', [], 'word'),
    ('(чи) так', 'unlabelled', 'так', ['чи так'], 'word'),
])
def test_lexical_notation(head, pos, lemma, variants, kind):
    row = build.headword_fields(head, pos, 200)
    assert row['lemma'] == lemma and row.get('variants', []) == variants and row['kind'] == kind
    assert proof.signature(row) == proof.expected(head, pos, 200)
    if lemma == 'бувай':
        assert row['stressed'] == 'Бува́й!' and row['pos'] == 'intj'
    if lemma == 'провести час':
        assert {'form': 'провели'} in row['tokens']
        assert {'form': 'ми'} not in row['tokens']


def test_invalid_notation_and_unicode():
    with pytest.raises(ValueError, match='parentheses'):
        build.headword_fields('слово (', 'noun', 200)
    assert build.lexical('  cáм   é  ', unstress=True) == proof.clean('  cáм   é  ', True) == 'сам е'


def database(tmp_path):
    path = tmp_path / 'vesum.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)')
        conn.executemany('INSERT INTO forms VALUES (?,?,?,?)', [
            ('ми', 'ми', 'noun', 'noun:pron'), ('був', 'бути', 'verb', 'verb:past'),
            ('Львів', 'Львів', 'noun', 'noun:prop:geo'), ('час', 'час', 'noun', 'noun'),
        ])
    return path


def test_read_only_form_attestation_is_lemma_bound(tmp_path):
    path = database(tmp_path)
    before = path.read_bytes()
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as conn:
        for lemma, positions, state in [('ми', ['noun'], 'found'), ('був', [], 'found'), ('такос', [], 'missing')]:
            row = build.headword_fields(lemma, 'unlabelled', 200)
            build.attest(row, conn)
            assert row['vesum'] == state and row['vesum_pos'] == positions
        row = build.headword_fields('Львів', 'noun', 200)
        build.attest(row, conn)
        assert row['vesum_tags'] == ['noun:prop:geo']
        row = build.headword_fields('вільний час', 'noun', 200)
        build.attest(row, conn)
        assert [t['vesum'] for t in row['tokens']] == ['missing', 'found']
    assert path.read_bytes() == before


class Document:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __getitem__(self, i):
        lines = self.pages.get(i + 1, [])
        class Page:
            def get_text(self, mode):
                return {'blocks': [{'lines': lines}]}
        return Page()


def test_both_pdf_extractors_cover_layout_without_a_private_fixture(tmp_path, monkeypatch):
    doc = Document({200: [line(span('швидка́'), span(' ', False), span('допомо́га'), span(', ж., ', False))],
                    217: [line(span('бажа́ти', x=78, y=393, size=10)),
                          line(span('побажа́ти,', x=274, y=393, size=10)),
                          line(span('проза', x=57, y=260, size=10))],
                    223: [line(span('фотографува́тися', x=78, y=600, size=10)),
                          line(span('сфотографува́тися', x=270, y=600, size=10))]})
    monkeypatch.setattr(build.pymupdf, 'open', lambda _: doc)
    rows, accounting = build.extract(Path('unused'), database(tmp_path))
    independently, pages = proof.pdf_entries(Path('unused'))
    assert Counter(map(proof.signature, rows)) == Counter(independently)
    assert len(rows) == 5 and len(accounting) == 3
    assert pages[217] == {'entry_lines': 2, 'entries': 2, 'non_entry_lines': 1}
    assert rows[1]['pair'] == rows[2]['pair'] == 'vp-001'
    assert rows[3]['pair'] == rows[4]['pair'] == 'vp-002'
    doc.pages[217].append(line(span('написа́ти', x=270, y=780, size=10)))
    with pytest.raises(ValueError, match='unmapped'):
        build.extract(Path('unused'), tmp_path / 'vesum.db')


def inventory(tmp_path, rows):
    path = tmp_path / 'inventory.yaml'
    path.write_text(yaml.safe_dump({'sources': [{'headwords': rows}]}, allow_unicode=True))
    return path


def test_build_cli_retains_metadata_and_errors(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'inventory.yaml'
    path.write_text('sources: [{title: Authored, headwords: []}]')
    row = build.headword_fields('ми', 'unlabelled', 200)
    monkeypatch.setattr(build, 'extract', lambda *args: ([row], []))
    args = ['--inventory', str(path), '--pdf', 'unused', '--vesum-db', 'unused']
    assert build.main(args) == 0
    assert yaml.safe_load(path.read_text())['sources'][0] == {'title': 'Authored', 'headwords': [row]}
    assert 'Generated 1 entries' in capsys.readouterr().out
    path.unlink()
    assert build.main(args) == 1


def test_proof_comparison_detects_boundary_metadata_and_multiplicity_drift(tmp_path, monkeypatch):
    rows = [build.headword_fields('слово', 'noun', page) for page in range(200, 224) for _ in range(5)]
    rows[1] = build.headword_fields('два слова', 'noun', 200)
    rows[-1] = build.headword_fields('читати', 'verb', 223, 'vp-001')
    independently = list(map(proof.signature, rows))
    monkeypatch.setattr(proof, 'pdf_entries', lambda _: (independently, {}))
    path = inventory(tmp_path, rows)
    result = proof.compare(Path('unused'), path)
    assert result['unexplained_differences'] == 0 and result['sample_matches'] == 100
    assert len({r['page'] for r in result['sample']}) == 24
    assert proof.main(['--pdf', 'unused', '--inventory', str(path)]) == 0
    rows[0].update(pos='adv', stressed='сло́во', variants=['слова'])
    rows.append(rows[-1])
    path = inventory(tmp_path, rows)
    result = proof.compare(Path('unused'), path)
    assert result['unexplained_differences'] == 3
    assert proof.main(['--pdf', 'unused', '--inventory', str(path)]) == 1


def test_proof_cli_input_error_is_typed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(proof, 'compare', lambda *args: (_ for _ in ()).throw(ValueError('private details')))
    assert proof.main(['--pdf', 'unused', '--inventory', str(tmp_path / 'missing')]) == 2
    assert json.loads(capsys.readouterr().out) == {'error': 'ValueError'}
