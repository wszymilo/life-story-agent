-- Migration: 001_initial_schema.sql
-- Life Story Preservation Agent - Initial Schema
-- Run with: supabase db push or psql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    birth_date DATE,
    country_of_origin TEXT,
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

-- Meta-story: track source events
ALTER TABLE events ADD COLUMN IF NOT EXISTS source_event_ids UUID[] DEFAULT '{}';

-- Indexes for performance
CREATE INDEX idx_relatives_user_id ON relatives(user_id);
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_time_anchor_date ON events(time_anchor_date);
CREATE INDEX idx_audio_recordings_event_id ON audio_recordings(event_id);
CREATE INDEX idx_follow_up_questions_event_id ON follow_up_questions(event_id);

-- Row Level Security (RLS)

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE relatives ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE follow_up_questions ENABLE ROW LEVEL SECURITY;

-- Users: users can read/update their own profile
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Relatives: users can manage their own relatives
CREATE POLICY "Users can view own relatives" ON relatives
    FOR SELECT USING (user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'));

CREATE POLICY "Users can manage own relatives" ON relatives
    FOR ALL USING (user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'));

-- Events: users can manage their own events
CREATE POLICY "Users can view own events" ON events
    FOR SELECT USING (user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'));

CREATE POLICY "Users can manage own events" ON events
    FOR ALL USING (user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'));

-- Audio recordings: users can manage their own recordings
CREATE POLICY "Users can view own recordings" ON audio_recordings
    FOR SELECT USING (
        event_id IN (SELECT id FROM events WHERE user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'))
    );

CREATE POLICY "Users can manage own recordings" ON audio_recordings
    FOR ALL USING (
        event_id IN (SELECT id FROM events WHERE user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'))
    );

-- Follow-up questions: users can manage their own questions
CREATE POLICY "Users can view own questions" ON follow_up_questions
    FOR SELECT USING (
        event_id IN (SELECT id FROM events WHERE user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'))
    );

CREATE POLICY "Users can manage own questions" ON follow_up_questions
    FOR ALL USING (
        event_id IN (SELECT id FROM events WHERE user_id = (SELECT id FROM users WHERE email = auth.jwt()->>'email'))
    );

-- Function to auto-create user on first login (for magic link auth)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();