# #9160 — removal-only practice meaning containment, round 3

Evaluation build on `codex/fix-9160-contain`; no release was published. This transform uses the same frozen 6,217-row release as round 2. Every retained English display requires a direct per-lemma bilingual source match. A Balla English→Ukrainian mapping to another lemma vetoes it; Balla example translations do not count as headword mappings. Qualified Atlas senses remain literal when their independent source supports the same qualified text. No Ukrainian display is derived or replaced.

## Frozen inputs and exact transform

| Input/code | SHA-256 |
| --- | --- |
| Release gzip | `d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19` |
| Atlas database | `fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca` |
| Sources database | `7868ce16f3cc8280676f08f436b94563ba20e3e7909ad236f06c2bdce19baa7b` |
| Generator | `f5fafb5760c6e544650babadb2109f5508e98dbe6b1aa1e2d7ced349bef48009` |
| Containment | `f56ebfab864e8e534963ee22d20bdef50e0d6a8c5eb1f101b408667547022093` |
| Reproducer | `181e39adb4e4049fe9ba6f42b487483edc778d3e145f4ad1cfb5ee256f4e10ed` |

Run from this dispatch worktree; outputs are ignored local evaluation files:

```bash
mkdir -p batch_state/meaning-9160-r3
gh release download atlas-practice-deck -R learn-ukrainian/learn-ukrainian.github.io -p lexicon-practice-deck-atlas-practice-v1-f1e1cf95470ce319.json.gz -D batch_state/meaning-9160-r3
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.audit.reproduce_meaning_9160 --package batch_state/meaning-9160-r3/lexicon-practice-deck-atlas-practice-v1-f1e1cf95470ce319.json.gz --atlas-db /home/ops/learn-ukrainian/data/atlas.db --sources-db /home/ops/learn-ukrainian/data/sources.db --output batch_state/meaning-9160-r3/shards
```

The reproducer verifies all three frozen input hashes, writes the 55 package files, and checks size budgets. The output is an evaluation artifact, not a published deck.

## Meaning admission versus round 2

| Level | Frozen rows | R2 English | R3 English | Δ English | R2 withheld | R3 withheld | Δ withheld |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | 1496 | 1167 | 890 | -277 | 329 | 606 | +277 |
| A2 | 1511 | 1158 | 823 | -335 | 353 | 688 | +335 |
| B1 | 1505 | 696 | 512 | -184 | 809 | 993 | +184 |
| B2 | 1040 | 643 | 445 | -198 | 397 | 595 | +198 |
| C1 | 665 | 253 | 162 | -91 | 412 | 503 | +91 |
| **Total** | **6217** | **3917** | **2832** | **-1085** | **2300** | **3385** | **+1085** |

All retained meanings are English; retained Ukrainian meanings remain 0 at every level. The withheld count includes rows whose non-meaning drills remain available.

## Mode eligibility versus round 2

| Level | Mode | Release flags | R2 retained | R3 retained | Δ retained | R2 withheld | R3 withheld |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | flashcards | 1496 | 1167 | 890 | -277 | 329 | 606 |
| A1 | matching | 1362 | 1064 | 793 | -271 | 298 | 569 |
| A1 | choice | 1362 | 1064 | 793 | -271 | 298 | 569 |
| A1 | synonym | 0 | 0 | 0 | +0 | 0 | 0 |
| A2 | flashcards | 1511 | 1158 | 823 | -335 | 353 | 688 |
| A2 | matching | 1340 | 1046 | 773 | -273 | 294 | 567 |
| A2 | choice | 1340 | 1046 | 773 | -273 | 294 | 567 |
| A2 | synonym | 0 | 0 | 0 | +0 | 0 | 0 |
| B1 | flashcards | 1505 | 696 | 512 | -184 | 809 | 993 |
| B1 | matching | 652 | 593 | 458 | -135 | 59 | 194 |
| B1 | choice | 652 | 593 | 458 | -135 | 59 | 194 |
| B1 | synonym | 0 | 0 | 0 | +0 | 0 | 0 |
| B2 | flashcards | 1040 | 643 | 445 | -198 | 397 | 595 |
| B2 | matching | 779 | 550 | 403 | -147 | 229 | 376 |
| B2 | choice | 779 | 550 | 403 | -147 | 229 | 376 |
| B2 | synonym | 0 | 0 | 0 | +0 | 0 | 0 |
| C1 | flashcards | 665 | 253 | 162 | -91 | 412 | 503 |
| C1 | matching | 511 | 217 | 144 | -73 | 294 | 367 |
| C1 | choice | 511 | 217 | 144 | -73 | 294 | 367 |
| C1 | synonym | 0 | 0 | 0 | +0 | 0 | 0 |

