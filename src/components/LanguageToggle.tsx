import { useTranslation } from 'react-i18next'

interface LanguageToggleProps {
  onToggle?: (lang: string) => void
}

export function LanguageToggle({ onToggle }: LanguageToggleProps) {
  const { i18n, t } = useTranslation()
  const currentLang = i18n.language

  const toggleLanguage = () => {
    const newLang = currentLang === 'pl' ? 'en' : 'pl'
    i18n.changeLanguage(newLang)
    onToggle?.(newLang)
  }

  return (
    <button
      type="button"
      onClick={toggleLanguage}
      className="flex items-center gap-1 px-3 py-2 min-h-12 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg"
      title={t('onboarding.languageLabel')}
    >
      <span className={currentLang === 'pl' ? 'font-bold' : 'text-gray-400'}>PL</span>
      <span className="text-gray-300">|</span>
      <span className={currentLang === 'en' ? 'font-bold' : 'text-gray-400'}>EN</span>
    </button>
  )
}
