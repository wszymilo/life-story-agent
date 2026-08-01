-- Life Story Preservation Agent — Clean Schema
-- Stripped of Supabase-specific RLS and auth triggers.
-- All migrations (001–008) applied, with users.id as TEXT for Firebase UIDs.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================================================
-- Migration 001: Initial schema (cleaned — no RLS, no Supabase auth)
-- ==========================================================================

-- Users table — id is TEXT (Firebase UID), not UUID
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    birth_date DATE,
    country_of_origin TEXT,
    preferred_language TEXT DEFAULT 'pl',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Relatives table
CREATE TABLE IF NOT EXISTS relatives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Events table
DO $$ BEGIN
    CREATE TYPE event_status AS ENUM ('draft', 'complete');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    time_anchor TEXT,
    time_anchor_date DATE,
    place TEXT,
    status event_status NOT NULL DEFAULT 'draft',
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audio recordings table
DO $$ BEGIN
    CREATE TYPE recording_type AS ENUM ('initial_story', 'follow_up_response');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS audio_recordings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    audio_url TEXT NOT NULL,
    transcript TEXT,
    recording_type recording_type NOT NULL,
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Follow-up questions table
CREATE TABLE IF NOT EXISTS follow_up_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    was_answered BOOLEAN NOT NULL DEFAULT FALSE,
    audio_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_relatives_user_id ON relatives(user_id);
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_time_anchor_date ON events(time_anchor_date);
CREATE INDEX IF NOT EXISTS idx_audio_recordings_event_id ON audio_recordings(event_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_questions_event_id ON follow_up_questions(event_id);

-- ==========================================================================
-- Migration 002: Add source_event_ids to events
-- ==========================================================================

ALTER TABLE events ADD COLUMN IF NOT EXISTS source_event_ids JSON DEFAULT '[]'::json;

-- ==========================================================================
-- Migration 003 + 005: Evaluation results table (no content columns)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    eval_type TEXT NOT NULL,
    factual_accuracy INT CHECK (factual_accuracy BETWEEN 1 AND 5),
    coherence INT CHECK (coherence BETWEEN 1 AND 5),
    completeness INT CHECK (completeness BETWEEN 1 AND 5),
    overall_score INT CHECK (overall_score BETWEEN 1 AND 5),
    evaluator_model TEXT DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eval_created ON evaluation_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eval_event ON evaluation_results(event_id);

-- ==========================================================================
-- Migration 006 + 008: Add trace_id to events
-- ==========================================================================

ALTER TABLE events ADD COLUMN IF NOT EXISTS trace_id VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events(trace_id);

-- ==========================================================================
-- Migration 007 is inherently applied above (users.id is TEXT from the start)
-- ==========================================================================