These are index flags in the local evaluation shards, not a live-session availability claim. Non-meaning mode eligibility is unchanged.

## Qualifier and fragment audit

The 237 load-bearing stripped-qualifier rows split into **97 retained with a literal sense qualifier** and **140 withheld**. Six further rows with a qualified Atlas part selected a separate supported unqualified Atlas alternative; they are reported separately because that qualifier was not load-bearing.

Regression outcomes in the frozen rows: `дно` → `bed (of a river)`; `ураження`, `електронний`, `музичний`, `тікати`, and `слізний` → withheld. The five named Cyrillic cross-reference fragments and `ківі` (`kiwi 2`) are withheld. `увесь` and `задовольнятися` remain withheld; the optional mechanical recovery levers do not override independent-support admission.

## Withheld reasons

| Level | Reason | R2 | R3 | Δ |
| --- | --- | ---: | ---: | ---: |
| A1 | `dictionary_fragment` | 2 | 2 | +0 |
| A1 | `example_quotation` | 6 | 0 | -6 |
| A1 | `parenthesized_citation` | 2 | 2 | +0 |
| A1 | `reviewed_wrong_sense` | 1 | 1 | +0 |
| A1 | `unattributed_english` | 178 | 33 | -145 |
| A1 | `unbound_english_sense` | 82 | 77 | -5 |
| A1 | `unsupported_english_source` | 58 | 58 | +0 |
| A1 | `unsupported_independent_head` | 0 | 433 | +433 |
| A2 | `dictionary_fragment` | 1 | 2 | +1 |
| A2 | `example_quotation` | 1 | 0 | -1 |
| A2 | `parenthesized_citation` | 3 | 4 | +1 |
| A2 | `reviewed_wrong_sense` | 26 | 26 | +0 |
| A2 | `unattributed_english` | 159 | 35 | -124 |
| A2 | `unbound_english_sense` | 93 | 92 | -1 |
| A2 | `unbound_ukrainian` | 1 | 1 | +0 |
| A2 | `unsupported_english_source` | 69 | 69 | +0 |
| A2 | `unsupported_independent_head` | 0 | 459 | +459 |
| B1 | `dated_citation` | 408 | 408 | +0 |
| B1 | `dictionary_fragment` | 109 | 110 | +1 |
| B1 | `example_quotation` | 26 | 26 | +0 |
| B1 | `parenthesized_citation` | 104 | 104 | +0 |
| B1 | `reviewed_wrong_sense` | 18 | 18 | +0 |
| B1 | `same_word_sum11` | 27 | 27 | +0 |
| B1 | `unattributed_english` | 59 | 13 | -46 |
| B1 | `unbound_english_sense` | 0 | 14 | +14 |
| B1 | `unbound_ukrainian` | 47 | 47 | +0 |
| B1 | `unsupported_english_source` | 11 | 10 | -1 |
| B1 | `unsupported_independent_head` | 0 | 216 | +216 |
| B2 | `dated_citation` | 13 | 13 | +0 |
| B2 | `dictionary_fragment` | 24 | 27 | +3 |
| B2 | `example_quotation` | 2 | 1 | -1 |
| B2 | `parenthesized_citation` | 27 | 27 | +0 |
| B2 | `reviewed_wrong_sense` | 12 | 12 | +0 |
| B2 | `same_word_sum11` | 23 | 23 | +0 |
| B2 | `unattributed_english` | 153 | 32 | -121 |
| B2 | `unbound_english_sense` | 0 | 12 | +12 |
| B2 | `unbound_ukrainian` | 42 | 42 | +0 |
| B2 | `unsupported_english_source` | 101 | 101 | +0 |
| B2 | `unsupported_independent_head` | 0 | 305 | +305 |
| C1 | `dated_citation` | 3 | 3 | +0 |
| C1 | `dictionary_fragment` | 13 | 13 | +0 |
| C1 | `example_quotation` | 2 | 2 | +0 |
| C1 | `parenthesized_citation` | 53 | 53 | +0 |
| C1 | `reviewed_wrong_sense` | 8 | 8 | +0 |
| C1 | `same_word_sum11` | 11 | 11 | +0 |
| C1 | `unattributed_english` | 112 | 26 | -86 |
| C1 | `unbound_english_sense` | 0 | 6 | +6 |
| C1 | `unbound_ukrainian` | 13 | 13 | +0 |
| C1 | `unsupported_english_source` | 197 | 197 | +0 |
| C1 | `unsupported_independent_head` | 0 | 171 | +171 |

