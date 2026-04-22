import { useState, useCallback } from 'react'
import { exportEvent, ExportResult } from '../services/events'

export function useEventExport() {
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const downloadExport = useCallback(async (eventId: string): Promise<void> => {
    setExporting(true)
    setExportError(null)
    try {
      const { blob, filename }: ExportResult = await exportEvent(eventId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
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
