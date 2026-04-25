import i18n from '../i18n'

export function formatDate(dateStr: string | null, locale?: string): string | null {
  if (!dateStr) return null
  try {
    const resolvedLocale = locale || (i18n.language === 'en' ? 'en-GB' : 'pl-PL')
    const date = new Date(dateStr)
    return date.toLocaleDateString(resolvedLocale, {
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
