"""The v2 effective-prompt record contract at the preamble evaluation boundary.

The original v2 checks come from eval/uk_preamble/dispatch.py:168-189.
Historical v2 records retain their submitted-byte contract. New compositions
require both the source brief and the stored effective payload to match.
"""


def condition_problems(conditions, *, expected, same_path):
    problems = []
    if expected.get('schema_version') != 2:
        problems.append('v2 task cannot satisfy a legacy composition')
    original = expected.get('source_prompt_sha256', expected['effective_prompt_sha256'])
    for key in ('prompt_sha256', 'stored_prompt_sha256'):
        if conditions.get(key) != original:
            problems.append(f'{key} differs from the exact submitted prompt')
    for key in ('cwd', 'worktree_path'):
        if not same_path(conditions.get(key), expected[key]):
            problems.append(f'worker {key} differs from the frozen frame')
    if conditions.get('mode') != 'read-only':
        problems.append('mode is not read-only')
    if conditions.get('research') is not None:
        problems.append('research context was injected')
    modern = 'source_prompt_sha256' in expected
    reported = conditions.get('effective_prompt_sha256') is not None or conditions.get('prompt_blocks') is not None
    if (modern or reported) and (
        conditions.get('effective_prompt_sha256') != expected['effective_prompt_sha256']
        or conditions.get('prompt_blocks') != expected['prompt_blocks']
        or (modern and conditions.get('stored_effective_prompt_sha256') != expected['effective_prompt_sha256'])
    ):
        problems.append('v2 effective prompt composition differs from the frozen frame')
    return problems
