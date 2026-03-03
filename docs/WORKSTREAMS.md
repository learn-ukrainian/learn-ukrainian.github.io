# Workstreams — V4 Full Curriculum Rebuild

> Master epic: [#717](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/717)
> Last updated: 2026-03-03

## Overview

8 workstreams, each with a GitHub label (`ws:*`) for filtering.

```
gh issue list --label "ws:rebuild-core" --state open
```

## Priority Order

| Priority | Workstream | Label | Focus |
|----------|-----------|-------|-------|
| **P0** | V4 Pipeline | `ws:v4-pipeline` | Test v4, prove upgrade + rebuild paths |
| **P0** | RAG | `ws:rag` | Supports all rebuild waves |
| **P1** | Core Rebuild | `ws:rebuild-core` | A1-B2 (Wave 1: 325 modules) |
| **P1** | Seminar Rebuild | `ws:rebuild-seminar` | HIST/BIO/ISTORIO (Waves 2-3, 6) |
| **P2** | Advanced Rebuild | `ws:rebuild-advanced` | C1/LIT/LIT-*/OES/RUTH/C2 (Waves 4-8) |
| **P2** | l2-uk-direct | `ws:l2-uk-direct` | Separate track, parallel work |
| **P3** | Infrastructure | `ws:infra` | Tests, CI/CD, performance |
| **P3** | Documentation | `ws:docs` | Site, guides, docs cleanup |

## ws:v4-pipeline — Pipeline V4 Testing & Launch

**Goal**: Prove v4 works for both upgrade and full-rebuild paths before batch runs.

| # | Title | Status |
|---|-------|--------|
| 703 | Pipeline v4 implementation | Code done, needs testing |
| 667 | Pipeline hardening (test regime) | Revised for v4 |
| 670 | Diagnose failing modules | Re-scope for v4 |
| 672 | Batch runs | Re-scope for v4 |
| ~~681~~ | ~~Gemini 3-preview → 3.1-preview~~ | ✅ Done |
| 640 | Prose proofreading script | Integrated into v4 validate |
| 718 | V4 upgrade: A1 track + HIST alignment audit | New |
| 719 | D.1 inline fixes — eliminate D.2 for simple repairs | New |
| 720 | V4 research quality evaluation | New |
| 725 | Audit & clean external_resources.yaml | In progress |

**Next action**: Run A1 track upgrade (#718) — 64 modules through v4 discover→content→review.

## ws:rebuild-core — Core Tracks A1-B2 (Wave 1)

**Goal**: All 325 A1-B2 modules rebuilt/upgraded through v4.

| # | Title | Status |
|---|-------|--------|
| 717 | Master rebuild epic | New |
| 560 | The Great Rebuild | Master content epic |
| 709 | A1 restructure 44→64 | Committed, 63/64 built |
| 710 | Research for new/restructured modules | Not started |
| 699 | Rewrite Cyrillic Code I-IV plans | Not started |
| 682 | A2 immersion rules | Not started |
| 594 | Pre-seed Phase A research | Not started |
| 705 | Vocabulary progression audit | Not started |

**Strategy**:
- A1: upgrade existing 63 + build 1 missing
- A2/B1/B2: drop content, rebuild from plans

## ws:rebuild-seminar — Seminar Tracks (Waves 2-3, 6)

**Goal**: HIST(140), BIO(175), ISTORIO(136) modules at v4 reviewed status.

| # | Title | Status |
|---|-------|--------|
| 706 | Seminar depth review | Not started |
| 499 | Chronicle quotes for C1-BIO | Not started |
| 635-638 | REALNA ISTORIIA content additions | Not started |
| 675 | Textbook image enrichment | Not started |

**Strategy**:
- HIST: upgrade via `--restart-from discover --review`
- BIO: upgrade 76 + build 99
- ISTORIO: upgrade 3 + build 133

## ws:rebuild-advanced — Advanced Tracks (Waves 4-8)

**Goal**: C1(106), LIT(221), LIT-*(159), OES(100), RUTH(112), C2(91) = 789 modules.

| # | Title | Status |
|---|-------|--------|
| 303 | C2 implementation | Blocked on v4 batch |
| 263 | C2 vocab | Blocked on #303 |
| 497 | OES + RUTH tracks | Blocked on plans + RAG |
| 550 | Literature expansion | Blocked on #701 |
| 658 | Literature Matrix Phase B | Blocked on #550 |
| 659 | Canonical gap fill | Blocked on #550 |
| 429 | PRO tracks activities | **DEFERRED** to STEM phase |
| 676 | Monolingual toggle | Feature, not rebuild |

**Depends on**: Literary RAG (#701), pipeline maturity from Waves 1-3.

## ws:rag — RAG Infrastructure

**Goal**: Comprehensive Ukrainian language verification and enrichment.

| # | Title | Status |
|---|-------|--------|
| 666 | RAG Infrastructure (Qdrant) | Operational (10K images, 1.2K text chunks) |
| 692 | RAG Content Expansion | Ongoing |
| 683 | Textbook processing pipeline | In progress |
| 695 | rag_batch_verify.py | Not started |
| 701 | Literary RAG (ukrlib) | In progress |
| 712 | Benchmark EmbeddingGemma vs BGE-M3 | Not started |
| 713 | Image annotation bugs | Not started |
| 715 | ZNO exam dataset (2,328 questions) | Not started |
| 376 | Map Dobra Forma textbook | Not started |
| 722 | Crawl and index ESU into RAG | New |
| 723 | Live query tools for research verification | New |
| 724 | Scrape ukrainianlessons.com full content | New |

## ws:l2-uk-direct — Direct Track

**Goal**: L1-agnostic Ukrainian course, parallel to l2-uk-en.

| # | Title | Status |
|---|-------|--------|
| 661 | Infrastructure & tooling | 10/47 A1 modules in draft |
| 662 | A1 module build | In progress |
| 664 | Scripts (source_images, manifest) | Not started |
| 674 | A2→B2 roadmap | Planning only |
| 708 | Dedicated pipeline | Not started |

## ws:infra — Infrastructure & Tech Debt

| # | Title | Status |
|---|-------|--------|
| 520 | Comprehensive test suite | 36 test files exist, v4 coverage missing |
| 521 | Performance bottlenecks | Not started |
| 532 | CI/CD pipeline | Not started |
| 688 | Deduplicate shared infrastructure | Not started |

## ws:docs — Documentation & Site

| # | Title | Status |
|---|-------|--------|
| 522 | Documentation gaps | Ongoing |
| 655 | Migrate to Astro Starlight | Not started |
| 634 | Monolingual lexicon builder | Not started |
