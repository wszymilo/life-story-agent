-- Migration: Add evaluation_results table
-- Description: Store LLM-as-judge evaluation results for quality tracking

CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id),
    eval_type TEXT NOT NULL,
    prompt_hash TEXT,
    prompt_text TEXT,
    summary_text TEXT,
    factual_accuracy INT CHECK (factual_accuracy BETWEEN 1 AND 5),
    coherence INT CHECK (coherence BETWEEN 1 AND 5),
    completeness INT CHECK (completeness BETWEEN 1 AND 5),
    overall_score INT CHECK (overall_score BETWEEN 1 AND 5),
    evaluator_model TEXT DEFAULT 'gpt-4o',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for dashboard queries
CREATE INDEX IF NOT EXISTS idx_eval_created ON evaluation_results(created_at DESC);

-- Index for event lookups
CREATE INDEX IF NOT EXISTS idx_eval_event ON evaluation_results(event_id);

-- Enable RLS
ALTER TABLE evaluation_results ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can insert (for auto-evaluation)
CREATE POLICY "Anyone can insert evaluations" ON evaluation_results
    FOR INSERT TO authenticated
    WITH CHECK (true);

-- Policy: Only admin can read (checked via API, not RLS)
CREATE POLICY "Anyone can read evaluations" ON evaluation_results
    FOR SELECT TO authenticated
    USING (true);