-- Migration: 002_add_trace_id.sql
-- Life Story Preservation Agent - Add LangFuse trace_id to events

ALTER TABLE events ADD COLUMN IF NOT EXISTS trace_id VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events(trace_id);
