import { useState, FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { updateUserProfile } from '../services/user'
import { TopBar } from './TopBar'

const COUNTRIES = [
  'Poland',
  'United Kingdom',
  'United States',
]

const COUNTRY_TO_LANGUAGE: Record<string, string> = {
  'Poland': 'pl',
  'United Kingdom': 'en',
  'United States': 'en',
}

export function OnboardingScreen() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { refreshProfile } = useAuth()
  const [step, setStep] = useState(1)
  const [name, setName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [country, setCountry] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleNext = () => {
    setError('')
    if (step === 1) {
      if (!name.trim()) {
        setError(t('onboarding.nameError'))
        return
      }
    }
    if (step === 2) {
      if (!birthDate) {
        setError(t('onboarding.birthDateError'))
        return
      }
    }
    setStep(step + 1)
  }

  const handleBack = () => {
    setError('')
    setStep(step - 1)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!country) {
      setError(t('onboarding.countryError'))
      return
    }

    setSaving(true)
    setError('')

    try {
      await updateUserProfile({
        name: name.trim(),
        birth_date: birthDate,
        country_of_origin: country,
        preferred_language: COUNTRY_TO_LANGUAGE[country] || 'pl',
      })
      await refreshProfile()
      navigate('/', { replace: true })
    } catch {
      setError(t('onboarding.saveError'))
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar title={t('onboarding.welcome')} back={step > 1 ? { action: handleBack } : undefined} />
      <div className="max-w-md mx-auto p-4">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 text-center">
            {t('onboarding.heading')}
          </h1>
        </div>

        <div className="flex justify-center mb-8">
          <div className="flex gap-3">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`w-6 h-6 rounded-full transition-colors ${
                  s === step ? 'bg-blue-600' : s < step ? 'bg-green-500' : 'bg-gray-300'
                }`}
                role="img"
                aria-label={t('common.stepOf', { step: s, total: 3 })}
              />
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          {step === 1 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 text-lg">
                {t('onboarding.nameQuestion')}
              </h2>
              <form noValidate onSubmit={(e) => { e.preventDefault(); handleNext() }}>
                <input
                  type="text"
                  name="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={t('onboarding.namePlaceholder')}
                  className="w-full px-4 py-4 text-xl border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-12"
                  autoFocus
                />
                {error && <p className="text-red-600 mt-2 text-lg">{error}</p>}
                <button
                  type="submit"
                  className="w-full mt-6 bg-blue-600 text-white py-4 px-6 rounded-lg font-medium text-lg hover:bg-blue-700 min-h-12"
                >
                  {t('common.next')}
                </button>
              </form>
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 text-lg">
                {t('onboarding.birthDateQuestion')}
              </h2>
              <form noValidate onSubmit={(e) => { e.preventDefault(); handleNext() }}>
                <input
                  type="date"
                  name="birthDate"
                  value={birthDate}
                  onChange={(e) => setBirthDate(e.target.value)}
                  className="w-full px-4 py-4 text-xl border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-12"
                  autoFocus
                />
                {error && <p className="text-red-600 mt-2 text-lg">{error}</p>}
                <div className="flex gap-4 mt-6">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="flex-1 bg-gray-200 text-gray-700 py-4 px-6 rounded-lg font-medium text-lg hover:bg-gray-300 min-h-12"
                  >
                    {t('common.back')}
                  </button>
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-4 px-6 rounded-lg font-medium text-lg hover:bg-blue-700 min-h-12"
                  >
                    {t('common.next')}
                  </button>
                </div>
              </form>
            </div>
          )}

          {step === 3 && (
            <form noValidate onSubmit={handleSubmit}>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 text-lg">
                {t('onboarding.countryQuestion')}
              </h2>
              <select
                name="country"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full px-4 py-4 text-xl border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white min-h-12"
                autoFocus
              >
                <option value="">{t('onboarding.countryPlaceholder')}</option>
                {COUNTRIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              {error && <p className="text-red-600 mt-2 text-lg">{error}</p>}
              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 bg-gray-200 text-gray-700 py-4 px-6 rounded-lg font-medium text-lg hover:bg-gray-300 min-h-12"
                >
                  {t('common.back')}
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-blue-600 text-white py-4 px-6 rounded-lg font-medium text-lg hover:bg-blue-700 disabled:opacity-50 min-h-12"
                >
                  {saving ? t('common.saving') : t('common.save')}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
