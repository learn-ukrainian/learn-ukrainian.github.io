# #9160 — practice meaning containment, round 4

Evaluation build on `codex/fix-9160-contain`; no release was published. The transform uses the same frozen 6,217-row package and source snapshots as round 3. It changes admission of existing English source text only. Parenthesized qualifiers stay atomic, cross-reference stubs are rejected, and a reverse Balla mapping is read alongside direct per-lemma forward evidence and recorded lemma forms. English heads that conflict with the first learner-English sense are withheld. No Ukrainian display was derived or replaced.

## Frozen inputs and exact transform

| Input/code | SHA-256 |
| --- | --- |
| Release gzip | `d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19` |
| Atlas database | `fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca` |
| Sources database | `7868ce16f3cc8280676f08f436b94563ba20e3e7909ad236f06c2bdce19baa7b` |
| Generator | `8bf43a2442baf9a9315255de3298e096c2fdf37781dec190f1891f32bac3e322` |
| Containment | `7f39bc01886cae3dbb15e52b6f46d2726981b597dede0a7f489ed9245123bb64` |
| Reproducer | `181e39adb4e4049fe9ba6f42b487483edc778d3e145f4ad1cfb5ee256f4e10ed` |

Run inside the dispatch worktree. The package download and generated shards live in ignored local `batch_state/`; they are evaluation files, not publication assets.

```bash
mkdir -p batch_state/meaning-9160-r4
gh release download atlas-practice-deck -R learn-ukrainian/learn-ukrainian.github.io -p lexicon-practice-deck-atlas-practice-v1-f1e1cf95470ce319.json.gz -D batch_state/meaning-9160-r4
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.audit.reproduce_meaning_9160 --package batch_state/meaning-9160-r4/lexicon-practice-deck-atlas-practice-v1-f1e1cf95470ce319.json.gz --atlas-db /home/ops/learn-ukrainian/data/atlas.db --sources-db /home/ops/learn-ukrainian/data/sources.db --output batch_state/meaning-9160-r4/shards
```

The reproducer verified all three frozen input hashes, wrote the 55 package files, and checked size budgets.

## Meaning admission versus round 3

| Level | Frozen rows | R3 English | R4 English | Change | R3 withheld | R4 withheld | Change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | 1,496 | 890 | 1,022 | +132 | 606 | 474 | -132 |
| A2 | 1,511 | 823 | 959 | +136 | 688 | 552 | -136 |
| B1 | 1,505 | 512 | 591 | +79 | 993 | 914 | -79 |
| B2 | 1,040 | 445 | 532 | +87 | 595 | 508 | -87 |
| C1 | 665 | 162 | 192 | +30 | 503 | 473 | -30 |
| **Total** | **6,217** | **2,832** | **3,296** | **+464** | **3,385** | **2,921** | **-464** |

All retained meanings are English; retained Ukrainian meanings remain 0. Withheld rows retain their independent non-meaning drills.

## Mode eligibility versus round 3

| Level | Mode | Frozen flags | R3 retained | R4 retained | Change | R3 withheld | R4 withheld |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | flashcards | 1,496 | 890 | 1,022 | +132 | 606 | 474 |
| A1 | matching | 1,362 | 793 | 921 | +128 | 569 | 441 |
| A1 | choice | 1,362 | 793 | 921 | +128 | 569 | 441 |
| A1 | synonym | 0 | 0 | 0 | 0 | 0 | 0 |
| A2 | flashcards | 1,511 | 823 | 959 | +136 | 688 | 552 |
| A2 | matching | 1,340 | 773 | 906 | +133 | 567 | 434 |
| A2 | choice | 1,340 | 773 | 906 | +133 | 567 | 434 |
| A2 | synonym | 0 | 0 | 0 | 0 | 0 | 0 |
| B1 | flashcards | 1,505 | 512 | 591 | +79 | 993 | 914 |
| B1 | matching | 652 | 458 | 529 | +71 | 194 | 123 |
| B1 | choice | 652 | 458 | 529 | +71 | 194 | 123 |
| B1 | synonym | 0 | 0 | 0 | 0 | 0 | 0 |
| B2 | flashcards | 1,040 | 445 | 532 | +87 | 595 | 508 |
| B2 | matching | 779 | 403 | 486 | +83 | 376 | 293 |
| B2 | choice | 779 | 403 | 486 | +83 | 376 | 293 |
| B2 | synonym | 0 | 0 | 0 | 0 | 0 | 0 |
| C1 | flashcards | 665 | 162 | 192 | +30 | 503 | 473 |
| C1 | matching | 511 | 144 | 172 | +28 | 367 | 339 |
| C1 | choice | 511 | 144 | 172 | +28 | 367 | 339 |
| C1 | synonym | 0 | 0 | 0 | 0 | 0 | 0 |

