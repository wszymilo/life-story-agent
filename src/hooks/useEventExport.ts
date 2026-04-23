import { useState, useCallback } from 'react'
import JSZip from 'jszip'
import { EventData, AudioRecording, streamAudio } from '../services/events'

function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9\u00C0-\u017F\s-]/g, '').replace(/\s+/g, '_').slice(0, 50) || 'story'
}

export function useEventExport() {
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const downloadExport = useCallback(async (event: EventData): Promise<void> => {
    setExporting(true)
    setExportError(null)
    try {
      const zip = new JSZip()

      // Build markdown
      const mdLines: string[] = [`# ${event.title || 'Untitled Memory'}`]
      if (event.time_anchor_date || event.time_anchor) {
        mdLines.push(`\n**Date:** ${event.time_anchor_date || event.time_anchor}`)
      }
      if (event.place) {
        mdLines.push(`\n**Place:** ${event.place}`)
      }
      if (event.summary) {
        mdLines.push(`\n## Summary\n\n${event.summary}`)
      }

      mdLines.push('\n## Sources\n')
      for (const recording of event.recordings || []) {
        mdLines.push(`\n### ${recording.recording_type === 'initial_story' ? 'Initial Story' : 'Follow-up Answer'}`)
        mdLines.push(`- Recorded: ${new Date(recording.created_at).toLocaleString()}`)
        if (recording.transcript) {
          mdLines.push(`\n${recording.transcript}`)
        }
      }

      zip.file('story.md', mdLines.join('\n'))

      // Add audio files
      for (const recording of event.recordings || []) {
        if (!recording.audio_url) continue
        try {
          const blob = await streamAudio(event.id, recording.id)
          zip.file(`recording_${recording.id}.webm`, blob)
        } catch {
          // Skip audio files that fail to load
        }
      }

      const zipBlob = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(zipBlob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${sanitizeFilename(event.title || 'story')}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to export'
      setExportError(message)
      alert(message)
    } finally {
      setExporting(false)
    }
  }, [])

  return { exporting, exportError, downloadExport }
}
