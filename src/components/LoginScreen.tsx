import { useState, FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import { signInWithPassword } from '../services/auth'

type LoginState = 'idle' | 'loading' | 'success' | 'error'

export function LoginScreen() {
  const { t } = useTranslation()
  const location = useLocation()
  const verifiedEmail = (location.state as { verifiedEmail?: string })?.verifiedEmail
  const [email, setEmail] = useState(verifiedEmail || '')
  const [showVerifiedMessage, setShowVerifiedMessage] = useState(!!verifiedEmail)
  const [password, setPassword] = useState('')
  const [loginState, setLoginState] = useState<LoginState>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoginState('loading')
    setErrorMessage('')

    const result = await signInWithPassword(email, password)

    if (result.success) {
      setLoginState('success')
      setShowVerifiedMessage(false)
    } else {
      setLoginState('error')
      setErrorMessage(result.error || t('login.errorSend'))
    }
  }

  if (loginState === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-green-600 text-5xl mb-4">✓</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {t('login.successTitle')}
          </h1>
          <p className="text-gray-600" dangerouslySetInnerHTML={{ __html: t('login.successMessage', { email }) }} />
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
            {t('login.signInHeading')}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                {t('login.emailLabel')}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('login.emailPlaceholder')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                disabled={loginState === 'loading'}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                {t('login.passwordLabel')}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t('login.passwordPlaceholder')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                disabled={loginState === 'loading'}
              />
            </div>

            {showVerifiedMessage && (
              <div className="bg-green-50 text-green-700 text-sm p-3 rounded-lg">
                {t('login.emailVerified')}
              </div>
            )}

            {loginState === 'error' && (
              <div className="text-red-600 text-sm" role="alert" aria-live="assertive">{errorMessage}</div>
            )}

            <button
              type="submit"
              disabled={loginState === 'loading'}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium text-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loginState === 'loading' ? t('login.sending') : t('login.signIn')}
            </button>
</form>

        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            {t('login.noAccount')}{' '}
            <Link to="/signup" className="text-blue-600 hover:underline">
              {t('login.signUpLink')}
            </Link>
          </p>
        </div>
      </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          {t('login.passwordInfo')}
        </p>
      </div>
    </div>
  )
}