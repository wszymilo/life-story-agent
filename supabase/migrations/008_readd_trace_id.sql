-- Migration: 008_readd_trace_id.sql
-- Life Story Preservation Agent - Re-add LangFuse trace_id to events
-- (v4 SDK uses propagate_attributes for first call, then langfuse_trace_id for reuse)

ALTER TABLE events ADD COLUMN IF NOT EXISTS trace_id VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events(trace_id);
