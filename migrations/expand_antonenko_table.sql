-- Expand the existing style_guide table
ALTER TABLE style_guide ADD COLUMN word_lower TEXT;
ALTER TABLE style_guide ADD COLUMN excerpt_full TEXT;
ALTER TABLE style_guide ADD COLUMN page INTEGER;

-- Create an index to make idempotent inserts and queries fast
CREATE UNIQUE INDEX IF NOT EXISTS idx_style_guide_word_page ON style_guide(word, page);
