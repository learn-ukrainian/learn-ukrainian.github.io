# Dual-Mode Design Tokens

This document is the source of truth for the design-layer semantic tokens used
by Learn Ukrainian light and dark themes.

## Semantic Tokens

| Token | Light | Dark |
| --- | --- | --- |
| `--lu-bg` | `#ffffff` | `#0f0f1a` |
| `--lu-surface` | `#ffffff` | `#242526` |
| `--lu-surface-muted` | `#f8f9fa` | `#1a1a2e` |
| `--lu-border` | `#ebeced` | `#303846` |
| `--lu-text` | `#1c1e21` | `#e3e3e3` |
| `--lu-text-muted` | `#6b6b6b` | `#989898` |
| `--lu-primary` | `#0057B7` | `#5B9BD5` |
| `--lu-accent` | `#FFD700` | `#FFD700` |
| `--lu-on-accent` | `#1c1e21` | `#1c1e21` |
| `--lu-state-active` | `rgba(0,87,183,.08)` | `rgba(91,155,213,.22)` |
| `--lu-state-correct-bg` | `rgba(46,125,50,.08)` | `rgba(46,160,70,.26)` |
| `--lu-state-correct-fg` | `#2E7D32` | `#81C995` |
| `--lu-state-wrong-bg` | `rgba(198,40,40,.08)` | `rgba(210,70,70,.26)` |
| `--lu-state-wrong-fg` | `#C62828` | `#F28B82` |
| `--lu-state-missed` | `rgba(251,188,4,.15)` | `rgba(251,188,4,.22)` |
| `--lu-state-drag` | `rgba(106,27,154,.08)` | `rgba(167,130,224,.18)` |
| `--lu-match-right` | `rgba(230,81,0,.08)` | `rgba(230,145,56,.20)` |

## Section Identity Tokens

The light values below are extracted from the `.lu-hero` gradients in
`starlight/src/styles/course.css`. Dark values are darker and desaturated so
the identities remain legible against `--lu-bg`.

| Section token | Extracted light pair | Chosen dark pair |
| --- | --- | --- |
| `--lu-id-core` | `#0057B8` -> `#1A6FD4` | `#174A73` -> `#245F8C` |
| `--lu-id-lexicon` | `#00695C` -> `#004D40` | `#175A50` -> `#123F39` |
| `--lu-id-folk` | `#A4133C` -> `#C9621A` | `#6D2135` -> `#74401F` |
| `--lu-id-lit` | `#4A148C` -> `#AD1457` | `#3A2362` -> `#6A2747` |
| `--lu-id-seminar` | `#4E342E` -> `#00695C` | `#3A2D2A` -> `#175A50` |
| `--lu-id-history` | `#BF360C` -> `#6D4C41` | `#773318` -> `#523F38` |
