export function formatDate(dateStr: string | null, locale: string = 'pl-PL'): string | null {
  if (!dateStr) return null
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString(locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

export function formatDuration(seconds: number | null): string | null {
  if (!seconds) return null
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
