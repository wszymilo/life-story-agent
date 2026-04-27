import { useState, FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, Link } from 'react-router-dom'
import { signUp } from 'aws-amplify/auth'

type SignUpState = 'idle' | 'loading' | 'success' | 'error'

export function SignUpScreen() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [state, setState] = useState<SignUpState>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [validationError, setValidationError] = useState('')

  const validateForm = () => {
    if (password.length < 8) {
      setValidationError(t('signup.passwordTooShort'))
      return false
    }
    if (!/[a-z]/.test(password)) {
      setValidationError(t('signup.requireLowercase'))
      return false
    }
    if (!/[A-Z]/.test(password)) {
      setValidationError(t('signup.requireUppercase'))
      return false
    }
    if (!/[0-9]/.test(password)) {
      setValidationError(t('signup.requireNumber'))
      return false
    }
    if (password !== confirmPassword) {
      setValidationError(t('signup.passwordMismatch'))
      return false
    }
    setValidationError('')
    return true
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setState('loading')
    setErrorMessage('')
    setValidationError('')

    if (!validateForm()) {
      setState('error')
      return
    }

    try {
      await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
          },
        },
      })
      setState('success')
    } catch (error) {
      setState('error')
      setErrorMessage(error instanceof Error ? error.message : t('signup.errorSend'))
    }
  }

  if (state === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-green-600 text-5xl mb-4">✓</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {t('signup.successTitle')}
          </h1>
          <p className="text-gray-600 mb-6">
            {t('signup.successMessage', { email })}
          </p>
          <button
            onClick={() => navigate('/login')}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium text-lg hover:bg-blue-700"
          >
            {t('signup.goToLogin')}
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
            {t('signup.title')}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                {t('signup.emailLabel')}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('signup.emailPlaceholder')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                disabled={state === 'loading'}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                {t('signup.passwordLabel')}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t('signup.passwordPlaceholder')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                disabled={state === 'loading'}
              />
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                {t('signup.confirmPasswordLabel')}
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t('signup.confirmPasswordPlaceholder')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                disabled={state === 'loading'}
              />
            </div>

            <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
              <p className="font-medium mb-2">{t('signup.passwordRequirements')}:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>{t('signup.minLength')}</li>
                <li>{t('signup.requireLowercase')}</li>
                <li>{t('signup.requireUppercase')}</li>
                <li>{t('signup.requireNumber')}</li>
              </ul>
            </div>

            {(state === 'error' && validationError) && (
              <div className="text-red-600 text-sm" role="alert">{validationError}</div>
            )}

            {state === 'error' && errorMessage && (
              <div className="text-red-600 text-sm" role="alert" aria-live="assertive">{errorMessage}</div>
            )}

            <button
              type="submit"
              disabled={state === 'loading'}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium text-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {state === 'loading' ? t('signup.sending') : t('signup.submit')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              {t('signup.haveAccount')}{' '}
              <Link to="/login" className="text-blue-600 hover:underline">
                {t('signup.signInLink')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}