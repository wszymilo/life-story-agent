import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { updateUserProfile } from '../services/user'

const COUNTRIES = [
  'Poland',
  'United States',
  'United Kingdom',
  'Germany',
  'France',
  'Spain',
  'Italy',
  'Canada',
  'Australia',
  'Brazil',
  'Mexico',
  'Argentina',
  'Ukraine',
  'Russia',
  'Czech Republic',
  'Slovakia',
  'Hungary',
  'Romania',
  'Netherlands',
  'Sweden',
]

export function OnboardingScreen() {
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
        setError('Please enter your name')
        return
      }
    }
    if (step === 2) {
      if (!birthDate) {
        setError('Please select your birth date')
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
      setError('Please select your country')
      return
    }

    setSaving(true)
    setError('')

    try {
      await updateUserProfile({
        name: name.trim(),
        birth_date: birthDate,
        country_of_origin: country,
      })
      await refreshProfile()
      navigate('/', { replace: true })
    } catch {
      setError('Failed to save. Please try again.')
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-md mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 text-center">
            Welcome!
          </h1>
          <p className="text-gray-600 text-center mt-2">
            Let's get to know you better
          </p>
        </div>

        <div className="flex justify-center mb-8">
          <div className="flex gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`w-3 h-3 rounded-full transition-colors ${
                  s === step ? 'bg-blue-600' : s < step ? 'bg-green-500' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          {step === 1 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                What is your name?
              </h2>
              <form onSubmit={(e) => { e.preventDefault(); handleNext() }}>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your full name"
                  className="w-full px-4 py-4 text-xl border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  autoFocus
                />
                {error && <p className="text-red-600 mt-2">{error}</p>}
                <button
                  type="submit"
                  className="w-full mt-6 bg-blue-600 text-white py-4 px-6 rounded-lg font-medium text-lg hover:bg-blue-700"
                >
                  Next
                </button>
              </form>
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                When were you born?
              </h2>
              <form onSubmit={(e) => { e.preventDefault(); handleNext() }}>
                <input
                  type="date"
                  value={birthDate}
                  onChange={(e) => setBirthDate(e.target.value)}
                  className="w-full px-4 py-4 text-xl border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  autoFocus
                />
                {error && <p className="text-red-600 mt-2">{error}</p>}
                <div className="flex gap-4 mt-6">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="flex-1 bg-gray-200 text-gray-700 py-4 px-6 rounded-lg font-medium text-lg hover:bg-gray-300"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-4 px-6 rounded-lg font-medium text-lg hover:bg-blue-700"
                  >
                    Next
                  </button>
                </div>
              </form>
            </div>
          )}

          {step === 3 && (
            <form onSubmit={handleSubmit}>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Where are you from?
              </h2>
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full px-4 py-4 text-xl border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                autoFocus
              >
                <option value="">Select your country</option>
                {COUNTRIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              {error && <p className="text-red-600 mt-2">{error}</p>}
              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 bg-gray-200 text-gray-700 py-4 px-6 rounded-lg font-medium text-lg hover:bg-gray-300"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-blue-600 text-white py-4 px-6 rounded-lg font-medium text-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}