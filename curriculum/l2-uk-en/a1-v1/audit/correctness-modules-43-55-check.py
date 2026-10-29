"""Recheck the frozen A1 modules 43-55 census, source fixes and V7 payloads."""

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.generate_mdx.converters import yaml_activities_to_jsx
from scripts.yaml_activities import ActivityParser

PAYLOAD = re.compile(r'(?:items|questions|pairs|groups)=\{JSON.parse\(`(.*?)`\)\}')
COMPONENT = re.compile(r'^<(FillIn|Quiz|MatchUp|GroupSort|TrueFalse|ErrorCorrection|Translate|Unjumble|Order|OddOneOut)\b')
HERE = Path(__file__).parent


def decode(value):
    return json.loads(re.sub(r'\\([\\`$])', lambda match: match[1], value))


def activity_rows(activity):
    return activity.get('items', activity.get('pairs', activity.get('groups', [])))


def component_lines(page):
    return [line for line in page.splitlines() if COMPONENT.match(line)]


def payload_item(payload, index, activity_type):
    if activity_type == 'group-sort':
        name, items = list(payload.items())[index]
        return {'name': name, 'items': items}
    return payload[index]


def normalize_words(text):
    return re.findall(r"[\w]+(?:[’ʼ'][\w]+)*", text.lower().replace('’', "'").replace('ʼ', "'"))


def structural(activity):
    kind = activity['type']
    rows = activity_rows(activity)
    if kind == 'fill-in':
        for row in rows:
            assert len(re.findall(r'_{3,}', row['sentence'])) == 1
            assert row['answer'] in row['options']
            assert len(row['options']) == len(set(row['options']))
    elif kind in ('quiz', 'translate'):
        for row in rows:
            assert sum(option.get('correct') is True for option in row['options']) == 1
            texts = [option['text'] for option in row['options']]
            assert len(texts) == len(set(texts))
    elif kind == 'true-false':
        for row in rows:
            assert type(row['answer']) is bool
            for alias in ('correct', 'isTrue'):
                assert alias not in row or row[alias] is row['answer']
    elif kind == 'match-up':
        assert len({row['left'] for row in rows}) == len(rows)
        assert len({row['right'] for row in rows}) == len(rows)
    elif kind == 'group-sort':
        assert len({row['name'] for row in rows}) == len(rows)
        owners = {}
        for group in rows:
            for entry in group['items']:
                assert entry not in owners or owners[entry] == group['name']
                owners[entry] = group['name']
    elif kind == 'order':
        assert sorted(activity['correct_order']) == list(range(len(rows)))
    elif kind == 'unjumble':
        for row in rows:
            words = row['words'] if isinstance(row['words'], list) else row['words'].split('/')
            assert Counter(normalize_words(' '.join(words))) == Counter(normalize_words(row['answer']))
    elif kind == 'error-correction':
        for row in rows:
            assert row['error'] in row['sentence']
            assert '/' not in row['correction']
    elif kind == 'odd-one-out':
        for row in rows:
            assert row['words'].count(row['answer']) == 1
    else:
        raise AssertionError(('unexamined activity type', kind))


def main():
    ledger = json.loads((HERE / 'correctness-modules-43-55-items.json').read_text())
    modules = yaml.safe_load((ROOT / 'curriculum/l2-uk-en/curriculum.yaml').read_text())['levels']['a1-v1']['modules'][42:55]
    assert modules == ledger['modules']
    receipts = {}
    shards = {}
    for line in (HERE / 'correctness-modules-43-55-evidence.jsonl').read_text().splitlines():
        row = json.loads(line)
        digest = row.pop('receipt_sha256')
        actual = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert digest == actual, row['id']
        name = row['shard']
        assert re.fullmatch(r'correctness-modules-43-55-evidence-\d{2}\.jsonl', name)
        if name not in shards:
            shards[name] = [json.loads(value) for value in (HERE / name).read_text().splitlines()]
        result = dict(shards[name][row['line'] - 1])
        result_digest = result.pop('receipt_sha256')
        actual = hashlib.sha256(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert result_digest == actual == row['result_sha256']
        assert result['id'] == row['id'] and row['id'] not in receipts
        receipts[row['id']] = result
    assert sum(len(values) for values in shards.values()) == len(receipts)
    by_id = {row['id']: row for row in ledger['items']}
    assert len(by_id) == len(ledger['items'])
    seen = set()
    counts = Counter(modules=len(modules))
    parser = ActivityParser()
    for slug in modules:
        source = ROOT / f'curriculum/l2-uk-en/a1-v1/{slug}/activities.yaml'
        raw = yaml.safe_load(source.read_text())
        page = (ROOT / f'site/src/content/docs/a1-v1/{slug}.mdx').read_text()
        parts = component_lines(page)
        parsed = parser.parse(source)
        flat = [(section, ai, activity) for section, arr in raw.items() for ai, activity in enumerate(arr)]
        assert len(parts) == len(parsed) == len(flat)
        for (section, ai, activity), parsed_activity, line in zip(flat, parsed, parts, strict=True):
            counts['activities'] += 1
            structural(activity)
            actual = decode(PAYLOAD.search(line)[1])
            canonical = yaml_activities_to_jsx([parsed_activity], is_ukrainian_forced=False)
            expected = decode(PAYLOAD.search(canonical)[1])
            assert '### ' + activity['title'] in page.splitlines()
            for ii, item in enumerate(activity_rows(activity)):
                id = f'{slug}/{section}/{ai}/{ii}'
                saved = by_id[id]
                seen.add(id)
                counts['source_rows'] += 1
                counts['items'] += len(item['items']) if activity['type'] == 'group-sort' else 1
                assert item == saved['after'], (id, 'source changed after census')
                assert saved['verdict'] in ('checked-clean', 'fixed')
                assert saved['rationale'] and saved['sources']
                assert all(ref in receipts for ref in saved['sources']), id
                displayed = payload_item(actual, ii, activity['type'])
                assert displayed == saved['after_payload'], (id, 'published payload changed')
                if saved['verdict'] == 'fixed':
                    counts['fixed_source_rows'] += 1
                    assert displayed == payload_item(expected, ii, activity['type']), (id, 'V7 regeneration mismatch')
                else:
                    assert displayed == saved['before_payload'], (id, 'unrepaired item changed')
        expected_hashes = ledger['file_sha256'][slug]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_hashes['source']
        assert hashlib.sha256(page.encode()).hexdigest() == expected_hashes['page']
    assert seen == set(by_id)
    assert dict(counts) == ledger['counts'], (dict(counts), ledger['counts'])
    print(json.dumps({'result': 'PASS', **counts, 'source_receipts': len(receipts)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
