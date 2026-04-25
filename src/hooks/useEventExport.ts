import { useState, useCallback } from 'react'
import JSZip from 'jszip'
import unidecode from 'unidecode'
import i18n from '../i18n'
import { EventData, AudioRecording, streamAudio } from '../services/events'

function sanitizeFilename(name: string): string {
  // First transliterate Unicode characters to ASCII equivalents
  // e.g., "Motocyklowa Odysseja przez Norwegię" → "Motocyklowa Odysseja przez Norwegie"
  // e.g., "Zażółć gęślą jaźń" → "Zazolc gesla jazn"
  let sanitized = unidecode(name)

  // Then remove invalid filename characters for Windows/Mac/Linux
  // Also replace commas, periods, and spaces with underscores for cleaner filenames
  sanitized = sanitized.replace(/[<>:"/\\|?*,]/g, '_')
  sanitized = sanitized.replace(/\s+/g, '_')
  sanitized = sanitized.trim().replace(/^[.]+|[.]+$/g, '').replace(/^_+|_+$/g, '')
  if (!sanitized) {
    sanitized = 'untitled'
  }
  return sanitized.slice(0, 100)
}

function generateMarkdown(title: string, summary: string | null, recordings: AudioRecording[]): string {
  const mdLines: string[] = [
    `# ${title}`,
    '',
  ]

  if (summary) {
    mdLines.push(`## ${i18n.t('export.summary')}`)
    mdLines.push('')
    mdLines.push(summary)
    mdLines.push('')
  }

  mdLines.push('---')
  mdLines.push('')
  mdLines.push(`## ${i18n.t('export.recordings')}`)
  mdLines.push('')

  for (const rec of recordings) {
    const recType = rec.recording_type || 'unknown'
    const created = rec.created_at
      ? new Date(rec.created_at).toISOString()
      : ''
    if (created) {
      mdLines.push(`- **${recType}** - ${created}`)
    } else {
      mdLines.push(`- **${recType}**`)
    }
  }

  mdLines.push('')
  mdLines.push('---')
  mdLines.push('')
  mdLines.push(`*${i18n.t('export.exportedFrom')}*`)

  return mdLines.join('\n')
}

export function useEventExport() {
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const downloadExport = useCallback(async (event: EventData): Promise<void> => {
    setExporting(true)
    setExportError(null)
    try {
      const zip = new JSZip()

      const title = event.title || i18n.t('export.untitledStory')
      const safeTitle = sanitizeFilename(title)

      // Generate markdown and add to root
      const mdContent = generateMarkdown(title, event.summary, event.recordings || [])
      zip.file(`${safeTitle}.md`, mdContent)

      // Sort recordings into initial story and follow-ups
      const initialStory = event.recordings?.find(
        (r) => r.recording_type === 'initial_story'
      )
      const additionalRecordings =
        event.recordings?.filter((r) => r.recording_type !== 'initial_story') || []

      // Add initial story to artifacts/
      if (initialStory) {
        if (initialStory.transcript) {
          zip.file(`artifacts/${safeTitle}.txt`, initialStory.transcript)
        }
        if (initialStory.audio_url) {
          try {
            const blob = await streamAudio(event.id, initialStory.id)
            zip.file(`artifacts/${safeTitle}.webm`, blob)
          } catch {
            // Skip audio files that fail to load
          }
        }
      }

      // Add follow-ups to artifacts/additional/
      for (let i = 0; i < additionalRecordings.length; i++) {
        const rec = additionalRecordings[i]
        const baseName = `follow_up_${i + 1}`
        if (rec.transcript) {
          zip.file(`artifacts/additional/${baseName}.txt`, rec.transcript)
        }
        if (rec.audio_url) {
          try {
            const blob = await streamAudio(event.id, rec.id)
            zip.file(`artifacts/additional/${baseName}.webm`, blob)
          } catch {
            // Skip audio files that fail to load
          }
        }
      }

      const zipBlob = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(zipBlob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${safeTitle}.zip`
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
