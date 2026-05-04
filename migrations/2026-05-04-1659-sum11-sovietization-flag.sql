-- Migration: add sovietization_risk metadata to sum11 (СУМ-11) table
-- Issue: #1659 (parent EPIC #1657)
-- Context: СУМ-11 (1970-1980) is partially Sovietized for ideologically loaded
-- entries. Without a flag layer, reviewer pulls Soviet framing as authoritative.
-- This migration adds two columns; the scan script populates them.
--
-- Safety:
-- * ALTER TABLE on a 127K-row regular (non-FTS) table is fast.
-- * Columns have DEFAULT values so existing SELECT queries are unaffected.
-- * No data is removed or rewritten.
--
-- Rollback: see corresponding _rollback.sql

ALTER TABLE sum11 ADD COLUMN sovietization_risk INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sum11 ADD COLUMN sovietization_keywords TEXT NOT NULL DEFAULT '';

-- sovietization_risk semantics:
--   0 = clean (no Soviet-era markers in definition or text)
--   1 = present (≥1 keyword match in definition or text)
--   2 = high (≥3 keyword matches OR a definition opener that frames the
--       headword in Soviet ideology)
--
-- sovietization_keywords: comma-separated list of matched keyword stems
-- (e.g. "ленін,більшовик,радянськ"). Empty when sovietization_risk = 0.

CREATE INDEX IF NOT EXISTS idx_sum11_sovietization
    ON sum11(sovietization_risk) WHERE sovietization_risk > 0;
