-- Drop sensitive content columns from evaluation_results
-- Scores-only storage for admin dashboard

ALTER TABLE evaluation_results
DROP COLUMN IF EXISTS prompt_text,
DROP COLUMN IF EXISTS summary_text,
DROP COLUMN IF EXISTS prompt_hash;
