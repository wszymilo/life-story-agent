import { useState, FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'
import { confirmSignUp } from 'aws-amplify/auth'

type VerifyState = 'idle' | 'loading' | 'success' | 'error'

export function VerifyEmailScreen() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const email = (location.state as { email?: string })?.email || ''

  const [code, setCode] = useState('')
  const [state, setState] = useState<VerifyState>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setState('loading')
    setErrorMessage('')

    try {
      await confirmSignUp({
        username: email,
        confirmationCode: code,
      })
      setState('success')
    } catch (error) {
      setState('error')
      setErrorMessage(error instanceof Error ? error.message : t('verify.errorSend'))
    }
  }

  if (state === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-green-600 text-5xl mb-4">✓</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {t('verify.successTitle')}
          </h1>
          <p className="text-gray-600 mb-6">
            {t('verify.successMessage')}
          </p>
          <button
            onClick={() => navigate('/login', { state: { verifiedEmail: email } })}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium text-lg hover:bg-blue-700"
          >
            {t('verify.goToLogin')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            {t('app.name')}
          </h1>
          <p className="text-gray-600 mt-2">
            {t('app.tagline')}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            {t('verify.title')}
          </h2>

          <p className="text-gray-600 mb-6">
            {t('verify.description', { email })}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="code"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                {t('verify.codeLabel')}
              </label>
              <input
                id="code"
                name="code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                placeholder={t('verify.codePlaceholder')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg text-center tracking-widest"
                disabled={state === 'loading'}
                autoFocus
              />
            </div>

            {state === 'error' && errorMessage && (
              <div className="text-red-600 text-sm" role="alert" aria-live="assertive">{errorMessage}</div>
            )}

            <button
              type="submit"
              disabled={state === 'loading'}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium text-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {state === 'loading' ? t('verify.sending') : t('verify.submit')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              {t('verify.noCode')}{' '}
              <button
                onClick={() => navigate('/signup')}
                className="text-blue-600 hover:underline"
              >
                {t('verify.tryAgain')}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}