These are local evaluation index flags. No live-session availability or published-deck state is claimed.

## Class checks and residual

The top-level splitter leaves qualifier commas and semicolons intact and handles top-level slash alternatives. The four round-3 comma-piece cases are withheld; `якнайкраще`'s mixed-script cross-reference is withheld. The full Atlas translation vocabulary scan informed the cross-reference prefixes in the fragment filter, including `female equivalent of`, `endearing form of`, `a specific spelling of`, and `alternative letter-case form of`.

The 21 correct heads named in the round-3 withholding audit now appear in the local transform; `ураження` remains withheld, and the Atlas head `впливати → to swim in` is withheld. In the 6,217 output rows, `gloss` equals `glossClean` everywhere, 0 withheld rows retain a meaning mode, 0 retained displays contain Cyrillic, and 0 retained displays start with the cross-reference stub prefixes checked in the audit. The `unsupported_independent_head` reason count fell from 1,584 to 908; this reason-code change is **not** the marginal effect of rule (b), because rows may still fail another admission rule.

The round-3 independent held-out draw found 3 fragment displays in 150 and 21 over-withheld rows in 60. Round 4 has deterministic regression and whole-artifact checks, but has not received a fresh independent held-out semantic evaluation. This report does not certify publication, issue closure, or live deck replacement.

## Output shard hashes

| File | SHA-256 |
| --- | --- |
| `practice-index.A1.json` | `ebbf4e70e147425efc68153d1ec7dd95d5612f5afcaad03533766a97ea55ade4` |
| `practice-index.A2.json` | `759befe992e576f9633f8d5d723d83050a7861e954b68d3024be87a63b0f175a` |
| `practice-index.B1.json` | `e5c2a535a2fa2b796ed11ae7ec7b61c767ed3d0bd8f9ca8921a1fe40c0608c9f` |
| `practice-index.B2.json` | `8f43a86e8257ff3eb7aaa6642d3052fb9580b39505e1a1caf631dc30e8d6a394` |
| `practice-index.C1.json` | `22946d7fbd208f7fe8b64de6dbcb2a3b47a154aba830ad46d7b32e3739b646b1` |
| `practice-lexemes.A1.json` | `7df3da18c0a4c34a0a371ba140fa847b883ecdbc880b7b43c5759a62d663a327` |
| `practice-lexemes.A2.json` | `d106de6b3102e27cfcec245315523f8fd02ac40636bc97cb658a7dd75db91329` |
| `practice-lexemes.B1.json` | `5690f8e421d033369a22ade621e18f7d4ddb7bf5ac70ac0fca3e337d36303566` |
| `practice-lexemes.B2.json` | `1e9777240a38df5c37460731b10384fb2550b9e5a1d822d92c0fd6f1d277de5f` |
| `practice-lexemes.C1.json` | `91839c11cdfa48b8bc02073ec9f289427e6dd29be26a5c14b8646dc62e792d2f` |
| `practice-synonym.A1.json` | `a941e7dafa1a0f136ed0f97bd98548a4e3786b34cb727c68cec4bdb092462d7c` |
| `practice-synonym.A2.json` | `9701ccb57d7a20e327ebae341776499883cc3b33cfcf389d9535b24ded5cabad` |
| `practice-synonym.B1.json` | `4745abff6ca1f318c6ea37161f1120ba14134e4b0db0a0a463663701da38494b` |
| `practice-synonym.B2.json` | `e56430a67078cb765380c3e0409e8a29314b2078980306da0e156608e7c55ee5` |
| `practice-synonym.C1.json` | `7beb5a2f9db4445e111fb7bae03579b6532aacd49ed208405b61601a6d30735d` |