## Output shard hashes

| File | SHA-256 |
| --- | --- |
| `practice-index.A1.json` | `3d075500051d1d3f2affe95b23801707a1961aa6f4c09af8871aa9ded3d42506` |
| `practice-index.A2.json` | `a8e390954564636a08fd1e32d7d7c805bdb14442dcb5ea6cdb2dcb070340e9bc` |
| `practice-index.B1.json` | `0f382e51d9310c936006a320a6a5814009ed5a3b53846cf6d5b10b6fb6a6b877` |
| `practice-index.B2.json` | `11bf7c0fb930429e8b2660e82e22a68f72b0db3a92b74b266694ed1ada4dceaf` |
| `practice-index.C1.json` | `15fee42a161814858abad3e7a4d57f6e9fd44c2f56f745b061358d3013ded047` |
| `practice-lexemes.A1.json` | `88b264dd4390319b34cf230edb21c515c8e3d7b8ac8808641cb9f308a824fd0e` |
| `practice-lexemes.A2.json` | `d66e348a6af5b011441c5c0003084511039b1aba1591d4f353f2f1b666a1fd41` |
| `practice-lexemes.B1.json` | `4ebc0c29cee56b0cacfa4dae9d779ec80c60874b51cfe7dac949e1740622bbf1` |
| `practice-lexemes.B2.json` | `4c71202bb9fa493af2a94f28fc905c8b1951a3f4b84536d3291a1ba8c223d8ce` |
| `practice-lexemes.C1.json` | `470f9d81a9301f88e0f762b2e2080ab23de86186a935f62ccba8944befae699d` |
| `practice-synonym.A1.json` | `a941e7dafa1a0f136ed0f97bd98548a4e3786b34cb727c68cec4bdb092462d7c` |
| `practice-synonym.A2.json` | `9701ccb57d7a20e327ebae341776499883cc3b33cfcf389d9535b24ded5cabad` |
| `practice-synonym.B1.json` | `4745abff6ca1f318c6ea37161f1120ba14134e4b0db0a0a463663701da38494b` |
| `practice-synonym.B2.json` | `e56430a67078cb765380c3e0409e8a29314b2078980306da0e156608e7c55ee5` |
| `practice-synonym.C1.json` | `7beb5a2f9db4445e111fb7bae03579b6532aacd49ed208405b61601a6d30735d` |

## Residual and disposition

Round-2 independent evaluation found 1 wrong sense in 150 held-out rows and six fragments. This round fixes those named class regressions in the frozen transform. A fresh independent held-out semantic evaluation of the round-3 head has not yet been performed; this report does not certify publication or issue closure. The frozen source snapshot contains further unsupported heads, now withheld by the class rule.
