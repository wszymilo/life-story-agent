-- Migration: 007_remove_trace_id.sql
-- Life Story Preservation Agent - Remove LangFuse trace_id from events
-- (v4 SDK uses propagate_attributes + @observe() instead)

DROP INDEX IF EXISTS idx_events_trace_id;
ALTER TABLE events DROP COLUMN IF EXISTS trace_id;
