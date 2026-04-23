import { useState, useCallback } from 'react'

export function useEventSelection() {
  const [multiSelectMode, setMultiSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const toggleSelection = useCallback((eventId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(eventId)) {
        next.delete(eventId)
      } else {
        next.add(eventId)
      }
      return next
    })
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set())
    setMultiSelectMode(false)
  }, [])

  const enterSelectionMode = useCallback(() => {
    setMultiSelectMode(true)
  }, [])

  const isSelected = useCallback(
    (eventId: string) => selectedIds.has(eventId),
    [selectedIds]
  )

  return {
    multiSelectMode,
    selectedIds,
    toggleSelection,
    clearSelection,
    enterSelectionMode,
    isSelected,
  }
}
