-- Migration 002: Add preferred_language to users (Apr 20, 2026)
-- Run manually on existing database, or skip if fresh deployment
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language TEXT DEFAULT 'pl';

-- Meta-story: track source events
ALTER TABLE events ADD COLUMN IF NOT EXISTS source_event_ids UUID[] DEFAULT '{}';
