-- Migration: 001_initial_schema.sql
-- Life Story Preservation Agent - Aurora PostgreSQL Schema
-- Consolidated from Supabase migrations (without RLS - handled in app code)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    birth_date DATE,
    country_of_origin TEXT,
    preferred_language TEXT DEFAULT 'pl',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Relatives table
CREATE TABLE relatives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Events table
CREATE TYPE event_status AS ENUM ('draft', 'complete');

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    time_anchor TEXT,
    time_anchor_date DATE,
    place TEXT,
    status event_status NOT NULL DEFAULT 'draft',
    summary TEXT,
    source_event_ids UUID[] DEFAULT '{}',
    trace_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audio recordings table
CREATE TYPE recording_type AS ENUM ('initial_story', 'follow_up_response');

CREATE TABLE audio_recordings (
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
CREATE TABLE follow_up_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    was_answered BOOLEAN NOT NULL DEFAULT FALSE,
    audio_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Evaluation results table
CREATE TABLE evaluation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id),
    eval_type TEXT NOT NULL,
    factual_accuracy INT CHECK (factual_accuracy BETWEEN 1 AND 5),
    coherence INT CHECK (coherence BETWEEN 1 AND 5),
    completeness INT CHECK (completeness BETWEEN 1 AND 5),
    overall_score INT CHECK (overall_score BETWEEN 1 AND 5),
    evaluator_model TEXT DEFAULT 'gpt-4o',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_relatives_user_id ON relatives(user_id);
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_time_anchor_date ON events(time_anchor_date);
CREATE INDEX idx_events_trace_id ON events(trace_id);
CREATE INDEX idx_audio_recordings_event_id ON audio_recordings(event_id);
CREATE INDEX idx_follow_up_questions_event_id ON follow_up_questions(event_id);
CREATE INDEX idx_eval_created ON evaluation_results(created_at DESC);
CREATE INDEX idx_eval_event ON evaluation_results(event_id);

-- Function to auto-create user on first login (for Cognito auth trigger - future)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
