-- Migration: Add storage policies for audio-recordings bucket
-- Description: Allow authenticated users to upload and read audio files

-- Allow authenticated users to upload to audio-recordings bucket
CREATE POLICY IF NOT EXISTS "Allow uploads" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'audio-recordings');

-- Allow authenticated users to read from audio-recordings bucket
CREATE POLICY IF NOT EXISTS "Allow reads" ON storage.objects
FOR SELECT TO authenticated
USING (bucket_id = 'audio-recordings');

-- Allow public read access (for serving audio files to frontend)
CREATE POLICY IF NOT EXISTS "Allow public reads" ON storage.objects
FOR SELECT USING (bucket_id = 'audio-recordings');
